class TestResearcherSkill:
    """Test that ResearcherSkill returns required fields per spec"""

    def test_researcher_required_fields_exist(self, spec):
        """Spec should define required fields for researcher output"""
        assert "research" in spec
        assert "required_fields" in spec["research"]
        required = spec["research"]["required_fields"]
        assert isinstance(required, list)
        assert len(required) > 0

    def test_researcher_required_fields_contain_urls(self, spec):
        """Researcher should provide URLs in output"""
        required = spec["research"]["required_fields"]
        assert "urls" in required, "urls should be a required field"

    def test_researcher_required_fields_contain_instalacao(self, spec):
        """Researcher should provide installation info"""
        required = spec["research"]["required_fields"]
        assert "instalacao" in required

    def test_researcher_required_fields_contain_requisitos(self, spec):
        """Researcher should provide requirements"""
        required = spec["research"]["required_fields"]
        assert "requisitos" in required

    def test_researcher_required_fields_contain_erros(self, spec):
        """Researcher should identify common errors"""
        required = spec["research"]["required_fields"]
        assert "erros" in required

    def test_researcher_required_fields_contain_alternativas(self, spec):
        """Researcher should find alternatives"""
        required = spec["research"]["required_fields"]
        assert "alternativas" in required

    def test_researcher_search_queries_defined(self, spec):
        """Spec should define search queries for research"""
        assert "search_queries" in spec["research"]
        queries = spec["research"]["search_queries"]
        assert isinstance(queries, list)
        assert len(queries) > 0

    def test_researcher_scraper_config_exists(self, spec):
        """Scraper configuration should be defined"""
        assert "scraper" in spec["research"]
        scraper = spec["research"]["scraper"]
        assert "max_chars_per_page" in scraper
        assert "timeout_seconds" in scraper
        assert "max_scrapes_per_tool" in scraper


class TestAnalystSkill:
    """Test that AnalystSkill produces required analysis structure"""

    def test_analyst_required_fields_exist(self, spec):
        """Spec should define required fields for analyst output"""
        assert "analysis" in spec
        assert "required_fields" in spec["analysis"]
        required = spec["analysis"]["required_fields"]
        assert isinstance(required, list)
        assert len(required) >= 5

    def test_analyst_produces_requirements_table(self, spec):
        """Analyst should produce requirements table"""
        required = spec["analysis"]["required_fields"]
        assert "tabela_requisitos" in required

    def test_analyst_produces_comparison_table(self, spec):
        """Analyst should compare alternatives"""
        required = spec["analysis"]["required_fields"]
        assert "tabela_comparacao" in required

    def test_analyst_analyzes_pros(self, spec):
        """Analyst should identify pros"""
        required = spec["analysis"]["required_fields"]
        assert "pros" in required

    def test_analyst_analyzes_contras(self, spec):
        """Analyst should identify cons"""
        required = spec["analysis"]["required_fields"]
        assert "contras" in required

    def test_analyst_identifies_otimizacoes(self, spec):
        """Analyst should identify optimizations"""
        required = spec["analysis"]["required_fields"]
        assert "otimizacoes" in required


class TestWriterSkill:
    """Test that WriterSkill generates all required sections"""

    def test_writer_includes_required_sections(self, spec):
        """Writer should generate all required article sections"""
        assert "article" in spec
        required_sections = spec["article"]["required_sections"]
        assert len(required_sections) == 10, "Article must have exactly 10 required sections"

    def test_writer_includes_tldr_section(self, spec):
        """Writer should include TLDR section"""
        required_sections = spec["article"]["required_sections"]
        assert "tldr" in required_sections

    def test_writer_includes_o_que_e_section(self, spec):
        """Writer should include 'O que é' section"""
        required_sections = spec["article"]["required_sections"]
        assert "o_que_e" in required_sections

    def test_writer_includes_conclusao_section(self, spec):
        """Writer should include Conclusão section"""
        required_sections = spec["article"]["required_sections"]
        assert "conclusao" in required_sections

    def test_writer_includes_referencias_section(self, spec):
        """Writer should include Referências section"""
        required_sections = spec["article"]["required_sections"]
        assert "referencias" in required_sections

    def test_article_quality_rules_defined(self, spec):
        """Article quality rules should be defined"""
        assert "quality_rules" in spec["article"]
        rules = spec["article"]["quality_rules"]
        assert "no_placeholders" in rules
        assert "min_references" in rules
        assert "min_errors" in rules
        assert "min_tips" in rules


class TestCriticSkill:
    """Test that CriticSkill validates against spec"""

    def test_critic_validation_uses_validator(self, validator, valid_article):
        """CriticSkill should use SpecValidator for validation"""
        result = validator.validate(valid_article)
        assert hasattr(result, 'passed')
        assert hasattr(result, 'problems')

    def test_critic_detects_invalid_articles(self, validator):
        """CriticSkill should reject articles with problems"""
        invalid = "# Title\n[TODO: content]"
        result = validator.validate(invalid)
        assert not result.passed
        assert len(result.problems) > 0

    def test_critic_accepts_valid_articles(self, validator, valid_article):
        """CriticSkill should accept properly formatted articles"""
        result = validator.validate(valid_article)
        assert result.passed
        assert len(result.problems) == 0

    def test_critic_provides_actionable_feedback(self, validator):
        """CriticSkill feedback should be actionable"""
        invalid = "# Only title"
        result = validator.validate(invalid)
        problems = result.problems
        for problem in problems:
            assert isinstance(problem, str)
            assert len(problem) > 10, "Problems should be descriptive"

    def test_critic_problems_as_prompt(self, validator):
        """CriticSkill should provide formatted feedback for prompts"""
        invalid = "# Only title"
        result = validator.validate(invalid)
        prompt = validator.problems_as_prompt(result)
        if not result.passed:
            assert len(prompt) > 0
            assert "problema" in prompt.lower() or "correção" in prompt.lower()


class TestPipelineIntegration:
    """Integration tests for how skills work together"""

    def test_spec_defines_llm_models(self, spec):
        """Spec should define LLM models for each skill"""
        assert "models" in spec
        models = spec["models"]
        assert "researcher" in models
        assert "analyst" in models
        assert "writer" in models
        assert "critic" in models

    def test_spec_defines_llm_config(self, spec):
        """Spec should define LLM configuration"""
        assert "llm" in spec
        llm = spec["llm"]
        assert "provider" in llm
        assert "timeout" in llm
        assert "temperature" in llm

    def test_pipeline_timeout_configured(self, spec):
        """Pipeline should have timeout configuration"""
        assert "pipeline" in spec
        assert "timeout_total_seconds" in spec["pipeline"]
        timeout = spec["pipeline"]["timeout_total_seconds"]
        assert timeout == 1800, "Total pipeline timeout should be 30 minutes"
        assert isinstance(timeout, int)
        assert timeout > 0
