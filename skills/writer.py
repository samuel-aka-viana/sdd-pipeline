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
        writer_input = llm_conf.get("writer_input", {})
        self.temp   = temperatures["writer"]
        self.timeout = timeouts.get("writer", timeouts.get("default", 300))
        self.ctx_len = context_length.get("writer", context_length.get("default", 8192))
        self.max_research_chars = writer_input.get("max_research_chars", 12000)
        self.max_analysis_chars = writer_input.get("max_analysis_chars", 6000)
        self.max_correction_chars = writer_input.get("max_correction_chars", 2500)

    def run(self, research, analysis, ferramentas, contexto,
            foco="comparação geral", questoes=None,
            correction_instructions="", research_quality="ok"):

        questoes = questoes or []
        logger.debug(f"Starting writer: ferramentas={ferramentas}, foco={foco}, quality={research_quality}")
        
        lessons = self.memory.get_lessons_for_prompt()
        if lessons:
            logger.debug(f"Using memory lessons for writer")

        compact_research = self.compact_text_block(
            text=research,
            max_chars=self.max_research_chars,
            label="DADOS DE PESQUISA",
        )
        compact_analysis = self.compact_text_block(
            text=analysis,
            max_chars=self.max_analysis_chars,
            label="ANÁLISE TÉCNICA",
        )

        correction_block = ""
        if correction_instructions:
            logger.debug(f"Applying correction instructions: {len(correction_instructions)} chars")
            compact_corrections = self.compact_text_block(
                text=correction_instructions,
                max_chars=self.max_correction_chars,
                label="CORREÇÕES",
            )
            correction_block = f"""
############################################################
# CORREÇÕES OBRIGATÓRIAS — O ARTIGO FOI REPROVADO
# Se estas correções não forem aplicadas, será reprovado de novo.
############################################################

{compact_corrections}

ATENÇÃO: O artigo anterior foi REJEITADO por conter os problemas acima.
- Releia CADA problema listado
- Encontre o trecho exato no artigo que causa o problema
- Reescreva APENAS esse trecho
- NÃO use as palavras/frases proibidas em nenhum lugar do artigo
############################################################
"""

        questoes_block = ""
        question_answer_template_block = ""
        if questoes:
            lista = "\n".join(f"- {question}" for question in questoes)
            questoes_block = f"""
O artigo DEVE responder explicitamente estas perguntas:
{lista}
Cada resposta deve aparecer claramente no texto.
"""
            question_answer_template_block = self.build_question_answer_template_block(questoes)
            logger.debug(f"Added {len(questoes)} questions to writer prompt")
        objective_requirements_block = self.build_objective_requirements_block(questoes)

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
{compact_research}

ANÁLISE TÉCNICA:
{compact_analysis}

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
8. Sempre que a pergunta pedir benchmark/latência/throughput, responda com métrica numérica ou
   escreva explicitamente "Sem dados mensuráveis nas fontes consultadas" (sem inventar números)
{objective_requirements_block}

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
{question_answer_template_block}
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

    def build_question_answer_template_block(self, questoes: list[str]) -> str:
        if not questoes:
            return ""
        formatted_questions = "\n".join(
            f'- Pergunta: "{question}"\n  Resposta objetiva: [resposta]\n  Evidência/URL: [URL da seção Referências ou N/D]'
            for question in questoes
        )
        return (
            "\n\n## Respostas às Perguntas do Contexto\n"
            "Responda cada pergunta abaixo de forma explícita. "
            "Se faltarem números, escreva exatamente: "
            "\"Sem dados mensuráveis nas fontes consultadas\" "
            "e use Evidência/URL: N/D.\n\n"
            f"{formatted_questions}\n"
        )

    def build_objective_requirements_block(self, questoes: list[str]) -> str:
        normalized_questions = " ".join(questoes or []).lower()
        requirements = []

        if any(token in normalized_questions for token in ("p95", "latência", "latencia", "throughput")):
            requirements.append(
                "- Inclua uma mini tabela comparando p95/throughput de DuckDB vs Polars, "
                "ou declare ausência de dados mensuráveis com fonte."
            )

        if any(token in normalized_questions for token in ("sql-first", "sql first", "dataframe-first", "dataframe first")):
            requirements.append(
                "- Descreva ganhos e perdas de SQL-first vs DataFrame-first com critérios objetivos "
                "(complexidade, manutenção, performance)."
            )

        if any(token in normalized_questions for token in ("integração", "integracao", "python", "compatibilidade")):
            requirements.append(
                "- Mostre esforço de integração Python com exemplos mínimos de libs/APIs e riscos de manutenção."
            )

        if any(token in normalized_questions for token in ("ambos", "pipeline", "arquitetura combinada")):
            requirements.append(
                "- Inclua um cenário claro de arquitetura combinada (quando usar ambos no mesmo pipeline)."
            )

        if not requirements:
            return ""

        joined_requirements = "\n".join(requirements)
        return f"\nREQUISITOS OBJETIVOS DE COBERTURA:\n{joined_requirements}\n"

    def compact_text_block(self, text: str, max_chars: int, label: str) -> str:
        content = (text or "").strip()
        if len(content) <= max_chars:
            return content

        head_size = int(max_chars * 0.7)
        tail_size = max_chars - head_size
        compacted_content = (
            f"{content[:head_size]}\n\n"
            f"[... {label} truncado para caber no contexto ...]\n\n"
            f"{content[-tail_size:]}"
        )
        logger.warning(
            f"Writer input truncated for {label}: {len(content)} -> {len(compacted_content)} chars"
        )
        return compacted_content
