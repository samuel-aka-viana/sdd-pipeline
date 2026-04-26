from __future__ import annotations


def decide_retry_or_finalize(
    pipeline,
    *,
    ferramentas: str,
    foco: str,
    iteration: int,
    research_enrichment_count: int,
    stagnant_iterations: int,
    evaluation: dict,
) -> dict:
    approved = bool(evaluation.get("approved"))
    if approved:
        return {"action": "FINALIZE_APPROVED", "reason": "approved", "priority_fixes": []}
    if iteration >= pipeline.max_iterations:
        return {"action": "FINALIZE_INCOMPLETE", "reason": "max_iterations", "priority_fixes": []}
    if stagnant_iterations >= pipeline.max_stagnant_iterations:
        return {"action": "FINALIZE_INCOMPLETE", "reason": "stagnation", "priority_fixes": []}

    prompt = pipeline.prompts.get(
        "orchestrator",
        "decide_retry_or_finalize",
        ferramentas=ferramentas,
        foco=foco,
        iteration=iteration,
        max_iterations=pipeline.max_iterations,
        research_enrichment_count=research_enrichment_count,
        max_research_enrichments=pipeline.max_research_enrichments,
        stagnant_iterations=stagnant_iterations,
        max_stagnant_iterations=pipeline.max_stagnant_iterations,
        approved=approved,
        layer=evaluation.get("layer", ""),
        problems=evaluation.get("problems", []),
        warnings=evaluation.get("warnings", []),
    )
    if prompt:
        try:
            from skills.schemas import OrchestratorDecision
            parsed = pipeline.llm.generate_structured(
                role="critic",
                model=pipeline.orchestrator_model,
                prompt=prompt,
                schema=OrchestratorDecision,
                temperature=pipeline.orchestrator_temp,
                num_ctx=pipeline.orchestrator_ctx_len,
                timeout=pipeline.orchestrator_timeout,
            )
            decision = {
                "action": parsed.action,
                "reason": parsed.reason,
                "priority_fixes": parsed.priority_fixes,
            }
            pipeline.memory.log_event("orchestrator_decision_llm", {
                "action": parsed.action,
                "reason": str(parsed.reason)[:200],
            })
            return decision
        except Exception as exc:
            pipeline.memory.log_event("orchestrator_decision_llm_failed", {"error": str(exc)})

    should_enrich = pipeline.should_enrich_research_after_critic_failure(
        evaluation=evaluation,
        research_quality="weak",
    )
    return {
        "action": "ENRICH_RESEARCH" if should_enrich else "RETRY_WRITER",
        "reason": "deterministic_fallback",
        "priority_fixes": [],
    }


def update_stagnation_state(
    pipeline,
    evaluation: dict,
    previous_problem_signature: tuple[str, ...] | None,
    stagnant_iterations: int,
) -> tuple[tuple[str, ...] | None, int]:
    current_problem_signature = normalize_problem_signature(
        pipeline, evaluation.get("problems", [])
    )
    if current_problem_signature and current_problem_signature == previous_problem_signature:
        stagnant_iterations += 1
    else:
        stagnant_iterations = 0
    return current_problem_signature, stagnant_iterations


def should_stop_for_stagnation(
    pipeline,
    stagnant_iterations: int,
    iteration: int,
    ferramentas: str,
    evaluation: dict,
) -> bool:
    if stagnant_iterations < pipeline.max_stagnant_iterations:
        return False
    pipeline.log.error(
        "Sem progresso no critic após múltiplas iterações. Encerrando para evitar loop."
    )
    pipeline.memory.log_event("critic_stagnation_break", {
        "ferramentas": ferramentas,
        "iteration": iteration,
        "stagnant_iterations": stagnant_iterations,
        "problems": evaluation.get("problems", []),
    })
    return True


def normalize_problem_signature(pipeline, problems: list[str]) -> tuple[str, ...]:
    import re

    normalized_items = []
    for problem_text in problems:
        normalized_text = re.sub(r'^\d+\.\s*', '', problem_text.lower().strip())
        normalized_text = re.sub(r'\s+', ' ', normalized_text)
        if normalized_text:
            normalized_items.append(normalized_text)
    return tuple(sorted(normalized_items))
