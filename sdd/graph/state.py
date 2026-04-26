"""PipelineState TypedDict for the LangGraph-based SDD pipeline."""

from __future__ import annotations

from typing import TypedDict

from sdd.schemas import EvidencePack


class PipelineState(TypedDict):
    # ── Persistent between iterations ──────────────────────────────
    ferramentas: str
    foco: str
    questoes: list[str]
    evidence_pack: EvidencePack | None
    analysis: dict | None
    article_v1: str | None          # first article version, for diff
    iteration: int
    stagnant_count: int

    # ── Volatile per iteration (reset each cycle) ───────────────────
    article: str | None
    critic_result: dict | None
    correction: str | None
