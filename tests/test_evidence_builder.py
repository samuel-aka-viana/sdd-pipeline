"""Tests for EvidenceBuilderSkill and EvidencePack schemas."""
from skills.schemas import EvidenceGap, EvidenceItem, EvidencePack


def test_evidence_item_valid():
    item = EvidenceItem(
        id="docker_abc123",
        tool="docker",
        topic="docker",
        claim="Docker requires 4GB RAM",
        source_url="https://docs.docker.com/get-started/",
        source_quality="docs",
        evidence="Docker requires 4GB RAM minimum for production workloads.",
        confidence=1.0,
    )
    assert item.id == "docker_abc123"
    assert item.source_quality == "docs"
    assert item.confidence == 1.0


def test_evidence_pack_empty():
    pack = EvidencePack(ferramentas="docker", foco="instalação")
    assert pack.ferramentas == "docker"
    assert pack.items == []
    assert pack.gaps == []
    assert pack.retained_urls == []


def test_evidence_gap_valid():
    gap = EvidenceGap(topic="podman", reason="nenhuma URL encontrada no research")
    assert gap.topic == "podman"


from skills.evidence_builder import EvidenceBuilderSkill


RESEARCH_WITH_URLS = """\
# docker
Docker is a containerization platform. See https://docs.docker.com/get-started/ for details.
Community support at https://stackoverflow.com/questions/tagged/docker

# podman
Podman documentation at https://docs.podman.io/en/latest/ explains rootless containers.
Blog post at https://medium.com/podman-tutorial
"""

RESEARCH_NO_URLS = """\
# docker
Docker is a containerization platform with no links here.
"""


def test_evidence_builder_extracts_urls():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build(RESEARCH_WITH_URLS, "docker e podman", "comparação geral")
    assert pack.total_urls_found == 4
    assert len(pack.retained_urls) == 4
    assert "https://docs.docker.com/get-started/" in pack.retained_urls


def test_evidence_builder_items_have_tool():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build(RESEARCH_WITH_URLS, "docker e podman", "comparação geral")
    tools = {item.tool for item in pack.items}
    assert "docker" in tools
    assert "podman" in tools


def test_evidence_builder_docs_have_high_confidence():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build(RESEARCH_WITH_URLS, "docker e podman", "comparação geral")
    docs_items = [i for i in pack.items if "docs." in i.source_url]
    assert all(i.confidence == 1.0 for i in docs_items)


def test_evidence_builder_empty_research():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build("", "docker", "instalação")
    assert pack.items == []
    assert pack.retained_urls == []
    assert len(pack.gaps) == 1
    assert pack.gaps[0].topic == "docker"


def test_evidence_builder_no_urls_creates_gap():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build(RESEARCH_NO_URLS, "docker", "instalação")
    assert pack.items == []
    assert len(pack.gaps) == 1
    assert pack.gaps[0].topic == "docker"


def test_evidence_builder_retained_urls_ordered_by_quality():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build(RESEARCH_WITH_URLS, "docker e podman", "comparação geral")
    # docs should come before blog in retained_urls
    doc_idx = next(i for i, u in enumerate(pack.retained_urls) if "docs." in u)
    blog_idx = next(i for i, u in enumerate(pack.retained_urls) if "medium.com" in u)
    assert doc_idx < blog_idx


def test_evidence_builder_pack_fields():
    builder = EvidenceBuilderSkill(memory=None)
    pack = builder.build(RESEARCH_WITH_URLS, "docker e podman", "comparação geral")
    assert pack.ferramentas == "docker e podman"
    assert pack.foco == "comparação geral"


from unittest.mock import MagicMock
import json
from pathlib import Path


def test_evidence_stage_saves_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()

    from pipeline_stages.evidence import run_evidence_stage
    from skills.schemas import EvidencePack

    mock_pipeline = MagicMock()
    mock_pipeline.enforce_global_timeout = MagicMock()

    builder = EvidenceBuilderSkill(memory=None)
    mock_pipeline.evidence_builder = builder

    mock_memory = MagicMock()
    mock_pipeline.memory = mock_memory

    pack = run_evidence_stage(
        mock_pipeline,
        research=RESEARCH_WITH_URLS,
        ferramentas="docker e podman",
        foco="comparação geral",
        started_at=0.0,
    )

    assert isinstance(pack, EvidencePack)
    assert (tmp_path / "output" / "evidence_pack.json").exists()
    data = json.loads((tmp_path / "output" / "evidence_pack.json").read_text())
    assert data["ferramentas"] == "docker e podman"
    mock_memory.log_event.assert_called_with("evidence_pack_built", {
        "ferramentas": "docker e podman",
        "total_urls_found": pack.total_urls_found,
        "retained_urls": len(pack.retained_urls),
        "items": len(pack.items),
        "gaps": len(pack.gaps),
    })


def test_research_stage_does_not_save_debug_research(tmp_path, monkeypatch):
    """save_debug("research", ...) must NOT be called from research stage."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()

    from pipeline_stages.research import run_research_stage

    mock_pipeline = MagicMock()
    mock_pipeline.parse_tools.return_value = ["docker"]
    mock_pipeline.enforce_global_timeout = MagicMock()
    mock_pipeline.researcher = MagicMock()
    mock_pipeline.researcher.run.return_value = "# docker\nsome content https://docs.docker.com"
    mock_pipeline.memory = MagicMock()
    mock_pipeline.save_debug = MagicMock()
    mock_pipeline.save_research_history = MagicMock()
    mock_pipeline.assess_research_quality = MagicMock(return_value="ok")

    run_research_stage(
        mock_pipeline,
        ferramentas="docker",
        foco="instalação",
        questoes=[],
        started_at=0.0,
    )

    for call in mock_pipeline.save_debug.call_args_list:
        assert call.args[0] != "research", "debug_research.md must not be saved by default"


def test_html_debug_disabled_by_default(monkeypatch):
    """HTML_DEBUG_ENABLED must be False when SDD_HTML_DEBUG env is not set."""
    monkeypatch.delenv("SDD_HTML_DEBUG", raising=False)
    import importlib
    import researcher_modules.constants as constants
    importlib.reload(constants)
    assert constants.HTML_DEBUG_ENABLED is False


def test_langgraph_has_evidence_node():
    """LangGraph graph must have 'evidence' node, not 'relevance_filter'."""
    from orchestration.langgraph_runner import LangGraphOrchestrator
    mock_pipeline = MagicMock()
    mock_pipeline.spec = {"pipeline": {}}
    orch = LangGraphOrchestrator(mock_pipeline)
    nodes = set(orch.graph.get_graph().nodes.keys())
    assert "evidence" in nodes
    assert "relevance_filter" not in nodes


def test_pipeline_state_has_evidence_pack_field():
    """PipelineState TypedDict must declare evidence_pack field."""
    from orchestration.langgraph_runner import PipelineState
    import typing
    hints = typing.get_type_hints(PipelineState)
    assert "evidence_pack" in hints
