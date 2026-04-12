import yaml
import logging
from pathlib import Path

from llm import LLMClient

logger = logging.getLogger(__name__)


class WriterSkill:

    def __init__(self, memory, spec_path="spec/article_spec.yaml"):
        self.memory = memory
        self.spec   = yaml.safe_load(Path(spec_path).read_text())
        self.llm    = LLMClient(spec_path)
        self.model  = self.llm.model_for_role("writer")
        llm_conf = self.spec.get("llm", {})
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        context_length = llm_conf.get("context_length", self.spec.get("ollama", {}).get("context_length", {}))
        self.temp   = temperatures["writer"]
        self.timeout = timeouts.get("writer", timeouts.get("default", 300))
        self.ctx_len = context_length.get("writer", context_length.get("default", 8192))

    def run(self, research, analysis, ferramentas, contexto,
            foco="comparação geral", questoes=None,
            correction_instructions="", research_quality="ok"):

        questoes = questoes or []
        logger.debug(f"Starting writer: ferramentas={ferramentas}, foco={foco}, quality={research_quality}")
        
        lessons = self.memory.get_lessons_for_prompt()
        if lessons:
            logger.debug(f"Using memory lessons for writer")

        correction_block = ""
        if correction_instructions:
            logger.debug(f"Applying correction instructions: {len(correction_instructions)} chars")
            correction_block = f"""
############################################################
# CORREÇÕES OBRIGATÓRIAS — O ARTIGO FOI REPROVADO
# Se estas correções não forem aplicadas, será reprovado de novo.
############################################################

{correction_instructions}

ATENÇÃO: O artigo anterior foi REJEITADO por conter os problemas acima.
- Releia CADA problema listado
- Encontre o trecho exato no artigo que causa o problema
- Reescreva APENAS esse trecho
- NÃO use as palavras/frases proibidas em nenhum lugar do artigo
############################################################
"""

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {q}" for q in questoes)
            questoes_block = f"""
O artigo DEVE responder explicitamente estas perguntas:
{lista}
Cada resposta deve aparecer claramente no texto.
"""
            logger.debug(f"Added {len(questoes)} questions to writer prompt")

        lessons_block = f"\n{lessons}\n" if lessons else ""

        research_warning = ""
        if research_quality == "weak":
            logger.warning(f"Research quality is WEAK - warning writer to not invent data")
            research_warning = """
############################################################
# AVISO: OS DADOS DE PESQUISA SÃO INSUFICIENTES
# A pesquisa retornou poucos dados concretos.
# Você DEVE:
# - OMITIR seções inteiras se não houver dados para preenchê-las
# - NUNCA inventar comandos, URLs, nomes de modelos ou números
# - Preferir escrever "Não foram encontrados dados concretos" do que inventar
# - Manter o artigo CURTO se os dados forem poucos
# Um artigo curto e correto é melhor que um longo e inventado.
############################################################
"""

        prompt = f"""Você é um tech writer experiente. Escreva um artigo técnico completo.

FERRAMENTAS: {ferramentas}
CONTEXTO: {contexto}
FOCO: {foco}
{questoes_block}
{correction_block}
{lessons_block}
{research_warning}

DADOS DE PESQUISA:
{research}

ANÁLISE TÉCNICA:
{analysis}

REGRAS INVIOLÁVEIS:
1. NUNCA use placeholders: [Descreva...], [TODO], [X], DADO AUSENTE,
   NÃO ENCONTRADO, N/A — a presença de QUALQUER UM desses reprova o artigo
2. NUNCA use frases genéricas como solução: "conforme necessário",
   "consulte a documentação", "verifique a configuração" — isso reprova
3. Se não tem um dado concreto, há 3 opções:
   a) Omita a linha/seção silenciosamente
   b) Explique por que o dado não existe (ex: "não publica requisitos oficiais")
   c) Dê uma estimativa baseada em evidência ("baseado em testes da comunidade, ~500MB")
4. Use APENAS comandos que aparecem nos dados acima — nunca invente
5. URLs em referências devem ser APENAS das URLs consultadas na pesquisa
6. Toda tabela deve ter TODAS as células preenchidas — se não tem dado, remova a linha
7. Toda solução em Armadilhas deve ter comando real com no mínimo 20 caracteres

TEMPLATE (inclua TODAS as seções):

# [Título descritivo sobre {ferramentas}]

> **TL;DR:** [Uma frase objetiva, máximo 20 palavras]

## O que é e por que usar
[2 parágrafos com foco em: {foco}]

## Requisitos
[Se há dados: tabela. Se não há requisitos oficiais: explique em 1-2 frases por quê.]

## Instalação
### Método 1: [nome]
```bash
[comandos reais]
```
### Método 2: [nome]
```bash
[comandos reais]
```

## Configuração
[arquivo de configuração com caminho real e conteúdo]

## Exemplo Prático
### Cenário: [descrição realista para {contexto}]
[passos numerados com comandos reais + resultado esperado]

## Armadilhas Comuns
### ⚠ [Nome do erro real]
**Sintoma:** [descrição concreta]
**Causa:** [explicação técnica]
**Solução:**
```bash
[comando real com no mínimo 20 caracteres]
```

### ⚠ [Nome do erro real]
**Sintoma:** ...  **Causa:** ...  **Solução:** ...

## Dicas de Otimização
[mínimo 3 dicas com comandos reais quando disponíveis]

## Conclusão
[trade-offs para {contexto} considerando {foco}]

## Referências
[mínimo 3 URLs reais da pesquisa, formato: - URL]
"""
        resp = self.llm.generate(
            role="writer",
            model=self.model,
            prompt=prompt,
            temperature=self.temp,
            num_ctx=self.ctx_len,
            timeout=self.timeout,
        )
        self.memory.log_event("article_written", {"ferramentas": ferramentas})
        return resp.response
