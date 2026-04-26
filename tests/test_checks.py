"""Unit tests for sdd/checks/ deterministic check functions."""
from sdd.checks.groundedness import check_groundedness
from sdd.checks.placeholder import check_placeholders
from sdd.checks.question_coverage import check_question_coverage
from sdd.checks.structural import check_structural
from sdd.checks import run_deterministic_checks, CHECK_ORDER


# ---------------------------------------------------------------------------
# check_groundedness
# ---------------------------------------------------------------------------

class TestCheckGroundedness:
    def test_url_in_code_block_is_ignored(self):
        article = "Veja o exemplo:\n```bash\ngit clone https://github.com/seu-repo\n```\n"
        problems = check_groundedness(article, retained_urls=[])
        assert problems == []

    def test_url_outside_code_block_not_in_retained_urls_returns_problem(self):
        article = "Confira em https://example.com/artigo para mais detalhes."
        problems = check_groundedness(article, retained_urls=["https://other.com"])
        assert len(problems) == 1
        assert "example.com/artigo" in problems[0]

    def test_url_outside_code_block_in_retained_urls_returns_no_problem(self):
        article = "Confira em https://example.com/artigo para mais detalhes."
        problems = check_groundedness(article, ["https://example.com/artigo"])
        assert problems == []

    def test_empty_article_no_problems(self):
        assert check_groundedness("", []) == []

    def test_multiple_outside_urls_reported(self):
        article = "Ver https://a.com e https://b.com e https://c.com e https://d.com"
        problems = check_groundedness(article, [])
        assert len(problems) == 1
        assert "4 encontradas" in problems[0]


# ---------------------------------------------------------------------------
# check_placeholders
# ---------------------------------------------------------------------------

class TestCheckPlaceholders:
    def test_todo_bracket_returns_problem(self):
        article = "Faça [TODO completar esta seção]"
        problems = check_placeholders(article)
        assert any("TODO" in p for p in problems)

    def test_todo_colon_returns_problem(self):
        article = "TODO: implementar depois"
        problems = check_placeholders(article)
        assert any("TODO" in p for p in problems)

    def test_seu_token_returns_problem(self):
        article = "Use SEU_TOKEN para autenticar."
        problems = check_placeholders(article)
        assert any("SEU_TOKEN" in p for p in problems)

    def test_seu_repo_in_code_block_still_returns_problem(self):
        # Placeholders ARE checked even inside code blocks
        article = "```bash\ngit clone https://github.com/seu-repo\n```"
        problems = check_placeholders(article)
        assert any("seu-repo" in p.lower() for p in problems)

    def test_insira_bracket_returns_problem(self):
        article = "[INSIRA O CONTEÚDO AQUI]"
        problems = check_placeholders(article)
        assert any("INSIRA" in p.upper() for p in problems)

    def test_adicione_bracket_returns_problem(self):
        article = "[Adicione exemplos aqui]"
        problems = check_placeholders(article)
        assert any("ADICIONE" in p.upper() for p in problems)

    def test_clean_article_no_problems(self):
        article = "Este é um artigo limpo sem placeholders. Instale com apt install docker."
        problems = check_placeholders(article)
        assert problems == []


# ---------------------------------------------------------------------------
# check_question_coverage
# ---------------------------------------------------------------------------

class TestCheckQuestionCoverage:
    def test_missing_key_terms_returns_problem(self):
        article = "Docker é uma ferramenta de containerização."
        questions = ["Como instalar Kubernetes no Linux?"]
        problems = check_question_coverage(article, questions)
        assert len(problems) == 1
        assert "Kubernetes" in problems[0]

    def test_article_contains_key_terms_no_problem(self):
        article = "Para instalar Kubernetes no Linux, use kubeadm."
        questions = ["Como instalar Kubernetes no Linux?"]
        problems = check_question_coverage(article, questions)
        assert problems == []

    def test_empty_questions_no_problems(self):
        assert check_question_coverage("qualquer texto", []) == []

    def test_short_word_only_question_skipped(self):
        # All words <= 4 chars — no keywords to check
        problems = check_question_coverage("algo", ["Veja ok?"])
        assert problems == []


# ---------------------------------------------------------------------------
# check_structural
# ---------------------------------------------------------------------------

def make_valid_article():
    return """\
# TL;DR
Resumo rápido.

## O que é
Explicação.

## Requisitos
Lista.

## Instalacao
Passos.

## Configuracao
Config.

## Exemplo Pratico
Código aqui.

## Armadilhas
- erro comum 1
- armadilha 2
- problema de configuração

## Otimizacoes
- otimiza A
- dica B
- otimiza C
- melhoria D

## Conclusao
Fim.

## Referencias
- https://example.com/ref1
- https://example.com/ref2
- https://example.com/ref3
"""


class TestCheckStructural:
    def test_missing_required_section_returns_problem(self):
        config = {
            "required_sections": ["conclusao"],
            "min_refs": 0,
            "min_errors": 0,
            "min_tips": 0,
        }
        article = "# Introdução\nSem conclusão aqui."
        problems = check_structural(article, config)
        assert any("conclusao" in p for p in problems)

    def test_fewer_refs_than_min_returns_problem(self):
        config = {
            "required_sections": [],
            "min_refs": 3,
            "min_errors": 0,
            "min_tips": 0,
        }
        article = "Texto sem referências no formato correto."
        problems = check_structural(article, config)
        assert any("Referências" in p for p in problems)

    def test_valid_article_no_problems(self):
        config = {
            "required_sections": ["conclusao"],
            "min_refs": 3,
            "min_errors": 2,
            "min_tips": 3,
        }
        article = make_valid_article()
        problems = check_structural(article, config)
        assert problems == []


# ---------------------------------------------------------------------------
# run_deterministic_checks (integration)
# ---------------------------------------------------------------------------

class TestRunDeterministicChecks:
    def test_check_order_constant(self):
        assert CHECK_ORDER == ["placeholder", "groundedness", "question_coverage", "structural"]

    def test_returns_combined_problems(self):
        article = "TODO: completar"
        problems = run_deterministic_checks(
            article=article,
            retained_urls=[],
            questions=[],
            config={"required_sections": [], "min_refs": 0, "min_errors": 0, "min_tips": 0},
        )
        assert any("TODO" in p for p in problems)

    def test_clean_inputs_no_problems(self):
        article = make_valid_article()
        problems = run_deterministic_checks(
            article=article,
            retained_urls=["https://example.com/ref1", "https://example.com/ref2", "https://example.com/ref3"],
            questions=["Como configurar Otimizacoes no sistema?"],
            config={"required_sections": [], "min_refs": 3, "min_errors": 2, "min_tips": 3},
        )
        assert problems == []
