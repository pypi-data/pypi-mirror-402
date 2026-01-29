"""
Exception hierarchy for Wally Dev CLI.

Provides user-friendly error messages and categorized exceptions
for better error handling and debugging.
"""

from typing import Optional


class WallyDevError(Exception):
    """
    Base exception for all Wally Dev CLI errors.

    Attributes:
        message: Technical error message
        user_message: User-friendly message (shown to user)
        hint: Optional hint for resolution
        exit_code: Suggested exit code for CLI
    """

    user_message: str = "Ocorreu um erro inesperado."
    hint: Optional[str] = None
    exit_code: int = 6  # EXIT_ERROR_RUNTIME by default

    def __init__(
        self,
        message: Optional[str] = None,
        user_message: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        self.message = message or self.user_message
        if user_message:
            self.user_message = user_message
        if hint:
            self.hint = hint
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.user_message

    def format_for_user(self) -> str:
        """Format error message for display to user."""
        parts = [self.user_message]
        if self.hint:
            parts.append(f"💡 Dica: {self.hint}")
        return "\n".join(parts)


# =============================================================================
# Configuration Errors (exit code 2)
# =============================================================================


class ConfigurationError(WallyDevError):
    """Raised when configuration is invalid or missing."""

    user_message = "Erro de configuração."
    exit_code = 2

    def __init__(
        self,
        message: Optional[str] = None,
        field: Optional[str] = None,
        hint: Optional[str] = None,
    ):
        self.field = field
        if field and not message:
            message = f"Configuração inválida ou ausente: {field}"
        super().__init__(message=message, user_message=message, hint=hint)


class NotLoggedInError(ConfigurationError):
    """Raised when user is not logged in."""

    user_message = "Você não está autenticado."
    hint = "Execute 'wally-dev login' primeiro."

    def __init__(self) -> None:
        super().__init__(message=self.user_message, hint=self.hint)


# =============================================================================
# Authentication Errors (exit code 3)
# =============================================================================


class AuthenticationError(WallyDevError):
    """Raised when authentication fails."""

    user_message = "Falha na autenticação."
    exit_code = 3


class InvalidCredentialsError(AuthenticationError):
    """Raised when username/password is invalid."""

    user_message = "Usuário ou senha inválidos."
    hint = "Verifique suas credenciais e tente novamente."


class InvalidAPIKeyError(AuthenticationError):
    """Raised when API key is invalid."""

    user_message = "API key inválida ou expirada."
    hint = "Verifique sua API key em: https://app.equallyze.com/admin/api-keys"


class TokenExpiredError(AuthenticationError):
    """Raised when access token is expired."""

    user_message = "Sessão expirada."
    hint = "Execute 'wally-dev login' para autenticar novamente."


class PermissionDeniedError(AuthenticationError):
    """Raised when user doesn't have permission."""

    user_message = "Permissão negada para esta operação."


# =============================================================================
# Network Errors (exit code 4)
# =============================================================================


class NetworkError(WallyDevError):
    """Base class for network-related errors."""

    user_message = "Erro de conexão com o servidor."
    exit_code = 4


class ConnectionFailedError(NetworkError):
    """Raised when connection to server fails."""

    user_message = "Não foi possível conectar ao servidor Wally."
    hint = "Verifique sua conexão de internet e tente novamente."


class RequestTimeoutError(NetworkError):
    """Raised when request times out."""

    user_message = "Tempo limite de conexão excedido."
    hint = "O servidor pode estar sobrecarregado. Tente novamente em alguns minutos."


# =============================================================================
# API Errors (exit code 5)
# =============================================================================


class APIError(WallyDevError):
    """Base class for API errors."""

    user_message = "Erro na comunicação com a API."
    exit_code = 5

    def __init__(
        self,
        message: Optional[str] = None,
        status_code: Optional[int] = None,
        response: Optional[dict] = None,
        hint: Optional[str] = None,
    ):
        self.status_code = status_code
        self.response = response
        super().__init__(message=message, hint=hint)


class NotFoundError(APIError):
    """Raised when requested resource is not found."""

    user_message = "Recurso não encontrado."


class NormNotFoundError(NotFoundError):
    """Raised when norm is not found."""

    user_message = "Norma não encontrada."
    hint = "Verifique o ID da norma e tente novamente."


class TestCaseNotFoundError(NotFoundError):
    """Raised when test case is not found."""

    user_message = "Caso de teste não encontrado."


class RuleNotFoundError(NotFoundError):
    """Raised when rule is not found."""

    user_message = "Regra não encontrada."
    hint = "Verifique o ID da regra e tente novamente."


class NormLockedError(APIError):
    """Raised when norm is already locked by another user."""

    user_message = "Esta norma está bloqueada por outro usuário."
    hint = (
        "Aguarde o outro usuário concluir suas alterações ou entre em contato com o administrador."
    )


class ServerError(APIError):
    """Raised for server-side errors (5xx)."""

    user_message = "Erro interno do servidor."
    hint = "Tente novamente mais tarde. Se o erro persistir, entre em contato com o suporte."


# =============================================================================
# Runtime Errors (exit code 6)
# =============================================================================


class RuntimeError(WallyDevError):
    """Base class for runtime errors."""

    exit_code = 6


class WorkspaceError(RuntimeError):
    """Raised when workspace operations fail."""

    user_message = "Erro ao manipular o workspace."


class TestCaseExecutionError(RuntimeError):
    """Raised when test case execution fails."""

    user_message = "Erro ao executar o caso de teste."
