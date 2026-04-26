"""Tests for EvidenceBuilderSkill and EvidencePack schemas."""
import pytest
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
