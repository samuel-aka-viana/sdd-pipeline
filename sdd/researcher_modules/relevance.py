import re
from urllib.parse import urlparse

from sdd.researcher_modules.constants import (
    GENERIC_KEYWORD_TERMS,
    HIGH_TRUST_DOMAIN_HINTS,
    LOW_SIGNAL_DOMAINS,
    LOW_SIGNAL_PATH_MARKERS,
    MEDIUM_TRUST_DOMAINS,
    NON_TEXT_EXTENSIONS,
    NON_TEXT_PATH_MARKERS,
    QNA_DOMAINS,
    TECH_EVIDENCE_TERMS,
    TOOL_IDENTITY_STOPWORDS,
    TRUSTED_TECH_DOMAINS,
)


def domain_fail_rate(domain_scrape_stats: dict, host: str) -> float:
    stats = domain_scrape_stats.get(host, {})
    attempts = int(stats.get("attempts", 0))
    if attempts <= 0:
        return 0.0
    fail = int(stats.get("fail", 0))
    return fail / max(attempts, 1)


def is_high_trust_host(host: str) -> bool:
    if any(
        host == trusted_domain or host.endswith(f".{trusted_domain}")
        for trusted_domain in TRUSTED_TECH_DOMAINS
    ):
        return True
    if any(host.startswith(prefix) for prefix in HIGH_TRUST_DOMAIN_HINTS):
        return True
    return False


def is_medium_trust_host(host: str) -> bool:
    return any(
        host == medium_domain or host.endswith(f".{medium_domain}")
        for medium_domain in MEDIUM_TRUST_DOMAINS
    )


def is_qna_host(host: str) -> bool:
    return any(host == qna_domain or host.endswith(f".{qna_domain}") for qna_domain in QNA_DOMAINS)


def has_tool_identity_match(combined_text: str, tool_identity_terms: set[str]) -> bool:
    if not tool_identity_terms:
        return False
    return any(tool_term in combined_text for tool_term in tool_identity_terms)


def has_required_tool_anchor(combined_text: str, tool_identity_terms: set[str]) -> bool:
    requires_dbt_anchor = "dbt" in tool_identity_terms or "sqlmesh" in tool_identity_terms
    if not requires_dbt_anchor:
        return True
    required_anchors = ("dbt", "dbt-core", "sqlmesh")
    return any(required_anchor in combined_text for required_anchor in required_anchors)


def is_low_signal_host(host: str) -> bool:
    return any(
        host == low_signal_domain or host.endswith(f".{low_signal_domain}")
        for low_signal_domain in LOW_SIGNAL_DOMAINS
    )


def should_skip_url(url: str, skip_domains: set[str], domain_scrape_stats: dict) -> bool:
    if not url or not url.startswith("http"):
        return True

    parsed_url = urlparse(url.lower())
    host = parsed_url.netloc
    path = parsed_url.path or ""
    query = parsed_url.query or ""

    if any(
        host == blocked_domain or host.endswith(f".{blocked_domain}")
        for blocked_domain in skip_domains
    ):
        return True

    if any(path.endswith(extension) for extension in NON_TEXT_EXTENSIONS):
        return True

    if any(marker in path for marker in NON_TEXT_PATH_MARKERS):
        return True

    if is_low_signal_host(host):
        return True

    domain_stats = domain_scrape_stats.get(host, {})
    attempts = int(domain_stats.get("attempts", 0))
    fail_rate = domain_fail_rate(domain_scrape_stats, host)
    if attempts >= 8 and fail_rate >= 0.9:
        return True

    if any(marker in path for marker in LOW_SIGNAL_PATH_MARKERS):
        return True

    if host.endswith("github.com") and path.startswith("/topics/"):
        return True
    if host.endswith("stackoverflow.com") and "/questions/tagged/" in path:
        return True
    if host.endswith("stackoverflow.com") and path.startswith("/tags/"):
        return True
    if "trk=" in query:
        return True

    return False


def build_relevance_keywords(tool: str, alternative: str) -> set[str]:
    raw_terms = [tool or "", alternative or ""]
    split_terms = []
    for term in raw_terms:
        split_terms.extend(re.split(r"[^a-zA-Z0-9]+", term.lower()))
    return {
        term
        for term in split_terms
        if len(term) >= 3 and term not in GENERIC_KEYWORD_TERMS
    }


def build_tool_identity_terms(tool: str, alternative: str) -> set[str]:
    raw_terms = [(tool or "").lower().strip(), (alternative or "").lower().strip()]
    tool_terms: set[str] = set()
    for raw_term in raw_terms:
        if raw_term:
            tool_terms.add(raw_term)
        split_terms = re.split(r"[^a-zA-Z0-9]+", raw_term)
        tool_terms.update(
            term
            for term in split_terms
            if len(term) >= 3
            and term not in GENERIC_KEYWORD_TERMS
            and term not in TOOL_IDENTITY_STOPWORDS
        )
    return {term for term in tool_terms if term}


def is_result_relevant(
    result_item: dict,
    relevance_keywords: set[str],
    tool_identity_terms: set[str],
) -> bool:
    url = (result_item.get("url", "") or "").lower()
    parsed_url = urlparse(url)
    host = parsed_url.netloc
    title = (result_item.get("title", "") or "").lower()
    snippet = (result_item.get("snippet", "") or "").lower()
    combined_text = f"{url} {title} {snippet}"
    if not has_required_tool_anchor(combined_text, tool_identity_terms):
        return False

    if is_qna_host(host):
        return has_tool_identity_match(combined_text, tool_identity_terms)

    if any(
        host == trusted_domain or host.endswith(f".{trusted_domain}")
        for trusted_domain in TRUSTED_TECH_DOMAINS
    ):
        return has_tool_identity_match(combined_text, tool_identity_terms)

    if not relevance_keywords:
        return has_tool_identity_match(combined_text, tool_identity_terms)

    return any(keyword in combined_text for keyword in relevance_keywords)


def compute_source_score(
    result_item: dict,
    relevance_keywords: set[str],
    tool_identity_terms: set[str],
    domain_scrape_stats: dict,
) -> int:
    url = (result_item.get("url", "") or "").lower()
    title = (result_item.get("title", "") or "").lower()
    snippet = (result_item.get("snippet", "") or "").lower()
    combined_text = f"{url} {title} {snippet}"
    parsed_url = urlparse(url)
    host = parsed_url.netloc

    source_score = 0

    if is_high_trust_host(host):
        source_score += 5
    elif is_medium_trust_host(host):
        source_score += 2
    elif is_qna_host(host):
        source_score += 1

    keyword_matches = sum(1 for keyword in relevance_keywords if keyword in combined_text)
    source_score += min(3, keyword_matches)

    if has_tool_identity_match(combined_text, tool_identity_terms):
        source_score += 3

    evidence_matches = sum(1 for term in TECH_EVIDENCE_TERMS if term in combined_text)
    source_score += min(3, evidence_matches)

    if is_low_signal_host(host):
        source_score -= 4
    if "sponsored" in combined_text or "affiliate" in combined_text:
        source_score -= 2
    fail_rate = domain_fail_rate(domain_scrape_stats, host)
    if fail_rate >= 0.8:
        source_score -= 4
    elif fail_rate >= 0.6:
        source_score -= 2

    return source_score


def filter_search_results(
    results_by_query: dict[str, list[dict]],
    tool: str,
    alternative: str,
    skip_domains: set[str],
    domain_scrape_stats: dict,
    source_min_score_keep: int,
    source_max_results_per_query: int,
) -> dict[str, list[dict]]:
    relevance_keywords = build_relevance_keywords(tool, alternative)
    tool_identity_terms = build_tool_identity_terms(tool, alternative)
    filtered_results_by_query: dict[str, list[dict]] = {}
    for query, results in results_by_query.items():
        scored_results = []
        for result_item in results:
            url = result_item.get("url", "")
            if should_skip_url(url, skip_domains=skip_domains, domain_scrape_stats=domain_scrape_stats):
                continue
            if not is_result_relevant(
                result_item=result_item,
                relevance_keywords=relevance_keywords,
                tool_identity_terms=tool_identity_terms,
            ):
                continue
            source_score = compute_source_score(
                result_item=result_item,
                relevance_keywords=relevance_keywords,
                tool_identity_terms=tool_identity_terms,
                domain_scrape_stats=domain_scrape_stats,
            )
            if source_score < source_min_score_keep:
                continue
            scored_results.append((source_score, result_item))

        scored_results.sort(key=lambda score_and_result: score_and_result[0], reverse=True)
        filtered_results_by_query[query] = [
            result_item
            for source_score, result_item in scored_results[:source_max_results_per_query]
        ]
    return filtered_results_by_query
