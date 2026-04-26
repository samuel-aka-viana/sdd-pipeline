import re

REF_LINE_PATTERN = re.compile(r"^- https?://", re.MULTILINE)
ERRORS_KEYWORDS = ["erro", "armadilha", "problema", "pitfall", "falha"]
TIPS_KEYWORDS = ["otimiza", "dica", "tip", "melhoria", "sugestão", "recomend"]


def check_structural(article: str, config: dict) -> list[str]:
    """Return problems if article structure doesn't meet spec requirements."""
    problems = []
    article_lower = article.lower()

    required_sections = config.get("required_sections", [])
    for section in required_sections:
        section_normalized = section.replace("_", " ").lower()
        heading_pattern = re.compile(
            r"^#{1,2}\s+" + re.escape(section_normalized),
            re.MULTILINE | re.IGNORECASE,
        )
        if not heading_pattern.search(article):
            problems.append(f"Seção obrigatória ausente: '{section}'")

    min_refs = config.get("min_refs", 3)
    ref_count = len(REF_LINE_PATTERN.findall(article))
    if ref_count < min_refs:
        problems.append(
            f"Referências insuficientes: {ref_count} encontradas, mínimo {min_refs}"
        )

    min_errors = config.get("min_errors", 2)
    errors_count = sum(1 for kw in ERRORS_KEYWORDS if kw in article_lower)
    if errors_count < min_errors:
        problems.append(
            f"Cobertura de erros/armadilhas insuficiente: {errors_count} menções, mínimo {min_errors}"
        )

    min_tips = config.get("min_tips", 3)
    tips_count = sum(1 for kw in TIPS_KEYWORDS if kw in article_lower)
    if tips_count < min_tips:
        problems.append(
            f"Cobertura de dicas/otimizações insuficiente: {tips_count} menções, mínimo {min_tips}"
        )

    return problems
