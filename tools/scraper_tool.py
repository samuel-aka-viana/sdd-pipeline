import logging
import time
import asyncio
import trafilatura
from trafilatura import extract
from trafilatura.settings import use_config
from urllib.parse import urlparse

log = logging.getLogger(__name__)

try:
    from curl_cffi import requests as cffi_requests
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class ScraperTool:

    def __init__(
        self,
        max_chars: int = 8000,
        timeout: int = 15,
        use_fallback: bool = True,
        compliant_mode: bool = True,
        max_retries: int = 2,
        browser_user_agent: str = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    ):
        self.max_chars = max_chars
        self.timeout = timeout
        self.use_fallback = use_fallback
        self.compliant_mode = compliant_mode
        self.max_retries = max_retries
        self.browser_user_agent = browser_user_agent
        self.config = use_config()
        self.config.set("DEFAULT", "DOWNLOAD_TIMEOUT", str(timeout))
        self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "200")

    def extract_text(self, url: str) -> dict:
        if HAS_CFFI:
            result = self.cffi_fetch(url)
            if result["status"] == "ok":
                return result
            if result["status"] == "cffi_cloudflare_challenge" and self.use_fallback and HAS_PLAYWRIGHT:
                playwright_result = self.playwright_extract(url)
                if playwright_result["status"] == "ok":
                    return playwright_result

        result = self.trafilatura_extract(url)
        if result["status"] == "ok":
            return result

        if self.use_fallback and HAS_PLAYWRIGHT:
            playwright_result = self.playwright_extract(url)
            if playwright_result["status"] == "ok":
                return playwright_result

        return result

    def cffi_fetch(self, url: str) -> dict:
        last_status = "cffi_failed"
        for attempt_number in range(self.max_retries + 1):
            try:
                response = cffi_requests.get(
                    url,
                    impersonate="chrome",
                    timeout=self.timeout,
                    headers=self.build_browser_headers(url),
                )
                if self.is_cloudflare_challenge(
                    body_text=response.text,
                    status_code=response.status_code,
                ):
                    return {"url": url, "text": "", "status": "cffi_cloudflare_challenge"}

                if response.status_code != 200:
                    last_status = f"cffi_http_{response.status_code}"
                    if response.status_code in {403, 429, 503} and attempt_number < self.max_retries:
                        time.sleep(0.6 * (attempt_number + 1))
                        continue
                    return {"url": url, "text": "", "status": last_status}

                text = extract(
                    response.text,
                    include_links=False,
                    include_images=False,
                    output_format="markdown",
                )

                if not text or len(text) < 100:
                    last_status = "cffi_empty_extract"
                    if attempt_number < self.max_retries:
                        time.sleep(0.35 * (attempt_number + 1))
                        continue
                    return {"url": url, "text": "", "status": last_status}

                return {
                    "url": url,
                    "text": text[: self.max_chars],
                    "status": "ok",
                    "source": "cffi",
                    "truncated": len(text) > self.max_chars,
                }
            except Exception as error:
                error_type = type(error).__name__
                last_status = "cffi_error"
                log.debug(f"cffi [{error_type}] attempt {attempt_number + 1}: {url[:60]}")
                if attempt_number < self.max_retries:
                    time.sleep(0.4 * (attempt_number + 1))
                    continue
                return {"url": url, "text": "", "status": last_status}

        return {"url": url, "text": "", "status": last_status}

    def trafilatura_extract(self, url: str) -> dict:
        try:
            downloaded = trafilatura.fetch_url(url, config=self.config)
            if not downloaded:
                return {"url": url, "text": "", "status": "trafilatura_fetch_failed"}

            text = extract(
                downloaded,
                include_links=False,
                include_images=False,
                output_format="markdown",
                config=self.config,
            )

            if not text or len(text) < 100:
                return {"url": url, "text": "", "status": "trafilatura_empty"}

            return {
                "url": url,
                "text": text[: self.max_chars],
                "status": "ok",
                "source": "trafilatura",
                "truncated": len(text) > self.max_chars,
            }
        except Exception as e:
            error_type = type(e).__name__
            # Minimal logging for trafilatura errors
            log.debug(f"trafilatura [{error_type}]: {url[:60]}")
            return {"url": url, "text": "", "status": "trafilatura_error"}

    def playwright_extract(self, url: str) -> dict:
        """Sync wrapper around async playwright extraction. Creates own event loop per call."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._playwright_extract_async(url))
            return result
        except Exception as error:
            error_type = type(error).__name__
            log.debug(f"playwright async init failed [{error_type}]: {url[:60]}")
            return {"url": url, "text": "", "status": "playwright_error"}
        finally:
            try:
                loop.close()
            except Exception:
                pass

    async def _playwright_extract_async(self, url: str) -> dict:
        """Async playwright extraction using proper async context."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)

                context_opts = {
                    "user_agent": self.browser_user_agent,
                } if self.compliant_mode else {}

                if self.compliant_mode:
                    context_opts.update({
                        "locale": "en-US",
                        "timezone_id": "America/New_York",
                        "viewport": {"width": 1366, "height": 768},
                        "java_script_enabled": True,
                        "extra_http_headers": {
                            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.7",
                            "DNT": "1",
                        },
                    })

                context = await browser.new_context(**context_opts)
                page = await context.new_page()

                try:
                    response = await page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
                    await page.wait_for_load_state("networkidle", timeout=self.timeout * 1000)
                    page_html = await page.content()
                    page_title = (await page.title() or "").strip()
                    status_code = response.status if response else 0

                    if self.is_cloudflare_challenge(
                        body_text=f"{page_title}\n{page_html}",
                        status_code=status_code,
                    ):
                        await page.close()
                        await context.close()
                        await browser.close()
                        return {"url": url, "text": "", "status": "cloudflare_challenge"}

                    text = await page.inner_text("body")

                    if not text or len(text) < 100:
                        await page.close()
                        await context.close()
                        await browser.close()
                        return {"url": url, "text": "", "status": "playwright_empty"}

                    result = {
                        "url": url,
                        "text": text[: self.max_chars],
                        "status": "ok",
                        "source": "playwright",
                        "truncated": len(text) > self.max_chars,
                    }

                    await page.close()
                    await context.close()
                    await browser.close()
                    return result

                except asyncio.TimeoutError:
                    await page.close()
                    await context.close()
                    await browser.close()
                    log.debug(f"playwright timeout: {url[:60]} ({self.timeout}s)")
                    return {"url": url, "text": "", "status": "playwright_timeout"}
                except Exception as e:
                    await page.close()
                    await context.close()
                    await browser.close()
                    error_type = type(e).__name__
                    log.debug(f"playwright page error [{error_type}]: {url[:60]}")
                    return {"url": url, "text": "", "status": "playwright_error"}

        except asyncio.TimeoutError:
            log.debug(f"playwright timeout: {url[:60]} ({self.timeout}s)")
            return {"url": url, "text": "", "status": "playwright_timeout"}
        except Exception as error:
            error_type = type(error).__name__
            log.debug(f"playwright failed [{error_type}]: {url[:60]}")
            return {"url": url, "text": "", "status": "playwright_error"}

    def build_browser_headers(self, url: str) -> dict:
        if not self.compliant_mode:
            return {}
        host = self.extract_host(url)
        return {
            "User-Agent": self.browser_user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "Referer": f"https://{host}/",
        }

    def extract_host(self, url: str) -> str:
        parsed_url = urlparse(url)
        return parsed_url.netloc or "localhost"

    def is_cloudflare_challenge(self, body_text: str, status_code: int = 0) -> bool:
        if not body_text:
            return status_code in {403, 429, 503}
        normalized_body = body_text.lower()
        challenge_markers = (
            "cloudflare",
            "attention required",
            "just a moment",
            "checking your browser",
            "cf-challenge",
            "/cdn-cgi/challenge-platform",
            "verify you are human",
        )
        has_marker = any(challenge_marker in normalized_body for challenge_marker in challenge_markers)
        return has_marker and status_code in {0, 403, 429, 503, 200}

