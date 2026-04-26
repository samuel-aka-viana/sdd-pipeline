import yaml
import logging
from pathlib import Path
from typing import Optional, Any

from llm import LLMClient
from utils.logger import EventLog
from skills.prompts.manager import PromptManager

from memory.research_chroma import ResearchChroma

try:
    from crawl4ai.content_filter_strategy import PruningContentFilter
    from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
    HAS_CRAWL4AI_MARKDOWN_FILTERS = True
except ImportError:
    HAS_CRAWL4AI_MARKDOWN_FILTERS = False

from researcher_modules.constants import (
    DEFAULT_SKIP_DOMAINS,
    DOMAIN_SCRAPE_STATS_PATH,
    HTML_DEBUG_ENABLED,
    MAX_CHARS_PER_SCRAPE,
    MAX_PARALLEL_PER_DOMAIN,
    MAX_SCRAPES_PER_TOOL,
)
from researcher_modules.crawl4ai_config import build_crawl4ai_run_config
from researcher_modules.cached_search import (
    expand_cached_queries as expand_cached_queries_module,
    search_cached_content as search_cached_content_module,
)
from researcher_modules.chain_run import (
    finalize_chain_run,
    new_chain_run,
    write_chain_phase,
)
from researcher_modules.context_builder import build_context as build_context_module
from researcher_modules.debug_io import (
    save_context_debug as save_context_debug_module,
    save_html_debug as save_html_debug_module,
)
from researcher_modules.markdown import (
    extract_best_markdown,
    extract_redirect_target,
    extract_section_structure,
    is_low_quality_text,
)
from researcher_modules.queries import (
    build_queries as build_queries_module,
    build_question_query as build_question_query_module,
    has_intent_term as has_intent_term_module,
)
from researcher_modules.reanalyze import reanalyze_urls_for_tips_and_errors as reanalyze_urls_module
from researcher_modules.relevance import (
    build_relevance_keywords as build_relevance_keywords_module,
    build_tool_identity_terms as build_tool_identity_terms_module,
    compute_source_score as compute_source_score_module,
    domain_fail_rate,
    filter_search_results as filter_search_results_module,
    has_required_tool_anchor as has_required_tool_anchor_module,
    has_tool_identity_match as has_tool_identity_match_module,
    is_high_trust_host as is_high_trust_host_module,
    is_low_signal_host as is_low_signal_host_module,
    is_medium_trust_host as is_medium_trust_host_module,
    is_qna_host as is_qna_host_module,
    is_result_relevant as is_result_relevant_module,
    should_skip_url as should_skip_url_module,
)
from researcher_modules.scrape_async import scrape_urls_batch_async
from researcher_modules.scrape_threaded import scrape_urls_parallel as scrape_urls_parallel_module
from researcher_modules.source_quality import infer_source_quality, load_domain_scrape_stats
from researcher_modules.run_flow import run_research

logger = logging.getLogger(__name__)


class ResearcherSkill:
    """Executa pesquisa técnica estruturada com focus e coleta de dados.
    
    Combina busca multiquery, scraping de URLs e análise LLM para gerar
    relatórios de pesquisa sobre uma ferramenta.
    """

    def __init__(
        self,
        search_tool,
        scraper_tool,
        memory,
        spec_path="spec/article_spec.yaml",
        pipeline_logger=None,
        chroma=None,
    ):
        """Initialize researcher with tools and configuration.
        
        Args:
            search_tool: Search tool implementing search_multi() and save_urls()
            scraper_tool: Scraper tool implementing extract_text()
            memory: Memory system for learning lessons and logging events
            spec_path: Path to article_spec.yaml with LLM config
        """
        self.search = search_tool
        self.scraper = scraper_tool
        self.memory = memory
        self.chroma = chroma if chroma is not None else ResearchChroma()
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self.llm = LLMClient(spec_path)
        self.prompts = PromptManager(memory, prompts_dir="prompts")
        self.model = self.llm.model_for_role("researcher")
        self.pipeline_logger = pipeline_logger
        self.event_log = pipeline_logger.event_log if pipeline_logger else EventLog()
        self.last_scrape_stats = {"ok": 0, "fail": 0, "skipped": 0}
        scraper_conf = self.spec.get("research", {}).get("scraper", {})
        self.max_scrapes_per_tool = int(scraper_conf.get("max_scrapes_per_tool", MAX_SCRAPES_PER_TOOL))
        self.max_chars_per_scrape = int(scraper_conf.get("max_chars_per_page", MAX_CHARS_PER_SCRAPE))
        skip_domains_from_spec = (
            self.spec.get("research", {})
            .get("scraper", {})
            .get("skip_domains", [])
        )
        self.skip_domains = {
            domain.lower().strip()
            for domain in (list(DEFAULT_SKIP_DOMAINS) + list(skip_domains_from_spec))
            if domain and domain.strip()
        }
        source_guardrails = self.spec.get("research", {}).get("source_guardrails", {})
        self.source_min_score_keep = int(source_guardrails.get("min_score_keep", 3))
        self.source_max_results_per_query = int(source_guardrails.get("max_results_per_query", 5))
        llm_conf = self.spec.get("llm", {})
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        context_length = llm_conf.get("context_length", self.spec.get("ollama", {}).get("context_length", {}))
        self.temp = temperatures["researcher"]
        self.timeout = timeouts.get("researcher", timeouts.get("default", 300))
        self.ctx_len = context_length.get("researcher", context_length.get("default", 8192))
        # Store scraped URLs for re-analysis (e.g., when looking for tips/errors)
        self._scraped_urls = {}
        # Track URL richness (has tips, errors, commands, etc.)
        self._url_richness = {}
        self.domain_scrape_stats = self._load_domain_scrape_stats()
        self.chain_runs: dict[str, dict[str, Any]] = {}
        self._active_chain_run: dict[str, Any] | None = None

    def _new_chain_run(
        self,
        tool: str,
        foco: str,
        alternative: str,
        queries: list[str],
    ) -> dict[str, Any]:
        run_data = new_chain_run(
            tool=tool,
            foco=foco,
            alternative=alternative,
            queries=queries,
        )
        self._active_chain_run = run_data
        return run_data

    def _write_chain_phase(self, phase: str, payload: dict[str, Any]) -> str:
        return write_chain_phase(
            run_data=self._active_chain_run,
            phase=phase,
            payload=payload,
            memory=self.memory,
        )

    def _finalize_chain_run(self):
        run_data, chain_run_entry = finalize_chain_run(
            run_data=self._active_chain_run,
            last_scrape_stats=self.last_scrape_stats,
            memory=self.memory,
        )
        if not run_data or not chain_run_entry:
            return
        self.chain_runs[run_data["tool_safe"]] = chain_run_entry
        self._active_chain_run = None

    def get_chain_runs(self) -> dict[str, dict[str, Any]]:
        return dict(self.chain_runs)

    def _load_domain_scrape_stats(self) -> dict:
        return load_domain_scrape_stats(DOMAIN_SCRAPE_STATS_PATH)

    def _domain_fail_rate(self, host: str) -> float:
        return domain_fail_rate(self.domain_scrape_stats, host)

    def _infer_source_quality(self, url: str) -> str:
        return infer_source_quality(url)

    def extract_section_structure(self, _url: str, markdown_content: str) -> dict:
        return extract_section_structure(markdown_content)

    def log_url_found(
        self,
        url: str,
        title: str = "",
        status: str = "",
        elapsed: float | None = None,
        source: str = "",
        scrape_status: str = "",
        phase: str = "",
        preview: str = "",
    ):
        if self.pipeline_logger:
            self.pipeline_logger.found_url(
                url,
                title=title,
                status=status,
                elapsed=elapsed,
                source=source,
                scrape_status=scrape_status,
                phase=phase,
                preview=preview,
            )
            return
        self.event_log.log_event("url_found", {
            "url": url,
            "title": title,
            "status": status,
            "elapsed_seconds": elapsed,
            "source": source,
            "scrape_status": scrape_status,
            "phase": phase,
            "preview": preview[:100] if preview else "",
        })

    def run(
        self,
        tool,
        alternative="",
        foco="comparação geral",
        questoes=None,
        refresh_search: bool = False,
        targeted_questions_only: bool = False,
        urls: list[str] | None = None,
        skip_search: bool = False,
    ):
        return run_research(
            tool=tool,
            alternative=alternative,
            foco=foco,
            questoes=questoes,
            refresh_search=refresh_search,
            targeted_questions_only=targeted_questions_only,
            urls=urls,
            skip_search=skip_search,
            build_queries_fn=self.build_queries,
            new_chain_run_fn=self._new_chain_run,
            search_multi_fn=self.search.search_multi,
            memory=self.memory,
            load_domain_scrape_stats_fn=lambda: setattr(
                self,
                "domain_scrape_stats",
                self._load_domain_scrape_stats(),
            ),
            filter_search_results_fn=self.filter_search_results,
            count_results_fn=self.count_results,
            save_urls_fn=self.search.save_urls,
            build_context_fn=self.build_context,
            save_context_debug_fn=self.save_context_debug,
            get_lessons_for_prompt_fn=self.memory.get_lessons_for_prompt,
            prompts_get_fn=self.prompts.get,
            llm_generate_fn=self.llm.generate,
            model=self.model,
            temp=self.temp,
            ctx_len=self.ctx_len,
            timeout=self.timeout,
            get_active_chain_run_fn=lambda: self._active_chain_run,
            write_chain_phase_fn=self._write_chain_phase,
            finalize_chain_run_fn=self._finalize_chain_run,
            logger=logger,
            get_last_scrape_stats_fn=lambda: self.last_scrape_stats,
        )

    def save_context_debug(self, tool: str, context: str):
        save_context_debug_module(
            tool=tool,
            context=context,
            last_scrape_stats=self.last_scrape_stats,
            max_scrapes_per_tool=self.max_scrapes_per_tool,
            max_chars_per_scrape=self.max_chars_per_scrape,
            logger=logger,
        )

    def save_html_debug(
        self,
        tool: str,
        url: str,
        html: str,
        status: str,
        source: str = "",
        snippet: str = "",
    ):
        save_html_debug_module(
            tool=tool,
            url=url,
            html=html,
            status=status,
            source=source,
            snippet=snippet,
            html_debug_enabled=HTML_DEBUG_ENABLED,
            memory=self.memory,
            logger=logger,
        )

    def _build_crawl4ai_run_config(self, crawler_run_config_cls):
        return build_crawl4ai_run_config(
            crawler_run_config_cls=crawler_run_config_cls,
            has_markdown_filters=HAS_CRAWL4AI_MARKDOWN_FILTERS,
            pruning_content_filter_cls=PruningContentFilter if HAS_CRAWL4AI_MARKDOWN_FILTERS else None,
            default_markdown_generator_cls=DefaultMarkdownGenerator if HAS_CRAWL4AI_MARKDOWN_FILTERS else None,
        )

    def _extract_best_markdown(self, markdown_obj) -> str:
        return extract_best_markdown(markdown_obj)

    def _is_low_quality_text(self, text: str) -> bool:
        return is_low_quality_text(text)

    def _extract_redirect_target(self, result, source_url: str) -> str:
        return extract_redirect_target(result, source_url)

    def build_queries(
        self,
        tool,
        alternative,
        foco,
        questoes,
        targeted_questions_only: bool = False,
    ):
        return build_queries_module(
            tool=tool,
            alternative=alternative,
            foco=foco,
            questoes=questoes,
            targeted_questions_only=targeted_questions_only,
        )

    def build_question_query(
        self,
        tool: str,
        alternative: str,
        question: str,
        focus: str,
    ) -> str:
        return build_question_query_module(
            tool=tool,
            alternative=alternative,
            question=question,
            focus=focus,
        )

    def has_intent_term(self, text: str, terms: set[str]) -> bool:
        return has_intent_term_module(text, terms)

    def build_context(self, results_by_query, tool: str = "unknown"):
        context, stats = build_context_module(
            results_by_query=results_by_query,
            tool=tool,
            max_scrapes_per_tool=self.max_scrapes_per_tool,
            max_chars_per_scrape=self.max_chars_per_scrape,
            chroma=self.chroma,
            memory=self.memory,
            active_chain_run=self._active_chain_run,
            should_skip_url_fn=self.should_skip_url,
            log_url_found_fn=self.log_url_found,
            write_chain_phase_fn=self._write_chain_phase,
            scrape_urls_parallel_fn=self._scrape_urls_parallel,
            save_html_debug_fn=self.save_html_debug,
            extract_section_structure_fn=self.extract_section_structure,
            infer_source_quality_fn=self._infer_source_quality,
            scraped_urls_store=self._scraped_urls,
            url_richness_store=self._url_richness,
            logger=logger,
        )
        self.last_scrape_stats = stats
        if self._active_chain_run is not None:
            self._active_chain_run["last_scrape_stats"] = dict(stats)
        return context

    def _scrape_urls_parallel(self, urls_to_scrape: list[tuple], _tool: str) -> list[tuple]:
        return scrape_urls_parallel_module(
            urls_to_scrape=urls_to_scrape,
            scraper=self.scraper,
            max_parallel_per_domain=MAX_PARALLEL_PER_DOMAIN,
            async_batch_threshold=10,
            scrape_urls_batch_async_fn=self._scrape_urls_batch_async,
            logger=logger,
        )

    def _scrape_urls_batch_async(self, urls_to_scrape: list[tuple]) -> list[tuple]:
        return scrape_urls_batch_async(
            urls_to_scrape=urls_to_scrape,
            build_crawl4ai_run_config_fn=self._build_crawl4ai_run_config,
            extract_redirect_target_fn=self._extract_redirect_target,
            extract_best_markdown_fn=self._extract_best_markdown,
            is_low_quality_text_fn=self._is_low_quality_text,
            max_chars_per_scrape=self.max_chars_per_scrape,
            max_parallel_per_domain=MAX_PARALLEL_PER_DOMAIN,
            logger=logger,
        )

    def reanalyze_urls_for_tips_and_errors(self, tool: str, focus_on: str = "tips_and_errors") -> str:
        return reanalyze_urls_module(
            tool=tool,
            focus_on=focus_on,
            chroma=self.chroma,
            scraped_urls=self._scraped_urls,
            memory=self.memory,
            prompts=self.prompts,
            llm=self.llm,
            model=self.model,
            temp=self.temp,
            ctx_len=self.ctx_len,
            timeout=self.timeout,
        )

    def search_cached_content(self, query: str, tool: Optional[str] = None, k: int = 5) -> list[dict]:
        return search_cached_content_module(
            query=query,
            tool=tool,
            k=k,
            chroma=self.chroma,
            memory=self.memory,
            logger=logger,
            event_log=self.event_log,
        )

    def _expand_cached_queries(self, query: str, tool: Optional[str] = None) -> list[str]:
        return expand_cached_queries_module(query=query, tool=tool)

    def filter_search_results(
        self,
        results_by_query: dict[str, list[dict]],
        tool: str,
        alternative: str,
    ) -> dict[str, list[dict]]:
        return filter_search_results_module(
            results_by_query=results_by_query,
            tool=tool,
            alternative=alternative,
            skip_domains=self.skip_domains,
            domain_scrape_stats=self.domain_scrape_stats,
            source_min_score_keep=self.source_min_score_keep,
            source_max_results_per_query=self.source_max_results_per_query,
        )

    def build_relevance_keywords(self, tool: str, alternative: str) -> set[str]:
        return build_relevance_keywords_module(tool, alternative)

    def build_tool_identity_terms(self, tool: str, alternative: str) -> set[str]:
        return build_tool_identity_terms_module(tool, alternative)

    def is_result_relevant(
        self,
        result_item: dict,
        relevance_keywords: set[str],
        tool_identity_terms: set[str],
    ) -> bool:
        return is_result_relevant_module(
            result_item=result_item,
            relevance_keywords=relevance_keywords,
            tool_identity_terms=tool_identity_terms,
        )

    def compute_source_score(
        self,
        result_item: dict,
        relevance_keywords: set[str],
        tool_identity_terms: set[str],
    ) -> int:
        return compute_source_score_module(
            result_item=result_item,
            relevance_keywords=relevance_keywords,
            tool_identity_terms=tool_identity_terms,
            domain_scrape_stats=self.domain_scrape_stats,
        )

    def is_high_trust_host(self, host: str) -> bool:
        return is_high_trust_host_module(host)

    def is_medium_trust_host(self, host: str) -> bool:
        return is_medium_trust_host_module(host)

    def is_qna_host(self, host: str) -> bool:
        return is_qna_host_module(host)

    def has_tool_identity_match(self, combined_text: str, tool_identity_terms: set[str]) -> bool:
        return has_tool_identity_match_module(combined_text, tool_identity_terms)

    def has_required_tool_anchor(self, combined_text: str, tool_identity_terms: set[str]) -> bool:
        return has_required_tool_anchor_module(combined_text, tool_identity_terms)

    def is_low_signal_host(self, host: str) -> bool:
        return is_low_signal_host_module(host)

    def should_skip_url(self, url: str) -> bool:
        return should_skip_url_module(
            url=url,
            skip_domains=self.skip_domains,
            domain_scrape_stats=self.domain_scrape_stats,
        )

    def count_results(self, results_by_query: dict[str, list[dict]]) -> int:
        return sum(len(results) for results in results_by_query.values())
