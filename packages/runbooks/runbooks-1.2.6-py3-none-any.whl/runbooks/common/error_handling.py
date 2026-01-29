"""
Error Handling Enhancement for runbooks package - Enterprise Error Management

Provides standardized error handling decorators and utilities that build upon the existing
enhanced_exception_handler.py infrastructure while adding commonly needed patterns.

Following KISS & DRY principles - enhance existing structure with practical decorators.
"""

import sys
import time
from functools import wraps
from typing import Callable, Dict, Any, Optional

from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError, ProfileNotFound

from .rich_utils import print_error, print_warning, print_info, print_success, console
from .enhanced_exception_handler import (
    EnterpriseExceptionHandler,
    ErrorContext,
    create_exception_handler,
    enhanced_error_handling,
)


def handle_aws_errors(module_name: str = "runbooks", enable_recovery: bool = True):
    """
    Decorator for standardized AWS error handling with Rich CLI formatting.

    Provides consistent error handling across all runbooks modules with:
    - AWS-specific error classification and guidance
    - Profile override recommendations
    - Rich CLI formatted error messages
    - Automatic recovery suggestions

    Args:
        module_name: Name of the module using this decorator
        enable_recovery: Enable interactive error recovery workflows

    Usage:
        @handle_aws_errors(module_name="finops")
        def my_aws_operation(profile=None, region=None, **kwargs):
            # Your AWS operation code here
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Extract common parameters for error context
            profile = kwargs.get("profile")
            region = kwargs.get("region", "ap-southeast-2")
            operation = kwargs.get("operation", f.__name__)

            # Create error context
            context = ErrorContext(
                module_name=module_name,
                operation=operation,
                aws_profile=profile,
                aws_region=region,
                user_context=kwargs,
            )

            # Create exception handler
            handler = create_exception_handler(module_name, enable_rich_output=True)

            try:
                return f(*args, **kwargs)

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "Unknown")
                service = e.operation_name if hasattr(e, "operation_name") else "AWS"

                # Handle specific AWS errors with targeted guidance
                if error_code == "ExpiredToken":
                    print_error("AWS SSO token expired")
                    profile_name = profile or "your-profile"
                    print_info(f"Run: [bold green]aws sso login --profile {profile_name}[/]")
                    sys.exit(1)

                elif error_code in ["AccessDenied", "UnauthorizedOperation", "Forbidden"]:
                    print_error(f"Access denied: {e.response['Error']['Message']}")
                    print_warning("Check IAM permissions for this operation")

                    # Provide profile recommendations
                    if operation in ["finops", "cost-analysis"]:
                        print_info("Try using billing profile: [bold green]--profile BILLING_PROFILE[/]")
                    elif operation in ["inventory", "organizations"]:
                        print_info("Try using management profile: [bold green]--profile MANAGEMENT_PROFILE[/]")
                    elif operation in ["operate", "resource-management"]:
                        print_info("Try using ops profile: [bold green]--profile CENTRALISED_OPS_PROFILE[/]")

                    sys.exit(1)

                elif error_code in ["Throttling", "ThrottlingException", "RequestLimitExceeded"]:
                    print_warning(f"AWS API throttling detected: {error_code}")
                    print_info("Implementing automatic retry with backoff...")
                    time.sleep(2)  # Basic backoff
                    return f(*args, **kwargs)  # Retry once

                else:
                    # Use enterprise exception handler for complex cases
                    enhanced_error = handler.handle_aws_error(e, context, operation)
                    if enable_recovery and enhanced_error.retry_possible:
                        handler.create_error_recovery_workflow(enhanced_error, interactive=False)
                    sys.exit(1)

            except (NoCredentialsError, PartialCredentialsError, ProfileNotFound) as e:
                enhanced_error = handler.handle_credentials_error(e, context)
                if enable_recovery:
                    handler.create_error_recovery_workflow(enhanced_error, interactive=True)
                sys.exit(1)

            except ConnectionError as e:
                print_error(f"Network connection failed: {str(e)}")
                print_info("Check your internet connection and try again")
                sys.exit(1)

            except Exception as e:
                print_error(f"Unexpected error in {operation}: {str(e)}")
                if kwargs.get("debug") or kwargs.get("verbose"):
                    console.print_exception()
                sys.exit(1)

        return wrapper

    return decorator


def handle_performance_errors(target_seconds: int = 30, module_name: str = "runbooks"):
    """
    Decorator for performance monitoring and error handling.

    Monitors operation execution time and provides performance guidance
    when operations exceed enterprise targets.

    Args:
        target_seconds: Target execution time in seconds
        module_name: Name of the module for error context

    Usage:
        @handle_performance_errors(target_seconds=15, module_name="finops")
        def my_operation(**kwargs):
            # Your operation code here
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            operation = kwargs.get("operation", f.__name__)

            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time

                # Performance feedback
                if execution_time <= target_seconds:
                    print_success(f"⚡ Performance: {execution_time:.1f}s (target: <{target_seconds}s)")
                else:
                    print_warning(f"⚠️ Performance: {execution_time:.1f}s (exceeded {target_seconds}s target)")

                    # Provide optimization suggestions
                    if execution_time > target_seconds * 2:  # Significantly exceeded
                        print_info("Performance optimization suggestions:")
                        print_info(f"  • Consider using --parallel for {operation}")
                        print_info("  • Try a different AWS region for better performance")
                        print_info("  • Check for API throttling or network issues")

                        # Create performance error for enterprise tracking
                        context = ErrorContext(
                            module_name=module_name,
                            operation=operation,
                            performance_context={
                                "execution_time": execution_time,
                                "target_seconds": target_seconds,
                                "performance_ratio": execution_time / target_seconds,
                            },
                        )

                        handler = create_exception_handler(module_name)
                        handler.handle_performance_error(operation, execution_time, target_seconds, context)

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                print_error(f"❌ Operation failed after {execution_time:.1f}s: {str(e)}")
                raise

        return wrapper

    return decorator


def handle_validation_errors(f: Callable) -> Callable:
    """
    Decorator for data validation error handling.

    Provides clear guidance for data validation failures with
    suggestions for correction.

    Usage:
        @handle_validation_errors
        def my_validation_function(data, **kwargs):
            # Your validation code here
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)

        except (ValueError, TypeError) as e:
            error_msg = str(e)

            if "profile" in error_msg.lower():
                print_error(f"Profile validation error: {error_msg}")
                print_info("Check available profiles: [bold green]aws configure list-profiles[/]")

            elif "region" in error_msg.lower():
                print_error(f"Region validation error: {error_msg}")
                print_info("Use valid AWS region like: [bold green]ap-southeast-2, ap-southeast-6, eu-west-1[/]")

            elif "format" in error_msg.lower():
                print_error(f"Format validation error: {error_msg}")
                print_info("Supported formats: [bold green]json, csv, table, pdf, markdown[/]")

            else:
                print_error(f"Data validation error: {error_msg}")
                print_info("Review input parameters and try again")

            sys.exit(1)

        except Exception as e:
            print_error(f"Validation failed: {str(e)}")
            raise

    return wrapper


def graceful_degradation(fallback_function: Optional[Callable] = None, enable_fallback: bool = True):
    """
    Decorator for graceful degradation with fallback operations.

    Automatically attempts fallback operations when primary operation fails,
    providing seamless user experience with transparent recovery.

    Args:
        fallback_function: Optional fallback function to use
        enable_fallback: Enable automatic fallback attempts

    Usage:
        @graceful_degradation(fallback_function=simple_analysis)
        def complex_analysis(**kwargs):
            # Complex operation that might fail

        # Or with automatic fallback detection
        @graceful_degradation()
        def main_operation(**kwargs):
            # Will attempt fallback_operation if this fails

        def fallback_operation(**kwargs):
            # Simpler fallback version
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            operation = kwargs.get("operation", f.__name__)

            try:
                print_info(f"🚀 Attempting primary operation: {operation}")
                return f(*args, **kwargs)

            except Exception as primary_error:
                print_warning(f"⚠️ Primary operation failed: {operation}")
                print_info(f"Error: {str(primary_error)}")

                if not enable_fallback:
                    raise primary_error

                # Try fallback function if provided
                if fallback_function:
                    try:
                        print_info(f"🔄 Attempting fallback: {fallback_function.__name__}")
                        result = fallback_function(*args, **kwargs)
                        print_success(f"✅ Fallback operation succeeded: {fallback_function.__name__}")
                        return result

                    except Exception as fallback_error:
                        print_error(f"❌ Fallback operation failed: {fallback_function.__name__}")
                        print_error(f"Primary error: {str(primary_error)}")
                        print_error(f"Fallback error: {str(fallback_error)}")
                        raise primary_error

                # Try to find automatic fallback based on naming convention
                fallback_name = f"fallback_{f.__name__}"
                if hasattr(f.__module__, fallback_name):
                    try:
                        fallback_func = getattr(f.__module__, fallback_name)
                        print_info(f"🔄 Attempting automatic fallback: {fallback_name}")
                        result = fallback_func(*args, **kwargs)
                        print_success(f"✅ Automatic fallback succeeded: {fallback_name}")
                        return result

                    except Exception:
                        pass

                # No fallback available, raise original error
                print_error("❌ No fallback available, operation failed")
                raise primary_error

        return wrapper

    return decorator


def enterprise_error_context(module_name: str):
    """
    Context manager for enterprise error handling with comprehensive logging.

    Provides enterprise-grade error handling with audit trails, performance
    monitoring, and comprehensive error analysis.

    Usage:
        with enterprise_error_context("finops") as ctx:
            ctx.set_operation("cost_analysis")
            ctx.set_profile("BILLING_PROFILE")
            # Your operation code here
    """

    class EnterpriseErrorContext:
        def __init__(self, module_name: str):
            self.module_name = module_name
            self.handler = create_exception_handler(module_name)
            self.context = ErrorContext(module_name=module_name, operation="unknown")

        def set_operation(self, operation: str):
            self.context.operation = operation

        def set_profile(self, profile: str):
            self.context.aws_profile = profile

        def set_region(self, region: str):
            self.context.aws_region = region

        def add_user_context(self, **kwargs):
            self.context.user_context.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            if exc_value is not None:
                enhanced_error = self.handler.handle_exception(exc_value, self.context, {"context_manager": True})

                # Try recovery for retryable errors
                if enhanced_error.retry_possible:
                    recovery_success = self.handler.create_error_recovery_workflow(enhanced_error, interactive=False)
                    if recovery_success:
                        return True  # Suppress exception

            return False  # Let exception propagate

    return EnterpriseErrorContext(module_name)


# Utility functions for common error scenarios
def validate_aws_profile(profile: str) -> bool:
    """
    Validate AWS profile exists and is accessible.

    Args:
        profile: AWS profile name to validate

    Returns:
        True if profile is valid and accessible

    Raises:
        SystemExit if profile validation fails
    """
    try:
        import boto3

        session = boto3.Session(profile_name=profile)
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        print_success(f"Profile validation successful: {profile}")
        print_info(f"Account: {identity.get('Account', 'Unknown')}")
        print_info(f"User: {identity.get('Arn', 'Unknown')}")
        return True

    except ProfileNotFound:
        print_error(f"AWS profile not found: {profile}")
        print_info("Check available profiles: [bold green]aws configure list-profiles[/]")
        sys.exit(1)

    except Exception as e:
        print_error(f"Profile validation failed: {profile}")
        print_error(f"Error: {str(e)}")
        sys.exit(1)


def check_aws_connectivity(region: str = "ap-southeast-2") -> bool:
    """
    Check basic AWS connectivity and service availability.

    Args:
        region: AWS region to test connectivity

    Returns:
        True if connectivity is successful
    """
    try:
        import boto3

        session = boto3.Session()
        sts = session.client("sts", region_name=region)
        sts.get_caller_identity()
        print_success(f"AWS connectivity verified: {region}")
        return True

    except Exception as e:
        print_warning(f"AWS connectivity issue: {str(e)}")
        print_info("Check internet connection and AWS service status")
        return False
