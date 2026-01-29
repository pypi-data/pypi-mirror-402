"""
Inventory Module Main Entry Point.

This module provides the main entry point for the inventory module,
allowing it to be imported as runbooks.inventory.main as expected by tests.
"""

from runbooks.inventory import InventoryCollector, EnhancedInventoryCollector

__all__ = ["InventoryCollector", "EnhancedInventoryCollector"]
