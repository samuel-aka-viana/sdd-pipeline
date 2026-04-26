"""Stage: análise (analyst).

Suporta paralelismo opcional por aspecto, controlado pelo router/memory.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from httpx import TimeoutException


def _timeout_fallback(pipeline, research: str) -> str:
    """Fallback when analyst times out: log error and return raw research."""
    pipeline.log.error(
        f"Analyst timeout ({pipeline.analyst.timeout}s) — usando research bruto"
    )
    return f"Análise interrompida por timeout ({pipeline.analyst.timeout}s).\n\n{research}"


def run_analysis_stage(
    pipeline,
    *,
    research: str,
    ferramentas: str,
    contexto: str,
    foco: str,
    questoes: list[str],
    started_at: float,
    evidence_pack=None,
) -> str:
    pipeline.log.section(2, 3, "Analisando")
    pipeline.enforce_global_timeout(started_at, stage="análise")

    route = pipeline.memory.get("route", {})
    aspects = route.get("analysis_aspects", ["core"])
    can_parallelize = route.get("can_parallelize_analysis", False)

    if not can_parallelize or len(aspects) <= 1:
        analysis = _run_sequential_analysis(pipeline, research, ferramentas, contexto, foco, questoes, evidence_pack)
    else:
        analysis = _run_parallel_analysis(pipeline, research, ferramentas, contexto, aspects, questoes, evidence_pack)

    pipeline.memory.set("analysis", analysis)
    pipeline.save_debug("analysis", analysis)
    return analysis


def _run_sequential_analysis(pipeline, research, ferramentas, contexto, foco, questoes, evidence_pack=None):
    with pipeline.log.task("Gerando análise"):
        try:
            return pipeline.analyst.run(
                research=research,
                ferramentas=ferramentas,
                contexto=contexto,
                foco=foco,
                questoes=questoes,
            )
        except TimeoutException:
            return _timeout_fallback(pipeline, research)


def _run_parallel_analysis(pipeline, research, ferramentas, contexto, aspects, questoes, evidence_pack=None):
    with pipeline.log.task(f"Gerando análise paralela ({len(aspects)} aspectos)"):
        results: dict[str, str] = {}
        try:
            with ThreadPoolExecutor(max_workers=min(len(aspects), 3)) as pool:
                futures = {
                    pool.submit(
                        pipeline.analyst.run,
                        research=research,
                        ferramentas=ferramentas,
                        contexto=contexto,
                        foco=aspect,
                        questoes=questoes,
                    ): aspect
                    for aspect in aspects
                }
                for future in as_completed(futures):
                    aspect = futures[future]
                    try:
                        results[aspect] = future.result()
                    except Exception as e:
                        pipeline.log.error(f"Parallel analyst failed for {aspect}: {e}")
                        results[aspect] = ""

            analysis = "\n\n---\n\n".join(
                f"## Análise: {asp.upper()}\n{txt}"
                for asp, txt in results.items() if txt
            )
            pipeline.memory.log_event("parallel_analysis_complete", {
                "aspects": len(aspects),
                "successful": len([v for v in results.values() if v]),
            })
            return analysis
        except TimeoutException:
            return _timeout_fallback(pipeline, research)
