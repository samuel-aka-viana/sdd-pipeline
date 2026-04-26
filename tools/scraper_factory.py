"""
Scraper factory: automatically selects best available provider.

Priority:
1. Crawl4AI (single dependency, fastest, handles JS + CF)
2. Original ScraperTool (fallback if crawl4ai not installed or fails)
"""
import logging
import json
import time
from pathlib import Path
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class _ScraperWithFallback:
    """Wrapper that falls back from Crawl4AI to ScraperTool on repeated failures."""

    DOMAIN_FAILURE_THRESHOLD = 3
    DOMAIN_COOLDOWN_SECONDS = 600
    DOMAIN_STATS_PATH = Path(".memory/scrape_domain_stats.json")

    def __init__(self, crawl4ai_scraper, max_chars: int, timeout: int, compliant_mode: bool, max_retries: int):
        self.crawl4ai_scraper = crawl4ai_scraper
        self.fallback_scraper = None
        self.max_chars = max_chars
        self.timeout = timeout
        self.compliant_mode = compliant_mode
        self.max_retries = max_retries
        self.domain_failures: dict[str, int] = {}
        self.domain_fallback_until: dict[str, float] = {}
        self.domain_stats = self._load_domain_stats()
        self._write_counter = 0

    def extract_text(self, url: str) -> dict:
        """Try Crawl4AI first; fallback is domain-scoped with cooldown."""
        domain = self._extract_domain(url)
        now = time.time()
        in_domain_cooldown = self.domain_fallback_until.get(domain, 0) > now

        if in_domain_cooldown:
            result = self._get_fallback_scraper().extract_text(url)
            self._record_domain_result(domain, result, used_fallback=True)
            return result

        result = self.crawl4ai_scraper.extract_text(url)
        status = result.get("status")
        failed = status in (
            "crawl4ai_error",
            "timeout",
            "http_429",
            "http_403",
            "http_503",
            "parse_error",
            "low_quality_content",
        )

        if failed:
            self.domain_failures[domain] = self.domain_failures.get(domain, 0) + 1
            if self.domain_failures[domain] >= self.DOMAIN_FAILURE_THRESHOLD:
                self.domain_fallback_until[domain] = now + self.DOMAIN_COOLDOWN_SECONDS
                log.warning(
                    f"Crawl4AI failed {self.DOMAIN_FAILURE_THRESHOLD}+ times for {domain}; "
                    f"fallback enabled for {self.DOMAIN_COOLDOWN_SECONDS}s. "
                    f"(Current failure URL: {url})"
                )
        else:
            self.domain_failures[domain] = 0

        if failed and self._should_force_fallback(domain):
            fallback_result = self._get_fallback_scraper().extract_text(url)
            self._record_domain_result(domain, fallback_result, used_fallback=True)
            return fallback_result

        self._record_domain_result(domain, result, used_fallback=False)
        return result

    def _get_fallback_scraper(self):
        """Lazily initialize fallback scraper."""
        if self.fallback_scraper is None:
            try:
                from tools.scraper_tool import ScraperTool
                self.fallback_scraper = ScraperTool(
                    max_chars=self.max_chars,
                    timeout=self.timeout,
                    compliant_mode=self.compliant_mode,
                    max_retries=self.max_retries,
                )
                log.info("Switched to ScraperTool fallback (Crawl4AI unstable)")
            except ImportError:
                log.error("Fallback ScraperTool not available")
                raise
        return self.fallback_scraper

    def _extract_domain(self, url: str) -> str:
        try:
            return (urlparse(url).netloc or "unknown").lower()
        except Exception:
            return "unknown"

    def _should_force_fallback(self, domain: str) -> bool:
        return self.domain_fallback_until.get(domain, 0) > time.time()

    def _record_domain_result(self, domain: str, result: dict, used_fallback: bool):
        status = result.get("status", "unknown")
        ok = status == "ok"
        stats = self.domain_stats.setdefault(
            domain,
            {
                "attempts": 0,
                "success": 0,
                "fail": 0,
                "fallback_attempts": 0,
                "statuses": {},
                "last_updated": 0.0,
            },
        )
        stats["attempts"] += 1
        stats["success"] += int(ok)
        stats["fail"] += int(not ok)
        stats["fallback_attempts"] += int(used_fallback)
        statuses = stats.setdefault("statuses", {})
        statuses[status] = int(statuses.get(status, 0)) + 1
        stats["last_updated"] = time.time()
        self._write_counter += 1
        should_flush = (self._write_counter % 10 == 0) or used_fallback or (not ok)
        if should_flush:
            self._save_domain_stats()

    def _load_domain_stats(self) -> dict:
        path = self.DOMAIN_STATS_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_domain_stats(self):
        path = self.DOMAIN_STATS_PATH
        try:
            payload = json.dumps(self.domain_stats, ensure_ascii=False, indent=2)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
        except Exception:
            # Non-fatal telemetry persistence
            return

try:
    from tools.scraper_crawl4ai import ScraperCrawl4AI
    # Check if the module has crawl4ai available by checking the HAS_CRAWL4AI flag
    # This will be False if crawl4ai is not installed
    import tools.scraper_crawl4ai as crawl4ai_module
    HAS_CRAWL4AI = getattr(crawl4ai_module, 'HAS_CRAWL4AI', False)
except (ImportError, AttributeError):
    HAS_CRAWL4AI = False

try:
    from tools.scraper_tool import ScraperTool
    HAS_ORIGINAL = True
except ImportError:
    HAS_ORIGINAL = False


def create_scraper(
    max_chars: int = 8000,
    timeout: int = 15,
    compliant_mode: bool = True,
    max_retries: int = 2,
    provider: str = "auto",  # "auto", "crawl4ai", "original"
):
    """
    Create scraper instance with best available provider.

    Args:
        max_chars: Max chars per page
        timeout: Timeout in seconds
        compliant_mode: Compliance mode (for original scraper)
        max_retries: Max retries
        provider: Which provider to use ("auto", "crawl4ai", "original")

    Returns:
        Scraper instance with extract_text(url) method
    """
    if provider == "auto":
        crawl4ai_available = HAS_CRAWL4AI
        if crawl4ai_available:
            try:
                log.info("Using Crawl4AI scraper (single-provider)")
                scraper = ScraperCrawl4AI(
                    max_chars=max_chars,
                    timeout=timeout,
                    compliant_mode=compliant_mode,
                    max_retries=max_retries,
                )
                # Wrap with fallback handler
                return _ScraperWithFallback(scraper, max_chars, timeout, compliant_mode, max_retries)
            except ImportError:
                log.warning("Crawl4AI instantiation failed, falling back to ScraperTool")
                crawl4ai_available = False

        if not crawl4ai_available and HAS_ORIGINAL:
            log.info(
                "Crawl4AI not available, using legacy ScraperTool. "
                "Install crawl4ai: pip install crawl4ai"
            )
            return ScraperTool(
                max_chars=max_chars,
                timeout=timeout,
                compliant_mode=compliant_mode,
                max_retries=max_retries,
            )
        else:
            raise ImportError(
                "No scraper available. Install crawl4ai or check ScraperTool."
            )

    elif provider == "crawl4ai":
        if not HAS_CRAWL4AI:
            raise ImportError("Crawl4AI not installed. pip install crawl4ai")
        try:
            scraper = ScraperCrawl4AI(
                max_chars=max_chars,
                timeout=timeout,
                compliant_mode=compliant_mode,
                max_retries=max_retries,
            )
            # Wrap with fallback handler
            return _ScraperWithFallback(scraper, max_chars, timeout, compliant_mode, max_retries)
        except ImportError as e:
            raise ImportError(f"Crawl4AI instantiation failed: {e}")

    elif provider == "original":
        if not HAS_ORIGINAL:
            raise ImportError("Original ScraperTool not available.")
        return ScraperTool(
            max_chars=max_chars,
            timeout=timeout,
            compliant_mode=compliant_mode,
            max_retries=max_retries,
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")
