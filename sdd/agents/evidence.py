"""Thin wrapper over EvidenceBuilderSkill for Phase 4 interface."""

from skills.evidence_builder import EvidenceBuilderSkill
from sdd.schemas import EvidencePack


class EvidenceAgent:
    """Build EvidencePack from research text. Sole Chroma reader in new architecture."""

    def __init__(self, spec: dict, max_urls: int = 30):
        self.skill = EvidenceBuilderSkill(memory=None, max_urls=max_urls)
        self.spec = spec

    def run(self, research: str, ferramentas: str, foco: str) -> EvidencePack:
        """Build and return an EvidencePack from raw research text."""
        return self.skill.build(research=research, ferramentas=ferramentas, foco=foco)
