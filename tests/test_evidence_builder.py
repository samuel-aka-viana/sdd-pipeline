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
