from pathlib import Path

import yaml


class TemplateValidator:
    """Validates prompt template catalog required by runtime."""

    REQUIRED_TEMPLATES = {
        "researcher.yaml": ["main"],
        "analyst.yaml": ["main"],
        "writer.yaml": ["main"],
        "critic.yaml": ["semantic_check"],
        "orchestrator.yaml": ["decide_retry_or_finalize"],
        "research_enricher.yaml": ["targeted_research_questions", "reanalyze_cached_content"],
        "fact_checker.yaml": ["semantic_fact_check", "false_positive_filter"],
    }

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for filename, keys in self.REQUIRED_TEMPLATES.items():
            path = self.prompts_dir / filename
            if not path.exists():
                errors.append(f"Prompt file ausente: {path}")
                continue
            try:
                content = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            except Exception as exc:
                errors.append(f"Prompt inválido ({path}): {exc}")
                continue
            for key in keys:
                if not content.get(key):
                    errors.append(f"Template ausente em {path}: {key}")
        return errors
