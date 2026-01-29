"""
FOCUS 1.3 Cost Normalization and Reporting

Multi-cloud cost data normalization to FOCUS 1.3 specification (ratified Dec 5, 2025).
Includes cost aggregation and professional Excel report generation.

## Usage

```python
from runbooks.finops.focus import FocusNormalizer, CostAggregator, ExcelFormatter

# Normalize AWS/Azure data to FOCUS 1.3
normalizer = FocusNormalizer(version="1.3")
aws_focus = normalizer.normalize_aws(aws_df)
azure_focus = normalizer.normalize_azure(azure_df)
combined = normalizer.merge([aws_focus, azure_focus])

# Validate compliance
result = normalizer.validate(combined)
print(f"FOCUS 1.3 Compliant: {result['compliant']}")

# Generate Excel report
formatter = ExcelFormatter(currency="NZD")
formatter.create_report(
    by_subscription=subs_df,
    by_service=services_df,
    by_costcenter=costcenter_df,
    summary=summary_dict,
    output_path="cost-report.xlsx"
)
```

## FOCUS 1.3 Key Updates (Dec 2025)
- ServiceProvider/HostProvider columns (NEW)
- SplitCostAllocation columns (NEW)
- ContractCommitment dataset (NEW)
- Deprecated: Provider, Publisher columns

## References
- FOCUS Specification: https://focus.finops.org/
- FinOps Foundation: https://www.finops.org/

Migrated from: Cloud-Infrastructure/src/finops/
Framework: ADLC v3.0.0 | Version: 1.0.0
"""

__version__ = "1.0.0"

from runbooks.finops.focus.normalizer import (
    FocusNormalizer,
    CostAggregator,
    FOCUS_1_3_SCHEMA,
    FOCUS_REQUIRED_COLUMNS,
    AWS_TO_FOCUS_1_3,
    AZURE_TO_FOCUS_1_3,
)
from runbooks.finops.focus.excel_formatter import (
    ExcelFormatter,
    create_finops_excel_report,
)

__all__ = [
    "__version__",
    # Normalizer
    "FocusNormalizer",
    "CostAggregator",
    "FOCUS_1_3_SCHEMA",
    "FOCUS_REQUIRED_COLUMNS",
    "AWS_TO_FOCUS_1_3",
    "AZURE_TO_FOCUS_1_3",
    # Excel Formatter
    "ExcelFormatter",
    "create_finops_excel_report",
]
