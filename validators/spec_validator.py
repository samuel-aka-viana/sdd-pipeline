import re
import yaml
from pathlib import Path
from dataclasses import dataclass


@dataclass
class ValidationResult:
    passed:   bool
    problems: list[str]
    warnings: list[str]
    spec_references: list[str] = None
    corrections: dict = None

    def __post_init__(self):
        if self.spec_references is None:
            self.spec_references = []
        if self.corrections is None:
            self.corrections = {}

    def report(self) -> str:
        lines = []
        if self.problems:
            lines.append("PROBLEMAS (bloqueantes):")
            for index, problem in enumerate(self.problems):
                spec_ref = self.spec_references[index] if index < len(self.spec_references) else ""
                correction = self.corrections.get(problem, "")
                lines.append(f"  ✗ {problem}")
                if spec_ref:
                    lines.append(f"    📋 Spec: {spec_ref}")
                if correction:
                    lines.append(f"    ✓ Correção: {correction}")
        if self.warnings:
            lines.append("AVISOS (não bloqueantes):")
            for warning in self.warnings:
                lines.append(f"  ⚠ {warning}")
        if self.passed:
            lines.append("✓ Artigo passou em todas as validações")
        return "\n".join(lines)


class SpecValidator:

    SECTION_PATTERNS = {
        "tldr": ["tl;dr", "tldr", "resumo rápido"],
        "o_que_e": ["o que é", "por que usar", "introdução"],
        "requisitos": ["requisito", "hardware", "recurso"],
        "instalacao": ["instala"],
        "configuracao": ["configura"],
        "exemplo_pratico": ["exemplo", "caso de uso", "prático"],
        "armadilhas": ["armadilha", "erro comum", "problema comum", "pitfall", "⚠"],
        "otimizacoes": ["otimiza", "dica", "performance"],
        "conclusao": ["conclusão", "conclusao", "trade-off", "veredito"],
        "referencias": ["referência", "referencia", "fontes"],
        "arquitetura": ["arquitetura", "architecture", "componente"],
        "throughput": ["throughput", "mensagens/segundo", "msgs/s"],
        "garantias_entrega": ["at-least-once", "exactly-once", "garantia"],
        "compatibilidade_s3": ["s3 compat", "api s3", "s3 api"],
        "replicacao": ["replicação", "replica"],
        "modelos_recomendados": ["modelo recomendado", "recommended model"],
        "quantizacao": ["quantização", "quantization", "q4", "q8"],
        "benchmark": ["benchmark", "tokens/s", "tokens por segundo"],
        "migracao": ["migração", "migration", "migrar"],
        "seguranca": ["segurança", "security", "autenticação"],
    }

    def __init__(self, spec_path="spec/article_spec.yaml"):
        self.spec = yaml.safe_load(Path(spec_path).read_text())
        self.rules = self.spec["article"]["quality_rules"]

    def validate(self, artigo, secoes=None):
        problems = []
        warnings = []
        spec_references = []
        corrections = {}
        text_lower = artigo.lower()

        secoes_ativas = secoes or self.spec["article"]["required_sections"]
        urls_reais = re.findall(r'https?://[^\s\)\"\'\]]+', artigo)

        validation_context = {
            "artigo": artigo,
            "text_lower": text_lower,
            "secoes_ativas": secoes_ativas,
            "urls_reais": urls_reais,
            "problems": problems,
            "warnings": warnings,
            "spec_references": spec_references,
            "corrections": corrections,
        }

        validations = [
            self.validate_required_sections,
            self.validate_placeholders,
            self.validate_reference_count,
            self.validate_blocked_urls,
            self.validate_min_error_markers,
            self.validate_solution_content,
            self.validate_hardware_sanity,
            self.validate_code_blocks,
            self.validate_table_cells,
            self.validate_command_integrity,
            self.validate_min_tips,
        ]
        list(map(lambda validation_function: validation_function(validation_context), validations))

        return ValidationResult(
            passed=len(problems) == 0,
            problems=problems,
            warnings=warnings,
            spec_references=spec_references,
            corrections=corrections,
        )

    def add_problem(
        self,
        context: dict,
        problem: str,
        spec_reference: str,
        correction: str,
    ):
        context["problems"].append(problem)
        context["spec_references"].append(spec_reference)
        context["corrections"][problem] = correction

    def validate_required_sections(self, context: dict):
        for secao in context["secoes_ativas"]:
            patterns = self.SECTION_PATTERNS.get(secao, [secao.replace("_", " ")])
            if any(pattern in context["text_lower"] for pattern in patterns):
                continue
            self.add_problem(
                context=context,
                problem=f"Seção ausente: {secao}",
                spec_reference="article.required_sections",
                correction=f"Adicione a seção '# {secao.replace('_', ' ').title()}' ao artigo",
            )

    def validate_placeholders(self, context: dict):
        for pattern in self.rules["no_placeholders"]["patterns"]:
            if pattern.lower() not in context["text_lower"]:
                continue
            self.add_problem(
                context=context,
                problem=f"Placeholder não preenchido: '{pattern}'",
                spec_reference="article.quality_rules.no_placeholders",
                correction=f"Substitua '{pattern}' por conteúdo real ou remova a linha",
            )

    def validate_reference_count(self, context: dict):
        min_refs = self.rules["min_references"]
        url_count = len(context["urls_reais"])
        if url_count >= min_refs:
            return
        self.add_problem(
            context=context,
            problem=f"Referências insuficientes: {url_count} URLs, mínimo {min_refs}",
            spec_reference="article.quality_rules.min_references",
            correction=f"Adicione mais {min_refs - url_count} URL(s) de fontes confiáveis ao artigo",
        )

    def validate_blocked_urls(self, context: dict):
        blocked_patterns = self.rules.get("url_validation", {}).get("block_patterns", [])
        for url in context["urls_reais"]:
            if not any(blocked_pattern in url for blocked_pattern in blocked_patterns):
                continue
            self.add_problem(
                context=context,
                problem=f"URL inválida/placeholder: {url}",
                spec_reference="article.quality_rules.url_validation",
                correction="Use URL real com HTTPS que não seja localhost, example.com ou seu-repositorio",
            )

    def validate_min_error_markers(self, context: dict):
        error_markers = re.findall(r'(erro:|error:|armadilha|problema:|⚠|sintoma:)', context["text_lower"])
        min_errors = self.rules.get("min_errors", 2)
        if len(error_markers) >= min_errors:
            return
        context["warnings"].append(
            f"Poucos erros documentados: {len(error_markers)}, recomendado {min_errors}"
        )

    def validate_solution_content(self, context: dict):
        min_solution_chars = self.rules.get("min_solution_chars", 20)
        armadilha_blocks = re.findall(
            r'(?:solução|solu[çc][aã]o)[:\s]*```[a-z]*\n(.*?)```',
            context["artigo"],
            re.IGNORECASE | re.DOTALL,
        )
        for block in armadilha_blocks:
            content = block.strip()
            if len(content) >= min_solution_chars:
                continue
            self.add_problem(
                context=context,
                problem=(
                    f"Solução vazia/genérica em armadilha: "
                    f"'{content[:40]}' ({len(content)} chars, mínimo {min_solution_chars})"
                ),
                spec_reference="article.quality_rules.solution_content",
                correction=f"Forneça solução com código/comandos reais (mínimo {min_solution_chars} caracteres)",
            )

    def validate_hardware_sanity(self, context: dict):
        hardware_rules = self.rules.get("hardware_sanity")
        if not hardware_rules:
            return
        max_ram_minimum_gb = hardware_rules.get("max_ram_minimum_gb", 2)
        ram_values = re.findall(r'(\d+)\s*gb', context["text_lower"])
        for ram_value in ram_values:
            if int(ram_value) <= max_ram_minimum_gb * 2:
                continue
            context["warnings"].append(
                f"RAM suspeito: {ram_value}GB — verifique se está correto"
            )

    def validate_code_blocks(self, context: dict):
        code_blocks = re.findall(r'```', context["artigo"])
        if len(code_blocks) >= 4:
            return
        context["warnings"].append(
            "Poucos blocos de código — verifique se comandos foram incluídos"
        )

    def validate_table_cells(self, context: dict):
        table_rows = re.findall(r'\|(.+)\|', context["artigo"])
        for row in table_rows:
            cells = [cell.strip() for cell in row.split('|')]
            has_empty_data_cell = any(cell == '' for cell in cells if not re.match(r'^-+$', cell))
            if not has_empty_data_cell:
                continue
            context["warnings"].append("Tabela com célula vazia detectada")
            return

    def validate_command_integrity(self, context: dict):
        bash_blocks = re.findall(r'```bash\s*\n(.*?)```', context["artigo"], re.IGNORECASE | re.DOTALL)
        for block in bash_blocks:
            command_lines = [
                command_line.strip()
                for command_line in block.splitlines()
                if command_line.strip() and not command_line.strip().startswith("#")
            ]
            for command_line in command_lines:
                if re.search(r'--endpoint-url=\s*(?:$|--)', command_line):
                    self.add_problem(
                        context=context,
                        problem=f"Comando incompleto: endpoint-url vazio em '{command_line}'",
                        spec_reference="article.quality_rules.command_integrity",
                        correction=(
                            "Preencha --endpoint-url com URL real (ex: http://localhost:4566) "
                            "ou remova o parâmetro."
                        ),
                    )
                if re.fullmatch(r'curl(?:\s+[-\w]+(?:\s+\S+)*)?\s*', command_line) and not re.search(
                    r'https?://', command_line
                ):
                    self.add_problem(
                        context=context,
                        problem=f"Comando incompleto: curl sem URL em '{command_line}'",
                        spec_reference="article.quality_rules.command_integrity",
                        correction=(
                            "Inclua URL completa no curl (ex: curl http://localhost:4566/health) "
                            "ou remova o comando."
                        ),
                    )

        if re.search(r'QueueUrl["\']?\s*:\s*["\']\s*}', context["artigo"], re.IGNORECASE):
            self.add_problem(
                context=context,
                problem="Exemplo inválido: QueueUrl vazio/incompleto no resultado esperado",
                spec_reference="article.quality_rules.command_integrity",
                correction=(
                    "Substitua por retorno textual sem placeholder "
                    "(ex: 'campo QueueUrl retornado com sucesso')."
                ),
            )

    def validate_min_tips(self, context: dict):
        min_tips = self.rules.get("min_tips", 3)
        optimization_section = re.search(
            r'#\s*(?:otimiza|dica|performance)[^\n]*\n(.*?)(?=#\s|\Z)',
            context["artigo"],
            re.IGNORECASE | re.DOTALL
        )
        if not optimization_section:
            self.add_problem(
                context=context,
                problem=f"Seção de otimizações/dicas não encontrada ou vazia",
                spec_reference="article.quality_rules.min_tips",
                correction=f"Adicione seção '## Dicas de Otimização' com mínimo {min_tips} dicas listadas",
            )
            return

        tips_text = optimization_section.group(1)
        # Match both bullet points (- *) and numbered lists (1. 2. etc)
        tip_items = re.findall(r'(?:^|\n)\s*(?:[-*]|\d+\.)\s+\w', tips_text, re.MULTILINE)
        tip_count = len(tip_items)

        if tip_count < min_tips:
            self.add_problem(
                context=context,
                problem=f"Dicas insuficientes: {tip_count} dicas encontradas, mínimo {min_tips}",
                spec_reference="article.quality_rules.min_tips",
                correction=f"Adicione mais {min_tips - tip_count} dica(s) na seção de otimizações",
            )

    def problems_as_prompt(self, result):
        if result.passed:
            return ""
        lines = ["O artigo tem os seguintes problemas que DEVEM ser corrigidos:"]
        for index, problem in enumerate(result.problems, 1):
            lines.append(f"{index}. {problem}")
        lines.append(
            "\nReescreva o artigo corrigindo APENAS esses problemas."
        )
        lines.append("Mantenha todo o conteúdo existente que está correto.")
        lines.append(
            "LEMBRETE: Se não tem dado, OMITA a linha. "
            "Nunca escreva placeholders."
        )
        return "\n".join(lines)
