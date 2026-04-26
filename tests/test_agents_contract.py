"""Contract tests for sdd/agents/ — no real LLM calls."""

import inspect
import pytest
from unittest.mock import MagicMock, patch

from sdd.schemas import EvidencePack
from sdd.agents import ResearcherAgent, EvidenceAgent, AnalystAgent, WriterAgent, CriticAgent


MINIMAL_SPEC = {"llm": {}, "pipeline": {}}


# ---------------------------------------------------------------------------
# Instantiation contracts
# ---------------------------------------------------------------------------

def test_evidence_agent_instantiates():
    agent = EvidenceAgent(spec=MINIMAL_SPEC)
    assert agent is not None


def test_researcher_agent_instantiates():
    memory = MagicMock()
    search_tool = MagicMock()
    scraper_tool = MagicMock()
    agent = ResearcherAgent(search_tool=search_tool, scraper_tool=scraper_tool, memory=memory, spec=MINIMAL_SPEC)
    assert agent is not None


def test_analyst_agent_instantiates():
    memory = MagicMock()
    agent = AnalystAgent(memory=memory, spec=MINIMAL_SPEC)
    assert agent is not None


def test_writer_agent_instantiates():
    memory = MagicMock()
    agent = WriterAgent(memory=memory, spec=MINIMAL_SPEC)
    assert agent is not None


def test_critic_agent_instantiates():
    memory = MagicMock()
    agent = CriticAgent(memory=memory, spec=MINIMAL_SPEC)
    assert agent is not None


# ---------------------------------------------------------------------------
# WriterAgent.run() requires evidence_pack — no default value
# ---------------------------------------------------------------------------

def test_writer_run_requires_evidence_pack():
    sig = inspect.signature(WriterAgent.run)
    params = sig.parameters
    assert "evidence_pack" in params
    assert params["evidence_pack"].default is inspect.Parameter.empty


# ---------------------------------------------------------------------------
# CriticAgent deterministic rejection (no LLM call)
# ---------------------------------------------------------------------------

def test_critic_deterministic_rejection_on_placeholder():
    """Article with placeholder triggers deterministic rejection without LLM."""
    memory = MagicMock()
    agent = CriticAgent(memory=memory, spec=MINIMAL_SPEC)

    article_with_placeholder = "[TODO: fill in this section]"
    evidence_pack = EvidencePack(
        ferramentas="docker",
        foco="deploy",
        retained_urls=["https://docs.docker.com"],
    )

    # Patch skill.evaluate so we can confirm it is NOT called
    with patch.object(agent.skill, "evaluate") as mock_evaluate:
        result = agent.run(
            article=article_with_placeholder,
            evidence_pack=evidence_pack,
            ferramentas="docker",
            foco="deploy",
            questoes=["Como instalar Docker?"],
        )

    mock_evaluate.assert_not_called()
    assert result["approved"] is False
    assert result.get("deterministic_rejection") is True
    assert "action" in result


# ---------------------------------------------------------------------------
# Agent method signatures
# ---------------------------------------------------------------------------

def test_analyst_run_accepts_evidence_pack():
    sig = inspect.signature(AnalystAgent.run)
    assert "evidence_pack" in sig.parameters


def test_critic_run_accepts_questoes():
    sig = inspect.signature(CriticAgent.run)
    assert "questoes" in sig.parameters


def test_critic_has_no_private_methods():
    """Confirm no _prefixed methods on CriticAgent (dunder excluded)."""
    for name in dir(CriticAgent):
        if name.startswith("_") and not name.startswith("__"):
            pytest.fail(f"CriticAgent has private method: {name}")
