# =============================================================================
# MCP Validation Exceptions
# =============================================================================
# ADLC v3.0.0 - Custom exceptions for MCP validation framework
# =============================================================================

"""Custom exceptions for MCP validation framework."""

from typing import Any


class MCPValidationError(Exception):
    """Base exception for MCP validation errors."""

    def __init__(
        self,
        message: str,
        server: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCPValidationError.

        Args:
            message: Error message
            server: MCP server name that caused the error
            details: Additional error details
        """
        self.server = server
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for evidence logging."""
        return {
            "error_type": self.__class__.__name__,
            "message": str(self),
            "server": self.server,
            "details": self.details,
        }


class MCPAccuracyError(MCPValidationError):
    """Raised when MCP validation accuracy is below threshold."""

    def __init__(
        self,
        message: str,
        server: str,
        actual_accuracy: float,
        required_accuracy: float,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCPAccuracyError.

        Args:
            message: Error message
            server: MCP server name
            actual_accuracy: Actual accuracy achieved (0-100)
            required_accuracy: Required accuracy threshold (0-100)
            details: Additional error details
        """
        self.actual_accuracy = actual_accuracy
        self.required_accuracy = required_accuracy
        super().__init__(message, server, details)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for evidence logging."""
        result = super().to_dict()
        result.update(
            {
                "actual_accuracy": self.actual_accuracy,
                "required_accuracy": self.required_accuracy,
                "accuracy_gap": self.required_accuracy - self.actual_accuracy,
            }
        )
        return result


class MCPTimeoutError(MCPValidationError):
    """Raised when MCP or native API call times out."""

    def __init__(
        self,
        message: str,
        server: str,
        timeout_seconds: float,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCPTimeoutError.

        Args:
            message: Error message
            server: MCP server name
            timeout_seconds: Timeout duration in seconds
            operation: Operation that timed out
            details: Additional error details
        """
        self.timeout_seconds = timeout_seconds
        self.operation = operation
        super().__init__(message, server, details)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for evidence logging."""
        result = super().to_dict()
        result.update(
            {
                "timeout_seconds": self.timeout_seconds,
                "operation": self.operation,
            }
        )
        return result


class MCPConfigError(MCPValidationError):
    """Raised when MCP configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_file: str | None = None,
        missing_fields: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCPConfigError.

        Args:
            message: Error message
            config_file: Path to the problematic config file
            missing_fields: List of missing required fields
            details: Additional error details
        """
        self.config_file = config_file
        self.missing_fields = missing_fields or []
        super().__init__(message, server=None, details=details)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for evidence logging."""
        result = super().to_dict()
        result.update(
            {
                "config_file": self.config_file,
                "missing_fields": self.missing_fields,
            }
        )
        return result


class MCPAuthenticationError(MCPValidationError):
    """Raised when authentication fails for AWS/Azure APIs."""

    def __init__(
        self,
        message: str,
        server: str,
        profile: str | None = None,
        auth_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCPAuthenticationError.

        Args:
            message: Error message
            server: MCP server name
            profile: AWS profile or Azure subscription that failed
            auth_type: Authentication type (SSO, IAM, etc.)
            details: Additional error details
        """
        self.profile = profile
        self.auth_type = auth_type
        super().__init__(message, server, details)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for evidence logging."""
        result = super().to_dict()
        result.update(
            {
                "profile": self.profile,
                "auth_type": self.auth_type,
            }
        )
        return result


class MCPComparisonError(MCPValidationError):
    """Raised when MCP vs native API comparison fails."""

    def __init__(
        self,
        message: str,
        server: str,
        field_path: str,
        mcp_value: Any,
        native_value: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize MCPComparisonError.

        Args:
            message: Error message
            server: MCP server name
            field_path: JSONPath or field name where mismatch occurred
            mcp_value: Value from MCP server
            native_value: Value from native API
            details: Additional error details
        """
        self.field_path = field_path
        self.mcp_value = mcp_value
        self.native_value = native_value
        super().__init__(message, server, details)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for evidence logging."""
        result = super().to_dict()
        result.update(
            {
                "field_path": self.field_path,
                "mcp_value": str(self.mcp_value),
                "native_value": str(self.native_value),
            }
        )
        return result
