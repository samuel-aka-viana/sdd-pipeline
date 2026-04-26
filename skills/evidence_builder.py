"""Deterministic builder: research text → EvidencePack (no LLM)."""

from __future__ import annotations

import hashlib
import logging
from urllib.parse import urlparse

from skills.relevance_filter import (
    RelevanceFilterSkill,
    ScoredUrl,
)
from skills.schemas import EvidenceGap, EvidenceItem, EvidencePack

logger = logging.getLogger(__name__)

_QUALITY_CONFIDENCE: dict[str, float] = {
    "docs": 1.0,
    "usos": 0.8,
    "blog": 0.6,
    "outros": 0.4,
}

_CLASSIFIER = RelevanceFilterSkill(memory=None)


class EvidenceBuilderSkill:
    """Transforms raw research text into a structured EvidencePack.

    Deterministic — no LLM calls. Reuses URL classification logic from
    RelevanceFilterSkill (docs > usos > blog > outros).
    """

    def __init__(self, memory, max_urls: int = 30):
        self.memory = memory
        self.max_urls = max(1, int(max_urls))

    def build(self, research: str, ferramentas: str, foco: str) -> EvidencePack:
        if not research or not research.strip():
            tools = _parse_tool_names(ferramentas)
            return EvidencePack(
                ferramentas=ferramentas,
                foco=foco,
                gaps=[EvidenceGap(topic=t, reason="research vazio") for t in tools],
            )

        tools = _parse_tool_names(ferramentas)
        blocks = _split_tool_blocks(research)

        all_entries: list[tuple[str, ScoredUrl]] = []
        for block_tool, text in blocks.items():
            urls = _CLASSIFIER.extract_urls(text)
            scored = [_CLASSIFIER.classify(url) for url in urls]
            scored = _CLASSIFIER.attach_snippets(scored, text)
            for s in scored:
                all_entries.append((block_tool, s))

        # Deduplicate by URL — keep entry with best composite_score (lower = better)
        best: dict[str, tuple[str, ScoredUrl]] = {}
        for tool, s in all_entries:
            if s.url not in best or s.composite_score < best[s.url][1].composite_score:
                best[s.url] = (tool, s)

        ranked = sorted(best.values(), key=lambda ts: ts[1].composite_score)[: self.max_urls]
        retained_urls = [s.url for _, s in ranked]
        items = [_make_item(tool, s) for tool, s in ranked]

        covered_tools = {item.tool for item in items}
        gaps = [
            EvidenceGap(topic=t, reason="nenhuma URL encontrada no research")
            for t in tools
            if t not in covered_tools
        ]

        pack = EvidencePack(
            ferramentas=ferramentas,
            foco=foco,
            total_urls_found=len(all_entries),
            retained_urls=retained_urls,
            items=items,
            gaps=gaps,
        )

        if self.memory is not None:
            self.memory.log_event("evidence_pack_built_skill", {
                "ferramentas": ferramentas,
                "total_urls_found": len(all_entries),
                "retained": len(retained_urls),
                "gaps": len(gaps),
            })

        logger.info(
            "[evidence_builder] %d URLs found, %d retained, %d gaps",
            len(all_entries), len(retained_urls), len(gaps),
        )
        return pack


def _parse_tool_names(ferramentas: str) -> list[str]:
    return [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]


def _split_tool_blocks(research: str) -> dict[str, str]:
    """Split '# Tool\\ncontent\\n\\n# Tool2\\ncontent' into {tool: content}."""
    blocks: dict[str, str] = {}
    current_tool = "_default"
    current_lines: list[str] = []
    for line in research.splitlines():
        if line.startswith("# "):
            if current_lines:
                blocks[current_tool] = "\n".join(current_lines)
            current_tool = line[2:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        blocks[current_tool] = "\n".join(current_lines)
    return blocks


def _make_item(tool: str, scored: ScoredUrl) -> EvidenceItem:
    uid = hashlib.sha1(scored.url.encode()).hexdigest()[:8]
    snippet = scored.snippet or scored.url
    # First sentence of snippet as the claim (≤ 200 chars)
    claim = snippet.split(".")[0][:200].strip() or snippet[:200]
    title = urlparse(scored.url).netloc or scored.url[:60]
    confidence = _QUALITY_CONFIDENCE.get(scored.category, 0.4)
    return EvidenceItem(
        id=f"{tool}_{uid}",
        tool=tool,
        topic=tool,
        claim=claim,
        source_url=scored.url,
        source_title=title,
        source_quality=scored.category,
        evidence=snippet,
        confidence=confidence,
    )
