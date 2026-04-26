"""Thin wrapper over AnalystSkill for Phase 4 interface."""

from skills.analyst import AnalystSkill
from sdd.schemas import EvidencePack


class AnalystAgent:
    """Generate structured analysis from EvidencePack. No Chroma access."""

    def __init__(self, memory, spec: dict):
        self.skill = AnalystSkill(memory)
        self.spec = spec

    def run(self, evidence_pack: EvidencePack, ferramentas: str, foco: str) -> dict:
        """Run analysis on evidence pack and return structured analysis dict."""
        return self.skill.run(
            research="",
            ferramentas=ferramentas,
            contexto="",
            foco=foco,
            evidence_pack=evidence_pack,
        )
