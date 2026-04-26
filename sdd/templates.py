"""Template builders for all skills — pure functions, no instance state."""


# --- Analyst templates ---

def comparison_template(tools: list[str]) -> str:
    p = tools[0]
    s = tools[1] if len(tools) > 1 else "alternativa"
    return f"""## TABELA DE REQUISITOS
[Se há dados concretos de RAM/CPU, faça a tabela.
 Se não há requisitos oficiais, escreva um parágrafo curto explicando por quê.]

## TABELA COMPARATIVA
| Critério | {p} | {s} |
|----------|------|------|
[mínimo 5 critérios — APENAS os que têm dados para ambas as colunas]
[se só tem dado pra um lado, remova a linha]"""


def integration_template(tools: list[str]) -> str:
    t1 = tools[0]
    t2 = tools[1] if len(tools) > 1 else ""
    return f"""## TABELA DE REQUISITOS
[requisitos combinados do stack completo]

## COMO SE ENCAIXAM
[explique o papel de cada ferramenta no pipeline — quem produz, quem consome]

## TABELA DE INTEGRAÇÃO
| Aspecto | {t1} | {t2} | Como conectar |
|---------|------|------|---------------|
[mínimo 4 aspectos com dados concretos de como integrar]"""


def single_tool_template(tool: str, foco: str) -> str:
    return f"""## TABELA DE REQUISITOS
[Se há dados concretos de RAM/CPU, faça a tabela.
 Se não há requisitos oficiais, escreva um parágrafo curto explicando por quê.]

## ANÁLISE DETALHADA: {tool}
[análise focada em {foco} com dados concretos da pesquisa]
[organize por subtópicos relevantes ao foco]"""


# --- Writer templates ---

def build_question_answer_template_block(questoes: list[str]) -> str:
    if not questoes:
        return ""
    formatted = "\n".join(
        f'- Pergunta: "{q}"\n  Resposta objetiva: [resposta]\n  Evidência/URL: [URL da seção Referências ou N/D]'
        for q in questoes
    )
    return (
        "\n\n## Respostas às Perguntas do Contexto\n"
        "Responda cada pergunta abaixo de forma explícita. "
        'Se faltarem números, escreva exatamente: "Sem dados mensuráveis nas fontes consultadas" '
        "e use Evidência/URL: N/D.\n\n"
        f"{formatted}\n"
    )


def build_objective_requirements_block(questoes: list[str], ferramentas: str = "") -> str:
    normalized = " ".join(questoes or []).lower()
    tools_label = ferramentas if ferramentas else "as ferramentas"
    requirements = []

    if any(t in normalized for t in ("p95", "latência", "latencia", "throughput")):
        requirements.append(
            f"- Inclua uma mini tabela comparando p95/throughput de {tools_label}, "
            "ou declare ausência de dados mensuráveis com fonte."
        )
    if any(t in normalized for t in ("sql-first", "sql first", "dataframe-first", "dataframe first")):
        requirements.append(
            "- Descreva ganhos e perdas de SQL-first vs DataFrame-first com critérios objetivos "
            "(complexidade, manutenção, performance)."
        )
    if any(t in normalized for t in ("integração", "integracao", "python", "compatibilidade")):
        requirements.append(
            "- Mostre esforço de integração Python com exemplos mínimos de libs/APIs e riscos de manutenção."
        )
    if any(t in normalized for t in ("ambos", "pipeline", "arquitetura combinada")):
        requirements.append(
            "- Inclua um cenário claro de arquitetura combinada (quando usar ambos no mesmo pipeline)."
        )

    if not requirements:
        return ""
    return "\nREQUISITOS OBJETIVOS DE COBERTURA:\n" + "\n".join(requirements) + "\n"
