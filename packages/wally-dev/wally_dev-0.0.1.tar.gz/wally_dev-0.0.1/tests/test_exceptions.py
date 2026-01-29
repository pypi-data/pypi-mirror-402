"""Tests for exceptions module."""

from wally_dev.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    ConnectionFailedError,
    InvalidAPIKeyError,
    InvalidCredentialsError,
    NetworkError,
    NormLockedError,
    NormNotFoundError,
    NotFoundError,
    NotLoggedInError,
    PermissionDeniedError,
    RequestTimeoutError,
    RuleNotFoundError,
    RuntimeError,
    ServerError,
    TestCaseExecutionError,
    TestCaseNotFoundError,
    TokenExpiredError,
    WallyDevError,
    WorkspaceError,
)


class TestWallyDevError:
    """Tests for base exception class."""

    def test_default_message(self):
        """Test default error message."""
        error = WallyDevError()
        assert str(error) == "Ocorreu um erro inesperado."
        assert error.exit_code == 6

    def test_custom_message(self):
        """Test custom error message."""
        error = WallyDevError(
            message="Technical error",
            user_message="User-friendly message",
            hint="Try this instead",
        )
        assert str(error) == "User-friendly message"
        assert error.message == "Technical error"
        assert error.hint == "Try this instead"

    def test_format_for_user(self):
        """Test formatting error for user display."""
        error = WallyDevError(
            user_message="Something went wrong",
            hint="Check your configuration",
        )
        formatted = error.format_for_user()
        assert "Something went wrong" in formatted
        assert "Check your configuration" in formatted


class TestConfigurationErrors:
    """Tests for configuration-related errors."""

    def test_configuration_error(self):
        """Test ConfigurationError."""
        error = ConfigurationError(field="api_key")
        assert "api_key" in str(error)
        assert error.exit_code == 2

    def test_not_logged_in_error(self):
        """Test NotLoggedInError."""
        error = NotLoggedInError()
        assert "não está autenticado" in str(error).lower()
        assert "login" in error.hint.lower()


class TestAuthenticationErrors:
    """Tests for authentication-related errors."""

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError()
        assert error.exit_code == 3

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError."""
        error = InvalidCredentialsError()
        assert "inválid" in str(error).lower()

    def test_invalid_api_key_error(self):
        """Test InvalidAPIKeyError."""
        error = InvalidAPIKeyError()
        assert "api key" in str(error).lower()

    def test_token_expired_error(self):
        """Test TokenExpiredError."""
        error = TokenExpiredError()
        assert "expirad" in str(error).lower()

    def test_permission_denied_error(self):
        """Test PermissionDeniedError."""
        error = PermissionDeniedError()
        assert "permissão" in str(error).lower()


class TestNetworkErrors:
    """Tests for network-related errors."""

    def test_network_error(self):
        """Test NetworkError."""
        error = NetworkError()
        assert error.exit_code == 4

    def test_connection_failed_error(self):
        """Test ConnectionFailedError."""
        error = ConnectionFailedError()
        assert "conectar" in str(error).lower()

    def test_request_timeout_error(self):
        """Test RequestTimeoutError."""
        error = RequestTimeoutError()
        assert "tempo" in str(error).lower() or "timeout" in str(error).lower()


class TestAPIErrors:
    """Tests for API-related errors."""

    def test_api_error(self):
        """Test APIError."""
        error = APIError(
            message="API returned 500",
            status_code=500,
            response={"error": "Internal error"},
        )
        assert error.status_code == 500
        assert error.response == {"error": "Internal error"}
        assert error.exit_code == 5

    def test_not_found_error(self):
        """Test NotFoundError."""
        error = NotFoundError()
        assert "não encontrad" in str(error).lower()

    def test_norm_not_found_error(self):
        """Test NormNotFoundError."""
        error = NormNotFoundError()
        assert "norma" in str(error).lower()

    def test_rule_not_found_error(self):
        """Test RuleNotFoundError."""
        error = RuleNotFoundError()
        assert "regra" in str(error).lower()

    def test_testcase_not_found_error(self):
        """Test TestCaseNotFoundError."""
        error = TestCaseNotFoundError()
        assert "caso de teste" in str(error).lower()

    def test_norm_locked_error(self):
        """Test NormLockedError."""
        error = NormLockedError()
        assert "bloqueada" in str(error).lower()

    def test_server_error(self):
        """Test ServerError."""
        error = ServerError()
        assert "servidor" in str(error).lower()


class TestRuntimeErrors:
    """Tests for runtime errors."""

    def test_runtime_error(self):
        """Test RuntimeError."""
        error = RuntimeError()
        assert error.exit_code == 6

    def test_workspace_error(self):
        """Test WorkspaceError."""
        error = WorkspaceError()
        assert "workspace" in str(error).lower()

    def test_testcase_execution_error(self):
        """Test TestCaseExecutionError."""
        error = TestCaseExecutionError()
        assert "executar" in str(error).lower() or "caso de teste" in str(error).lower()
