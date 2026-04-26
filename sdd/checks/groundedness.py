from sdd.constraints import CODE_BLOCK_PATTERN, URL_PATTERN


def check_groundedness(article: str, retained_urls: list[str]) -> list[str]:
    """Return problems if article cites URLs not in retained_urls."""
    allowed = set(retained_urls)
    text_without_code = CODE_BLOCK_PATTERN.sub("", article)
    found_urls = [url.rstrip(".,;:!?") for url in URL_PATTERN.findall(text_without_code)]
    outside = [url for url in found_urls if url not in allowed]
    if not outside:
        return []
    sample = ", ".join(outside[:3])
    return [f"URLs fora do evidence pack ({len(outside)} encontradas): {sample}"]
