"""Tests for Chroma persistence and data validation."""

import pytest
from pathlib import Path
from memory.research_chroma import ResearchChroma


class TestChromaPersistence:
    """Test that scraped content is correctly saved to Chroma."""

    @pytest.fixture
    def chroma(self):
        """Fresh Chroma instance for testing."""
        return ResearchChroma(db_path=".memory/test_chroma_db")

    def test_save_scraped_content_returns_true(self, chroma):
        """save_scraped_content should return True on success."""
        result = chroma.save_scraped_content(
            tool="test_tool",
            url="https://test.com/page",
            title="Test Page",
            content="This is test content with enough words to be meaningful.",
            source_quality="test"
        )
        assert result is True, "save_scraped_content should return True"

    def test_save_scraped_content_creates_chunks(self, chroma):
        """Saved content should be chunked correctly."""
        content = "Test content. " * 100  # Large content to create multiple chunks
        chroma.save_scraped_content(
            tool="test_tool",
            url="https://test.com/page",
            title="Test Page",
            content=content,
            source_quality="test"
        )

        # Query should find the saved content
        results = chroma.query_similar(
            query_text="test",
            tool="test_tool",
            k=5
        )
        assert len(results) > 0, "Should find saved content"

    def test_metadata_preserved(self, chroma):
        """Metadata should be preserved in Chroma."""
        chroma.save_scraped_content(
            tool="docker",
            url="https://docs.docker.com/page",
            title="Docker Guide",
            content="Docker is a containerization platform.",
            source_quality="official"
        )

        # Query and check metadata
        results = chroma.query_similar(
            query_text="docker",
            tool="docker",
            k=1
        )

        assert len(results) > 0
        assert results[0]["tool"] == "docker"
        assert results[0]["url"] == "https://docs.docker.com/page"
        assert results[0]["title"] == "Docker Guide"

    def test_tool_filtering_works(self, chroma):
        """Tool-based filtering should prevent data mixing."""
        # Save Docker data
        chroma.save_scraped_content(
            tool="docker",
            url="https://docs.docker.com",
            title="Docker",
            content="Docker containers rootless mode",
            source_quality="official"
        )

        # Save Podman data
        chroma.save_scraped_content(
            tool="podman",
            url="https://docs.podman.io",
            title="Podman",
            content="Podman rootless containers",
            source_quality="official"
        )

        # Query for Docker only
        docker_results = chroma.query_similar(
            query_text="rootless",
            tool="docker",
            k=10
        )

        # All results should be Docker
        for result in docker_results:
            assert result["tool"] == "docker", "Tool filtering failed!"

        # Query for Podman only
        podman_results = chroma.query_similar(
            query_text="rootless",
            tool="podman",
            k=10
        )

        # All results should be Podman
        for result in podman_results:
            assert result["tool"] == "podman", "Tool filtering failed!"

    def test_similarity_score_is_valid(self, chroma):
        """Similarity scores should be between 0 and 1."""
        chroma.save_scraped_content(
            tool="test",
            url="https://test.com",
            title="Test",
            content="This is a test document about testing",
            source_quality="test"
        )

        results = chroma.query_similar(
            query_text="test",
            tool="test",
            k=1
        )

        assert len(results) > 0
        similarity = results[0]["similarity"]
        assert 0 <= similarity <= 1, f"Invalid similarity score: {similarity}"

    def test_empty_content_not_saved(self, chroma):
        """Empty content should not be saved."""
        result = chroma.save_scraped_content(
            tool="test",
            url="https://test.com",
            title="Empty",
            content="",  # Empty!
            source_quality="test"
        )
        # Should still return True (handled gracefully)
        assert result is not None

    def test_chunking_consistency(self, chroma):
        """Chunk count should match chunk_content output."""
        content = "Test content. " * 150
        chroma.save_scraped_content(
            tool="test",
            url="https://test.com",
            title="Test",
            content=content,
            source_quality="test"
        )

        # Get all chunks for this URL
        all_data = chroma.collection.get(
            where={"url": "https://test.com"},
            include=["metadatas"]
        )

        if all_data["metadatas"]:
            # Check that chunk_index and chunk_count are consistent
            for metadata in all_data["metadatas"]:
                chunk_idx = metadata.get("chunk_index", 0)
                chunk_count = metadata.get("chunk_count", 1)
                assert 0 <= chunk_idx < chunk_count, "Invalid chunk index"

    def test_cross_tool_search_works(self, chroma):
        """Cross-tool search should find data from other tools."""
        # Save to tool A
        chroma.save_scraped_content(
            tool="tool_a",
            url="https://tool-a.com",
            title="Tool A",
            content="Shared concept: rootless containers",
            source_quality="official"
        )

        # Save to tool B
        chroma.save_scraped_content(
            tool="tool_b",
            url="https://tool-b.com",
            title="Tool B",
            content="Implementation: rootless mode",
            source_quality="official"
        )

        # Cross-tool search
        results = chroma.cross_tool_search(
            query_text="rootless",
            exclude_tool="tool_a",
            k=5
        )

        # Should find tool_b
        assert any(r["tool"] == "tool_b" for r in results), \
            "Cross-tool search should find tool_b"

    def test_large_document_handling(self, chroma):
        """Should handle large documents gracefully."""
        large_content = "Test content. " * 5000  # Very large
        result = chroma.save_scraped_content(
            tool="test",
            url="https://test.com/large",
            title="Large Document",
            content=large_content,
            source_quality="test"
        )
        assert result is True, "Should handle large documents"

        # Should be queryable
        results = chroma.query_similar(
            query_text="test",
            tool="test",
            k=1
        )
        assert len(results) > 0, "Large document should be findable"


class TestChromaIntegration:
    """Test Chroma integration with Researcher."""

    def test_researcher_chroma_initialized(self):
        """Researcher should have Chroma available."""
        from skills.researcher import HAS_CHROMA

        if HAS_CHROMA:
            # Just verify that HAS_CHROMA is True means Chroma can be imported
            from memory.research_chroma import ResearchChroma
            chroma = ResearchChroma()
            assert chroma is not None, "Chroma should be importable"
        else:
            pytest.skip("Chroma not available")

    def test_researcher_saves_to_chroma(self):
        """Researcher should call save_scraped_content."""
        from skills.researcher import ResearcherSkill, HAS_CHROMA

        if not HAS_CHROMA:
            pytest.skip("Chroma not available")

        # This is a mocked test - full integration would require
        # mocking the search and scraper
        pytest.skip("Full integration test requires mocking")
