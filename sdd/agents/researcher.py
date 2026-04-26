"""Thin wrapper over ResearcherSkill for Phase 4 interface."""

from skills.researcher import ResearcherSkill


class ResearcherAgent:
    """Delegate research execution to ResearcherSkill."""

    def __init__(self, search_tool, scraper_tool, memory, spec: dict):
        self.skill = ResearcherSkill(search_tool=search_tool, scraper_tool=scraper_tool, memory=memory)
        self.spec = spec

    def run(self, tool: str, foco: str, questoes: list[str]) -> dict:
        """Run research for a tool and return urls + context."""
        return self.skill.run(tool=tool, foco=foco, questoes=questoes)
