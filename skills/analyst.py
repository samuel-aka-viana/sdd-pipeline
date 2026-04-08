import yaml
from pathlib import Path
from ollama import Client


class AnalystSkill:

    def __init__(self, memory, spec_path="spec/article_spec.yaml"):
        self.memory = memory
        self.spec   = yaml.safe_load(Path(spec_path).read_text())
        self.model  = self.spec["models"]["analyst"]
        self.temp   = self.spec["ollama"]["temperature"]["analyst"]
        timeouts = self.spec["ollama"].get("timeout", {})
        self.timeout = timeouts.get("analyst", timeouts.get("default", 300))
        self.llm    = Client(host=self.spec["ollama"]["base_url"], timeout=self.timeout)

    def run(self, research, ferramentas, contexto,
            foco="comparação geral", questoes=None):

        questoes = questoes or []
        tools = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
        is_single = len(tools) == 1
        is_integration = foco == "integração"

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {q}" for q in questoes)
            questoes_block = f"\nA análise deve fornecer dados para responder:\n{lista}\n"

        if is_single:
            table_block = self._single_tool_template(tools[0], foco)
        elif is_integration:
            table_block = self._integration_template(tools, foco)
        else:
            table_block = self._comparison_template(tools, foco)

        prompt = f"""Você é um analista técnico. Analise os dados de pesquisa abaixo.

FERRAMENTAS: {ferramentas}
CONTEXTO DE USO: {contexto}
FOCO DA ANÁLISE: {foco}
{questoes_block}

DADOS DA PESQUISA:
{research}

REGRAS CRÍTICAS:
- Produza APENAS o que os dados suportam
- Se um dado não existe na pesquisa, OMITA a linha ou célula da tabela
- NUNCA escreva "DADO AUSENTE", "NÃO ENCONTRADO", "N/A" ou qualquer placeholder
- Se uma tabela inteira não tem dados suficientes, substitua por um parágrafo
  explicando o que se sabe
- Células vazias são PROIBIDAS — remova a linha inteira se não tiver dado
- NUNCA use frases genéricas como "consulte a documentação" ou "conforme necessário"

{table_block}

## PRÓS
[3 itens com justificativa técnica baseada nos dados]

## CONTRAS
[3 itens com justificativa técnica baseada nos dados]

## OTIMIZAÇÕES
[3 dicas com comando real se disponível nos dados]

## RECOMENDAÇÃO
[1 parágrafo: recomendação para "{contexto}" considerando "{foco}"]
"""
        resp = self.llm.generate(
            model=self.model,
            prompt=prompt,
            options={"temperature": self.temp},
        )

        self.memory.log_event("analysis_done", {
            "ferramentas": ferramentas,
            "foco": foco,
            "mode": "single" if is_single else ("integration" if is_integration else "comparison"),
        })
        return resp.response

    def _comparison_template(self, tools, foco):
        t1, t2 = tools[0], tools[1] if len(tools) > 1 else "alternativa"
        return f"""## TABELA DE REQUISITOS
[Se há dados concretos de RAM/CPU, faça a tabela.
 Se não há requisitos oficiais, escreva um parágrafo curto explicando por quê.]

## TABELA COMPARATIVA
| Critério | {t1} | {t2} |
|----------|------|------|
[mínimo 5 critérios — APENAS os que têm dados para ambas as colunas]
[se só tem dado pra um lado, remova a linha]"""

    def _integration_template(self, tools, foco):
        return f"""## TABELA DE REQUISITOS
[requisitos combinados do stack completo]

## COMO SE ENCAIXAM
[explique o papel de cada ferramenta no pipeline — quem produz, quem consome]

## TABELA DE INTEGRAÇÃO
| Aspecto | {tools[0]} | {tools[1] if len(tools) > 1 else ''} | Como conectar |
|---------|------|------|---------------|
[mínimo 4 aspectos com dados concretos de como integrar]"""

    def _single_tool_template(self, tool, foco):
        return f"""## TABELA DE REQUISITOS
[Se há dados concretos de RAM/CPU, faça a tabela.
 Se não há requisitos oficiais, escreva um parágrafo curto explicando por quê.]

## ANÁLISE DETALHADA: {tool}
[análise focada em {foco} com dados concretos da pesquisa]
[organize por subtópicos relevantes ao foco]"""