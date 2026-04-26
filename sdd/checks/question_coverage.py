def check_question_coverage(article: str, questions: list[str]) -> list[str]:
    """Return problems if questions from the spec are not addressed in the article."""
    article_lower = article.lower()
    problems = []
    for question in questions:
        key_words = [word for word in question.split() if len(word) > 4]
        if not key_words:
            continue
        answered = any(word.lower() in article_lower for word in key_words)
        if not answered:
            problems.append(f"Pergunta não respondida no artigo: '{question}'")
    return problems
