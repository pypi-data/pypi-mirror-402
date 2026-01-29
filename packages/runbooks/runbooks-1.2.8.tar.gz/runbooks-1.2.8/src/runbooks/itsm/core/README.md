# ITSM Core Module

**Purpose**: Enterprise data loading and core functionality for ITSM Analytics platform

---

## Quick Start

### Basic Usage (Backward Compatible)
```python
from runbooks.itsm.core import DataLoader

# Load all data (production or sample fallback)
aws_df, azure_df, pricing_df = DataLoader.load_ticket_data()

print(f"Loaded {len(aws_df)} AWS tickets")
print(f"Loaded {len(azure_df)} Azure tickets")
```

### Modern Usage (New Interface)
```python
from runbooks.itsm.core import ITSMDataLoader

# Initialize with optional config
loader = ITSMDataLoader()

# Load data
aws_df, azure_df, pricing_df = loader.load_all_data()

# Future: Load as Pydantic models (requires models/ticket.py)
# tickets = loader.load_as_models()
```

---

## Module Contents

### Classes

#### `ITSMDataLoader`
Main data loader class with dual interface support.

**Methods**:
- `__init__(config: Optional[dict] = None)` - Initialize with optional config
- `load_all_data()` - Load AWS, Azure, and pricing data (DataFrame interface)
- `load_as_models()` - Load as Pydantic models (future, requires Day 2)

**Private Methods** (preserve original logic):
- `_load_aws_tickets()` - Load AWS Excel file
- `_load_azure_tickets()` - Load Azure Excel file
- `_load_pricing_model()` - Load pricing Excel file
- `_generate_sample_data()` - Generate reproducible sample data
- `_generate_aws_sample(n)` - Generate AWS tickets
- `_generate_azure_sample(n)` - Generate Azure tickets
- `_generate_pricing_sample()` - Generate pricing data

#### `DataLoader`
Backward-compatible wrapper preserving original static method interface.

**Methods**:
- `load_ticket_data()` - Static method matching original API

#### `DataLoadError`
Custom exception for data loading failures.

### Functions

#### `load_ticket_data()`
Convenience function for quick data loading.

---

## Data Sources

### Production Files (Optional)
```
dashboard-itsm/data/
├── AWS-Tickets.xlsx           # AWS ITSM tickets
├── Azure-Tickets.xlsx         # Azure ITSM tickets
└── Cloud price revision...    # Pricing model comparison
```

**Required Columns**:
- `Issue key`, `Issue Type`, `Status`, `Priority`
- `Created`, `Resolved`, `Updated` (datetime)
- `Team Name`, `Assignee`, `Reporter`, `Summary`

### Sample Data (Fallback)
If production files unavailable, generates reproducible sample data:
- **AWS**: 2,457 tickets (50% Incident, 9% Change, 39% SR, 2% Task)
- **Azure**: 540 tickets (20% Incident, 21% Change, 47% SR, 12% Task)
- **Pricing**: 12-month cost comparison

**Reproducibility**: `np.random.seed(42)` ensures consistent results

---

## Configuration

### Default Configuration
```python
{
    'AWS_FILE': 'dashboard-itsm/data/AWS-Tickets.xlsx',
    'AZURE_FILE': 'dashboard-itsm/data/Azure-Tickets.xlsx',
    'PRICING_FILE': 'dashboard-itsm/data/Cloud price revision v 1.1 1.9.25 Bluecurrent Model.xlsx',
    'SLA_TARGETS': {'P1': 4, 'P2': 8, 'P3': 24, 'P4': 48},
    'enable_sample_data': True
}
```

### Custom Configuration (Future)
```python
from runbooks.itsm.config import ITSMConfig

config = ITSMConfig.from_file('itsm_config.yaml')
loader = ITSMDataLoader(config)
```

---

## Return Data Format

### DataFrames
All methods return tuple of `(aws_df, azure_df, pricing_df)`:

#### AWS/Azure DataFrame Schema
| Column | Type | Description |
|--------|------|-------------|
| `Issue key` | str | Unique ticket identifier |
| `Issue Type` | str | Incident, Change, Service request, Task |
| `Status` | str | Closed, Resolved, In Progress, Open, Done |
| `Priority` | str | P1, P2, P3, P4 |
| `Created` | datetime | Ticket creation timestamp |
| `Resolved` | datetime | Resolution timestamp (NaT if open) |
| `Updated` | datetime | Last update timestamp |
| `Resolution_Hours` | float | Hours to resolution (calculated) |
| `Source` | str | 'AWS' or 'Azure' |
| `Team Name` | str | Assigned team |
| `Assignee` | str | Individual assignee |
| `Reporter` | str | Ticket reporter |
| `Summary` | str | Ticket description |

#### Pricing DataFrame Schema
| Column | Type | Description |
|--------|------|-------------|
| `Month` | str | Jan, Feb, ..., Dec |
| `Existing_Cost` | int | Current variable cost model |
| `New_Model_Cost` | int | Fixed story point model |

---

## Resolution Hours Calculation

Preserved from original implementation (lines 46, 55):

```python
Resolution_Hours = (Resolved - Created).dt.total_seconds() / 3600
```

- Calculated for all tickets
- `NaN` for open tickets (no Resolved timestamp)
- Used for SLA compliance, MTTR, and analytics

---

## Error Handling

### Graceful Degradation
1. Attempts production Excel file loading
2. On failure, checks `enable_sample_data` config
3. Falls back to sample data generation
4. Raises `DataLoadError` only if both fail

### Sample Output
```
⚠️  Error loading data: Missing optional dependency 'openpyxl'
   Generating sample data for demonstration...
✅ Sample data generated: 2457 AWS tickets, 540 Azure tickets
```

---

## Testing

### Built-in Validation
```bash
cd /Volumes/Working/1xOps/CloudOps-Runbooks
uv run python src/runbooks/itsm/core/data_loader.py
```

**Validates**:
- Import success
- Data loading (2,997 tickets)
- Distribution matching
- Backward compatibility
- Resolution hours calculation

### Manual Testing
```python
from runbooks.itsm.core import ITSMDataLoader

loader = ITSMDataLoader()
aws, azure, pricing = loader.load_all_data()

assert len(aws) == 2457
assert len(azure) == 540
assert len(pricing) == 12
assert 'Resolution_Hours' in aws.columns
```

---

## Dependencies

### Required
- `pandas` - DataFrame operations
- `numpy` - Sample data generation

### Optional
- `openpyxl` - Excel file reading (production data)
- `models/ticket.py` - Pydantic models (Day 2, for `load_as_models()`)
- `config.py` - Configuration management (Day 1, for `ITSMConfig`)

### Install
```bash
uv add pandas numpy openpyxl
```

---

## Integration Examples

### Example 1: Original Dashboard (Backward Compatible)
```python
# In complete_itsm_dashboard.py (no changes needed)
from complete_itsm_dashboard import DataLoader

aws_df, azure_df, pricing_df = DataLoader.load_ticket_data()
```

### Example 2: New Modular Dashboard
```python
from runbooks.itsm.core import ITSMDataLoader

loader = ITSMDataLoader()
aws_df, azure_df, pricing_df = loader.load_all_data()

# Use DataFrames as before
combined_df = pd.concat([aws_df, azure_df])
```

### Example 3: Future Pydantic Interface
```python
from runbooks.itsm.core import ITSMDataLoader

loader = ITSMDataLoader()
tickets = loader.load_as_models()  # Returns TicketCollection

for ticket in tickets.aws_tickets:
    print(f"{ticket.issue_key}: {ticket.status}")
```

---

## Performance

### Sample Data Generation
- **Time**: <1 second for 2,997 tickets
- **Memory**: ~5MB for DataFrames
- **Reproducible**: Yes (seed=42)

### Production Data Loading
- **Time**: 2-5 seconds (depends on Excel file size)
- **Memory**: Proportional to ticket count
- **Caching**: DataFrames cached in loader instance

---

## Validation Report

See `VALIDATION_REPORT.md` for comprehensive validation results including:
- Distribution matching verification
- Sample data consistency
- Integration pattern testing
- Success criteria validation

---

## Changelog

### v1.0.0 (2025-10-15) - Initial Implementation
- ✅ Extracted DataLoader from complete_itsm_dashboard.py (lines 34-130)
- ✅ Dual interface: DataFrame (backward compatible) + Pydantic (future)
- ✅ 100% backward compatibility with original interface
- ✅ Sample data generation with exact distributions
- ✅ Resolution_Hours calculation preserved
- ✅ Graceful error handling with fallback
- ✅ Comprehensive documentation and validation

---

## Support

**Issues**: Report to @agent-data-engineer via ITSM Analytics project
**Documentation**: See VALIDATION_REPORT.md for detailed validation results
**Testing**: Run `python src/runbooks/itsm/core/data_loader.py` for built-in tests

---

**Status**: ✅ Production Ready (awaiting config.py and models/ticket.py for full features)
