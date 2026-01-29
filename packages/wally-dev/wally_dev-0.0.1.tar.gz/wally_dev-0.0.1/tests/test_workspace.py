"""Tests for workspace module."""

import json
from pathlib import Path

import pytest

from wally_dev.exceptions import TestCaseNotFoundError
from wally_dev.models import ExampleTestCase, TestCase
from wally_dev.workspace import WorkspaceManager


@pytest.fixture
def workspace(tmp_path: Path) -> WorkspaceManager:
    """Create a workspace manager with temp directory."""
    return WorkspaceManager(base_path=tmp_path)


@pytest.fixture
def sample_testcase() -> TestCase:
    """Create a sample test case."""
    return TestCase(
        id="tc123",
        name="Test Alt Text",
        description="Verifies alt text presence",
        rule_id="rule456",
        norm_id="norm789",
        language="HTML",
        enabled=True,
        examples=[
            ExampleTestCase(
                id="ex1",
                name="Image with alt",
                description="Valid image",
                html='<img src="test.jpg" alt="Test">',
                expected_result="pass",
                explanation="Has alt text",
            ),
            ExampleTestCase(
                id="ex2",
                name="Image without alt",
                description="Invalid image",
                html='<img src="test.jpg">',
                expected_result="fail",
                explanation="Missing alt text",
            ),
        ],
    )


def _create_testcase_dir(workspace: WorkspaceManager, norm_id: str, testcase: TestCase) -> Path:
    """Helper to create a testcase directory structure for tests."""
    testcase_dir = workspace.get_testcases_dir(norm_id) / testcase.id
    testcase_dir.mkdir(parents=True, exist_ok=True)

    # Create testcase.json
    json_path = testcase_dir / "testcase.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(testcase.to_file_dict(), f, indent=2, ensure_ascii=False)

    # Create code directory with finder/validator
    code_dir = testcase_dir / "code"
    code_dir.mkdir(exist_ok=True)

    (code_dir / "finder.py").write_text("""
from bs4 import BeautifulSoup

def find(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.find_all("img")
""")

    (code_dir / "validator.py").write_text("""
def validate(element):
    alt = element.get("alt", "")
    return bool(alt and alt.strip())
""")

    # Create examples directories
    examples_dir = testcase_dir / "examples"
    compliant_dir = examples_dir / "compliant"
    non_compliant_dir = examples_dir / "non-compliant"
    compliant_dir.mkdir(parents=True, exist_ok=True)
    non_compliant_dir.mkdir(parents=True, exist_ok=True)

    (compliant_dir / "example.html").write_text('<img src="test.jpg" alt="Test">')
    (non_compliant_dir / "example.html").write_text('<img src="test.jpg">')

    return testcase_dir


class TestWorkspaceManager:
    """Tests for WorkspaceManager class."""

    def test_ensure_norm_dir(self, workspace: WorkspaceManager):
        """Test creating norm directory structure."""
        norm_dir = workspace.ensure_norm_dir("norm123")

        assert norm_dir.exists()
        assert (norm_dir / "testCases").exists()

    def test_save_testcase_legacy_format(
        self, workspace: WorkspaceManager, sample_testcase: TestCase
    ):
        """Test saving a test case (legacy format for upload)."""
        # This tests the save_testcase method which saves in legacy format
        json_path = workspace.save_testcase("norm789", sample_testcase)

        assert json_path.exists()

        # Verify JSON content
        with open(json_path) as f:
            data = json.load(f)
        assert data["_id"] == "tc123"
        assert data["name"] == "Test Alt Text"
        assert len(data["examples"]) == 2

    def test_save_testcases(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test saving multiple test cases."""
        tc2 = TestCase(
            id="tc456",
            name="Another Test",
            rule_id="rule789",
            examples=[],
        )

        count = workspace.save_testcases("norm789", [sample_testcase, tc2])

        assert count == 2
        assert (workspace.get_testcases_dir("norm789") / "tc123.json").exists()
        assert (workspace.get_testcases_dir("norm789") / "tc456.json").exists()

    def test_load_testcase_new_format(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test loading a test case (new directory format)."""
        # Create testcase in new format
        _create_testcase_dir(workspace, "norm789", sample_testcase)

        loaded = workspace.load_testcase("norm789", "tc123")

        assert loaded.id == "tc123"
        assert loaded.name == "Test Alt Text"
        assert len(loaded.examples) > 0

    def test_load_testcase_not_found(self, workspace: WorkspaceManager):
        """Test loading non-existent test case."""
        workspace.ensure_norm_dir("norm789")

        with pytest.raises(TestCaseNotFoundError):
            workspace.load_testcase("norm789", "nonexistent")

    def test_load_all_testcases(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test loading all test cases for a norm."""
        _create_testcase_dir(workspace, "norm789", sample_testcase)

        testcases = workspace.load_all_testcases("norm789")

        assert len(testcases) == 1
        assert testcases[0].id == "tc123"

    def test_list_norms(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test listing norms in workspace."""
        _create_testcase_dir(workspace, "norm1", sample_testcase)
        _create_testcase_dir(workspace, "norm2", sample_testcase)

        norms = workspace.list_norms()

        assert set(norms) == {"norm1", "norm2"}

    def test_delete_norm(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test deleting a norm's workspace."""
        _create_testcase_dir(workspace, "norm789", sample_testcase)
        assert workspace.get_norm_dir("norm789").exists()

        result = workspace.delete_norm("norm789")

        assert result is True
        assert not workspace.get_norm_dir("norm789").exists()

    def test_get_workspace_info(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test getting workspace info."""
        _create_testcase_dir(workspace, "norm789", sample_testcase)

        info = workspace.get_workspace_info("norm789")

        assert info["norm_id"] == "norm789"
        assert info["exists"] is True
        assert info["testcase_count"] == 1
        assert "tc123" in info["testcases"]

    def test_get_testcase_code_dir(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test getting code directory path."""
        _create_testcase_dir(workspace, "norm789", sample_testcase)

        code_dir = workspace.get_testcase_code_dir("norm789", "tc123")

        assert code_dir.exists()
        assert (code_dir / "finder.py").exists()
        assert (code_dir / "validator.py").exists()

    def test_get_testcase_dir(self, workspace: WorkspaceManager, sample_testcase: TestCase):
        """Test getting testcase directory path."""
        _create_testcase_dir(workspace, "norm789", sample_testcase)

        testcase_dir = workspace.get_testcase_dir("norm789", "tc123")

        assert testcase_dir.exists()
        assert (testcase_dir / "testcase.json").exists()
        assert (testcase_dir / "code").exists()
        assert (testcase_dir / "examples").exists()

    def test_extract_testcases_zip(self, workspace: WorkspaceManager):
        """Test extracting test cases from ZIP."""
        import io
        import zipfile

        # Create a test ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("tc1/testcase.json", '{"_id": "tc1", "name": "Test 1"}')
            zf.writestr("tc1/code/finder.py", "def find(html): return []")
            zf.writestr("tc1/code/validator.py", "def validate(el): return True")
            zf.writestr("tc2/testcase.json", '{"_id": "tc2", "name": "Test 2"}')

        zip_content = zip_buffer.getvalue()

        count = workspace.extract_testcases_zip("norm123", zip_content)

        assert count == 2
        assert (workspace.get_testcases_dir("norm123") / "tc1" / "testcase.json").exists()
        assert (workspace.get_testcases_dir("norm123") / "tc1" / "code" / "finder.py").exists()
        assert (workspace.get_testcases_dir("norm123") / "tc2" / "testcase.json").exists()

    def test_extract_testcases_zip_invalid(self, workspace: WorkspaceManager):
        """Test extracting from invalid ZIP raises error."""
        from wally_dev.exceptions import WorkspaceError

        with pytest.raises(WorkspaceError):
            workspace.extract_testcases_zip("norm123", b"not a valid zip")

    def test_extract_examples_zip(self, workspace: WorkspaceManager):
        """Test extracting examples from ZIP."""
        import io
        import zipfile

        # First create the testcase directory
        workspace.ensure_norm_dir("norm123")
        testcase_dir = workspace.get_testcases_dir("norm123") / "tc1"
        testcase_dir.mkdir(parents=True, exist_ok=True)

        # Create a test ZIP file with examples
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("tc1/examples/compliant/example1.html", "<img alt='test'>")
            zf.writestr("tc1/examples/non-compliant/example1.html", "<img>")

        zip_content = zip_buffer.getvalue()

        count = workspace.extract_examples_zip("norm123", zip_content)

        assert count == 2
        examples_dir = testcase_dir / "examples"
        assert (examples_dir / "compliant" / "example1.html").exists()
        assert (examples_dir / "non-compliant" / "example1.html").exists()

    def test_extract_examples_zip_invalid(self, workspace: WorkspaceManager):
        """Test extracting examples from invalid ZIP raises error."""
        from wally_dev.exceptions import WorkspaceError

        with pytest.raises(WorkspaceError):
            workspace.extract_examples_zip("norm123", b"not a valid zip")

    def test_save_generated_testcase(self, workspace: WorkspaceManager):
        """Test saving a generated testcase."""
        generated = {
            "finder_py": "def find(html): return []",
            "validator_py": "def validate(el): return True",
            "code": "# combined code",
            "compliant_html": "<img alt='test'>",
            "non_compliant_html": "<img>",
        }

        testcase_dir = workspace.save_generated_testcase(
            norm_id="norm456",
            testcase_id="tc_generated_123",
            generated=generated,
        )

        assert testcase_dir.exists()
        assert (testcase_dir / "testcase.json").exists()
        assert (testcase_dir / "code" / "finder.py").exists()
        assert (testcase_dir / "code" / "validator.py").exists()
        assert (testcase_dir / "code" / "main.py").exists()
        assert (testcase_dir / "examples" / "compliant").exists()
        assert (testcase_dir / "examples" / "non-compliant").exists()

    def test_delete_norm_nonexistent(self, workspace: WorkspaceManager):
        """Test deleting a non-existent norm returns False."""
        result = workspace.delete_norm("nonexistent")
        assert result is False

    def test_list_norms_empty(self, workspace: WorkspaceManager):
        """Test listing norms when none exist."""
        norms = workspace.list_norms()
        assert norms == []

    def test_get_workspace_info_nonexistent(self, workspace: WorkspaceManager):
        """Test getting info for non-existent norm."""
        info = workspace.get_workspace_info("nonexistent")
        assert info["exists"] is False
        assert info["testcase_count"] == 0

    def test_load_all_testcases_empty(self, workspace: WorkspaceManager):
        """Test loading testcases when none exist."""
        workspace.ensure_norm_dir("empty_norm")
        testcases = workspace.load_all_testcases("empty_norm")
        assert testcases == []

    def test_load_testcase_with_code_files(
        self, workspace: WorkspaceManager, sample_testcase: TestCase
    ):
        """Test loading testcase reads code from files."""
        _create_testcase_dir(workspace, "norm789", sample_testcase)

        loaded = workspace.load_testcase("norm789", "tc123")

        # Should have loaded the testcase successfully
        assert loaded.id == "tc123"
        assert loaded.name == "Test Alt Text"
