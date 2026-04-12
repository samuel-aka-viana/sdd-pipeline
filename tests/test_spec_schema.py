import json
import pytest
import yaml
from pathlib import Path
import jsonschema


class TestSpecSchema:
    """Test suite for specification versioning and schema validation."""

    @pytest.fixture
    def schema(self):
        """Load the JSON schema."""
        with open("spec/schema.json") as f:
            return json.load(f)

    @pytest.fixture
    def spec(self):
        """Load the YAML spec."""
        with open("spec/article_spec.yaml") as f:
            return yaml.safe_load(f)

    def test_spec_file_exists(self):
        """Spec file exists and is readable."""
        spec_path = Path("spec/article_spec.yaml")
        assert spec_path.exists(), "spec/article_spec.yaml file not found"

    def test_schema_file_exists(self):
        """Schema file exists and is valid JSON."""
        schema_path = Path("spec/schema.json")
        assert schema_path.exists(), "spec/schema.json file not found"
        
        with open(schema_path) as f:
            schema = json.load(f)
        assert isinstance(schema, dict), "Schema should be a valid JSON object"
        assert "$schema" in schema, "Schema should have $schema field"

    def test_valid_spec_passes_schema(self, spec, schema):
        """Valid spec passes JSON schema validation."""
        try:
            jsonschema.validate(spec, schema)
        except jsonschema.ValidationError as e:
            pytest.fail(f"Spec validation failed: {e.message}")

    def test_spec_has_version(self, spec):
        """Spec includes semantic version."""
        assert "spec_version" in spec, "Spec must have spec_version field"
        assert isinstance(spec["spec_version"], str), "spec_version must be string"
        
        # Check semantic versioning format (major.minor.patch)
        parts = spec["spec_version"].split(".")
        assert len(parts) == 3, "spec_version must be in format major.minor.patch"
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' must be numeric"

    def test_spec_changelog_present(self, spec):
        """Spec includes changelog for version."""
        assert "spec_changelog" in spec, "Spec must have spec_changelog field"
        assert isinstance(spec["spec_changelog"], dict), "spec_changelog must be a dict"
        
        version = spec["spec_version"]
        assert version in spec["spec_changelog"], f"Changelog must have entry for version {version}"
        
        changelog_entry = spec["spec_changelog"][version]
        assert "date" in changelog_entry, "Changelog entry must have date"
        assert "changes" in changelog_entry, "Changelog entry must have changes"
        assert isinstance(changelog_entry["changes"], list), "changes must be a list"

    def test_required_top_level_keys(self, spec, schema):
        """All required top-level keys are present."""
        required_keys = schema.get("required", [])
        assert required_keys, "Schema should define required top-level keys"
        
        for key in required_keys:
            assert key in spec, f"Spec must have required key '{key}'"

    def test_article_section_structure(self, spec):
        """Article section has required structure."""
        assert "article" in spec
        article = spec["article"]
        
        assert "required_sections" in article, "article must have required_sections"
        assert isinstance(article["required_sections"], list), "required_sections must be a list"
        assert len(article["required_sections"]) >= 8, "Should have at least 8 required sections"
        
        assert "quality_rules" in article, "article must have quality_rules"
        assert isinstance(article["quality_rules"], dict), "quality_rules must be a dict"

    def test_research_section_structure(self, spec):
        """Research section has required structure."""
        assert "research" in spec
        research = spec["research"]
        
        assert "required_fields" in research, "research must have required_fields"
        assert isinstance(research["required_fields"], list), "required_fields must be a list"
        
        assert "search_queries" in research, "research must have search_queries"
        assert isinstance(research["search_queries"], list), "search_queries must be a list"
        assert len(research["search_queries"]) > 0, "Should have at least one search query"
        
        assert "scraper" in research, "research must have scraper configuration"
        assert isinstance(research["scraper"], dict), "scraper must be a dict"

    def test_analysis_section_structure(self, spec):
        """Analysis section has required structure."""
        assert "analysis" in spec
        analysis = spec["analysis"]
        
        assert "required_fields" in analysis, "analysis must have required_fields"
        assert isinstance(analysis["required_fields"], list), "required_fields must be a list"
        assert len(analysis["required_fields"]) > 0, "Should have at least one required field"

    def test_pipeline_section_structure(self, spec):
        """Pipeline section has timeout and max_iterations."""
        assert "pipeline" in spec
        pipeline = spec["pipeline"]
        
        assert "timeout_total_seconds" in pipeline, "pipeline must have timeout_total_seconds"
        assert isinstance(pipeline["timeout_total_seconds"], int), "timeout_total_seconds must be integer"
        assert pipeline["timeout_total_seconds"] >= 60, "timeout should be at least 60 seconds"
        
        assert "max_iterations" in pipeline, "pipeline must have max_iterations"
        assert isinstance(pipeline["max_iterations"], int), "max_iterations must be integer"
        assert pipeline["max_iterations"] >= 1, "max_iterations should be at least 1"

    def test_llm_section_structure(self, spec):
        """LLM section has provider configuration."""
        assert "llm" in spec
        llm = spec["llm"]
        
        assert "provider" in llm, "llm must have provider"
        assert isinstance(llm["provider"], str), "provider must be string"

    def test_missing_spec_version_fails(self, schema):
        """Missing spec_version fails schema validation."""
        invalid_spec = {
            "article": {"required_sections": [], "quality_rules": {}},
            "research": {"required_fields": [], "search_queries": [], "scraper": {}},
            "analysis": {"required_fields": []},
            "pipeline": {"timeout_total_seconds": 900, "max_iterations": 3},
            "llm": {"provider": "test"},
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_spec, schema)

    def test_missing_required_sections_fails(self, schema):
        """Missing article.required_sections fails schema validation."""
        invalid_spec = {
            "spec_version": "1.0.0",
            "article": {"quality_rules": {}},  # missing required_sections
            "research": {"required_fields": [], "search_queries": [], "scraper": {}},
            "analysis": {"required_fields": []},
            "pipeline": {"timeout_total_seconds": 900, "max_iterations": 3},
            "llm": {"provider": "test"},
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_spec, schema)

    def test_invalid_timeout_type_fails(self, schema):
        """Invalid timeout type fails schema validation."""
        invalid_spec = {
            "spec_version": "1.0.0",
            "article": {"required_sections": ["test"], "quality_rules": {}},
            "research": {"required_fields": [], "search_queries": ["q"], "scraper": {}},
            "analysis": {"required_fields": []},
            "pipeline": {"timeout_total_seconds": "not_an_integer", "max_iterations": 3},
            "llm": {"provider": "test"},
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(invalid_spec, schema)

    def test_pipeline_validates_spec(self):
        """Pipeline initialization validates spec against schema."""
        from pipeline import SDDPipeline
        
        try:
            pipeline = SDDPipeline()
            assert pipeline.spec is not None
            assert pipeline.spec.get("spec_version") is not None
        except ValueError as e:
            pytest.fail(f"Pipeline should load valid spec: {e}")

    def test_pipeline_rejects_invalid_spec(self, tmp_path):
        """Pipeline raises error if spec is invalid."""
        # Create a temporary invalid spec file
        invalid_spec_path = tmp_path / "invalid_spec.yaml"
        invalid_spec_path.write_text("spec_version: 1.0.0\n")  # Missing required fields
        
        from pipeline import SDDPipeline
        
        with pytest.raises(ValueError, match="Spec validation failed"):
            SDDPipeline(spec_path=str(invalid_spec_path))
