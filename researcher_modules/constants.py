"""Constantes do researcher: queries, hosts confiáveis, stopwords, intents.

Movido de skills/researcher.py para reduzir tamanho do módulo principal.
Importado via `from researcher_modules.constants import *` em researcher.py.
"""

from __future__ import annotations

from pathlib import Path

FOCUS_QUERIES: dict[str, list[str]] = {
    "comparação geral": [
        "{tool} vs {alternative}",
        "{tool} vs {alternative} when to use which",
        "{tool} vs {alternative} pros cons",
        "{tool} vs {alternative} benchmark comparison 2024 2025",
        "{alternative} vs {tool} comparison real world",
        "{tool} vs {alternative} features table",
        "{tool} vs {alternative} when to use which",
        "{tool} common errors site:stackoverflow.com",
        "{tool} minimum requirements hardware",
        "{tool} troubleshooting FAQ",
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
    "{tool} vs {alternative} pros cons",
    "{alternative} vs {tool} comparison",
    "{tool} vs {alternative} 2024 2025",
    "{tool} common errors site:stackoverflow.com",
    "{tool} site:github.com",
    "{tool} minimum requirements hardware",
    "{tool} best practices production",
    "{tool} vs {alternative} when to use",
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
    # Homônimos frequentes de "ministack" fora do contexto de software cloud
    "programming4.us",
    "petapixel.com",
    "storagereview.com",
    "studylib.net",
    "macsales.com",
    "owc.com",
    "macrumors.com",
    "newertech.com",
    "manualslib.es",
    "alternate.es",
    "plazavea.com.pe",
    "musisol.com",
    "soydemac.com",
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
    "a", "as", "o", "os", "de", "da", "das", "do", "dos",
    "e", "em", "para", "por", "com", "sem", "que",
    "como", "quando", "qual", "quais",
    "no", "na", "nos", "nas",
    "um", "uma", "ou", "ao", "aos",
    "nao", "não",
}

TOOL_IDENTITY_STOPWORDS = {
    "core",
}

PERFORMANCE_INTENT_TERMS = {
    "benchmark", "benchmarks",
    "latencia", "latência",
    "throughput",
    "rps", "qps",
    "p50", "p95", "p99",
    "cpu", "ram", "vram",
    "memoria", "memória",
}

INTEGRATION_INTENT_TERMS = {
    "integracao", "integração",
    "arquitetura",
    "pipeline",
    "fluxo",
    "connector",
}

SECURITY_INTENT_TERMS = {
    "seguranca", "segurança",
    "auth", "autenticacao", "autenticação",
    "rbac",
    "tls", "ssl",
    "cve",
    "vulnerabilidade",
}

MAX_SCRAPES_PER_TOOL = 10
MAX_CHARS_PER_SCRAPE = 4000
DOMAIN_SCRAPE_STATS_PATH = Path(".memory/scrape_domain_stats.json")
MAX_PARALLEL_PER_DOMAIN = 1
HTML_DEBUG_ENABLED = True
