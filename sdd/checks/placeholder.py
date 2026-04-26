import re

PLACEHOLDER_PATTERNS = [
    (r"\[TODO", None),
    (r"TODO:", None),
    (r"SEU_TOKEN", None),
    (r"seu-repo", re.IGNORECASE),
    (r"SEU-TOKEN", None),
    (r"<seu-", re.IGNORECASE),
    (r"seu_repo", re.IGNORECASE),
    (r"\[INSIRA", re.IGNORECASE),
    (r"\[ADICIONE", re.IGNORECASE),
]

COMPILED_PATTERNS = [
    re.compile(pattern, flags if flags is not None else 0)
    for pattern, flags in PLACEHOLDER_PATTERNS
]


def check_placeholders(article: str) -> list[str]:
    """Return problems if article contains placeholder/template text."""
    problems = []
    for compiled in COMPILED_PATTERNS:
        match = compiled.search(article)
        if match:
            problems.append(f"Placeholder encontrado: '{match.group()}'")
    return problems
