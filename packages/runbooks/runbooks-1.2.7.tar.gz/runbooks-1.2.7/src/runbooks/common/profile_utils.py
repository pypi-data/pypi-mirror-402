# Profile utilities for multi-account AWS operations with enterprise caching
import os
import time
import boto3
import subprocess
from typing import Optional, List, Dict, Any
from runbooks.common.rich_utils import console
from datetime import datetime
from botocore.config import Config
from botocore.exceptions import TokenRetrievalError, NoCredentialsError, ClientError

# Enhanced caching system for enterprise performance
_profile_cache: Dict[str, str] = {}
_validation_cache: Dict[str, bool] = {}  # Cache for profile validation results
_cache_timestamp: Optional[float] = None
_cache_ttl: int = 300  # 5 minutes TTL for enterprise session management
_session_id: Optional[str] = None  # Track session consistency
_session_cache: Dict[str, boto3.Session] = {}  # Cache AWS sessions
_warnings_shown: set = set()  # v1.1.23 BUG FIX: Track warnings to prevent duplicates

# Timeout configuration for AWS API calls (prevents execution flow hangs)
_AWS_CLIENT_CONFIG = Config(
    connect_timeout=30,  # Connection timeout: 30 seconds
    read_timeout=60,  # Read timeout: 60 seconds
    retries={"max_attempts": 3, "mode": "adaptive"},
)


def _get_session_id() -> str:
    """Generate consistent session ID for cache scoping"""
    global _session_id
    if _session_id is None:
        _session_id = f"session_{int(time.time())}"
    return _session_id


def _detect_operation_type(service_name: Optional[str], api_call: Optional[str]) -> Optional[str]:
    """
    Detect operation type from AWS service name or API call.

    Auto-detection logic maps AWS services and API calls to appropriate operation types:
    - Billing services: Cost Explorer (ce), Cost and Usage Reports (cur), Budgets
    - Management services: Organizations, SSO, Identity Store, IAM
    - Centralized ops services: CloudWatch, Logs, X-Ray, Lambda
    - Operational services: All other AWS services (EC2, S3, RDS, etc.)

    Args:
        service_name: AWS service name (e.g., 'ce', 'organizations', 'ec2')
        api_call: AWS API call name (e.g., 'GetCostAndUsage', 'ListAccounts')

    Returns:
        Operation type string ("billing", "management", "centralised_ops") or None for default

    Example:
        >>> _detect_operation_type(service_name='ce', api_call=None)
        'billing'
        >>> _detect_operation_type(service_name='organizations', api_call='ListAccounts')
        'management'
        >>> _detect_operation_type(service_name='ec2', api_call=None)
        None  # Uses default operational type
    """
    # Billing operation detection
    billing_services = ["ce", "cur", "budgets", "pricing", "cost-explorer", "billing-cost-management"]
    billing_apis = [
        "GetCostAndUsage",
        "GetCostForecast",
        "DescribeReportDefinitions",
        "GetCostCategories",
        "GetSavingsPlansUtilization",
    ]

    # Management operation detection
    management_services = [
        "organizations",
        "sso",
        "identitystore",
        "iam",
        "cloudtrail",
        "well-architected",
        "core-mcp",
        "well-architected-security",
    ]
    management_apis = [
        "ListAccounts",
        "DescribeOrganization",
        "ListOrganizationalUnits",
        "ListInstancesForAccessPortal",
        "GetUser",
        "CreateTrail",
    ]

    # Centralized operations detection
    centralised_ops_services = [
        "cloudwatch",
        "logs",
        "xray",
        "lambda",
        "cloudwatch-appsignals",
        "lambda-tool",
        "terraform-mcp",
        "aws-diagram",
    ]
    centralised_ops_apis = [
        "PutMetricData",
        "GetMetricStatistics",
        "DescribeLogGroups",
        "GetTraceSummaries",
        "Invoke",
        "CreateLogGroup",
    ]

    # Normalize inputs for comparison
    service_lower = service_name.lower() if service_name else ""
    api_lower = api_call if api_call else ""

    # Detection logic with service name priority
    if service_lower in billing_services or any(api in api_lower for api in billing_apis):
        return "billing"
    elif service_lower in management_services or any(api in api_lower for api in management_apis):
        return "management"
    elif service_lower in centralised_ops_services or any(api in api_lower for api in centralised_ops_apis):
        return "operational"  # Maps to CENTRALISED_OPS_PROFILE
    else:
        return None  # Use default operation_type


def get_profile_for_operation(
    operation_type: str = "operational",
    user_specified_profile: Optional[str] = None,
    profiles: Optional[List[str]] = None,
    service_name: Optional[str] = None,
    api_call: Optional[str] = None,
    silent: bool = False,
) -> str:
    """
    Enhanced profile resolution with intelligent routing and auto-detection.

    Priority Order:
    1. User-specified profile (--profile parameter) - HIGHEST PRIORITY
    2. Auto-detected operation type (from service_name or api_call) - NEW
    3. Explicit operation_type parameter
    4. Environment variable mapping (per operation type)
    5. Default profile fallback

    Args:
        operation_type: Type of operation (billing, management, operational). Default: "operational"
        user_specified_profile: User-provided profile via --profile parameter
        profiles: List of profiles for multi-account operations (deprecated)
        service_name: AWS service name for auto-detection (e.g., 'ce', 'organizations')
        api_call: AWS API call name for auto-detection (e.g., 'GetCostAndUsage')
        silent: Suppress profile logging messages. Default: False

    Returns:
        Profile name to use for the operation

    Auto-Detection Examples:
        >>> # Auto-detect billing profile from service name
        >>> get_profile_for_operation(service_name='ce')
        '${BILLING_PROFILE}'

        >>> # Auto-detect management profile from API call
        >>> get_profile_for_operation(service_name='organizations', api_call='ListAccounts')
        '${MANAGEMENT_PROFILE}'

        >>> # Explicit operation type
        >>> get_profile_for_operation(operation_type='billing')
        '${BILLING_PROFILE}'

        >>> # User override (highest priority)
        >>> get_profile_for_operation(user_specified_profile='my-custom-profile')
        'my-custom-profile'

    Caching Strategy:
    - Cache profile resolution to prevent redundant AWS API calls
    - Session-scoped caching with 5-minute TTL
    - Only log profile selection once per session to reduce noise
    """
    global _cache_timestamp
    current_time = time.time()

    # PRIORITY 1: User-specified profile ALWAYS takes precedence
    if user_specified_profile and user_specified_profile != "default":
        profile_cache_key = f"{_get_session_id()}:{user_specified_profile}"

        # Return cached result if still valid and within TTL
        if profile_cache_key in _profile_cache and _cache_timestamp and current_time - _cache_timestamp < _cache_ttl:
            return _profile_cache[profile_cache_key]

        # Update cache timestamp only when cache is actually refreshed
        if not _cache_timestamp or current_time - _cache_timestamp >= _cache_ttl:
            _profile_cache.clear()
            _validation_cache.clear()
            _cache_timestamp = current_time

        available_profiles = boto3.Session().available_profiles
        if user_specified_profile in available_profiles:
            # REMOVED: Verbose profile logging consolidated in finops.py dashboard
            # Cache the result to prevent duplicate logging
            _profile_cache[profile_cache_key] = user_specified_profile
            return user_specified_profile
        else:
            console.log(f"[red]Error: Profile '{user_specified_profile}' not found in AWS config[/]")
            console.log(f"[yellow]Available profiles: {', '.join(available_profiles)}[/]")
            raise SystemExit(1)

    # PRIORITY 2: Auto-detect operation type from service/API (NEW)
    if service_name or api_call:
        detected_type = _detect_operation_type(service_name, api_call)
        if detected_type:
            operation_type = detected_type

    # Create profile-specific cache key
    profile_cache_key = f"{_get_session_id()}:{operation_type}"

    # Return cached result if still valid and within TTL
    if profile_cache_key in _profile_cache and _cache_timestamp and current_time - _cache_timestamp < _cache_ttl:
        return _profile_cache[profile_cache_key]

    # Update cache timestamp only when cache is actually refreshed
    if not _cache_timestamp or current_time - _cache_timestamp >= _cache_ttl:
        _profile_cache.clear()
        _validation_cache.clear()
        _cache_timestamp = current_time

    available_profiles = boto3.Session().available_profiles

    # PRIORITY 3: AWS_PROFILE environment variable (standard AWS convention)
    aws_profile = os.getenv("AWS_PROFILE")
    if aws_profile and aws_profile in available_profiles:
        _profile_cache[profile_cache_key] = aws_profile
        return aws_profile

    # PRIORITY 4: Operation-specific environment variables
    profile_map = {
        "billing": os.getenv("BILLING_PROFILE"),
        "management": os.getenv("MANAGEMENT_PROFILE"),
        "operational": os.getenv("CENTRALISED_OPS_PROFILE"),
    }

    env_profile = profile_map.get(operation_type)
    if env_profile and env_profile in available_profiles:
        _profile_cache[profile_cache_key] = env_profile
        return env_profile

    # PRIORITY 5: Default profile fallback
    if "default" in available_profiles:
        _profile_cache[profile_cache_key] = "default"
        return "default"
    elif available_profiles:
        # Use first available profile if no default
        first_profile = available_profiles[0]
        # v1.1.23 BUG FIX: Show warning only once to prevent duplicates
        warning_key = f"no_default_profile_{first_profile}"
        if warning_key not in _warnings_shown:
            console.log(f"[yellow]Warning: No default profile found, using: {first_profile}[/]")
            _warnings_shown.add(warning_key)
        _profile_cache[profile_cache_key] = first_profile
        return first_profile
    else:
        console.log("[red]Error: No AWS profiles configured[/]")
        console.log("[yellow]Please run: aws configure sso or aws configure[/]")
        raise SystemExit(1)


def validate_sso_session(profile_name: str) -> bool:
    """
    Check if SSO session is valid for profile.

    Validates AWS SSO session by attempting to retrieve caller identity.
    Useful for detecting expired tokens before making actual API calls.

    Args:
        profile_name: AWS profile name to validate

    Returns:
        True if session valid, False if expired/missing

    Example:
        >>> if not validate_sso_session('my-sso-profile'):
        ...     print("Session expired, please run: aws sso login")
        ...     sys.exit(1)
    """
    try:
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client("sts", config=_AWS_CLIENT_CONFIG)
        sts_client.get_caller_identity()
        return True
    except Exception as e:
        error_str = str(e)
        # Specific SSO/token error detection
        if any(err in error_str for err in ["ExpiredToken", "InvalidToken", "TokenRetrievalError"]):
            return False
        # Re-raise unexpected errors
        raise


def validate_profile_access(profile_name: str, operation_description: str = "") -> bool:
    """
    Validate that the specified profile has proper AWS access with caching.

    Args:
        profile_name: AWS profile name to validate
        operation_description: Optional description of the operation (for logging)

    Returns:
        True if profile has access, False otherwise
    """
    # Check cache first to avoid redundant validations
    global _cache_timestamp
    current_time = time.time()
    cache_key = f"validation:{profile_name}"

    if cache_key in _validation_cache and _cache_timestamp and current_time - _cache_timestamp < _cache_ttl:
        return _validation_cache[cache_key]

    try:
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client("sts", config=_AWS_CLIENT_CONFIG)
        sts_client.get_caller_identity()

        # Cache successful validation
        _validation_cache[cache_key] = True
        return True
    except Exception as e:
        # Cache failed validation for shorter time to allow retry
        _validation_cache[cache_key] = False
        console.log(f"[yellow]Profile {profile_name} validation failed: {e}[/]")
        return False


def create_session_with_auto_refresh(profile_name: str, max_retries: int = 2, timeout: int = 60) -> boto3.Session:
    """
    Create boto3 session with automatic SSO token refresh on expiry.

    Prevents TokenRetrievalError in long-running automation workflows by
    automatically detecting expired SSO tokens and triggering aws sso login.

    Args:
        profile_name: AWS profile name (from ~/.aws/config)
        max_retries: Number of SSO login retry attempts (default: 2)
        timeout: SSO login subprocess timeout in seconds (default: 60)

    Returns:
        boto3.Session: Authenticated session with valid SSO token

    Raises:
        SystemExit: If SSO token refresh fails after max_retries

    Example:
        >>> # Long-running job with auto-refresh
        >>> session = create_session_with_auto_refresh('my-sso-profile')
        >>> ec2 = session.client('ec2')
        >>> # Session remains valid even after 15+ minutes
    """
    from .rich_utils import print_warning, print_info, print_success, print_error

    for attempt in range(1, max_retries + 1):
        try:
            session = boto3.Session(profile_name=profile_name)

            # Validate token by calling STS GetCallerIdentity
            sts_client = session.client("sts", config=_AWS_CLIENT_CONFIG)
            sts_client.get_caller_identity()

            # Token valid - return session
            return session

        except (TokenRetrievalError, ClientError) as e:
            if attempt < max_retries:
                print_warning(f"AWS SSO token expired (attempt {attempt}/{max_retries})")
                print_info("Attempting automatic token refresh...")

                # Execute aws sso login
                sso_login_cmd = ["aws", "sso", "login", "--profile", profile_name]

                try:
                    result = subprocess.run(sso_login_cmd, capture_output=True, text=True, timeout=timeout, check=False)

                    if result.returncode == 0:
                        print_success("SSO login completed successfully")
                        time.sleep(2)  # Allow token propagation
                        continue
                    else:
                        print_error(f"SSO login failed: {result.stderr}")

                except subprocess.TimeoutExpired:
                    print_error(f"SSO login timed out after {timeout}s")

            # Max retries exhausted or unrecoverable error
            print_error("SSO token auto-refresh failed")
            print_info("Manual intervention required:")
            print_info(f"   Run: aws sso login --profile {profile_name}")
            raise SystemExit(1)

    # Should never reach here
    raise SystemExit(1)


def get_account_id_from_profile(profile_name: str) -> Optional[str]:
    """
    Extract account ID from AWS profile.

    Args:
        profile_name: AWS profile name

    Returns:
        Account ID if available, None otherwise
    """
    try:
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client("sts")
        response = sts_client.get_caller_identity()
        return response.get("Account")
    except Exception:
        return None


def discover_available_profiles() -> Dict[str, List[str]]:
    """
    Discover available AWS profiles categorized by operation type.

    Analyzes all AWS profiles in ~/.aws/config and categorizes them based on
    naming patterns and role information. Useful for understanding available
    profile segregation before operations.

    Returns:
        Dictionary mapping operation types to list of matching profiles:
        {
            "billing": ["profile1", "profile2"],
            "management": ["profile3", "profile4"],
            "operational": ["profile5", "profile6", "profile7"]
        }

    Example:
        >>> profiles = discover_available_profiles()
        >>> print(f"Billing profiles: {', '.join(profiles['billing'])}")
        Billing profiles: ${BILLING_PROFILE}
    """
    available_profiles = boto3.Session().available_profiles
    categorized = {"billing": [], "management": [], "operational": []}

    # Categorization patterns (case-insensitive)
    billing_keywords = ["billing", "cost", "finance"]
    management_keywords = ["management", "admin", "organization", "sso", "iam"]
    ops_keywords = ["ops", "operational", "centralised", "centralized", "cloudwatch"]

    for profile in available_profiles:
        profile_lower = profile.lower()

        # Categorize based on profile name patterns
        if any(keyword in profile_lower for keyword in billing_keywords):
            categorized["billing"].append(profile)
        elif any(keyword in profile_lower for keyword in management_keywords):
            categorized["management"].append(profile)
        elif any(keyword in profile_lower for keyword in ops_keywords):
            categorized["operational"].append(profile)
        else:
            # Default to operational for uncategorized profiles
            categorized["operational"].append(profile)

    return categorized


def auto_discover_enterprise_profiles() -> Dict[str, Optional[str]]:
    """
    Auto-discover enterprise AWS SSO profiles for streamlined initialization.

    Searches for profiles matching common enterprise naming patterns:
    - *Billing* or *billing* for BILLING_PROFILE
    - *Management* or *management* for MANAGEMENT_PROFILE
    - *Ops* or *ops* for CENTRALISED_OPS_PROFILE
    - Single account profiles for SINGLE_AWS_PROFILE

    Returns:
        Dict mapping profile types to discovered profile names
    """
    available_profiles = boto3.Session().available_profiles
    discovered = {"billing": None, "management": None, "centralised_ops": None, "single_aws": None}

    # Search patterns for enterprise profiles
    for profile in available_profiles:
        profile_lower = profile.lower()

        # Billing profile detection
        if ("billing" in profile_lower or "cost" in profile_lower) and not discovered["billing"]:
            discovered["billing"] = profile

        # Management profile detection
        elif ("management" in profile_lower or "admin" in profile_lower) and not discovered["management"]:
            discovered["management"] = profile

        # Operations profile detection
        elif (
            "ops" in profile_lower or "operational" in profile_lower or "centralised" in profile_lower
        ) and not discovered["centralised_ops"]:
            discovered["centralised_ops"] = profile

        # Single account detection (typically shorter names or containing 'single')
        elif ("single" in profile_lower or len(profile) < 20) and not discovered["single_aws"]:
            discovered["single_aws"] = profile

    # Log discovered profiles for transparency
    for profile_type, profile_name in discovered.items():
        if profile_name:
            console.log(f"[green]✅ Auto-discovered {profile_type}: {profile_name}[/green]")
        else:
            console.log(f"[yellow]⚠️ No profile found for {profile_type}[/yellow]")

    return discovered


def setup_enterprise_environment_variables(discovered_profiles: Optional[Dict[str, Optional[str]]] = None) -> None:
    """
    Setup enterprise environment variables from discovered profiles.

    Args:
        discovered_profiles: Optional pre-discovered profiles dict
    """
    if not discovered_profiles:
        discovered_profiles = auto_discover_enterprise_profiles()

    # Set environment variables if not already set
    env_mappings = {
        "BILLING_PROFILE": discovered_profiles.get("billing"),
        "MANAGEMENT_PROFILE": discovered_profiles.get("management"),
        "CENTRALISED_OPS_PROFILE": discovered_profiles.get("centralised_ops"),
        "SINGLE_AWS_PROFILE": discovered_profiles.get("single_aws"),
    }

    for env_var, profile_name in env_mappings.items():
        if profile_name and not os.getenv(env_var):
            os.environ[env_var] = profile_name
            console.log(f"[blue]📋 Set {env_var}={profile_name}[/blue]")
        elif os.getenv(env_var):
            console.log(f"[dim]Using existing {env_var}={os.getenv(env_var)}[/dim]")


def create_cost_session(profile_name: Optional[str] = None) -> boto3.Session:
    """
    Create AWS session optimized for cost operations (Cost Explorer) with automatic SSO token refresh.

    Args:
        profile_name: AWS profile name for cost operations

    Returns:
        Configured boto3 Session for cost operations with auto-refresh capability

    Raises:
        SystemExit: When authentication fails after auto-refresh attempts
    """
    cost_profile = get_profile_for_operation("billing", profile_name)

    # Use cached session if available and validate it's still working
    session_key = f"cost:{cost_profile}"
    if session_key in _session_cache:
        cached_session = _session_cache[session_key]
        # Quick validation that the cached session still works
        try:
            # Test with a minimal STS call to check if credentials are valid (with timeout)
            sts_client = cached_session.client("sts", config=_AWS_CLIENT_CONFIG)
            sts_client.get_caller_identity()
            return cached_session
        except (TokenRetrievalError, NoCredentialsError):
            # Remove invalid cached session
            del _session_cache[session_key]
            console.log("[yellow]⚠️ Cached session expired, creating new session[/]")

    # Create session with automatic SSO token refresh
    session = create_session_with_auto_refresh(cost_profile)

    # Cache the validated session
    _session_cache[session_key] = session
    return session


def create_management_session(profile_name: Optional[str] = None) -> boto3.Session:
    """
    Create AWS session optimized for management operations (Organizations) with automatic SSO token refresh.

    Args:
        profile_name: AWS profile name for management operations

    Returns:
        Configured boto3 Session for management operations with auto-refresh capability

    Raises:
        SystemExit: When authentication fails after auto-refresh attempts
    """
    mgmt_profile = get_profile_for_operation("management", profile_name)

    # Use cached session if available and validate it's still working
    session_key = f"management:{mgmt_profile}"
    if session_key in _session_cache:
        cached_session = _session_cache[session_key]
        # Quick validation that the cached session still works
        try:
            # Test with a minimal STS call to check if credentials are valid (with timeout)
            sts_client = cached_session.client("sts", config=_AWS_CLIENT_CONFIG)
            sts_client.get_caller_identity()
            return cached_session
        except (TokenRetrievalError, NoCredentialsError):
            # Remove invalid cached session
            del _session_cache[session_key]
            console.log("[yellow]⚠️ Cached session expired, creating new session[/]")

    # Create session with automatic SSO token refresh
    session = create_session_with_auto_refresh(mgmt_profile)

    # Cache the validated session
    _session_cache[session_key] = session
    return session


def create_operational_session(profile_name: Optional[str] = None) -> boto3.Session:
    """
    Create AWS session optimized for operational tasks (EC2, S3, etc) with automatic SSO token refresh.

    Args:
        profile_name: AWS profile name for operational tasks

    Returns:
        Configured boto3 Session for operational tasks with auto-refresh capability
    """
    ops_profile = get_profile_for_operation("operational", profile_name)

    # Use cached session if available and validate it's still working
    session_key = f"operational:{ops_profile}"
    if session_key in _session_cache:
        cached_session = _session_cache[session_key]
        # Quick validation that the cached session still works
        try:
            # Test with a minimal STS call to check if credentials are valid (with timeout)
            sts_client = cached_session.client("sts", config=_AWS_CLIENT_CONFIG)
            sts_client.get_caller_identity()
            return cached_session
        except (TokenRetrievalError, NoCredentialsError):
            # Remove invalid cached session
            del _session_cache[session_key]
            console.log("[yellow]⚠️ Cached session expired, creating new session[/]")

    # Create session with automatic SSO token refresh
    session = create_session_with_auto_refresh(ops_profile)

    # Cache the validated session
    _session_cache[session_key] = session
    return session


def get_current_profile_info(profile_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Get current profile information including account ID and region.

    Args:
        profile_name: AWS profile name to get info for

    Returns:
        Dictionary containing profile information
    """
    try:
        session = boto3.Session(profile_name=profile_name)
        sts_client = session.client("sts", config=_AWS_CLIENT_CONFIG)
        identity = sts_client.get_caller_identity()

        return {
            "profile_name": profile_name or "default",
            "account_id": identity.get("Account"),
            "user_arn": identity.get("Arn"),
            "region": session.region_name or "ap-southeast-2",
        }
    except Exception as e:
        return {
            "profile_name": profile_name or "default",
            "error": str(e),
            "account_id": None,
            "user_arn": None,
            "region": None,
        }


def resolve_profile_for_operation_silent(operation_type: str, user_specified_profile: Optional[str] = None) -> str:
    """
    Silent version of profile resolution without logging.

    Args:
        operation_type: Type of operation (billing, management, operational)
        user_specified_profile: User-provided profile via --profile parameter

    Returns:
        Profile name to use for the operation
    """
    # Skip all logging and caching, just return the profile
    if user_specified_profile and user_specified_profile != "default":
        return user_specified_profile

    # Check environment variables
    profile_map = {
        "billing": os.getenv("BILLING_PROFILE"),
        "management": os.getenv("MANAGEMENT_PROFILE"),
        "operational": os.getenv("CENTRALISED_OPS_PROFILE"),
    }

    env_profile = profile_map.get(operation_type)
    if env_profile:
        return env_profile

    return user_specified_profile or "default"


def get_mcp_profile_for_service(service_name: str) -> str:
    """
    Map AWS service or MCP server to appropriate profile for multi-account Landing Zone.

    Profile Segregation Architecture:
    - AWS_MANAGEMENT_PROFILE: Organizations, IAM, SSO, CloudTrail, Well-Architected
    - AWS_BILLING_PROFILE: Cost Explorer, Billing/Cost Management
    - AWS_CENTRALISED_OPS_PROFILE: CloudWatch, Lambda, Terraform, Diagrams
    - AWS_DEFAULT_PROFILE: Account-specific services (EC2, S3, RDS, etc.)

    Args:
        service_name: AWS service name or MCP server name (e.g., 'core-mcp', 'cost-explorer', 'ec2')

    Returns:
        Profile name from appropriate environment variable

    Reference:
        .mcp-networking.json → MCP server profile mapping configuration

    Example:
        >>> profile = get_mcp_profile_for_service('cost-explorer')
        >>> # Returns value from AWS_BILLING_PROFILE env var
        >>> profile = get_mcp_profile_for_service('ec2')
        >>> # Returns value from AWS_DEFAULT_PROFILE env var
    """
    # Management account services (centralized control plane)
    management_services = ["core-mcp", "iam", "organizations", "sso", "cloudtrail", "well-architected-security"]

    # Billing account services (cost management)
    billing_services = ["cost-explorer", "billing-cost-management"]

    # Centralized operations services (shared tooling)
    centralised_ops_services = ["cloudwatch", "cloudwatch-appsignals", "lambda-tool", "terraform-mcp", "aws-diagram"]

    # Normalize service name for matching
    service_lower = service_name.lower()

    # Map service to appropriate profile
    if any(svc in service_lower for svc in management_services):
        return os.getenv("AWS_MANAGEMENT_PROFILE", "default")
    elif any(svc in service_lower for svc in billing_services):
        return os.getenv("AWS_BILLING_PROFILE", "default")
    elif any(svc in service_lower for svc in centralised_ops_services):
        return os.getenv("AWS_CENTRALISED_OPS_PROFILE", "default")
    else:
        # Account-specific services (EC2, S3, RDS, etc.) use default profile
        return os.getenv("AWS_DEFAULT_PROFILE", "default")


def list_available_profiles() -> List[str]:
    """
    Get list of all available AWS profiles.

    Returns:
        List of available profile names
    """
    return boto3.Session().available_profiles


def clear_profile_cache() -> None:
    """Clear the profile cache for testing or troubleshooting."""
    global _profile_cache, _validation_cache, _session_cache, _cache_timestamp, _session_id
    _profile_cache.clear()
    _validation_cache.clear()
    _session_cache.clear()
    _cache_timestamp = None
    _session_id = None


def create_timeout_protected_client(session: boto3.Session, service_name: str, region_name: Optional[str] = None):
    """
    Create AWS service client with timeout protection to prevent execution flow hangs.

    This function should be used by all FinOps modules to create AWS clients with
    enterprise-grade timeout protection and retry configuration.

    Args:
        session: boto3 Session to use for client creation
        service_name: AWS service name (e.g., 'ec2', 'ce', 'workspaces', 'rds')
        region_name: AWS region name (optional)

    Returns:
        AWS service client with timeout protection

    Example:
        session = create_cost_session()
        ce_client = create_timeout_protected_client(session, 'ce', 'ap-southeast-2')
        ec2_client = create_timeout_protected_client(session, 'ec2', region_name)
    """
    return session.client(service_name, region_name=region_name, config=_AWS_CLIENT_CONFIG)
