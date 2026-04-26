from __future__ import annotations

from tools.scraper_crawl4ai import ScraperCrawl4AI


def test_navigation_in_progress_error_is_classified_as_retryable():
    scraper = object.__new__(ScraperCrawl4AI)
    scraper.max_retries = 2

    result = scraper._classify_crawl4ai_exception(
        RuntimeError(
            "Page.content: Unable to retrieve content because the page is navigating and changing the content."
        )
    )

    assert result["status"] == "navigation_in_progress"
    assert scraper._should_retry_status("navigation_in_progress", attempt=0) is True


def test_navigation_in_progress_gets_longer_backoff():
    scraper = object.__new__(ScraperCrawl4AI)
    delay = scraper._backoff_sleep(0, "navigation_in_progress")
    assert delay >= 1.2
