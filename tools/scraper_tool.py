import logging
import trafilatura
from trafilatura import extract
from trafilatura.settings import use_config

log = logging.getLogger(__name__)

try:
    from curl_cffi import requests as cffi_requests
    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


class ScraperTool:

    def __init__(self, max_chars: int = 8000, timeout: int = 15, use_fallback: bool = True):
        self.max_chars = max_chars
        self.timeout = timeout
        self.use_fallback = use_fallback
        self.config = use_config()
        self.config.set("DEFAULT", "DOWNLOAD_TIMEOUT", str(timeout))
        self.config.set("DEFAULT", "MIN_OUTPUT_SIZE", "200")

    def extract_text(self, url: str) -> dict:
        if HAS_CFFI:
            result = self.cffi_fetch(url)
            if result["status"] == "ok":
                return result

        result = self.trafilatura_extract(url)
        if result["status"] == "ok":
            return result

        if self.use_fallback and HAS_PLAYWRIGHT:
            playwright_result = self.playwright_extract(url)
            if playwright_result["status"] == "ok":
                return playwright_result

        return result

    def cffi_fetch(self, url: str) -> dict:
        try:
            resp = cffi_requests.get(url, impersonate="chrome", timeout=self.timeout)
            if resp.status_code != 200:
                return {"url": url, "text": "", "status": f"cffi_http_{resp.status_code}"}

            text = extract(
                resp.text,
                include_links=False,
                include_images=False,
                output_format="markdown",
            )

            if not text or len(text) < 100:
                return {"url": url, "text": "", "status": "cffi_empty_extract"}

            return {
                "url": url,
                "text": text[: self.max_chars],
                "status": "ok",
                "source": "cffi",
                "truncated": len(text) > self.max_chars,
            }
        except Exception as e:
            log.debug("cffi failed: %s — %s", url, e)
            return {"url": url, "text": "", "status": f"cffi_error: {e}"}

    def trafilatura_extract(self, url: str) -> dict:
        try:
            downloaded = trafilatura.fetch_url(url, config=self.config)
            if not downloaded:
                return {"url": url, "text": "", "status": "fetch_failed"}

            text = extract(
                downloaded,
                include_links=False,
                include_images=False,
                output_format="markdown",
                config=self.config,
            )

            if not text or len(text) < 100:
                return {"url": url, "text": "", "status": "empty_extract"}

            return {
                "url": url,
                "text": text[: self.max_chars],
                "status": "ok",
                "source": "trafilatura",
                "truncated": len(text) > self.max_chars,
            }
        except Exception as e:
            return {"url": url, "text": "", "status": f"trafilatura_error: {e}"}

    def playwright_extract(self, url: str) -> dict:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=self.timeout * 1000)
                page.wait_for_load_state("networkidle", timeout=self.timeout * 1000)
                text = page.inner_text("body")
                browser.close()

            if not text or len(text) < 100:
                return {"url": url, "text": "", "status": "playwright_empty"}

            return {
                "url": url,
                "text": text[: self.max_chars],
                "status": "ok",
                "source": "playwright",
                "truncated": len(text) > self.max_chars,
            }
        except Exception as e:
            log.warning("playwright fallback failed: %s — %s", url, e)
            return {"url": url, "text": "", "status": f"playwright_error: {e}"}
