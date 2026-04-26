"""Shared utilities for skills — pure functions and constants."""

import re

TEMPORAL_MARKERS = (
    "ano atual",
    "já que o ano atual",
    "é 2023",
    "impossível, já que o ano atual",
    "data do link",
    "datas futuras",
    "conhecimento temporal",
)

TOOL_TYPE_ALLOWLIST: dict[str, set[str]] = {
    "containers": {"rootless", "nerdctl", "cri-o", "containerd", "buildkit"},
    "orchestration": {"kubectl", "helm", "cri-o", "containerd"},
    "databases_olap": {"duckdb", "polars", "datafusion", "datafusion-cli"},
    "llm_tools": {"ollama", "llama.cpp", "lm-studio", "vllm"},
}


def extract_evidence_based_issues(critic_output: str, article_excerpt: str) -> list[str]:
    issues = []
    article_lower = article_excerpt.lower()
    for line in critic_output.split("\n"):
        line = line.strip()
        if not line or not line[0].isdigit():
            continue
        match = re.match(
            r'^\d+\.\s*TRECHO:\s*"(.+?)"\s*\|\s*PROBLEMA:\s*(.+)$',
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            continue
        excerpt = match.group(1).strip()
        problem = match.group(2).strip()
        if len(excerpt) < 8 or len(problem) < 10:
            continue
        if excerpt.lower() not in article_lower:
            continue
        issues.append(f'Trecho "{excerpt}": {problem}')
    return issues
