import asyncio
import time as time_module
from urllib.parse import urlparse


async def async_crawl_task(
    crawler,
    url: str,
    result_item: dict,
    config,
    domain_semaphore,
    extract_redirect_target_fn,
    extract_best_markdown_fn,
    is_low_quality_text_fn,
    max_chars_per_scrape: int,
    logger,
):
    """Single async crawl task with timing."""
    async with domain_semaphore:
        scrape_start = time_module.time()
        try:
            result = await crawler.arun(url=url, config=config)
            scrape_elapsed = time_module.time() - scrape_start

            if 300 <= result.status_code < 400:
                redirect_target = extract_redirect_target_fn(result, url)
                if redirect_target and redirect_target != url:
                    result = await crawler.arun(url=redirect_target, config=config)
                    scrape_elapsed = time_module.time() - scrape_start

            if result.status_code != 200:
                return (
                    url,
                    {
                        "status": f"http_{result.status_code}",
                        "text": "",
                        "truncated": False,
                        "url": url,
                        "source": "crawl4ai",
                        "elapsed": scrape_elapsed,
                        "html": result.html or "",
                    },
                    result_item,
                )

            markdown_obj = getattr(result, "markdown", None)
            text = extract_best_markdown_fn(markdown_obj)
            markdown = text
            html_raw = result.html or ""

            if not text and result.html:
                try:
                    from trafilatura import extract as traf_extract
                    text = traf_extract(
                        result.html,
                        include_links=False,
                        include_images=False,
                        output_format="markdown",
                    )
                except Exception:
                    text = result.html[:1000]

            if is_low_quality_text_fn(text) and result.html:
                try:
                    from trafilatura import extract as traf_extract
                    better_text = traf_extract(
                        result.html,
                        include_links=False,
                        include_images=False,
                        output_format="markdown",
                    )
                    if better_text and not is_low_quality_text_fn(better_text):
                        text = better_text
                except Exception:
                    pass

            if not text:
                return (
                    url,
                    {
                        "status": "parse_error",
                        "text": "",
                        "truncated": False,
                        "url": url,
                        "source": "crawl4ai",
                        "elapsed": scrape_elapsed,
                        "html": html_raw,
                    },
                    result_item,
                )

            if is_low_quality_text_fn(text):
                return (
                    url,
                    {
                        "status": "low_quality_content",
                        "text": text[:max_chars_per_scrape],
                        "text_full": text,
                        "truncated": len(text) > max_chars_per_scrape,
                        "url": url,
                        "source": "crawl4ai",
                        "elapsed": scrape_elapsed,
                        "html": html_raw,
                        "quality_reason": "content_too_short_or_ui_noise",
                    },
                    result_item,
                )

            truncated = len(text) > max_chars_per_scrape
            text_full = text
            text = text[:max_chars_per_scrape]

            return (
                url,
                {
                    "status": "ok",
                    "text": text,
                    "text_full": text_full,
                    "markdown": markdown,
                    "truncated": truncated,
                    "url": url,
                    "source": "crawl4ai",
                    "elapsed": scrape_elapsed,
                    "html": html_raw,
                },
                result_item,
            )

        except asyncio.TimeoutError:
            return (
                url,
                {
                    "status": "timeout",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                    "elapsed": time_module.time() - scrape_start,
                    "html": "",
                },
                result_item,
            )
        except Exception as exc:
            logger.debug(f"Async crawl failed for {url}: {exc}")
            return (
                url,
                {
                    "status": "crawl4ai_error",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                    "elapsed": time_module.time() - scrape_start,
                    "html": "",
                    "error_detail": str(exc),
                },
                result_item,
            )


def scrape_urls_batch_async(
    urls_to_scrape: list[tuple],
    build_crawl4ai_run_config_fn,
    extract_redirect_target_fn,
    extract_best_markdown_fn,
    is_low_quality_text_fn,
    max_chars_per_scrape: int,
    max_parallel_per_domain: int,
    logger,
) -> list[tuple]:
    """Scrape 10+ URLs using async batching (much faster than threading)."""

    async def batch_scrape():
        from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

        config = build_crawl4ai_run_config_fn(CrawlerRunConfig)

        scraped_results = []
        domain_semaphores: dict[str, asyncio.Semaphore] = {}

        async with AsyncWebCrawler(always_by_pass_cache=False) as crawler:
            tasks = []
            for url, result_item in urls_to_scrape:
                domain = (urlparse(url).netloc or "unknown").lower()
                semaphore = domain_semaphores.get(domain)
                if semaphore is None:
                    semaphore = asyncio.Semaphore(max_parallel_per_domain)
                    domain_semaphores[domain] = semaphore
                task = async_crawl_task(
                    crawler=crawler,
                    url=url,
                    result_item=result_item,
                    config=config,
                    domain_semaphore=semaphore,
                    extract_redirect_target_fn=extract_redirect_target_fn,
                    extract_best_markdown_fn=extract_best_markdown_fn,
                    is_low_quality_text_fn=is_low_quality_text_fn,
                    max_chars_per_scrape=max_chars_per_scrape,
                    logger=logger,
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    logger.debug(f"Async batch scrape error: {result}")
                    continue
                scraped_results.append(result)

        return scraped_results

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(batch_scrape())
    finally:
        loop.close()
