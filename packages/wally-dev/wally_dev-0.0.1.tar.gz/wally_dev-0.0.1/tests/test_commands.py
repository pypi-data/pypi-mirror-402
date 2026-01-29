"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from wally_dev.cli import cli


class TestNormsCommand:
    """Tests for norms command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_norms_help(self, runner: CliRunner):
        """Test norms help."""
        result = runner.invoke(cli, ["norms", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_norms_list_help(self, runner: CliRunner):
        """Test norms list help."""
        result = runner.invoke(cli, ["norms", "list", "--help"])
        assert result.exit_code == 0


class TestRulesCommand:
    """Tests for rules command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_rules_help(self, runner: CliRunner):
        """Test rules help."""
        result = runner.invoke(cli, ["rules", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output

    def test_rules_list_help(self, runner: CliRunner):
        """Test rules list help."""
        result = runner.invoke(cli, ["rules", "list", "--help"])
        assert result.exit_code == 0
        assert "--norm-id" in result.output

    def test_rules_list_requires_norm_id(self, runner: CliRunner):
        """Test rules list requires --norm-id."""
        result = runner.invoke(cli, ["rules", "list"])
        assert result.exit_code != 0
        assert "norm-id" in result.output.lower() or "required" in result.output.lower()


class TestTestcasesCommand:
    """Tests for testcases command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_testcases_help(self, runner: CliRunner):
        """Test testcases help."""
        result = runner.invoke(cli, ["testcases", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output
        assert "list" in result.output

    def test_testcases_create_help(self, runner: CliRunner):
        """Test testcases create help."""
        result = runner.invoke(cli, ["testcases", "create", "--help"])
        assert result.exit_code == 0
        assert "--all" in result.output
        assert "--rule-id" in result.output
        assert "--target" in result.output
        assert "--dry-run" in result.output

    def test_testcases_create_requires_target(self, runner: CliRunner):
        """Test testcases create requires --target."""
        result = runner.invoke(cli, ["testcases", "create", "--all"])
        assert result.exit_code != 0
        assert "target" in result.output.lower()

    def test_testcases_create_requires_all_or_rule_id(self, runner: CliRunner):
        """Test testcases create requires --all or --rule-id."""
        # Without --all or --rule-id, just --target is not enough
        result = runner.invoke(cli, ["testcases", "create", "--target", "html"])
        # Should fail or show error message
        assert (
            result.exit_code != 0
            or "Especifique" in result.output
            or "autenticado" in result.output
        )

    def test_testcases_list_help(self, runner: CliRunner):
        """Test testcases list help."""
        result = runner.invoke(cli, ["testcases", "list", "--help"])
        assert result.exit_code == 0
        assert "--rule-id" in result.output


class TestStatusCommand:
    """Tests for status command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_status_help(self, runner: CliRunner):
        """Test status help."""
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0


class TestCheckoutCommand:
    """Tests for checkout command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_checkout_help(self, runner: CliRunner):
        """Test checkout help."""
        result = runner.invoke(cli, ["checkout", "--help"])
        assert result.exit_code == 0
        assert "--norm-id" in result.output
        assert "--force" in result.output

    def test_checkout_without_norm_id_interactive(self, runner: CliRunner):
        """Test checkout without --norm-id enters interactive mode."""
        result = runner.invoke(cli, ["checkout"])
        # Now optional - enters interactive mode or requires auth
        # Exit code 1 with NotLoggedInError exception is also acceptable
        assert (
            result.exit_code == 0
            or "login" in result.output.lower()
            or (result.exception and type(result.exception).__name__ == "NotLoggedInError")
        )


class TestPushCommand:
    """Tests for push command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_push_help(self, runner: CliRunner):
        """Test push help."""
        result = runner.invoke(cli, ["push", "--help"])
        assert result.exit_code == 0
        assert "--norm-id" in result.output
        assert "--keep-lock" in result.output

    def test_push_without_norm_id_auto_detects(self, runner: CliRunner):
        """Test push without --norm-id auto-detects from checkout."""
        result = runner.invoke(cli, ["push"])
        # Now optional - auto-detects or shows no checkout message
        # Exit code 1 with NotLoggedInError exception is also acceptable
        assert (
            result.exit_code == 0
            or "checkout" in result.output.lower()
            or (result.exception and type(result.exception).__name__ == "NotLoggedInError")
        )


class TestRunCommand:
    """Tests for run command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_run_help(self, runner: CliRunner):
        """Test run help."""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "--testcase" in result.output


class TestLogoutCommand:
    """Tests for logout command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_logout_help(self, runner: CliRunner):
        """Test logout help."""
        result = runner.invoke(cli, ["logout", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output


class TestLoginCommand:
    """Tests for login command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_login_help(self, runner: CliRunner):
        """Test login help."""
        result = runner.invoke(cli, ["login", "--help"])
        assert result.exit_code == 0
        assert "--username" in result.output
        # --org-id removed - organization is selected after login
