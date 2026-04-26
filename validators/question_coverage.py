from __future__ import annotations

import re


def validate_question_coverage(pipeline, article: str, questoes: list[str]) -> dict:
    if not questoes:
        return {"approved": True, "layer": "question_coverage", "problems": [], "warnings": []}

    normalized_article = pipeline.normalize_text_for_match(article)
    missing_questions: list[str] = []
    missing_metric_evidence: list[str] = []

    for question in questoes:
        clean_question = (question or "").strip()
        if not clean_question:
            continue
        normalized_question = pipeline.normalize_text_for_match(clean_question)
        if normalized_question not in normalized_article:
            missing_questions.append(clean_question)
            continue
        if question_requires_metric_evidence(pipeline, clean_question) and not has_numeric_or_no_data_evidence(
            pipeline,
            article,
            clean_question,
        ):
            missing_metric_evidence.append(clean_question)

    problems = []
    if missing_questions:
        problems.append(
            "Perguntas do contexto sem resposta explícita: " + "; ".join(missing_questions)
        )
    if missing_metric_evidence:
        problems.append(
            "Perguntas de métricas mensuráveis sem número ou sem a frase "
            "'Sem dados mensuráveis nas fontes consultadas': "
            + "; ".join(missing_metric_evidence)
        )

    if not problems:
        return {"approved": True, "layer": "question_coverage", "problems": [], "warnings": []}

    correction_prompt = (
        "DADOS INSUFICIENTES PARA PERGUNTAS DO CONTEXTO.\n"
        "Corrija obrigatoriamente:\n"
        "- Inclua a seção 'Respostas às Perguntas do Contexto'.\n"
        "- Replique cada pergunta literal do input e responda de forma objetiva.\n"
        "- Para perguntas de p95/throughput/latência: inclua número mensurável OU a frase "
        "'Sem dados mensuráveis nas fontes consultadas'.\n"
        "- Não invente dados.\n"
    )
    return {
        "approved": False,
        "layer": "question_coverage",
        "problems": problems,
        "warnings": [],
        "correction_prompt": correction_prompt,
        "report": "\n".join(problems),
    }


def question_requires_metric_evidence(pipeline, question: str) -> bool:
    normalized_question = pipeline.normalize_text_for_match(question)
    metric_tokens = (
        "p95",
        "latencia",
        "throughput",
        "agregacoes",
        "agregacao",
        "benchmark",
    )
    return any(metric_token in normalized_question for metric_token in metric_tokens)


def has_numeric_or_no_data_evidence(pipeline, article: str, question: str) -> bool:
    normalized_article = pipeline.normalize_text_for_match(article)
    normalized_question = pipeline.normalize_text_for_match(question)
    idx = normalized_article.find(normalized_question)
    if idx == -1:
        return False
    window = normalized_article[idx: idx + 900]
    if "sem dados mensuraveis nas fontes consultadas" in window:
        return True
    return bool(re.search(r"\b\d+(?:[.,]\d+)?\s*(?:ms|s|seg|qps|rps|rows/s|linhas/s|%)?\b", window))
