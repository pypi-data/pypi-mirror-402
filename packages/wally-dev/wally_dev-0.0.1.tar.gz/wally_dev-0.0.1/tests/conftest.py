"""
Shared fixtures for Wally Dev CLI tests.
"""

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from wally_dev.config import LocalConfig, Settings
from wally_dev.models import ExampleTestCase, Norm, Rule, TestCase

# =============================================================================
# CLI Fixtures
# =============================================================================


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def isolated_runner(tmp_path: Path):
    """Create an isolated CLI runner with temp directory."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        yield runner


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for configuration."""
    env_vars = {
        "WALLY_DEV_BACKEND_URL": "https://api.wally.test",
        "WALLY_DEV_TIMEOUT": "30",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def settings(mock_env_vars) -> Settings:
    """Create test settings instance."""
    return Settings(
        backend_url="https://api.wally.test",
        timeout=30,
    )


@pytest.fixture
def temp_config(tmp_path: Path) -> LocalConfig:
    """Create a LocalConfig with temporary file."""
    config_file = tmp_path / ".wally-dev.json"
    config = LocalConfig.__new__(LocalConfig)
    config.config_file = config_file
    config._data = {}
    return config


@pytest.fixture
def logged_in_config(temp_config: LocalConfig) -> LocalConfig:
    """Create a logged-in LocalConfig."""
    temp_config._data = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "user_id": "user123",
        "user_email": "test@example.com",
        "organization_id": "org456",
    }
    temp_config._save()
    return temp_config


@pytest.fixture
def config_with_locked_norm(logged_in_config: LocalConfig) -> LocalConfig:
    """Create a logged-in config with a locked norm."""
    logged_in_config.add_locked_norm(
        "norm789",
        {
            "norm_name": "Test Norm",
            "checkout_at": "2024-01-01T00:00:00",
            "testcase_count": 5,
        },
    )
    return logged_in_config


# =============================================================================
# Model Fixtures
# =============================================================================


@pytest.fixture
def sample_norm() -> Norm:
    """Create a sample Norm instance."""
    return Norm(
        id="norm123",
        name="WCAG 2.1 AA",
        version="2.1",
        description="Web Content Accessibility Guidelines 2.1 Level AA",
        rules_count=50,
        tags=["wcag", "accessibility"],
    )


@pytest.fixture
def sample_rule() -> Rule:
    """Create a sample Rule instance."""
    return Rule(
        id="rule456",
        name="Alt Text Required",
        description="All images must have alt text",
        norm_id="norm123",
        severity="critical",
        category="images",
        is_automatable=True,
        wcag_criteria=["1.1.1"],
    )


@pytest.fixture
def sample_rules() -> list[Rule]:
    """Create a list of sample rules."""
    return [
        Rule(
            id="rule001",
            name="Alt Text Required",
            description="All images must have alt text",
            norm_id="norm123",
            severity="critical",
            category="images",
            is_automatable=True,
        ),
        Rule(
            id="rule002",
            name="Lang Attribute Required",
            description="HTML must have lang attribute",
            norm_id="norm123",
            severity="error",
            category="document",
            is_automatable=True,
        ),
        Rule(
            id="rule003",
            name="Color Contrast",
            description="Text must have sufficient contrast",
            norm_id="norm123",
            severity="warning",
            category="visual",
            is_automatable=False,
        ),
    ]


@pytest.fixture
def sample_testcase() -> TestCase:
    """Create a sample TestCase instance."""
    return TestCase(
        id="tc123",
        name="Alt Text Verification",
        description="Verifies images have alt text",
        rule_id="rule456",
        norm_id="norm123",
        code="def validate(element): return bool(element.get('alt'))",
        language="html",
        enabled=True,
        tags=["html", "images"],
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


@pytest.fixture
def sample_testcases(sample_testcase: TestCase) -> list[TestCase]:
    """Create a list of sample test cases."""
    return [
        sample_testcase,
        TestCase(
            id="tc124",
            name="Lang Attribute Check",
            description="Verifies HTML has lang",
            rule_id="rule002",
            norm_id="norm123",
            language="html",
            enabled=True,
        ),
    ]


# =============================================================================
# API Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_api_response_norm() -> dict[str, Any]:
    """Mock API response for a norm."""
    return {
        "_id": "norm123",
        "name": "WCAG 2.1 AA",
        "version": "2.1",
        "description": "Web Content Accessibility Guidelines",
        "referenceLink": "https://www.w3.org/TR/WCAG21/",
        "rulesCount": 50,
        "tags": ["wcag"],
        "lockedBy": None,
        "organizationId": "org456",
    }


@pytest.fixture
def mock_api_response_rules() -> dict[str, Any]:
    """Mock API response for rules list."""
    return {
        "items": [
            {
                "_id": "rule001",
                "name": "Alt Text Required",
                "description": "All images must have alt text",
                "normId": "norm123",
                "severity": "critical",
                "category": "images",
                "isAutomatable": True,
            },
            {
                "_id": "rule002",
                "name": "Lang Attribute",
                "description": "HTML must have lang",
                "normId": "norm123",
                "severity": "error",
                "category": "document",
                "isAutomatable": True,
            },
        ]
    }


@pytest.fixture
def mock_api_response_testcases() -> list[dict[str, Any]]:
    """Mock API response for testcases list."""
    return [
        {
            "_id": "tc001",
            "name": "Alt Text Test",
            "description": "Tests alt text",
            "ruleId": "rule001",
            "normId": "norm123",
            "language": "html",
            "enabled": True,
        },
    ]


@pytest.fixture
def mock_api_client(sample_norm, sample_rules, sample_testcases):
    """Create a mock API client."""
    client = MagicMock()
    client.get_norm.return_value = sample_norm
    client.get_rules_by_norm.return_value = sample_rules
    client.get_testcases_by_norm.return_value = sample_testcases
    client.lock_norm.return_value = sample_norm
    client.unlock_norm.return_value = sample_norm
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    return client


# =============================================================================
# Workspace Fixtures
# =============================================================================


@pytest.fixture
def workspace_with_testcase(tmp_path: Path, sample_testcase: TestCase) -> Path:
    """Create a workspace with a testcase directory structure."""
    from wally_dev.workspace import WorkspaceManager

    workspace = WorkspaceManager(base_path=tmp_path)
    norm_id = sample_testcase.norm_id
    testcase_id = sample_testcase.id

    # Create directories
    testcase_dir = workspace.get_testcase_dir(norm_id, testcase_id)
    code_dir = testcase_dir / "code"
    examples_dir = testcase_dir / "examples"
    compliant_dir = examples_dir / "compliant"
    non_compliant_dir = examples_dir / "non-compliant"

    for d in [code_dir, compliant_dir, non_compliant_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Create testcase.json
    (testcase_dir / "testcase.json").write_text(
        json.dumps(sample_testcase.to_file_dict(), indent=2), encoding="utf-8"
    )

    # Create finder.py
    (code_dir / "finder.py").write_text("""
from bs4 import BeautifulSoup

def find(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.find_all("img")
""")

    # Create validator.py
    (code_dir / "validator.py").write_text("""
def validate(element):
    alt = element.get("alt", "")
    return bool(alt and alt.strip())
""")

    # Create examples
    (compliant_dir / "example.html").write_text('<img src="test.jpg" alt="Test">')
    (non_compliant_dir / "example.html").write_text('<img src="test.jpg">')

    return tmp_path
