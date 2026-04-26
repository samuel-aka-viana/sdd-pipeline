"""Stage: writer (geração do artigo)."""

from __future__ import annotations

from httpx import TimeoutException


def run_writer_iteration(
    pipeline,
    *,
    iteration: int,
    research: str,
    analysis: str,
    ferramentas: str,
    contexto: str,
    foco: str,
    questoes: list[str],
    correction_instructions: str,
    research_quality: str,
    evidence_pack=None,
) -> str:
    with pipeline.log.task("Escrevendo artigo"):
        try:
            return pipeline.writer.run(
                research=research,
                analysis=analysis,
                ferramentas=ferramentas,
                contexto=contexto,
                foco=foco,
                questoes=questoes,
                correction_instructions=correction_instructions,
                research_quality=research_quality,
            )
        except TimeoutException:
            pipeline.log.error(
                f"Writer timeout ({pipeline.writer.timeout}s) na iteração {iteration}"
            )
            if iteration == pipeline.max_iterations:
                return f"# Timeout\n\nGeração interrompida: writer excedeu {pipeline.writer.timeout}s."
            return ""
