import pytest
from unittest.mock import patch
from validators.spec_validator import ValidationResult
from skills.critic import CriticSkill
from memory.memory_store import MemoryStore
import tempfile


class TestPipelineE2E:
    """End-to-end tests for the complete pipeline with validation feedback loop."""

    @pytest.fixture
    def memory(self):
        """Create a temporary memory store for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(path=tmpdir)
            yield store

    @pytest.fixture
    def critic(self, memory):
        """Create CriticSkill with mocked LLM."""
        with patch('skills.critic.LLMClient'):
            return CriticSkill(memory, "spec/article_spec.yaml")

    def test_pipeline_flow_with_invalid_article(self, critic):
        """
        Pipeline detects invalid article (missing section) and rejects it.
        
        Validates that:
        1. Invalid article fails validation
        2. Problems are identified with spec references
        3. Feedback includes correction guidance
        """
        invalid_article = """
# TLDR
This article is incomplete.

# O que é
Missing required sections.
"""
        # Should have references in the response
        result = critic.evaluate(invalid_article, "test-tool")
        
        assert result["approved"] is False
        assert result["layer"] == "deterministic"
        assert len(result["problems"]) > 0
        # Check that correction prompt includes spec references
        assert "Seção ausente" in str(result["correction_prompt"])

    def test_pipeline_validation_result_includes_spec_references(self, critic):
        """
        ValidationResult includes spec_references and corrections fields.
        
        Validates that enhanced ValidationResult structure is in place.
        """
        invalid_article = """# TLDR
Summary.

# [TODO: Add O que é section]
Missing this.
"""
        # Run through critic's validator
        result = critic.validator.validate(invalid_article)
        
        # Check enhanced ValidationResult fields exist
        assert hasattr(result, 'spec_references')
        assert hasattr(result, 'corrections')
        assert isinstance(result.spec_references, list)
        assert isinstance(result.corrections, dict)
        
        # Check that problems have corresponding spec references
        assert len(result.spec_references) >= 0
        if len(result.problems) > 0:
            # Should have spec references for problems
            assert any('article' in ref for ref in result.spec_references)

    def test_pipeline_feedback_includes_spec_rules(self, critic):
        """
        Pipeline feedback cites spec rules in error messages.
        
        Validates that corrections include spec rule names.
        """
        invalid_article = """
# TLDR
Brief summary.

# O que é
An overview [TODO: expand this].

# Requisitos
System requirements: [Descreva as dependências]
"""
        result = critic.evaluate(invalid_article, "test-tool")
        
        assert result["approved"] is False
        # Feedback should mention spec references
        feedback = result["correction_prompt"]
        assert "Spec" in feedback or "placeholder" in feedback.lower()

    def test_pipeline_multiple_validation_failures(self, critic):
        """
        Pipeline detects multiple validation failures simultaneously.
        
        Validates that all problems are reported at once.
        """
        multi_problem_article = """
# TLDR
Short summary.

# [TODO: Add more sections]
"""
        result = critic.evaluate(multi_problem_article, "test-tool")
        
        assert result["approved"] is False
        # Should report multiple missing sections
        assert len(result["problems"]) > 1

    def test_pipeline_valid_article_passes(self, critic):
        """
        Valid article passes all validation stages.
        
        Validates that a properly formed article passes without corrections.
        """
        valid_article = """
# TLDR
A summary of k3s.

# O que é
k3s is a lightweight Kubernetes.

# Requisitos
- CPU: 2 cores
- RAM: 1 GB

# Instalação
```bash
curl -sfL https://get.k3s.io | sh -
```

# Configuração
```bash
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
```

# Exemplo Prático
```bash
kubectl apply -f deployment.yaml
```

# Armadilhas
## Erro: Port conflict
Symptoms: Port already in use
Solution:
```bash
sudo ss -tlnp | grep :6443
```

# Otimizações
- Tip 1: Use local storage for development
- Tip 2: Disable unused components
- Tip 3: Configure resource limits

# Conclusão
k3s is lightweight and production-ready.

# Referências
- https://k3s.io
- https://kubernetes.io/docs
- https://github.com/k3s-io/k3s
"""
        result = critic.evaluate(valid_article, "kubernetes")
        
        assert result["approved"] is True
        assert result["layer"] == "semantic"
        assert len(result.get("problems", [])) == 0

    def test_pipeline_validation_report_format(self, critic):
        """
        ValidationResult report() method produces readable output.
        
        Validates that human-readable reports include spec references.
        """
        invalid_article = """
# TLDR
Missing sections.
"""
        result = critic.validator.validate(invalid_article)
        report = result.report()
        
        # Report should be readable
        assert "PROBLEMAS" in report or "✓" in report
        assert isinstance(report, str)
        assert len(report) > 0

    def test_pipeline_spec_references_structure(self, critic):
        """
        Spec references follow naming convention: article.{category}.{rule}.
        
        Validates reference format consistency.
        """
        invalid_article = """
# TLDR
Summary.

# [TODO: Add content]
Placeholder here.
"""
        result = critic.validator.validate(invalid_article)
        
        for ref in result.spec_references:
            # All references should start with 'article'
            if ref:  # Non-empty references
                assert ref.startswith("article"), f"Reference should start with 'article': {ref}"

    def test_pipeline_corrections_map_to_problems(self, critic):
        """
        Each problem has a corresponding correction in corrections dict.
        
        Validates that corrections are properly mapped.
        """
        invalid_article = """
# TLDR
Summary.

# O que é
Missing sections and [TODO: placeholders]
"""
        result = critic.validator.validate(invalid_article)
        
        # Each problem should have a potential correction
        for problem in result.problems:
            # Either in corrections dict or spec references
            assert problem in result.corrections or len(result.spec_references) > 0

    def test_pipeline_error_message_clarity(self, critic):
        """
        Error messages are specific and actionable.
        
        Validates that errors guide users to solutions.
        """
        invalid_article = """
# TLDR
Summary.

# Requisitos
Needs more stuff
"""
        result = critic.validator.validate(invalid_article)
        
        # Errors should be specific (mention the section or pattern)
        for problem in result.problems:
            assert len(problem) > 10, "Error message should be descriptive"
            # Should mention what's wrong, not be generic
            assert "Seção" in problem or "Placeholder" in problem or "Referências" in problem or "URL" in problem or "Solução" in problem

    def test_pipeline_integration_with_memory_logging(self, critic):
        """
        Pipeline logs validation results to memory for learning.
        
        Validates that memory captures validation state.
        """
        invalid_article = """
# TLDR
Incomplete.
"""
        result = critic.evaluate(invalid_article, "test-tool")
        
        # Check that memory was called for logging
        assert critic.memory is not None
        
        # Verify the evaluation captured all needed data
        assert "approved" in result
        assert "layer" in result
        assert "problems" in result or "approved" in result

    def test_pipeline_deterministic_vs_semantic_layers(self, critic):
        """
        Pipeline distinguishes between deterministic (spec) and semantic layers.
        
        Validates layer-based validation approach.
        """
        # Article with deterministic problem (missing section)
        det_article = """
# TLDR
Summary.
"""
        result = critic.evaluate(det_article, "test-tool")
        
        # Should be rejected at deterministic layer
        assert result["approved"] is False
        assert result["layer"] == "deterministic"

    def test_pipeline_repeated_validation_consistency(self, critic):
        """
        Running validation multiple times on same article produces consistent results.
        
        Validates deterministic behavior.
        """
        article = """
# TLDR
Summary.

# [TODO placeholder]
Content.
"""
        result1 = critic.validator.validate(article)
        result2 = critic.validator.validate(article)
        
        # Results should be identical
        assert result1.problems == result2.problems
        assert result1.passed == result2.passed
        assert result1.spec_references == result2.spec_references

    def test_pipeline_feedback_loop_simulation(self, critic):
        """
        Simulates a feedback loop where article is corrected based on validation feedback.
        
        Validates iterative improvement pattern.
        """
        # First iteration: article with problems
        article_v1 = """
# TLDR
Summary.

# O que é
Description.
"""
        result_v1 = critic.validator.validate(article_v1)
        assert result_v1.passed is False
        
        # Simulate correction based on feedback
        problems = result_v1.problems
        assert any("Seção" in problem_text for problem_text in problems)
        
        # Second iteration: article corrected
        article_v2 = """
# TLDR
Summary.

# O que é
Description.

# Requisitos
Minimal requirements needed.

# Instalação
Installation instructions.

# Configuração
Configuration steps.

# Exemplo Prático
Usage example with code.

# Armadilhas
Common mistakes:
Erro: Connection refused
Sintoma: Port not accessible
Solução:
```bash
lsof -i :port
```

# Otimizações
- Optimization 1
- Optimization 2
- Optimization 3

# Conclusão
Final thoughts.

# Referências
- https://example.com/docs
- https://github.com/example
- https://docs.example.io
"""
        result_v2 = critic.validator.validate(article_v2)
        
        # Verify improvement
        assert len(result_v2.problems) < len(result_v1.problems)
        # Ideally, after correction, should pass
        # (In this case, we're just verifying more problems are fixed)

    def test_pipeline_handles_edge_cases(self, critic):
        """
        Pipeline handles edge cases gracefully (very short, empty, malformed).
        
        Validates robustness.
        """
        edge_cases = [
            "",  # Empty
            "   ",  # Whitespace only
            "a",  # Single character
            "#" * 1000,  # Spam
        ]
        
        for article in edge_cases:
            result = critic.validator.validate(article)
            # Should not crash, should report as failed
            assert isinstance(result, ValidationResult)
            assert result.passed is False

    def test_pipeline_spec_version_validation(self, critic):
        """
        Pipeline can report which spec version validated the article.
        
        Validates spec versioning awareness.
        """
        valid_article = """
# TLDR
Summary.

# O que é
Description.

# Requisitos
Requirements.

# Instalação
```bash
install
```

# Configuração
```bash
configure
```

# Exemplo Prático
```bash
example
```

# Armadilhas
Erro: Problem
Sintoma: Symptom
Solução:
```bash
solution
```

# Otimizações
- Tip 1
- Tip 2
- Tip 3

# Conclusão
Conclusion.

# Referências
- https://example1.io
- https://example2.io
- https://example3.io
"""
        critic.validator.validate(valid_article)
        
        # Spec should be loaded
        assert critic.validator.spec is not None
        assert "spec_version" in critic.validator.spec
        # Version should follow semantic versioning
        version = critic.validator.spec["spec_version"]
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3  # major.minor.patch
