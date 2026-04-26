"""Deterministic routing logic for the SDD LangGraph pipeline."""

from sdd.graph.state import PipelineState

MAX_ITERATIONS = 3
MAX_STAGNANT = 2

ROUTE_MAP = {
    "RETRY_WRITER": "writer",
    "ENRICH_RESEARCH": "research",
    "FINALIZE_APPROVED": "finalize",
    "FINALIZE_INCOMPLETE": "finalize",
}


def route_after_critic(state: PipelineState) -> str:
    """Return next node name based on critic result and iteration count."""
    critic_result = state.get("critic_result") or {}
    approved = critic_result.get("approved", False)

    if approved:
        return "finalize"

    iteration = state.get("iteration", 0)
    if iteration >= MAX_ITERATIONS:
        return "finalize"

    stagnant = state.get("stagnant_count", 0)
    if stagnant >= MAX_STAGNANT:
        return "finalize"

    action = critic_result.get("action", "RETRY_WRITER")
    return ROUTE_MAP.get(action, "writer")
