"""LangGraph node functions for the SDD pipeline.

Each node receives the full PipelineState and returns a dict with only the keys it modifies.
LangGraph merges these dicts automatically.
"""

from __future__ import annotations

import yaml
from pathlib import Path

from sdd.agents import ResearcherAgent, EvidenceAgent, AnalystAgent, WriterAgent, CriticAgent
from sdd.graph.state import PipelineState


_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _load_spec() -> dict:
    """Load article spec from spec/article_spec.yaml."""
    return yaml.safe_load((_PROJECT_ROOT / "spec/article_spec.yaml").read_text())


def _make_memory():
    """Instantiate a minimal MemoryStore for agent use."""
    from memory.memory_store import MemoryStore
    return MemoryStore()


def node_research(state: PipelineState) -> dict:
    """Run research for all tools and return concatenated research text."""
    from tools.search_tool import SearchTool
    from tools.scraper_factory import create_scraper

    spec = _load_spec()
    memory = _make_memory()
    search_tool = SearchTool()
    scraper_tool = create_scraper()
    agent = ResearcherAgent(search_tool=search_tool, scraper_tool=scraper_tool, memory=memory, spec=spec)

    ferramentas = state["ferramentas"]
    foco = state["foco"]
    questoes = state["questoes"]

    tool_list = [tool.strip() for tool in ferramentas.split(" vs ")]
    research_parts = []
    for tool in tool_list:
        result = agent.run(tool=tool, foco=foco, questoes=questoes)
        research_parts.append(result.get("context", ""))

    combined_research = "\n\n".join(research_parts)
    return {"evidence_pack": None, "article": None, "critic_result": None, "correction": None,
            "iteration": state.get("iteration", 0), "stagnant_count": state.get("stagnant_count", 0),
            "article_v1": state.get("article_v1"), "analysis": {"raw_research": combined_research}}


def node_evidence(state: PipelineState) -> dict:
    """Build EvidencePack from research stored in analysis dict."""
    spec = _load_spec()
    agent = EvidenceAgent(spec=spec)

    raw_research = (state.get("analysis") or {}).get("raw_research", "")
    pack = agent.run(
        research=raw_research,
        ferramentas=state["ferramentas"],
        foco=state["foco"],
    )
    return {"evidence_pack": pack}


def node_analysis(state: PipelineState) -> dict:
    """Generate structured analysis from EvidencePack."""
    spec = _load_spec()
    memory = _make_memory()
    agent = AnalystAgent(memory=memory, spec=spec)

    analysis = agent.run(
        evidence_pack=state["evidence_pack"],
        ferramentas=state["ferramentas"],
        foco=state["foco"],
    )
    return {"analysis": analysis}


def node_writer(state: PipelineState) -> dict:
    """Write article from evidence_pack and analysis; track first version and iteration count."""
    spec = _load_spec()
    memory = _make_memory()
    agent = WriterAgent(memory=memory, spec=spec)

    text = agent.run(
        evidence_pack=state["evidence_pack"],
        analysis=state["analysis"],
        ferramentas=state["ferramentas"],
        foco=state["foco"],
        correction=state.get("correction"),
    )

    current_iteration = state.get("iteration", 0)
    article_v1 = text if current_iteration == 0 else state.get("article_v1")

    return {
        "article": text,
        "article_v1": article_v1,
        "iteration": current_iteration + 1,
    }


def node_critic(state: PipelineState) -> dict:
    """Evaluate article quality; detect stagnation by comparing corrections."""
    evidence_pack = state.get("evidence_pack")
    if evidence_pack is None:
        return {"critic_result": {"approved": False, "action": "FINALIZE_INCOMPLETE"}, "correction": None}

    spec = _load_spec()
    memory = _make_memory()
    agent = CriticAgent(memory=memory, spec=spec)

    result = agent.run(
        article=state.get("article", ""),
        evidence_pack=evidence_pack,
        ferramentas=state["ferramentas"],
        foco=state["foco"],
        questoes=state["questoes"],
    )

    new_correction = result.get("correction")
    previous_correction = state.get("correction")
    stagnant_count = state.get("stagnant_count", 0)
    if new_correction and new_correction == previous_correction:
        stagnant_count += 1

    return {
        "critic_result": result,
        "correction": new_correction,
        "stagnant_count": stagnant_count,
    }


def node_finalize(state: PipelineState) -> dict:
    """Persist final article and return terminal state marker."""
    article = state.get("article") or state.get("article_v1", "")
    approved = (state.get("critic_result") or {}).get("approved", False)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    if article:
        ferramentas_slug = state["ferramentas"].replace(" ", "_").replace("/", "-")
        output_path = output_dir / f"article_{ferramentas_slug}.md"
        output_path.write_text(article)

    return {"article": article, "critic_result": state.get("critic_result") or {"approved": approved}}
