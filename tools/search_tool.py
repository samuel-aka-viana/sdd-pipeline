import time
import logging
import json
from pathlib import Path
from ddgs import DDGS
from tools.source_ranker import SourceRanker

log = logging.getLogger(__name__)

RETRY_WAIT = 5
MAX_RETRIES = 2


class SearchTool:

    def __init__(
        self,
        results_per_query: int = 8,
        cache_enabled: bool = True,
        cache_ttl_seconds: int = 86400,
        cache_path: str = ".memory/search_cache.json",
        rank_sources: bool = True,
    ):
        self.num = results_per_query
        self.cache_enabled = cache_enabled
        self.cache_ttl_seconds = cache_ttl_seconds
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_index = self.load_cache()
        self.ranker = SourceRanker() if rank_sources else None

    def search(self, query: str, num: int | None = None, force_refresh: bool = False) -> list[dict]:
        num = num or self.num
        cache_key = self.build_cache_key(query, num)
        cached_entry = self.cache_index.get(cache_key)

        if self.cache_enabled and not force_refresh and self.is_cache_fresh(cached_entry):
            cached_results = cached_entry.get("results", [])
            if cached_results:
                return cached_results[:num]

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with DDGS() as ddgs:
                    raw = list(ddgs.text(query, max_results=num))
                results = [
                    {
                        "title":   result_item.get("title", ""),
                        "url":     result_item.get("href", ""),
                        "snippet": result_item.get("body", ""),
                    }
                    for result_item in raw
                ]

                # Rank sources: prioritize official docs (60%) + technical articles (40%)
                if self.ranker and results:
                    results = self.ranker.rank_results(results)
                    log.debug(f"Source distribution: {self.ranker.get_tier_distribution(results)}")

                if self.cache_enabled and results:
                    self.cache_index[cache_key] = {
                        "query": query,
                        "num": num,
                        "ts": time.time(),
                        "results": results,
                    }
                    self.save_cache()
                return results
            except Exception as e:
                log.warning("search failed (attempt %d): %s — %s", attempt, query, e)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT * attempt)
        if self.cache_enabled and cached_entry:
            return cached_entry.get("results", [])[:num]
        return []

    def search_multi(
        self,
        queries: list[str],
        delay: float = 1.0,
        force_refresh: bool = False,
    ) -> dict[str, list]:
        results = {}
        for query in queries:
            results[query] = self.search(query, force_refresh=force_refresh)
            if delay > 0:
                time.sleep(delay)
        return results

    def save_urls(self, results_by_query: dict, path: str):
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            for query, results in results_by_query.items():
                f.write(f"\n## Query: {query}\n")
                for result_item in results:
                    f.write(f"- {result_item['url']}\n")

    def build_cache_key(self, query: str, num: int) -> str:
        normalized_query = " ".join(query.lower().strip().split())
        return f"{normalized_query}|{num}"

    def is_cache_fresh(self, cache_entry: dict | None) -> bool:
        if not cache_entry:
            return False
        entry_timestamp = float(cache_entry.get("ts", 0))
        return (time.time() - entry_timestamp) <= self.cache_ttl_seconds

    def load_cache(self) -> dict:
        if not self.cache_enabled or not self.cache_path.exists():
            return {}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return data if isinstance(data, dict) else {}

    def save_cache(self):
        if not self.cache_enabled:
            return
        try:
            self.cache_path.write_text(
                json.dumps(self.cache_index, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            log.warning("failed to persist search cache: %s", error)
