def build_context(
    results_by_query,
    tool: str,
    max_scrapes_per_tool: int,
    max_chars_per_scrape: int,
    chroma,
    memory,
    active_chain_run,
    should_skip_url_fn,
    log_url_found_fn,
    write_chain_phase_fn,
    scrape_urls_parallel_fn,
    save_html_debug_fn,
    extract_section_structure_fn,
    infer_source_quality_fn,
    scraped_urls_store: dict,
    url_richness_store: dict,
    logger,
):
    """Build scraped context for LLM from search results with chaining telemetry."""
    lines = []
    seen_urls: set[str] = set()
    urls_to_scrape = []
    discovered_count = 0
    snippet_fallback_count = 0
    chain_run = active_chain_run

    for query, results in results_by_query.items():
        lines.append(f"\n### Busca: {query}")

        for result_item in results:
            url = result_item.get("url", "")
            if not url.startswith("http") or url in seen_urls:
                continue
            if should_skip_url_fn(url):
                log_url_found_fn(url, status="skipped", phase="filtered_skip")
                if chain_run:
                    chain_run["phases"]["discovery"].append({
                        "query": query,
                        "url": url,
                        "title": result_item.get("title", ""),
                        "snippet": (result_item.get("snippet", "") or "")[:240],
                        "selected_for_scrape": False,
                        "status": "skipped",
                        "reason": "filtered_skip",
                    })
                continue
            seen_urls.add(url)
            discovered_count += 1
            snippet_preview = (result_item.get("snippet", "") or "").replace("\n", " ").strip()[:100]
            log_url_found_fn(
                url,
                title=result_item.get("snippet", "")[:40],
                status="discovered",
                phase="search_discovered",
                preview=snippet_preview,
            )

            if len(urls_to_scrape) < max_scrapes_per_tool:
                urls_to_scrape.append((url, result_item))
                if chain_run:
                    chain_run["phases"]["discovery"].append({
                        "query": query,
                        "url": url,
                        "title": result_item.get("title", ""),
                        "snippet": (result_item.get("snippet", "") or "")[:240],
                        "selected_for_scrape": True,
                        "status": "queued",
                    })
            else:
                snippet_fallback_count += 1
                lines.append(f"URL: {url}")
                lines.append(f"Resumo: {result_item.get('snippet', '')}")
                lines.append("---")
                title = result_item.get("snippet", "")[:40]
                log_url_found_fn(
                    url,
                    title=title,
                    status="snippet_fallback",
                    phase="snippet_fallback",
                    preview=snippet_preview,
                )
                if chain_run:
                    chain_run["phases"]["discovery"].append({
                        "query": query,
                        "url": url,
                        "title": result_item.get("title", ""),
                        "snippet": (result_item.get("snippet", "") or "")[:240],
                        "selected_for_scrape": False,
                        "status": "snippet_fallback",
                        "reason": "max_scrapes_limit",
                    })

    if chain_run:
        write_chain_phase_fn("discovery", {
            "tool": tool,
            "max_scrapes_per_tool": max_scrapes_per_tool,
            "results_count": len(chain_run["phases"]["discovery"]),
            "entries": chain_run["phases"]["discovery"],
        })

    scraped_results = scrape_urls_parallel_fn(urls_to_scrape, tool)

    for url, result, result_item in scraped_results:
        save_html_debug_fn(
            tool=tool,
            url=url,
            html=result.get("html", "") or "",
            status=result.get("status", "unknown"),
            source=result.get("source", ""),
            snippet=(result_item.get("snippet", "") if isinstance(result_item, dict) else ""),
        )
        if chain_run:
            chain_run["phases"]["scrape"].append({
                "url": url,
                "status": result.get("status", "unknown"),
                "elapsed_seconds": result.get("elapsed", 0),
                "source": result.get("source", ""),
                "error_detail": result.get("error_detail", ""),
                "quality_reason": result.get("quality_reason", ""),
            })
        if result["status"] == "ok":
            text = result["text"][:max_chars_per_scrape]
            tag = " [TRUNCADO]" if result.get("truncated") else ""
            lines.append(f"URL: {url}{tag}")
            lines.append(f"Conteúdo Extraído:\n{text}")
            lines.append("---")
            title = text.split("\n")[0][:40] if text else ""

            scraped_urls_store[url] = result["text"]

            markdown_raw = result.get("markdown", "")
            if not markdown_raw and result.get("source") == "crawl4ai":
                markdown_raw = result["text"]

            structure = extract_section_structure_fn(url, markdown_raw)
            url_richness_store[url] = structure

            if chroma is not None:
                content_text = result.get("text_full") or result.get("text", "")
                if content_text:
                    content_preview = content_text[:200]
                    memory.log_event("scraped_content_preview", {
                        "tool": tool,
                        "url": url[:60],
                        "preview": content_preview,
                        "total_chars": len(content_text),
                    })

                    source_quality = infer_source_quality_fn(url)
                    success = chroma.save_scraped_content(
                        tool=tool,
                        url=url,
                        title=title,
                        content=content_text,
                        markdown_raw=markdown_raw,
                        source_quality=source_quality,
                        scrape_elapsed_seconds=result.get("elapsed", 0),
                    )
                    chunks_count = len(chroma.chunk_content(content_text)) if success else 0
                    if chain_run:
                        chain_run["phases"]["index"].append({
                            "url": url,
                            "success": bool(success),
                            "content_chars": len(content_text),
                            "chunk_count": chunks_count,
                            "source_quality": source_quality,
                        })
                    if success:
                        memory.log_event("chroma_save", {
                            "tool": tool,
                            "url": url,
                            "content_chars": len(content_text),
                            "chunk_count": chunks_count,
                            "source_quality": source_quality,
                        })
                    else:
                        logger.warning(f"Failed to save to Chroma: {url[:60]}")

            content_text = result.get("text", "")
            preview = content_text[:100].replace("\n", " ")[:80] if content_text else "[VAZIO]"
            if chain_run:
                chain_run["phases"]["extract"].append({
                    "url": url,
                    "status": "ok",
                    "chars": len(content_text),
                    "truncated": bool(result.get("truncated")),
                    "preview_100": (result.get("text", "") or "")[:100],
                })
            memory.log_event("content_extracted", {
                "url": url[:60],
                "status": "ok" if content_text else "empty",
                "preview": preview,
                "chars": len(content_text),
            })

            log_url_found_fn(
                url,
                title=title,
                status="ok",
                elapsed=result.get("elapsed", 0),
                source=result.get("source", ""),
                scrape_status=result.get("status", "ok"),
                phase="scrape_ok",
                preview=preview,
            )
        else:
            error_msg = result.get("status", "unknown_error")
            memory.log_event("content_extraction_failed", {
                "url": url[:60],
                "error": error_msg,
                "error_detail": result.get("error_detail", ""),
                "elapsed": result.get("elapsed", 0),
            })

            snippet = result_item.get("snippet", "")
            if snippet:
                lines.append(f"URL: {url} [SCRAPE_FALHOU: {result['status']}]")
                lines.append(f"Resumo (fallback): {snippet}")
                lines.append("---")
                scraped_urls_store[url] = snippet
            if chain_run:
                chain_run["phases"]["extract"].append({
                    "url": url,
                    "status": "snippet_fallback" if snippet else "failed_no_snippet",
                    "chars": len(snippet or ""),
                    "truncated": False,
                    "preview_100": (snippet or "")[:100],
                    "error": result.get("status", "unknown_error"),
                })

            log_url_found_fn(
                url,
                title=f"[{result['status']}]",
                status="scrape_failed",
                elapsed=result.get("elapsed", 0),
                scrape_status=result.get("status", ""),
                phase="scrape_failed",
                preview=(snippet or "").replace("\n", " ").strip()[:100],
            )

    scrape_ok = sum(1 for r in scraped_results if r[1]["status"] == "ok")
    scrape_fail = sum(1 for r in scraped_results if r[1]["status"] != "ok")

    last_scrape_stats = {
        "discovered": discovered_count,
        "ok": scrape_ok,
        "fail": scrape_fail,
        "snippet_fallback": snippet_fallback_count,
        "skipped": len(seen_urls) - len(urls_to_scrape),
    }
    if chain_run:
        write_chain_phase_fn("scrape", {
            "tool": tool,
            "stats": last_scrape_stats,
            "entries": chain_run["phases"]["scrape"],
        })
        write_chain_phase_fn("extract", {
            "tool": tool,
            "max_chars_per_scrape": max_chars_per_scrape,
            "entries": chain_run["phases"]["extract"],
        })
        write_chain_phase_fn("index", {
            "tool": tool,
            "enabled": chroma is not None,
            "entries": chain_run["phases"]["index"],
        })

    return "\n".join(lines), last_scrape_stats
