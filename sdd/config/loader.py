from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_CONFIG_DIR = Path(__file__).resolve().parent

DEFAULT_RESEARCH_REQUIRED_FIELDS = [
    "urls",
    "instalacao",
    "requisitos",
    "erros",
    "alternativas",
]

DEFAULT_ANALYSIS_REQUIRED_FIELDS = [
    "tabela_requisitos",
    "tabela_comparacao",
    "pros",
    "contras",
    "otimizacoes",
]

DEFAULT_LLM_TIMEOUT = {
    "researcher": 240,
    "analyst": 180,
    "writer": 360,
    "critic": 180,
    "default": 240,
}

DEFAULT_LLM_TEMPERATURE = {
    "researcher": 0.1,
    "analyst": 0.1,
    "writer": 0.3,
    "critic": 0.0,
}

DEFAULT_LLM_CONTEXT_LENGTH = {
    "default": 16000,
    "researcher": 16000,
    "analyst": 16000,
    "writer": 16000,
    "critic": 16000,
}

DEFAULT_WRITER_INPUT = {
    "max_research_chars": 16000,
    "max_analysis_chars": 16000,
    "max_correction_chars": 4000,
}


def _read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _deep_merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_runtime_config(config_dir: str | Path = DEFAULT_CONFIG_DIR) -> dict:
    config_path = Path(config_dir)
    models_raw = _read_yaml(config_path / "models.yaml")
    pipeline_raw = _read_yaml(config_path / "pipeline.yaml")
    quality_raw = _read_yaml(config_path / "quality.yaml")
    infra_raw = _read_yaml(config_path / "infra.yaml")

    role_entries = {
        name: value
        for name, value in models_raw.items()
        if isinstance(value, dict) and "model" in value
    }
    models = {name: str(value["model"]).strip() for name, value in role_entries.items()}
    model_providers = {
        name: str(value.get("provider", "ollama")).strip().lower()
        for name, value in role_entries.items()
    }

    required_sections = list(quality_raw.get("required_sections", []))
    quality_rules = {
        "no_placeholders": quality_raw.get("no_placeholders", {}),
        "min_references": int(quality_raw.get("min_refs", 3)),
        "min_errors": int(quality_raw.get("min_errors", 2)),
        "min_tips": int(quality_raw.get("min_tips", 3)),
        "min_solution_chars": int(quality_raw.get("min_solution_chars", 20)),
        "hardware_sanity": quality_raw.get("hardware_sanity", {"max_ram_minimum_gb": 2}),
        "url_validation": quality_raw.get("url_validation", {}),
    }

    llm = {
        "provider": models_raw.get("default_provider", "openrouter_free"),
        "timeout": models_raw.get("timeout", DEFAULT_LLM_TIMEOUT),
        "temperature": models_raw.get("temperature", DEFAULT_LLM_TEMPERATURE),
        "context_length": models_raw.get("context_length", DEFAULT_LLM_CONTEXT_LENGTH),
        "writer_input": models_raw.get("writer_input", DEFAULT_WRITER_INPUT),
        "providers": {
            "openrouter": infra_raw.get("openrouter", {}),
            "ollama": infra_raw.get("ollama", {}),
        },
    }

    search_conf = infra_raw.get("search", {})
    source_guardrails = {
        "min_score_keep": int(search_conf.get("min_score_keep", 3)),
        "max_results_per_query": int(search_conf.get("max_results_per_query", 5)),
    }

    pipeline = {
        "timeout_total_seconds": int(pipeline_raw.get("timeout_total_seconds", 1800)),
        "max_iterations": int(pipeline_raw.get("max_iterations", 2)),
        "max_stagnant_iterations": int(pipeline_raw.get("max_stagnant", 2)),
        "max_research_enrichments": int(pipeline_raw.get("max_enrichments", 1)),
        "orchestration": {"backend": pipeline_raw.get("backend", "langgraph")},
    }

    return {
        "spec_version": "1.0.0",
        "spec_changelog": {
            "1.0.0": {
                "date": "2026-04-26",
                "changes": ["Split config compatibility view backed by sdd/config/*.yaml"],
            }
        },
        "models": models,
        "model_providers": model_providers,
        "llm": llm,
        "article": {
            "required_sections": required_sections,
            "quality_rules": quality_rules,
        },
        "research": {
            "required_fields": list(infra_raw.get("required_fields", DEFAULT_RESEARCH_REQUIRED_FIELDS)),
            "search_queries": list(search_conf.get("search_queries", [])),
            "search_cache": {
                "enabled": bool(search_conf.get("cache_enabled", True)),
                "ttl_seconds": int(search_conf.get("cache_ttl_seconds", 86400)),
                "results_per_query": int(search_conf.get("results_per_query", 8)),
                "path": search_conf.get("cache_path", ".memory/search_cache.json"),
            },
            "scraper": dict(infra_raw.get("scraper", {})),
            "source_guardrails": source_guardrails,
            "relevance_filter": {
                "max_urls": int(search_conf.get("max_urls", 30)),
                "rerank": bool(search_conf.get("rerank", True)),
            },
        },
        "analysis": {
            "required_fields": list(
                infra_raw.get("analysis_required_fields", DEFAULT_ANALYSIS_REQUIRED_FIELDS)
            )
        },
        "pipeline": pipeline,
    }


def resolve_runtime_config(spec: dict | None = None, spec_path: str | None = None) -> dict:
    if spec is not None:
        base = load_runtime_config()
        return _deep_merge(base, spec)
    if spec_path:
        return yaml.safe_load(Path(spec_path).read_text())
    return load_runtime_config()
