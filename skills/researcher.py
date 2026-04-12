import yaml
import logging
from pathlib import Path

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

# URLs que gastam tokens sem retornar dados úteis
SKIP_DOMAINS = {
    "youtube.com", "youtu.be", "twitter.com", "x.com",
    "facebook.com", "instagram.com", "tiktok.com",
    "pinterest.com", "reddit.com/gallery",
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
        llm_conf = self.spec.get("llm", {})
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        self.temp = temperatures["researcher"]
        self.timeout = timeouts.get("researcher", timeouts.get("default", 300))

    def log_url_found(self, url: str, title: str = "", status: str = "", elapsed: float | None = None):
        if self.pipeline_logger:
            self.pipeline_logger.found_url(url, title=title, status=status, elapsed=elapsed)
            return
        self.event_log.log_event("url_found", {
            "url": url,
            "title": title,
            "status": status,
            "elapsed_seconds": elapsed,
        })

    def run(self, tool, alternative="", foco="comparação geral", questoes=None):
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
        
        queries = self.build_queries(tool, alternative, foco, questoes)
        logger.debug(f"Built {len(queries)} search queries")

        results_by_query = self.search.search_multi(queries)
        logger.debug(f"Got search results for {len(results_by_query)} queries")
        
        self.search.save_urls(results_by_query, f"output/urls_{tool}.txt")

        context = self.build_context(results_by_query)
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

    def build_queries(self, tool, alternative, foco, questoes):
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
        templates = FOCUS_QUERIES.get(foco, DEFAULT_QUERIES)
        alt = alternative or "alternatives"
        queries = [
            query_template.replace("{tool}", tool).replace("{alternative}", alt)
            for query_template in templates
        ]
        for question in questoes[:4]:
            queries.append(f"{tool} {question}")
        return queries

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
                if any(domain in url for domain in SKIP_DOMAINS):
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
                    self.log_url_found(url, title=title, status="ok", elapsed=scrape_elapsed)
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
                    )

        self.last_scrape_stats = {
            "ok": scrape_ok,
            "fail": scrape_fail,
            "skipped": len(seen_urls) - total_scrapes,
        }
        return "\n".join(lines)
