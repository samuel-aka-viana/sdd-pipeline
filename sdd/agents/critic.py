"""Thin wrapper over CriticSkill for Phase 4 interface."""

import yaml
from pathlib import Path

from skills.critic import CriticSkill
from sdd.schemas import EvidencePack
from sdd.checks import run_deterministic_checks


class CriticAgent:
    """Evaluate article. Runs deterministic checks first; LLM only if all pass."""

    def __init__(self, memory, spec: dict):
        self.skill = CriticSkill(memory)
        self.spec = spec

    def run(
        self,
        article: str,
        evidence_pack: EvidencePack,
        ferramentas: str,
        foco: str,
        questoes: list[str],
    ) -> dict:
        """Evaluate article quality; return approval dict with action and correction."""
        config = self.load_quality_config()
        problems = run_deterministic_checks(
            article=article,
            retained_urls=evidence_pack.retained_urls,
            questions=questoes,
            config=config,
        )
        if problems:
            return {
                "approved": False,
                "action": "RETRY_WRITER",
                "correction": "\n".join(problems),
                "deterministic_rejection": True,
            }
        return self.skill.evaluate(
            artigo=article,
            ferramentas=ferramentas,
            evidence_pack=evidence_pack,
        )

    def load_quality_config(self) -> dict:
        """Load quality check configuration from sdd/config/quality.yaml."""
        config_path = Path(__file__).parent.parent / "config/quality.yaml"
        return yaml.safe_load(config_path.read_text())
