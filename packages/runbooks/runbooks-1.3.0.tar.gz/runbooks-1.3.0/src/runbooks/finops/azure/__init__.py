"""
Azure FinOps Extension - FOCUS 1.3 Aligned Cost Management

Azure Cost Management integration with FOCUS 1.3 schema alignment.
Provides executive reporting, cost tier classification, and Excel export.

## Usage

```python
from runbooks.finops.azure import AzureCostReport, AzureReportConfig

config = AzureReportConfig(
    customer_name="Customer",
    billing_period="November 2025",
    date_range="01 Nov - 30 Nov 2025",
)
config.services_csv = Path("data/services.csv")
config.subscriptions_csv = Path("data/subscriptions.csv")

report = AzureCostReport(config)
report.generate()
report.show_summary()
report.export_excel()
```

## FOCUS 1.3 Alignment (Ratified Dec 5, 2025)
- Schema: 105 columns from Azure Cost Management
- Key columns: BilledCost, EffectiveCost, ServiceName, SubscriptionName
- Multi-currency: BillingCurrency, PricingCurrency

## References
- Microsoft FinOps Toolkit: https://microsoft.github.io/finops-toolkit/
- FOCUS Specification: https://focus.finops.org/
- Azure FOCUS Schema: https://learn.microsoft.com/azure/cost-management-billing/dataset-schema/cost-usage-details-focus

Migrated from: Cloud-Infrastructure/src/runbooks_finops_azure/
Framework: ADLC v3.0.0 | Version: 1.3.0

## v1.3.0 Updates (2026-01-20)
- Added analysis module: cross_validate_sources(), calculate_accuracy(), analyze_trends(), detect_anomalies()
- Added report_generator module: generate_cfo_summary(), generate_cto_summary(), generate_stakeholder_email()
- Supports thin wrapper command architecture (azure-monthly.md 2,200 → ~500 LOC)

## v1.2.0 Updates (2026-01-20)
- Added get_azure_cost_data() convenience function (mirrors AWS pattern)
- Complete cost data retrieval with optional Portal CSV cross-validation
- API is ALWAYS authoritative (v2.3.0 architecture)

## v1.1.0 Updates (2026-01-20)
- Added portal_csv_validator module for 4-Way Validation
- Added parse_portal_csv(), validate_portal_csv(), find_portal_csv()
"""

__version__ = "1.3.0"

from runbooks.finops.azure.types import (
    AzureCostData,
    AzureServiceCost,
    AzureSubscriptionCost,
    FOCUSCostRecord,
    AzureExportMetadata,
    classify_cost_tier,
)
from runbooks.finops.azure.config import AzureReportConfig
from runbooks.finops.azure.cost_report import AzureCostReport
from runbooks.finops.azure.cost_processor import (
    process_azure_cost_data,
    load_azure_services_csv,
    load_azure_subscriptions_csv,
    aggregate_services_by_name,
    aggregate_subscriptions_by_name,
    get_top_n_services,
)
from runbooks.finops.azure.client import (
    AzureCostClient,
    get_azure_client,
    get_azure_cost_data,
)
from runbooks.finops.azure.portal_csv_validator import (
    PortalCSVData,
    ValidationResult,
    parse_portal_csv,
    validate_portal_csv,
    find_portal_csv,
    detect_csv_format,
)
from runbooks.finops.azure.analysis import (
    calculate_variance,
    cross_validate_sources,
    calculate_accuracy,
    analyze_trends,
    detect_anomalies,
    generate_cost_summary,
    get_exchange_rate,
    DEFAULT_THRESHOLDS,
)
from runbooks.finops.azure.report_generator import (
    generate_cfo_summary,
    generate_cto_summary,
    generate_stakeholder_email,
    export_csv_reports,
    export_xlsx_report,
)

__all__ = [
    "__version__",
    # Configuration
    "AzureReportConfig",
    # Types (FOCUS 1.3 aligned)
    "AzureCostData",
    "AzureServiceCost",
    "AzureSubscriptionCost",
    "FOCUSCostRecord",
    "AzureExportMetadata",
    "classify_cost_tier",
    # Report facade
    "AzureCostReport",
    # Processors
    "process_azure_cost_data",
    "load_azure_services_csv",
    "load_azure_subscriptions_csv",
    "aggregate_services_by_name",
    "aggregate_subscriptions_by_name",
    "get_top_n_services",
    # Azure API Client (C1 + v1.1.0)
    "AzureCostClient",
    "get_azure_client",
    "get_azure_cost_data",
    # Portal CSV Validation (v1.1.0)
    "PortalCSVData",
    "ValidationResult",
    "parse_portal_csv",
    "validate_portal_csv",
    "find_portal_csv",
    "detect_csv_format",
    # Analysis (v1.3.0)
    "calculate_variance",
    "cross_validate_sources",
    "calculate_accuracy",
    "analyze_trends",
    "detect_anomalies",
    "generate_cost_summary",
    "get_exchange_rate",
    "DEFAULT_THRESHOLDS",
    # Report Generation (v1.3.0)
    "generate_cfo_summary",
    "generate_cto_summary",
    "generate_stakeholder_email",
    "export_csv_reports",
    "export_xlsx_report",
]
