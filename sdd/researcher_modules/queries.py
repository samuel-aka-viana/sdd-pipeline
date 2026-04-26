import re
from langchain_core.prompts import PromptTemplate

from sdd.constraints import (
    DEFAULT_QUERIES,
    FOCUS_QUERIES,
    GENERIC_KEYWORD_TERMS,
    INTEGRATION_INTENT_TERMS,
    PERFORMANCE_INTENT_TERMS,
    QUESTION_STOPWORDS,
    SECURITY_INTENT_TERMS,
)


def has_intent_term(text: str, terms: set[str]) -> bool:
    normalized_text = (text or "").lower()
    return any(intent_term in normalized_text for intent_term in terms)


def build_question_query(
    tool: str,
    alternative: str,
    question: str,
    focus: str,
) -> str:
    normalized_question = (question or "").lower().strip()
    question_terms = [
        term
        for term in re.split(r"[^a-zA-Z0-9]+", normalized_question)
        if len(term) >= 3 and term not in QUESTION_STOPWORDS and term not in GENERIC_KEYWORD_TERMS
    ]
    compact_terms = " ".join(question_terms[:8]).strip()
    scope_terms = [tool]
    if alternative and any(
        marker in normalized_question
        for marker in ("integr", "junto", "combinar", "ambos", "dois")
    ):
        scope_terms.append(alternative)

    base_query = " ".join(scope_terms + ([compact_terms] if compact_terms else [normalized_question]))

    if has_intent_term(normalized_question, PERFORMANCE_INTENT_TERMS):
        return f"{base_query} benchmark latency throughput"
    if has_intent_term(normalized_question, INTEGRATION_INTENT_TERMS):
        return f"{base_query} integration architecture example"
    if has_intent_term(normalized_question, SECURITY_INTENT_TERMS):
        return f"{base_query} security hardening best practices"
    focus_lower = (focus or "").lower()
    if (
        ("performance" in focus_lower or "throughput" in focus_lower)
        and has_intent_term(base_query, PERFORMANCE_INTENT_TERMS)
    ):
        return f"{base_query} benchmark latency throughput"
    if "integra" in focus_lower and has_intent_term(base_query, INTEGRATION_INTENT_TERMS):
        return f"{base_query} integration architecture example"
    return base_query.strip()


def build_queries(
    tool: str,
    alternative: str,
    foco: str,
    questoes,
    targeted_questions_only: bool = False,
) -> list[str]:
    if targeted_questions_only and questoes:
        return [
            build_question_query(
                tool=tool,
                alternative=alternative,
                question=question,
                focus=foco,
            )
            for question in questoes[:6]
        ]

    templates = FOCUS_QUERIES.get(foco, DEFAULT_QUERIES)
    alt = alternative or "alternatives"
    queries = [
        PromptTemplate.from_template(query_template).format(tool=tool, alternative=alt)
        for query_template in templates
    ]

    # Inject reversed-perspective queries so the primary tool captures articles
    # written from the alternative's point of view.
    if alternative and foco not in ("integração",):
        reversed_queries = [
            f"{alt} vs {tool} comparison",
            f"{alt} vs {tool} advantages disadvantages",
        ]
        existing = {q.lower() for q in queries}
        for reversed_query in reversed_queries:
            if reversed_query.lower() not in existing:
                queries.append(reversed_query)

    for question in (questoes or [])[:4]:
        queries.append(
            build_question_query(
                tool=tool,
                alternative=alternative,
                question=question,
                focus=foco,
            )
        )
    return queries
