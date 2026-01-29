#!/usr/bin/env python3
"""
ITSM Data Loader - Enterprise Data Loading with Dual Interface

Extracted from complete_itsm_dashboard.py (lines 34-130)
Preserves exact logic with dual interface: DataFrame mode (backward compatible)
and Pydantic model mode (future-ready).

Author: @agent-data-engineer
Date: 2025-10-15
Phase: 1 - Day 3 (Data Loading Layer)
"""

from typing import Tuple, Optional
from pathlib import Path
import pandas as pd
import numpy as np


# Custom exception for data loading failures
class DataLoadError(Exception):
    """Raised when data loading fails"""

    pass


class ITSMDataLoader:
    """
    Enterprise ITSM Data Loader with dual interface support.

    Features:
    - Production Excel file loading with graceful fallback
    - Sample data generation for testing/demo (reproducible with seed=42)
    - Automatic Resolution_Hours calculation
    - Dual interface: DataFrame mode + Pydantic model mode (future)

    Usage:
        # DataFrame interface (backward compatible)
        loader = ITSMDataLoader()
        aws_df, azure_df, pricing_df = loader.load_all_data()

        # Pydantic interface (future-ready, requires models/ticket.py)
        # tickets = loader.load_as_models()
    """

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize data loader with optional configuration.

        Args:
            config: Optional ITSMConfig instance or dict with paths
                   If None, uses default paths from dashboard root
        """
        self.config = config or self._get_default_config()
        self._aws_df = None
        self._azure_df = None
        self._pricing_df = None

    def _get_default_config(self) -> dict:
        """Get default configuration matching original DataLoader"""
        # Determine project root (dashboard-itsm directory)
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent.parent / "dashboard-itsm"

        return {
            "AWS_FILE": str(project_root / "data" / "AWS-Tickets.xlsx"),
            "AZURE_FILE": str(project_root / "data" / "Azure-Tickets.xlsx"),
            "PRICING_FILE": str(project_root / "data" / "Cloud price revision v 1.1 1.9.25 Bluecurrent Model.xlsx"),
            "SLA_TARGETS": {"P1": 4, "P2": 8, "P3": 24, "P4": 48},
            "enable_sample_data": True,  # Allow fallback to sample data
        }

    def load_all_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load all ITSM data (AWS, Azure, Pricing).

        This is the primary interface preserving exact logic from original DataLoader.
        Tries production Excel files first, falls back to sample data if unavailable.

        Returns:
            Tuple of (aws_df, azure_df, pricing_df) with Resolution_Hours calculated

        Raises:
            DataLoadError: If both production and sample data loading fail
        """
        try:
            # Try loading production data
            aws_df = self._load_aws_tickets()
            azure_df = self._load_azure_tickets()
            pricing_df = self._load_pricing_model()

            print(f"✅ Production data loaded: {len(aws_df)} AWS tickets, {len(azure_df)} Azure tickets")
            return aws_df, azure_df, pricing_df

        except Exception as e:
            # Check if sample data is enabled
            if self.config.get("enable_sample_data", True):
                print(f"⚠️  Error loading data: {e}")
                print("   Generating sample data for demonstration...")
                return self._generate_sample_data()
            else:
                raise DataLoadError(f"Failed to load production data and sample data is disabled: {e}")

    def load_as_models(self):
        """
        Load data as Pydantic models (future interface).

        Returns:
            TicketCollection with validated Ticket models

        Note:
            Requires models/ticket.py to be implemented (Day 2 dependency)
            Will raise ImportError if models not available yet
        """
        try:
            from ..models.ticket import Ticket, TicketCollection

            # Load as DataFrames first
            aws_df, azure_df, pricing_df = self.load_all_data()

            # Convert to Pydantic models
            tickets = []
            for _, row in pd.concat([aws_df, azure_df]).iterrows():
                ticket = Ticket.from_dataframe_row(row)
                tickets.append(ticket)

            return TicketCollection(tickets=tickets)

        except ImportError as e:
            raise ImportError(
                "Pydantic model interface requires models/ticket.py (Day 2 dependency). "
                "Use load_all_data() for DataFrame interface instead."
            ) from e

    # Private methods - preserve exact logic from original

    def _load_aws_tickets(self) -> pd.DataFrame:
        """Load AWS tickets from Excel file (exact logic from line 40-46)"""
        aws_df = pd.read_excel(self.config["AWS_FILE"], sheet_name="AWS-Tickets")
        aws_df["Source"] = "AWS"
        aws_df["Created"] = pd.to_datetime(aws_df["Created"], errors="coerce")
        aws_df["Resolved"] = pd.to_datetime(aws_df["Resolved"], errors="coerce")
        aws_df["Updated"] = pd.to_datetime(aws_df["Updated"], errors="coerce")
        aws_df["Resolution_Hours"] = (aws_df["Resolved"] - aws_df["Created"]).dt.total_seconds() / 3600
        return aws_df

    def _load_azure_tickets(self) -> pd.DataFrame:
        """Load Azure tickets from Excel file (exact logic from line 48-55)"""
        azure_df = pd.read_excel(self.config["AZURE_FILE"], sheet_name="Azure-Tickets")
        azure_df = azure_df[azure_df["Issue key"].notna()].copy()  # Remove empty rows
        azure_df["Source"] = "Azure"
        azure_df["Created"] = pd.to_datetime(azure_df["Created"], errors="coerce")
        azure_df["Resolved"] = pd.to_datetime(azure_df["Resolved"], errors="coerce")
        azure_df["Updated"] = pd.to_datetime(azure_df["Updated"], errors="coerce")
        azure_df["Resolution_Hours"] = (azure_df["Resolved"] - azure_df["Created"]).dt.total_seconds() / 3600
        return azure_df

    def _load_pricing_model(self) -> pd.DataFrame:
        """Load pricing model from Excel file (exact logic from line 57-58)"""
        pricing_df = pd.read_excel(self.config["PRICING_FILE"], sheet_name="Bluecurrent")
        return pricing_df

    def _add_resolution_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Resolution_Hours calculated field to DataFrame.

        Note: This is now integrated directly in _load_aws_tickets and _load_azure_tickets
        for exact compatibility with original logic.
        """
        df["Resolution_Hours"] = (df["Resolved"] - df["Created"]).dt.total_seconds() / 3600
        return df

    def _generate_sample_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Generate realistic sample data when production data is unavailable.

        Preserves exact distributions from original (lines 68-130):
        - AWS: 2,457 tickets with specific type/priority/team distributions
        - Azure: 540 tickets with different distributions
        - Pricing: 12-month cost comparison data

        Uses seed=42 for reproducibility.
        """
        np.random.seed(42)

        # AWS sample data (2,457 tickets) - exact logic from lines 72-95
        aws_df = self._generate_aws_sample(n=2457)

        # Azure sample data (540 tickets) - exact logic from lines 97-120
        azure_df = self._generate_azure_sample(n=540)

        # Pricing model data - exact logic from lines 122-127
        pricing_df = self._generate_pricing_sample()

        print(f"✅ Sample data generated: {len(aws_df)} AWS tickets, {len(azure_df)} Azure tickets")
        return aws_df, azure_df, pricing_df

    def _generate_aws_sample(self, n: int) -> pd.DataFrame:
        """
        Generate AWS sample data with exact distributions from original.

        Distributions (lines 76-87):
        - Issue Type: 50% Incident, 9% Change, 39% Service request, 2% Task
        - Priority: 1% P1, 5% P2, 30% P3, 64% P4
        - Team: 60% Datacom, 25% Cloud, 15% Network
        - Status: 60% Closed, 20% Resolved, 5% In Progress, 5% Open, 10% Done
        """
        aws_df = pd.DataFrame(
            {
                "Issue key": [f"AWS-{i:05d}" for i in range(n)],
                "Issue Type": np.random.choice(
                    ["Incident", "Change", "Service request", "Task"], n, p=[0.5, 0.09, 0.39, 0.02]
                ),
                "Status": np.random.choice(
                    ["Closed", "Resolved", "In Progress", "Open", "Done"], n, p=[0.6, 0.2, 0.05, 0.05, 0.1]
                ),
                "Priority": np.random.choice(["P1", "P2", "P3", "P4"], n, p=[0.01, 0.05, 0.3, 0.64]),
                "Created": pd.date_range(start="2024-01-01", end="2024-12-31", periods=n),
                "Team Name": np.random.choice(
                    ["Datacom Service Desk", "Cloud Team", "Network Team"], n, p=[0.6, 0.25, 0.15]
                ),
                "Assignee": np.random.choice([f"Agent_{i}" for i in range(20)], n),
                "Reporter": np.random.choice([f"User_{i}" for i in range(50)], n),
                "Summary": [f"AWS Issue {i}" for i in range(n)],
            }
        )

        # Add resolved timestamp with exponential distribution (mean=24h)
        aws_df["Resolved"] = aws_df["Created"] + pd.to_timedelta(np.random.exponential(24, n), unit="h")

        # Set Resolved to NaT for non-closed tickets
        aws_df.loc[~aws_df["Status"].isin(["Closed", "Resolved", "Done"]), "Resolved"] = pd.NaT

        # Calculate resolution hours
        aws_df["Resolution_Hours"] = (aws_df["Resolved"] - aws_df["Created"]).dt.total_seconds() / 3600

        aws_df["Updated"] = aws_df["Created"]
        aws_df["Source"] = "AWS"

        return aws_df

    def _generate_azure_sample(self, n: int) -> pd.DataFrame:
        """
        Generate Azure sample data with exact distributions from original.

        Distributions (lines 101-113):
        - Issue Type: 20% Incident, 21% Change, 47% Service request, 12% Task
        - Priority: 1% P1, 2% P2, 32% P3, 65% P4
        - Team: 70% Datacom, 20% Cloud, 10% Infrastructure
        - Status: 70% Closed, 15% Resolved, 5% In Progress, 5% Open, 5% Done
        """
        azure_df = pd.DataFrame(
            {
                "Issue key": [f"AZ-{i:05d}" for i in range(n)],
                "Issue Type": np.random.choice(
                    ["Incident", "Change", "Service request", "Task"], n, p=[0.2, 0.21, 0.47, 0.12]
                ),
                "Status": np.random.choice(
                    ["Closed", "Resolved", "In Progress", "Open", "Done"], n, p=[0.7, 0.15, 0.05, 0.05, 0.05]
                ),
                "Priority": np.random.choice(["P1", "P2", "P3", "P4"], n, p=[0.01, 0.02, 0.32, 0.65]),
                "Created": pd.date_range(start="2024-01-01", end="2024-12-31", periods=n),
                "Team Name": np.random.choice(
                    ["Datacom Service Desk", "Cloud Team", "Infrastructure"], n, p=[0.7, 0.2, 0.1]
                ),
                "Assignee": np.random.choice([f"Agent_{i}" for i in range(15)], n),
                "Reporter": np.random.choice([f"User_{i}" for i in range(30)], n),
                "Summary": [f"Azure Issue {i}" for i in range(n)],
            }
        )

        # Add resolved timestamp with exponential distribution (mean=36h)
        azure_df["Resolved"] = azure_df["Created"] + pd.to_timedelta(np.random.exponential(36, n), unit="h")

        # Set Resolved to NaT for non-closed tickets
        azure_df.loc[~azure_df["Status"].isin(["Closed", "Resolved", "Done"]), "Resolved"] = pd.NaT

        # Calculate resolution hours
        azure_df["Resolution_Hours"] = (azure_df["Resolved"] - azure_df["Created"]).dt.total_seconds() / 3600

        azure_df["Updated"] = azure_df["Created"]
        azure_df["Source"] = "Azure"

        return azure_df

    def _generate_pricing_sample(self) -> pd.DataFrame:
        """
        Generate pricing model sample data (exact values from lines 123-126).

        Returns 12-month cost comparison:
        - Existing_Cost: Variable monthly costs (Jan-Dec)
        - New_Model_Cost: Fixed $52,687/month story point model
        """
        pricing_df = pd.DataFrame(
            {
                "Month": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                "Existing_Cost": [42171, 60248, 73558, 70492, 37532, 36073, 34687, 33370, 32119, 30931, 29695, 28368],
                "New_Model_Cost": [52687] * 12,
            }
        )

        return pricing_df


# Backward compatibility with original DataLoader interface
class DataLoader:
    """
    Backward-compatible wrapper for original DataLoader static interface.

    This preserves the exact API from complete_itsm_dashboard.py allowing
    existing code to work without modification:

        aws_df, azure_df, pricing_df = DataLoader.load_ticket_data()
    """

    @staticmethod
    def load_ticket_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load ticket data using original static method interface.

        Returns:
            Tuple of (aws_df, azure_df, pricing_df)
        """
        loader = ITSMDataLoader()
        return loader.load_all_data()

    @staticmethod
    def _generate_sample_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate sample data using original static method interface"""
        loader = ITSMDataLoader()
        return loader._generate_sample_data()


# Convenience functions for direct usage
def load_ticket_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Convenience function for loading ticket data.

    Returns:
        Tuple of (aws_df, azure_df, pricing_df)
    """
    return DataLoader.load_ticket_data()


if __name__ == "__main__":
    # Test the data loader
    print("Testing ITSMDataLoader...")
    print("-" * 60)

    # Test new interface
    loader = ITSMDataLoader()
    aws_df, azure_df, pricing_df = loader.load_all_data()

    print(f"\n✅ Data Loading Test Complete")
    print(f"   AWS tickets: {len(aws_df)}")
    print(f"   Azure tickets: {len(azure_df)}")
    print(f"   Pricing months: {len(pricing_df)}")

    # Validate distributions
    print(f"\n📊 AWS Distribution Validation:")
    print(f"   Issue Types: {aws_df['Issue Type'].value_counts().to_dict()}")
    print(f"   Priorities: {aws_df['Priority'].value_counts().to_dict()}")

    print(f"\n📊 Azure Distribution Validation:")
    print(f"   Issue Types: {azure_df['Issue Type'].value_counts().to_dict()}")
    print(f"   Priorities: {azure_df['Priority'].value_counts().to_dict()}")

    # Test backward compatibility
    print(f"\n🔄 Testing Backward Compatibility...")
    aws_compat, azure_compat, pricing_compat = DataLoader.load_ticket_data()
    print(f"   ✅ Original DataLoader interface works")
    print(f"   AWS: {len(aws_compat)}, Azure: {len(azure_compat)}")
