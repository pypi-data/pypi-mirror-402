"""
ITSM Core Module - Data Loading and Processing

This module contains the core data loading functionality for the ITSM Analytics platform.

Exports:
    ITSMDataLoader: Main data loader class with dual interface
    DataLoader: Backward-compatible wrapper for original interface
    DataLoadError: Custom exception for data loading failures
    load_ticket_data: Convenience function for loading data
"""

from .data_loader import ITSMDataLoader, DataLoader, DataLoadError, load_ticket_data

__all__ = ["ITSMDataLoader", "DataLoader", "DataLoadError", "load_ticket_data"]
