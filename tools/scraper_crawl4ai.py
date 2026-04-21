"""
Unified scraper using Crawl4AI as primary provider.
Simplified, faster, and single-dependency scraping layer.
"""
import logging
import time
from urllib.parse import urlparse

log = logging.getLogger(__name__)

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False

try:
    from trafilatura import extract
    from trafilatura.settings import use_config
    HAS_TRAFILATURA = True
except ImportError:
    HAS_TRAFILATURA = False


class ScraperCrawl4AI:
    """
    Unified scraper using Crawl4AI as primary provider.

    Advantages over playwright/curl_cffi combo:
    - Single dependency (crawl4ai)
    - Handles JS rendering, CloudFlare, headers automatically
    - Faster than playwright for most cases
    - Simpler codebase, fewer fallbacks needed
    """

    def __init__(
        self,
        max_chars: int = 8000,
        timeout: int = 15,
        compliant_mode: bool = True,
        max_retries: int = 2,
    ):
        if not HAS_CRAWL4AI:
            raise ImportError(
                "crawl4ai not installed. Install with: pip install crawl4ai"
            )

        self.max_chars = max_chars
        self.timeout = timeout
        self.compliant_mode = compliant_mode
        self.max_retries = max_retries
        self.config = None
        if HAS_TRAFILATURA:
            self.config = use_config()
            self.config.set("DEFAULT", "DOWNLOAD_TIMEOUT", str(timeout))
            self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "200")

    def extract_text(self, url: str) -> dict:
        """
        Extract text from URL using Crawl4AI.

        Returns:
            dict with keys:
                - status: "ok", "timeout", "http_error", "parse_error", "invalid_url"
                - text: extracted markdown text (empty if failed)
                - truncated: bool, whether content was truncated to max_chars
                - source: "crawl4ai"
        """
        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return {
                    "status": "invalid_url",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                }
        except Exception:
            return {
                "status": "invalid_url",
                "text": "",
                "truncated": False,
                "url": url,
                "source": "crawl4ai",
            }

        # Try Crawl4AI
        for attempt in range(self.max_retries + 1):
            try:
                result = self._crawl4ai_extract(url)
                if result["status"] == "ok":
                    return result

                # Retry on rate-limit or temp error
                if result["status"] in ("timeout", "http_429", "http_503"):
                    if attempt < self.max_retries:
                        time.sleep(0.5 * (attempt + 1))
                        continue

                return result

            except Exception as e:
                log.warning(f"Crawl4AI extraction error for {url}: {e}")
                if attempt == self.max_retries:
                    return {
                        "status": "crawl4ai_error",
                        "text": "",
                        "truncated": False,
                        "url": url,
                        "source": "crawl4ai",
                    }
                time.sleep(0.5 * (attempt + 1))

        return {
            "status": "failed",
            "text": "",
            "truncated": False,
            "url": url,
            "source": "crawl4ai",
        }

    def _crawl4ai_extract(self, url: str) -> dict:
        """Use Crawl4AI to extract page content."""
        import asyncio

        try:
            # Run async crawl4ai in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._async_crawl(url))
            loop.close()
            return result
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "text": "",
                "truncated": False,
                "url": url,
                "source": "crawl4ai",
            }
        except Exception as e:
            log.debug(f"Crawl4AI failed: {e}")
            return {
                "status": "crawl4ai_error",
                "text": "",
                "truncated": False,
                "url": url,
                "source": "crawl4ai",
            }

    async def _async_crawl(self, url: str) -> dict:
        """Async crawl using Crawl4AI."""
        config = CrawlerRunConfig(
            wait_until="domcontentloaded",  # Wait for DOM, not full page load
        )

        async with AsyncWebCrawler(always_by_pass_cache=False) as crawler:
            result = await crawler.arun(url=url, config=config)

            if result.status_code != 200:
                return {
                    "status": f"http_{result.status_code}",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                }

            # Prefer markdown format from crawl4ai
            text = result.markdown_v2.raw_markdown if result.markdown_v2 else ""

            if not text and result.html:
                # Fallback: extract from HTML using trafilatura if available
                if HAS_TRAFILATURA:
                    try:
                        from trafilatura import extract as traf_extract

                        text = traf_extract(
                            result.html,
                            include_links=False,
                            include_images=False,
                            output_format="markdown",
                        )
                    except Exception:
                        text = result.html[:1000]  # Raw HTML fallback
                else:
                    text = result.html[:1000]

            if not text:
                return {
                    "status": "parse_error",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                }

            # Truncate if needed
            truncated = len(text) > self.max_chars
            text = text[: self.max_chars]

            return {
                "status": "ok",
                "text": text,
                "truncated": truncated,
                "url": url,
                "source": "crawl4ai",
            }
