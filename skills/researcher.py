import yaml
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

from llm import LLMClient
from logger import EventLog

logger = logging.getLogger(__name__)

FOCUS_QUERIES: dict[str, list[str]] = {
    "comparação geral": [
        "{tool} vs {alternative}",
        "{tool} vs {alternative} when to use which",
        "{tool} vs {alternative} pros cons",
        "{tool} vs {alternative} benchmark comparison 2024 2025",
        "{tool} getting started official docs",
        "{tool} install quickstart tutorial",
        "{tool} common errors site:stackoverflow.com",
        "{tool} troubleshooting FAQ",
        "{tool} minimum requirements hardware",
        "{tool} vs {alternative} features table",
    ],
    "performance / throughput": [
        "{tool} benchmark throughput latency results",
        "{tool} vs {alternative} performance comparison numbers",
        "{tool} tuning performance production best practices",
        "{tool} common bottlenecks site:stackoverflow.com",
        "{tool} load test results concurrent connections",
        "{tool} profiling CPU memory usage under load",
        "{tool} vs {alternative} requests per second benchmark",
        "{tool} performance optimization config flags",
        "{tool} scalability limits production",
        "{tool} resource consumption idle vs peak",
    ],
    "custo": [
        "{tool} pricing model tiers",
        "{tool} pricing calculator",
        "{tool} vs {alternative} cost comparison monthly",
        "{tool} hidden costs egress storage bandwidth",
        "{tool} cost optimization tips reduce bill",
        "{tool} free tier limits what is included",
        "{tool} self hosted vs managed cost comparison",
        "{tool} cost at scale 100k 1M requests",
        "{tool} vs {alternative} total cost of ownership",
        "{tool} pricing changes 2024 2025",
    ],
    "migração": [
        "{tool} migration from {alternative} step by step",
        "{tool} migration guide official docs",
        "{tool} vs {alternative} compatibility layer",
        "{tool} breaking changes migration issues site:stackoverflow.com",
        "{tool} migration tool automated converter",
        "{tool} {alternative} coexistence side by side",
        "{tool} migration gotchas pitfalls real world",
        "{tool} API compatibility {alternative} drop in replacement",
        "{tool} migration rollback strategy",
        "{tool} config differences from {alternative}",
    ],
    "integração": [
        "{tool} {alternative} integration example tutorial",
        "{tool} {alternative} end to end setup guide",
        "{tool} {alternative} getting started together",
        "{tool} connector {alternative} site:github.com",
        "{tool} {alternative} docker compose example",
        "{tool} {alternative} architecture diagram how they fit",
        "{tool} {alternative} example project site:github.com",
        "{tool} exporter plugin {alternative}",
        "{tool} {alternative} common integration errors",
        "{tool} {alternative} production setup best practices",
    ],
    "segurança": [
        "{tool} security configuration hardening guide",
        "{tool} vs {alternative} security comparison",
        "{tool} authentication authorization setup RBAC",
        "{tool} CVE vulnerabilities site:github.com",
        "{tool} TLS SSL configuration mutual auth",
        "{tool} security best practices production",
        "{tool} rootless unprivileged setup",
        "{tool} secrets management configuration",
        "{tool} audit logging security events",
        "{tool} network policy firewall rules",
    ],
    "hardware limitado / edge": [
        "{tool} minimum requirements RAM CPU disk",
        "{tool} raspberry pi ARM installation tutorial",
        "{tool} vs {alternative} resource usage comparison",
        "{tool} low memory configuration optimization",
        "{tool} lightweight alternative embedded edge",
        "{tool} ARM64 aarch64 support",
        "{tool} reduce memory footprint tips",
        "{tool} run on 1GB 2GB 4GB RAM",
        "{tool} disable features save resources",
        "{tool} single node small cluster resource usage",
    ],
    "quantização / modelos locais": [
        "{tool} quantization Q4_K_M Q8_0 quality difference",
        "{tool} recommended models 8GB RAM 16GB RAM list",
        "{tool} tokens per second benchmark results table",
        "{tool} model RAM usage size comparison table",
        "{tool} best models to run locally 2024 2025",
        "{tool} run llama qwen gemma phi mistral RAM required",
        "{tool} how to check memory usage ps verbose",
        "{tool} GGUF model size RAM needed calculator",
        "{tool} compare quantization levels quality loss",
        "{tool} context length RAM impact 2048 4096 8192",
        "{tool} CPU only inference speed tips",
        "{tool} num_thread num_ctx performance tuning",
    ],
}

DEFAULT_QUERIES = [
    "{tool} getting started official docs",
    "{tool} install quickstart tutorial",
    "{tool} vs {alternative}",
    "{tool} vs {alternative} pros cons",
    "{tool} common errors site:stackoverflow.com",
    "{tool} site:github.com",
    "{tool} minimum requirements hardware",
    "{tool} best practices production",
]

DEFAULT_SKIP_DOMAINS = {
    "youtube.com", "youtu.be", "m.youtube.com",
    "twitter.com", "x.com", "t.co",
    "facebook.com", "fb.com",
    "instagram.com", "threads.net",
    "tiktok.com",
    "pinterest.com",
    "reddit.com/gallery",
    "linkedin.com",
    "twitch.tv", "vimeo.com", "dailymotion.com",
    "kwai.com", "kuaishou.com", "snapchat.com",
    "imgur.com", "giphy.com",
}

NON_TEXT_PATH_MARKERS = (
    "/shorts/",
    "/reel/",
    "/reels/",
    "/video/",
    "/videos/",
    "/watch",
    "/live/",
    "/clip/",
)

NON_TEXT_EXTENSIONS = (
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
)

LOW_SIGNAL_DOMAINS = {
    "databasemart.com",
    "aitooldiscovery.com",
    "toolify.ai",
    "g2.com",
    "saashub.com",
    "news.ycombinator.com",
    "slashdot.org",
    "scribd.com",
    "udemy.com",
    "sourceforge.net",
    "stackshare.io",
    "openalternative.co",
    "userbenchmark.com",
    "userbenchmark.org",
    "humanbenchmark.com",
    "dedicatedcore.com",
    "getorchestra.io",
    "readmedium.com",
    "github-wiki-see.page",
    "explore.market.dev",
    "explaintopic.com",
    "news.lavx.hu",
    "news.smol.ai",
    "cccok.cn",
    "toolhalla.ai",
    "arsturn.com",
    "vmme.org",
    "techbyjz.blog",
    "markaicode.com",
    "fastlaunchapi.dev",
    "codezup.com",
    "johal.in",
}

LOW_SIGNAL_PATH_MARKERS = (
    "/software/compare/",
    "/compare/",
)

TRUSTED_TECH_DOMAINS = {
    "github.com",
    "docs.ollama.com",
    "docs.docker.com",
    "docs.podman.io",
    "docs.pola.rs",
    "kubernetes.io",
}

HIGH_TRUST_DOMAIN_HINTS = (
    "docs.",
    "developer.",
    "developers.",
)

MEDIUM_TRUST_DOMAINS = {
    "medium.com",
    "dev.to",
    "substack.com",
    "readthedocs.io",
    "deepwiki.com",
}

TECH_EVIDENCE_TERMS = (
    "benchmark",
    "throughput",
    "latency",
    "error",
    "issue",
    "troubleshoot",
    "troubleshooting",
    "install",
    "quickstart",
    "docs",
    "reference",
    "api",
    "config",
    "flag",
    "command",
    "docker",
    "kubernetes",
    "memory",
    "ram",
    "cpu",
    "vram",
    "quantization",
)

QNA_DOMAINS = {
    "stackoverflow.com",
    "superuser.com",
    "serverfault.com",
}

GENERIC_KEYWORD_TERMS = {
    "tool",
    "tools",
    "stack",
    "error",
    "errors",
    "issue",
    "issues",
    "guide",
    "tutorial",
    "docs",
    "official",
    "alternative",
    "alternatives",
}

QUESTION_STOPWORDS = {
    "a",
    "as",
    "o",
    "os",
    "de",
    "da",
    "das",
    "do",
    "dos",
    "e",
    "em",
    "para",
    "por",
    "com",
    "sem",
    "que",
    "como",
    "quando",
    "qual",
    "quais",
    "no",
    "na",
    "nos",
    "nas",
    "um",
    "uma",
    "ou",
    "ao",
    "aos",
    "nao",
    "não",
}

TOOL_IDENTITY_STOPWORDS = {
    "core",
}

PERFORMANCE_INTENT_TERMS = {
    "benchmark",
    "benchmarks",
    "latencia",
    "latência",
    "throughput",
    "rps",
    "qps",
    "p50",
    "p95",
    "p99",
    "cpu",
    "ram",
    "vram",
    "memoria",
    "memória",
}

INTEGRATION_INTENT_TERMS = {
    "integracao",
    "integração",
    "arquitetura",
    "pipeline",
    "fluxo",
    "connector",
}

SECURITY_INTENT_TERMS = {
    "seguranca",
    "segurança",
    "auth",
    "autenticacao",
    "autenticação",
    "rbac",
    "tls",
    "ssl",
    "cve",
    "vulnerabilidade",
}

MAX_SCRAPES_PER_TOOL = 10
MAX_CHARS_PER_SCRAPE = 4000


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
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self.llm = LLMClient(spec_path)
        self.model = self.llm.model_for_role("researcher")
        self.pipeline_logger = pipeline_logger
        self.event_log = pipeline_logger.event_log if pipeline_logger else EventLog()
        self.last_scrape_stats = {"ok": 0, "fail": 0, "skipped": 0}
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
        self.temp = temperatures["researcher"]
        self.timeout = timeouts.get("researcher", timeouts.get("default", 300))

    def log_url_found(
        self,
        url: str,
        title: str = "",
        status: str = "",
        elapsed: float | None = None,
        source: str = "",
        scrape_status: str = "",
    ):
        if self.pipeline_logger:
            self.pipeline_logger.found_url(
                url,
                title=title,
                status=status,
                elapsed=elapsed,
                source=source,
                scrape_status=scrape_status,
            )
            return
        self.event_log.log_event("url_found", {
            "url": url,
            "title": title,
            "status": status,
            "elapsed_seconds": elapsed,
            "source": source,
            "scrape_status": scrape_status,
        })

    def run(
        self,
        tool,
        alternative="",
        foco="comparação geral",
        questoes=None,
        refresh_search: bool = False,
        targeted_questions_only: bool = False,
    ):
        """Execute research pipeline for a tool.
        
        Builds search queries, scrapes URLs, learns from memory, calls LLM researcher,
        and logs event with stats.
        
        Args:
            tool: Tool/technology to research (e.g., "DuckDB")
            alternative: Alternative tool for comparison (e.g., "Polars")
            foco: Research focus from FOCUS_QUERIES keys
            questoes: Optional list of custom questions to include
            
        Returns:
            LLM-generated research report as string
            
        Example:
            researcher = ResearcherSkill(search_tool, scraper, memory)
            report = researcher.run(
                "DuckDB", 
                alternative="Polars",
                foco="comparação geral",
                questoes=["streaming support?", "GPU acceleration?"]
            )
        """
        questoes = questoes or []
        logger.debug(f"Starting research for tool: {tool}, foco: {foco}")
        
        queries = self.build_queries(
            tool=tool,
            alternative=alternative,
            foco=foco,
            questoes=questoes,
            targeted_questions_only=targeted_questions_only,
        )
        logger.debug(f"Built {len(queries)} search queries")

        results_by_query = self.search.search_multi(queries, force_refresh=refresh_search)
        logger.debug(f"Got search results for {len(results_by_query)} queries")

        filtered_results_by_query = self.filter_search_results(
            results_by_query=results_by_query,
            tool=tool,
            alternative=alternative,
        )
        filtered_out_count = self.count_results(results_by_query) - self.count_results(filtered_results_by_query)
        if filtered_out_count > 0:
            logger.info(
                "Search guardrail filtered %d URL(s) for non-relevant/video/social domains",
                filtered_out_count,
            )

        self.search.save_urls(filtered_results_by_query, f"output/urls_{tool}.txt")

        context = self.build_context(filtered_results_by_query)
        logger.debug(f"Context built: {len(context)} chars, scrape_stats: {self.last_scrape_stats}")
        
        lessons = self.memory.get_lessons_for_prompt()
        if lessons:
            logger.debug(f"Using learned lessons from memory")

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {question}" for question in questoes)
            questoes_block = f"\nBusque dados específicos para responder:\n{lista}\n"
            logger.debug(f"Added {len(questoes)} custom questions to prompt")

        prompt = f"""Você é um pesquisador técnico. Analise os dados abaixo sobre {tool}.
Foco desta pesquisa: {foco}
{questoes_block}
{lessons}

DADOS DA BUSCA:
{context}

REGRAS CRÍTICAS:
- Extraia APENAS o que está nos dados acima
- Se um dado NÃO aparece nos resultados, OMITA a linha inteira
- NUNCA escreva "NÃO ENCONTRADO", "DADO AUSENTE", "N/A" ou qualquer placeholder
- Se uma seção inteira não tem dados, escreva: "Sem dados nos resultados para esta seção."
- NUNCA invente números, versões ou comandos
- Copie comandos EXATOS dos snippets
- URLs marcadas como SCRAPE_FALHOU têm apenas o snippet do buscador — dados rasos

Produza o relatório:

## URLS CONSULTADAS
[liste APENAS URLs que começam com https://]

## REQUISITOS DE HARDWARE
[Se encontrou valores concretos, liste-os. Senão, explique brevemente
 por que não existem requisitos oficiais se os dados sugerirem isso,
 ou omita esta seção.]

## COMANDOS DE INSTALAÇÃO
[comandos exatos dos snippets em blocos ```bash]

## ERROS COMUNS
[erros encontrados nos resultados com causa e solução]

## DADOS RELEVANTES PARA: {foco}
[informações específicas sobre o foco]

## ALTERNATIVAS MENCIONADAS
[ferramentas comparadas nos resultados]
"""
        logger.debug(f"Calling LLM researcher (timeout: {self.timeout}s, temp: {self.temp})")
        resp = self.llm.generate(
            role="researcher",
            model=self.model,
            prompt=prompt,
            temperature=self.temp,
            timeout=self.timeout,
        )
        logger.debug(f"LLM response received: {len(resp.response)} chars")

        self.memory.log_event("research_done", {
            "tool": tool,
            "foco": foco,
            "queries": queries,
            "scrape_stats": self.last_scrape_stats,
        })
        return resp.response

    def build_queries(
        self,
        tool,
        alternative,
        foco,
        questoes,
        targeted_questions_only: bool = False,
    ):
        """Build list of search queries from FOCUS_QUERIES templates.
        
        Substitutes {tool} and {alternative} placeholders and appends custom questions.
        
        Args:
            tool: Tool name to substitute
            alternative: Alternative tool name
            foco: Focus key to lookup FOCUS_QUERIES
            questoes: Custom questions to append (max 4)
            
        Returns:
            List of formatted query strings
            
        Example:
            queries = researcher.build_queries("DuckDB", "Polars", "comparação geral", [])
            # Returns ~10-14 queries about DuckDB vs Polars
        """
        if targeted_questions_only and questoes:
            return [
                self.build_question_query(
                    tool=tool,
                    alternative=alternative,
                    question=question,
                    focus=foco,
                )
                for question in questoes[:6]
            ]

        templates = FOCUS_QUERIES.get(foco, DEFAULT_QUERIES)
        alt = alternative or "alternatives"
        queries = [
            query_template.replace("{tool}", tool).replace("{alternative}", alt)
            for query_template in templates
        ]
        for question in questoes[:4]:
            queries.append(
                self.build_question_query(
                    tool=tool,
                    alternative=alternative,
                    question=question,
                    focus=foco,
                )
            )
        return queries

    def build_question_query(
        self,
        tool: str,
        alternative: str,
        question: str,
        focus: str,
    ) -> str:
        normalized_question = (question or "").lower().strip()
        question_terms = [
            term
            for term in re.split(r"[^a-zA-Z0-9]+", normalized_question)
            if len(term) >= 3 and term not in QUESTION_STOPWORDS and term not in GENERIC_KEYWORD_TERMS
        ]
        compact_terms = " ".join(question_terms[:8]).strip()
        scope_terms = [tool]
        if alternative and any(
            marker in normalized_question
            for marker in ("integr", "junto", "combinar", "ambos", "dois")
        ):
            scope_terms.append(alternative)

        base_query = " ".join(scope_terms + ([compact_terms] if compact_terms else [normalized_question]))

        if self.has_intent_term(normalized_question, PERFORMANCE_INTENT_TERMS):
            return f"{base_query} benchmark latency throughput"
        if self.has_intent_term(normalized_question, INTEGRATION_INTENT_TERMS):
            return f"{base_query} integration architecture example"
        if self.has_intent_term(normalized_question, SECURITY_INTENT_TERMS):
            return f"{base_query} security hardening best practices"
        focus_lower = (focus or "").lower()
        if (
            ("performance" in focus_lower or "throughput" in focus_lower)
            and self.has_intent_term(base_query, PERFORMANCE_INTENT_TERMS)
        ):
            return f"{base_query} benchmark latency throughput"
        if "integra" in focus_lower and self.has_intent_term(base_query, INTEGRATION_INTENT_TERMS):
            return f"{base_query} integration architecture example"
        return base_query.strip()

    def has_intent_term(self, text: str, terms: set[str]) -> bool:
        normalized_text = (text or "").lower()
        return any(intent_term in normalized_text for intent_term in terms)

    def build_context(self, results_by_query):
        """Scrape URLs and build context string for LLM analysis.
        
        Extracts text from URLs, skips non-useful domains, tracks scraping stats,
        and logs events to PipelineLogger for real-time monitoring.
        
        Max 10 URLs scraped per tool; uses search snippets as fallback if scrape fails.
        Each URL limited to 4000 chars.
        
        Args:
            results_by_query: Dict from search_tool.search_multi() with format:
                {query: [{"url": "...", "snippet": "...", ...}, ...]}
                
        Returns:
            Multi-line context string with scraped content, ready for LLM prompt
            
        Sets self.last_scrape_stats dict with {ok, fail, skipped} counts
            
        Example:
            context = researcher.build_context(search_results)
            # Returns formatted context with real-time event logging
        """
        import time as time_module
        
        lines = []
        seen_urls: set[str] = set()
        scrape_ok = 0
        scrape_fail = 0
        total_scrapes = 0
        for query, results in results_by_query.items():
            lines.append(f"\n### Busca: {query}")

            for result_item in results:
                url = result_item.get("url", "")
                if not url.startswith("http") or url in seen_urls:
                    continue
                if self.should_skip_url(url):
                    self.log_url_found(url, status="skipped")
                    continue
                seen_urls.add(url)

                if total_scrapes >= MAX_SCRAPES_PER_TOOL:
                    lines.append(f"URL: {url}")
                    lines.append(f"Resumo: {result_item.get('snippet', '')}")
                    lines.append("---")
                    title = result_item.get('snippet', '')[:40]
                    self.log_url_found(url, title=title, status="ok")
                    continue

                total_scrapes += 1
                
                scrape_start = time_module.time()
                result = self.scraper.extract_text(url)
                scrape_elapsed = time_module.time() - scrape_start

                if result["status"] == "ok":
                    scrape_ok += 1
                    text = result["text"][:MAX_CHARS_PER_SCRAPE]
                    tag = " [TRUNCADO]" if result.get("truncated") else ""
                    lines.append(f"URL: {url}{tag}")
                    lines.append(f"Conteúdo Extraído:\n{text}")
                    lines.append("---")
                    title = text.split('\n')[0][:40] if text else ""
                    self.log_url_found(
                        url,
                        title=title,
                        status="ok",
                        elapsed=scrape_elapsed,
                        source=result.get("source", ""),
                        scrape_status=result.get("status", ""),
                    )
                else:
                    scrape_fail += 1
                    self.memory.log_event("scrape_failed", {
                        "url": url, "status": result["status"],
                        "elapsed_seconds": scrape_elapsed
                    })
                    snippet = result_item.get("snippet", "")
                    if snippet:
                        lines.append(f"URL: {url} [SCRAPE_FALHOU: {result['status']}]")
                        lines.append(f"Resumo (fallback): {snippet}")
                        lines.append("---")
                    self.log_url_found(
                        url,
                        title=f"[{result['status']}]",
                        status="scrape_failed",
                        elapsed=scrape_elapsed,
                        source=result.get("source", ""),
                        scrape_status=result.get("status", ""),
                    )

        self.last_scrape_stats = {
            "ok": scrape_ok,
            "fail": scrape_fail,
            "skipped": len(seen_urls) - total_scrapes,
        }
        return "\n".join(lines)

    def filter_search_results(
        self,
        results_by_query: dict[str, list[dict]],
        tool: str,
        alternative: str,
    ) -> dict[str, list[dict]]:
        relevance_keywords = self.build_relevance_keywords(tool, alternative)
        tool_identity_terms = self.build_tool_identity_terms(tool, alternative)
        filtered_results_by_query: dict[str, list[dict]] = {}
        for query, results in results_by_query.items():
            scored_results = []
            for result_item in results:
                url = result_item.get("url", "")
                if self.should_skip_url(url):
                    continue
                if not self.is_result_relevant(
                    result_item=result_item,
                    relevance_keywords=relevance_keywords,
                    tool_identity_terms=tool_identity_terms,
                ):
                    continue
                source_score = self.compute_source_score(
                    result_item=result_item,
                    relevance_keywords=relevance_keywords,
                    tool_identity_terms=tool_identity_terms,
                )
                if source_score < self.source_min_score_keep:
                    continue
                scored_results.append((source_score, result_item))

            scored_results.sort(key=lambda score_and_result: score_and_result[0], reverse=True)
            filtered_results_by_query[query] = [
                result_item
                for source_score, result_item in scored_results[: self.source_max_results_per_query]
            ]
        return filtered_results_by_query

    def build_relevance_keywords(self, tool: str, alternative: str) -> set[str]:
        raw_terms = [tool or "", alternative or ""]
        split_terms = []
        for term in raw_terms:
            split_terms.extend(re.split(r"[^a-zA-Z0-9]+", term.lower()))
        return {
            term
            for term in split_terms
            if len(term) >= 3 and term not in GENERIC_KEYWORD_TERMS
        }

    def build_tool_identity_terms(self, tool: str, alternative: str) -> set[str]:
        raw_terms = [(tool or "").lower().strip(), (alternative or "").lower().strip()]
        tool_terms: set[str] = set()
        for raw_term in raw_terms:
            if raw_term:
                tool_terms.add(raw_term)
            split_terms = re.split(r"[^a-zA-Z0-9]+", raw_term)
            tool_terms.update(
                term
                for term in split_terms
                if len(term) >= 3
                and term not in GENERIC_KEYWORD_TERMS
                and term not in TOOL_IDENTITY_STOPWORDS
            )
        return {term for term in tool_terms if term}

    def is_result_relevant(
        self,
        result_item: dict,
        relevance_keywords: set[str],
        tool_identity_terms: set[str],
    ) -> bool:
        url = (result_item.get("url", "") or "").lower()
        parsed_url = urlparse(url)
        host = parsed_url.netloc
        title = (result_item.get("title", "") or "").lower()
        snippet = (result_item.get("snippet", "") or "").lower()
        combined_text = f"{url} {title} {snippet}"
        if not self.has_required_tool_anchor(combined_text, tool_identity_terms):
            return False

        if self.is_qna_host(host):
            return self.has_tool_identity_match(combined_text, tool_identity_terms)

        if any(
            host == trusted_domain or host.endswith(f".{trusted_domain}")
            for trusted_domain in TRUSTED_TECH_DOMAINS
        ):
            return self.has_tool_identity_match(combined_text, tool_identity_terms)

        if not relevance_keywords:
            return self.has_tool_identity_match(combined_text, tool_identity_terms)

        return any(keyword in combined_text for keyword in relevance_keywords)

    def compute_source_score(
        self,
        result_item: dict,
        relevance_keywords: set[str],
        tool_identity_terms: set[str],
    ) -> int:
        url = (result_item.get("url", "") or "").lower()
        title = (result_item.get("title", "") or "").lower()
        snippet = (result_item.get("snippet", "") or "").lower()
        combined_text = f"{url} {title} {snippet}"
        parsed_url = urlparse(url)
        host = parsed_url.netloc

        source_score = 0

        if self.is_high_trust_host(host):
            source_score += 5
        elif self.is_medium_trust_host(host):
            source_score += 2
        elif self.is_qna_host(host):
            source_score += 1

        keyword_matches = sum(1 for keyword in relevance_keywords if keyword in combined_text)
        source_score += min(3, keyword_matches)

        if self.has_tool_identity_match(combined_text, tool_identity_terms):
            source_score += 3

        evidence_matches = sum(1 for term in TECH_EVIDENCE_TERMS if term in combined_text)
        source_score += min(3, evidence_matches)

        if self.is_low_signal_host(host):
            source_score -= 4
        if "sponsored" in combined_text or "affiliate" in combined_text:
            source_score -= 2

        return source_score

    def is_high_trust_host(self, host: str) -> bool:
        if any(
            host == trusted_domain or host.endswith(f".{trusted_domain}")
            for trusted_domain in TRUSTED_TECH_DOMAINS
        ):
            return True
        if any(host.startswith(prefix) for prefix in HIGH_TRUST_DOMAIN_HINTS):
            return True
        return False

    def is_medium_trust_host(self, host: str) -> bool:
        return any(
            host == medium_domain or host.endswith(f".{medium_domain}")
            for medium_domain in MEDIUM_TRUST_DOMAINS
        )

    def is_qna_host(self, host: str) -> bool:
        return any(host == qna_domain or host.endswith(f".{qna_domain}") for qna_domain in QNA_DOMAINS)

    def has_tool_identity_match(self, combined_text: str, tool_identity_terms: set[str]) -> bool:
        if not tool_identity_terms:
            return False
        return any(tool_term in combined_text for tool_term in tool_identity_terms)

    def has_required_tool_anchor(self, combined_text: str, tool_identity_terms: set[str]) -> bool:
        requires_dbt_anchor = "dbt" in tool_identity_terms or "sqlmesh" in tool_identity_terms
        if not requires_dbt_anchor:
            return True
        required_anchors = ("dbt", "dbt-core", "sqlmesh")
        return any(required_anchor in combined_text for required_anchor in required_anchors)

    def is_low_signal_host(self, host: str) -> bool:
        return any(
            host == low_signal_domain or host.endswith(f".{low_signal_domain}")
            for low_signal_domain in LOW_SIGNAL_DOMAINS
        )

    def should_skip_url(self, url: str) -> bool:
        if not url or not url.startswith("http"):
            return True

        parsed_url = urlparse(url.lower())
        host = parsed_url.netloc
        path = parsed_url.path or ""
        query = parsed_url.query or ""

        if any(
            host == blocked_domain or host.endswith(f".{blocked_domain}")
            for blocked_domain in self.skip_domains
        ):
            return True

        if any(path.endswith(extension) for extension in NON_TEXT_EXTENSIONS):
            return True

        if any(marker in path for marker in NON_TEXT_PATH_MARKERS):
            return True

        if self.is_low_signal_host(host):
            return True

        if any(marker in path for marker in LOW_SIGNAL_PATH_MARKERS):
            return True

        if host.endswith("github.com") and path.startswith("/topics/"):
            return True
        if host.endswith("stackoverflow.com") and "/questions/tagged/" in path:
            return True
        if host.endswith("stackoverflow.com") and path.startswith("/tags/"):
            return True
        if "trk=" in query:
            return True

        return False

    def count_results(self, results_by_query: dict[str, list[dict]]) -> int:
        return sum(len(results) for results in results_by_query.values())
