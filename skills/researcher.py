import yaml
from pathlib import Path
from ollama import Client

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

    def __init__(self, search_tool, scraper_tool, memory, spec_path="spec/article_spec.yaml"):
        self.search = search_tool
        self.scraper = scraper_tool
        self.memory = memory
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self.model = self.spec["models"]["researcher"]
        self.temp = self.spec["ollama"]["temperature"]["researcher"]
        self.llm = Client(host=self.spec["ollama"]["base_url"])

    # ------------------------------------------------------------------
    # público
    # ------------------------------------------------------------------
    def run(self, tool, alternative="", foco="comparação geral", questoes=None):
        questoes = questoes or []
        queries = self._build_queries(tool, alternative, foco, questoes)

        results_by_query = self.search.search_multi(queries)
        self.search.save_urls(results_by_query, f"output/urls_{tool}.txt")

        context = self._build_context(results_by_query)
        lessons = self.memory.get_lessons_for_prompt()

        questoes_block = ""
        if questoes:
            lista = "\n".join(f"- {q}" for q in questoes)
            questoes_block = f"\nBusque dados específicos para responder:\n{lista}\n"

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
        resp = self.llm.generate(
            model=self.model,
            prompt=prompt,
            options={"temperature": self.temp},
        )

        self.memory.log_event("research_done", {
            "tool": tool,
            "foco": foco,
            "queries": queries,
            "scrape_stats": self._last_scrape_stats,
        })
        return resp.response

    # ------------------------------------------------------------------
    # queries
    # ------------------------------------------------------------------
    def _build_queries(self, tool, alternative, foco, questoes):
        templates = FOCUS_QUERIES.get(foco, DEFAULT_QUERIES)
        alt = alternative or "alternatives"
        queries = [
            q.replace("{tool}", tool).replace("{alternative}", alt)
            for q in templates
        ]
        for q in questoes[:4]:
            queries.append(f"{tool} {q}")
        return queries

    # ------------------------------------------------------------------
    # contexto
    # ------------------------------------------------------------------
    def _build_context(self, results_by_query):
        lines = []
        seen_urls: set[str] = set()
        scrape_ok = 0
        scrape_fail = 0
        total_scrapes = 0

        for query, results in results_by_query.items():
            lines.append(f"\n### Busca: {query}")

            for r in results:
                url = r.get("url", "")
                if not url.startswith("http") or url in seen_urls:
                    continue
                if any(d in url for d in SKIP_DOMAINS):
                    continue
                seen_urls.add(url)

                if total_scrapes >= MAX_SCRAPES_PER_TOOL:
                    lines.append(f"URL: {url}")
                    lines.append(f"Resumo: {r.get('snippet', '')}")
                    lines.append("---")
                    continue

                total_scrapes += 1
                result = self.scraper.extract_text(url)

                if result["status"] == "ok":
                    scrape_ok += 1
                    text = result["text"][:MAX_CHARS_PER_SCRAPE]
                    tag = " [TRUNCADO]" if result.get("truncated") else ""
                    lines.append(f"URL: {url}{tag}")
                    lines.append(f"Conteúdo Extraído:\n{text}")
                    lines.append("---")
                else:
                    scrape_fail += 1
                    self.memory.log_event("scrape_failed", {
                        "url": url, "status": result["status"],
                    })
                    snippet = r.get("snippet", "")
                    if snippet:
                        lines.append(f"URL: {url} [SCRAPE_FALHOU: {result['status']}]")
                        lines.append(f"Resumo (fallback): {snippet}")
                        lines.append("---")

        self._last_scrape_stats = {
            "ok": scrape_ok,
            "fail": scrape_fail,
            "skipped": len(seen_urls) - total_scrapes,
        }
        return "\n".join(lines)