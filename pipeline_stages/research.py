"""Stage: pesquisa (researcher).

Pesquisa por ferramenta de forma sequencial com checagem de timeout global.
Saída textual em blocos `# {tool}\n{data}`, ordem preservada pela lista
original de ferramentas.
"""

from __future__ import annotations

from httpx import TimeoutException


def run_research_stage(
    pipeline,
    *,
    ferramentas: str,
    foco: str,
    questoes: list[str],
    started_at: float,
    refresh_search: bool = False,
    urls: list[str] | None = None,
    skip_search: bool = False,
) -> str:
    pipeline.log.section(1, 3, "Pesquisando")
    tools_list = pipeline.parse_tools(ferramentas)
    pipeline.enforce_global_timeout(started_at, stage="pesquisa (sequential start)")
    research_parts = [
        _research_one_tool(
            pipeline,
            tools_list,
            idx,
            foco,
            questoes,
            refresh_search,
            urls,
            skip_search,
            started_at,
        )
        for idx in range(len(tools_list))
    ]

    research = "\n\n".join(research_parts)
    pipeline.memory.set("research", research)
    return research


def _research_one_tool(pipeline, tools_list, idx, foco, questoes,
                       refresh_search, urls, skip_search, started_at):
    tool = tools_list[idx]
    pipeline.enforce_global_timeout(started_at, stage=f"pesquisa ({tool})")
    alternative_tool = next((t for t in tools_list if t != tool), "")
    tool_research = run_research_for_tool(
        pipeline,
        tool=tool,
        alternative_tool=alternative_tool,
        foco=foco,
        questoes=questoes,
        refresh_search=refresh_search,
        urls=urls,
        skip_search=skip_search,
    )
    pipeline.save_research_history(tool, tool_research)
    return tool_research


def run_research_for_tool(
    pipeline,
    *,
    tool: str,
    alternative_tool: str,
    foco: str,
    questoes: list[str],
    refresh_search: bool = False,
    targeted_questions_only: bool = False,
    urls: list[str] | None = None,
    skip_search: bool = False,
) -> str:
    with pipeline.log.task(f"Pesquisando {tool}"):
        try:
            data = pipeline.researcher.run(
                tool=tool,
                alternative=alternative_tool,
                foco=foco,
                questoes=questoes,
                refresh_search=refresh_search,
                targeted_questions_only=targeted_questions_only,
                urls=urls,
                skip_search=skip_search,
            )
        except TimeoutException:
            pipeline.log.error(
                f"Researcher timeout ({pipeline.researcher.timeout}s) — "
                f"dados insuficientes para {tool}"
            )
            data = f"# {tool}\n\nPesquisa interrompida por timeout ({pipeline.researcher.timeout}s)."
    return f"# {tool}\n{data}"
