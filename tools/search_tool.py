import time
import logging
from pathlib import Path
from ddgs import DDGS

log = logging.getLogger(__name__)

RETRY_WAIT = 5
MAX_RETRIES = 2


class SearchTool:

    def __init__(self, results_per_query: int = 8):
        self.num = results_per_query

    def search(self, query: str, num: int | None = None) -> list[dict]:
        num = num or self.num
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                with DDGS() as ddgs:
                    raw = list(ddgs.text(query, max_results=num))
                return [
                    {
                        "title":   result_item.get("title", ""),
                        "url":     result_item.get("href", ""),
                        "snippet": result_item.get("body", ""),
                    }
                    for result_item in raw
                ]
            except Exception as e:
                log.warning("search failed (attempt %d): %s — %s", attempt, query, e)
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT * attempt)
        return []

    def search_multi(self, queries: list[str], delay: float = 1.0) -> dict[str, list]:
        results = {}
        for query in queries:
            results[query] = self.search(query)
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
