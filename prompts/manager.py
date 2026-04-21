import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PromptManager:
    """Load prompts from YAML. Log usage metrics to memory."""

    def __init__(self, memory, prompts_dir="prompts"):
        self.memory = memory
        self.prompts_dir = Path(prompts_dir)
        self._cache = {}

    def get(self, role: str, template_key: str, **kwargs) -> str:
        """Load prompt template and format with kwargs."""
        try:
            prompts = self._load(role)
            if template_key not in prompts:
                logger.warning(f"Template '{template_key}' not found for role '{role}'")
                return ""

            template = prompts[template_key]
            rendered = template.format(**kwargs)

            self.memory.log_event("prompt_used", {
                "role": role,
                "template_key": template_key,
                "version": prompts.get("version", "unknown"),
                "rendered_chars": len(rendered),
            })

            return rendered
        except Exception as e:
            logger.error(f"Error loading prompt {role}/{template_key}: {e}")
            return ""

    def _load(self, role: str) -> dict:
        """Load and cache prompt file for role."""
        if role not in self._cache:
            path = self.prompts_dir / f"{role}.yaml"
            try:
                content = yaml.safe_load(path.read_text())
                self._cache[role] = content or {}
            except FileNotFoundError:
                logger.warning(f"Prompt file not found: {path}")
                self._cache[role] = {}
            except yaml.YAMLError as e:
                logger.error(f"Invalid YAML in {path}: {e}")
                self._cache[role] = {}

        return self._cache[role]

    def reload(self, role: str = None):
        """Reload prompt cache (for development/testing)."""
        if role:
            self._cache.pop(role, None)
        else:
            self._cache.clear()
        logger.debug(f"Reloaded prompts cache for role(s): {role or 'all'}")
