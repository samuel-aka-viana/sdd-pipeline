import yaml
import logging
from pathlib import Path
from validators.spec_validator import SpecValidator

from llm import LLMClient

logger = logging.getLogger(__name__)


class CriticSkill:

    def __init__(self, memory, spec_path="spec/article_spec.yaml"):
        self.memory    = memory
        self.spec      = yaml.safe_load(Path(spec_path).read_text())
        self.llm       = LLMClient(spec_path)
        self.model     = self.llm.model_for_role("critic")
        llm_conf = self.spec.get("llm", {})
        temperatures = llm_conf.get("temperature", self.spec.get("ollama", {}).get("temperature", {}))
        timeouts = llm_conf.get("timeout", self.spec.get("ollama", {}).get("timeout", {}))
        self.temp      = temperatures["critic"]
        self.timeout = timeouts.get("critic", timeouts.get("default", 300))
        self.validator = SpecValidator(spec_path)

    def evaluate(self, artigo: str, ferramentas: str) -> dict:
        logger.debug(f"Starting deterministic validation for: {ferramentas}")
        result = self.validator.validate(artigo)
        logger.debug(f"Deterministic validation: passed={result.passed}, problems={len(result.problems)}, warnings={len(result.warnings)}")

        self.memory.log_event("critic_ran", {
            "ferramentas": ferramentas,
            "passed":      result.passed,
            "problems":    result.problems,
            "warnings":    result.warnings,
            "spec_references": result.spec_references,
        })

        if not result.passed:
            logger.info(f"Article REJECTED by deterministic layer: {len(result.problems)} problems found")
            feedback_parts = []
            for i, problem in enumerate(result.problems):
                spec_ref = result.spec_references[i] if i < len(result.spec_references) else ""
                correction = result.corrections.get(problem, "")
                feedback_parts.append(f"- {problem}")
                if spec_ref:
                    feedback_parts.append(f"  📋 Regra da Spec: {spec_ref}")
                if correction:
                    feedback_parts.append(f"  ✓ Correção: {correction}")
            
            detailed_feedback = "\n".join(feedback_parts)
            correction_prompt_base = self.validator.problems_as_prompt(result)
            correction_prompt_enhanced = (
                "FEEDBACK COM REFERÊNCIA À SPEC:\n\n" +
                detailed_feedback +
                "\n\n" +
                correction_prompt_base
            )
            
            return {
                "approved":          False,
                "layer":             "deterministic",
                "problems":          result.problems,
                "correction_prompt": correction_prompt_enhanced,
                "report":            result.report(),
            }

        logger.debug(f"Article PASSED deterministic layer. Starting semantic validation...")
        semantic_issues = self._semantic_check(artigo, ferramentas)

        if semantic_issues:
            logger.info(f"Article REJECTED by semantic layer: {len(semantic_issues)} issues found")
            prompt_lines = [
                "O artigo passou na validação estrutural mas tem problemas semânticos:",
                *[f"- {s}" for s in semantic_issues],
                "\nCorrija APENAS esses problemas. Mantenha o resto intacto.",
            ]
            return {
                "approved":          False,
                "layer":             "semantic",
                "problems":          semantic_issues,
                "correction_prompt": "\n".join(prompt_lines),
                "report":            result.report(),
            }

        logger.info(f"Article APPROVED by both deterministic and semantic layers")
        return {
            "approved": True,
            "layer":    "semantic",
            "warnings": result.warnings,
            "report":   result.report(),
        }

    def _semantic_check(self, artigo: str, ferramentas: str) -> list[str]:
        prompt = f"""Revise este artigo sobre {ferramentas}.
Liste APENAS problemas factuais óbvios:
- Comando que claramente não existe nessa ferramenta
- Número claramente impossível (ex: "consome 3MB de RAM" para banco de dados)
- Contradição interna entre seções
- Import ou path de código que não existe

Responda APENAS com lista numerada de problemas encontrados.
Se não encontrar problemas, responda exatamente: SEM PROBLEMAS

ARTIGO:
{artigo[:4000]}
"""
        resp = self.llm.generate(
            role="critic",
            model=self.model,
            prompt=prompt,
            temperature=self.temp,
            timeout=self.timeout,
        )
        text = resp.response.strip()
        if "SEM PROBLEMAS" in text.upper():
            return []
        return [
            l.strip()
            for l in text.split("\n")
            if l.strip() and l[0].isdigit()
        ]
