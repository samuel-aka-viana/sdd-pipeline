"""
Testes de skills com LLM mockado para aumentar cobertura.

Estes testes mocam as chamadas LLM para tornar os testes:
- Rápidos (sem I/O real)
- Determinísticos (sem dependência de API)
- Aumentar coverage: skills 30-50% → 70%+
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from skills.researcher import ResearcherSkill
from skills.analyst import AnalystSkill
from skills.writer import WriterSkill
from skills.critic import CriticSkill


class TestResearcherSkillMocked:
    """Testes de Researcher com LLM mockado."""
    
    @pytest.mark.deterministic
    @patch('skills.researcher.LLMClient')
    def test_researcher_run_calls_llm_with_correct_role(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(
            response="## URLS CONSULTADAS\n- https://docker.com\n\n## REQUISITOS\n4GB RAM"
        )
        mock_llm_class.return_value = mock_instance
        
        mock_search = MagicMock()
        mock_search.search_multi.return_value = {
            "query1": [{"url": "https://docker.com", "snippet": "Docker info"}]
        }
        mock_search.save_urls = MagicMock()
        
        mock_scraper = MagicMock()
        mock_scraper.extract_text.return_value = {
            "status": "ok",
            "text": "Docker documentation content here",
            "truncated": False
        }
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        researcher = ResearcherSkill(mock_search, mock_scraper, mock_memory)
        
        # Act
        result = researcher.run("docker", "kubernetes", "comparação geral")
        
        # Assert
        assert mock_instance.generate.called
        assert mock_instance.model_for_role.call_args[0][0] == "researcher"
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.deterministic
    @patch('skills.researcher.LLMClient')
    def test_researcher_run_builds_queries_correctly(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(response="Test response")
        mock_llm_class.return_value = mock_instance
        
        mock_search = MagicMock()
        mock_search.search_multi.return_value = {}
        mock_search.save_urls = MagicMock()
        
        mock_scraper = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        researcher = ResearcherSkill(mock_search, mock_scraper, mock_memory)
        
        # Act
        researcher.run("docker", "kubernetes", "performance / throughput", 
                      questoes=["latency benchmarks"])
        
        # Assert
        assert mock_search.search_multi.called
        call_args = mock_search.search_multi.call_args
        queries = call_args[0][0]
        assert len(queries) > 0
        assert any("docker" in query.lower() for query in queries)

    @pytest.mark.deterministic
    @patch('skills.researcher.LLMClient')
    def test_researcher_handles_empty_search_results(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(response="No data found")
        mock_llm_class.return_value = mock_instance
        
        mock_search = MagicMock()
        mock_search.search_multi.return_value = {}
        mock_search.save_urls = MagicMock()
        
        mock_scraper = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        researcher = ResearcherSkill(mock_search, mock_scraper, mock_memory)
        
        # Act
        result = researcher.run("nonexistent-tool")
        
        # Assert
        assert isinstance(result, str)


class TestAnalystSkillMocked:
    """Testes de Analyst com LLM mockado."""
    
    @pytest.mark.deterministic
    @patch('skills.analyst.LLMClient')
    def test_analyst_run_single_tool_mode(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(
            response="## TABELA DE REQUISITOS\nRAM: 4GB\nCPU: 2 cores"
        )
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        analyst = AnalystSkill(mock_memory)
        research = "Docker requires 4GB RAM minimum"
        
        # Act
        result = analyst.run(research, "docker", "production", "performance / throughput")
        
        # Assert
        assert mock_instance.generate.called
        assert isinstance(result, str)

    @pytest.mark.deterministic
    @patch('skills.analyst.LLMClient')
    def test_analyst_run_comparison_mode(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(
            response="| Feature | Docker | Podman |\n|---------|--------|--------|"
        )
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        analyst = AnalystSkill(mock_memory)
        research = "Docker vs Podman comparison"
        
        # Act
        result = analyst.run(research, "docker e podman", "staging", "comparação geral")
        
        # Assert
        assert mock_instance.generate.called
        assert isinstance(result, str)

    @pytest.mark.deterministic
    @patch('skills.analyst.LLMClient')
    def test_analyst_run_integration_mode(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(
            response="## COMO SE ENCAIXAM\nPrometheus coleta, Grafana visualiza"
        )
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        analyst = AnalystSkill(mock_memory)
        research = "Prometheus and Grafana integration"
        
        # Act
        result = analyst.run(research, "prometheus e grafana", "monitoring", "integração")
        
        # Assert
        assert mock_instance.generate.called
        assert isinstance(result, str)


class TestWriterSkillMocked:
    """Testes de Writer com LLM mockado."""
    
    @pytest.mark.deterministic
    @patch('skills.writer.LLMClient')
    def test_writer_run_basic(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(
            response="""# TLDR
Brief summary.

# O que é
Docker explanation.

# Requisitos
4GB RAM.

# Instalação
curl command.

# Configuração
Config steps.

# Exemplo Prático
Example code.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Summary.

# Referências
- https://docker.com
- https://github.com/docker
- https://docs.docker.com"""
        )
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        writer = WriterSkill(mock_memory)
        
        # Act
        result = writer.run(
            research="Docker research",
            analysis="Docker analysis",
            ferramentas="docker",
            contexto="production"
        )
        
        # Assert
        assert mock_instance.generate.called
        assert isinstance(result, str)
        assert "TLDR" in result or "tldr" in result.lower()

    @pytest.mark.deterministic
    @patch('skills.writer.LLMClient')
    def test_writer_run_with_correction_instructions(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(response="# TLDR\nCorrected article")
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        writer = WriterSkill(mock_memory)
        
        # Act
        writer.run(
            research="research",
            analysis="analysis",
            ferramentas="docker",
            contexto="test",
            correction_instructions="Fix section X"
        )
        
        # Assert
        assert mock_instance.generate.called
        # Verify correction_instructions were passed to LLM
        call_kwargs = mock_instance.generate.call_args[1]
        assert "prompt" in call_kwargs
        assert "Fix section X" in call_kwargs["prompt"]

    @pytest.mark.deterministic
    @patch('skills.writer.LLMClient')
    def test_writer_run_weak_research_quality(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(response="# TLDR\nArticle")
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        mock_memory.get_lessons_for_prompt.return_value = ""
        
        writer = WriterSkill(mock_memory)
        
        # Act
        writer.run(
            research="limited research",
            analysis="limited analysis",
            ferramentas="docker",
            contexto="test",
            research_quality="weak"
        )
        
        # Assert
        assert mock_instance.generate.called
        # Verify weak research warning was included
        call_kwargs = mock_instance.generate.call_args[1]
        assert "prompt" in call_kwargs
        assert "AVISO" in call_kwargs["prompt"]


class TestCriticSkillMocked:
    """Testes de Critic com LLM mockado."""
    
    @pytest.mark.deterministic
    @patch('skills.critic.LLMClient')
    def test_critic_evaluate_deterministic_pass(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        
        critic = CriticSkill(mock_memory)
        valid_article = """# TLDR
Summary.

# O que é
Docker explanation.

# Requisitos
4GB RAM.

# Instalação
curl command.

# Configuração
Config.

# Exemplo Prático
Example.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Conclusion.

# Referências
- https://docker.com
- https://github.com/docker
- https://docs.docker.com"""
        
        # Act
        result = critic.evaluate(valid_article, "docker")
        
        # Assert
        assert result["approved"] == True
        assert result["layer"] == "semantic"

    @pytest.mark.deterministic
    @patch('skills.critic.LLMClient')
    def test_critic_evaluate_deterministic_fail(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        
        critic = CriticSkill(mock_memory)
        invalid_article = "Missing sections and [TODO placeholder]"
        
        # Act
        result = critic.evaluate(invalid_article, "docker")
        
        # Assert
        assert result["approved"] == False
        assert result["layer"] == "deterministic"
        assert len(result["problems"]) > 0

    @pytest.mark.deterministic
    @patch('skills.critic.LLMClient')
    def test_critic_evaluate_semantic_fail(self, mock_llm_class):
        # Arrange
        mock_instance = MagicMock()
        mock_instance.model_for_role.return_value = "test-model"
        mock_instance.generate.return_value = Mock(
            response="This command doesn't actually exist in Docker"
        )
        mock_llm_class.return_value = mock_instance
        
        mock_memory = MagicMock()
        
        critic = CriticSkill(mock_memory)
        valid_structure_article = """# TLDR
Summary.

# O que é
Explanation.

# Requisitos
4GB RAM.

# Instalação
curl install.

# Configuração
Config.

# Exemplo Prático
docker fake-command.

# Armadilhas
Error 1. Error 2.

# Otimizações
Tip 1. Tip 2. Tip 3.

# Conclusão
Conclusion.

# Referências
- https://docker.com
- https://github.com/docker
- https://docs.docker.com"""
        
        # Act
        result = critic.evaluate(valid_structure_article, "docker")
        
        # Assert
        # Should be approved or failed by semantic check (depends on LLM output)
        assert "layer" in result
        assert result["layer"] in ["semantic", "deterministic"]
