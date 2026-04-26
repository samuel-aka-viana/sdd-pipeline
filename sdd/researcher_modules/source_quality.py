import json
from pathlib import Path
from urllib.parse import urlparse

from sdd.researcher_modules.constants import (
    HIGH_TRUST_DOMAIN_HINTS,
    MEDIUM_TRUST_DOMAINS,
    QNA_DOMAINS,
    TRUSTED_TECH_DOMAINS,
)


def load_domain_scrape_stats(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def infer_source_quality(url: str) -> str:
    """Infer source quality level for FTS metadata."""
    domain = urlparse(url).netloc.lower()

    if any(domain.endswith(trusted) for trusted in TRUSTED_TECH_DOMAINS):
        return "official"

    if any(hint in domain for hint in HIGH_TRUST_DOMAIN_HINTS):
        return "trusted"

    if domain in MEDIUM_TRUST_DOMAINS:
        return "medium"

    if domain in QNA_DOMAINS:
        return "medium"

    return "unknown"
