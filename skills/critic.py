import yaml
import logging
import re
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
            problem_entries = zip(result.problems, result.spec_references + [""] * len(result.problems))
            for problem, spec_ref in problem_entries:
                correction = result.corrections.get(problem, "")
                feedback_parts.append(f"- {problem}")
                optional_feedback_lines = [
                    f"  📋 Regra da Spec: {spec_ref}" if spec_ref else "",
                    f"  ✓ Correção: {correction}" if correction else "",
                ]
                feedback_parts.extend(
                    line for line in optional_feedback_lines if line
                )
            
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
        semantic_issues = self.semantic_check(artigo, ferramentas)
        semantic_issues = self.filter_known_false_positives(semantic_issues)

        if semantic_issues:
            logger.info(f"Article REJECTED by semantic layer: {len(semantic_issues)} issues found")
            prompt_lines = [
                "O artigo passou na validação estrutural mas tem problemas semânticos:",
                *[f"- {issue}" for issue in semantic_issues],
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

    def semantic_check(self, artigo: str, ferramentas: str) -> list[str]:
        prompt = f"""Revise este artigo sobre {ferramentas}.
Liste APENAS problemas factuais óbvios:
- Comando que claramente não existe nessa ferramenta
- Número claramente impossível (ex: "consome 3MB de RAM" para banco de dados)
- Contradição interna entre seções
- Import ou path de código que não existe

Formato obrigatório de resposta:
1. TRECHO: "<citação literal exata do artigo>" | PROBLEMA: <explicação objetiva>
2. TRECHO: "<citação literal exata do artigo>" | PROBLEMA: <explicação objetiva>

Regras:
- Só reporte se houver TRECHO literal presente no ARTIGO.
- Se não houver evidência textual, NÃO reporte.
- NÃO use suposição de "ano atual" para invalidar links/datas.
- NÃO critique datas futuras ou anos como 2026/2027 por si só.
- Ignore qualquer limitação de conhecimento temporal do modelo.
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
        return self.extract_evidence_based_issues(text, artigo[:4000])

    def filter_known_false_positives(self, issues: list[str]) -> list[str]:
        filtered_issues = []
        temporal_false_positive_markers = (
            "ano atual",
            "já que o ano atual",
            "é 2023",
            "impossível, já que o ano atual",
            "data do link",
            "datas futuras",
            "conhecimento temporal",
        )
        for issue in issues:
            normalized_issue = (issue or "").lower()
            if any(marker in normalized_issue for marker in temporal_false_positive_markers):
                continue
            filtered_issues.append(issue)
        return filtered_issues

    def extract_evidence_based_issues(self, critic_output: str, article_excerpt: str) -> list[str]:
        issues = []
        article_lower = article_excerpt.lower()

        for response_line in critic_output.split("\n"):
            line = response_line.strip()
            if not line or not line[0].isdigit():
                continue

            match = re.match(
                r'^\d+\.\s*TRECHO:\s*"(.+?)"\s*\|\s*PROBLEMA:\s*(.+)$',
                line,
                flags=re.IGNORECASE,
            )
            if not match:
                continue

            quoted_excerpt = match.group(1).strip()
            problem_text = match.group(2).strip()
            if len(quoted_excerpt) < 8 or len(problem_text) < 10:
                continue
            if quoted_excerpt.lower() not in article_lower:
                continue

            issues.append(f'Trecho "{quoted_excerpt}": {problem_text}')

        return issues
