"""
Data models for Wally Dev CLI.

Uses Pydantic for type safety, validation, and serialization.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class Organization(BaseModel):
    """Represents a user organization."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique identifier")
    name: str = Field(..., description="Organization name")
    description: Optional[str] = Field(None, description="Organization description")
    role: Optional[str] = Field(None, description="User role in this organization")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Organization":
        """Create Organization from API response."""
        return cls(
            _id=data.get("_id", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description"),
            role=data.get("role"),
        )


class Norm(BaseModel):
    """Represents an accessibility norm/standard."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique identifier")
    name: str = Field(..., description="Norm name")
    version: Optional[str] = Field(None, description="Norm version")
    description: Optional[str] = Field(None, description="Norm description")
    reference_link: Optional[str] = Field(None, alias="referenceLink", description="Reference URL")
    rules_count: Optional[int] = Field(None, alias="rulesCount", description="Number of rules")
    tags: list[str] = Field(default_factory=list, description="Associated tags")
    locked_by: Optional[str] = Field(None, alias="lockedBy", description="User who locked the norm")
    locked_at: Optional[datetime] = Field(
        None, alias="lockedAt", description="When norm was locked"
    )
    organization_id: Optional[str] = Field(
        None, alias="organizationId", description="Organization ID"
    )

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Norm":
        """Create Norm from API response."""
        return cls(
            _id=data.get("_id", data.get("id", "")),
            name=data.get("name", ""),
            version=data.get("version"),
            description=data.get("description"),
            referenceLink=data.get("referenceLink"),
            rulesCount=data.get("rulesCount"),
            tags=data.get("tags", []),
            lockedBy=data.get("lockedBy"),
            lockedAt=data.get("lockedAt"),
            organizationId=data.get("organizationId"),
        )


class Rule(BaseModel):
    """Represents an accessibility rule within a norm."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique identifier")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    norm_id: str = Field(..., alias="normId", description="Parent norm ID")
    severity: Optional[str] = Field(None, description="Severity level")
    category: Optional[str] = Field(None, description="Rule category")
    is_automatable: Optional[bool] = Field(
        None, alias="isAutomatable", description="Whether rule can be automated"
    )
    wcag_criteria: list[str] = Field(default_factory=list, alias="wcagCriteria")
    test_cases_count: Optional[int] = Field(None, alias="testCasesCount")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Rule":
        """Create Rule from API response."""
        return cls(
            _id=data.get("_id", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description"),
            normId=data.get("normId", ""),
            severity=data.get("severity"),
            category=data.get("category"),
            isAutomatable=data.get("isAutomatable"),
            wcagCriteria=data.get("wcagCriteria", []),
            testCasesCount=data.get("testCasesCount"),
        )


class ExampleTestCase(BaseModel):
    """Represents an example within a test case (pass/fail scenario)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique identifier")
    name: str = Field(..., description="Example name")
    description: Optional[str] = Field(None, description="Example description")
    html: str = Field(..., description="HTML content to test")
    expected_result: str = Field(
        ..., alias="expectedResult", description="Expected result (pass/fail)"
    )
    explanation: Optional[str] = Field(None, description="Explanation of the result")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ExampleTestCase":
        """Create ExampleTestCase from API response."""
        return cls(
            _id=data.get("_id", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description"),
            html=data.get("html", ""),
            expectedResult=data.get("expectedResult", ""),
            explanation=data.get("explanation"),
        )


class TestCase(BaseModel):
    """Represents a test case for an accessibility rule."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="Unique identifier")
    name: str = Field(..., description="Test case name")
    description: Optional[str] = Field(None, description="Test case description")
    rule_id: str = Field(..., alias="ruleId", description="Parent rule ID")
    norm_id: Optional[str] = Field(None, alias="normId", description="Parent norm ID")
    code: Optional[str] = Field(None, description="Test case implementation code")
    language: Optional[str] = Field(None, description="Target language (HTML, REACT, etc)")
    enabled: bool = Field(True, description="Whether test case is active")
    examples: list[ExampleTestCase] = Field(default_factory=list, description="Example scenarios")
    tags: list[str] = Field(default_factory=list, description="Associated tags")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TestCase":
        """Create TestCase from API response."""
        examples = [ExampleTestCase.from_api_response(ex) for ex in data.get("examples", [])]
        return cls(
            _id=data.get("_id", data.get("id", "")),
            name=data.get("name", ""),
            description=data.get("description"),
            ruleId=data.get("ruleId", ""),
            normId=data.get("normId"),
            code=data.get("code"),
            language=data.get("language"),
            enabled=data.get("enabled", True),
            examples=examples,
            tags=data.get("tags", []),
            createdAt=data.get("createdAt"),
            updatedAt=data.get("updatedAt"),
        )

    def to_file_dict(self) -> dict[str, Any]:
        """Convert to dictionary for file storage."""
        return {
            "_id": self.id,
            "name": self.name,
            "description": self.description,
            "ruleId": self.rule_id,
            "normId": self.norm_id,
            "code": self.code,
            "language": self.language,
            "enabled": self.enabled,
            "examples": [
                {
                    "_id": ex.id,
                    "name": ex.name,
                    "description": ex.description,
                    "html": ex.html,
                    "expectedResult": ex.expected_result,
                    "explanation": ex.explanation,
                }
                for ex in self.examples
            ],
            "tags": self.tags,
        }


class UserInfo(BaseModel):
    """Represents authenticated user information."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., alias="_id", description="User ID")
    email: str = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    organization_id: Optional[str] = Field(None, alias="organizationId")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "UserInfo":
        """Create UserInfo from API response."""
        return cls(
            _id=data.get("_id", data.get("id", "")),
            email=data.get("email", ""),
            name=data.get("name"),
            organizationId=data.get("organizationId"),
        )


class TestCaseRunResult(BaseModel):
    """Result of running a test case locally."""

    test_case_id: str
    example_id: str
    passed: bool
    expected: str
    actual: str
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    details: Optional[dict[str, Any]] = None


class LoginResponse(BaseModel):
    """Response from login endpoint."""

    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(..., alias="accessToken", description="JWT access token")
    refresh_token: Optional[str] = Field(
        None, alias="refreshToken", description="JWT refresh token"
    )
    token_type: str = Field(default="Bearer", alias="tokenType")
    expires_in: Optional[int] = Field(
        None, alias="expiresIn", description="Token expiration in seconds"
    )
    user: UserInfo = Field(..., description="Authenticated user info")

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LoginResponse":
        """Create LoginResponse from API response."""
        user_data = data.get("user", {})
        return cls(
            accessToken=data.get("accessToken", data.get("access_token", "")),
            refreshToken=data.get("refreshToken", data.get("refresh_token")),
            tokenType=data.get("tokenType", data.get("token_type", "Bearer")),
            expiresIn=data.get("expiresIn", data.get("expires_in")),
            user=UserInfo.from_api_response(user_data),
        )
