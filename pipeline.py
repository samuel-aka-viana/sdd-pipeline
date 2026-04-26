import os
import yaml
import json
import jsonschema
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from httpx import TimeoutException
from time import monotonic
from concurrent.futures import ThreadPoolExecutor, as_completed

from tools.search_tool import SearchTool
from tools.scraper_factory import create_scraper
from memory.memory_store import MemoryStore
from memory.research_chroma import ResearchChroma
from orchestration import LangGraphOrchestrator
from skills.researcher import ResearcherSkill
from skills.analyst import AnalystSkill
from skills.writer import WriterSkill
from skills.critic import CriticSkill
from skills.relevance_filter import RelevanceFilterSkill
from skills.evidence_builder import EvidenceBuilderSkill
from skills.router import ToolTypeRouter
from validators.template_validator import TemplateValidator
from logger import PipelineLogger
from prompts.manager import PromptManager
from llm import LLMClient
from utils import extract_json_object
from article_sanitizer import ArticleSanitizer
from enrichment.coordinator import EnrichmentCoordinator


class SDDPipeline:

    MAX_ITERATIONS = 3

    def __init__(
        self,
        spec_path: str = "spec/article_spec.yaml",
        verbose: bool = True,
        event_log_path: str = "output/pipeline_events.jsonl",
        verbosity: str | None = None,
    ):
        self.spec_path = spec_path
        self.spec      = yaml.safe_load(Path(spec_path).read_text())
        self.log       = PipelineLogger(verbose=verbose, log_file=event_log_path, verbosity=verbosity)
        
        # Load and validate spec against schema
        with open("spec/schema.json") as f:
            schema = json.load(f)
        
        try:
            jsonschema.validate(self.spec, schema)
            if self.log.verbosity == "detailed":
                self.log.console.print(f"[green]✓ Spec version {self.spec.get('spec_version', 'unknown')} validated against schema[/green]")
        except jsonschema.ValidationError as e:
            self.log.error(f"Spec validation failed: {e.message}")
            raise ValueError(f"Spec validation failed: {e.message}")
        template_errors = TemplateValidator(prompts_dir="prompts").validate()
        if template_errors:
            joined = " | ".join(template_errors)
            self.log.error(f"Prompt template validation failed: {joined}")
            raise ValueError(f"Prompt template validation failed: {joined}")
        
        self.memory    = MemoryStore()
        self.prompts   = PromptManager(self.memory, prompts_dir="prompts")
        self.llm       = LLMClient(spec_path)
        self.orchestrator_model = self.llm.model_for_role("critic")
        pipeline_conf = self.spec.get("pipeline", {})
        raw_timeout_total = pipeline_conf.get("timeout_total_seconds")
        self.timeout_total_seconds = (
            int(raw_timeout_total)
            if raw_timeout_total not in (None, "")
            else None
        )
        raw_max_iterations = pipeline_conf.get("max_iterations", self.MAX_ITERATIONS)
        try:
            self.max_iterations = max(1, int(raw_max_iterations))
        except (TypeError, ValueError):
            self.max_iterations = self.MAX_ITERATIONS
        raw_max_stagnant_iterations = pipeline_conf.get("max_stagnant_iterations", 2)
        try:
            self.max_stagnant_iterations = max(1, int(raw_max_stagnant_iterations))
        except (TypeError, ValueError):
            self.max_stagnant_iterations = 2
        raw_max_research_enrichments = pipeline_conf.get("max_research_enrichments", 1)
        try:
            self.max_research_enrichments = max(0, int(raw_max_research_enrichments))
        except (TypeError, ValueError):
            self.max_research_enrichments = 1
        llm_conf = self.spec.get("llm", {})
        context_length = llm_conf.get("context_length", self.spec.get("ollama", {}).get("context_length", {}))
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        self.orchestrator_ctx_len = context_length.get("critic", context_length.get("default", 8192))
        self.orchestrator_temp = temperatures.get("critic", 0.0)
        self.orchestrator_timeout = timeouts.get("critic", timeouts.get("default", 300))

        # lê config do scraper do spec
        scraper_conf = self.spec.get("research", {}).get("scraper", {})
        search_cache_conf = self.spec.get("research", {}).get("search_cache", {})
        search_tool  = SearchTool(
            results_per_query=search_cache_conf.get("results_per_query", 8),
            cache_enabled=search_cache_conf.get("enabled", True),
            cache_ttl_seconds=search_cache_conf.get("ttl_seconds", 86400),
            cache_path=search_cache_conf.get("path", ".memory/search_cache.json"),
        )
        scraper_tool = create_scraper(
            max_chars=scraper_conf.get("max_chars_per_page", 4000),
            timeout=scraper_conf.get("timeout_seconds", 15),
            compliant_mode=scraper_conf.get("compliant_mode", True),
            max_retries=scraper_conf.get("max_retries", 2),
            provider=scraper_conf.get("provider", "auto"),
        )

        self.chroma = ResearchChroma()
        self.researcher = ResearcherSkill(
            search_tool,
            scraper_tool,
            self.memory,
            spec_path,
            pipeline_logger=self.log,
            chroma=self.chroma,
        )
        self.analyst    = AnalystSkill(self.memory, spec_path, chroma=self.chroma)
        self.writer     = WriterSkill(self.memory, spec_path, chroma=self.chroma)
        self.critic     = CriticSkill(self.memory, spec_path, chroma=self.chroma)
        relevance_conf = self.spec.get("research", {}).get("relevance_filter", {})
        self.relevance_filter = RelevanceFilterSkill(
            self.memory,
            max_urls=int(relevance_conf.get("max_urls", 30)),
            embedding_fn=self._build_embedding_fn() if relevance_conf.get("rerank", True) else None,
        )
        self.evidence_builder = EvidenceBuilderSkill(
            self.memory,
            max_urls=int(relevance_conf.get("max_urls", 30)),
        )
        self.router     = ToolTypeRouter()
        self.orchestrator = LangGraphOrchestrator(self)
        self._sanitizer = ArticleSanitizer(self.spec)
        self._enrichment = EnrichmentCoordinator(self)

        os.makedirs("output", exist_ok=True)
        os.makedirs("artigos", exist_ok=True)

    def run(
        self,
        ferramentas: str,
        contexto:    str,
        foco:        str = "comparação geral",
        questoes:    list[str] | None = None,
        refresh_search: bool = False,
        urls:        list[str] | None = None,
        skip_search: bool = False,
        existing_research: str | None = None,
    ) -> str:
        questoes = questoes or []
        started_at = monotonic()
        article = ""
        iteration = 0
        evaluation = {"approved": False, "problems": [], "correction_prompt": ""}
        pipeline_status = "running"

        try:
            final_state = self.orchestrator.run({
                "ferramentas": ferramentas,
                "contexto": contexto,
                "foco": foco,
                "questoes": questoes,
                "refresh_search": refresh_search,
                "urls": urls,
                "skip_search": skip_search,
                "existing_research": existing_research,
                "started_at": started_at,
            })
            article = final_state.get("article", "") or article
            iteration = final_state.get("iteration", iteration)
            evaluation = final_state.get("evaluation", evaluation)
            pipeline_status = final_state.get("pipeline_status", pipeline_status)
        except TimeoutException as exc:
            pipeline_status = "timeout_recovered"
            self.log.error(str(exc))
            self.memory.log_event("pipeline_timeout_total", {
                "ferramentas": ferramentas,
                "foco": foco,
                "timeout_total_seconds": self.timeout_total_seconds,
                "elapsed_seconds": round(monotonic() - started_at, 2),
            })
            if not article:
                article = (
                    "# Timeout\n\n"
                    f"Pipeline excedeu timeout total de {self.timeout_total_seconds}s."
                )

        # ---- save ----
        slug = ferramentas.lower().replace(" ", "-").replace(",", "")[:40]
        ts   = datetime.now().strftime("%Y%m%d_%H%M")
        path = f"artigos/{slug}_{ts}.md"

        Path(path).write_text(article, encoding="utf-8")

        metrics = {
            "ferramentas": ferramentas,
            "foco":        foco,
            "perguntas":   len(questoes),
            "iterações":   iteration,
            "aprovado":    evaluation["approved"],
            "output":      path,
        }
        self.log.metrics(metrics)
        self.log.saved(path)

        self.save_metrics(ferramentas, path, evaluation["approved"], foco)
        if pipeline_status == "running":
            pipeline_status = "completed"
        elapsed = round(monotonic() - started_at, 2)
        self.save_chain_pipeline_summary(
            ferramentas=ferramentas,
            foco=foco,
            output_path=path,
            pipeline_status=pipeline_status,
            elapsed_seconds=elapsed,
            evaluation=evaluation,
            iteration=iteration,
        )
        return path

    def _build_embedding_fn(self):
        try:
            collection = self.chroma.collection
            embed_fn = getattr(collection, "_embedding_function", None)
            if embed_fn is None:
                return None
            return lambda texts: list(embed_fn(texts))
        except Exception:
            return None

    def initialize_run_context(self, ferramentas: str, contexto: str, foco: str, questoes: list[str]):
        self.log.pipeline_start(ferramentas, contexto)
        if self.log.verbosity == "detailed":
            self.log.console.print(
                f"   [dim]Foco: {foco} | "
                f"Perguntas: {len(questoes)}[/dim]\n"
            )

        self.memory.set("ferramentas", ferramentas)
        self.memory.set("contexto", contexto)
        self.memory.set("foco", foco)
        self.memory.set("questoes", questoes)

        route = self.router.classify(ferramentas, foco)
        self.memory.set("route", route)
        self.memory.log_event("router_classified", {
            "ferramentas": ferramentas,
            "tool_type": route.get("tool_type"),
            "can_parallelize_analysis": route.get("can_parallelize_analysis"),
            "analysis_aspects": route.get("analysis_aspects"),
        })

        self.memory.log_event("pipeline_start", {
            "ferramentas": ferramentas,
            "contexto": contexto,
            "foco": foco,
            "questoes": questoes,
        })

    @staticmethod
    def extract_json_object(raw_text: str) -> dict:
        return extract_json_object(raw_text)

    def decide_retry_or_finalize(self, **kw) -> dict:
        from orchestration.decision import decide_retry_or_finalize
        return decide_retry_or_finalize(self, **kw)

    def run_research_stage(
        self,
        ferramentas: str,
        foco: str,
        questoes: list[str],
        started_at: float,
        refresh_search: bool = False,
        urls: list[str] | None = None,
        skip_search: bool = False,
    ) -> str:
        from pipeline_stages.research import run_research_stage
        return run_research_stage(
            self,
            ferramentas=ferramentas,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
            refresh_search=refresh_search,
            urls=urls,
            skip_search=skip_search,
        )

    def run_research_for_tool(
        self,
        tool: str,
        alternative_tool: str,
        foco: str,
        questoes: list[str],
        refresh_search: bool = False,
        targeted_questions_only: bool = False,
        urls: list[str] | None = None,
        skip_search: bool = False,
    ) -> str:
        from pipeline_stages.research import run_research_for_tool
        return run_research_for_tool(
            self,
            tool=tool,
            alternative_tool=alternative_tool,
            foco=foco,
            questoes=questoes,
            refresh_search=refresh_search,
            targeted_questions_only=targeted_questions_only,
            urls=urls,
            skip_search=skip_search,
        )

    def log_weak_research_warning(self, research_quality: str):
        if research_quality != "weak":
            return
        if self.log.verbosity == "detailed":
            self.log.console.print(
                "   [yellow]⚠ Research fraco — poucos dados concretos encontrados[/yellow]"
            )

    def run_relevance_filter_stage(self, research: str, started_at: float) -> str:
        from pipeline_stages.relevance import run_relevance_filter_stage
        return run_relevance_filter_stage(self, research=research, started_at=started_at)

    def run_evidence_stage(
        self,
        research: str,
        ferramentas: str,
        foco: str,
        started_at: float,
    ):
        from pipeline_stages.evidence import run_evidence_stage
        return run_evidence_stage(
            self,
            research=research,
            ferramentas=ferramentas,
            foco=foco,
            started_at=started_at,
        )

    def run_analysis_stage(
        self,
        research: str,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        started_at: float,
    ) -> str:
        from pipeline_stages.analysis import run_analysis_stage
        return run_analysis_stage(
            self,
            research=research,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
        )

    def enrich_analysis_with_tips(self, analysis: str, ferramentas: str, foco: str) -> str:
        return self._enrichment.enrich_analysis_with_tips(analysis, ferramentas, foco)

    def should_enrich_research_after_critic_failure(self, evaluation: dict, research_quality: str) -> bool:
        return self._enrichment.should_enrich_research_after_critic_failure(evaluation, research_quality)

    def normalize_text_for_match(self, text: str) -> str:
        return self._sanitizer.normalize_text_for_match(text)

    def question_requires_metric_evidence(self, question: str) -> bool:
        from validators.question_coverage import question_requires_metric_evidence
        return question_requires_metric_evidence(self, question)

    def has_numeric_or_no_data_evidence(self, article: str, question: str) -> bool:
        from validators.question_coverage import has_numeric_or_no_data_evidence
        return has_numeric_or_no_data_evidence(self, article, question)

    def validate_question_coverage(self, article: str, questoes: list[str]) -> dict:
        from validators.question_coverage import validate_question_coverage
        return validate_question_coverage(self, article, questoes)

    def enrich_research_and_analysis_for_critic(self, ferramentas, contexto, foco, questoes, started_at, enrichment_number, evaluation):
        return self._enrichment.enrich_research_and_analysis_for_critic(ferramentas, contexto, foco, questoes, started_at, enrichment_number, evaluation)

    def build_targeted_research_questions(self, evaluation: dict) -> list[str]:
        return self._enrichment.build_targeted_research_questions(evaluation)

    def _build_targeted_research_questions_fallback(self, evaluation: dict) -> list[str]:
        return self._enrichment._build_targeted_research_questions_fallback(evaluation)

    def log_memory_hit_if_available(self):
        lessons = self.memory.get_lessons_for_prompt()
        if not lessons:
            return
        lesson_line = next(
            (lesson for lesson in lessons.splitlines() if lesson.startswith("-")),
            lessons.splitlines()[0],
        )
        self.log.memory_hit(lesson_line)

    def run_writer_iteration(
        self,
        iteration: int,
        research: str,
        analysis: str,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        correction_instructions: str,
        research_quality: str,
    ) -> str:
        from pipeline_stages.writer import run_writer_iteration
        return run_writer_iteration(
            self,
            iteration=iteration,
            research=research,
            analysis=analysis,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            correction_instructions=correction_instructions,
            research_quality=research_quality,
        )

    def run_critic_iteration(
        self,
        article: str,
        ferramentas: str,
        started_at: float,
        iteration: int,
    ) -> dict:
        from pipeline_stages.critic import run_critic_iteration
        return run_critic_iteration(
            self,
            article=article,
            ferramentas=ferramentas,
            started_at=started_at,
            iteration=iteration,
        )

    def handle_approved_article(
        self,
        iteration: int,
        evaluation: dict,
        correction_instructions: str,
        ferramentas: str,
        foco: str,
    ):
        self.log.critic_passed(
            evaluation.get("layer", ""),
            evaluation.get("warnings", []),
        )
        self.memory.log_event("article_approved", {
            "iteration": iteration,
            "ferramentas": ferramentas,
            "foco": foco,
        })
        if iteration <= 1:
            return
        pattern = self.extract_correction_pattern(correction_instructions)
        self.memory.learn(
            problem_pattern=pattern,
            solution=f"Resolvido em {iteration} iterações",
            context=f"{ferramentas} | foco: {foco}",
        )

    def extract_correction_pattern(self, correction_instructions: str) -> str:
        problems = [
            line.strip()
            for line in correction_instructions.splitlines()
            if line.strip() and line.strip()[0].isdigit()
        ]
        return "; ".join(problems)[:150] if problems else correction_instructions[:150]

    def update_stagnation_state(self, evaluation, previous_problem_signature, stagnant_iterations):
        from orchestration.decision import update_stagnation_state
        return update_stagnation_state(self, evaluation, previous_problem_signature, stagnant_iterations)

    def should_stop_for_stagnation(self, stagnant_iterations, iteration, ferramentas, evaluation):
        from orchestration.decision import should_stop_for_stagnation
        return should_stop_for_stagnation(self, stagnant_iterations, iteration, ferramentas, evaluation)

    def parse_tools(self, ferramentas: str) -> list[str]:
        return [
            tool_name.strip()
            for tool_name in ferramentas.lower().replace(" e ", ",").split(",")
            if tool_name.strip()
        ]

    def assess_research_quality(self, research: str) -> str:
        """Retorna 'weak' se o research não tem dados suficientes."""
        indicators = 0
        lower = research.lower()
        # tem URLs reais?
        import re
        urls = re.findall(r'https?://[^\s]+', research)
        if len(urls) >= 5:
            indicators += 1
        # tem blocos de código?
        if research.count("```") >= 4:
            indicators += 1
        # tem conteúdo extraído (não só snippets)?
        if "conteúdo extraído" in lower or "conteúdo:" in lower:
            indicators += 1
        # não tem muitos scrape_falhou?
        fail_count = lower.count("scrape_falhou")
        if fail_count <= 2:
            indicators += 1
        return "ok" if indicators >= 3 else "weak"

    def sanitize_article(self, article: str) -> str:
        return self._sanitizer.sanitize_article(article)

    def sanitize_question_answer_evidence_urls(self, article: str) -> str:
        return self._sanitizer.sanitize_question_answer_evidence_urls(article)

    def extract_reference_urls(self, article: str) -> set[str]:
        return self._sanitizer.extract_reference_urls(article)

    def handle_incomplete_commands(self, article: str) -> str:
        return self._sanitizer.handle_incomplete_commands(article)

    def save_debug(self, stage: str, content: str):
        Path(f"output/debug_{stage}.md").write_text(content, encoding="utf-8")

    def save_research_history(self, tool: str, research: str):
        """Save research to tool-specific file for historical reuse (no truncation)."""
        Path("output").mkdir(exist_ok=True)
        tool_safe = tool.lower().replace(" ", "_")
        filepath = Path(f"output/debug_research_{tool_safe}.md")
        filepath.write_text(research, encoding="utf-8")
        self.log.console.print(f"   [cyan]Pesquisa salva em:[/cyan] {filepath}")

    def load_research_history(self, tool: str) -> str | None:
        """Load research from tool-specific file if it exists."""
        tool_safe = tool.lower().replace(" ", "_")
        filepath = Path(f"output/debug_research_{tool_safe}.md")
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return None

    def list_research_files(self) -> list[tuple[str, str, int]]:
        """List all saved research files: [(filename, tool, size_bytes)]."""
        output_dir = Path("output")
        files = []
        for f in sorted(output_dir.glob("debug_research_*.md")):
            tool = f.stem.replace("debug_research_", "")
            size = f.stat().st_size
            files.append((f.name, tool, size))
        return files

    def save_metrics(self, ferramentas, path, approved, foco):
        entry = {
            "ts":          datetime.now().isoformat(),
            "ferramentas": ferramentas,
            "foco":        foco,
            "output":      path,
            "approved":    approved,
        }
        with open("output/metrics.json", "a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

    def save_chain_pipeline_summary(
        self,
        ferramentas: str,
        foco: str,
        output_path: str,
        pipeline_status: str,
        elapsed_seconds: float,
        evaluation: dict,
        iteration: int,
    ):
        """Persist run-level synthesis/eval summary linked to per-tool chain artifacts."""
        try:
            chain_runs = {}
            if hasattr(self.researcher, "get_chain_runs"):
                chain_runs = self.researcher.get_chain_runs()

            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_dir = Path("output/chains/pipeline")
            summary_dir.mkdir(parents=True, exist_ok=True)
            summary_path = summary_dir / f"{run_id}.json"
            payload = {
                "run_id": run_id,
                "ferramentas": ferramentas,
                "foco": foco,
                "pipeline_status": pipeline_status,
                "elapsed_seconds": elapsed_seconds,
                "iteration": iteration,
                "output_path": output_path,
                "evaluation": {
                    "approved": bool(evaluation.get("approved")),
                    "problems": evaluation.get("problems", []),
                },
                "chain_runs": chain_runs,
                "generated_at": datetime.now().isoformat(),
            }
            summary_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self.memory.log_event("chain_pipeline_saved", {
                "path": str(summary_path),
                "tool_runs": len(chain_runs),
            })
        except Exception as exc:
            self.memory.log_event("chain_pipeline_save_failed", {
                "error": str(exc),
            })

    def enforce_global_timeout(self, started_at: float, stage: str):
        if not self.timeout_total_seconds:
            return
        elapsed = monotonic() - started_at
        if elapsed <= self.timeout_total_seconds:
            return
        raise TimeoutException(
            "Pipeline timeout total excedido "
            f"({elapsed:.1f}s > {self.timeout_total_seconds}s) durante {stage}"
        )

    def normalize_problem_signature(self, problems: list[str]) -> tuple[str, ...]:
        from orchestration.decision import normalize_problem_signature
        return normalize_problem_signature(self, problems)
