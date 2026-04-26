from sdd.checks.placeholder import check_placeholders
from sdd.checks.groundedness import check_groundedness
from sdd.checks.question_coverage import check_question_coverage
from sdd.checks.structural import check_structural

CHECK_ORDER = [
    "placeholder",
    "groundedness",
    "question_coverage",
    "structural",
]


def run_deterministic_checks(
    article: str,
    retained_urls: list[str],
    questions: list[str],
    config: dict,
) -> list[str]:
    """Run all 4 deterministic checks in order; return combined problem list."""
    problems = []
    problems.extend(check_placeholders(article))
    problems.extend(check_groundedness(article, retained_urls))
    problems.extend(check_question_coverage(article, questions))
    problems.extend(check_structural(article, config))
    return problems
