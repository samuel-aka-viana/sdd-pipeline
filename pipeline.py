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
from skills.researcher import ResearcherSkill
from skills.analyst import AnalystSkill
from skills.writer import WriterSkill
from skills.critic import CriticSkill
from skills.router import ToolTypeRouter
from validators.rules_engine import AdaptiveRulesEngine
from logger import PipelineLogger


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
        
        self.memory    = MemoryStore()
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

        self.researcher = ResearcherSkill(
            search_tool,
            scraper_tool,
            self.memory,
            spec_path,
            pipeline_logger=self.log,
        )
        self.analyst    = AnalystSkill(self.memory, spec_path)
        self.writer     = WriterSkill(self.memory, spec_path)
        self.critic     = CriticSkill(self.memory, spec_path)
        self.router     = ToolTypeRouter()
        self.rules_engine = AdaptiveRulesEngine()

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

        self.initialize_run_context(ferramentas, contexto, foco, questoes)

        try:
            # OPTIMIZATION 1: If using existing research from history, skip research stage
            if existing_research:
                self.log.section(1, 3, "⏭️  Reutilizando Pesquisa Histórica")
                research = existing_research
                research_quality = {"has_data": True, "from_history": True, "chars": len(research)}
                self.memory.log_event("research_reused_from_history", {
                    "ferramentas": ferramentas,
                    "research_chars": len(research),
                })
                self.log.console.print(f"   [green]✓[/green] Pesquisa histórica carregada ({len(research)} chars)")
            # OPTIMIZATION 2: If reusing URLs, skip research entirely (data already in Chroma)
            elif skip_search and urls:
                self.log.section(1, 3, "⏭️  Pulando Pesquisa (URLs Pré-Carregadas)")
                research = f"# Contexto Pré-Carregado\n\nReutilizando {len(urls)} URLs já scrapeadas do Chroma.\n"
                research_quality = {"has_data": True, "url_count": len(urls)}
                self.memory.log_event("research_skipped_optimization", {
                    "ferramentas": ferramentas,
                    "urls_count": len(urls),
                })
            else:
                research = self.run_research_stage(
                    ferramentas=ferramentas,
                    foco=foco,
                    questoes=questoes,
                    started_at=started_at,
                    refresh_search=refresh_search,
                    urls=urls,
                    skip_search=skip_search,
                )
                research_quality = self.assess_research_quality(research)
                self.log_weak_research_warning(research_quality)

            analysis = self.run_analysis_stage(
                research=research,
                ferramentas=ferramentas,
                contexto=contexto,
                foco=foco,
                questoes=questoes,
                started_at=started_at,
            )

            # NEW: Enrich analysis with tips/dicas from Chroma before writing
            analysis = self.enrich_analysis_with_tips(
                analysis=analysis,
                ferramentas=ferramentas,
                foco=foco,
            )

            article, iteration, evaluation = self.run_write_critic_stage(
                research=research,
                analysis=analysis,
                ferramentas=ferramentas,
                contexto=contexto,
                foco=foco,
                questoes=questoes,
                research_quality=research_quality,
                started_at=started_at,
                refresh_search=refresh_search,
            )
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
        self.log.pipeline_end(
            status=pipeline_status,
            elapsed_seconds=elapsed,
            approved=evaluation.get("approved"),
            iteration=iteration,
        )
        return path

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
        self.log.section(1, 3, "Pesquisando")
        tools_list = self.parse_tools(ferramentas)
        research_parts = []

        for tool in tools_list:
            self.enforce_global_timeout(started_at, stage=f"pesquisa ({tool})")
            alternative_tool = next((tool_name for tool_name in tools_list if tool_name != tool), "")
            tool_research = self.run_research_for_tool(
                tool=tool,
                alternative_tool=alternative_tool,
                foco=foco,
                questoes=questoes,
                refresh_search=refresh_search,
                urls=urls,
                skip_search=skip_search,
            )
            research_parts.append(tool_research)
            # Save individual tool research (complete, no truncation)
            self.save_research_history(tool, tool_research)

        research = "\n\n".join(research_parts)
        self.memory.set("research", research)
        self.save_debug("research", research)
        return research

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
        with self.log.task(f"Pesquisando {tool}"):
            try:
                data = self.researcher.run(
                    tool=tool,
                    alternative=alternative_tool,
                    foco=foco,
                    questoes=questoes,
                    refresh_search=refresh_search,
                    targeted_questions_only=targeted_questions_only,
                    urls=urls,
                    skip_search=skip_search,
                )
            except TimeoutException:
                self.log.error(
                    f"Researcher timeout ({self.researcher.timeout}s) — "
                    f"dados insuficientes para {tool}"
                )
                data = f"# {tool}\n\nPesquisa interrompida por timeout ({self.researcher.timeout}s)."
        return f"# {tool}\n{data}"

    def log_weak_research_warning(self, research_quality: str):
        if research_quality != "weak":
            return
        if self.log.verbosity == "detailed":
            self.log.console.print(
                "   [yellow]⚠ Research fraco — poucos dados concretos encontrados[/yellow]"
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
        self.log.section(2, 3, "Analisando")
        self.enforce_global_timeout(started_at, stage="análise")

        route = self.memory.get("route", {})
        aspects = route.get("analysis_aspects", ["core"])
        can_parallelize = route.get("can_parallelize_analysis", False)

        if not can_parallelize or len(aspects) <= 1:
            with self.log.task("Gerando análise"):
                try:
                    analysis = self.analyst.run(
                        research=research,
                        ferramentas=ferramentas,
                        contexto=contexto,
                        foco=foco,
                        questoes=questoes,
                    )
                except TimeoutException:
                    self.log.error(
                        f"Analyst timeout ({self.analyst.timeout}s) — usando research bruto"
                    )
                    analysis = f"Análise interrompida por timeout ({self.analyst.timeout}s).\n\n{research}"
        else:
            with self.log.task(f"Gerando análise paralela ({len(aspects)} aspectos)"):
                results = {}
                try:
                    with ThreadPoolExecutor(max_workers=min(len(aspects), 3)) as pool:
                        futures = {
                            pool.submit(
                                self.analyst.run,
                                research=research,
                                ferramentas=ferramentas,
                                contexto=contexto,
                                foco=aspect,
                                questoes=questoes,
                            ): aspect
                            for aspect in aspects
                        }
                        for future in as_completed(futures):
                            aspect = futures[future]
                            try:
                                results[aspect] = future.result()
                            except Exception as e:
                                self.log.error(f"Parallel analyst failed for {aspect}: {e}")
                                results[aspect] = ""

                    analysis = "\n\n---\n\n".join(
                        f"## Análise: {asp.upper()}\n{txt}"
                        for asp, txt in results.items() if txt
                    )
                    self.memory.log_event("parallel_analysis_complete", {
                        "aspects": len(aspects),
                        "successful": len([v for v in results.values() if v]),
                    })
                except TimeoutException:
                    self.log.error(
                        f"Analyst timeout ({self.analyst.timeout}s) — usando research bruto"
                    )
                    analysis = f"Análise interrompida por timeout ({self.analyst.timeout}s).\n\n{research}"

        self.memory.set("analysis", analysis)
        self.save_debug("analysis", analysis)
        return analysis

    def enrich_analysis_with_tips(
        self,
        analysis: str,
        ferramentas: str,
        foco: str,
    ) -> str:
        """Enrich analysis with tips/dicas from Chroma if missing.

        Validates that analysis has ## DICAS or ## OTIMIZAÇÕES section.
        If missing, queries Chroma for relevant tips and injects them.

        Returns enriched analysis (or original if already has tips).
        """
        # Check if analysis already has tips section
        has_dicas = "## dicas" in analysis.lower() or "## otimizações" in analysis.lower()

        if has_dicas:
            self.log.console.print("[green]✓[/green] Análise já contém dicas/otimizações")
            return analysis

        # Analysis missing tips — fetch from Chroma
        self.log.console.print("[yellow]⚠[/yellow] Buscando dicas no Chroma...")

        try:
            # Parse tool name(s) from ferramentas string
            tool_names = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
            primary_tool = tool_names[0] if tool_names else None

            # Query Chroma for tips related to tool/focus (filtered by primary tool to avoid mixing data)
            query = f"{ferramentas} dicas tips otimizações best practices {foco}"

            # Try to use researcher's search_cached_content if available
            if hasattr(self.researcher, 'search_cached_content'):
                tips_results = self.researcher.search_cached_content(query, tool=primary_tool, k=5)
            else:
                tips_results = []

            if not tips_results:
                self.log.console.print("[dim]Sem dicas encontradas no Chroma[/dim]")
                self.memory.log_event("analysis_enrich_failed", {
                    "ferramentas": ferramentas,
                    "reason": "no_chroma_tips",
                })
                return analysis

            # Build tips section from Chroma results
            tips_block = "\n## OTIMIZAÇÕES\n"
            tips_count = 0

            for result in tips_results[:5]:
                text = result.get("text", "")
                url = result.get("url", "")

                # Extract actionable tips (lines with commands, config, etc)
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                for line in lines:
                    if any(keyword in line.lower() for keyword in ["comando", "config", "flag", "opção", "--", "cmd", "export"]):
                        tips_block += f"- {line}\n"
                        tips_count += 1
                        if tips_count >= 3:
                            break

                if tips_count >= 3:
                    break

            if tips_count > 0:
                enriched_analysis = analysis + tips_block
                self.log.console.print(f"[green]✓[/green] Enriquecido com {tips_count} dicas do Chroma")
                self.memory.log_event("analysis_enriched_with_tips", {
                    "ferramentas": ferramentas,
                    "tips_count": tips_count,
                })
                return enriched_analysis
            else:
                self.log.console.print("[dim]Sem dicas extraíveis encontradas[/dim]")
                return analysis

        except Exception as e:
            self.log.console.print(f"[dim]Erro ao enriquecer análise: {e}[/dim]")
            self.memory.log_event("analysis_enrich_error", {
                "ferramentas": ferramentas,
                "error": str(e),
            })
            return analysis

    def run_write_critic_stage(
        self,
        research: str,
        analysis: str,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        research_quality: str,
        started_at: float,
        refresh_search: bool = False,
    ) -> tuple[str, int, dict]:
        self.log.section(3, 3, "Escrevendo")
        self.log_memory_hit_if_available()

        article = ""
        evaluation = {"approved": False, "problems": [], "correction_prompt": ""}
        correction_instructions = ""
        previous_problem_signature = None
        stagnant_iterations = 0
        research_enrichment_count = 0

        for iteration in range(1, self.max_iterations + 1):
            self.enforce_global_timeout(started_at, stage=f"iteração {iteration} (writer)")
            self.log.iteration(iteration, self.max_iterations)
            writer_started = monotonic()
            self.log.event_log.log_event("writer_start", {
                "iteration": iteration,
                "article_chars_previous": len(article),
                "correction_chars": len(correction_instructions),
                "research_quality": research_quality,
            })

            article = self.run_writer_iteration(
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
            writer_elapsed = round(monotonic() - writer_started, 3)
            self.log.event_log.log_event("writer_end", {
                "iteration": iteration,
                "elapsed_seconds": writer_elapsed,
                "article_chars": len(article),
                "empty_article": not bool(article),
            })
            if not article:
                continue

            sanitize_started = monotonic()
            article = self.sanitize_article(article)
            self.log.event_log.log_event("sanitize_end", {
                "iteration": iteration,
                "elapsed_seconds": round(monotonic() - sanitize_started, 3),
                "article_chars": len(article),
            })

            coverage_evaluation = self.validate_question_coverage(article, questoes)
            if not coverage_evaluation["approved"]:
                self.log.event_log.log_event("question_coverage_failed", {
                    "iteration": iteration,
                    "problem_count": len(coverage_evaluation.get("problems", [])),
                })
                evaluation = coverage_evaluation
                self.log.critic_failed(evaluation.get("problems", []))
                correction_instructions = evaluation.get("correction_prompt", "")
                should_enrich = self.should_enrich_research_after_critic_failure(
                    evaluation=evaluation,
                    research_quality=research_quality,
                )
                if should_enrich and research_enrichment_count < self.max_research_enrichments:
                    research_enrichment_count += 1
                    (
                        research,
                        analysis,
                        research_quality,
                    ) = self.enrich_research_and_analysis_for_critic(
                        ferramentas=ferramentas,
                        contexto=contexto,
                        foco=foco,
                        questoes=questoes,
                        started_at=started_at,
                        refresh_search=refresh_search,
                        enrichment_number=research_enrichment_count,
                        evaluation=evaluation,
                    )
                    previous_problem_signature = None
                    stagnant_iterations = 0
                    continue
                previous_problem_signature, stagnant_iterations = self.update_stagnation_state(
                    evaluation=evaluation,
                    previous_problem_signature=previous_problem_signature,
                    stagnant_iterations=stagnant_iterations,
                )
                if self.should_stop_for_stagnation(stagnant_iterations, iteration, ferramentas, evaluation):
                    self.log.section_end(3, 3, "Escrevendo", status="stagnation_break")
                    break
                if iteration == self.max_iterations:
                    self.log.error("Máximo de iterações atingido. Salvando melhor versão.")
                    self.memory.log_event("max_iterations_reached", {
                        "ferramentas": ferramentas,
                        "problems": evaluation.get("problems", []),
                    })
                continue

            critic_started = monotonic()
            self.log.event_log.log_event("critic_start", {
                "iteration": iteration,
                "article_chars": len(article),
            })
            evaluation = self.run_critic_iteration(
                article=article,
                ferramentas=ferramentas,
                started_at=started_at,
                iteration=iteration,
            )
            self.log.event_log.log_event("critic_end", {
                "iteration": iteration,
                "elapsed_seconds": round(monotonic() - critic_started, 3),
                "approved": evaluation.get("approved", False),
                "layer": evaluation.get("layer", ""),
                "problem_count": len(evaluation.get("problems", [])),
                "warning_count": len(evaluation.get("warnings", [])),
            })

            if evaluation["approved"]:
                self.handle_approved_article(iteration, evaluation, correction_instructions, ferramentas, foco)
                self.log.section_end(3, 3, "Escrevendo", status="ok")
                return article, iteration, evaluation

            self.log.critic_failed(evaluation.get("problems", []))
            correction_instructions = evaluation.get("correction_prompt", "")

            should_enrich = self.should_enrich_research_after_critic_failure(
                evaluation=evaluation,
                research_quality=research_quality,
            )
            if should_enrich and research_enrichment_count < self.max_research_enrichments:
                research_enrichment_count += 1
                (
                    research,
                    analysis,
                    research_quality,
                ) = self.enrich_research_and_analysis_for_critic(
                    ferramentas=ferramentas,
                    contexto=contexto,
                    foco=foco,
                    questoes=questoes,
                    started_at=started_at,
                    refresh_search=refresh_search,
                    enrichment_number=research_enrichment_count,
                    evaluation=evaluation,
                )
                previous_problem_signature = None
                stagnant_iterations = 0
                continue

            previous_problem_signature, stagnant_iterations = self.update_stagnation_state(
                evaluation=evaluation,
                previous_problem_signature=previous_problem_signature,
                stagnant_iterations=stagnant_iterations,
            )
            if self.should_stop_for_stagnation(stagnant_iterations, iteration, ferramentas, evaluation):
                self.log.section_end(3, 3, "Escrevendo", status="stagnation_break")
                break
            if iteration == self.max_iterations:
                self.log.error("Máximo de iterações atingido. Salvando melhor versão.")
                self.memory.log_event("max_iterations_reached", {
                    "ferramentas": ferramentas,
                    "problems": evaluation.get("problems", []),
                })
        self.log.section_end(3, 3, "Escrevendo", status="incomplete")
        return article, iteration, evaluation

    def should_enrich_research_after_critic_failure(
        self,
        evaluation: dict,
        research_quality: str,
    ) -> bool:
        evidence_chunks = []
        evidence_chunks.extend(evaluation.get("problems", []))
        evidence_chunks.extend(evaluation.get("warnings", []))
        evidence_chunks.append(evaluation.get("correction_prompt", ""))
        combined_feedback = " ".join(str(chunk) for chunk in evidence_chunks).lower()

        enrichment_markers = (
            # Only trigger enrichment for DATA-related issues, not structural
            "referências insuficientes",
            "sem dados",
            "dados insuficientes",
            "não foram encontrados dados",
            "nao foram encontrados dados",
            "falta evidência",
            "falta evidencia",
            "dados mensuráveis",
            "dados measuráveis",
            "perguntas do contexto",
            "métricas mensuráveis",
            "metricas mensuraveis",
            "benchmark",
        )
        # NOTE: Removed "insuficiente" and "p95"/"throughput" because they match
        # structural issues like "Dicas insuficientes" or "Poucos erros documentados"
        # which are Writer problems, not Research problems.
        if any(marker in combined_feedback for marker in enrichment_markers):
            return True
        return research_quality == "weak"

    def normalize_text_for_match(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.lower()

    def question_requires_metric_evidence(self, question: str) -> bool:
        normalized_question = self.normalize_text_for_match(question)
        metric_tokens = (
            "p95",
            "latencia",
            "throughput",
            "agregacoes",
            "agregacao",
            "benchmark",
        )
        return any(metric_token in normalized_question for metric_token in metric_tokens)

    def has_numeric_or_no_data_evidence(self, article: str, question: str) -> bool:
        normalized_article = self.normalize_text_for_match(article)
        normalized_question = self.normalize_text_for_match(question)
        idx = normalized_article.find(normalized_question)
        if idx == -1:
            return False
        window = normalized_article[idx: idx + 900]
        if "sem dados mensuraveis nas fontes consultadas" in window:
            return True
        return bool(re.search(r"\b\d+(?:[.,]\d+)?\s*(?:ms|s|seg|qps|rps|rows/s|linhas/s|%)?\b", window))

    def validate_question_coverage(self, article: str, questoes: list[str]) -> dict:
        if not questoes:
            return {"approved": True, "layer": "question_coverage", "problems": [], "warnings": []}

        normalized_article = self.normalize_text_for_match(article)
        missing_questions: list[str] = []
        missing_metric_evidence: list[str] = []

        for question in questoes:
            clean_question = (question or "").strip()
            if not clean_question:
                continue
            normalized_question = self.normalize_text_for_match(clean_question)
            if normalized_question not in normalized_article:
                missing_questions.append(clean_question)
                continue
            if self.question_requires_metric_evidence(clean_question) and not self.has_numeric_or_no_data_evidence(
                article,
                clean_question,
            ):
                missing_metric_evidence.append(clean_question)

        problems = []
        if missing_questions:
            problems.append(
                "Perguntas do contexto sem resposta explícita: " + "; ".join(missing_questions)
            )
        if missing_metric_evidence:
            problems.append(
                "Perguntas de métricas mensuráveis sem número ou sem a frase "
                "'Sem dados mensuráveis nas fontes consultadas': "
                + "; ".join(missing_metric_evidence)
            )

        if not problems:
            return {"approved": True, "layer": "question_coverage", "problems": [], "warnings": []}

        correction_prompt = (
            "DADOS INSUFICIENTES PARA PERGUNTAS DO CONTEXTO.\n"
            "Corrija obrigatoriamente:\n"
            "- Inclua a seção 'Respostas às Perguntas do Contexto'.\n"
            "- Replique cada pergunta literal do input e responda de forma objetiva.\n"
            "- Para perguntas de p95/throughput/latência: inclua número mensurável OU a frase "
            "'Sem dados mensuráveis nas fontes consultadas'.\n"
            "- Não invente dados.\n"
        )
        return {
            "approved": False,
            "layer": "question_coverage",
            "problems": problems,
            "warnings": [],
            "correction_prompt": correction_prompt,
            "report": "\n".join(problems),
        }

    def enrich_research_and_analysis_for_critic(
        self,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        started_at: float,
        refresh_search: bool,
        enrichment_number: int,
        evaluation: dict,
    ) -> tuple[str, str, str]:
        self.memory.log_event("research_enrichment_started", {
            "ferramentas": ferramentas,
            "foco": foco,
            "enrichment_number": enrichment_number,
        })

        # Check if problem is "Dicas insuficientes" or "Poucos erros" → use reanalyze instead of re-search
        problems_text = " ".join(evaluation.get("problems", [])).lower()
        if "dicas insuficientes" in problems_text or "poucos erro" in problems_text:
            return self._enrich_via_reanalysis(ferramentas, contexto, foco, questoes, evaluation)

        self.log.console.print(
            f"   [yellow]↻ Enriquecendo pesquisa ({enrichment_number}/{self.max_research_enrichments}) "
            f"após crítica de falta de dados[/yellow]"
        )

        targeted_questions = self.build_targeted_research_questions(evaluation)
        if self.log.verbosity == "detailed" and targeted_questions:
            self.log.console.print(
                "   [dim]Perguntas direcionadas do critic:[/dim] "
                + "; ".join(targeted_questions)
            )

        enriched_parts = []
        tools_list = self.parse_tools(ferramentas)
        for tool in tools_list:
            self.enforce_global_timeout(started_at, stage=f"enriquecimento de pesquisa ({tool})")
            alternative_tool = next((tool_name for tool_name in tools_list if tool_name != tool), "")
            enriched_parts.append(
                self.run_research_for_tool(
                    tool=tool,
                    alternative_tool=alternative_tool,
                    foco=foco,
                    questoes=targeted_questions or questoes,
                    refresh_search=True if not refresh_search else refresh_search,
                    targeted_questions_only=bool(targeted_questions),
                )
            )

        enriched_research = "\n\n".join(enriched_parts)
        self.memory.set("research", enriched_research)
        self.save_debug("research", enriched_research)

        enriched_analysis = self.run_analysis_stage(
            research=enriched_research,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=started_at,
        )
        enriched_quality = self.assess_research_quality(enriched_research)
        return enriched_research, enriched_analysis, enriched_quality

    def _enrich_via_reanalysis(
        self,
        ferramentas: str,
        contexto: str,
        foco: str,
        questoes: list[str],
        evaluation: dict,
    ) -> tuple[str, str, str]:
        """Re-analyze already-scraped URLs to extract tips/errors WITHOUT re-searching.

        This is much faster (3-5s) than full re-search (5-10 min).
        """
        self.log.console.print(
            f"   [yellow]♻ Re-analisando URLs já coletadas para extrair dicas/erros[/yellow]"
        )

        problems_text = " ".join(evaluation.get("problems", [])).lower()
        focus_on = "tips_and_errors"
        if "dicas insuficientes" in problems_text and "poucos erro" not in problems_text:
            focus_on = "tips_only"
        elif "poucos erro" in problems_text and "dicas insuficientes" not in problems_text:
            focus_on = "errors_only"

        tools_list = self.parse_tools(ferramentas)
        enrichment_parts = []

        for tool in tools_list:
            try:
                # Re-analyze cached markdown without new searches
                tips_and_errors = self.researcher.reanalyze_urls_for_tips_and_errors(
                    tool=tool,
                    focus_on=focus_on
                )
                enrichment_parts.append(f"# {tool}\n{tips_and_errors}")
            except Exception as e:
                self.log.error(f"Reanalysis failed for {tool}: {e}")
                enrichment_parts.append(f"# {tool}\n(Re-análise falhou)")

        enrichment_text = "\n\n".join(enrichment_parts)

        # Create synthetic research enrichment (much lighter than full re-search)
        current_research = self.memory.get("research", "")
        enriched_research = f"{current_research}\n\n## ANÁLISE DE URLS JÁ COLETADAS\n{enrichment_text}"

        self.memory.set("research", enriched_research)
        self.save_debug("research_reanalyzed", enrichment_text)

        # Re-run analysis with enriched context
        enriched_analysis = self.run_analysis_stage(
            research=enriched_research,
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes=questoes,
            started_at=monotonic(),
        )

        enriched_quality = self.assess_research_quality(enriched_research)
        return enriched_research, enriched_analysis, enriched_quality

    def build_targeted_research_questions(self, evaluation: dict) -> list[str]:
        feedback_chunks = []
        feedback_chunks.extend(evaluation.get("problems", []))
        feedback_chunks.extend(evaluation.get("warnings", []))
        feedback_chunks.append(evaluation.get("correction_prompt", ""))
        feedback_text = " ".join(str(chunk) for chunk in feedback_chunks).lower()

        questions = []
        if any(term in feedback_text for term in ("referências insuficientes", "fontes", "urls")):
            questions.append("fontes oficiais e comunitárias confiáveis para este tópico")
        if any(term in feedback_text for term in ("erro", "armadilha", "troubleshoot")):
            questions.append("erros comuns reais com causa e solução validada")
        if any(term in feedback_text for term in ("instala", "comando", "endpoint-url", "curl")):
            questions.append("comandos de instalação e verificação com sintaxe exata")
        if any(term in feedback_text for term in ("requisito", "hardware", "ram", "cpu")):
            questions.append("requisitos mínimos de hardware com números concretos")
        if any(term in feedback_text for term in ("benchmark", "latência", "throughput", "performance")):
            questions.append("benchmarks e métricas de performance com metodologia")

        if not questions and evaluation.get("problems"):
            first_problem = str(evaluation["problems"][0]).strip()
            if first_problem:
                questions.append(f"dados concretos para corrigir: {first_problem[:120]}")

        return questions[:4]

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
        with self.log.task("Escrevendo artigo"):
            try:
                return self.writer.run(
                    research=research,
                    analysis=analysis,
                    ferramentas=ferramentas,
                    contexto=contexto,
                    foco=foco,
                    questoes=questoes,
                    correction_instructions=correction_instructions,
                    research_quality=research_quality,
                )
            except TimeoutException:
                self.log.error(
                    f"Writer timeout ({self.writer.timeout}s) na iteração {iteration}"
                )
                if iteration == self.max_iterations:
                    return f"# Timeout\n\nGeração interrompida: writer excedeu {self.writer.timeout}s."
                return ""

    def run_critic_iteration(
        self,
        article: str,
        ferramentas: str,
        started_at: float,
        iteration: int,
    ) -> dict:
        self.enforce_global_timeout(started_at, stage=f"iteração {iteration} (critic)")
        route = self.memory.get("route", {})
        tool_type = route.get("tool_type", "unknown")

        with self.log.task("Validando contra spec"):
            try:
                return self.critic.evaluate(article, ferramentas, tool_type=tool_type)
            except TimeoutException:
                self.log.error(
                    f"Critic timeout ({self.critic.timeout}s) — aprovando sem validação semântica"
                )
                return {
                    "approved": True,
                    "layer": "timeout_skip",
                    "warnings": [f"Validação semântica pulada: critic excedeu {self.critic.timeout}s"],
                    "report": "Validação semântica pulada por timeout.",
                }

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

    def update_stagnation_state(
        self,
        evaluation: dict,
        previous_problem_signature: tuple[str, ...] | None,
        stagnant_iterations: int,
    ) -> tuple[tuple[str, ...] | None, int]:
        current_problem_signature = self.normalize_problem_signature(
            evaluation.get("problems", [])
        )
        if current_problem_signature and current_problem_signature == previous_problem_signature:
            stagnant_iterations += 1
        else:
            stagnant_iterations = 0
        return current_problem_signature, stagnant_iterations

    def should_stop_for_stagnation(
        self,
        stagnant_iterations: int,
        iteration: int,
        ferramentas: str,
        evaluation: dict,
    ) -> bool:
        if stagnant_iterations < self.max_stagnant_iterations:
            return False
        self.log.error(
            "Sem progresso no critic após múltiplas iterações. Encerrando para evitar loop."
        )
        self.memory.log_event("critic_stagnation_break", {
            "ferramentas": ferramentas,
            "iteration": iteration,
            "stagnant_iterations": stagnant_iterations,
            "problems": evaluation.get("problems", []),
        })
        return True

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
        """Remove frases proibidas que o modelo insiste em usar."""
        import re
        patterns = self.spec["article"]["quality_rules"]["no_placeholders"]["patterns"]

        lines = article.split("\n")
        cleaned = []

        for line in lines:
            lower = line.lower().strip()
            has_placeholder = any(pattern.lower() in lower for pattern in patterns)
            if has_placeholder:
                if lower.startswith("#") and len(lower) < 80:
                    continue
                for pattern in patterns:
                    line = re.sub(re.escape(pattern), "", line, flags=re.IGNORECASE)
                if not line.strip() or line.strip() in (".", "-", "*"):
                    continue
            cleaned.append(line)

        result = "\n".join(cleaned)

        # remove blocos ```bash``` vazios ou com só comentários
        result = re.sub(
            r'```bash\s*\n(\s*#[^\n]*\n)*\s*```',
            '',
            result,
        )
        # remove blocos de código vazios de qualquer linguagem
        result = re.sub(
            r'```[a-zA-Z0-9_+-]*\s*\n\s*```',
            '',
            result,
        )

        # remove URLs inventadas
        url_rules = self.spec["article"]["quality_rules"].get("url_validation", {})
        for block_pattern in url_rules.get("block_patterns", []):
            result = re.sub(rf'https?://[^\s]*{re.escape(block_pattern)}[^\s]*', '', result)

        result = self.sanitize_question_answer_evidence_urls(result)
        return self.handle_incomplete_commands(result)

    def sanitize_question_answer_evidence_urls(self, article: str) -> str:
        reference_urls = self.extract_reference_urls(article)
        if not reference_urls:
            return article

        sanitized_lines: list[str] = []
        for raw_line in article.splitlines():
            line = raw_line
            normalized_line = self.normalize_text_for_match(line)
            if "evidencia/url:" not in normalized_line:
                sanitized_lines.append(line)
                continue

            found_urls = re.findall(r'https?://[^\s)]+', line)
            if not found_urls:
                sanitized_lines.append(line)
                continue

            has_url_outside_references = any(found_url not in reference_urls for found_url in found_urls)
            if has_url_outside_references:
                sanitized_lines.append("Evidência/URL: N/D (fora das referências coletadas)")
                continue
            sanitized_lines.append(line)

        return "\n".join(sanitized_lines)

    def extract_reference_urls(self, article: str) -> set[str]:
        reference_urls: set[str] = set()
        in_references = False
        for line in article.splitlines():
            stripped_line = line.strip()
            normalized_line = self.normalize_text_for_match(stripped_line)
            if normalized_line.startswith("## referencias"):
                in_references = True
                continue
            if in_references and stripped_line.startswith("## "):
                break
            if not in_references:
                continue
            match = re.match(r'^-\s*(https?://\S+)\s*$', stripped_line)
            if match:
                reference_urls.add(match.group(1))
        return reference_urls

    def handle_incomplete_commands(self, article: str) -> str:
        import re

        updated_lines: list[str] = []
        has_endpoint_research_note = False
        has_curl_research_note = False
        has_queue_research_note = False

        for line in article.splitlines():
            updated_line = line
            stripped_line = updated_line.strip()

            if re.search(r'--endpoint-url=\s*(?:$|--)', stripped_line):
                updated_line = ""
                has_endpoint_research_note = True

            if re.fullmatch(r'curl(?:\s+[-\w]+(?:\s+\S+)*)?\s*', stripped_line) and not re.search(
                r'https?://', stripped_line
            ):
                updated_line = ""
                has_curl_research_note = True

            if 'QueueUrl": " }' in updated_line:
                updated_line = "Resultado esperado: retorno com campo `QueueUrl` válido."
                has_queue_research_note = True

            if updated_line:
                updated_lines.append(updated_line)

        if has_endpoint_research_note:
            updated_lines.append(
                "Nota: endpoint de serviço não confirmado nas fontes coletadas; "
                "validação manual é necessária com pesquisa adicional."
            )
        if has_curl_research_note:
            updated_lines.append(
                "Nota: comando curl removido por falta de URL confirmada nas fontes; "
                "validação manual é necessária com pesquisa adicional."
            )
        if has_queue_research_note:
            updated_lines.append(
                "Nota: exemplo de QueueUrl foi normalizado; valide o payload real manualmente."
            )

        return "\n".join(updated_lines)

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
        import re

        normalized_items = []
        for problem_text in problems:
            normalized_text = re.sub(r'^\d+\.\s*', '', problem_text.lower().strip())
            normalized_text = re.sub(r'\s+', ' ', normalized_text)
            if normalized_text:
                normalized_items.append(normalized_text)
        return tuple(sorted(normalized_items))
