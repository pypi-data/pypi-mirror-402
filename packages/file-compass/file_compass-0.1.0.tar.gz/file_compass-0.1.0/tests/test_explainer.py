"""
Tests for file_compass.explainer module.
"""

import pytest
import tempfile
from pathlib import Path

from file_compass.explainer import (
    ResultExplainer,
    VisualPreviewGenerator,
    MatchReason,
    ExplainedResult,
    VisualPreview
)


class TestResultExplainer:
    """Tests for ResultExplainer class."""

    def setup_method(self):
        self.explainer = ResultExplainer()

    def test_explain_exact_match(self):
        """Test explanation with exact word match."""
        result = self.explainer.explain_match(
            query="embedding generation",
            result_preview="def generate_embedding(text):\n    return model.embed(text)",
            result_path="/project/embedder.py",
            chunk_name="generate_embedding",
            chunk_type="function",
            relevance=0.85
        )

        assert result.relevance == 0.85
        assert len(result.reasons) > 0
        assert "embedding" in result.summary.lower() or "generate" in result.summary.lower()

        # Should have exact match reason
        exact_reasons = [r for r in result.reasons if r.reason_type == "exact"]
        assert len(exact_reasons) > 0

    def test_explain_filename_match(self):
        """Test explanation includes filename matches."""
        result = self.explainer.explain_match(
            query="config settings",
            result_preview="DEBUG = True\nLOG_LEVEL = 'INFO'",
            result_path="/project/config.py",
            chunk_name=None,
            chunk_type="module",
            relevance=0.7
        )

        # Should have filename match
        filename_reasons = [r for r in result.reasons if r.reason_type == "filename"]
        assert len(filename_reasons) > 0
        assert "config" in result.summary.lower()

    def test_explain_structure_match(self):
        """Test explanation for chunk name (function/class) match."""
        result = self.explainer.explain_match(
            query="authenticate user",
            result_preview="def authenticate_user(username, password):\n    ...",
            result_path="/project/auth.py",
            chunk_name="authenticate_user",
            chunk_type="function",
            relevance=0.9
        )

        # Should have structure match
        structure_reasons = [r for r in result.reasons if r.reason_type == "structure"]
        assert len(structure_reasons) > 0

    def test_explain_semantic_match(self):
        """Test explanation when match is primarily semantic."""
        result = self.explainer.explain_match(
            query="machine learning training",
            result_preview="for epoch in range(num_epochs):\n    loss = model.forward(batch)",
            result_path="/project/train.py",
            chunk_name="train_model",
            chunk_type="function",
            relevance=0.75
        )

        # Should have semantic match (no exact matches for query terms)
        semantic_reasons = [r for r in result.reasons if r.reason_type == "semantic"]
        assert len(semantic_reasons) > 0

    def test_explain_multiple_matches(self):
        """Test multiple word matches are tracked."""
        result = self.explainer.explain_match(
            query="file parser yaml",
            result_preview="def parse_yaml_file(path):\n    with open(path) as f:\n        return yaml.load(f)",
            result_path="/project/file_parser.py",
            chunk_name="parse_yaml_file",
            chunk_type="function",
            relevance=0.92
        )

        # Should have multiple exact matches
        exact_reasons = [r for r in result.reasons if r.reason_type == "exact"]
        matched_words = {r.matched_text.lower() for r in exact_reasons}
        assert "yaml" in matched_words or "file" in matched_words

    def test_explain_to_dict(self):
        """Test serialization to dict."""
        result = self.explainer.explain_match(
            query="test",
            result_preview="def test_function():",
            result_path="/test.py",
            chunk_name="test_function",
            chunk_type="function",
            relevance=0.8
        )

        result_dict = result.to_dict()
        assert "relevance" in result_dict
        assert "summary" in result_dict
        assert "reasons" in result_dict
        assert isinstance(result_dict["reasons"], list)

    def test_explain_low_relevance_no_matches(self):
        """Test explanation for low relevance without matches."""
        result = self.explainer.explain_match(
            query="completely unrelated query",
            result_preview="x = 1\ny = 2",
            result_path="/random.py",
            chunk_name=None,
            chunk_type="module",
            relevance=0.35
        )

        # Should still have some explanation
        assert len(result.summary) > 0

    def test_tokenize_handles_camelcase(self):
        """Test tokenization extracts meaningful words."""
        tokens = self.explainer._tokenize("calculateEmbeddingVector")
        # Should extract words
        assert len(tokens) > 0

    def test_find_exact_matches_case_insensitive(self):
        """Test exact matching is case insensitive."""
        matches = self.explainer._find_exact_matches(
            {"embedding", "model"},
            "The EMBEDDING model generates Embedding vectors"
        )

        # Should find "embedding" (appears twice with different cases)
        embedding_match = next((m for m in matches if m[0].lower() == "embedding"), None)
        assert embedding_match is not None
        assert embedding_match[1] >= 2  # At least 2 occurrences


class TestVisualPreviewGenerator:
    """Tests for VisualPreviewGenerator class."""

    def setup_method(self):
        self.generator = VisualPreviewGenerator(context_lines=2, max_preview_lines=15)

    def test_generate_preview_basic(self):
        """Test basic preview generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("\n".join([f"line {i}" for i in range(1, 21)]))
            temp_path = f.name

        try:
            preview = self.generator.generate_preview(
                file_path=temp_path,
                line_start=5,
                line_end=7
            )

            assert preview is not None
            assert preview.language == "python"
            assert preview.line_start <= 5  # Should include context
            assert preview.line_end >= 7
            assert 5 in preview.highlight_lines
            assert 6 in preview.highlight_lines
            assert 7 in preview.highlight_lines
            assert "line 5" in preview.content
        finally:
            Path(temp_path).unlink()

    def test_generate_preview_with_query_highlighting(self):
        """Test that query terms are highlighted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            content = """def calculate_total():
    total = 0
    for item in items:
        total += item.price
    return total

def calculate_average():
    return calculate_total() / len(items)
"""
            f.write(content)
            temp_path = f.name

        try:
            preview = self.generator.generate_preview(
                file_path=temp_path,
                line_start=1,
                line_end=5,
                query="calculate total",
                highlight_matches=True
            )

            assert preview is not None
            # Lines with "calculate" or "total" should be highlighted
            assert len(preview.highlight_lines) > 0
        finally:
            Path(temp_path).unlink()

    def test_generate_preview_detects_language(self):
        """Test language detection from file extension."""
        test_cases = [
            (".py", "python"),
            (".js", "javascript"),
            (".ts", "typescript"),
            (".md", "markdown"),
            (".json", "json"),
            (".rs", "rust"),
            (".go", "go"),
            (".unknown", "text")
        ]

        for ext, expected_lang in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix=ext, delete=False) as f:
                f.write("test content")
                temp_path = f.name

            try:
                preview = self.generator.generate_preview(
                    file_path=temp_path,
                    line_start=1,
                    line_end=1
                )
                assert preview is not None
                assert preview.language == expected_lang, f"Expected {expected_lang} for {ext}"
            finally:
                Path(temp_path).unlink()

    def test_generate_preview_handles_truncation(self):
        """Test that long files are truncated."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("\n".join([f"line {i}" for i in range(1, 101)]))
            temp_path = f.name

        try:
            # Request a range that would exceed max_preview_lines
            preview = self.generator.generate_preview(
                file_path=temp_path,
                line_start=1,
                line_end=50
            )

            assert preview is not None
            # Should be truncated to max_preview_lines
            actual_lines = preview.content.count("\n") + 1
            assert actual_lines <= self.generator.max_preview_lines
            assert preview.truncated
        finally:
            Path(temp_path).unlink()

    def test_generate_preview_nonexistent_file(self):
        """Test handling of nonexistent file."""
        preview = self.generator.generate_preview(
            file_path="/nonexistent/file.py",
            line_start=1,
            line_end=10
        )

        assert preview is None

    def test_generate_preview_line_number_formatting(self):
        """Test line numbers are properly formatted."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("\n".join([f"content {i}" for i in range(1, 11)]))
            temp_path = f.name

        try:
            preview = self.generator.generate_preview(
                file_path=temp_path,
                line_start=5,
                line_end=5
            )

            assert preview is not None
            # Should have arrow marker on highlighted line
            assert "→" in preview.content
            # Should have line numbers
            assert "5" in preview.content
        finally:
            Path(temp_path).unlink()

    def test_generate_compact_preview(self):
        """Test compact preview from stored content."""
        preview_data = self.generator.generate_compact_preview(
            content_preview="def hello():\n    print('Hello')",
            file_path="/project/hello.py",
            line_start=10,
            line_end=11
        )

        assert "language" in preview_data
        assert preview_data["language"] == "python"
        assert preview_data["line_start"] == 10
        assert "10" in preview_data["content"]
        assert "11" in preview_data["content"]

    def test_visual_preview_to_dict(self):
        """Test VisualPreview serialization."""
        preview = VisualPreview(
            content="1 │ test",
            line_start=1,
            line_end=1,
            highlight_lines=[1],
            language="python",
            truncated=False,
            total_lines=1
        )

        result = preview.to_dict()
        assert result["content"] == "1 │ test"
        assert result["language"] == "python"
        assert result["highlight_lines"] == [1]
        assert result["truncated"] is False


class TestMatchReason:
    """Tests for MatchReason dataclass."""

    def test_match_reason_creation(self):
        """Test creating a MatchReason."""
        reason = MatchReason(
            reason_type="exact",
            description="Contains 'embedding'",
            confidence=0.9,
            matched_text="embedding",
            location="content"
        )

        assert reason.reason_type == "exact"
        assert reason.confidence == 0.9
        assert reason.matched_text == "embedding"

    def test_match_reason_optional_fields(self):
        """Test MatchReason with optional fields None."""
        reason = MatchReason(
            reason_type="semantic",
            description="Semantically related",
            confidence=0.7
        )

        assert reason.matched_text is None
        assert reason.location is None


class TestExplainedResult:
    """Tests for ExplainedResult dataclass."""

    def test_explained_result_to_dict(self):
        """Test ExplainedResult serialization."""
        reasons = [
            MatchReason("exact", "Contains 'test'", 0.9, "test", "content"),
            MatchReason("semantic", "Related to testing", 0.7)
        ]

        result = ExplainedResult(
            relevance=0.85,
            reasons=reasons,
            summary="contains 'test'; related to testing"
        )

        result_dict = result.to_dict()

        assert result_dict["relevance"] == 0.85
        assert result_dict["summary"] == "contains 'test'; related to testing"
        assert len(result_dict["reasons"]) == 2
        assert result_dict["reasons"][0]["type"] == "exact"
        assert result_dict["reasons"][1]["type"] == "semantic"
