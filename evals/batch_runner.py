import argparse
import json
import os
import re
import threading
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import monotonic
from typing import Any
from uuid import uuid4

from langsmith import Client

from pipeline import SDDPipeline


@dataclass
class EvalCase:
    id: str
    ferramentas: str
    contexto: str
    foco: str
    questoes: list[str]
    expected_terms: list[str]
    min_words: int
    pass_threshold: float


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return normalized.lower()


def normalize_for_match(text: str) -> str:
    lowered = normalize_text(text)
    cleaned = re.sub(r"[^\w\s]", " ", lowered, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned, flags=re.UNICODE).strip()


def load_cases(path: str) -> list[EvalCase]:
    cases: list[EvalCase] = []
    case_path = Path(path)
    if not case_path.exists():
        raise FileNotFoundError(f"Arquivo de casos não encontrado: {path}")

    for line_number, raw_line in enumerate(case_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        cases.append(
            EvalCase(
                id=str(payload["id"]),
                ferramentas=str(payload["ferramentas"]),
                contexto=str(payload["contexto"]),
                foco=str(payload.get("foco", "comparação geral")),
                questoes=[str(item) for item in payload.get("questoes", [])],
                expected_terms=[str(item) for item in payload.get("expected_terms", [])],
                min_words=int(payload.get("min_words", 500)),
                pass_threshold=float(payload.get("pass_threshold", 0.7)),
            )
        )
    if not cases:
        raise ValueError(f"Nenhum caso válido em {path}")
    return cases


def read_last_metrics_for_output(output_path: str, metrics_path: str = "output/metrics.json") -> dict[str, Any]:
    metrics_file = Path(metrics_path)
    if not metrics_file.exists():
        return {}

    matched: dict[str, Any] = {}
    for raw_line in metrics_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("output") == output_path:
            matched = item
    return matched


def compute_question_coverage(article: str, questions: list[str]) -> float:
    if not questions:
        return 1.0
    article_norm = normalize_for_match(article)
    hits = 0
    for question in questions:
        if normalize_for_match(question) in article_norm:
            hits += 1
    return hits / len(questions)


def compute_expected_term_coverage(article: str, expected_terms: list[str]) -> float:
    if not expected_terms:
        return 1.0
    article_norm = normalize_for_match(article)
    hits = 0
    for term in expected_terms:
        if normalize_for_match(term) in article_norm:
            hits += 1
    return hits / len(expected_terms)


def compute_word_count(article: str) -> int:
    return len(re.findall(r"\b\w+\b", article, flags=re.UNICODE))


def score_case(case: EvalCase, article: str, approved: bool) -> dict[str, Any]:
    question_coverage = compute_question_coverage(article, case.questoes)
    term_coverage = compute_expected_term_coverage(article, case.expected_terms)
    word_count = compute_word_count(article)
    min_words_ratio = min(1.0, word_count / max(case.min_words, 1))
    approved_score = 1.0 if approved else 0.0

    composite = (
        approved_score * 0.5
        + question_coverage * 0.2
        + term_coverage * 0.2
        + min_words_ratio * 0.1
    )
    passed = composite >= case.pass_threshold

    return {
        "approved": approved,
        "approved_score": round(approved_score, 4),
        "question_coverage": round(question_coverage, 4),
        "expected_term_coverage": round(term_coverage, 4),
        "word_count": word_count,
        "min_words_ratio": round(min_words_ratio, 4),
        "pass_threshold": case.pass_threshold,
        "composite_score": round(composite, 4),
        "passed": passed,
    }


def consolidate_case_results(cases_results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(cases_results)
    if total == 0:
        return {
            "cases_total": 0,
            "cases_passed": 0,
            "approval_rate": 0.0,
            "pass_rate": 0.0,
            "avg_composite_score": 0.0,
            "avg_question_coverage": 0.0,
            "avg_expected_term_coverage": 0.0,
        }

    approved_count = sum(1 for item in cases_results if item["score"]["approved"])
    passed_count = sum(1 for item in cases_results if item["score"]["passed"])
    avg_composite = sum(item["score"]["composite_score"] for item in cases_results) / total
    avg_questions = sum(item["score"]["question_coverage"] for item in cases_results) / total
    avg_terms = sum(item["score"]["expected_term_coverage"] for item in cases_results) / total

    return {
        "cases_total": total,
        "cases_passed": passed_count,
        "approval_rate": round(approved_count / total, 4),
        "pass_rate": round(passed_count / total, 4),
        "avg_composite_score": round(avg_composite, 4),
        "avg_question_coverage": round(avg_questions, 4),
        "avg_expected_term_coverage": round(avg_terms, 4),
    }


class LangSmithTracker:
    def __init__(self, enabled: bool):
        self.enabled = enabled and bool(
            os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
        )
        self.project_name = os.getenv("LANGSMITH_PROJECT", "sdd-ollama-evals")
        self.dataset_name = os.getenv("LANGSMITH_DATASET", "sdd-ollama-fixed-cases")
        self.client = Client() if self.enabled else None

    def sync_dataset(self, cases: list[EvalCase]) -> dict[str, Any]:
        if not self.enabled or not self.client:
            return {"enabled": False, "reason": "LANGSMITH_API_KEY ausente ou integração desabilitada"}

        try:
            dataset = next(
                self.client.list_datasets(dataset_name=self.dataset_name, limit=1),
                None,
            )
            if dataset is None:
                dataset = self.client.create_dataset(
                    self.dataset_name,
                    description="Casos fixos de avaliação para o pipeline SDD Ollama.",
                )

            existing_case_ids = set()
            for example in self.client.list_examples(dataset_id=dataset.id, limit=500):
                metadata = example.metadata or {}
                case_id = metadata.get("case_id")
                if case_id:
                    existing_case_ids.add(str(case_id))

            created = 0
            for case in cases:
                if case.id in existing_case_ids:
                    continue
                self.client.create_example(
                    dataset_id=dataset.id,
                    inputs={
                        "ferramentas": case.ferramentas,
                        "contexto": case.contexto,
                        "foco": case.foco,
                        "questoes": case.questoes,
                    },
                    outputs={
                        "expected_terms": case.expected_terms,
                        "min_words": case.min_words,
                        "pass_threshold": case.pass_threshold,
                    },
                    metadata={
                        "case_id": case.id,
                        "source": "evals/cases.jsonl",
                    },
                )
                created += 1
            return {
                "enabled": True,
                "dataset_name": self.dataset_name,
                "dataset_id": str(dataset.id),
                "created_examples": created,
            }
        except Exception as exc:
            return {"enabled": True, "error": str(exc)}

    def log_case_result(self, run_id: str, case: EvalCase, case_result: dict[str, Any]):
        if not self.enabled or not self.client:
            return
        try:
            self.client.create_run(
                id=run_id,
                name=f"eval_case:{case.id}",
                run_type="chain",
                project_name=self.project_name,
                inputs={
                    "case_id": case.id,
                    "ferramentas": case.ferramentas,
                    "contexto": case.contexto,
                    "foco": case.foco,
                    "questoes": case.questoes,
                },
                outputs={
                    "output_path": case_result["output_path"],
                    "approved": case_result["score"]["approved"],
                    "score": case_result["score"],
                },
                extra={"metadata": {"kind": "eval_case", "eval_run_id": case_result["eval_run_id"]}},
                start_time=datetime.fromisoformat(case_result["started_at"]),
                end_time=datetime.fromisoformat(case_result["ended_at"]),
            )
            self.client.create_feedback(
                run_id=run_id,
                key="composite_score",
                score=float(case_result["score"]["composite_score"]),
                comment=f"approved={case_result['score']['approved']}",
            )
            self.client.create_feedback(
                run_id=run_id,
                key="passed",
                score=bool(case_result["score"]["passed"]),
            )
        except Exception:
            return


def run_single_case(eval_run_id: str, case: EvalCase, verbosity: str) -> dict[str, Any]:
    started_at = utc_now_iso()
    wall_clock_start = monotonic()

    event_log_path = f"output/evals/events_{eval_run_id}_{case.id}.jsonl"
    pipeline = SDDPipeline(verbose=False, verbosity=verbosity, event_log_path=event_log_path)
    run_out: dict[str, Any] = {}
    run_error: dict[str, Exception] = {}

    def _run_pipeline():
        try:
            run_out["output_path"] = pipeline.run(
                ferramentas=case.ferramentas,
                contexto=case.contexto,
                foco=case.foco,
                questoes=case.questoes,
            )
        except Exception as exc:
            run_error["error"] = exc

    worker = threading.Thread(target=_run_pipeline, daemon=True)
    worker.start()
    last_event_signature = ""
    last_event_change_t = monotonic()

    while worker.is_alive():
        worker.join(timeout=15)
        if worker.is_alive():
            event = read_last_event(event_log_path)
            if event:
                event_type = event.get("type", "unknown")
                phase = event.get("phase", "")
                phase_str = f" phase={phase}" if phase else ""
                signature = f"{event_type}:{phase}:{event.get('timestamp', event.get('ts', ''))}"
                if signature != last_event_signature:
                    last_event_signature = signature
                    last_event_change_t = monotonic()
                stale_for = int(monotonic() - last_event_change_t)
                stale_str = f" stale={stale_for}s" if stale_for >= 30 else ""
                print(
                    f"    heartbeat [{case.id}] t+{int(monotonic() - wall_clock_start)}s"
                    f" event={event_type}{phase_str}{stale_str}",
                    flush=True,
                )
            else:
                print(
                    f"    heartbeat [{case.id}] t+{int(monotonic() - wall_clock_start)}s aguardando eventos",
                    flush=True,
                )

    if "error" in run_error:
        raise run_error["error"]
    output_path = str(run_out["output_path"])

    metrics = read_last_metrics_for_output(output_path)
    approved = bool(metrics.get("approved", False))
    article = Path(output_path).read_text(encoding="utf-8")
    score = score_case(case=case, article=article, approved=approved)

    return {
        "eval_run_id": eval_run_id,
        "case_id": case.id,
        "started_at": started_at,
        "ended_at": utc_now_iso(),
        "elapsed_seconds": round(monotonic() - wall_clock_start, 3),
        "ferramentas": case.ferramentas,
        "contexto": case.contexto,
        "foco": case.foco,
        "questoes": case.questoes,
        "output_path": output_path,
        "score": score,
    }


def append_jsonl(path: str, payload: dict[str, Any]):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_last_event(path: str) -> dict[str, Any]:
    event_file = Path(path)
    if not event_file.exists():
        return {}
    last_line = ""
    try:
        with event_file.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    last_line = line
        return json.loads(last_line) if last_line else {}
    except Exception:
        return {}


def run_batch(
    *,
    cases_path: str,
    limit: int | None,
    case_id_filter: set[str] | None,
    verbosity: str,
    use_langsmith: bool,
) -> dict[str, Any]:
    eval_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_cases = load_cases(cases_path)
    selected_cases = [case for case in all_cases if not case_id_filter or case.id in case_id_filter]
    if limit:
        selected_cases = selected_cases[:limit]
    if not selected_cases:
        raise ValueError("Nenhum caso selecionado para execução.")

    tracker = LangSmithTracker(enabled=use_langsmith)
    dataset_status = tracker.sync_dataset(selected_cases)

    case_results: list[dict[str, Any]] = []
    for index, case in enumerate(selected_cases, 1):
        print(f"[{index}/{len(selected_cases)}] rodando case `{case.id}`", flush=True)
        case_result = run_single_case(eval_run_id=eval_run_id, case=case, verbosity=verbosity)
        case_results.append(case_result)
        tracker.log_case_result(run_id=str(uuid4()), case=case, case_result=case_result)

        score = case_result["score"]
        print(
            "  -> approved="
            f"{score['approved']} | passed={score['passed']} | composite={score['composite_score']}"
        , flush=True)

    consolidated = consolidate_case_results(case_results)
    execution_report = {
        "eval_run_id": eval_run_id,
        "generated_at": utc_now_iso(),
        "cases_path": cases_path,
        "selected_case_ids": [case.id for case in selected_cases],
        "langsmith_dataset_sync": dataset_status,
        "consolidated_score": consolidated,
        "cases": case_results,
    }

    report_path = Path(f"output/evals/run_{eval_run_id}.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(execution_report, ensure_ascii=False, indent=2), encoding="utf-8")

    append_jsonl(
        "output/evals/scores.jsonl",
        {
            "eval_run_id": eval_run_id,
            "generated_at": execution_report["generated_at"],
            "cases_total": consolidated["cases_total"],
            "cases_passed": consolidated["cases_passed"],
            "pass_rate": consolidated["pass_rate"],
            "approval_rate": consolidated["approval_rate"],
            "avg_composite_score": consolidated["avg_composite_score"],
            "report_path": str(report_path),
        },
    )

    print("\nScore consolidado da execução:", flush=True)
    print(json.dumps(consolidated, ensure_ascii=False, indent=2), flush=True)
    print(f"\nRelatório salvo em: {report_path}", flush=True)
    return execution_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Runner de eval batch com score consolidado.")
    parser.add_argument("--cases", default="evals/cases.jsonl", help="Caminho do dataset fixo (JSONL).")
    parser.add_argument("--limit", type=int, default=None, help="Limita quantidade de casos.")
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Filtra por case_id (pode repetir o argumento).",
    )
    parser.add_argument(
        "--verbosity",
        default="quiet",
        choices=["quiet", "minimal", "detailed"],
        help="Verbosity interna do pipeline durante os evals.",
    )
    parser.add_argument(
        "--no-langsmith",
        action="store_true",
        help="Desabilita integração com LangSmith.",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    run_batch(
        cases_path=args.cases,
        limit=args.limit,
        case_id_filter=set(args.case_id) if args.case_id else None,
        verbosity=args.verbosity,
        use_langsmith=not args.no_langsmith,
    )


if __name__ == "__main__":
    main()
