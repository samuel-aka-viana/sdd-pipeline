import gzip
import json
import asyncio
from unittest.mock import Mock

from sdd.researcher_modules.chain_run import finalize_chain_run, new_chain_run, write_chain_phase
from sdd.researcher_modules.crawl4ai_config import build_crawl4ai_run_config
from sdd.researcher_modules.debug_io import save_context_debug, save_html_debug
from sdd.researcher_modules.markdown import (
    extract_best_markdown,
    extract_redirect_target,
    extract_section_structure,
    is_low_quality_text,
)
from sdd.researcher_modules.queries import build_queries, build_question_query
from sdd.researcher_modules.relevance import filter_search_results
from sdd.researcher_modules.scrape_async import async_crawl_task
from sdd.researcher_modules.source_quality import infer_source_quality, load_domain_scrape_stats
from sdd.researcher_modules.relevance import should_skip_url


class DummyMarkdown:
    def __init__(self, fit_markdown=None, raw_markdown=None):
        self.fit_markdown = fit_markdown
        self.raw_markdown = raw_markdown


class DummyResult:
    def __init__(self, redirected_url="", response_headers=None):
        self.redirected_url = redirected_url
        self.response_headers = response_headers or {}


class DummyCrawlResult:
    def __init__(self, status_code=200, html="<html>x</html>", markdown=None, redirected_url=""):
        self.status_code = status_code
        self.html = html
        self.markdown = markdown
        self.redirected_url = redirected_url
        self.response_headers = {}


class DummyCrawler:
    def __init__(self, result):
        self._result = result

    async def arun(self, url, config):
        _ = (url, config)
        return self._result


class DummyRunConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyPruningFilter:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DummyMarkdownGenerator:
    def __init__(self, content_filter=None, options=None):
        self.content_filter = content_filter
        self.options = options or {}


def test_build_question_query_adds_performance_terms():
    query = build_question_query(
        tool="docker",
        alternative="kubernetes",
        question="Qual a latencia e throughput do docker?",
        focus="comparação geral",
    )

    assert "benchmark latency throughput" in query


def test_build_queries_targeted_only_limits_to_six():
    questions = [f"q{i}" for i in range(10)]
    queries = build_queries(
        tool="docker",
        alternative="podman",
        foco="comparação geral",
        questoes=questions,
        targeted_questions_only=True,
    )

    assert len(queries) == 6


def test_filter_search_results_respects_score_and_sorting():
    results_by_query = {
        "docker docs": [
            {
                "url": "https://docs.docker.com/engine/install/",
                "title": "Install Docker Engine",
                "snippet": "Official docker docs with benchmark and troubleshooting",
            },
            {
                "url": "https://example.com/random-post",
                "title": "Some post",
                "snippet": "generic content",
            },
        ]
    }

    filtered = filter_search_results(
        results_by_query=results_by_query,
        tool="docker",
        alternative="",
        skip_domains=set(),
        domain_scrape_stats={},
        source_min_score_keep=3,
        source_max_results_per_query=5,
    )

    assert len(filtered["docker docs"]) == 1
    assert filtered["docker docs"][0]["url"].startswith("https://docs.docker.com")


def test_should_skip_url_blocks_low_signal_ansible_result_domains():
    urls = [
        "https://a-listware.com/blog/ansible-alternatives",
        "https://www.guru99.com/ansible-alternative.html",
        "https://bobcares.com/blog/ansible-alternatives-open-source/",
        "https://alternativeto.net/software/ansible-tower/",
        "https://www.freelancer.com/job-search/ansible-serverspec/",
        "https://speakerdeck.com/jqckb/molecule-ou-comment-tester-ses-roles-ansible",
        "https://www.webkkk.net/shakahl/ansible-runner-docker",
        "https://dohost.us/index.php/2025/11/04/optimizing-playbook-performance-forks-pipelining-strategy/",
    ]

    for url in urls:
        assert should_skip_url(url, skip_domains=set(), domain_scrape_stats={}) is True


def test_extract_section_structure_flags_tips_errors_and_tables():
    markdown = """
## Tip de performance
use cache
## Error comum
stack trace
| col | val |
| --- | --- |
"""
    sections = extract_section_structure(markdown)

    assert sections["tips"]
    assert sections["errors"]
    assert sections["has_table"] is True


def test_extract_best_markdown_prefers_fit_then_raw_then_string():
    obj = DummyMarkdown(fit_markdown="x" * 600, raw_markdown="raw")
    assert extract_best_markdown(obj) == "x" * 600
    assert extract_best_markdown(DummyMarkdown(fit_markdown="small", raw_markdown="raw")) == "raw"
    assert extract_best_markdown("plain") == "plain"


def test_is_low_quality_text_and_redirect_extraction():
    assert is_low_quality_text("skip to main content") is True
    assert is_low_quality_text("texto " * 200) is False

    result = DummyResult(response_headers={"Location": "/new-path"})
    target = extract_redirect_target(result, "https://example.com/old")
    assert target == "https://example.com/new-path"


def test_source_quality_and_domain_stats_loading(tmp_path):
    missing = load_domain_scrape_stats(tmp_path / "missing.json")
    assert missing == {}

    data_file = tmp_path / "domain_stats.json"
    payload = {"docs.docker.com": {"attempts": 4, "fail": 1}}
    data_file.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_domain_scrape_stats(data_file)
    assert loaded == payload

    assert infer_source_quality("https://docs.docker.com/engine/install/") == "official"
    assert infer_source_quality("https://stackoverflow.com/questions/1") == "medium"
    assert infer_source_quality("https://totally-unknown.example") == "unknown"


def test_build_crawl4ai_run_config_optionally_injects_markdown_generator():
    with_filter = build_crawl4ai_run_config(
        crawler_run_config_cls=DummyRunConfig,
        has_markdown_filters=True,
        pruning_content_filter_cls=DummyPruningFilter,
        default_markdown_generator_cls=DummyMarkdownGenerator,
    )
    assert "markdown_generator" in with_filter.kwargs

    no_filter = build_crawl4ai_run_config(
        crawler_run_config_cls=DummyRunConfig,
        has_markdown_filters=False,
        pruning_content_filter_cls=DummyPruningFilter,
        default_markdown_generator_cls=DummyMarkdownGenerator,
    )
    assert "markdown_generator" not in no_filter.kwargs
    assert no_filter.kwargs["wait_until"] == "load"


def test_debug_io_saves_context_and_html(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = Mock()
    memory = Mock()

    context_path = save_context_debug(
        tool="docker",
        context="conteudo de teste",
        last_scrape_stats={"ok": 1, "fail": 0, "skipped": 0},
        max_scrapes_per_tool=12,
        max_chars_per_scrape=4000,
        logger=logger,
    )
    assert context_path.endswith("output/debug_context_docker.md")
    assert "CONTEXTO BRUTO - docker" in (tmp_path / context_path).read_text(encoding="utf-8")

    html_path = save_html_debug(
        tool="docker",
        url="https://docs.docker.com/engine/install/",
        html="<html>ok</html>",
        status="ok",
        source="crawl4ai",
        snippet="",
        html_debug_enabled=True,
        memory=memory,
        logger=logger,
    )
    assert html_path.endswith(".html.gz")
    with gzip.open(tmp_path / html_path, "rt", encoding="utf-8") as fh:
        saved = fh.read()
    assert "<!-- html_present: true -->" in saved
    memory.log_event.assert_called()


def test_debug_io_respects_html_toggle(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = Mock()
    memory = Mock()
    html_path = save_html_debug(
        tool="docker",
        url="https://docs.docker.com/engine/install/",
        html="<html>ok</html>",
        status="ok",
        source="crawl4ai",
        snippet="",
        html_debug_enabled=False,
        memory=memory,
        logger=logger,
    )
    assert html_path == ""
    memory.log_event.assert_not_called()


def test_chain_run_roundtrip_writes_files_and_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = Mock()

    run_data = new_chain_run(
        tool="docker",
        foco="comparação geral",
        alternative="podman",
        queries=["docker vs podman"],
    )
    assert run_data["tool_safe"] == "docker"

    phase_path = write_chain_phase(
        run_data=run_data,
        phase="discovery",
        payload={"items": [1, 2]},
        memory=memory,
    )
    assert phase_path.endswith("01_discovery.json")

    run_data["phases"]["discovery"].append({"url": "https://docs.docker.com"})
    finalized, entry = finalize_chain_run(
        run_data=run_data,
        last_scrape_stats={"ok": 1, "fail": 0, "skipped": 0},
        memory=memory,
    )
    assert finalized is not None
    assert entry is not None
    assert "summary" in finalized["files"]


def test_async_crawl_task_returns_ok_payload_without_real_crawl4ai():
    logger = Mock()
    result = DummyCrawlResult(status_code=200, html="<html>ok</html>", markdown="conteudo markdown")
    crawler = DummyCrawler(result)
    payload = asyncio.run(
        async_crawl_task(
            crawler=crawler,
            url="https://example.com",
            result_item={"url": "https://example.com"},
            config=object(),
            domain_semaphore=asyncio.Semaphore(1),
            extract_redirect_target_fn=lambda crawl_result, url: "",
            extract_best_markdown_fn=lambda markdown_obj: markdown_obj or "",
            is_low_quality_text_fn=lambda text: False,
            max_chars_per_scrape=4000,
            logger=logger,
        )
    )
    url, scrape_result, result_item = payload
    assert url == "https://example.com"
    assert scrape_result["status"] == "ok"
    assert result_item["url"] == "https://example.com"
