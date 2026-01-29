# VPC Pattern Library - Reusable Components for Network Analysis

**Purpose**: Modular base classes for AWS VPC/networking resource analysis with 60-70% code reuse potential across all 7 runbooks modules.

**Architecture**: Abstract Base Class (ABC) design with composition pattern for maximum flexibility and reusability.

**Business Value**: Reduce development time for future network optimization features by extracting proven patterns from VPCE cleanup operations.

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Available Patterns](#available-patterns)
4. [Usage Guide](#usage-guide)
5. [Testing](#testing)
6. [Examples](#examples)

---

## Overview

The VPC Pattern Library provides 8 reusable base classes extracted from enterprise VPCE cleanup operations. These patterns enable:

- **Cost Analysis**: AWS Cost Explorer integration for actual cost data
- **Resource Validation**: AWS API verification for resource existence
- **Script Generation**: Dual-format cleanup scripts (bash + boto3)
- **Export Services**: GitHub-flavored markdown export
- **Organizations Metadata**: Account names, emails, tags, OU paths
- **VPC Context**: VPC names, CIDRs, resource counts
- **Activity Intelligence**: CloudTrail-based usage analysis
- **Decision Frameworks**: Data-driven cleanup prioritization

### Design Principles

**KISS (Keep It Simple, Stupid)**:
- Each pattern has a single, well-defined responsibility
- Simple interfaces with clear abstract method contracts
- Minimal dependencies between patterns

**DRY (Don't Repeat Yourself)**:
- 60% code reduction via pattern extraction (3,376 → ~1,200 lines)
- Reusable across VPC, NAT Gateway, ENI, and other network analysis modules
- Shared dataclasses for consistent results structure

**LEAN (Less is More)**:
- Focus on essential functionality only
- Graceful fallback when optional features unavailable
- Error isolation prevents cascading failures

---

## Architecture

### Abstract Base Class (ABC) Design

All patterns use Python's `ABC` module to define contracts:

```python
from abc import ABC, abstractmethod

class MyPattern(ABC):
    @abstractmethod
    def _get_resources(self) -> List:
        """Subclasses must implement this method."""
        pass

    def public_api_method(self):
        """Concrete implementation using abstract data source."""
        resources = self._get_resources()
        # ... enrichment logic
```

**Benefits**:
- **Type Safety**: Python enforces abstract method implementation
- **Clear Contracts**: Developers know exactly what to implement
- **Testability**: Easy to create mock implementations for testing

### Composition Pattern

Patterns are designed for multiple inheritance (composition pattern):

```python
class VPCECleanupManager(
    CostExplorerEnricher,
    OrganizationsEnricher,
    VPCEnricher,
    CloudTrailActivityAnalyzer,
    DecisionFramework,
    # ... and 3 more base classes
):
    """
    Inherits from 8 base classes, implements 7 abstract methods.
    Reuses 60-70% of code from patterns.
    """
```

**Benefits**:
- **Modularity**: Add/remove capabilities by adjusting inheritance
- **Flexibility**: Pick patterns needed for specific use cases
- **Maintainability**: Fix bugs in one place, affects all users

### Dataclass Results

All patterns return strongly-typed dataclasses:

```python
@dataclass
class CostEnrichmentResult:
    enriched_count: int
    total_cost: Decimal
    account_costs: Dict[str, Decimal]
    errors: List[str]
```

**Benefits**:
- **Type Safety**: IDE autocomplete + type checking
- **Documentation**: Self-documenting return values
- **Consistency**: Standard result format across all patterns

---

## Available Patterns

### 1. CostExplorerEnricher

**Purpose**: Integrate AWS Cost Explorer for actual cost data (vs estimated pricing).

**Abstract Method**:
```python
@abstractmethod
def _get_cost_enrichable_accounts(self) -> Dict[str, List]:
    """Return resources grouped by account for cost enrichment."""
    pass
```

**Public API**:
```python
result = manager.enrich_with_cost_explorer(
    billing_profile="billing-readonly",
    lookback_days=30
)
# Returns: CostEnrichmentResult
```

**Use Cases**:
- VPCE cost validation (estimated vs actual)
- NAT Gateway cost analysis
- VPC resource cost attribution
- Multi-account cost aggregation

**Reusability**: All 7 runbooks modules (any AWS resource with cost dimension)

---

### 2. AWSResourceValidator

**Purpose**: Validate resource existence via AWS APIs (cross-validation).

**Abstract Method**:
```python
@abstractmethod
def _get_resources_for_validation(self) -> List:
    """Return resources to validate against AWS APIs."""
    pass
```

**Public API**:
```python
result = manager.validate_endpoints_exist()
# Returns: ValidationResult (exists, not_found, errors)
```

**Use Cases**:
- VPCE existence validation
- VPC resource verification
- Multi-account resource discovery
- Stale data detection

**Reusability**: Inventory, Security, Remediation modules

---

### 3. CleanupScriptGenerator

**Purpose**: Generate dual-format cleanup scripts (bash + boto3 Python).

**Abstract Method**:
```python
@abstractmethod
def _get_resources_for_cleanup(self) -> List:
    """Return resources for cleanup script generation."""
    pass
```

**Public API**:
```python
result = manager.generate_cleanup_scripts(
    output_dir=Path("./scripts"),
    dry_run_default=True
)
# Returns: ScriptGenerationResult (bash_file, python_file)
```

**Use Cases**:
- VPCE cleanup automation
- NAT Gateway removal scripts
- ENI cleanup workflows
- Multi-account cleanup orchestration

**Reusability**: FinOps, Remediation, Operations modules

---

### 4. MarkdownExporter

**Purpose**: Export analysis results to GitHub-flavored markdown.

**Abstract Method**:
```python
@abstractmethod
def _get_data_for_export(self) -> Tuple[DataFrame, Dict]:
    """Return dataframe and metadata for markdown export."""
    pass
```

**Public API**:
```python
result = manager.export_to_markdown(
    output_dir=Path("./reports"),
    include_metadata=True
)
# Returns: MarkdownExportResult (file_path, record_count)
```

**Use Cases**:
- Executive reporting
- Audit trail documentation
- Compliance evidence packages
- Stakeholder communication

**Reusability**: All 7 runbooks modules (any report generation)

---

### 5. OrganizationsEnricher

**Purpose**: Enrich resources with AWS Organizations account metadata.

**Abstract Method**:
```python
@abstractmethod
def _get_resources_by_account(self) -> Dict:
    """Return resources grouped by account for metadata enrichment."""
    pass
```

**Public API**:
```python
result = manager.enrich_with_organizations_api(
    management_profile="org-management-readonly",
    include_tags=True,
    include_ou_paths=True
)
# Returns: OrganizationEnrichmentResult
```

**Use Cases**:
- Multi-account landing zone analysis
- Account name/email enrichment
- OU-based filtering
- Tag-based categorization

**Reusability**: All multi-account operations (Inventory, FinOps, Security)

---

### 6. VPCEnricher

**Purpose**: Enrich network resources with VPC metadata (names, CIDRs, resources).

**Abstract Method**:
```python
@abstractmethod
def _get_vpce_resources(self) -> List:
    """Return VPCE/network resources for VPC enrichment."""
    pass
```

**Public API**:
```python
result = manager.enrich_with_vpc_api(
    include_resource_counts=True
)
# Returns: VPCEnrichmentResult (names, CIDRs, resource counts)
```

**Use Cases**:
- VPCE VPC context
- NAT Gateway VPC mapping
- ENI VPC attribution
- VPC resource inventory

**Reusability**: VPC, Inventory, Network analysis modules

---

### 7. CloudTrailActivityAnalyzer

**Purpose**: Analyze resource activity via CloudTrail event history (90-day lookback).

**Abstract Method**:
```python
@abstractmethod
def _get_resources_for_activity_analysis(self) -> List:
    """Return resources for CloudTrail activity analysis."""
    pass
```

**Public API**:
```python
result = manager.analyze_cloudtrail_activity(
    lookback_days=90,
    idle_threshold_days=30
)
# Returns: ActivityAnalysisResult (active/idle classification)
```

**Use Cases**:
- Idle resource detection
- Usage pattern analysis
- Cleanup prioritization
- Compliance reporting (last access tracking)

**Reusability**: FinOps, Operations, Security modules

---

### 8. DecisionFramework

**Purpose**: Data-driven cleanup prioritization via two-gate scoring (activity + cost).

**Abstract Method**:
```python
@abstractmethod
def _get_resources_for_scoring(self) -> List:
    """Return resources for decision scoring."""
    pass
```

**Public API**:
```python
criteria = DecisionCriteria(
    idle_threshold_days=30,
    high_cost_threshold=100.0,
    activity_weight=0.6,
    cost_weight=0.4
)
result = manager.calculate_decision_scores(criteria)
# Returns: DecisionFrameworkResult (MUST/SHOULD/Could priorities)
```

**Use Cases**:
- Cleanup prioritization
- Executive decision support
- Savings opportunity ranking
- Risk-based remediation

**Reusability**: FinOps, Remediation, Operations modules

---

## Usage Guide

### Step 1: Choose Patterns

Identify which patterns your manager class needs:

- **Cost analysis?** → `CostExplorerEnricher`
- **Resource validation?** → `AWSResourceValidator`
- **Cleanup scripts?** → `CleanupScriptGenerator`
- **Markdown reports?** → `MarkdownExporter`
- **Account metadata?** → `OrganizationsEnricher`
- **VPC context?** → `VPCEnricher`
- **Activity analysis?** → `CloudTrailActivityAnalyzer`
- **Decision scoring?** → `DecisionFramework`

### Step 2: Inherit from Patterns

```python
from runbooks.vpc.patterns import (
    CostExplorerEnricher,
    OrganizationsEnricher,
    VPCEnricher,
)

class MyNetworkAnalyzer(
    CostExplorerEnricher,
    OrganizationsEnricher,
    VPCEnricher,
):
    """Custom network analysis manager using 3 patterns."""
    pass
```

### Step 3: Implement Abstract Methods

Each pattern requires 1 abstract method implementation:

```python
class MyNetworkAnalyzer(CostExplorerEnricher, OrganizationsEnricher, VPCEnricher):
    def __init__(self, resources: List[NetworkResource]):
        self.resources = resources
        self.account_summaries = self._group_by_account()

    # CostExplorerEnricher requirement
    def _get_cost_enrichable_accounts(self) -> Dict[str, List]:
        return self.account_summaries

    # OrganizationsEnricher requirement
    def _get_resources_by_account(self) -> Dict:
        return self.account_summaries

    # VPCEnricher requirement
    def _get_vpce_resources(self) -> List:
        return self.resources
```

### Step 4: Use Pattern APIs

```python
analyzer = MyNetworkAnalyzer(resources)

# Cost analysis
cost_result = analyzer.enrich_with_cost_explorer(billing_profile="billing-readonly")
print(f"Total cost: ${cost_result.total_cost}")

# Organizations metadata
org_result = analyzer.enrich_with_organizations_api(management_profile="org-mgmt")
print(f"Account names: {org_result.account_names}")

# VPC context
vpc_result = analyzer.enrich_with_vpc_api()
print(f"VPC names: {vpc_result.vpc_names}")
```

---

## Testing

### Unit Tests

Each pattern has comprehensive unit tests:

```bash
# Run all pattern tests
uv run pytest tests/vpc/patterns/ -v

# Run specific pattern tests
uv run pytest tests/vpc/patterns/test_organizations_enrichment.py -v
```

**Coverage Target**: ≥97% for all patterns

### Test Structure

```python
# tests/vpc/patterns/test_my_pattern.py
import pytest
from unittest.mock import Mock, patch
from runbooks.vpc.patterns import MyPattern

class MockManager(MyPattern):
    """Mock implementation for testing."""
    def _get_resources(self):
        return self.test_resources

@patch('boto3.Session')
def test_my_pattern_success(mock_session):
    """Test successful pattern operation."""
    # Setup mocks
    mock_client = Mock()
    mock_session.return_value.client.return_value = mock_client

    # Execute
    manager = MockManager(test_resources=[...])
    result = manager.enrich_with_pattern()

    # Verify
    assert result.enriched_count > 0
```

### Integration Tests

Composition pattern validation:

```bash
# Run integration tests
uv run pytest tests/vpc/test_vpce_composition_pattern.py -v
```

---

## Examples

### Example 1: NAT Gateway Cost Optimizer

```python
from runbooks.vpc.patterns import CostExplorerEnricher, DecisionFramework
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class NATGateway:
    id: str
    account_id: str
    monthly_cost: float

class NATGatewayOptimizer(CostExplorerEnricher, DecisionFramework):
    def __init__(self, nat_gateways: List[NATGateway]):
        self.nat_gateways = nat_gateways
        self.account_summaries = self._group_by_account()

    def _get_cost_enrichable_accounts(self) -> Dict:
        return self.account_summaries

    def _get_resources_for_scoring(self) -> List:
        return self.nat_gateways

    def _group_by_account(self):
        # ... grouping logic
        pass

# Usage
optimizer = NATGatewayOptimizer(nat_gateways)

# Get actual costs
cost_result = optimizer.enrich_with_cost_explorer(billing_profile="billing")
print(f"Total NAT Gateway cost: ${cost_result.total_cost}")

# Calculate cleanup priorities
decision_result = optimizer.calculate_decision_scores(criteria)
print(f"MUST cleanup: {decision_result.must_cleanup} NAT Gateways")
print(f"Savings potential: ${decision_result.savings_potential['MUST']}/year")
```

### Example 2: ENI Cleanup Manager

```python
from runbooks.vpc.patterns import (
    CloudTrailActivityAnalyzer,
    CleanupScriptGenerator,
    MarkdownExporter,
)

class ENICleanupManager(
    CloudTrailActivityAnalyzer,
    CleanupScriptGenerator,
    MarkdownExporter,
):
    def __init__(self, enis: List[ENI]):
        self.enis = enis

    def _get_resources_for_activity_analysis(self) -> List:
        return self.enis

    def _get_resources_for_cleanup(self) -> List:
        return [eni for eni in self.enis if eni.is_idle]

    def _get_data_for_export(self):
        # ... DataFrame creation
        pass

# Usage
manager = ENICleanupManager(enis)

# Analyze activity
activity_result = manager.analyze_cloudtrail_activity()
print(f"Idle ENIs: {activity_result.idle_resources}")

# Generate cleanup scripts
script_result = manager.generate_cleanup_scripts(output_dir=Path("./scripts"))
print(f"Bash script: {script_result.bash_file_path}")

# Export markdown report
export_result = manager.export_to_markdown(output_dir=Path("./reports"))
print(f"Report: {export_result.markdown_file_path}")
```

### Example 3: Multi-Account VPC Analyzer

```python
from runbooks.vpc.patterns import (
    OrganizationsEnricher,
    VPCEnricher,
    AWSResourceValidator,
)

class MultiAccountVPCAnalyzer(
    OrganizationsEnricher,
    VPCEnricher,
    AWSResourceValidator,
):
    def __init__(self, vpcs: List[VPC]):
        self.vpcs = vpcs
        self.account_summaries = self._group_by_account()

    def _get_resources_by_account(self) -> Dict:
        return self.account_summaries

    def _get_vpce_resources(self) -> List:
        return self.vpcs

    def _get_resources_for_validation(self) -> List:
        return self.vpcs

# Usage
analyzer = MultiAccountVPCAnalyzer(vpcs)

# Get account names from Organizations
org_result = analyzer.enrich_with_organizations_api(
    management_profile="org-mgmt-readonly"
)
print(f"Accounts: {', '.join(org_result.account_names.values())}")

# Get VPC metadata
vpc_result = analyzer.enrich_with_vpc_api(include_resource_counts=True)
for vpc_id, name in vpc_result.vpc_names.items():
    cidr = vpc_result.vpc_cidrs[vpc_id]
    resources = vpc_result.vpc_resources[vpc_id]
    print(f"{name}: {cidr}, {resources['subnets']} subnets")

# Validate VPCs exist
validation_result = analyzer.validate_endpoints_exist()
print(f"Valid VPCs: {validation_result.valid_count}/{validation_result.total_resources}")
```

---

## Pattern Composition Examples

### Minimal Composition (1 pattern)

```python
class SimpleAnalyzer(CostExplorerEnricher):
    """Just cost analysis, no other features."""
    def _get_cost_enrichable_accounts(self):
        return self.account_summaries
```

### Moderate Composition (3-4 patterns)

```python
class ModerateAnalyzer(
    CostExplorerEnricher,
    OrganizationsEnricher,
    DecisionFramework,
):
    """Cost + Organizations + Decision scoring."""
    # Implement 3 abstract methods
```

### Full Composition (8 patterns)

```python
class FullFeaturedAnalyzer(
    CostExplorerEnricher,
    AWSResourceValidator,
    CleanupScriptGenerator,
    MarkdownExporter,
    OrganizationsEnricher,
    VPCEnricher,
    CloudTrailActivityAnalyzer,
    DecisionFramework,
):
    """Complete feature set with all 8 patterns."""
    # Implement 7 abstract methods (some patterns share methods)
```

---

## Best Practices

### 1. Graceful Fallback

All patterns handle AWS API errors gracefully:

```python
# Example: Organizations API unavailable
result = manager.enrich_with_organizations_api()
if result.enriched_count == 0:
    print(f"Organizations unavailable, using account IDs only")
    # Application continues with fallback behavior
```

### 2. Error Isolation

Per-resource errors don't block batch operations:

```python
# Example: 100 resources, 2 fail
result = manager.analyze_cloudtrail_activity()
print(f"Analyzed: {result.resources_analyzed}/100")
print(f"Errors: {len(result.errors)} non-blocking failures")
```

### 3. Rich CLI Integration

All patterns use Rich CLI for beautiful output:

```python
# Patterns automatically provide:
# - Progress bars for batch operations
# - Color-coded status messages
# - Formatted tables for results
# - Professional UX across all modules
```

### 4. Profile Management

Multi-account operations support profile override:

```python
# Billing profile for Cost Explorer
cost_result = manager.enrich_with_cost_explorer(billing_profile="billing-readonly")

# Management profile for Organizations
org_result = manager.enrich_with_organizations_api(management_profile="org-mgmt")

# Per-resource profiles for VPC API
vpc_result = manager.enrich_with_vpc_api()  # Uses resource.profile attribute
```

---

## Migration Guide

### Converting Existing Code to Patterns

**Before** (monolithic implementation):
```python
class MyManager:
    def analyze_costs(self):
        # 200 lines of Cost Explorer logic
        pass

    def get_account_names(self):
        # 150 lines of Organizations logic
        pass
```

**After** (pattern composition):
```python
from runbooks.vpc.patterns import CostExplorerEnricher, OrganizationsEnricher

class MyManager(CostExplorerEnricher, OrganizationsEnricher):
    def _get_cost_enrichable_accounts(self):
        return self.account_summaries

    def _get_resources_by_account(self):
        return self.account_summaries

    # 350 lines → 20 lines (94% reduction via pattern reuse)
```

**Benefits**:
- 60-70% code reduction
- Consistent error handling
- Built-in Rich CLI integration
- Comprehensive test coverage

---

## Roadmap

### Planned Patterns
1. **S3 Cost Analyzer** (FinOps module)
2. **Lambda Optimizer** (FinOps module)
3. **Security Baseline Validator** (Security module)
4. **Compliance Reporter** (Security module)

### Future Enhancements
- Async/parallel processing for large datasets
- Caching layer for repeated API calls
- Metrics/observability integration
- Custom plugin system for extensibility

---

## Support

**Documentation**: @src/runbooks/vpc/patterns/*.py (inline docstrings)
**Tests**: @tests/vpc/patterns/ (comprehensive unit tests)
**Examples**: @notebooks/vpc/vpce-cleanup-manager-operations.ipynb (Cells 2.5-2.10)

**Contact**: Runbooks Development Team

---

**Pattern Library Status**: Production-ready (v1.1.11)
**Business Value**: 60-70% code reuse potential across all 7 runbooks modules
**Quality**: ≥97% test coverage target, graceful error handling, Rich CLI integration
**Reusability**: Proven in VPCE cleanup operations, ready for NAT Gateway, ENI, VPC, and other network analysis modules
