def _to_list_safe(value) -> list:
    """Normaliza coleções (incluindo arrays) para lista sem bool ambíguo."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    try:
        return list(value)
    except TypeError:
        return [value]


def run_research(
    tool,
    alternative,
    foco,
    questoes,
    refresh_search,
    targeted_questions_only,
    urls,
    skip_search,
    build_queries_fn,
    new_chain_run_fn,
    search_multi_fn,
    memory,
    load_domain_scrape_stats_fn,
    filter_search_results_fn,
    count_results_fn,
    save_urls_fn,
    build_context_fn,
    save_context_debug_fn,
    get_lessons_for_prompt_fn,
    prompts_get_fn,
    llm_generate_fn,
    model,
    temp,
    ctx_len,
    timeout,
    get_active_chain_run_fn,
    write_chain_phase_fn,
    finalize_chain_run_fn,
    logger,
    get_last_scrape_stats_fn,
):
    questoes = _to_list_safe(questoes)
    logger.debug(f"Starting research for tool: {tool}, foco: {foco}")

    queries = build_queries_fn(
        tool=tool,
        alternative=alternative,
        foco=foco,
        questoes=questoes,
        targeted_questions_only=targeted_questions_only,
    )
    logger.debug(f"Built {len(queries)} search queries")
    new_chain_run_fn(
        tool=tool,
        foco=foco,
        alternative=alternative,
        queries=queries,
    )

    urls_list = _to_list_safe(urls)
    if skip_search and len(urls_list) > 0:
        logger.info(f"⏭️  Skipping web search - using {len(urls_list)} provided URLs")
        url_results = [
            {"url": url.strip(), "title": url.strip()[:50], "snippet": ""}
            for url in urls_list
            if str(url).strip()
        ]
        results_by_query = {"provided_urls": url_results}
        memory.log_event("search_skipped", {
            "tool": tool,
            "urls_provided": len(url_results),
        })
    else:
        results_by_query = search_multi_fn(queries, force_refresh=refresh_search)
        logger.debug(f"Got search results for {len(results_by_query)} queries")

    for query, results in results_by_query.items():
        results_count = len(results) if results else 0
        if results_count < 3:
            logger.info(f"⚠️  Weak query results ({results_count}): {query}")
            memory.log_event("weak_search_query", {
                "tool": tool,
                "query": query,
                "results_count": results_count,
            })

    load_domain_scrape_stats_fn()
    filtered_results_by_query = filter_search_results_fn(
        results_by_query=results_by_query,
        tool=tool,
        alternative=alternative,
    )
    filtered_out_count = count_results_fn(results_by_query) - count_results_fn(filtered_results_by_query)
    if filtered_out_count > 0:
        logger.info(
            "Search guardrail filtered %d URL(s) for non-relevant/video/social domains",
            filtered_out_count,
        )

    save_urls_fn(filtered_results_by_query, f"output/urls_{tool}.txt")

    context = build_context_fn(filtered_results_by_query, tool=tool)

    logger.debug("Context built: %s chars", len(context))
    last_scrape_stats = get_last_scrape_stats_fn() or {}

    # rely on owner object for last_scrape_stats; thin-context fallback checks via chain store not required

    if last_scrape_stats.get("discovered", 0) == 0 and alternative and not skip_search:
            logger.warning(
                f"⚠️  Zero context for '{tool}' — retrying with reversed-perspective queries"
            )
            memory.log_event("research_thin_context_fallback", {
                "tool": tool,
                "alternative": alternative,
                "original_context_chars": len(context),
            })
            fallback_queries = [
                f"{alternative} vs {tool} comparison",
                f"{alternative} vs {tool} pros cons 2024 2025",
                f"{alternative} vs {tool} real world production",
                f"{tool} vs {alternative} site:github.com",
            ]
            fallback_results = search_multi_fn(fallback_queries, force_refresh=True)
            fallback_filtered = filter_search_results_fn(
                results_by_query=fallback_results,
                tool=tool,
                alternative=alternative,
            )
            fallback_context = build_context_fn(fallback_filtered, tool=tool)
            if fallback_context.strip():
                context = fallback_context
                logger.info("✓ Fallback search recovered %s chars for '%s'", len(context), tool)
            else:
                logger.warning(f"Fallback search also returned no content for '{tool}'")

    save_context_debug_fn(tool=tool, context=context)

    lessons = get_lessons_for_prompt_fn()
    if lessons:
        logger.debug("Using learned lessons from memory")

    questoes_block = ""
    if len(questoes) > 0:
        lista = "\n".join(f"- {question}" for question in questoes)
        questoes_block = f"\nBusque dados específicos para responder:\n{lista}\n"
        logger.debug(f"Added {len(questoes)} custom questions to prompt")

    prompt = prompts_get_fn(
        "researcher",
        "main",
        tool=tool,
        foco=foco,
        questoes_block=questoes_block,
        lessons=lessons,
        context=context,
    )
    if not prompt:
        raise RuntimeError("Prompt template missing: prompts/researcher.yaml#main")
    logger.debug(f"Calling LLM researcher (timeout: {timeout}s, temp: {temp})")

    resp = llm_generate_fn(
        role="researcher",
        model=model,
        prompt=prompt,
        temperature=temp,
        num_ctx=ctx_len,
        timeout=timeout,
    )
    logger.debug(f"LLM response received: {len(resp.response)} chars")

    memory.log_event("research_done", {
        "tool": tool,
        "foco": foco,
        "queries": len(queries),
        "scrape_stats": last_scrape_stats,
    })
    run_data = get_active_chain_run_fn() or {}
    synthesis_payload = {
        "tool": tool,
        "foco": foco,
        "context_chars": len(context),
        "report_chars": len(resp.response),
        "scrape_stats": last_scrape_stats,
        "context_debug_file": f"output/debug_context_{(tool or 'unknown').lower().replace(' ', '_')}.md",
        "legacy_research_file": f"output/debug_research_{(tool or 'unknown').lower().replace(' ', '_')}.md",
        "chain_run_id": run_data.get("run_id", ""),
    }
    if run_data:
        run_data["phases"]["synthesis_eval"] = synthesis_payload
        write_chain_phase_fn("synthesis_eval", synthesis_payload)
    finalize_chain_run_fn()
    return resp.response
