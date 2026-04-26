"""Thin wrapper over WriterSkill for Phase 4 interface."""

from skills.writer import WriterSkill
from sdd.schemas import EvidencePack


class WriterAgent:
    """Write article from EvidencePack and analysis. evidence_pack is mandatory."""

    def __init__(self, memory, spec: dict):
        self.skill = WriterSkill(memory)
        self.spec = spec

    def run(
        self,
        evidence_pack: EvidencePack,
        analysis: dict,
        ferramentas: str,
        foco: str,
        correction: str | None = None,
    ) -> str:
        """Write and return article string from evidence pack and analysis."""
        return self.skill.run(
            research="",
            analysis=str(analysis),
            ferramentas=ferramentas,
            contexto="",
            foco=foco,
            correction_instructions=correction or "",
            evidence_pack=evidence_pack,
        )
