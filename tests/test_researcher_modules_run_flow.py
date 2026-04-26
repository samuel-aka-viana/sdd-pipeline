from types import SimpleNamespace

import numpy as np

from sdd.researcher_modules.run_flow import run_research


class _MemoryStub:
    def log_event(self, _name, _payload):
        return None


class _LoggerStub:
    def debug(self, *_args, **_kwargs):
        return None

    def info(self, *_args, **_kwargs):
        return None

    def warning(self, *_args, **_kwargs):
        return None


def test_run_research_accepts_numpy_inputs_for_questions_and_urls():
    query_calls = {}

    def _build_queries_fn(**_kwargs):
        return ["query 1"]

    def _new_chain_run_fn(**_kwargs):
        return None

    def _search_multi_fn(_queries, force_refresh=False):
        query_calls["called"] = True
        query_calls["force_refresh"] = force_refresh
        return {}

    def _build_context_fn(_filtered_results_by_query, tool):
        return f"contexto para {tool}"

    def _prompts_get_fn(*_args, **_kwargs):
        return "prompt-ok"

    def _llm_generate_fn(**_kwargs):
        return SimpleNamespace(response="research-ok")

    result = run_research(
        tool="ministack",
        alternative="localstack",
        foco="comparação geral",
        questoes=np.array(["latência", "custo"]),
        refresh_search=False,
        targeted_questions_only=False,
        urls=np.array(["https://example.org/a", "https://example.org/b"], dtype=object),
        skip_search=True,
        build_queries_fn=_build_queries_fn,
        new_chain_run_fn=_new_chain_run_fn,
        search_multi_fn=_search_multi_fn,
        memory=_MemoryStub(),
        load_domain_scrape_stats_fn=lambda: None,
        filter_search_results_fn=lambda **kwargs: kwargs["results_by_query"],
        count_results_fn=lambda r: sum(len(v) for v in r.values()),
        save_urls_fn=lambda *_args, **_kwargs: None,
        build_context_fn=_build_context_fn,
        save_context_debug_fn=lambda **_kwargs: None,
        get_lessons_for_prompt_fn=lambda: "",
        prompts_get_fn=_prompts_get_fn,
        llm_generate_fn=_llm_generate_fn,
        model="x",
        temp=0.1,
        ctx_len=1024,
        timeout=30,
        get_active_chain_run_fn=lambda: {},
        write_chain_phase_fn=lambda *_args, **_kwargs: None,
        finalize_chain_run_fn=lambda: None,
        logger=_LoggerStub(),
        get_last_scrape_stats_fn=lambda: {"discovered": 1, "ok": 1, "fail": 0},
    )

    assert result == "research-ok"
    assert "called" not in query_calls
