from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from sdd.config import load_runtime_config


class TestRuntimeConfigShape:
    """Validate the split runtime config and legacy-compatible merged shape."""

    @pytest.fixture
    def schema(self):
        with open("spec/schema.json") as file_handle:
            return json.load(file_handle)

    @pytest.fixture
    def config(self):
        return load_runtime_config()

    def test_split_config_files_exist(self):
        assert Path("sdd/config/models.yaml").exists()
        assert Path("sdd/config/pipeline.yaml").exists()
        assert Path("sdd/config/quality.yaml").exists()
        assert Path("sdd/config/infra.yaml").exists()

    def test_schema_file_exists(self):
        schema_path = Path("spec/schema.json")
        assert schema_path.exists(), "spec/schema.json file not found"
        with open(schema_path) as file_handle:
            schema = json.load(file_handle)
        assert isinstance(schema, dict)
        assert "$schema" in schema

    def test_merged_config_has_required_top_level_keys(self, config):
        assert "article" in config
        assert "research" in config
        assert "analysis" in config
        assert "pipeline" in config
        assert "llm" in config
        assert "models" in config
        assert "model_providers" in config

    def test_article_section_structure(self, config):
        article = config["article"]
        assert isinstance(article["required_sections"], list)
        assert len(article["required_sections"]) >= 8
        assert isinstance(article["quality_rules"], dict)

    def test_research_section_structure(self, config):
        research = config["research"]
        assert isinstance(research["required_fields"], list)
        assert isinstance(research["search_queries"], list)
        assert len(research["search_queries"]) > 0
        assert isinstance(research["scraper"], dict)

    def test_analysis_section_structure(self, config):
        analysis = config["analysis"]
        assert isinstance(analysis["required_fields"], list)
        assert len(analysis["required_fields"]) > 0

    def test_pipeline_section_structure(self, config):
        pipeline = config["pipeline"]
        assert isinstance(pipeline["timeout_total_seconds"], int)
        assert pipeline["timeout_total_seconds"] >= 60
        assert isinstance(pipeline["max_iterations"], int)
        assert pipeline["max_iterations"] >= 1

    def test_llm_section_structure(self, config):
        llm = config["llm"]
        assert isinstance(llm["provider"], str)
        assert isinstance(llm["timeout"], dict)
        assert isinstance(llm["temperature"], dict)
        assert isinstance(llm["context_length"], dict)

    def test_merged_config_can_be_projected_to_legacy_schema(self, config, schema):
        projected = {
            "spec_version": "1.0.0",
            "spec_changelog": {"1.0.0": {"date": "2026-04-26", "changes": ["split config compatibility view"]}},
            "article": config["article"],
            "research": config["research"],
            "analysis": config["analysis"],
            "pipeline": config["pipeline"],
            "llm": {"provider": config["llm"]["provider"]},
        }
        jsonschema.validate(projected, schema)
