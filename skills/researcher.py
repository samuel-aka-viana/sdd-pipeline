import asyncio

import yaml
import logging
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm import LLMClient
from logger import EventLog

try:
    from memory.research_chroma import ResearchChroma
    HAS_CHROMA = True
except ImportError:
    HAS_CHROMA = False

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
        self.chroma = ResearchChroma() if HAS_CHROMA else None
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
        # Store scraped URLs for re-analysis (e.g., when looking for tips/errors)
        self._scraped_urls = {}
        # Track URL richness (has tips, errors, commands, etc.)
        self._url_richness = {}

    def _infer_source_quality(self, url: str) -> str:
        """Infer source quality level for FTS metadata."""
        domain = urlparse(url).netloc.lower()

        if any(domain.endswith(trusted) for trusted in TRUSTED_TECH_DOMAINS):
            return "official"

        if any(hint in domain for hint in HIGH_TRUST_DOMAIN_HINTS):
            return "trusted"

        if domain in MEDIUM_TRUST_DOMAINS:
            return "medium"

        if domain in QNA_DOMAINS:
            return "medium"

        return "unknown"

    def extract_section_structure(self, url: str, markdown_content: str) -> dict:
        """Analyze markdown structure to detect rich content (tips, errors, commands, benchmarks).

        Uses header hierarchy from Crawl4AI's structured markdown to classify content.
        Enables smart prioritization: URLs with many tips get analyzed first when
        critic says "Dicas insuficientes".
        """
        sections = {
            "tips": [],
            "errors": [],
            "commands": [],
            "benchmarks": [],
            "warnings": [],
            "has_table": False,
        }

        if not markdown_content:
            return sections

        # Find all headers (preserves Crawl4AI structure)
        headers = re.findall(r'^#+\s+(.+)$', markdown_content, re.MULTILINE)

        for header in headers:
            header_lower = header.lower()
            if any(word in header_lower for word in ["dica", "tip", "otimiza", "optimization"]):
                sections["tips"].append(header)
            elif any(word in header_lower for word in ["erro", "error", "problema", "pitfall"]):
                sections["errors"].append(header)
            elif any(word in header_lower for word in ["command", "instala", "install", "bash"]):
                sections["commands"].append(header)
            elif any(word in header_lower for word in ["benchmark", "performance", "throughput", "latency"]):
                sections["benchmarks"].append(header)
            elif any(word in header_lower for word in ["warning", "⚠", "cuidado", "aviso"]):
                sections["warnings"].append(header)

        # Check for tables (another indicator of structured content)
        sections["has_table"] = bool(re.search(r'\|.*\|', markdown_content))

        return sections

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
        urls: list[str] | None = None,
        skip_search: bool = False,
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

        # NEW: Skip web search if URLs provided
        if skip_search and urls:
            logger.info(f"⏭️  Skipping web search - using {len(urls)} provided URLs")
            # Convert bare URLs to result dicts with {url, title, snippet}
            url_results = [
                {"url": url.strip(), "title": url.strip()[:50], "snippet": ""}
                for url in urls
                if url.strip()
            ]
            results_by_query = {"provided_urls": url_results}
            self.memory.log_event("search_skipped", {
                "tool": tool,
                "urls_provided": len(url_results),
            })
        else:
            results_by_query = self.search.search_multi(queries, force_refresh=refresh_search)
            logger.debug(f"Got search results for {len(results_by_query)} queries")

        # LOG WEAK QUERIES: Log to Chroma event tracking
        for query, results in results_by_query.items():
            results_count = len(results) if results else 0
            if results_count < 3:
                logger.info(f"⚠️  Weak query results ({results_count}): {query}")
                self.memory.log_event("weak_search_query", {
                    "tool": tool,
                    "query": query,
                    "results_count": results_count,
                })

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

        context = self.build_context(filtered_results_by_query, tool=tool)
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
            "queries": len(queries),
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

    def build_context(self, results_by_query, tool: str = "unknown"):
        """Scrape URLs and build context string for LLM analysis.

        Uses parallel scraping (3 workers) instead of serial.
        Extracts text from URLs, skips non-useful domains, tracks scraping stats.

        Max 10 URLs scraped per tool; uses search snippets as fallback if scrape fails.
        Each URL limited to 4000 chars.

        Args:
            results_by_query: Dict from search_tool.search_multi()

        Returns:
            Multi-line context string with scraped content, ready for LLM prompt
        """
        import time as time_module

        lines = []
        seen_urls: set[str] = set()
        urls_to_scrape = []

        # PHASE 1: Collect URLs to scrape (filter + deduplicate)
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

                if len(urls_to_scrape) < MAX_SCRAPES_PER_TOOL:
                    urls_to_scrape.append((url, result_item))
                else:
                    # Limit reached: use snippet as fallback
                    lines.append(f"URL: {url}")
                    lines.append(f"Resumo: {result_item.get('snippet', '')}")
                    lines.append("---")
                    title = result_item.get('snippet', '')[:40]
                    self.log_url_found(url, title=title, status="ok")

        # PHASE 2: Parallel scraping (3 workers)
        scraped_results = self._scrape_urls_parallel(urls_to_scrape, tool)

        # PHASE 3: Build context from scraped results
        for url, result, result_item in scraped_results:
            if result["status"] == "ok":
                text = result["text"][:MAX_CHARS_PER_SCRAPE]
                tag = " [TRUNCADO]" if result.get("truncated") else ""
                lines.append(f"URL: {url}{tag}")
                lines.append(f"Conteúdo Extraído:\n{text}")
                lines.append("---")
                title = text.split('\n')[0][:40] if text else ""

                # Store for re-analysis
                self._scraped_urls[url] = result["text"]

                # Extract markdown structure from Crawl4AI result
                markdown_raw = result.get("markdown", "")
                if not markdown_raw and result.get("source") == "crawl4ai":
                    # Fallback: use text as markdown if not explicitly provided
                    markdown_raw = result["text"]

                # Analyze markdown structure to detect rich content
                structure = self.extract_section_structure(url, markdown_raw)
                self._url_richness[url] = structure

                # PERSIST to Chroma (primary) with intelligent chunking
                if self.chroma:
                    content_text = result.get("text", "")
                    if content_text:
                        # Log RAW CONTENT preview BEFORE saving (for debugging)
                        content_preview = content_text[:200]
                        self.memory.log_event("scraped_content_preview", {
                            "tool": tool,
                            "url": url[:60],
                            "preview": content_preview,
                            "total_chars": len(content_text),
                        })

                        success = self.chroma.save_scraped_content(
                            tool=tool,
                            url=url,
                            title=title,
                            content=content_text,
                            markdown_raw=markdown_raw,
                            source_quality=self._infer_source_quality(url),
                            scrape_elapsed_seconds=result.get("elapsed", 0),
                        )
                        # Log Chroma persistence event (only if successful)
                        if success:
                            chunks_count = len(self.chroma.chunk_content(content_text))
                            self.memory.log_event("chroma_save", {
                                "tool": tool,
                                "url": url,
                                "content_chars": len(content_text),
                                "chunk_count": chunks_count,
                                "source_quality": self._infer_source_quality(url),
                            })
                        else:
                            logger.warning(f"Failed to save to Chroma: {url[:60]}")

                # Log content preview BEFORE anything
                content_text = result.get("text", "")
                preview = content_text[:100].replace("\n", " ")[:80] if content_text else "[VAZIO]"
                self.memory.log_event("content_extracted", {
                    "url": url[:60],
                    "status": "ok" if content_text else "empty",
                    "preview": preview,
                    "chars": len(content_text),
                })

                self.log_url_found(
                    url, title=title, status="ok",
                    elapsed=result.get("elapsed", 0),
                    source=result.get("source", ""),
                )
            else:
                # Scrape failed: log the error clearly
                error_msg = result.get("status", "unknown_error")
                self.memory.log_event("content_extraction_failed", {
                    "url": url[:60],
                    "error": error_msg,
                    "elapsed": result.get("elapsed", 0),
                })

                # Scrape failed: use snippet
                snippet = result_item.get("snippet", "")
                if snippet:
                    lines.append(f"URL: {url} [SCRAPE_FALHOU: {result['status']}]")
                    lines.append(f"Resumo (fallback): {snippet}")
                    lines.append("---")
                    self._scraped_urls[url] = snippet

                self.log_url_found(
                    url,
                    title=f"[{result['status']}]",
                    status="scrape_failed",
                    elapsed=result.get("elapsed", 0),
                )

        scrape_ok = sum(1 for r in scraped_results if r[1]["status"] == "ok")
        scrape_fail = sum(1 for r in scraped_results if r[1]["status"] != "ok")

        self.last_scrape_stats = {
            "ok": scrape_ok,
            "fail": scrape_fail,
            "skipped": len(seen_urls) - len(urls_to_scrape),
        }
        return "\n".join(lines)

    def _scrape_urls_parallel(self, urls_to_scrape: list[tuple], tool: str) -> list[tuple]:
        """Scrape URLs in parallel using 3 worker threads.

        Args:
            urls_to_scrape: List of (url, result_item) tuples
            tool: Tool name for logging

        Returns:
            List of (url, result, result_item) tuples
        """
        import time as time_module

        def scrape_single_url(url: str, result_item: dict) -> tuple:
            scrape_start = time_module.time()
            result = self.scraper.extract_text(url)
            scrape_elapsed = time_module.time() - scrape_start
            result["elapsed"] = scrape_elapsed
            return (url, result, result_item)

        scraped_results = []
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {
                pool.submit(scrape_single_url, url, result_item): (url, result_item)
                for url, result_item in urls_to_scrape
            }

            for future in futures:
                try:
                    result_tuple = future.result()
                    scraped_results.append(result_tuple)
                except Exception as e:
                    url, result_item = futures[future]
                    logger.warning(f"Parallel scrape failed for {url}: {e}")
                    scraped_results.append((url, {"status": "error", "elapsed": 0}, result_item))

        # For large batches (10+ URLs), try async batching for speed
        if len(urls_to_scrape) >= 10:
            try:
                return self._scrape_urls_batch_async(urls_to_scrape)
            except Exception as e:
                logger.warning(f"Async batch scraping failed, using threaded fallback: {e}")

        return scraped_results

    def _scrape_urls_batch_async(self, urls_to_scrape: list[tuple]) -> list[tuple]:
        """Scrape 10+ URLs using async batching (much faster than threading).

        For 30 URLs: 15s (threaded) → 5-7s (async batch).
        Uses Crawl4AI's native async capabilities.
        """
        import asyncio
        import time as time_module

        async def batch_scrape():
            from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

            config = CrawlerRunConfig(
                wait_until="domcontentloaded",
            )

            scraped_results = []

            async with AsyncWebCrawler(always_by_pass_cache=False) as crawler:
                # Create tasks for all URLs in parallel
                tasks = []
                for url, result_item in urls_to_scrape:
                    task = self._async_crawl_task(crawler, url, result_item, config)
                    tasks.append(task)

                # Wait for all to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        logger.debug(f"Async batch scrape error: {result}")
                        continue
                    scraped_results.append(result)

            return scraped_results

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(batch_scrape())
        finally:
            loop.close()

    async def _async_crawl_task(self, crawler, url: str, result_item: dict, config):
        """Single async crawl task with timing."""
        import time as time_module

        scrape_start = time_module.time()
        try:
            result = await crawler.arun(url=url, config=config)
            scrape_elapsed = time_module.time() - scrape_start

            if result.status_code != 200:
                return (
                    url,
                    {
                        "status": f"http_{result.status_code}",
                        "text": "",
                        "truncated": False,
                        "url": url,
                        "source": "crawl4ai",
                        "elapsed": scrape_elapsed,
                    },
                    result_item,
                )

            text = result.markdown_v2.raw_markdown if result.markdown_v2 else ""
            markdown = text

            if not text and result.html:
                try:
                    from trafilatura import extract as traf_extract
                    text = traf_extract(
                        result.html,
                        include_links=False,
                        include_images=False,
                        output_format="markdown",
                    )
                except Exception:
                    text = result.html[:1000]

            if not text:
                return (
                    url,
                    {
                        "status": "parse_error",
                        "text": "",
                        "truncated": False,
                        "url": url,
                        "source": "crawl4ai",
                        "elapsed": scrape_elapsed,
                    },
                    result_item,
                )

            truncated = len(text) > MAX_CHARS_PER_SCRAPE
            text = text[:MAX_CHARS_PER_SCRAPE]

            return (
                url,
                {
                    "status": "ok",
                    "text": text,
                    "markdown": markdown,
                    "truncated": truncated,
                    "url": url,
                    "source": "crawl4ai",
                    "elapsed": scrape_elapsed,
                },
                result_item,
            )

        except asyncio.TimeoutError:
            return (
                url,
                {
                    "status": "timeout",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                    "elapsed": time_module.time() - scrape_start,
                },
                result_item,
            )
        except Exception as e:
            logger.debug(f"Async crawl failed for {url}: {e}")
            return (
                url,
                {
                    "status": "crawl4ai_error",
                    "text": "",
                    "truncated": False,
                    "url": url,
                    "source": "crawl4ai",
                    "elapsed": time_module.time() - scrape_start,
                },
                result_item,
            )

    def reanalyze_urls_for_tips_and_errors(self, tool: str, focus_on: str = "tips_and_errors") -> str:
        """Re-analyze already-scraped content to extract tips and errors.

        When critic finds "Dicas insuficientes" or "Poucos erros documentados",
        instead of re-searching, use Chroma to find relevant chunks semantically.

        Args:
            tool: Tool name
            focus_on: "tips_and_errors" (default), "tips_only", or "errors_only"

        Returns:
            Structured text with tips and errors found
        """
        if not self.chroma and not self._scraped_urls:
            return "Nenhuma URL foi scrapada para re-análise."

        # Priority 1: Semantic search in Chroma for tips/errors
        context_lines = []

        if self.chroma:
            # Search semantically for tips and errors
            if focus_on != "errors_only":
                tips_query = f"{tool} dicas otimização tips best practices"
                tips_results = self.chroma.query_similar(
                    tips_query,
                    tool=tool,
                    k=5,
                    distance_threshold=0.25,
                )
                self.memory.log_event("chroma_query", {
                    "tool": tool,
                    "query": tips_query,
                    "results_count": len(tips_results),
                    "query_type": "tips",
                })
                for result in tips_results:
                    context_lines.append(f"URL: {result['url']}")
                    context_lines.append(result["text"][:1000])
                    context_lines.append(f"(Similaridade: {result['similarity']:.2f})")
                    context_lines.append("---")

            if focus_on != "tips_only":
                error_query = f"{tool} erros problemas errors troubleshooting solução"
                error_results = self.chroma.query_similar(
                    error_query,
                    tool=tool,
                    k=5,
                    distance_threshold=0.25,
                )
                self.memory.log_event("chroma_query", {
                    "tool": tool,
                    "query": error_query,
                    "results_count": len(error_results),
                    "query_type": "errors",
                })
                for result in error_results:
                    context_lines.append(f"URL: {result['url']}")
                    context_lines.append(result["text"][:1000])
                    context_lines.append(f"(Similaridade: {result['similarity']:.2f})")
                    context_lines.append("---")
        else:
            # Fallback: use local scraped URLs if Chroma not available
            for url, content in list(self._scraped_urls.items())[:5]:
                context_lines.append(f"URL: {url}")
                context_lines.append(content[:1000])
                context_lines.append("---")

        context = "\n".join(context_lines)

        # Tailor prompt based on focus
        if focus_on == "tips_only":
            task = """TAREFA:
1. Identifique PELO MENOS 3 dicas práticas (otimizações, best practices, configurações)
2. Use APENAS o que está escrito no conteúdo acima

FORMATO:
## Dicas Encontradas
- [Dica 1 com comando real ou configuração]
- [Dica 2]
- [Dica 3]"""
        elif focus_on == "errors_only":
            task = """TAREFA:
1. Identifique PELO MENOS 2 erros comuns com soluções
2. Use APENAS o que está escrito no conteúdo acima

FORMATO:
## Erros Comuns
- **Erro 1**: [descrição] → **Solução**: [passo]
- **Erro 2**: [descrição] → **Solução**: [passo]"""
        else:  # tips_and_errors
            task = """TAREFA:
1. Identifique PELO MENOS 3 dicas práticas (otimizações, best practices, configurações)
2. Identifique PELO MENOS 2 erros comuns com soluções
3. Use APENAS o que está escrito no conteúdo acima

FORMATO:
## Dicas Encontradas
- [Dica 1 com comando real ou configuração]
- [Dica 2]
- [Dica 3]

## Erros Comuns
- **Erro 1**: [descrição] → **Solução**: [passo]
- **Erro 2**: [descrição] → **Solução**: [passo]"""

        prompt = f"""Você é um analista técnico especializado. Analise o conteúdo já scrapado sobre {tool}.

OBJETIVO: Extrair DICAS e ERROS COMUNS do conteúdo que já temos (SEM FAZER NOVAS BUSCAS).

CONTEÚDO JÁ SCRAPADO (priorizado por riqueza de estrutura):
{context}

{task}

Se não conseguir identificar o mínimo esperado, escreva o que conseguiu encontrar.
NÃO invente dados — use APENAS o que está no conteúdo acima.
"""

        resp = self.llm.generate(
            role="researcher",
            model=self.model,
            prompt=prompt,
            temperature=self.temp,
            timeout=self.timeout,
        )

        return resp.response

    def search_cached_content(self, query: str, tool: Optional[str] = None, k: int = 5) -> list[dict]:
        """Search cached research using semantic similarity (Chroma).

        Useful for:
        - Finding "Docker tips" when writing about "Podman"
        - Avoiding redundant searches when similar content exists
        - Cross-tool knowledge transfer

        Args:
            query: Natural language search (e.g., "performance benchmarks")
            tool: Filter by tool (optional)
            k: Number of results

        Returns:
            List of {text, url, title, similarity} dicts
        """
        if not self.chroma:
            logger.warning("Chroma not available for semantic search")
            return []

        if tool:
            results = self.chroma.query_similar(query, tool=tool, k=k)
            self.memory.log_event("chroma_query", {
                "tool": tool,
                "query": query,
                "results_count": len(results),
                "query_type": "cached_search",
            })
            return results
        else:
            results = self.chroma.cross_tool_search(query, k=k)
            self.memory.log_event("chroma_query", {
                "tool": "all",
                "query": query,
                "results_count": len(results),
                "query_type": "cross_tool",
            })
            return results

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
