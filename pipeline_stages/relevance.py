"""Stage: filtro de relevância (após researcher, antes de analyst)."""

from __future__ import annotations


def run_relevance_filter_stage(pipeline, *, research: str, started_at: float) -> str:
    pipeline.enforce_global_timeout(started_at, stage="relevance_filter")
    query = _build_rerank_query(pipeline)
    filtered = pipeline.relevance_filter.run(research, query=query)
    pipeline.save_debug("research_filtered", filtered)
    return filtered


def _build_rerank_query(pipeline) -> str:
    """Constrói a query do rerank a partir do contexto da execução atual."""
    ferramentas = pipeline.memory.get("ferramentas", "") or ""
    foco = pipeline.memory.get("foco", "") or ""
    parts = [p for p in (ferramentas, foco) if p]
    return " ".join(parts).strip()
