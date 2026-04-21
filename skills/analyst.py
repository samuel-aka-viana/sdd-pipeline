import yaml
import logging
from pathlib import Path

from llm import LLMClient

try:
    from memory.research_chroma import ResearchChroma
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

logger = logging.getLogger(__name__)


class AnalystSkill:

    def __init__(self, memory, spec_path="spec/article_spec.yaml"):
        self.memory = memory
        self.spec   = yaml.safe_load(Path(spec_path).read_text())
        self.llm    = LLMClient(spec_path)
        self.model  = self.llm.model_for_role("analyst")
        self.chroma = ResearchChroma() if HAS_CHROMA else None
        llm_conf = self.spec.get("llm", {})
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        self.temp   = temperatures["analyst"]
        self.timeout = timeouts.get("analyst", timeouts.get("default", 300))

    def run(self, research, ferramentas, contexto,
            foco="comparação geral", questoes=None):

        questoes = questoes or []
        logger.debug(f"Starting analysis for: {ferramentas}, contexto: {contexto}, foco: {foco}")

        # NEW: If research is minimal (skip_search optimization), fetch context from Chroma
        if research and len(research.strip()) < 200:
            logger.info("Research is minimal — fetching context from Chroma cache")
            chroma_context = self._get_cached_research_context(ferramentas, foco)
            if chroma_context:
                research = f"{research}\n\n## CONTEXTO DO CACHE CHROMA\n{chroma_context}"
                self.memory.log_event("analyst_used_chroma_cache", {
                    "ferramentas": ferramentas,
                    "foco": foco,
                    "context_chars": len(chroma_context),
                })
                logger.info(f"Enhanced research with {len(chroma_context)} chars from Chroma")

        tools = [tool_name.strip() for tool_name in ferramentas.lower().replace(" e ", ",").split(",") if tool_name.strip()]
        is_single = len(tools) == 1
        is_integration = foco == "integração"
        logger.debug(f"Parsed tools: {tools}, is_single: {is_single}, is_integration: {is_integration}")

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {question}" for question in questoes)
            questoes_block = f"\nA análise deve fornecer dados para responder:\n{lista}\n"
            logger.debug(f"Added {len(questoes)} custom analysis questions")

        # NEW: Get similar analysis patterns from Chroma for better structure
        similar_analysis_block = self._get_similar_analysis_patterns(ferramentas, foco)

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
{similar_analysis_block}

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

    def _get_cached_research_context(self, ferramentas: str, foco: str) -> str:
        """Fetch research context from Chroma cache when skip_search is used.

        Retrieves relevant scraped content for the tool/focus combination
        to enhance minimal research (when skip_search=True).

        Returns formatted context block with cached research data.
        """
        if not self.chroma:
            return ""

        try:
            # Parse tool name(s) from ferramentas string
            tool_names = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
            primary_tool = tool_names[0] if tool_names else None

            # Search for relevant research context (filtered by primary tool to avoid mixing data)
            query = f"{ferramentas} {foco} requisitos performance comparação benchmark"
            results = self.chroma.query_similar(
                query_text=query,
                tool=primary_tool,
                k=5,
                distance_threshold=0.25,
            )

            if not results:
                logger.debug(f"No cached context found for {ferramentas}")
                return ""

            context_block = ""
            urls_seen = set()

            for result in results[:5]:
                url = result.get("url", "")
                text = result.get("text", "")
                similarity = result.get("similarity", 0)

                if url in urls_seen or not text:
                    continue
                urls_seen.add(url)

                # Limit context to avoid bloat
                text_excerpt = text[:800]
                context_block += f"\n**De {url} (relevância: {similarity:.2f}):**\n{text_excerpt}...\n"

            if context_block:
                logger.info(f"Retrieved {len(urls_seen)} cached sources from Chroma")
                self.memory.log_event("analyst_chroma_context_retrieved", {
                    "ferramentas": ferramentas,
                    "foco": foco,
                    "sources_found": len(urls_seen),
                    "context_chars": len(context_block),
                })

            return context_block

        except Exception as e:
            logger.debug(f"Failed to get cached research context: {e}")
            return ""

    def _get_similar_analysis_patterns(self, ferramentas: str, foco: str) -> str:
        """Fetch similar analysis structures from Chroma for inspiration.

        Uses semantic search to find analyses with similar focus and tool types.
        Returns formatted block with structure examples to guide LLM analysis.
        """
        if not self.chroma:
            return ""

        try:
            # Parse tool name(s) from ferramentas string
            tool_names = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
            primary_tool = tool_names[0] if tool_names else None

            # Search for analyses with similar tool/foco (filtered by tool to avoid cross-tool data mixing)
            query = f"{ferramentas} análise {foco} tabela pros contras otimizações"
            results = self.chroma.query_similar(
                query_text=query,
                tool=primary_tool,
                k=3,
                distance_threshold=0.20,
            )

            if not results:
                return ""

            patterns_block = "\n## PADRÕES DE ANÁLISES SIMILARES (para referência):\n"
            for i, result in enumerate(results[:3], 1):
                text_preview = result.get("text", "")[:200]
                title = result.get("title", "Análise")
                similarity = result.get("similarity", 0)

                patterns_block += f"\n**Padrão {i}:** {title} (relevância: {similarity:.2f})\n"
                patterns_block += f"```\n{text_preview}...\n```\n"

            patterns_block += "\nAdapte a estrutura de Prós/Contras/Otimizações baseado nesses padrões.\n"
            logger.debug(f"Injected {len(results)} analysis patterns from Chroma")
            self.memory.log_event("analyst_patterns_injected", {
                "query": query,
                "patterns_found": len(results),
            })
            return patterns_block

        except Exception as e:
            logger.debug(f"Failed to get analysis patterns from Chroma: {e}")
            return ""

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
