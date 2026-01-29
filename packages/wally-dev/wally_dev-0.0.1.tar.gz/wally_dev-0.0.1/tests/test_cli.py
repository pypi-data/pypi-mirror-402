"""Tests for CLI commands - basic functionality tests."""

import pytest
from click.testing import CliRunner

from wally_dev.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_main_help(self, runner: CliRunner):
        """Test main CLI help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Wally Dev CLI" in result.output
        assert "login" in result.output
        assert "logout" in result.output
        assert "checkout" in result.output
        assert "push" in result.output
        assert "run" in result.output
        assert "status" in result.output

    def test_login_help(self, runner: CliRunner):
        """Test login command help."""
        result = runner.invoke(cli, ["login", "--help"])
        assert result.exit_code == 0
        assert "--username" in result.output
        assert "--password" not in result.output  # Password should not be an option

    def test_checkout_help(self, runner: CliRunner):
        """Test checkout command help."""
        result = runner.invoke(cli, ["checkout", "--help"])
        assert result.exit_code == 0
        assert "--norm-id" in result.output

    def test_push_help(self, runner: CliRunner):
        """Test push command help."""
        result = runner.invoke(cli, ["push", "--help"])
        assert result.exit_code == 0
        assert "--norm-id" in result.output
        assert "--keep-lock" in result.output

    def test_run_help(self, runner: CliRunner):
        """Test run command help."""
        result = runner.invoke(cli, ["run", "--help"])
        assert result.exit_code == 0
        assert "--testcase" in result.output
        assert "--example" in result.output

    def test_status_help(self, runner: CliRunner):
        """Test status command help."""
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_logout_help(self, runner: CliRunner):
        """Test logout command help."""
        result = runner.invoke(cli, ["logout", "--help"])
        assert result.exit_code == 0
        assert "--force" in result.output


class TestCLIVersion:
    """Tests for CLI version."""

    def test_version(self, runner: CliRunner):
        """Test version output."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.1" in result.output


class TestLoginCommand:
    """Tests for login command."""

    def test_login_prompts_for_credentials(self, runner: CliRunner, mocker):
        """Test that login prompts for username and password when not provided."""
        # Mock getpass to avoid blocking on TTY input (getpass reads from /dev/tty directly)
        # This is necessary because getpass.getpass doesn't work with CliRunner's input
        mocker.patch("getpass.getpass", return_value="test_password")

        # Provide input for username and org_id prompts (handled by Click)
        result = runner.invoke(cli, ["login"], input="test@example.com\norg123\n")

        # The command should prompt for Email and Organização
        assert "Email" in result.output or "login" in result.output.lower()


class TestCheckoutCommand:
    """Tests for checkout command."""

    def test_checkout_without_norm_id_shows_interactive(self, runner: CliRunner):
        """Test that checkout without --norm-id shows interactive selection."""
        result = runner.invoke(cli, ["checkout"])
        # Should not fail immediately - will show interactive selection or auth error
        # (exit 0 means interactive mode started, or auth required)
        # Exit code 1 with NotLoggedInError exception is also acceptable
        assert (
            result.exit_code == 0
            or "login" in result.output.lower()
            or (result.exception and type(result.exception).__name__ == "NotLoggedInError")
        )


class TestPushCommand:
    """Tests for push command."""

    def test_push_without_norm_id_auto_detects(self, runner: CliRunner):
        """Test that push without --norm-id auto-detects from local checkout."""
        result = runner.invoke(cli, ["push"])
        # Should not fail immediately - will auto-detect or show no checkout message
        # (exit 0 means auto-detect worked or no checkout found)
        # Exit code 1 with NotLoggedInError exception is also acceptable
        assert (
            result.exit_code == 0
            or "checkout" in result.output.lower()
            or (result.exception and type(result.exception).__name__ == "NotLoggedInError")
        )


class TestRunCommand:
    """Tests for run command."""

    def test_run_requires_testcase(self, runner: CliRunner):
        """Test that run requires --testcase."""
        result = runner.invoke(cli, ["run"])
        assert result.exit_code != 0
        assert "required" in result.output.lower() or "Missing" in result.output


class TestMainFunction:
    """Tests for main() entry point."""

    def test_main_returns_zero_on_help(self, mocker):
        """Test main returns 0 on help."""
        from wally_dev.cli import main

        mocker.patch("sys.argv", ["wally-dev", "--help"])
        # main() catches the SystemExit from --help
        result = main()
        assert result == 0

    def test_main_handles_click_exception(self, mocker):
        """Test main handles ClickException."""
        from click import ClickException

        from wally_dev.cli import cli, main

        # Mock cli to raise ClickException
        mocker.patch.object(cli, "main", side_effect=ClickException("Test error"))
        result = main()
        assert result == 1  # ClickException exit code

    def test_main_handles_keyboard_interrupt(self, mocker):
        """Test main handles KeyboardInterrupt."""
        from wally_dev.cli import cli, main

        mocker.patch.object(cli, "main", side_effect=KeyboardInterrupt())
        result = main()
        assert result == 130

    def test_main_handles_generic_exception(self, mocker):
        """Test main handles generic exceptions."""
        from wally_dev.cli import cli, main

        mocker.patch.object(cli, "main", side_effect=Exception("Unexpected error"))
        result = main()
        assert result == 1


class TestNormsGroup:
    """Tests for norms command group."""

    def test_norms_help(self, runner: CliRunner):
        """Test norms help."""
        result = runner.invoke(cli, ["norms", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output


class TestRulesGroup:
    """Tests for rules command group."""

    def test_rules_help(self, runner: CliRunner):
        """Test rules help."""
        result = runner.invoke(cli, ["rules", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output


class TestTestcasesGroup:
    """Tests for testcases command group."""

    def test_testcases_help(self, runner: CliRunner):
        """Test testcases help."""
        result = runner.invoke(cli, ["testcases", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output
