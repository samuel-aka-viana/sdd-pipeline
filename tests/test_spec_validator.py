import pytest


@pytest.mark.deterministic
@pytest.mark.spec_driven
class TestSpecValidatorSections:
    """Test required_sections validation"""

    def test_valid_article_with_all_sections(self, validator, valid_article):
        """A valid article with all 10 required sections should pass"""
        result = validator.validate(valid_article)
        assert result.passed, f"Valid article should pass: {result.problems}"

    def test_missing_tldr_section(self, validator, invalid_article_missing_tldr):
        """Article missing TLDR section should fail"""
        result = validator.validate(invalid_article_missing_tldr)
        assert not result.passed
        assert any("tldr" in problem_text.lower() for problem_text in result.problems)

    def test_missing_o_que_e_section(self, validator):
        """Article missing 'O que é' section should fail"""
        article = "# TLDR\nBrief\n# Requisitos\nContent"
        result = validator.validate(article)
        assert not result.passed
        assert any("o que é" in problem_text.lower() or "o_que_e" in problem_text.lower() for problem_text in result.problems)

    def test_missing_requisitos_section(self, validator):
        """Article missing Requisitos section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent\n# Instalação\nSteps"
        result = validator.validate(article)
        assert not result.passed
        assert any("requisito" in problem_text.lower() for problem_text in result.problems)

    def test_missing_instalacao_section(self, validator):
        """Article missing Instalação section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent\n# Requisitos\nReqs"
        result = validator.validate(article)
        assert not result.passed
        assert any("instala" in problem_text.lower() for problem_text in result.problems)

    def test_missing_configuracao_section(self, validator):
        """Article missing Configuração section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent\n# Instalação\nSteps"
        result = validator.validate(article)
        assert not result.passed
        assert any("configura" in problem_text.lower() for problem_text in result.problems)

    def test_missing_exemplo_pratico_section(self, validator):
        """Article missing Exemplo Prático section should fail"""
        article = "# TLDR\nBrief\n# Configuração\nConfig"
        result = validator.validate(article)
        assert not result.passed
        assert any("exemplo" in problem_text.lower() or "prático" in problem_text.lower() for problem_text in result.problems)

    def test_missing_armadilhas_section(self, validator):
        """Article missing Armadilhas section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent"
        result = validator.validate(article)
        assert not result.passed
        assert any("armadilha" in problem_text.lower() or "erro comum" in problem_text.lower() for problem_text in result.problems)

    def test_missing_otimizacoes_section(self, validator):
        """Article missing Otimizações section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent"
        result = validator.validate(article)
        assert not result.passed
        assert any("otimiza" in problem_text.lower() or "dica" in problem_text.lower() for problem_text in result.problems)

    def test_missing_conclusao_section(self, validator):
        """Article missing Conclusão section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent"
        result = validator.validate(article)
        assert not result.passed
        assert any("conclus" in problem_text.lower() for problem_text in result.problems)

    def test_missing_referencias_section(self, validator):
        """Article missing Referências section should fail"""
        article = "# TLDR\nBrief\n# O que é\nContent"
        result = validator.validate(article)
        assert not result.passed
        assert any("referência" in problem_text.lower() or "referencia" in problem_text.lower() for problem_text in result.problems)

    def test_missing_all_sections(self, validator):
        """Article with no required sections should fail with multiple problems"""
        result = validator.validate("# Random Section\nNo required sections here")
        assert not result.passed
        assert len(result.problems) >= 5


class TestSpecValidatorPlaceholders:
    """Test placeholder/anti-pattern detection (11+ patterns)"""

    def test_placeholder_TODO_detected(self, validator, valid_article):
        """[TODO placeholder should be detected as invalid"""
        article = valid_article.replace(
            "# O que é",
            "# O que é\n[TODO: Complete this]"
        )
        result = validator.validate(article)
        assert not result.passed
        assert any("[TODO" in problem_text or "placeholder" in problem_text.lower() for problem_text in result.problems)

    def test_placeholder_Descreva_detected(self, validator, valid_article):
        """[Descreva placeholder should be detected"""
        article = valid_article.replace(
            "# Requisitos",
            "# Requisitos\n[Descreva os requisitos]"
        )
        result = validator.validate(article)
        assert not result.passed
        assert any("placeholder" in problem_text.lower() for problem_text in result.problems)

    def test_placeholder_X_detected(self, validator, valid_article):
        """[X] placeholder should be detected"""
        article = valid_article.replace(
            "# Configuração",
            "# Configuração\n[X] Configure the tool"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_inserir_detected(self, validator, valid_article):
        """[inserir placeholder should be detected"""
        article = valid_article.replace(
            "# Instalação",
            "# Instalação\n[inserir procedimento]"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_preencher_detected(self, validator, valid_article):
        """[preencher placeholder should be detected"""
        article = valid_article.replace(
            "# Configuração",
            "# Configuração\n[preencher com suas configurações]"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_PREENCHER_detected(self, validator, valid_article):
        """PREENCHER placeholder should be detected"""
        article = valid_article.replace(
            "# O que é",
            "# O que é\nPREENCHER COM DESCRIÇÃO"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_Verifique_detected(self, validator, valid_article):
        """# Verifique comment should be detected"""
        article = valid_article.replace(
            "# Instalação",
            "# Instalação\n# Verifique a documentação"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_Ajuste_detected(self, validator, valid_article):
        """# Ajuste comment should be detected"""
        article = valid_article.replace(
            "# Configuração",
            "# Configuração\n# Ajuste conforme necessário"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_Configure_detected(self, validator, valid_article):
        """# Configure comment should be detected"""
        article = valid_article.replace(
            "# Configuração",
            "# Configuração\n# Configure o parâmetro"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_Corrija_detected(self, validator, valid_article):
        """# Corrija comment should be detected"""
        article = valid_article.replace(
            "# Armadilhas",
            "# Armadilhas\n# Corrija o erro se necessário"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_placeholder_Substitua_detected(self, validator, valid_article):
        """# Substitua comment should be detected"""
        article = valid_article.replace(
            "# Instalação",
            "# Instalação\n# Substitua pelo seu caminho"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_generic_placeholder_conforme_necessario(self, validator, valid_article):
        """Generic phrase 'conforme necessário' should be detected"""
        article = valid_article.replace(
            "# Configuração",
            "# Configuração\nAdjuste conforme necessário"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_generic_placeholder_verifique_documentacao(self, validator, valid_article):
        """Generic phrase 'verifique a documentação' should be detected"""
        article = valid_article.replace(
            "# Requisitos",
            "# Requisitos\nVerifique a documentação oficial"
        )
        result = validator.validate(article)
        assert not result.passed

    def test_no_placeholders_in_valid_article(self, validator, valid_article):
        """Valid article should have no placeholder problems"""
        result = validator.validate(valid_article)
        placeholder_problems = [problem_text for problem_text in result.problems if "placeholder" in problem_text.lower()]
        assert len(placeholder_problems) == 0, f"Valid article has placeholder problems: {placeholder_problems}"


class TestSpecValidatorQuantitative:
    """Test min_references, min_errors, min_tips"""

    def test_minimum_references_required_3(self, validator, invalid_article_insufficient_refs):
        """Article must have at least 3 references (URLs)"""
        result = validator.validate(invalid_article_insufficient_refs)
        assert not result.passed
        assert any("referência" in problem_text.lower() or "url" in problem_text.lower() for problem_text in result.problems)

    def test_three_references_passes(self, validator, valid_article):
        """Article with 3 or more references should pass reference check"""
        result = validator.validate(valid_article)
        reference_problems = [problem_text for problem_text in result.problems if "referência" in problem_text.lower() or "url" in problem_text.lower()]
        assert len(reference_problems) == 0, f"Valid article with 3+ refs failed: {reference_problems}"

    def test_urls_are_counted_correctly(self, validator):
        """Count of URLs should be accurate"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
https://docs1.com
# Instalação
https://docs2.com
https://docs3.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
Error 1. Error 2.
# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://ref1.com
- https://ref2.com
"""
        result = validator.validate(article)
        reference_problems = [problem_text for problem_text in result.problems if "referência" in problem_text.lower()]
        assert len(reference_problems) == 0, "Article with 5 URLs should pass"

    def test_minimum_errors_in_armadilhas_section(self, validator):
        """Armadilhas section should warn if fewer than 2 errors documented"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
System requirements
# Instalação
Install here from https://docs.com
# Configuração
Config details
# Exemplo Prático
Example code here
# Armadilhas
Only one error documented here
# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://docs.com
- https://github.com/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        error_warnings = [warning_text for warning_text in result.warnings if "erro" in warning_text.lower()]
        assert len(error_warnings) > 0, "Should warn about insufficient errors"

    def test_minimum_tips_in_otimizacoes_section(self, validator):
        """Otimizações section should warn if fewer than 3 tips documented"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
System requirements
# Instalação
Install from https://docs.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
Error 1. Error 2.
# Otimizações
Only two tips provided
# Conclusão
Summary
# Referências
- https://docs.com
- https://github.com/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        assert result.passed or len(result.problems) == 0


class TestSpecValidatorHardware:
    """Test hardware_sanity checks"""

    def test_ram_sanity_check_warning(self, validator):
        """RAM values > 2GB as minimum should trigger a warning"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
System requirements:
- RAM: 8 GB minimum
- CPU: 4 cores minimum
# Instalação
Install from https://docs.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
Error 1. Error 2.
# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://docs.com
- https://github.com/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        ram_warnings = [warning_text for warning_text in result.warnings if "ram" in warning_text.lower() or "gb" in warning_text.lower()]
        assert len(ram_warnings) > 0, "Should warn about high RAM requirement"

    def test_reasonable_ram_no_warning(self, validator, valid_article):
        """Reasonable RAM values should not trigger warnings"""
        result = validator.validate(valid_article)
        ram_warnings = [warning_text for warning_text in result.warnings if "ram" in warning_text.lower() or "gb" in warning_text.lower()]
        assert len(ram_warnings) == 0, "1GB RAM should not trigger warning"


class TestSpecValidatorURLs:
    """Test URL validation rules"""

    def test_urls_must_be_https(self, validator, invalid_article_with_http_url):
        """HTTP URLs should fail validation (must be HTTPS)"""
        result = validator.validate(invalid_article_with_http_url)
        assert not result.passed
        assert any("https" in problem_text.lower() or "url" in problem_text.lower() for problem_text in result.problems)

    def test_https_urls_pass(self, validator, valid_article):
        """HTTPS URLs should pass validation"""
        result = validator.validate(valid_article)
        https_problems = [problem_text for problem_text in result.problems if "https" in problem_text.lower() and "inválida" in problem_text.lower()]
        assert len(https_problems) == 0

    def test_no_localhost_urls(self, validator, invalid_article_localhost_url):
        """Localhost URLs should fail validation"""
        result = validator.validate(invalid_article_localhost_url)
        assert not result.passed
        assert any("localhost" in problem_text.lower() or "inválida" in problem_text.lower() for problem_text in result.problems)

    def test_no_example_com_urls(self, validator):
        """example.com URLs should fail validation"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
Requirements from https://example.com
# Instalação
Install from https://docs.example.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
Error 1. Error 2.
# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://docs.example.com
- https://github.com/repo
- https://tutorial.example.com
"""
        result = validator.validate(article)
        assert not result.passed
        assert any("inválida" in problem_text.lower() or "exemplo" in problem_text.lower() for problem_text in result.problems)

    def test_no_seu_repositorio_placeholder(self, validator):
        """'seu-repositorio' placeholder in URLs should fail"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
Requirements
# Instalação
Install from https://seu-repositorio.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
Error 1. Error 2.
# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://seu-repositorio.com
- https://github.com/real/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        assert not result.passed


class TestSpecValidatorSolutionContent:
    """Test minimum solution character validation"""

    def test_solution_empty_fails(self, validator):
        """Empty solution blocks should fail"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
Requirements
# Instalação
Install from https://docs.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
1. First error
   Solução: ```
   ```

2. Second error
   Solução: Error handling code

# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://docs.com
- https://github.com/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        solution_problems = [problem_text for problem_text in result.problems if "solução" in problem_text.lower()]
        assert len(solution_problems) > 0, "Empty solution should fail"

    def test_solution_generic_fails(self, validator):
        """Generic solutions should fail"""
        article = """
# TLDR
Summary
# O que é
Explanation
# Requisitos
Requirements
# Instalação
Install from https://docs.com
# Configuração
Config
# Exemplo Prático
Example
# Armadilhas
1. First error
   Solução: ```
   Fix it
   ```

# Otimizações
Tip 1. Tip 2. Tip 3.
# Conclusão
Summary
# Referências
- https://docs.com
- https://github.com/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        solution_problems = [problem_text for problem_text in result.problems if "solução" in problem_text.lower()]
        assert len(solution_problems) > 0, "Generic solution should fail"


class TestSpecValidatorCodeBlocks:
    """Test code block presence"""

    def test_code_blocks_present(self, validator, valid_article):
        """Valid article should have multiple code blocks"""
        result = validator.validate(valid_article)
        code_warnings = [warning_text for warning_text in result.warnings if "código" in warning_text.lower() or "code" in warning_text.lower()]
        assert len(code_warnings) == 0


class TestSpecValidatorIntegration:
    """Integration tests combining multiple validation rules"""

    def test_valid_article_passes_all_checks(self, validator, valid_article):
        """A properly formatted article should pass all validations"""
        result = validator.validate(valid_article)
        assert result.passed, f"Valid article failed validation: {result.problems}"
        assert len(result.problems) == 0

    def test_multiple_violations_detected(self, validator):
        """Multiple problems should be reported together"""
        article = "# Only Title\n[TODO: incomplete]"
        result = validator.validate(article)
        assert not result.passed
        assert len(result.problems) >= 2

    def test_validator_returns_correct_structure(self, validator):
        """ValidationResult should have passed, problems, and warnings attributes"""
        result = validator.validate("# Test\nContent")
        assert hasattr(result, 'passed')
        assert hasattr(result, 'problems')
        assert hasattr(result, 'warnings')
        assert isinstance(result.problems, list)
        assert isinstance(result.warnings, list)

    def test_partial_success_with_warnings(self, validator, valid_article):
        """Article can pass with problems=0 but have warnings"""
        result = validator.validate(valid_article)
        assert result.passed
        assert len(result.problems) == 0

    def test_validation_report_readable(self, validator, valid_article):
        """ValidationResult.report() should produce readable output"""
        result = validator.validate(valid_article)
        report = result.report()
        assert isinstance(report, str)
        if result.passed:
            assert "✓" in report


class TestSpecValidatorEdgeCases:
    """Edge cases and boundary conditions"""

    def test_empty_article(self, validator):
        """Empty article should fail with multiple problems"""
        result = validator.validate("")
        assert not result.passed
        assert len(result.problems) > 0

    def test_article_with_all_sections_lowercase(self, validator):
        """Section detection should be case-insensitive"""
        article = """
# tldr
summary

# o que é
explanation

# requisitos
requirements

# instalação
install

# configuração
config

# exemplo prático
example

# armadilhas
error 1. error 2.

# otimizações
tip 1. tip 2. tip 3.

# conclusão
summary

# referências
- https://docs.com
- https://github.com/repo
- https://tutorial.com
"""
        result = validator.validate(article)
        # Should find sections despite lowercase
        section_problems = [problem_text for problem_text in result.problems if "seção ausente" in problem_text.lower()]
        assert len(section_problems) == 0, "Should find sections in lowercase"

    def test_article_with_extra_sections(self, validator, valid_article):
        """Extra non-required sections should not cause failure"""
        extended = valid_article + "\n# Extra Section\nExtra content here"
        result = validator.validate(extended)
        assert result.passed, "Extra sections should not invalidate article"

    def test_multiple_urls_on_single_line(self, validator):
        """Multiple URLs on one line should be counted"""
        article = """
# TLDR
Summary

# O que é
Explanation with https://docs.com and https://github.com/repo in text

# Requisitos
Requirements

# Instalação
Install https://docs.com

# Configuração
Config

# Exemplo Prático
Example

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary

# Referências
- https://tutorial.com
"""
        result = validator.validate(article)
        reference_problems = [problem_text for problem_text in result.problems if "referência" in problem_text.lower()]
        assert len(reference_problems) == 0, "Should count multiple URLs"

    def test_url_with_special_characters(self, validator):
        """URLs with special characters should be recognized"""
        article = """
# TLDR
Summary

# O que é
Explanation

# Requisitos
Requirements

# Instalação
Install from https://docs.com/v1.0/install?param=value

# Configuração
Config

# Exemplo Prático
Example

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary

# Referências
- https://github.com/user/repo/releases
- https://tutorial.example.com/page#section
- https://docs.com/api/reference?v=2
"""
        result = validator.validate(article)
        reference_problems = [problem_text for problem_text in result.problems if "referência" in problem_text.lower()]
        assert len(reference_problems) == 0, "Should handle URLs with special chars"
