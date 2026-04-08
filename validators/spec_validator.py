import re
import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ValidationResult:
    passed:   bool
    problems: list[str]
    warnings: list[str]

    def report(self) -> str:
        lines = []
        if self.problems:
            lines.append("PROBLEMAS (bloqueantes):")
            for p in self.problems:
                lines.append(f"  ✗ {p}")
        if self.warnings:
            lines.append("AVISOS (não bloqueantes):")
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        if self.passed:
            lines.append("✓ Artigo passou em todas as validações")
        return "\n".join(lines)


class SpecValidator:

    def __init__(self, spec_path="spec/article_spec.yaml"):
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self._rules = self.spec["article"]["quality_rules"]

    def validate(self, artigo, secoes=None):
        problems = []
        warnings = []
        text_lower = artigo.lower()

        secoes_ativas = secoes or self.spec["article"]["required_sections"]

        section_patterns = {
            "tldr":             ["tl;dr", "tldr", "resumo rápido"],
            "o_que_e":          ["o que é", "por que usar", "introdução"],
            "requisitos":       ["requisito", "hardware", "recurso"],
            "instalacao":       ["instala"],
            "configuracao":     ["configura"],
            "exemplo_pratico":  ["exemplo", "caso de uso", "prático"],
            "armadilhas":       ["armadilha", "erro comum", "problema comum",
                                 "pitfall", "⚠"],
            "otimizacoes":      ["otimiza", "dica", "performance"],
            "conclusao":        ["conclusão", "conclusao", "trade-off", "veredito"],
            "referencias":      ["referência", "referencia", "fontes"],
            "arquitetura":      ["arquitetura", "architecture", "componente"],
            "throughput":       ["throughput", "mensagens/segundo", "msgs/s"],
            "garantias_entrega":["at-least-once", "exactly-once", "garantia"],
            "compatibilidade_s3":["s3 compat", "api s3", "s3 api"],
            "replicacao":       ["replicação", "replica"],
            "modelos_recomendados": ["modelo recomendado", "recommended model"],
            "quantizacao":      ["quantização", "quantization", "q4", "q8"],
            "benchmark":        ["benchmark", "tokens/s", "tokens por segundo"],
            "migracao":         ["migração", "migration", "migrar"],
            "seguranca":        ["segurança", "security", "autenticação"],
        }

        for secao in secoes_ativas:
            patterns = section_patterns.get(secao, [secao.replace("_", " ")])
            if not any(p in text_lower for p in patterns):
                problems.append(f"Seção ausente: {secao}")

        for pattern in self._rules["no_placeholders"]["patterns"]:
            if pattern.lower() in text_lower:
                problems.append(f"Placeholder não preenchido: '{pattern}'")

        urls_reais = re.findall(r'https?://[^\s\)\"\'\]]+', artigo)
        min_refs = self._rules["min_references"]
        if len(urls_reais) < min_refs:
            problems.append(
                f"Referências insuficientes: {len(urls_reais)} URLs, mínimo {min_refs}"
            )

        url_rules = self._rules.get("url_validation", {})
        block = url_rules.get("block_patterns", [])
        for url in urls_reais:
            for bp in block:
                if bp in url:
                    problems.append(f"URL inválida/placeholder: {url}")
                    break

        error_markers = re.findall(
            r'(erro:|error:|armadilha|problema:|⚠|sintoma:)', text_lower
        )
        min_errors = self._rules.get("min_errors", 2)
        if len(error_markers) < min_errors:
            warnings.append(
                f"Poucos erros documentados: {len(error_markers)}, "
                f"recomendado {min_errors}"
            )

        min_sol = self._rules.get("min_solution_chars", 20)
        armadilha_blocks = re.findall(
            r'(?:solução|solu[çc][aã]o)[:\s]*```[a-z]*\n(.*?)```',
            artigo, re.IGNORECASE | re.DOTALL
        )
        for block in armadilha_blocks:
            content = block.strip()
            if len(content) < min_sol:
                problems.append(
                    f"Solução vazia/genérica em armadilha: "
                    f"'{content[:40]}' ({len(content)} chars, mínimo {min_sol})"
                )

        hw = self._rules.get("hardware_sanity")
        if hw:
            max_ram = hw.get("max_ram_minimum_gb", 2)
            ram_values = re.findall(r'(\d+)\s*gb', text_lower)
            for val in ram_values:
                if int(val) > max_ram * 2:
                    warnings.append(
                        f"RAM suspeito: {val}GB — verifique se está correto"
                    )

        code_blocks = re.findall(r'```', artigo)
        if len(code_blocks) < 4:
            warnings.append(
                "Poucos blocos de código — verifique se comandos foram incluídos"
            )

        table_rows = re.findall(r'\|(.+)\|', artigo)
        for row in table_rows:
            cells = [c.strip() for c in row.split('|')]
            if any(c == '' for c in cells if not re.match(r'^-+$', c)):
                warnings.append("Tabela com célula vazia detectada")
                break

        return ValidationResult(
            passed=len(problems) == 0,
            problems=problems,
            warnings=warnings,
        )

    def problems_as_prompt(self, result):
        if result.passed:
            return ""
        lines = ["O artigo tem os seguintes problemas que DEVEM ser corrigidos:"]
        for i, p in enumerate(result.problems, 1):
            lines.append(f"{i}. {p}")
        lines.append(
            "\nReescreva o artigo corrigindo APENAS esses problemas."
        )
        lines.append("Mantenha todo o conteúdo existente que está correto.")
        lines.append(
            "LEMBRETE: Se não tem dado, OMITA a linha. "
            "Nunca escreva placeholders."
        )
        return "\n".join(lines)