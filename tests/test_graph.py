"""Tests for sdd/graph/ — graph structure and deterministic routing."""

from __future__ import annotations

from langgraph.graph import StateGraph

from sdd.graph.routing import MAX_ITERATIONS, MAX_STAGNANT, route_after_critic
from sdd.graph.runner import build_graph
from sdd.graph.state import PipelineState


# ── build_graph ──────────────────────────────────────────────────────────────

def test_build_graph_returns_state_graph():
    graph = build_graph()
    assert isinstance(graph, StateGraph)


def test_build_graph_compiles_without_error():
    graph = build_graph()
    app = graph.compile()
    assert app is not None


# ── route_after_critic ───────────────────────────────────────────────────────

def test_route_approved_goes_to_finalize():
    state: dict = {"critic_result": {"approved": True, "action": "FINALIZE_APPROVED"}, "iteration": 0, "stagnant_count": 0}
    assert route_after_critic(state) == "finalize"


def test_route_max_iterations_goes_to_finalize():
    state: dict = {
        "critic_result": {"approved": False, "action": "RETRY_WRITER"},
        "iteration": MAX_ITERATIONS,
        "stagnant_count": 0,
    }
    assert route_after_critic(state) == "finalize"


def test_route_max_stagnant_goes_to_finalize():
    state: dict = {
        "critic_result": {"approved": False, "action": "RETRY_WRITER"},
        "iteration": 0,
        "stagnant_count": MAX_STAGNANT,
    }
    assert route_after_critic(state) == "finalize"


def test_route_retry_writer_goes_to_writer():
    state: dict = {
        "critic_result": {"approved": False, "action": "RETRY_WRITER"},
        "iteration": 0,
        "stagnant_count": 0,
    }
    assert route_after_critic(state) == "writer"


def test_route_enrich_research_goes_to_research():
    state: dict = {
        "critic_result": {"approved": False, "action": "ENRICH_RESEARCH"},
        "iteration": 0,
        "stagnant_count": 0,
    }
    assert route_after_critic(state) == "research"


def test_route_finalize_approved_action_goes_to_finalize():
    state: dict = {
        "critic_result": {"approved": False, "action": "FINALIZE_APPROVED"},
        "iteration": 0,
        "stagnant_count": 0,
    }
    assert route_after_critic(state) == "finalize"


def test_route_finalize_incomplete_action_goes_to_finalize():
    state: dict = {
        "critic_result": {"approved": False, "action": "FINALIZE_INCOMPLETE"},
        "iteration": 0,
        "stagnant_count": 0,
    }
    assert route_after_critic(state) == "finalize"


def test_route_unknown_action_defaults_to_writer():
    state: dict = {
        "critic_result": {"approved": False, "action": "UNKNOWN_ACTION"},
        "iteration": 0,
        "stagnant_count": 0,
    }
    assert route_after_critic(state) == "writer"


def test_route_no_critic_result_defaults_to_writer():
    state: dict = {"iteration": 0, "stagnant_count": 0}
    assert route_after_critic(state) == "writer"


# ── PipelineState fields ─────────────────────────────────────────────────────

def test_pipeline_state_has_required_persistent_fields():
    required = {"ferramentas", "foco", "questoes", "evidence_pack", "analysis",
                "article_v1", "iteration", "stagnant_count"}
    assert required.issubset(PipelineState.__annotations__)


def test_pipeline_state_has_required_volatile_fields():
    required = {"article", "critic_result", "correction"}
    assert required.issubset(PipelineState.__annotations__)
