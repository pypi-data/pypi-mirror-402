"""
ITSM Analytics Module - Phase 1 Foundation.

Provides configuration management, Pydantic data models, and data loading
for ITSM ticket analytics with AWS and Azure support.

Phase 1 Components:
- config: Configuration management with backward compatibility
- models: Pydantic ticket models with validation
- core: Data loading with dual interface (DataFrame + Pydantic)
- tests: Comprehensive test suite (85 tests, 84.7% coverage)

Usage:
    from runbooks.itsm import ITSMConfig, ITSMDataLoader
    from runbooks.itsm.models import AWSTicket, AzureTicket, TicketCollection

    # Load configuration
    config = ITSMConfig()

    # Load data
    loader = ITSMDataLoader(config)
    aws_df, azure_df, pricing_df = loader.load_all_data()

    # Or load as Pydantic models
    collection = loader.load_as_models()
"""

__version__ = "1.0.0"
__phase__ = "1"

# Configuration
from runbooks.itsm.config import (
    ITSMConfig,
    DataSourceConfig,
    SLAConfig,
    DesignSystemConfig,
    VisualizationConfig,
    get_config,
    get_legacy_config,
)

# Models
from runbooks.itsm.models import (
    TicketSource,
    TicketType,
    TicketStatus,
    TicketPriority,
    BaseTicket,
    AWSTicket,
    AzureTicket,
    TicketCollection,
)

# Core
from runbooks.itsm.core import (
    ITSMDataLoader,
    DataLoadError,
    load_ticket_data,
)

__all__ = [
    # Version
    "__version__",
    "__phase__",
    # Configuration
    "ITSMConfig",
    "DataSourceConfig",
    "SLAConfig",
    "DesignSystemConfig",
    "VisualizationConfig",
    "get_config",
    "get_legacy_config",
    # Models
    "TicketSource",
    "TicketType",
    "TicketStatus",
    "TicketPriority",
    "BaseTicket",
    "AWSTicket",
    "AzureTicket",
    "TicketCollection",
    # Core
    "ITSMDataLoader",
    "DataLoadError",
    "load_ticket_data",
]
