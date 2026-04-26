"""Pydantic schemas for structured outputs across all skills."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# --- Critic schemas ---

class SemanticIssue(BaseModel):
    excerpt: str = Field(..., description="Trecho exato do artigo (≥ 8 chars).")
    problem: str = Field(..., description="Descrição do problema (≥ 10 chars).")


class SemanticCheckResult(BaseModel):
    issues: list[SemanticIssue] = Field(default_factory=list)


class FilteredIssuesResult(BaseModel):
    filtered_issues: list[SemanticIssue] = Field(default_factory=list)


# --- Orchestrator schemas ---

OrchestratorAction = Literal[
    "RETRY_WRITER",
    "ENRICH_RESEARCH",
    "FINALIZE_APPROVED",
    "FINALIZE_INCOMPLETE",
]


class OrchestratorDecision(BaseModel):
    action: OrchestratorAction = Field(..., description="Próxima ação do pipeline.")
    reason: str = Field(default="llm_decision")
    priority_fixes: list[str] = Field(default_factory=list)


class TargetedQuestionsResult(BaseModel):
    questions: list[str] = Field(default_factory=list)


# --- EvidencePack schemas ---

class EvidenceItem(BaseModel):
    id: str
    tool: str
    topic: str
    claim: str
    source_url: str
    source_title: str = ""
    source_quality: str = "unknown"
    evidence: str
    confidence: float = 0.0


class EvidenceGap(BaseModel):
    topic: str
    reason: str


class EvidencePack(BaseModel):
    ferramentas: str
    foco: str
    total_urls_found: int = 0
    retained_urls: list[str] = []
    items: list[EvidenceItem] = []
    gaps: list[EvidenceGap] = []
