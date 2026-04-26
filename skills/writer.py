import logging
from skills.base import SkillBase
from skills.templates import build_question_answer_template_block, build_objective_requirements_block
from utils import compact_text_block

logger = logging.getLogger(__name__)


class WriterSkill(SkillBase):
    ROLE = "writer"

    def __init__(self, memory, spec_path="spec/article_spec.yaml", chroma=None):
        super().__init__(memory, spec_path, chroma)
        # TODO Phase 4: replace with LangChain native
        llm_conf = self.spec.get("llm", {})
        writer_input = llm_conf.get("writer_input", {})
        self.max_research_chars = writer_input.get("max_research_chars", 16000)
        self.max_analysis_chars = writer_input.get("max_analysis_chars", 16000)
        self.max_correction_chars = writer_input.get("max_correction_chars", 4000)
        self.truncation_stats: dict = {}

    def run(
        self,
        research,
        analysis,
        ferramentas,
        contexto,
        foco="comparação geral",
        questoes=None,
        correction_instructions="",
        research_quality="ok",
        evidence_pack=None,
    ):
        questoes = questoes or []

        if evidence_pack and evidence_pack.retained_urls:
            urls_lines = "\n".join(
                f"- {url}" for url in evidence_pack.retained_urls[:20]
            )
            evidence_summary = (
                f"FONTES VERIFICADAS ({len(evidence_pack.retained_urls)} URLs"
                f" — use APENAS estas em Referências):\n{urls_lines}"
            )
        else:
            evidence_summary = ""
        logger.debug(f"Starting writer: ferramentas={ferramentas}, foco={foco}, quality={research_quality}")

        lessons = self.memory.get_lessons_for_prompt()

        compact_research = compact_text_block(research, self.max_research_chars, "DADOS DE PESQUISA", memory=self.memory, logger=logger)
        compact_analysis = compact_text_block(analysis, self.max_analysis_chars, "ANÁLISE TÉCNICA", memory=self.memory, logger=logger)

        correction_block = ""
        if correction_instructions:
            compact_corrections = compact_text_block(
                correction_instructions, self.max_correction_chars, "CORREÇÕES", memory=self.memory, logger=logger
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
            lista = "\n".join(f"- {q}" for q in questoes)
            questoes_block = (
                f"\nO artigo DEVE responder explicitamente estas perguntas:\n{lista}\n"
                "Cada resposta deve aparecer claramente no texto.\n"
            )
            question_answer_template_block = build_question_answer_template_block(questoes)

        objective_requirements_block = build_objective_requirements_block(questoes, ferramentas)
        lessons_block = f"\n{lessons}\n" if lessons else ""
        writing_examples_block = self._format_writing_examples(ferramentas, foco)

        research_warning = ""
        if research_quality == "weak":
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

        stable_prefix, volatile_suffix = self.prompts.get_with_cache(
            "writer",
            "main",
            ferramentas=ferramentas,
            contexto=contexto,
            foco=foco,
            questoes_block=questoes_block,
            correction_block=correction_block,
            lessons_block=lessons_block,
            writing_examples_block=writing_examples_block,
            research_warning=research_warning,
            evidence_summary=evidence_summary,
            compact_research=compact_research,
            compact_analysis=compact_analysis,
            objective_requirements_block=objective_requirements_block,
            question_answer_template_block=question_answer_template_block,
        )
        if not stable_prefix:
            raise RuntimeError("Prompt template missing: prompts/writer.yaml#main")

        resp = self.llm.generate_cached(
            role="writer",
            model=self.model,
            stable_prefix=stable_prefix,
            volatile_suffix=volatile_suffix,
            temperature=self.temp,
            num_ctx=self.ctx_len,
            timeout=self.timeout,
        )
        self.memory.log_event("article_written", {"ferramentas": ferramentas})
        return resp.response

    def _format_writing_examples(self, ferramentas: str, foco: str) -> str:
        if not self.chroma:
            return ""
        try:
            results = self.chroma.find_writing_examples(ferramentas)
        except Exception as e:
            logger.debug(f"Chroma writing examples failed: {e}")
            return ""
        if not results:
            return ""
        block = "\n## EXEMPLOS DE ARTIGOS BEM ESCRITOS (para referência de estilo):\n"
        for i, r in enumerate(results[:2], 1):
            block += (
                f"\n**Exemplo {i}:** {r.get('title', 'Sem título')} "
                f"(similaridade: {r.get('similarity', 0):.2f})\n"
                f"```\n{r.get('text', '')[:300]}...\n```\n"
            )
            if r.get("url"):
                block += f"Fonte: {r['url']}\n"
        block += "\nUse esses exemplos como referência para estrutura e nível de detalhe.\n"
        self.memory.log_event("writer_examples_injected", {"examples_found": len(results)})
        return block

