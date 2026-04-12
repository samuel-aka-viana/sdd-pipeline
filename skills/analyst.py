import yaml
import logging
from pathlib import Path

from llm import LLMClient

logger = logging.getLogger(__name__)


class AnalystSkill:

    def __init__(self, memory, spec_path="spec/article_spec.yaml"):
        self.memory = memory
        self.spec   = yaml.safe_load(Path(spec_path).read_text())
        self.llm    = LLMClient(spec_path)
        self.model  = self.llm.model_for_role("analyst")
        llm_conf = self.spec.get("llm", {})
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        self.temp   = temperatures["analyst"]
        self.timeout = timeouts.get("analyst", timeouts.get("default", 300))

    def run(self, research, ferramentas, contexto,
            foco="comparação geral", questoes=None):

        questoes = questoes or []
        logger.debug(f"Starting analysis for: {ferramentas}, contexto: {contexto}, foco: {foco}")
        
        tools = [tool_name.strip() for tool_name in ferramentas.lower().replace(" e ", ",").split(",") if tool_name.strip()]
        is_single = len(tools) == 1
        is_integration = foco == "integração"
        logger.debug(f"Parsed tools: {tools}, is_single: {is_single}, is_integration: {is_integration}")

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {question}" for question in questoes)
            questoes_block = f"\nA análise deve fornecer dados para responder:\n{lista}\n"
            logger.debug(f"Added {len(questoes)} custom analysis questions")

        if is_single:
            table_block = self.single_tool_template(tools[0], foco)
        elif is_integration:
            table_block = self.integration_template(tools)
        else:
            table_block = self.comparison_template(tools)
        logger.debug(f"Selected template: {'single' if is_single else ('integration' if is_integration else 'comparison')}")

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
        logger.debug(f"Calling LLM analyst (timeout: {self.timeout}s, temp: {self.temp})")
        resp = self.llm.generate(
            role="analyst",
            model=self.model,
            prompt=prompt,
            temperature=self.temp,
            timeout=self.timeout,
        )
        logger.debug(f"LLM response received: {len(resp.response)} chars")

        self.memory.log_event("analysis_done", {
            "ferramentas": ferramentas,
            "foco": foco,
            "mode": "single" if is_single else ("integration" if is_integration else "comparison"),
        })
        return resp.response

    def comparison_template(self, tools):
        primary_tool_name = tools[0]
        secondary_tool_name = tools[1] if len(tools) > 1 else "alternativa"
        return f"""## TABELA DE REQUISITOS
[Se há dados concretos de RAM/CPU, faça a tabela.
 Se não há requisitos oficiais, escreva um parágrafo curto explicando por quê.]

## TABELA COMPARATIVA
| Critério | {primary_tool_name} | {secondary_tool_name} |
|----------|------|------|
[mínimo 5 critérios — APENAS os que têm dados para ambas as colunas]
[se só tem dado pra um lado, remova a linha]"""

    def integration_template(self, tools):
        return f"""## TABELA DE REQUISITOS
[requisitos combinados do stack completo]

## COMO SE ENCAIXAM
[explique o papel de cada ferramenta no pipeline — quem produz, quem consome]

## TABELA DE INTEGRAÇÃO
| Aspecto | {tools[0]} | {tools[1] if len(tools) > 1 else ''} | Como conectar |
|---------|------|------|---------------|
[mínimo 4 aspectos com dados concretos de como integrar]"""

    def single_tool_template(self, tool, foco):
        return f"""## TABELA DE REQUISITOS
[Se há dados concretos de RAM/CPU, faça a tabela.
 Se não há requisitos oficiais, escreva um parágrafo curto explicando por quê.]

## ANÁLISE DETALHADA: {tool}
[análise focada em {foco} com dados concretos da pesquisa]
[organize por subtópicos relevantes ao foco]"""
