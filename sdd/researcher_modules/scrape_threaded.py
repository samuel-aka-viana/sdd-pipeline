import time as time_module


def scrape_urls_parallel(
    urls_to_scrape: list[tuple],
    scraper,
    max_parallel_per_domain: int,
    async_batch_threshold: int,
    scrape_urls_batch_async_fn,
    logger,
) -> list[tuple]:
    """Scrape URLs sequencialmente para reduzir risco de travas por concorrência."""
    _ = max_parallel_per_domain
    _ = async_batch_threshold
    _ = scrape_urls_batch_async_fn

    scraped_results: list[tuple] = []
    for url, result_item in urls_to_scrape:
        scrape_start = time_module.time()
        try:
            result = scraper.extract_text(url)
        except Exception as exc:
            logger.warning(f"Sequential scrape failed for {url}: {exc}")
            result = {"status": "error"}
        result["elapsed"] = time_module.time() - scrape_start
        scraped_results.append((url, result, result_item))
    return scraped_results
