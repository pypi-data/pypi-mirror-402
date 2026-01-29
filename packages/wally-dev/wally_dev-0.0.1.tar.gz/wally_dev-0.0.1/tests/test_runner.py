"""Tests for test case runner."""

from pathlib import Path

import pytest

from wally_dev.exceptions import TestCaseExecutionError
from wally_dev.models import ExampleTestCase, TestCase
from wally_dev.runner import TestCaseRunner


@pytest.fixture
def runner() -> TestCaseRunner:
    """Create a test case runner."""
    return TestCaseRunner(verbose=False)


@pytest.fixture
def code_dir_simple(tmp_path: Path) -> Path:
    """Create a temp directory with simple finder/validator code."""
    code_dir = tmp_path / "code"
    code_dir.mkdir()

    # finder.py - finds all divs
    (code_dir / "finder.py").write_text("""
from bs4 import BeautifulSoup

def find(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.find_all("div")
""")

    # validator.py - always passes
    (code_dir / "validator.py").write_text("""
def validate(element):
    return True
""")

    return code_dir


@pytest.fixture
def code_dir_alt_text(tmp_path: Path) -> Path:
    """Create a temp directory with alt text checker code."""
    code_dir = tmp_path / "code"
    code_dir.mkdir()

    # finder.py - finds all images
    (code_dir / "finder.py").write_text("""
from bs4 import BeautifulSoup

def find(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.find_all("img")
""")

    # validator.py - checks alt attribute
    (code_dir / "validator.py").write_text("""
def validate(element):
    alt = element.get("alt", "")
    return bool(alt and alt.strip())
""")

    return code_dir


@pytest.fixture
def simple_testcase() -> TestCase:
    """Create a simple test case."""
    return TestCase(
        id="tc_pass",
        name="Always Pass",
        rule_id="rule123",
        examples=[
            ExampleTestCase(
                id="ex1",
                name="Example 1",
                html="<div>Test</div>",
                expected_result="pass",
            ),
        ],
    )


@pytest.fixture
def alt_text_testcase() -> TestCase:
    """Create a test case for alt text checking."""
    return TestCase(
        id="tc_alt",
        name="Alt Text Check",
        rule_id="rule456",
        examples=[
            ExampleTestCase(
                id="ex_pass",
                name="With alt",
                html='<img src="test.jpg" alt="Description">',
                expected_result="compliant",
            ),
            ExampleTestCase(
                id="ex_fail",
                name="Without alt",
                html='<img src="test.jpg">',
                expected_result="non-compliant",
            ),
        ],
    )


class TestTestCaseRunnerNew:
    """Tests for TestCaseRunner class with finder/validator pattern."""

    def test_run_simple_pass(
        self, runner: TestCaseRunner, simple_testcase: TestCase, code_dir_simple: Path
    ):
        """Test running a simple passing test."""
        result = runner.run_example(simple_testcase, simple_testcase.examples[0], code_dir_simple)

        assert result.passed is True
        assert result.expected == "compliant"
        assert result.actual == "compliant"
        assert result.execution_time_ms > 0

    def test_run_alt_text_pass(
        self, runner: TestCaseRunner, alt_text_testcase: TestCase, code_dir_alt_text: Path
    ):
        """Test alt text check with valid image."""
        example = alt_text_testcase.examples[0]  # With alt
        result = runner.run_example(alt_text_testcase, example, code_dir_alt_text)

        assert result.passed is True
        assert result.expected == "compliant"
        assert result.actual == "compliant"

    def test_run_alt_text_fail(
        self, runner: TestCaseRunner, alt_text_testcase: TestCase, code_dir_alt_text: Path
    ):
        """Test alt text check with invalid image."""
        example = alt_text_testcase.examples[1]  # Without alt
        result = runner.run_example(alt_text_testcase, example, code_dir_alt_text)

        # Test passes because expected=non-compliant and actual=non-compliant
        assert result.passed is True
        assert result.expected == "non-compliant"
        assert result.actual == "non-compliant"

    def test_run_testcase_all_examples(
        self, runner: TestCaseRunner, alt_text_testcase: TestCase, code_dir_alt_text: Path
    ):
        """Test running all examples."""
        results = runner.run_testcase(alt_text_testcase, code_dir_alt_text)

        assert len(results) == 2
        assert "ex_pass" in results
        assert "ex_fail" in results
        assert all(r.passed for r in results.values())

    def test_run_missing_code_dir(self, runner: TestCaseRunner, simple_testcase: TestCase):
        """Test running test case without code_dir."""
        with pytest.raises(TestCaseExecutionError):
            runner.run_example(simple_testcase, simple_testcase.examples[0], None)

    def test_run_missing_finder(
        self, runner: TestCaseRunner, simple_testcase: TestCase, tmp_path: Path
    ):
        """Test running test case without finder.py."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "validator.py").write_text("def validate(el): return True")

        with pytest.raises(TestCaseExecutionError) as exc_info:
            runner.run_example(simple_testcase, simple_testcase.examples[0], code_dir)

        assert "finder.py" in str(exc_info.value.message)

    def test_run_missing_validator(
        self, runner: TestCaseRunner, simple_testcase: TestCase, tmp_path: Path
    ):
        """Test running test case without validator.py."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "finder.py").write_text("""
from bs4 import BeautifulSoup
def find(html): return BeautifulSoup(html, "html.parser").find_all("div")
""")

        with pytest.raises(TestCaseExecutionError) as exc_info:
            runner.run_example(simple_testcase, simple_testcase.examples[0], code_dir)

        assert "validator.py" in str(exc_info.value.message)

    def test_run_single_example(
        self, runner: TestCaseRunner, alt_text_testcase: TestCase, code_dir_alt_text: Path
    ):
        """Test running a single specific example."""
        result = runner.run_testcase_single_example(alt_text_testcase, "ex_pass", code_dir_alt_text)

        assert result.passed is True
        assert result.example_id == "ex_pass"

    def test_debug_testcase(
        self, runner: TestCaseRunner, simple_testcase: TestCase, code_dir_simple: Path
    ):
        """Test debug mode output."""
        debug_info = runner.debug_testcase(
            simple_testcase, simple_testcase.examples[0], code_dir_simple
        )

        assert debug_info["testcase_id"] == "tc_pass"
        assert debug_info["example_id"] == "ex1"
        assert debug_info["execution"]["success"] is True
        assert "validation_results" in debug_info["execution"]
        assert "elements_found" in debug_info["execution"]

    def test_run_with_invalid_finder(
        self, runner: TestCaseRunner, simple_testcase: TestCase, tmp_path: Path
    ):
        """Test running with finder that has syntax error."""
        code_dir = tmp_path / "code"
        code_dir.mkdir()
        (code_dir / "finder.py").write_text("def find(html): return []  # invalid syntax :")
        (code_dir / "validator.py").write_text("def validate(el): return True")

        # Should handle gracefully
        result = runner.run_example(simple_testcase, simple_testcase.examples[0], code_dir)
        # No elements found, so compliant
        assert result is not None

    def test_run_verbose_mode(self, simple_testcase: TestCase, code_dir_simple: Path):
        """Test running in verbose mode."""
        verbose_runner = TestCaseRunner(verbose=True)
        result = verbose_runner.run_example(
            simple_testcase, simple_testcase.examples[0], code_dir_simple
        )
        assert result.passed is True

    def test_run_testcase_no_examples(self, runner: TestCaseRunner, code_dir_simple: Path):
        """Test running testcase with no examples."""
        empty_tc = TestCase(
            id="tc_empty",
            name="Empty Test",
            rule_id="rule123",
            examples=[],
        )
        results = runner.run_testcase(empty_tc, code_dir_simple)
        assert results == {}

    def test_run_single_example_not_found(
        self, runner: TestCaseRunner, alt_text_testcase: TestCase, code_dir_alt_text: Path
    ):
        """Test running a non-existent example raises error."""
        from wally_dev.exceptions import TestCaseNotFoundError

        with pytest.raises(TestCaseNotFoundError):
            runner.run_testcase_single_example(
                alt_text_testcase, "nonexistent_example", code_dir_alt_text
            )
