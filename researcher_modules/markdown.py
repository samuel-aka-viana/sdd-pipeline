import re
from urllib.parse import urljoin


def extract_section_structure(markdown_content: str) -> dict:
    """Analyze markdown headers to detect rich sections for prioritization."""
    sections = {
        "tips": [],
        "errors": [],
        "commands": [],
        "benchmarks": [],
        "warnings": [],
        "has_table": False,
    }

    if not markdown_content:
        return sections

    headers = re.findall(r"^#+\s+(.+)$", markdown_content, re.MULTILINE)

    for header in headers:
        header_lower = header.lower()
        if any(word in header_lower for word in ["dica", "tip", "otimiza", "optimization"]):
            sections["tips"].append(header)
        elif any(word in header_lower for word in ["erro", "error", "problema", "pitfall"]):
            sections["errors"].append(header)
        elif any(word in header_lower for word in ["command", "instala", "install", "bash"]):
            sections["commands"].append(header)
        elif any(word in header_lower for word in ["benchmark", "performance", "throughput", "latency"]):
            sections["benchmarks"].append(header)
        elif any(word in header_lower for word in ["warning", "⚠", "cuidado", "aviso"]):
            sections["warnings"].append(header)

    sections["has_table"] = bool(re.search(r"\|.*\|", markdown_content))
    return sections


def extract_best_markdown(markdown_obj) -> str:
    fit_markdown = getattr(markdown_obj, "fit_markdown", None)
    if fit_markdown and fit_markdown.strip() and len(fit_markdown.strip()) >= 500:
        return fit_markdown
    if hasattr(markdown_obj, "raw_markdown"):
        raw_markdown = markdown_obj.raw_markdown or ""
        if raw_markdown.strip():
            return raw_markdown
        return raw_markdown
    if isinstance(markdown_obj, str):
        return markdown_obj
    return ""


def is_low_quality_text(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return True
    sample = cleaned.lower()[:320]
    noise_markers = (
        "skip to main content",
        "report a website issue",
        "start a new chat",
        "what can i help you with",
        "i'm gordon, your ai assistant",
        "open in app",
        "navigation menu",
        "cookie",
    )
    if any(marker in sample for marker in noise_markers):
        return True
    return len(cleaned) < 500


def extract_redirect_target(result, source_url: str) -> str:
    redirected_url = getattr(result, "redirected_url", "") or ""
    if redirected_url and redirected_url != source_url:
        return redirected_url
    headers = getattr(result, "response_headers", {}) or {}
    location = headers.get("location") or headers.get("Location")
    if location:
        return urljoin(source_url, str(location))
    return ""
