from typing import Optional


def expand_cached_queries(query: str, tool: Optional[str] = None) -> list[str]:
    base = str(query or "").strip()
    if not base and tool:
        base = f"{tool} documentação oficial"
    if not base:
        base = "documentação técnica oficial benchmark erros comuns"

    variants: list[str] = []
    if tool and tool.lower() not in base.lower():
        variants.append(f"{tool} {base}")
    variants.append(base)

    normalized = base.lower()
    if any(term in normalized for term in ("referência", "referencias", "referências", "fontes", "url", "urls")):
        variants.append(f"{base} documentação oficial github release notes")
    if any(term in normalized for term in ("erro", "problem", "troubleshoot", "falha")):
        variants.append(f"{base} troubleshooting issue solution example")
    if any(term in normalized for term in ("benchmark", "latên", "laten", "throughput", "performance", "métrica", "metrica")):
        variants.append(f"{base} benchmark numbers p95 throughput methodology")
    if any(term in normalized for term in ("instal", "config", "comando", "command")):
        variants.append(f"{base} install command config official docs")

    generic_evidence = [
        "documentação oficial",
        "guia de referência",
        "benchmark comparativo",
        "issue conhecido com solução",
    ]
    for suffix in generic_evidence:
        variants.append(f"{base} {suffix}")

    deduped: list[str] = []
    seen: set[str] = set()
    for item in variants:
        clean = " ".join(item.split()).strip()
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(clean)
    return deduped[:8]


def search_cached_content(
    query: str,
    tool: Optional[str],
    k: int,
    chroma,
    memory,
    logger,
    event_log=None,
) -> list[dict]:
    if chroma is None:
        logger.warning("Chroma not available for semantic search")
        return []

    expanded_queries = expand_cached_queries(query=query, tool=tool)
    similarity_thresholds = (0.30, 0.22, 0.16)
    per_query_k = max(4, min(10, k + 2))

    collected: list[dict] = []
    seen_signatures: set[tuple[str, str]] = set()

    for threshold in similarity_thresholds:
        for expanded_query in expanded_queries:
            if tool:
                partial = chroma.query_similar(
                    expanded_query,
                    tool=tool,
                    k=per_query_k,
                    distance_threshold=threshold,
                )
            else:
                partial = chroma.query_similar(
                    expanded_query,
                    tool=None,
                    k=per_query_k,
                    distance_threshold=threshold,
                )
            for result in partial:
                url = str(result.get("url", "")).strip()
                text_sig = str(result.get("text", "")).strip()[:180]
                if not text_sig:
                    continue
                signature = (url, text_sig)
                if signature in seen_signatures:
                    continue
                seen_signatures.add(signature)
                collected.append(result)
        if len(collected) >= max(k * 2, 8):
            break

    quality_weight = {"official": 3, "trusted": 2, "medium": 1, "unknown": 0}
    collected.sort(
        key=lambda item: (
            quality_weight.get(str(item.get("source_quality", "unknown")).lower(), 0),
            float(item.get("similarity", 0.0)),
        ),
        reverse=True,
    )

    results = collected[:max(k, 1)]
    urls = []
    seen_urls = set()
    for result in results:
        url = str(result.get("url", "")).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        urls.append(url)

    payload = {
        "tool": tool or "all",
        "query": query,
        "expanded_queries": len(expanded_queries),
        "results_count": len(results),
        "urls": urls,
        "query_type": "cached_search_expanded" if tool else "cross_tool_expanded",
    }
    memory.log_event("chroma_query", payload)
    if event_log is not None:
        event_log.log_event("chroma_query", payload)
    return results
