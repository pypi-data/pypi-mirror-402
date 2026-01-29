"""
API Client for Wally Dev CLI.

Handles all HTTP communication with the Wally platform API.
"""

from typing import Any, Callable, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import (
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_BACKOFF,
    DEFAULT_TIMEOUT,
    RETRY_STATUS_CODES,
    USER_AGENT,
)
from .exceptions import (
    APIError,
    ConnectionFailedError,
    InvalidCredentialsError,
    NormLockedError,
    NormNotFoundError,
    NotFoundError,
    PermissionDeniedError,
    RequestTimeoutError,
    ServerError,
    TestCaseNotFoundError,
    TokenExpiredError,
)
from .models import LoginResponse, Norm, Organization, Rule, TestCase, UserInfo


class WallyDevApiClient:
    """
    API client for Wally Dev CLI.

    Handles:
    - User authentication (login with username/password)
    - Norm locking/unlocking
    - Test case fetching and uploading
    - Automatic token refresh on expiration
    """

    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        organization_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        on_token_refresh: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize Wally Dev API client.

        Args:
            base_url: Wally API base URL
            access_token: JWT access token for authentication (optional for login)
            refresh_token: Refresh token for automatic token renewal
            organization_id: Organization ID for API calls
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            on_token_refresh: Callback called with (new_access_token, new_refresh_token) on refresh
        """
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.organization_id = organization_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.on_token_refresh = on_token_refresh
        self._is_refreshing = False
        self._session: Optional[requests.Session] = None

    def _get_session(self) -> requests.Session:
        """Get or create HTTP session with retry configuration."""
        if self._session is None:
            self._session = requests.Session()

            # Only retry on specific HTTP status codes, not on connection errors
            retry = Retry(
                total=self.max_retries,
                backoff_factor=DEFAULT_RETRY_BACKOFF,
                status_forcelist=RETRY_STATUS_CODES,
                raise_on_status=False,
                # Don't retry on connection errors - fail fast
                connect=0,
                read=0,
            )
            adapter = HTTPAdapter(max_retries=retry)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

        return self._session

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        _retry_on_401: bool = True,
    ) -> dict[str, Any]:
        """
        Make HTTP request to API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint (without base URL)
            data: Request body data
            params: Query parameters
            _retry_on_401: Internal flag to prevent infinite retry loops

        Returns:
            Response JSON data

        Raises:
            Various exceptions based on response status
        """
        url = f"{self.base_url}{endpoint}"
        session = self._get_session()
        headers = self._get_headers()

        try:
            response = session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=(DEFAULT_CONNECT_TIMEOUT, self.timeout),
            )

            # Handle different status codes
            if response.status_code == 200:
                return response.json() if response.content else {}
            elif response.status_code == 201:
                return response.json() if response.content else {}
            elif response.status_code == 204:
                return {}
            elif response.status_code == 401:
                # Could be invalid credentials or expired token
                if self.access_token and _retry_on_401 and self.refresh_token:
                    # Try to refresh the token
                    if self._try_refresh_token():
                        # Retry the request with the new token
                        return self._make_request(
                            method, endpoint, data, params, _retry_on_401=False
                        )
                if self.access_token:
                    raise TokenExpiredError()
                raise InvalidCredentialsError()
            elif response.status_code == 403:
                raise PermissionDeniedError()
            elif response.status_code == 404:
                raise NotFoundError()
            elif response.status_code == 409:
                # Conflict - norm is locked
                error_data = response.json() if response.content else {}
                raise NormLockedError(
                    message=error_data.get("message", "Norma já está bloqueada"),
                    status_code=409,
                    response=error_data,
                )
            elif response.status_code >= 500:
                raise ServerError(
                    message=f"Server error: {response.status_code}",
                    status_code=response.status_code,
                )
            else:
                error_data = response.json() if response.content else {}
                raise APIError(
                    message=error_data.get("message", f"API error: {response.status_code}"),
                    status_code=response.status_code,
                    response=error_data,
                )

        except (
            InvalidCredentialsError,
            TokenExpiredError,
            PermissionDeniedError,
            NotFoundError,
            NormLockedError,
            ServerError,
            APIError,
        ):
            # Re-raise our custom exceptions
            raise
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailedError(
                message=str(e),
                user_message=f"Não foi possível conectar ao servidor: {self.base_url}",
                hint="Verifique se a URL está correta e se o servidor está acessível.",
            ) from e
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(
                message=str(e),
                user_message="Tempo limite de conexão excedido.",
                hint="O servidor pode estar lento ou inacessível. Tente novamente.",
            ) from e
        except requests.exceptions.RequestException as e:
            raise APIError(message=str(e)) from e

    def _try_refresh_token(self) -> bool:
        """
        Attempt to refresh the access token using the refresh token.

        Returns:
            True if token was successfully refreshed, False otherwise
        """
        if self._is_refreshing or not self.refresh_token:
            return False

        self._is_refreshing = True
        try:
            result = self._refresh_token_request()
            if result:
                new_access_token: Optional[str] = result.get("access_token")
                new_refresh_token: Optional[str] = result.get("refresh_token", self.refresh_token)

                # Update client tokens
                self.access_token = new_access_token
                self.refresh_token = new_refresh_token

                # Notify callback to persist new tokens
                if self.on_token_refresh and new_access_token and new_refresh_token:
                    self.on_token_refresh(new_access_token, new_refresh_token)

                return True
        except Exception:
            # Refresh failed, will raise TokenExpiredError
            pass
        finally:
            self._is_refreshing = False

        return False

    def _refresh_token_request(self) -> Optional[dict[str, Any]]:
        """
        Make the actual refresh token API request.

        Returns:
            Response with new tokens or None on failure
        """
        url = f"{self.base_url}/auth/refresh-token"
        session = self._get_session()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }

        try:
            response = session.post(
                url,
                json={"refresh_token": self.refresh_token},
                headers=headers,
                timeout=(DEFAULT_CONNECT_TIMEOUT, self.timeout),
            )

            if response.status_code == 200:
                data: dict[str, Any] = response.json()
                if data.get("success", False):
                    return data
            return None
        except Exception:
            return None

    # =========================================================================
    # Authentication
    # =========================================================================

    def login(self, username: str, password: str) -> LoginResponse:
        """
        Login with username and password.

        Args:
            username: User email
            password: User password

        Returns:
            LoginResponse: Access token and user information

        Raises:
            InvalidCredentialsError: If credentials are invalid
        """
        response = self._make_request(
            "POST",
            "/auth/login",
            data={
                "username": username,
                "password": password,
            },
        )

        # Backend returns 200 with success: false on invalid credentials
        if not response.get("success", False):
            error_msg = response.get("error", "Credenciais inválidas")
            raise InvalidCredentialsError(user_message=error_msg)

        return LoginResponse.from_api_response(response)

    def list_organizations(self) -> list[Organization]:
        """
        List organizations accessible to the authenticated user.

        For regular users, returns organizations where user is owner or member.
        For superadmins, falls back to /organizations/all endpoint if no orgs found.

        Returns:
            List[Organization]: List of organizations

        Raises:
            TokenExpiredError: If token is expired
        """
        # Try user organizations first
        response = self._make_request("GET", "/organizations")
        organizations = self._parse_organizations_response(response)

        # If no organizations found, try superadmin endpoint
        # (will fail with 403 for non-superadmins, which is fine)
        if not organizations:
            try:
                response = self._make_request("GET", "/organizations/all")
                organizations = self._parse_organizations_response(response)
            except PermissionDeniedError:
                # User is not superadmin, return empty list
                pass

        return organizations

    def _parse_organizations_response(self, response: dict) -> list[Organization]:
        """
        Parse organizations from API response.

        API can return:
        - { success: true, data: { items: [...], total: N } } (paginated)
        - { success: true, data: { data: [...], total: N } } (nested data)
        - { success: true, data: [...] } (direct array)
        """
        if not isinstance(response, dict):
            return []

        data = response.get("data", response)

        # Handle paginated response: { items: [...] } or { data: [...] }
        if isinstance(data, dict):
            items = data.get("items") or data.get("data") or []
            if isinstance(items, list):
                return [Organization.from_api_response(org) for org in items]

        # Handle direct array
        elif isinstance(data, list):
            return [Organization.from_api_response(org) for org in data]

        return []

    def validate_token(self) -> UserInfo:
        """
        Validate access token and get user information.

        Returns:
            UserInfo: Authenticated user information

        Raises:
            TokenExpiredError: If token is expired
        """
        response = self._make_request("GET", "/auth/me")
        return UserInfo.from_api_response(response)

    # =========================================================================
    # Norms
    # =========================================================================

    def list_norms(self) -> list[Norm]:
        """
        List all norms accessible to the user.

        Returns:
            List[Norm]: List of norms

        Raises:
            PermissionDeniedError: If user doesn't have access
        """
        response = self._make_request("GET", f"/{self.organization_id}/norms")
        # API returns paginated response with 'items' array
        if isinstance(response, dict) and "items" in response:
            return [Norm.from_api_response(norm) for norm in response["items"]]
        elif isinstance(response, list):
            return [Norm.from_api_response(norm) for norm in response]
        return []

    def get_norm(self, norm_id: str) -> Norm:
        """
        Get norm by ID.

        Args:
            norm_id: Norm identifier

        Returns:
            Norm: Norm data

        Raises:
            NormNotFoundError: If norm doesn't exist
        """
        try:
            response = self._make_request("GET", f"/{self.organization_id}/norms/{norm_id}")
            return Norm.from_api_response(response)
        except NotFoundError as e:
            raise NormNotFoundError(message=f"Norma não encontrada: {norm_id}") from e

    def lock_norm(self, norm_id: str) -> Norm:
        """
        Lock a norm for editing.

        Sets lockedBy to current user, preventing others from editing.

        Args:
            norm_id: Norm identifier

        Returns:
            Norm: Updated norm data

        Raises:
            NormNotFoundError: If norm doesn't exist
            NormLockedError: If norm is already locked by another user
        """
        try:
            response = self._make_request("PATCH", f"/{self.organization_id}/norms/{norm_id}/lock")
            return Norm.from_api_response(response)
        except NotFoundError as e:
            raise NormNotFoundError(message=f"Norma não encontrada: {norm_id}") from e

    def unlock_norm(self, norm_id: str) -> Norm:
        """
        Unlock a norm.

        Sets lockedBy to null, allowing others to edit.

        Args:
            norm_id: Norm identifier

        Returns:
            Norm: Updated norm data

        Raises:
            NormNotFoundError: If norm doesn't exist
            PermissionDeniedError: If user doesn't own the lock
        """
        try:
            response = self._make_request(
                "PATCH", f"/{self.organization_id}/norms/{norm_id}/unlock"
            )
            return Norm.from_api_response(response)
        except NotFoundError as e:
            raise NormNotFoundError(message=f"Norma não encontrada: {norm_id}") from e

    # =========================================================================
    # Rules
    # =========================================================================

    def get_rules_by_norm(self, norm_id: str) -> list[Rule]:
        """
        Get all rules for a norm.

        Args:
            norm_id: Norm identifier

        Returns:
            List of rules
        """
        # Request with high limit to get all rules
        response = self._make_request(
            "GET", f"/{self.organization_id}/norms/{norm_id}/rules?limit=500"
        )
        # API returns paginated response with 'items' array
        if isinstance(response, dict) and "items" in response:
            return [Rule.from_api_response(r) for r in response["items"]]
        elif isinstance(response, dict) and "data" in response:
            return [Rule.from_api_response(r) for r in response["data"]]
        elif isinstance(response, list):
            return [Rule.from_api_response(r) for r in response]
        return []

    # =========================================================================
    # Test Cases
    # =========================================================================

    def get_testcases_by_norm(self, norm_id: str) -> list[TestCase]:
        """
        Get all test cases for a norm.

        Args:
            norm_id: Norm identifier

        Returns:
            List of test cases
        """
        response = self._make_request("GET", f"/{self.organization_id}/norms/{norm_id}/testcases")
        testcases_data = response.get("data", response) if isinstance(response, dict) else response
        if isinstance(testcases_data, list):
            return [TestCase.from_api_response(tc) for tc in testcases_data]
        return []

    def export_testcases_zip(self, norm_id: str, target: str = "html") -> bytes:
        """
        Export all test cases for a norm as a ZIP file.

        Args:
            norm_id: Norm identifier
            target: Target filter (html, react, angular, sonarqube). Default: html

        Returns:
            bytes: ZIP file content

        Raises:
            NormNotFoundError: If norm doesn't exist
            NotFoundError: If no test cases found for the target
        """
        url = f"{self.base_url}/{self.organization_id}/norms/{norm_id}/export"
        session = self._get_session()
        headers = self._get_headers()
        # Don't set Content-Type for file download
        headers.pop("Content-Type", None)

        try:
            response = session.get(
                url,
                params={"target": target},
                headers=headers,
                timeout=(DEFAULT_CONNECT_TIMEOUT, self.timeout),
            )

            if response.status_code == 200:
                return response.content
            elif response.status_code == 401:
                if self._try_refresh_token():
                    # Retry with new token
                    headers = self._get_headers()
                    headers.pop("Content-Type", None)
                    response = session.get(
                        url,
                        params={"target": target},
                        headers=headers,
                        timeout=(DEFAULT_CONNECT_TIMEOUT, self.timeout),
                    )
                    if response.status_code == 200:
                        return response.content
                raise TokenExpiredError()
            elif response.status_code == 404:
                raise NormNotFoundError(
                    message=f"Norma não encontrada ou sem casos de teste: {norm_id}"
                )
            else:
                raise APIError(
                    message=f"Erro ao exportar casos de teste: {response.status_code}",
                    status_code=response.status_code,
                )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailedError(
                message=str(e),
                user_message=f"Não foi possível conectar ao servidor: {self.base_url}",
            ) from e
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(
                message=str(e),
                user_message="Tempo limite de conexão excedido.",
            ) from e

    def export_examples_zip(self, norm_id: str) -> bytes:
        """
        Export all examples for a norm as a ZIP file.

        Args:
            norm_id: Norm identifier

        Returns:
            bytes: ZIP file content

        Raises:
            NormNotFoundError: If norm doesn't exist or no examples found
        """
        url = f"{self.base_url}/{self.organization_id}/norms/{norm_id}/examples/export"
        session = self._get_session()
        headers = self._get_headers()
        headers.pop("Content-Type", None)

        try:
            response = session.get(
                url,
                headers=headers,
                timeout=(DEFAULT_CONNECT_TIMEOUT, self.timeout),
            )

            if response.status_code == 200:
                return response.content
            elif response.status_code == 401:
                if self._try_refresh_token():
                    headers = self._get_headers()
                    headers.pop("Content-Type", None)
                    response = session.get(
                        url,
                        headers=headers,
                        timeout=(DEFAULT_CONNECT_TIMEOUT, self.timeout),
                    )
                    if response.status_code == 200:
                        return response.content
                raise TokenExpiredError()
            elif response.status_code == 404:
                raise NormNotFoundError(message=f"Norma não encontrada ou sem examples: {norm_id}")
            else:
                raise APIError(
                    message=f"Erro ao exportar examples: {response.status_code}",
                    status_code=response.status_code,
                )
        except requests.exceptions.ConnectionError as e:
            raise ConnectionFailedError(
                message=str(e),
                user_message=f"Não foi possível conectar ao servidor: {self.base_url}",
            ) from e
        except requests.exceptions.Timeout as e:
            raise RequestTimeoutError(
                message=str(e),
                user_message="Tempo limite de conexão excedido.",
            ) from e

    def get_testcase(self, testcase_id: str) -> TestCase:
        """
        Get a single test case by ID.

        Args:
            testcase_id: Test case identifier

        Returns:
            TestCase: Test case data

        Raises:
            TestCaseNotFoundError: If test case doesn't exist
        """
        try:
            response = self._make_request("GET", f"/{self.organization_id}/testcases/{testcase_id}")
            return TestCase.from_api_response(response)
        except NotFoundError as e:
            raise TestCaseNotFoundError(
                message=f"Caso de teste não encontrado: {testcase_id}"
            ) from e

    def update_testcase(self, testcase_id: str, data: dict[str, Any]) -> TestCase:
        """
        Update a test case.

        Args:
            testcase_id: Test case identifier
            data: Fields to update

        Returns:
            TestCase: Updated test case data

        Raises:
            TestCaseNotFoundError: If test case doesn't exist
        """
        try:
            response = self._make_request(
                "PUT", f"/{self.organization_id}/testcases/{testcase_id}", data=data
            )
            return TestCase.from_api_response(response)
        except NotFoundError as e:
            raise TestCaseNotFoundError(
                message=f"Caso de teste não encontrado: {testcase_id}"
            ) from e

    def bulk_update_testcases(self, testcases: list[dict[str, Any]]) -> list[TestCase]:
        """
        Update multiple test cases in bulk.

        Args:
            testcases: List of test case data with IDs

        Returns:
            List of updated test cases
        """
        response = self._make_request(
            "PATCH", f"/{self.organization_id}/testcases/bulk", data={"testcases": testcases}
        )
        results = response.get("data", response) if isinstance(response, dict) else response
        if isinstance(results, list):
            return [TestCase.from_api_response(tc) for tc in results]
        return []

    def create_testcase(
        self,
        norm_id: str,
        rule_id: str,
        name: str,
        description: Optional[str] = None,
        language: str = "html",
        code: Optional[str] = None,
        finder_code: Optional[str] = None,
        validator_code: Optional[str] = None,
    ) -> TestCase:
        """
        Create a new test case.

        Args:
            norm_id: Norm identifier
            rule_id: Rule identifier
            name: Test case name
            description: Test case description
            language: Target language (html, react, angular, etc.)
            code: Combined test case code
            finder_code: Finder module code
            validator_code: Validator module code

        Returns:
            TestCase: Created test case
        """
        data: dict[str, Any] = {
            "name": name,
            "description": description,
            "normId": norm_id,
            "ruleId": rule_id,
            "language": language,
            "enabled": True,
            "status": "draft",
            "tags": [language, "auto-generated"],
        }

        if code:
            data["code"] = code

        # Store finder and validator in metadata for reference
        metadata: dict[str, Any] = {"generatedBy": "wally-dev-cli"}
        if finder_code:
            metadata["finderCode"] = finder_code
        if validator_code:
            metadata["validatorCode"] = validator_code
        data["metadata"] = metadata

        response = self._make_request("POST", f"/{self.organization_id}/testcases", data=data)
        return TestCase.from_api_response(response)

    def create_example(
        self,
        testcase_id: str,
        name: str,
        html_content: str,
        is_compliant: bool,
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create an example for a test case.

        Args:
            testcase_id: Test case identifier
            name: Example name (e.g., "compliant-example.html")
            html_content: HTML content of the example
            is_compliant: Whether the example should pass validation
            description: Optional description

        Returns:
            Created example data
        """
        data = {
            "name": name,
            "html": html_content,
            "expectedResult": "pass" if is_compliant else "fail",
            "isCompliant": is_compliant,
            "description": description
            or f"{'Compliant' if is_compliant else 'Non-compliant'} example",
            "fileType": "html",
        }

        response = self._make_request(
            "POST", f"/{self.organization_id}/testcases/{testcase_id}/examples", data=data
        )
        return response

    # =========================================================================
    # Files
    # =========================================================================

    def get_testcase_files(self, testcase_id: str) -> list[dict[str, Any]]:
        """
        Get all files associated with a test case.

        Args:
            testcase_id: Test case identifier

        Returns:
            List of file metadata dicts with keys: _id, name, path, content, etc.
        """
        response = self._make_request(
            "GET", f"/{self.organization_id}/files/by-testcase/{testcase_id}"
        )
        if isinstance(response, dict):
            return response.get("data", response) if "data" in response else []
        return response if isinstance(response, list) else []

    def update_file_content(self, file_id: str, content: str) -> dict[str, Any]:
        """
        Update file content (text content via JSON).

        Args:
            file_id: File identifier
            content: New file content

        Returns:
            Updated file metadata
        """
        response = self._make_request(
            "PATCH", f"/{self.organization_id}/files/{file_id}/content", data={"content": content}
        )
        return response

    def update_file_binary(self, file_id: str, content: bytes) -> dict[str, Any]:
        """
        Update file content as binary data.

        Args:
            file_id: File identifier
            content: Binary content

        Returns:
            Updated file metadata
        """
        url = f"{self.base_url}/{self.organization_id}/files/{file_id}/binary"
        session = self._get_session()
        headers = {
            "Content-Type": "application/octet-stream",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
        }

        response = session.put(url, data=content, headers=headers, timeout=self.timeout)

        if response.status_code == 404:
            raise NotFoundError(message=f"Arquivo não encontrado: {file_id}")
        if response.status_code >= 400:
            raise APIError(message=f"Erro ao atualizar arquivo: {response.text}")

        result: dict[str, Any] = response.json()
        return result

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file.

        Args:
            file_id: File identifier

        Returns:
            True if deleted successfully
        """
        try:
            self._make_request("DELETE", f"/{self.organization_id}/files/{file_id}")
            return True
        except NotFoundError:
            return False

    def close(self) -> None:
        """Close the HTTP session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self) -> "WallyDevApiClient":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()
