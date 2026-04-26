import yaml
import logging
from pathlib import Path

from llm import LLMClient
from prompts.manager import PromptManager

logger = logging.getLogger(__name__)


class SkillBase:
    """Common initialisation for all pipeline skills.

    Subclasses declare their ROLE class variable and call super().__init__().
    Chroma is injected (not self-constructed) so the whole pipeline shares one client.
    """

    ROLE: str = ""

    def __init__(self, memory, spec_path: str = "spec/article_spec.yaml", chroma=None):
        self.memory = memory
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self.llm = LLMClient(spec_path)
        self.prompts = PromptManager(memory, prompts_dir="prompts")
        self.model = self.llm.model_for_role(self.ROLE)
        self.chroma = chroma

        llm_conf = self.spec.get("llm", {})
        _compat = self.spec.get("ollama", {})
        temps = llm_conf.get("temperature", _compat.get("temperature", {}))
        timeouts = llm_conf.get("timeout", _compat.get("timeout", {}))
        ctx = llm_conf.get("context_length", _compat.get("context_length", {}))

        self.temp = temps.get(self.ROLE, temps.get("default", 0.1))
        self.timeout = timeouts.get(self.ROLE, timeouts.get("default", 300))
        self.ctx_len = ctx.get(self.ROLE, ctx.get("default", 8192))
