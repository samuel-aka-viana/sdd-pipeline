"""
Scraper factory: automatically selects best available provider.

Priority:
1. Crawl4AI (single dependency, fastest, handles JS + CF)
2. Original ScraperTool (fallback if crawl4ai not installed or fails)
"""
import logging

log = logging.getLogger(__name__)


class _ScraperWithFallback:
    """Wrapper that falls back from Crawl4AI to ScraperTool on repeated failures."""

    def __init__(self, crawl4ai_scraper, max_chars: int, timeout: int, compliant_mode: bool, max_retries: int):
        self.crawl4ai_scraper = crawl4ai_scraper
        self.fallback_scraper = None
        self.max_chars = max_chars
        self.timeout = timeout
        self.compliant_mode = compliant_mode
        self.max_retries = max_retries
        self.crawl4ai_failure_count = 0
        self.use_fallback = False

    def extract_text(self, url: str) -> dict:
        """Try Crawl4AI first; if it fails 3+ times, use fallback."""
        if self.use_fallback:
            return self._get_fallback_scraper().extract_text(url)

        result = self.crawl4ai_scraper.extract_text(url)

        # Track failures
        if result.get("status") in ("crawl4ai_error", "timeout", "http_429"):
            self.crawl4ai_failure_count += 1
            if self.crawl4ai_failure_count >= 3:
                log.warning(
                    f"Crawl4AI failed 3+ times, switching to fallback ScraperTool. "
                    f"(Current failure: {url})"
                )
                self.use_fallback = True
                return self._get_fallback_scraper().extract_text(url)
        else:
            # Reset count on success
            self.crawl4ai_failure_count = 0

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
