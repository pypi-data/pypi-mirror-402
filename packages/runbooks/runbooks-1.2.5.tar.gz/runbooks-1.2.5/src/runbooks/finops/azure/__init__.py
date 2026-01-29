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
Framework: ADLC v3.0.0 | Version: 1.0.0
"""

__version__ = "1.0.0"

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
]
