import logging
import re as _re
from llm.structured import StructuredOutputError
from skills.base import SkillBase
from sdd.schemas import FilteredIssuesResult, SemanticCheckResult
from skills.utils import TEMPORAL_MARKERS, TOOL_TYPE_ALLOWLIST
from validators.spec_validator import SpecValidator

logger = logging.getLogger(__name__)

_ARTICLE_URL_RE = _re.compile(r"https?://[^\s)>\]\"'`<]+", _re.IGNORECASE)


def _check_url_groundedness(artigo: str, evidence_pack) -> list[str]:
    """Return problems for URLs in article that are not in the evidence pack."""
    if evidence_pack is None or not evidence_pack.retained_urls:
        return []
    allowed = set(evidence_pack.retained_urls)
    for item in evidence_pack.items:
        allowed.add(item.source_url)
    article_urls = [
        u.rstrip(".,;:!?")
        for u in _ARTICLE_URL_RE.findall(artigo)
    ]
    outside = [u for u in article_urls if u not in allowed]
    if not outside:
        return []
    sample = ", ".join(outside[:3])
    return [f"URLs fora do evidence pack ({len(outside)} encontradas): {sample}"]


class CriticSkill(SkillBase):
    ROLE = "critic"

    def __init__(self, memory, spec_path="spec/article_spec.yaml", chroma=None):
        super().__init__(memory, spec_path, chroma)
        self.semantic_window = self.ctx_len
        self.validator = SpecValidator(spec_path)
        # Modelo menor para classificação/filtro (semantic_check, false_positive_filter).
        # Cai pro modelo padrão do critic se critic_fast não estiver configurado.
        self.fast_model = self.llm.resolve_fast_model("critic")
        if self.fast_model != self.model:
            logger.info("[critic] usando fast_model=%s para sub-tasks de classificação", self.fast_model)

    def evaluate(self, artigo: str, ferramentas: str, tool_type: str = "unknown", evidence_pack=None) -> dict:
        logger.debug(f"Starting deterministic validation for: {ferramentas} (tool_type={tool_type})")
        result = self.validator.validate(artigo)
        groundedness_problems = _check_url_groundedness(artigo, evidence_pack)
        logger.debug(
            f"Deterministic validation: passed={result.passed}, "
            f"problems={len(result.problems)}, warnings={len(result.warnings)}"
        )

        self.memory.log_event("critic_ran", {
            "ferramentas": ferramentas,
            "tool_type": tool_type,
            "passed": result.passed,
            "problems": result.problems,
            "warnings": result.warnings,
            "spec_references": result.spec_references,
        })

        if not result.passed or groundedness_problems:
            all_problems = list(result.problems) + groundedness_problems
            logger.info(f"Article REJECTED by deterministic layer: {len(all_problems)} problems found")
            feedback_parts = []
            problem_entries = zip(result.problems, result.spec_references + [""] * len(result.problems))
            for problem, spec_ref in problem_entries:
                correction = result.corrections.get(problem, "")
                feedback_parts.append(f"- {problem}")
                optional_lines = [
                    f"  📋 Regra da Spec: {spec_ref}" if spec_ref else "",
                    f"  ✓ Correção: {correction}" if correction else "",
                ]
                feedback_parts.extend(line for line in optional_lines if line)
            for gp in groundedness_problems:
                feedback_parts.append(f"- {gp}")

            detailed_feedback = "\n".join(feedback_parts)
            correction_prompt_base = self.validator.problems_as_prompt(result)
            correction_prompt_enhanced = (
                "FEEDBACK COM REFERÊNCIA À SPEC:\n\n"
                + detailed_feedback
                + "\n\n"
                + correction_prompt_base
            )
            return {
                "approved": False,
                "layer": "deterministic",
                "problems": all_problems,
                "correction_prompt": correction_prompt_enhanced,
                "report": result.report(),
            }

        logger.debug("Article PASSED deterministic layer. Starting semantic validation...")
        semantic_issues = self.semantic_check(artigo, ferramentas, tool_type)
        semantic_issues = self.filter_known_false_positives(semantic_issues, tool_type)

        history_warnings = self._validate_against_history(artigo, ferramentas)
        if history_warnings:
            logger.debug(f"History validation found {len(history_warnings)} warnings")
            self.memory.log_event("critic_history_warnings", {
                "ferramentas": ferramentas,
                "warnings_count": len(history_warnings),
            })

        if semantic_issues:
            logger.info(f"Article REJECTED by semantic layer: {len(semantic_issues)} issues found")
            prompt_lines = [
                "O artigo passou na validação estrutural mas tem problemas semânticos:",
                *[f"- {issue}" for issue in semantic_issues],
                "\nCorrija APENAS esses problemas. Mantenha o resto intacto.",
            ]
            return {
                "approved": False,
                "layer": "semantic",
                "problems": semantic_issues,
                "correction_prompt": "\n".join(prompt_lines),
                "report": result.report(),
            }

        logger.info("Article APPROVED by both deterministic and semantic layers")
        return {
            "approved": True,
            "layer": "semantic",
            "warnings": result.warnings,
            "report": result.report(),
        }

    def _validate_against_history(self, artigo: str, ferramentas: str) -> list[str]:
        if not self.chroma:
            return []
        try:
            similar_articles = self.chroma.find_historical_articles(ferramentas)
        except Exception as e:
            logger.debug(f"History validation failed (graceful): {e}")
            return []

        if not similar_articles:
            return []

        warnings = []
        current_length = len(artigo)
        historical_lengths = [len(r.get("text", "")) for r in similar_articles]
        avg_length = sum(historical_lengths) / len(historical_lengths) if historical_lengths else 0

        if avg_length > 0 and current_length < avg_length * 0.6:
            warnings.append(
                f"Artigo é {((1 - current_length / avg_length) * 100):.0f}% menor que média histórica "
                f"({current_length} vs {avg_length:.0f} chars). Verifique se faltam seções."
            )

        similarities = [r.get("similarity", 0) for r in similar_articles]
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0

        if avg_similarity < 0.3:
            warnings.append(
                f"Artigo é muito diferente de artigos anteriores sobre {ferramentas} "
                f"(similaridade média: {avg_similarity:.2f}). Verifique consistência de estrutura."
            )
        elif avg_similarity > 0.85:
            warnings.append(
                f"Artigo é muito similar a versões anteriores ({avg_similarity:.2f}). "
                f"Verifique se há conteúdo único/atualizado."
            )
        return warnings

    def semantic_check(self, artigo: str, ferramentas: str, tool_type: str = "unknown") -> list[str]:
        prompt = self.prompts.get(
            "fact_checker",
            "semantic_fact_check",
            ferramentas=ferramentas,
            tool_type=tool_type,
            artigo=artigo[:self.semantic_window],
        )
        if not prompt:
            raise RuntimeError("Prompt template missing: prompts/fact_checker.yaml#semantic_fact_check")
        article_window = artigo[:self.semantic_window]
        try:
            result = self.llm.generate_structured(
                role="critic",
                model=self.fast_model,
                prompt=prompt,
                schema=SemanticCheckResult,
                temperature=self.temp,
                num_ctx=self.ctx_len,
                timeout=self.timeout,
            )
        except StructuredOutputError as exc:
            logger.info("semantic_check fallback para texto livre: %s", exc)
            resp = self.llm.generate(
                role="critic",
                model=self.fast_model,
                prompt=prompt,
                temperature=self.temp,
                num_ctx=self.ctx_len,
                timeout=self.timeout,
            )
            text = resp.response.strip()
            if "SEM PROBLEMAS" in text.upper():
                return []
            return self.extract_evidence_based_issues(text, article_window)

        article_lower = article_window.lower()
        extracted = []
        for issue in result.issues:
            excerpt = issue.excerpt.strip()
            problem = issue.problem.strip()
            if not excerpt or not problem:
                continue
            if excerpt.lower() not in article_lower:
                continue
            extracted.append(f'TRECHO: "{excerpt}" | PROBLEMA: {problem}')
        return extracted

    def filter_known_false_positives(self, issues: list[str], tool_type: str = "unknown") -> list[str]:
        allowed_patterns = TOOL_TYPE_ALLOWLIST.get(tool_type, set())

        filtered = [
            issue for issue in issues
            if not any(m in (issue or "").lower() for m in TEMPORAL_MARKERS)
            and not any(p.lower() in (issue or "").lower() for p in allowed_patterns)
        ]

        prompt = self.prompts.get(
            "fact_checker",
            "false_positive_filter",
            tool_type=tool_type,
            raw_issues=filtered,
            allowed_patterns=sorted(allowed_patterns),
        )
        if not prompt or not filtered:
            return filtered
        try:
            result = self.llm.generate_structured(
                role="critic",
                model=self.fast_model,
                prompt=prompt,
                schema=FilteredIssuesResult,
                temperature=self.temp,
                num_ctx=self.ctx_len,
                timeout=self.timeout,
            )
            mapped = []
            for item in result.filtered_issues:
                problem = item.problem.strip()
                excerpt = item.excerpt.strip()
                if not problem:
                    continue
                mapped.append(
                    f'TRECHO: "{excerpt}" | PROBLEMA: {problem}' if excerpt else problem
                )
            if mapped:
                return mapped
        except (StructuredOutputError, Exception) as exc:
            logger.debug("filter_known_false_positives sem JSON estruturado: %s", exc)
        return filtered

