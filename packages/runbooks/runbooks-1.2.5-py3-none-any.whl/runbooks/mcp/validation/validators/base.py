# =============================================================================
# Base MCP Validator
# =============================================================================
# ADLC v3.0.0 - Abstract base class for MCP cross-validation
# =============================================================================

"""Base validator class for MCP cross-validation."""

import json
import subprocess
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from ..core.constants import (
    ACCURACY_TARGET,
    BACKOFF_BASE,
    DEFAULT_TIMEOUT,
    MAX_BACKOFF,
    MAX_RETRIES,
)
from ..core.exceptions import (
    MCPAuthenticationError,
    MCPTimeoutError,
    MCPValidationError,
)
from ..core.types import (
    FieldComparison,
    ServerValidationResult,
    ValidationResult,
    ValidationStatus,
)


class BaseValidator(ABC):
    """Abstract base class for MCP validators.

    Provides common functionality for cross-validating MCP server outputs
    against native CLI APIs.
    """

    # Override in subclasses
    server_name: str = "unknown"
    profile_env_var: str = "AWS_PROFILE"
    native_command: str = ""

    def __init__(
        self,
        profile: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
        target_accuracy: float = ACCURACY_TARGET,
    ) -> None:
        """Initialize the validator.

        Args:
            profile: AWS/Azure profile to use (overrides env var)
            timeout: Command timeout in seconds
            target_accuracy: Target accuracy percentage (default 99.5%)
        """
        self.profile = profile
        self.timeout = timeout
        self.target_accuracy = target_accuracy
        self._validation_results: list[ValidationResult] = []

    @abstractmethod
    def get_mcp_data(self) -> dict[str, Any]:
        """Fetch data from MCP server.

        Returns:
            Dictionary containing MCP server response
        """
        pass

    @abstractmethod
    def get_native_data(self) -> dict[str, Any]:
        """Fetch data from native CLI API.

        Returns:
            Dictionary containing native API response
        """
        pass

    @abstractmethod
    def compare_results(self, mcp_data: dict[str, Any], native_data: dict[str, Any]) -> list[FieldComparison]:
        """Compare MCP and native API results field by field.

        Args:
            mcp_data: Data from MCP server
            native_data: Data from native API

        Returns:
            List of field comparisons
        """
        pass

    def run_cli_command(
        self,
        command: str,
        profile: str | None = None,
    ) -> dict[str, Any]:
        """Execute a CLI command and return JSON output.

        Args:
            command: CLI command to execute
            profile: Optional profile override

        Returns:
            Parsed JSON response

        Raises:
            MCPValidationError: If command fails
            MCPTimeoutError: If command times out
            MCPAuthenticationError: If authentication fails
        """
        effective_profile = profile or self.profile

        # Add profile to command if specified
        if effective_profile and "--profile" not in command:
            command = f"{command} --profile {effective_profile}"

        # Add JSON output format
        if "--output json" not in command and "az " not in command:
            command = f"{command} --output json"

        retries = 0
        last_error: Exception | None = None

        while retries < MAX_RETRIES:
            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )

                if result.returncode != 0:
                    stderr = result.stderr.strip()

                    # Check for authentication errors
                    if any(err in stderr.lower() for err in ["expired", "unauthorized", "access denied", "invalid"]):
                        raise MCPAuthenticationError(
                            f"Authentication failed: {stderr}",
                            server=self.server_name,
                            profile=effective_profile,
                        )

                    raise MCPValidationError(
                        f"Command failed: {stderr}",
                        server=self.server_name,
                        details={"command": command, "exit_code": result.returncode},
                    )

                return json.loads(result.stdout)

            except subprocess.TimeoutExpired:
                raise MCPTimeoutError(
                    f"Command timed out after {self.timeout}s",
                    server=self.server_name,
                    timeout_seconds=self.timeout,
                    operation=command,
                )

            except json.JSONDecodeError as e:
                raise MCPValidationError(
                    f"Failed to parse JSON response: {e}",
                    server=self.server_name,
                    details={"command": command},
                )

            except MCPAuthenticationError:
                raise

            except Exception as e:
                last_error = e
                retries += 1
                if retries < MAX_RETRIES:
                    backoff = min(BACKOFF_BASE * (2**retries), MAX_BACKOFF)
                    time.sleep(backoff)

        raise MCPValidationError(
            f"Command failed after {MAX_RETRIES} retries: {last_error}",
            server=self.server_name,
        )

    def calculate_accuracy(self, comparisons: list[FieldComparison]) -> float:
        """Calculate accuracy percentage from field comparisons.

        Args:
            comparisons: List of field comparisons

        Returns:
            Accuracy percentage (0-100)
        """
        if not comparisons:
            return 100.0

        matched = sum(1 for c in comparisons if c.match)
        return (matched / len(comparisons)) * 100

    def add_validation_result(
        self,
        check_name: str,
        status: ValidationStatus,
        message: str,
        field_comparisons: list[FieldComparison] | None = None,
        duration_ms: float | None = None,
        error: str | None = None,
    ) -> None:
        """Add a validation result to the internal list.

        Args:
            check_name: Name of the check
            status: Check status
            message: Human-readable message
            field_comparisons: Field comparison results
            duration_ms: Check duration in milliseconds
            error: Error message if applicable
        """
        self._validation_results.append(
            ValidationResult(
                check_name=check_name,
                status=status,
                message=message,
                field_comparisons=field_comparisons or [],
                duration_ms=duration_ms,
                error=error,
            )
        )

    def validate(self) -> ServerValidationResult:
        """Run the full validation process.

        Returns:
            ServerValidationResult with all validation details
        """
        started_at = datetime.utcnow()
        self._validation_results = []
        all_comparisons: list[FieldComparison] = []
        error_message: str | None = None

        try:
            # Step 1: Fetch MCP data
            start_time = time.time()
            try:
                mcp_data = self.get_mcp_data()
                self.add_validation_result(
                    check_name="mcp_data_fetch",
                    status=ValidationStatus.PASSED,
                    message="Successfully fetched MCP data",
                    duration_ms=(time.time() - start_time) * 1000,
                )
            except Exception as e:
                self.add_validation_result(
                    check_name="mcp_data_fetch",
                    status=ValidationStatus.ERROR,
                    message=f"Failed to fetch MCP data: {e}",
                    duration_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                )
                raise

            # Step 2: Fetch native API data
            start_time = time.time()
            try:
                native_data = self.get_native_data()
                self.add_validation_result(
                    check_name="native_api_fetch",
                    status=ValidationStatus.PASSED,
                    message="Successfully fetched native API data",
                    duration_ms=(time.time() - start_time) * 1000,
                )
            except Exception as e:
                self.add_validation_result(
                    check_name="native_api_fetch",
                    status=ValidationStatus.ERROR,
                    message=f"Failed to fetch native API data: {e}",
                    duration_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                )
                raise

            # Step 3: Compare results
            start_time = time.time()
            try:
                all_comparisons = self.compare_results(mcp_data, native_data)
                accuracy = self.calculate_accuracy(all_comparisons)
                status = ValidationStatus.PASSED if accuracy >= self.target_accuracy else ValidationStatus.FAILED
                self.add_validation_result(
                    check_name="data_comparison",
                    status=status,
                    message=f"Data comparison: {accuracy:.2f}% accuracy",
                    field_comparisons=all_comparisons,
                    duration_ms=(time.time() - start_time) * 1000,
                )
            except Exception as e:
                self.add_validation_result(
                    check_name="data_comparison",
                    status=ValidationStatus.ERROR,
                    message=f"Failed to compare data: {e}",
                    duration_ms=(time.time() - start_time) * 1000,
                    error=str(e),
                )
                raise

        except Exception as e:
            error_message = str(e)

        # Calculate overall accuracy
        accuracy = self.calculate_accuracy(all_comparisons) if all_comparisons else 0.0
        overall_status = (
            ValidationStatus.PASSED
            if accuracy >= self.target_accuracy and error_message is None
            else ValidationStatus.FAILED
            if error_message is None
            else ValidationStatus.ERROR
        )

        return ServerValidationResult(
            server_name=self.server_name,
            profile=self.profile,
            native_command=self.native_command,
            status=overall_status,
            accuracy=accuracy,
            target_accuracy=self.target_accuracy,
            validation_results=self._validation_results,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            error=error_message,
        )
