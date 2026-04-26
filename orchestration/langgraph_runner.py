from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from time import monotonic
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph


class PipelineState(TypedDict, total=False):
    ferramentas: str
    contexto: str
    foco: str
    questoes: list[str]
    refresh_search: bool
    urls: list[str] | None
    skip_search: bool
    existing_research: str | None
    started_at: float
    pipeline_status: str
    research: str
    research_quality: str
    analysis: str
    article: str
    evaluation: dict[str, Any]
    correction_instructions: str
    iteration: int
    research_enrichment_count: int
    previous_problem_signature: tuple[str, ...] | None
    stagnant_iterations: int
    write_status: str
    status: str
    evidence_pack: Any  # EvidencePack | None


class LangGraphOrchestrator:
    """LangGraph-first orchestration for the full SDD pipeline."""

    def __init__(self, pipeline):
        self.pipeline = pipeline
        self.writer_heartbeat_seconds = max(
            1,
            int(
                self.pipeline.spec.get("pipeline", {}).get("writer_heartbeat_seconds", 10)
            ),
        )
        self.graph = self._build_graph().compile()

    def _build_graph(self):
        graph = StateGraph(PipelineState)
        graph.add_node("bootstrap", self._bootstrap)
        graph.add_node("research", self._research)
        graph.add_node("evidence", self._evidence)
        graph.add_node("analysis", self._analysis)
        graph.add_node("start_write", self._start_write)
        graph.add_node("writer", self._writer)
        graph.add_node("question_coverage", self._question_coverage)
        graph.add_node("critic", self._critic)
        graph.add_node("after_failure", self._after_failure)
        graph.add_node("finalize", self._finalize)

        graph.set_entry_point("bootstrap")
        graph.add_edge("bootstrap", "research")
        graph.add_edge("research", "evidence")
        graph.add_edge("evidence", "analysis")
        graph.add_edge("analysis", "start_write")
        graph.add_edge("start_write", "writer")
        graph.add_edge("writer", "question_coverage")

        graph.add_conditional_edges(
            "question_coverage",
            self._route_after_question_coverage,
            {
                "critic": "critic",
                "after_failure": "after_failure",
            },
        )
        graph.add_conditional_edges(
            "critic",
            self._route_after_critic,
            {
                "finalize": "finalize",
                "after_failure": "after_failure",
            },
        )
        graph.add_conditional_edges(
            "after_failure",
            self._route_after_failure,
            {
                "writer": "writer",
                "finalize": "finalize",
            },
        )
        graph.add_edge("finalize", END)
        return graph

    def run(self, state: PipelineState) -> PipelineState:
        return self.graph.invoke(state)

    def _bootstrap(self, state: PipelineState) -> PipelineState:
        self.pipeline.initialize_run_context(
            ferramentas=state["ferramentas"],
            contexto=state["contexto"],
            foco=state["foco"],
            questoes=state["questoes"],
        )
        self.pipeline.memory.log_event("orchestrator_selected", {"backend": "langgraph"})
        return {
            "pipeline_status": "running",
            "status": "ok",
            "iteration": 0,
            "research_enrichment_count": 0,
            "previous_problem_signature": None,
            "stagnant_iterations": 0,
            "correction_instructions": "",
            "evaluation": {"approved": False, "problems": [], "correction_prompt": ""},
        }

    def _research(self, state: PipelineState) -> PipelineState:
        ferramentas = state["ferramentas"]
        foco = state["foco"]
        questoes = state["questoes"]
        started_at = state["started_at"]
        refresh_search = state.get("refresh_search", False)
        urls = state.get("urls")
        skip_search = state.get("skip_search", False)
        existing_research = state.get("existing_research")

        if existing_research:
            self.pipeline.log.section(1, 3, "⏭️  Reutilizando Pesquisa Histórica")
            research = existing_research
            research_quality = "strong"
            self.pipeline.memory.log_event("research_reused_from_history", {
                "ferramentas": ferramentas,
                "research_chars": len(research),
            })
            self.pipeline.log.console.print(
                f"   [green]✓[/green] Pesquisa histórica carregada ({len(research)} chars)"
            )
        elif skip_search and urls:
            self.pipeline.log.section(1, 3, "⏭️  Pulando Pesquisa (URLs Pré-Carregadas)")
            research = (
                "# Contexto Pré-Carregado\n\n"
                f"Reutilizando {len(urls)} URLs já scrapeadas do Chroma.\n"
            )
            research_quality = "strong"
            self.pipeline.memory.log_event("research_skipped_optimization", {
                "ferramentas": ferramentas,
                "urls_count": len(urls),
            })
        else:
            research = self.pipeline.run_research_stage(
                ferramentas=ferramentas,
                foco=foco,
                questoes=questoes,
                started_at=started_at,
                refresh_search=refresh_search,
                urls=urls,
                skip_search=skip_search,
            )
            research_quality = self.pipeline.assess_research_quality(research)
            self.pipeline.log_weak_research_warning(research_quality)

        return {
            "research": research,
            "research_quality": research_quality,
            "status": "ok",
        }

    def _evidence(self, state: PipelineState) -> PipelineState:
        pack = self.pipeline.run_evidence_stage(
            research=state["research"],
            ferramentas=state["ferramentas"],
            foco=state["foco"],
            started_at=state["started_at"],
        )
        return {"evidence_pack": pack, "status": "ok"}

    def _analysis(self, state: PipelineState) -> PipelineState:
        analysis = self.pipeline.run_analysis_stage(
            research=state["research"],
            evidence_pack=state.get("evidence_pack"),
            ferramentas=state["ferramentas"],
            contexto=state["contexto"],
            foco=state["foco"],
            questoes=state["questoes"],
            started_at=state["started_at"],
        )
        analysis = self.pipeline.enrich_analysis_with_tips(
            analysis=analysis,
            ferramentas=state["ferramentas"],
            foco=state["foco"],
        )
        return {"analysis": analysis, "status": "ok"}

    def _start_write(self, state: PipelineState) -> PipelineState:
        self.pipeline.log.section(3, 3, "Escrevendo")
        self.pipeline.log_memory_hit_if_available()
        return {"status": "ok"}

    def _writer(self, state: PipelineState) -> PipelineState:
        iteration = int(state.get("iteration", 0)) + 1
        self.pipeline.enforce_global_timeout(state["started_at"], stage=f"iteração {iteration} (writer)")
        self.pipeline.log.iteration(iteration, self.pipeline.max_iterations)

        writer_started = monotonic()
        correction_instructions = state.get("correction_instructions", "")
        self.pipeline.log.event_log.log_event("writer_start", {
            "iteration": iteration,
            "article_chars_previous": len(state.get("article", "")),
            "correction_chars": len(correction_instructions),
            "research_quality": state.get("research_quality"),
        })

        writer_inputs = {
            "iteration": iteration,
            "research": state["research"],
            "evidence_pack": state.get("evidence_pack"),
            "analysis": state["analysis"],
            "ferramentas": state["ferramentas"],
            "contexto": state["contexto"],
            "foco": state["foco"],
            "questoes": state["questoes"],
            "correction_instructions": correction_instructions,
            "research_quality": state["research_quality"],
        }
        article = self._run_writer_with_heartbeat(
            state=state,
            iteration=iteration,
            writer_started=writer_started,
            writer_inputs=writer_inputs,
        )
        writer_elapsed = round(monotonic() - writer_started, 3)
        self.pipeline.log.event_log.log_event("writer_end", {
            "iteration": iteration,
            "elapsed_seconds": writer_elapsed,
            "article_chars": len(article),
            "empty_article": not bool(article),
        })
        if article:
            sanitize_started = monotonic()
            article = self.pipeline.sanitize_article(article)
            self.pipeline.log.event_log.log_event("sanitize_end", {
                "iteration": iteration,
                "elapsed_seconds": round(monotonic() - sanitize_started, 3),
                "article_chars": len(article),
            })

        return {
            "iteration": iteration,
            "article": article,
            "status": "ok",
        }

    def _run_writer_with_heartbeat(
        self,
        *,
        state: PipelineState,
        iteration: int,
        writer_started: float,
        writer_inputs: dict[str, Any],
    ) -> str:
        heartbeat_count = 0
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.pipeline.run_writer_iteration, **writer_inputs)
            while True:
                try:
                    return future.result(timeout=self.writer_heartbeat_seconds)
                except FutureTimeoutError:
                    heartbeat_count += 1
                    elapsed = round(monotonic() - writer_started, 3)
                    self.pipeline.log.event_log.log_event("writer_heartbeat", {
                        "iteration": iteration,
                        "elapsed_seconds": elapsed,
                        "heartbeat_count": heartbeat_count,
                        "interval_seconds": self.writer_heartbeat_seconds,
                    })
                    # Garantia de timeout global mesmo enquanto aguarda resposta do writer.
                    self.pipeline.enforce_global_timeout(
                        state["started_at"],
                        stage=f"iteração {iteration} (writer_heartbeat)",
                    )

    def _question_coverage(self, state: PipelineState) -> PipelineState:
        evaluation = self.pipeline.validate_question_coverage(
            article=state.get("article", ""),
            questoes=state["questoes"],
        )
        if not evaluation.get("approved"):
            self.pipeline.log.event_log.log_event("question_coverage_failed", {
                "iteration": state.get("iteration", 0),
                "problem_count": len(evaluation.get("problems", [])),
            })
            self.pipeline.log.critic_failed(evaluation.get("problems", []))
        return {
            "evaluation": evaluation,
            "correction_instructions": evaluation.get("correction_prompt", ""),
            "write_status": "coverage_failed" if not evaluation.get("approved") else "coverage_ok",
        }

    def _critic(self, state: PipelineState) -> PipelineState:
        critic_started = monotonic()
        self.pipeline.log.event_log.log_event("critic_start", {
            "iteration": state.get("iteration", 0),
            "article_chars": len(state.get("article", "")),
        })
        evaluation = self.pipeline.run_critic_iteration(
            article=state.get("article", ""),
            ferramentas=state["ferramentas"],
            started_at=state["started_at"],
            iteration=state.get("iteration", 0),
            evidence_pack=state.get("evidence_pack"),
        )
        self.pipeline.log.event_log.log_event("critic_end", {
            "iteration": state.get("iteration", 0),
            "elapsed_seconds": round(monotonic() - critic_started, 3),
            "approved": evaluation.get("approved", False),
            "layer": evaluation.get("layer", ""),
            "problem_count": len(evaluation.get("problems", [])),
            "warning_count": len(evaluation.get("warnings", [])),
        })
        if evaluation.get("approved"):
            self.pipeline.handle_approved_article(
                iteration=state.get("iteration", 0),
                evaluation=evaluation,
                correction_instructions=state.get("correction_instructions", ""),
                ferramentas=state["ferramentas"],
                foco=state["foco"],
            )
            return {"evaluation": evaluation, "write_status": "approved"}

        self.pipeline.log.critic_failed(evaluation.get("problems", []))
        return {
            "evaluation": evaluation,
            "correction_instructions": evaluation.get("correction_prompt", ""),
            "write_status": "critic_failed",
        }

    def _after_failure(self, state: PipelineState) -> PipelineState:
        evaluation = state.get("evaluation", {})
        iteration = state.get("iteration", 0)
        research_quality = state.get("research_quality", "weak")
        research_enrichment_count = int(state.get("research_enrichment_count", 0))
        previous_problem_signature = state.get("previous_problem_signature")
        stagnant_iterations = int(state.get("stagnant_iterations", 0))

        decision = self.pipeline.decide_retry_or_finalize(
            ferramentas=state["ferramentas"],
            foco=state["foco"],
            iteration=iteration,
            research_enrichment_count=research_enrichment_count,
            stagnant_iterations=stagnant_iterations,
            evaluation=evaluation,
            research_quality=research_quality,
        )
        action = decision.get("action", "RETRY_WRITER")
        priority_fixes = decision.get("priority_fixes", [])
        if priority_fixes and not state.get("correction_instructions"):
            correction = "\n".join(f"- {item}" for item in priority_fixes if str(item).strip())
            if correction:
                state["correction_instructions"] = (
                    "PRIORIDADE DE CORREÇÃO:\n" + correction
                )

        if action == "FINALIZE_APPROVED":
            return {"write_status": "stop"}
        if action == "FINALIZE_INCOMPLETE":
            self.pipeline.log.section_end(3, 3, "Escrevendo", status="incomplete")
            return {"write_status": "stop"}

        should_enrich = action == "ENRICH_RESEARCH"
        if should_enrich and research_enrichment_count < self.pipeline.max_research_enrichments:
            research_enrichment_count += 1
            research, analysis, research_quality = self.pipeline.enrich_research_and_analysis_for_critic(
                ferramentas=state["ferramentas"],
                contexto=state["contexto"],
                foco=state["foco"],
                questoes=state["questoes"],
                started_at=state["started_at"],
                enrichment_number=research_enrichment_count,
                evaluation=evaluation,
            )
            return {
                "research": research,
                "analysis": analysis,
                "research_quality": research_quality,
                "research_enrichment_count": research_enrichment_count,
                "correction_instructions": state.get("correction_instructions", ""),
                "previous_problem_signature": None,
                "stagnant_iterations": 0,
                "write_status": "retry",
            }

        previous_problem_signature, stagnant_iterations = self.pipeline.update_stagnation_state(
            evaluation=evaluation,
            previous_problem_signature=previous_problem_signature,
            stagnant_iterations=stagnant_iterations,
        )
        if self.pipeline.should_stop_for_stagnation(
            stagnant_iterations=stagnant_iterations,
            iteration=iteration,
            ferramentas=state["ferramentas"],
            evaluation=evaluation,
        ):
            self.pipeline.log.section_end(3, 3, "Escrevendo", status="stagnation_break")
            return {
                "write_status": "stop",
                "correction_instructions": state.get("correction_instructions", ""),
                "previous_problem_signature": previous_problem_signature,
                "stagnant_iterations": stagnant_iterations,
            }

        if iteration >= self.pipeline.max_iterations:
            self.pipeline.log.error("Máximo de iterações atingido. Salvando melhor versão.")
            self.pipeline.memory.log_event("max_iterations_reached", {
                "ferramentas": state["ferramentas"],
                "problems": evaluation.get("problems", []),
            })
            self.pipeline.log.section_end(3, 3, "Escrevendo", status="incomplete")
            return {
                "write_status": "stop",
                "correction_instructions": state.get("correction_instructions", ""),
                "previous_problem_signature": previous_problem_signature,
                "stagnant_iterations": stagnant_iterations,
            }

        return {
            "write_status": "retry",
            "correction_instructions": state.get("correction_instructions", ""),
            "previous_problem_signature": previous_problem_signature,
            "stagnant_iterations": stagnant_iterations,
        }

    def _finalize(self, state: PipelineState) -> PipelineState:
        pipeline_status = state.get("pipeline_status", "completed")
        if pipeline_status == "running":
            pipeline_status = "completed"
        if state.get("write_status") == "approved":
            self.pipeline.log.section_end(3, 3, "Escrevendo", status="ok")
        elif state.get("write_status") not in {"stop"}:
            self.pipeline.log.section_end(3, 3, "Escrevendo", status="incomplete")

        elapsed = round(monotonic() - state["started_at"], 2)
        self.pipeline.log.pipeline_end(
            status=pipeline_status,
            elapsed_seconds=elapsed,
            approved=state.get("evaluation", {}).get("approved"),
            iteration=state.get("iteration"),
        )
        return {"pipeline_status": pipeline_status, "status": "ok"}

    def _route_after_question_coverage(self, state: PipelineState) -> str:
        if state.get("write_status") == "coverage_failed":
            return "after_failure"
        return "critic"

    def _route_after_critic(self, state: PipelineState) -> str:
        if state.get("write_status") == "approved":
            return "finalize"
        return "after_failure"

    def _route_after_failure(self, state: PipelineState) -> str:
        if state.get("write_status") == "retry":
            return "writer"
        return "finalize"
