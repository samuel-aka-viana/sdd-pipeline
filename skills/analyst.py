import logging
from skills.base import SkillBase
from skills.templates import comparison_template, integration_template, single_tool_template

logger = logging.getLogger(__name__)


class AnalystSkill(SkillBase):
    ROLE = "analyst"

    def run(self, research, ferramentas, contexto, foco="comparação geral", questoes=None):
        questoes = questoes or []
        logger.debug(f"Starting analysis for: {ferramentas}, foco: {foco}")

        if self.chroma and research and len(research.strip()) < 200:
            logger.info("Research is minimal — fetching context from Chroma cache")
            chroma_context = self._format_research_context(ferramentas, foco)
            if chroma_context:
                research = f"{research}\n\n## CONTEXTO DO CACHE CHROMA\n{chroma_context}"
                self.memory.log_event("analyst_used_chroma_cache", {
                    "ferramentas": ferramentas,
                    "foco": foco,
                    "context_chars": len(chroma_context),
                })

        tools = [t.strip() for t in ferramentas.lower().replace(" e ", ",").split(",") if t.strip()]
        is_single = len(tools) == 1
        is_integration = foco == "integração"

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {q}" for q in questoes)
            questoes_block = f"\nA análise deve fornecer dados para responder:\n{lista}\n"

        similar_analysis_block = self._format_analysis_patterns(ferramentas, foco)

        if is_single:
            table_block = single_tool_template(tools[0], foco)
        elif is_integration:
            table_block = integration_template(tools)
        else:
            table_block = comparison_template(tools)

        prompt = self.prompts.get(
            "analyst",
            "main",
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes_block=questoes_block,
            similar_analysis_block=similar_analysis_block,
            research=research,
            table_block=table_block,
        )
        if not prompt:
            raise RuntimeError("Prompt template missing: prompts/analyst.yaml#main")

        resp = self.llm.generate(
            role="analyst",
            model=self.model,
            prompt=prompt,
            temperature=self.temp,
            num_ctx=self.ctx_len,
            timeout=self.timeout,
        )
        self.memory.log_event("analysis_done", {
            "ferramentas": ferramentas,
            "foco": foco,
            "mode": "single" if is_single else ("integration" if is_integration else "comparison"),
        })
        return resp.response

    def _format_research_context(self, ferramentas: str, foco: str) -> str:
        try:
            results = self.chroma.find_research_context(ferramentas, foco)
        except Exception as e:
            logger.debug(f"Chroma research context failed: {e}")
            return ""
        if not results:
            return ""
        block = ""
        seen = set()
        for r in results[:5]:
            url = r.get("url", "")
            text = r.get("text", "")
            if url in seen or not text:
                continue
            seen.add(url)
            block += f"\n**De {url} (relevância: {r.get('similarity', 0):.2f}):**\n{text[:800]}...\n"
        if block:
            self.memory.log_event("analyst_chroma_context_retrieved", {
                "ferramentas": ferramentas,
                "foco": foco,
                "sources_found": len(seen),
                "context_chars": len(block),
            })
        return block

    def _format_analysis_patterns(self, ferramentas: str, foco: str) -> str:
        if not self.chroma:
            return ""
        try:
            results = self.chroma.find_analysis_patterns(ferramentas, foco)
        except Exception as e:
            logger.debug(f"Chroma analysis patterns failed: {e}")
            return ""
        if not results:
            return ""
        block = "\n## PADRÕES DE ANÁLISES SIMILARES (para referência):\n"
        for i, r in enumerate(results[:3], 1):
            block += (
                f"\n**Padrão {i}:** {r.get('title', 'Análise')} "
                f"(relevância: {r.get('similarity', 0):.2f})\n"
                f"```\n{r.get('text', '')[:200]}...\n```\n"
            )
        block += "\nAdapte a estrutura de Prós/Contras/Otimizações baseado nesses padrões.\n"
        self.memory.log_event("analyst_patterns_injected", {"patterns_found": len(results)})
        return block

