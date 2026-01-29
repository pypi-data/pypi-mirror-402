"""Tests for API client module."""

import pytest
import responses

from wally_dev.api_client import WallyDevApiClient
from wally_dev.exceptions import (
    APIError,
    InvalidCredentialsError,
    NormLockedError,
    NormNotFoundError,
    NotFoundError,
    PermissionDeniedError,
    ServerError,
    TestCaseNotFoundError,
    TokenExpiredError,
)


class TestWallyDevApiClient:
    """Tests for WallyDevApiClient class."""

    @pytest.fixture
    def client(self) -> WallyDevApiClient:
        """Create an API client for testing."""
        return WallyDevApiClient(
            base_url="https://api.wally.test",
            access_token="test-token",
            organization_id="org123",
        )

    @pytest.fixture
    def client_with_refresh(self) -> WallyDevApiClient:
        """Create an API client with refresh token."""
        return WallyDevApiClient(
            base_url="https://api.wally.test",
            access_token="test-token",
            refresh_token="test-refresh-token",
            organization_id="org123",
        )

    # =========================================================================
    # Initialization Tests
    # =========================================================================

    def test_client_initialization(self):
        """Test client initialization with parameters."""
        client = WallyDevApiClient(
            base_url="https://api.test/",
            access_token="token123",
            organization_id="org456",
            timeout=60,
        )
        assert client.base_url == "https://api.test"  # trailing slash removed
        assert client.access_token == "token123"
        assert client.organization_id == "org456"
        assert client.timeout == 60

    def test_client_context_manager(self, client: WallyDevApiClient):
        """Test client works as context manager."""
        with client as c:
            assert c is client
        # Should be closed after exit
        assert client._session is None

    # =========================================================================
    # Headers Tests
    # =========================================================================

    def test_get_headers_with_token(self, client: WallyDevApiClient):
        """Test headers include authorization."""
        headers = client._get_headers()
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers

    def test_get_headers_without_token(self):
        """Test headers without token."""
        client = WallyDevApiClient(
            base_url="https://api.test",
            organization_id="org123",
        )
        headers = client._get_headers()
        assert "Authorization" not in headers

    # =========================================================================
    # HTTP Response Handling Tests
    # =========================================================================

    @responses.activate
    def test_make_request_success_200(self, client: WallyDevApiClient):
        """Test successful 200 response."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1",
            json={"_id": "norm1", "name": "Test Norm"},
            status=200,
        )

        result = client._make_request("GET", "/org123/norms/norm1")
        assert result["name"] == "Test Norm"

    @responses.activate
    def test_make_request_success_201(self, client: WallyDevApiClient):
        """Test successful 201 response."""
        responses.add(
            responses.POST,
            "https://api.wally.test/org123/testcases",
            json={"_id": "tc1", "name": "New TestCase"},
            status=201,
        )

        result = client._make_request("POST", "/org123/testcases", data={"name": "New"})
        assert result["name"] == "New TestCase"

    @responses.activate
    def test_make_request_success_204(self, client: WallyDevApiClient):
        """Test successful 204 response (no content)."""
        responses.add(
            responses.DELETE,
            "https://api.wally.test/org123/testcases/tc1",
            status=204,
        )

        result = client._make_request("DELETE", "/org123/testcases/tc1")
        assert result == {}

    @responses.activate
    def test_make_request_401_no_token(self):
        """Test 401 without token raises InvalidCredentialsError."""
        client = WallyDevApiClient(
            base_url="https://api.wally.test",
            organization_id="org123",
        )
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            status=401,
        )

        with pytest.raises(InvalidCredentialsError):
            client._make_request("GET", "/org123/norms")

    @responses.activate
    def test_make_request_401_with_token_no_refresh(self, client: WallyDevApiClient):
        """Test 401 with token but no refresh token raises TokenExpiredError."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            status=401,
        )

        with pytest.raises(TokenExpiredError):
            client._make_request("GET", "/org123/norms")

    @responses.activate
    def test_make_request_403(self, client: WallyDevApiClient):
        """Test 403 raises PermissionDeniedError."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            status=403,
        )

        with pytest.raises(PermissionDeniedError):
            client._make_request("GET", "/org123/norms")

    @responses.activate
    def test_make_request_404(self, client: WallyDevApiClient):
        """Test 404 raises NotFoundError."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/notfound",
            status=404,
        )

        with pytest.raises(NotFoundError):
            client._make_request("GET", "/org123/norms/notfound")

    @responses.activate
    def test_make_request_409_norm_locked(self, client: WallyDevApiClient):
        """Test 409 raises NormLockedError."""
        responses.add(
            responses.PATCH,
            "https://api.wally.test/org123/norms/norm1/lock",
            json={"message": "Norm is locked by user@test.com"},
            status=409,
        )

        with pytest.raises(NormLockedError):
            client._make_request("PATCH", "/org123/norms/norm1/lock")

    @responses.activate
    def test_make_request_500(self, client: WallyDevApiClient):
        """Test 500 raises ServerError."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            status=500,
        )

        with pytest.raises(ServerError):
            client._make_request("GET", "/org123/norms")

    @responses.activate
    def test_make_request_other_error(self, client: WallyDevApiClient):
        """Test other status codes raise APIError."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            json={"message": "Bad Request"},
            status=400,
        )

        with pytest.raises(APIError):
            client._make_request("GET", "/org123/norms")

    # =========================================================================
    # Authentication Tests
    # =========================================================================

    @responses.activate
    def test_login_success(self, client: WallyDevApiClient):
        """Test successful login."""
        responses.add(
            responses.POST,
            "https://api.wally.test/auth/login",
            json={
                "success": True,
                "accessToken": "new-token",
                "refreshToken": "new-refresh",
                "user": {
                    "_id": "user123",
                    "email": "test@example.com",
                    "name": "Test User",
                },
            },
            status=200,
        )

        result = client.login("test@example.com", "password123")
        assert result.access_token == "new-token"
        assert result.user.email == "test@example.com"

    @responses.activate
    def test_login_invalid_credentials(self, client: WallyDevApiClient):
        """Test login with invalid credentials."""
        responses.add(
            responses.POST,
            "https://api.wally.test/auth/login",
            json={"success": False, "error": "Invalid password"},
            status=200,
        )

        with pytest.raises(InvalidCredentialsError):
            client.login("test@example.com", "wrong-password")

    @responses.activate
    def test_validate_token(self, client: WallyDevApiClient):
        """Test token validation."""
        responses.add(
            responses.GET,
            "https://api.wally.test/auth/me",
            json={
                "_id": "user123",
                "email": "test@example.com",
                "name": "Test User",
            },
            status=200,
        )

        result = client.validate_token()
        assert result.email == "test@example.com"

    # =========================================================================
    # Norms API Tests
    # =========================================================================

    @responses.activate
    def test_list_norms(self, client: WallyDevApiClient):
        """Test listing norms."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            json={
                "items": [
                    {"_id": "norm1", "name": "WCAG 2.1"},
                    {"_id": "norm2", "name": "NBR 17225"},
                ]
            },
            status=200,
        )

        norms = client.list_norms()
        assert len(norms) == 2
        assert norms[0].name == "WCAG 2.1"

    @responses.activate
    def test_list_norms_as_array(self, client: WallyDevApiClient):
        """Test listing norms when API returns array directly."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            json=[
                {"_id": "norm1", "name": "WCAG 2.1"},
            ],
            status=200,
        )

        norms = client.list_norms()
        assert len(norms) == 1

    @responses.activate
    def test_get_norm(self, client: WallyDevApiClient):
        """Test getting a single norm."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1",
            json={"_id": "norm1", "name": "WCAG 2.1", "version": "2.1"},
            status=200,
        )

        norm = client.get_norm("norm1")
        assert norm.id == "norm1"
        assert norm.name == "WCAG 2.1"

    @responses.activate
    def test_get_norm_not_found(self, client: WallyDevApiClient):
        """Test getting non-existent norm."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/notfound",
            status=404,
        )

        with pytest.raises(NormNotFoundError):
            client.get_norm("notfound")

    @responses.activate
    def test_lock_norm(self, client: WallyDevApiClient):
        """Test locking a norm."""
        responses.add(
            responses.PATCH,
            "https://api.wally.test/org123/norms/norm1/lock",
            json={"_id": "norm1", "name": "WCAG 2.1", "lockedBy": "user123"},
            status=200,
        )

        norm = client.lock_norm("norm1")
        assert norm.locked_by == "user123"

    @responses.activate
    def test_unlock_norm(self, client: WallyDevApiClient):
        """Test unlocking a norm."""
        responses.add(
            responses.PATCH,
            "https://api.wally.test/org123/norms/norm1/unlock",
            json={"_id": "norm1", "name": "WCAG 2.1", "lockedBy": None},
            status=200,
        )

        norm = client.unlock_norm("norm1")
        assert norm.locked_by is None

    # =========================================================================
    # Rules API Tests
    # =========================================================================

    @responses.activate
    def test_get_rules_by_norm(self, client: WallyDevApiClient):
        """Test getting rules for a norm."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1/rules",
            json={
                "items": [
                    {"_id": "rule1", "name": "Alt Text", "normId": "norm1"},
                    {"_id": "rule2", "name": "Lang Attr", "normId": "norm1"},
                ]
            },
            status=200,
        )

        rules = client.get_rules_by_norm("norm1")
        assert len(rules) == 2
        assert rules[0].name == "Alt Text"

    @responses.activate
    def test_get_rules_by_norm_with_data_key(self, client: WallyDevApiClient):
        """Test getting rules when API returns 'data' key."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1/rules",
            json={
                "data": [
                    {"_id": "rule1", "name": "Alt Text", "normId": "norm1"},
                ]
            },
            status=200,
        )

        rules = client.get_rules_by_norm("norm1")
        assert len(rules) == 1

    # =========================================================================
    # TestCases API Tests
    # =========================================================================

    @responses.activate
    def test_get_testcases_by_norm(self, client: WallyDevApiClient):
        """Test getting testcases for a norm."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1/testcases",
            json={
                "data": [
                    {"_id": "tc1", "name": "Test 1", "ruleId": "rule1"},
                ]
            },
            status=200,
        )

        testcases = client.get_testcases_by_norm("norm1")
        assert len(testcases) == 1

    @responses.activate
    def test_get_testcase(self, client: WallyDevApiClient):
        """Test getting a single testcase."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/testcases/tc1",
            json={"_id": "tc1", "name": "Test 1", "ruleId": "rule1"},
            status=200,
        )

        testcase = client.get_testcase("tc1")
        assert testcase.id == "tc1"

    @responses.activate
    def test_get_testcase_not_found(self, client: WallyDevApiClient):
        """Test getting non-existent testcase."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/testcases/notfound",
            status=404,
        )

        with pytest.raises(TestCaseNotFoundError):
            client.get_testcase("notfound")

    @responses.activate
    def test_update_testcase(self, client: WallyDevApiClient):
        """Test updating a testcase."""
        responses.add(
            responses.PUT,
            "https://api.wally.test/org123/testcases/tc1",
            json={"_id": "tc1", "name": "Updated Test", "ruleId": "rule1"},
            status=200,
        )

        testcase = client.update_testcase("tc1", {"name": "Updated Test"})
        assert testcase.name == "Updated Test"

    @responses.activate
    def test_create_testcase(self, client: WallyDevApiClient):
        """Test creating a testcase."""
        responses.add(
            responses.POST,
            "https://api.wally.test/org123/testcases",
            json={
                "_id": "tc-new",
                "name": "New TestCase",
                "ruleId": "rule1",
                "normId": "norm1",
            },
            status=201,
        )

        testcase = client.create_testcase(
            norm_id="norm1",
            rule_id="rule1",
            name="New TestCase",
            description="Test description",
            language="html",
        )
        assert testcase.id == "tc-new"
        assert testcase.name == "New TestCase"

    @responses.activate
    def test_create_example(self, client: WallyDevApiClient):
        """Test creating an example."""
        responses.add(
            responses.POST,
            "https://api.wally.test/org123/testcases/tc1/examples",
            json={
                "_id": "ex-new",
                "name": "compliant-example.html",
                "isCompliant": True,
            },
            status=201,
        )

        result = client.create_example(
            testcase_id="tc1",
            name="compliant-example.html",
            html_content="<img alt='test'>",
            is_compliant=True,
        )
        assert result["name"] == "compliant-example.html"

    @responses.activate
    def test_bulk_update_testcases(self, client: WallyDevApiClient):
        """Test bulk updating testcases."""
        responses.add(
            responses.PATCH,
            "https://api.wally.test/org123/testcases/bulk",
            json={
                "data": [
                    {"_id": "tc1", "name": "Updated 1", "ruleId": "rule1"},
                    {"_id": "tc2", "name": "Updated 2", "ruleId": "rule2"},
                ]
            },
            status=200,
        )

        testcases = client.bulk_update_testcases(
            [
                {"_id": "tc1", "name": "Updated 1"},
                {"_id": "tc2", "name": "Updated 2"},
            ]
        )
        assert len(testcases) == 2

    # =========================================================================
    # Export Tests
    # =========================================================================

    @responses.activate
    def test_export_testcases_zip(self, client: WallyDevApiClient):
        """Test exporting testcases as ZIP."""
        zip_content = b"PK\x03\x04..."  # Fake ZIP header
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1/export",
            body=zip_content,
            status=200,
            content_type="application/zip",
        )

        result = client.export_testcases_zip("norm1", target="html")
        assert result == zip_content

    @responses.activate
    def test_export_testcases_zip_not_found(self, client: WallyDevApiClient):
        """Test export when norm not found."""
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/notfound/export",
            status=404,
        )

        with pytest.raises(NormNotFoundError):
            client.export_testcases_zip("notfound")

    @responses.activate
    def test_export_examples_zip(self, client: WallyDevApiClient):
        """Test exporting examples as ZIP."""
        zip_content = b"PK\x03\x04..."
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms/norm1/examples/export",
            body=zip_content,
            status=200,
            content_type="application/zip",
        )

        result = client.export_examples_zip("norm1")
        assert result == zip_content

    # =========================================================================
    # Token Refresh Tests
    # =========================================================================

    @responses.activate
    def test_token_refresh_on_401(self, client_with_refresh: WallyDevApiClient):
        """Test automatic token refresh on 401."""
        # First request returns 401
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            status=401,
        )
        # Refresh token request succeeds
        responses.add(
            responses.POST,
            "https://api.wally.test/auth/refresh-token",
            json={
                "success": True,
                "access_token": "new-access-token",
                "refresh_token": "new-refresh-token",
            },
            status=200,
        )
        # Retry request succeeds
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            json={"items": []},
            status=200,
        )

        # Track token refresh callback
        tokens_refreshed = []
        client_with_refresh.on_token_refresh = lambda a, r: tokens_refreshed.append((a, r))

        result = client_with_refresh._make_request("GET", "/org123/norms")
        assert result == {"items": []}
        assert client_with_refresh.access_token == "new-access-token"
        assert len(tokens_refreshed) == 1

    @responses.activate
    def test_token_refresh_failure_raises_expired(self, client_with_refresh: WallyDevApiClient):
        """Test that failed refresh raises TokenExpiredError."""
        # First request returns 401
        responses.add(
            responses.GET,
            "https://api.wally.test/org123/norms",
            status=401,
        )
        # Refresh fails
        responses.add(
            responses.POST,
            "https://api.wally.test/auth/refresh-token/",
            json={"success": False},
            status=200,
        )

        with pytest.raises(TokenExpiredError):
            client_with_refresh._make_request("GET", "/org123/norms")

    # =========================================================================
    # Session Management Tests
    # =========================================================================

    def test_close_session(self, client: WallyDevApiClient):
        """Test closing the session."""
        # Force session creation
        _ = client._get_session()
        assert client._session is not None

        client.close()
        assert client._session is None

    def test_get_session_creates_session(self, client: WallyDevApiClient):
        """Test that _get_session creates a session."""
        assert client._session is None
        session = client._get_session()
        assert session is not None
        assert client._session is session

        # Second call returns same session
        session2 = client._get_session()
        assert session2 is session
