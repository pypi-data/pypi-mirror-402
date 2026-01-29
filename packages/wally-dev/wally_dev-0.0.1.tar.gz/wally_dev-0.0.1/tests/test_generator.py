"""Tests for test case generator module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from wally_dev.generator import GeneratorResult, TestCaseGenerator
from wally_dev.models import Rule


class TestTestCaseGenerator:
    """Tests for TestCaseGenerator class."""

    @pytest.fixture
    def sample_rule(self) -> Rule:
        """Create a sample rule for testing."""
        return Rule(
            id="rule123",
            name="Alt Text Required",
            description="All images must have alt text",
            norm_id="norm456",
            severity="critical",
            category="images",
            is_automatable=True,
        )

    @pytest.fixture
    def generator(self) -> TestCaseGenerator:
        """Create a generator instance."""
        return TestCaseGenerator(
            api_key="test-api-key",
            target="html",
            model="gpt-4o",
        )

    # =========================================================================
    # Initialization Tests
    # =========================================================================

    def test_initialization(self):
        """Test generator initialization."""
        gen = TestCaseGenerator(
            api_key="test-key",
            target="react",
            model="gpt-4",
            temperature=0.5,
            max_tokens=4000,
        )
        assert gen.api_key == "test-key"
        assert gen.target == "react"
        assert gen.model == "gpt-4"
        assert gen.temperature == 0.5
        assert gen.max_tokens == 4000
        assert gen._client is None

    def test_target_normalization(self):
        """Test that target is normalized to lowercase."""
        gen = TestCaseGenerator(api_key="test", target="REACT")
        assert gen.target == "react"

    # =========================================================================
    # Prompt Building Tests
    # =========================================================================

    def test_build_prompt_contains_rule_info(self, generator: TestCaseGenerator, sample_rule: Rule):
        """Test that prompt contains rule information."""
        prompt = generator._build_prompt(sample_rule)

        assert "rule123" in prompt
        assert "Alt Text Required" in prompt
        assert "All images must have alt text" in prompt
        assert "images" in prompt  # category
        assert "critical" in prompt  # severity

    def test_build_prompt_contains_target_context(self, sample_rule: Rule):
        """Test that prompt contains target-specific context."""
        gen_html = TestCaseGenerator(api_key="test", target="html")
        prompt_html = gen_html._build_prompt(sample_rule)
        assert "páginas HTML estáticas" in prompt_html

        gen_react = TestCaseGenerator(api_key="test", target="react")
        prompt_react = gen_react._build_prompt(sample_rule)
        assert "React" in prompt_react

    def test_build_prompt_json_format(self, generator: TestCaseGenerator, sample_rule: Rule):
        """Test that prompt requests JSON format."""
        prompt = generator._build_prompt(sample_rule)

        assert "JSON" in prompt
        assert "finder_py" in prompt
        assert "validator_py" in prompt
        assert "compliant_html" in prompt
        assert "non_compliant_html" in prompt

    # =========================================================================
    # Newline Fixing Tests
    # =========================================================================

    def test_fix_newlines_string(self, generator: TestCaseGenerator):
        """Test fixing newlines in strings."""
        result = generator._fix_newlines("line1\\nline2\\ttab")
        assert result == "line1\nline2\ttab"

    def test_fix_newlines_dict(self, generator: TestCaseGenerator):
        """Test fixing newlines in dicts."""
        input_dict = {"code": "def f():\\n    pass", "name": "test"}
        result = generator._fix_newlines(input_dict)
        assert result["code"] == "def f():\n    pass"
        assert result["name"] == "test"

    def test_fix_newlines_list(self, generator: TestCaseGenerator):
        """Test fixing newlines in lists."""
        input_list = ["line1\\nline2", "normal"]
        result = generator._fix_newlines(input_list)
        assert result[0] == "line1\nline2"
        assert result[1] == "normal"

    def test_fix_newlines_other_types(self, generator: TestCaseGenerator):
        """Test fixing newlines with non-string types."""
        assert generator._fix_newlines(123) == 123
        assert generator._fix_newlines(None) is None
        assert generator._fix_newlines(True) is True

    # =========================================================================
    # Combined Code Building Tests
    # =========================================================================

    def test_build_combined_code(self, generator: TestCaseGenerator):
        """Test building combined code from finder and validator."""
        finder_code = """from bs4 import BeautifulSoup

def find(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.find_all("img")
"""
        validator_code = """def validate(element):
    return bool(element.get("alt"))
"""

        combined = generator._build_combined_code(finder_code, validator_code)

        assert "FINDER" in combined
        assert "VALIDATOR" in combined
        assert "RUNNER" in combined
        assert "def find(" in combined
        assert "def validate(" in combined
        assert "def run(" in combined
        assert "def check_compliance(" in combined

    # =========================================================================
    # Generate Tests (with mocked OpenAI)
    # =========================================================================

    def test_generate_success(self, generator: TestCaseGenerator, sample_rule: Rule):
        """Test successful generation."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "finder_py": "def find(html): return []",
                            "validator_py": "def validate(el): return True",
                            "compliant_html": "<!DOCTYPE html><html></html>",
                            "non_compliant_html": "<!DOCTYPE html><html></html>",
                        }
                    )
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(generator, "_client", mock_client):
            generator._client = mock_client
            result = generator.generate(sample_rule)

        assert result is not None
        assert "finder_py" in result
        assert "validator_py" in result
        assert "code" in result

    def test_generate_missing_required_fields(
        self, generator: TestCaseGenerator, sample_rule: Rule
    ):
        """Test generation fails when required fields are missing."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content=json.dumps(
                        {
                            "finder_py": "def find(html): return []",
                            # Missing validator_py
                        }
                    )
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(generator, "_client", mock_client):
            generator._client = mock_client
            result = generator.generate(sample_rule)

        assert result is None

    def test_generate_invalid_json(self, generator: TestCaseGenerator, sample_rule: Rule):
        """Test generation handles invalid JSON."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="not valid json {{{"))]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(generator, "_client", mock_client):
            generator._client = mock_client
            result = generator.generate(sample_rule)

        assert result is None

    def test_generate_strips_markdown(self, generator: TestCaseGenerator, sample_rule: Rule):
        """Test generation strips markdown code blocks."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='```json\n{"finder_py": "def find(html): return []", "validator_py": "def validate(el): return True"}\n```'
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.object(generator, "_client", mock_client):
            generator._client = mock_client
            result = generator.generate(sample_rule)

        assert result is not None

    def test_generate_api_error(self, generator: TestCaseGenerator, sample_rule: Rule):
        """Test generation handles API errors gracefully."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.object(generator, "_client", mock_client):
            generator._client = mock_client
            result = generator.generate(sample_rule)

        assert result is None

    # =========================================================================
    # Client Lazy Loading Tests
    # =========================================================================

    def test_client_lazy_loading_attribute(self, generator: TestCaseGenerator):
        """Test that client is lazily loaded."""
        assert generator._client is None

    def test_generate_with_exception_returns_none(
        self, generator: TestCaseGenerator, sample_rule: Rule
    ):
        """Test that exceptions during generation return None."""
        # Force _client to be set to a mock that raises
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        generator._client = mock_client

        result = generator.generate(sample_rule)
        assert result is None


class TestGeneratorResult:
    """Tests for GeneratorResult class."""

    def test_successful_result(self):
        """Test creating a successful result."""
        result = GeneratorResult(
            success=True,
            finder_py="def find(): pass",
            validator_py="def validate(): pass",
            compliant_html="<html></html>",
            non_compliant_html="<html></html>",
            code="combined code",
        )

        assert result.success is True
        assert result.finder_py == "def find(): pass"
        assert result.error is None

    def test_failed_result(self):
        """Test creating a failed result."""
        result = GeneratorResult(
            success=False,
            error="API Error",
        )

        assert result.success is False
        assert result.error == "API Error"
        assert result.finder_py is None

    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = GeneratorResult(
            success=True,
            finder_py="finder code",
            validator_py="validator code",
            compliant_html="compliant html",
            non_compliant_html="non-compliant html",
            code="combined code",
        )

        d = result.to_dict()

        assert d["finder_py"] == "finder code"
        assert d["validator_py"] == "validator code"
        assert d["compliant_html"] == "compliant html"
        assert d["non_compliant_html"] == "non-compliant html"
        assert d["code"] == "combined code"
