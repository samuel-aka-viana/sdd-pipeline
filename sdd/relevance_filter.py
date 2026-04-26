"""Camada de relevância: classifica e prioriza URLs do research.

Aplicada após `researcher` e antes de `analyst`. Reduz ruído no contexto do
analyst limitando a um top-N ordenado por:
    rank de categoria (docs > usos > blog > outros)
    semantic_similarity (rerank opcional contra query, via embedding_fn)
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Callable, Sequence
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

EmbeddingFn = Callable[[list[str]], list[list[float]]]


CATEGORY_ORDER = ("docs", "usos", "blog", "outros")


DOCS_HOST_PATTERNS = (
    "docs.",
    "doc.",
    "developer.",
    "developers.",
    "readthedocs.io",
    "readthedocs.org",
    "learn.microsoft.com",
    "cloud.google.com",
    "aws.amazon.com",
    "kubernetes.io",
    "python.org",
    "nodejs.org",
    "rust-lang.org",
    "go.dev",
    "golang.org",
    "mozilla.org",
    "w3.org",
    "ietf.org",
    "spec.",
    "kernel.org",
)

DOCS_PATH_HINTS = ("/docs/", "/doc/", "/reference/", "/manual/", "/guide/", "/api/")

USOS_HOST_PATTERNS = (
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "stackoverflow.com",
    "stackexchange.com",
    "serverfault.com",
    "askubuntu.com",
    "superuser.com",
    "huggingface.co",
    "kaggle.com",
)

BLOG_HOST_PATTERNS = (
    "medium.com",
    "substack.com",
    "hashnode.com",
    "dev.to",
    "blog.",
    "towardsdatascience.com",
    "wordpress.com",
    "ghost.io",
    ".blogspot.",
)

URL_REGEX = re.compile(r"https?://[^\s)>\]\"'`<]+", re.IGNORECASE)


CONTEXT_WINDOW_CHARS = 240  # caracteres antes/depois da URL para representação semântica


@dataclass
class ScoredUrl:
    url: str
    category: str
    rank: int  # 0=docs, 1=usos, 2=blog, 3=outros
    similarity: float = 0.0
    snippet: str = ""

    @property
    def composite_score(self) -> float:
        # rank 0 = melhor; menor é primeiro. Combinamos com -similarity (maior é melhor).
        # Tradeoff fixo: rank dita ordem grossa; similarity desempata.
        return self.rank - 0.4 * self.similarity


class RelevanceFilterSkill:
    ROLE = "relevance_filter"

    def __init__(
        self,
        memory,
        max_urls: int = 30,
        embedding_fn: EmbeddingFn | None = None,
    ):
        self.memory = memory
        self.max_urls = max(1, int(max_urls))
        self.embedding_fn = embedding_fn

    def run(self, research: str, query: str | None = None) -> str:
        if not research:
            return research

        urls = self.extract_urls(research)
        if not urls:
            logger.info("[relevance_filter] nenhum URL encontrado no research")
            return research

        scored = [self.classify(url) for url in urls]
        scored = self.attach_snippets(scored, research)

        if query and self.embedding_fn is not None:
            scored = self.apply_semantic_rerank(scored, query)

        ranked = self.rank_and_truncate(scored)

        breakdown = self.category_breakdown(ranked)
        logger.info(
            "[relevance_filter] %d URLs encontrados, %d retidos (docs=%d, usos=%d, blog=%d, outros=%d) reranked=%s",
            len(urls), len(ranked),
            breakdown["docs"], breakdown["usos"], breakdown["blog"], breakdown["outros"],
            bool(query and self.embedding_fn is not None),
        )
        if self.memory is not None:
            self.memory.log_event("relevance_filter_summary", {
                "total_urls": len(urls),
                "retained_urls": len(ranked),
                "reranked": bool(query and self.embedding_fn is not None),
                **breakdown,
            })

        annotation = self.format_annotation(ranked, total=len(urls))
        return f"{research.rstrip()}\n\n{annotation}\n"

    def extract_urls(self, text: str) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for match in URL_REGEX.findall(text):
            url = match.rstrip(".,;:!?")
            if url not in seen:
                seen.add(url)
                result.append(url)
        return result

    def classify(self, url: str) -> ScoredUrl:
        host, path = self.split_host_path(url)

        if self.match_docs(host, path):
            return ScoredUrl(url=url, category="docs", rank=0)
        if self.match_host(host, USOS_HOST_PATTERNS):
            return ScoredUrl(url=url, category="usos", rank=1)
        if self.match_host(host, BLOG_HOST_PATTERNS):
            return ScoredUrl(url=url, category="blog", rank=2)
        return ScoredUrl(url=url, category="outros", rank=3)

    def split_host_path(self, url: str) -> tuple[str, str]:
        try:
            parsed = urlparse(url)
        except ValueError:
            return "", ""
        return (parsed.netloc or "").lower(), (parsed.path or "").lower()

    def match_host(self, host: str, patterns: tuple[str, ...]) -> bool:
        return any(pattern in host for pattern in patterns)

    def match_docs(self, host: str, path: str) -> bool:
        if self.match_host(host, DOCS_HOST_PATTERNS):
            return True
        return any(hint in path for hint in DOCS_PATH_HINTS)

    def attach_snippets(self, scored: list[ScoredUrl], research: str) -> list[ScoredUrl]:
        for item in scored:
            idx = research.find(item.url)
            if idx == -1:
                continue
            start = max(0, idx - CONTEXT_WINDOW_CHARS)
            end = min(len(research), idx + len(item.url) + CONTEXT_WINDOW_CHARS)
            item.snippet = research[start:end].replace("\n", " ").strip()
        return scored

    def apply_semantic_rerank(self, scored: list[ScoredUrl], query: str) -> list[ScoredUrl]:
        try:
            documents = [item.snippet or item.url for item in scored]
            embeddings = self.embedding_fn([query, *documents])
        except Exception as exc:
            logger.warning("[relevance_filter] embedding falhou, ignorando rerank: %s", exc)
            return scored

        if embeddings is None:
            return scored
        if len(embeddings) != len(scored) + 1:
            return scored
        query_vec = embeddings[0]
        for item, doc_vec in zip(scored, embeddings[1:]):
            item.similarity = self._cosine_similarity(query_vec, doc_vec)
        return scored

    def _cosine_similarity(self, a: Sequence[float] | None, b: Sequence[float] | None) -> float:
        if a is None or b is None:
            return 0.0
        try:
            len_a = len(a)
            len_b = len(b)
        except TypeError:
            return 0.0
        if len_a == 0 or len_b == 0 or len_a != len_b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def rank_and_truncate(self, scored: list[ScoredUrl]) -> list[ScoredUrl]:
        ordered = sorted(scored, key=lambda item: (item.composite_score, item.url))
        return ordered[: self.max_urls]

    def category_breakdown(self, scored: list[ScoredUrl]) -> dict[str, int]:
        counts = {key: 0 for key in CATEGORY_ORDER}
        for item in scored:
            counts[item.category] += 1
        return counts

    def format_annotation(self, ranked: list[ScoredUrl], total: int) -> str:
        lines = [
            f"## URLs Priorizadas (top {len(ranked)} de {total} — docs > usos > blog)",
        ]
        for category in CATEGORY_ORDER:
            bucket = [item for item in ranked if item.category == category]
            if not bucket:
                continue
            lines.append(f"\n### {category} ({len(bucket)})")
            for item in bucket:
                lines.append(f"- {item.url}")
        return "\n".join(lines)
