import json

from evals.batch_runner import (
    EvalCase,
    compute_expected_term_coverage,
    compute_question_coverage,
    consolidate_case_results,
    load_cases,
    score_case,
)


def test_load_cases_reads_jsonl(tmp_path):
    cases_file = tmp_path / "cases.jsonl"
    cases_file.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "case_a",
                        "ferramentas": "docker e podman",
                        "contexto": "linux",
                        "foco": "comparação geral",
                        "questoes": ["docker-compose funciona sem mudanças?"],
                        "expected_terms": ["rootless"],
                        "min_words": 500,
                        "pass_threshold": 0.75,
                    }
                ),
                json.dumps(
                    {
                        "id": "case_b",
                        "ferramentas": "duckdb e polars",
                        "contexto": "analytics",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    cases = load_cases(str(cases_file))
    assert len(cases) == 2
    assert cases[0].id == "case_a"
    assert cases[0].pass_threshold == 0.75
    assert cases[1].foco == "comparação geral"
    assert cases[1].min_words == 500
    assert cases[1].pass_threshold == 0.7


def test_coverage_helpers():
    article = (
        "Comparação entre Docker e Podman. Docker-compose funciona sem mudanças. "
        "Rootless melhora segurança."
    )
    question_score = compute_question_coverage(
        article,
        ["docker-compose funciona sem mudanças?", "qual usa menos RAM?"],
    )
    term_score = compute_expected_term_coverage(article, ["rootless", "benchmark"])
    assert question_score == 0.5
    assert term_score == 0.5


def test_score_case_composite_and_consolidation():
    case = EvalCase(
        id="case_a",
        ferramentas="docker e podman",
        contexto="linux",
        foco="comparação geral",
        questoes=["docker-compose funciona sem mudanças?"],
        expected_terms=["rootless"],
        min_words=1,
        pass_threshold=0.7,
    )
    article = "Docker-compose funciona sem mudanças. Rootless melhora segurança."
    score = score_case(case=case, article=article, approved=True)
    assert score["approved"] is True
    assert score["question_coverage"] == 1.0
    assert score["expected_term_coverage"] == 1.0
    assert score["composite_score"] == 1.0
    assert score["passed"] is True

    consolidated = consolidate_case_results(
        [
            {"score": score},
            {"score": {**score, "approved": False, "composite_score": 0.4, "passed": False}},
        ]
    )
    assert consolidated["cases_total"] == 2
    assert consolidated["cases_passed"] == 1
    assert consolidated["approval_rate"] == 0.5
    assert consolidated["avg_composite_score"] == 0.7
