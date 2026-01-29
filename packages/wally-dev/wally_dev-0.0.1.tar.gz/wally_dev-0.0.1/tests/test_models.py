"""Tests for models module."""

from wally_dev.models import ExampleTestCase, Norm, Rule, TestCase, UserInfo


class TestNorm:
    """Tests for Norm model."""

    def test_from_api_response(self):
        """Test creating Norm from API response."""
        data = {
            "_id": "norm123",
            "name": "WCAG 2.1",
            "version": "2.1",
            "description": "Web Content Accessibility Guidelines",
            "referenceLink": "https://www.w3.org/TR/WCAG21/",
            "rulesCount": 50,
            "tags": ["wcag", "accessibility"],
            "lockedBy": "user456",
            "organizationId": "org789",
        }

        norm = Norm.from_api_response(data)

        assert norm.id == "norm123"
        assert norm.name == "WCAG 2.1"
        assert norm.version == "2.1"
        assert norm.reference_link == "https://www.w3.org/TR/WCAG21/"
        assert norm.rules_count == 50
        assert norm.locked_by == "user456"

    def test_from_api_response_minimal(self):
        """Test creating Norm with minimal data."""
        data = {
            "_id": "norm123",
            "name": "Test Norm",
        }

        norm = Norm.from_api_response(data)

        assert norm.id == "norm123"
        assert norm.name == "Test Norm"
        assert norm.version is None
        assert norm.locked_by is None


class TestRule:
    """Tests for Rule model."""

    def test_from_api_response(self):
        """Test creating Rule from API response."""
        data = {
            "_id": "rule123",
            "name": "Alt Text Required",
            "description": "Images must have alt text",
            "normId": "norm456",
            "severity": "critical",
            "wcagCriteria": ["1.1.1"],
            "testCasesCount": 5,
        }

        rule = Rule.from_api_response(data)

        assert rule.id == "rule123"
        assert rule.name == "Alt Text Required"
        assert rule.norm_id == "norm456"
        assert rule.severity == "critical"
        assert rule.wcag_criteria == ["1.1.1"]


class TestExampleTestCase:
    """Tests for ExampleTestCase model."""

    def test_from_api_response(self):
        """Test creating ExampleTestCase from API response."""
        data = {
            "_id": "ex123",
            "name": "Valid Image",
            "description": "Image with proper alt text",
            "html": '<img src="test.jpg" alt="Test">',
            "expectedResult": "pass",
            "explanation": "Has descriptive alt text",
        }

        example = ExampleTestCase.from_api_response(data)

        assert example.id == "ex123"
        assert example.name == "Valid Image"
        assert example.expected_result == "pass"
        assert "alt" in example.html


class TestTestCase:
    """Tests for TestCase model."""

    def test_from_api_response(self):
        """Test creating TestCase from API response."""
        data = {
            "_id": "tc123",
            "name": "Alt Text Verification",
            "description": "Verifies alt text presence",
            "ruleId": "rule456",
            "normId": "norm789",
            "code": "def run(html): return True",
            "language": "HTML",
            "enabled": True,
            "examples": [
                {
                    "_id": "ex1",
                    "name": "Example 1",
                    "html": "<img>",
                    "expectedResult": "fail",
                }
            ],
            "tags": ["images", "alt-text"],
        }

        testcase = TestCase.from_api_response(data)

        assert testcase.id == "tc123"
        assert testcase.name == "Alt Text Verification"
        assert testcase.rule_id == "rule456"
        assert testcase.code == "def run(html): return True"
        assert len(testcase.examples) == 1
        assert testcase.examples[0].id == "ex1"

    def test_to_file_dict(self):
        """Test converting TestCase to file dict."""
        testcase = TestCase(
            id="tc123",
            name="Test",
            rule_id="rule456",
            norm_id="norm789",
            code="def run(html): pass",
            examples=[
                ExampleTestCase(
                    id="ex1",
                    name="Example",
                    html="<div>",
                    expected_result="pass",
                )
            ],
        )

        data = testcase.to_file_dict()

        assert data["_id"] == "tc123"
        assert data["ruleId"] == "rule456"
        assert data["normId"] == "norm789"
        assert len(data["examples"]) == 1
        assert data["examples"][0]["_id"] == "ex1"


class TestUserInfo:
    """Tests for UserInfo model."""

    def test_from_api_response(self):
        """Test creating UserInfo from API response."""
        data = {
            "_id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "organizationId": "org456",
        }

        user = UserInfo.from_api_response(data)

        assert user.id == "user123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.organization_id == "org456"
