"""
Unified scraper using Crawl4AI as primary provider.
Simplified, faster, and single-dependency scraping layer.
"""
import logging
import time
import random
from urllib.parse import urlparse, urljoin

log = logging.getLogger(__name__)

try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
    HAS_CRAWL4AI = True
except ImportError:
    HAS_CRAWL4AI = False

try:
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    HAS_MARKDOWN_FILTERS = True
except ImportError:
    HAS_MARKDOWN_FILTERS = False

try:
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

    def _build_run_config(self):
        kwargs = {
            "wait_until": "domcontentloaded",
            "word_count_threshold": 10,
            "excluded_tags": ["nav", "footer", "header", "aside", "form"],
            "remove_overlay_elements": True,
        }
        if HAS_MARKDOWN_FILTERS:
            kwargs["markdown_generator"] = DefaultMarkdownGenerator(
                content_filter=PruningContentFilter(
                    threshold=0.45,
                    threshold_type="dynamic",
                    min_word_threshold=8,
                ),
                options={"ignore_links": True},
            )
        return CrawlerRunConfig(**kwargs)

    def _is_low_quality_text(self, text: str) -> bool:
        cleaned = (text or "").strip()
        if not cleaned:
            return True
        sample = cleaned.lower()[:320]
        noise_markers = (
            "skip to main content",
            "report a website issue",
            "start a new chat",
            "what can i help you with",
            "i'm gordon, your ai assistant",
            "open in app",
            "navigation menu",
            "cookie",
        )
        if any(marker in sample for marker in noise_markers):
            return True
        return len(cleaned) < 500

    def _extract_redirect_target(self, result, source_url: str) -> str:
        redirected_url = getattr(result, "redirected_url", "") or ""
        if redirected_url and redirected_url != source_url:
            return redirected_url
        headers = getattr(result, "response_headers", {}) or {}
        location = headers.get("location") or headers.get("Location")
        if location:
            return urljoin(source_url, str(location))
        return ""

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

                if self._should_retry_status(result["status"], attempt):
                    time.sleep(self._backoff_sleep(attempt, result["status"]))
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
                        "error_detail": str(e),
                    }
                time.sleep(0.5 * (attempt + 1))

        return {
            "status": "failed",
            "text": "",
            "truncated": False,
            "url": url,
            "source": "crawl4ai",
        }

    def _should_retry_status(self, status: str, attempt: int) -> bool:
        if attempt >= self.max_retries:
            return False
        # Retry transient and anti-bot statuses.
        retryable = {
            "timeout",
            "http_429",
            "http_503",
            "http_403",
            "crawl4ai_error",
            "parse_error",
        }
        return status in retryable

    def _backoff_sleep(self, attempt: int, status: str) -> float:
        base = {
            "http_429": 1.2,
            "http_503": 1.0,
            "http_403": 0.9,
            "timeout": 0.8,
            "crawl4ai_error": 0.6,
            "parse_error": 0.4,
        }.get(status, 0.5)
        jitter = random.uniform(0.05, 0.35)
        return base * (attempt + 1) + jitter

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
                "error_detail": str(e),
            }

    def _extract_markdown_text(self, result) -> str:
        """Support Crawl4AI v0.8+ markdown API and older string-shaped results."""
        markdown_obj = getattr(result, "markdown", None)
        fit_markdown = getattr(markdown_obj, "fit_markdown", None)
        if fit_markdown and fit_markdown.strip() and len(fit_markdown.strip()) >= 500:
            return fit_markdown
        if hasattr(markdown_obj, "raw_markdown"):
            raw_markdown = markdown_obj.raw_markdown or ""
            if raw_markdown.strip():
                return raw_markdown
            return raw_markdown
        if isinstance(markdown_obj, str):
            return markdown_obj
        return ""

    async def _async_crawl(self, url: str) -> dict:
        """Async crawl using Crawl4AI."""
        config = self._build_run_config()

        async with AsyncWebCrawler(always_by_pass_cache=False) as crawler:
            result = await crawler.arun(url=url, config=config)

            if 300 <= result.status_code < 400:
                redirect_target = self._extract_redirect_target(result, url)
                if redirect_target and redirect_target != url:
                    result = await crawler.arun(url=redirect_target, config=config)

            if result.status_code != 200:
                return {
                    "status": f"http_{result.status_code}",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                }

            # Prefer markdown format from crawl4ai
            text = self._extract_markdown_text(result)
            html_raw = result.html or ""

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

            # If content still looks like UI/chrome noise, try trafilatura as secondary fallback.
            if self._is_low_quality_text(text) and result.html and HAS_TRAFILATURA:
                try:
                    from trafilatura import extract as traf_extract
                    better_text = traf_extract(
                        result.html,
                        include_links=False,
                        include_images=False,
                        output_format="markdown",
                    )
                    if better_text and not self._is_low_quality_text(better_text):
                        text = better_text
                except Exception:
                    pass

            if not text:
                return {
                    "status": "parse_error",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                }

            if self._is_low_quality_text(text):
                return {
                    "status": "low_quality_content",
                    "text": text[: self.max_chars],
                    "text_full": text,
                    "truncated": len(text) > self.max_chars,
                    "url": url,
                    "source": "crawl4ai",
                    "html": html_raw,
                    "quality_reason": "content_too_short_or_ui_noise",
                }

            # Truncate if needed
            truncated = len(text) > self.max_chars
            text_full = text
            text = text[: self.max_chars]

            return {
                "status": "ok",
                "text": text,
                "text_full": text_full,
                "truncated": truncated,
                "url": url,
                "source": "crawl4ai",
                "html": html_raw,
            }
