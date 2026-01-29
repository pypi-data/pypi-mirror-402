"""
Enterprise FinOps Platform Integration Layer

This module provides the integration layer between the runbooks package
and the FinOps notebook interfaces, enabling business-friendly access
to technical cost optimization capabilities.
"""

from runbooks import __version__

from .core.runbooks_wrapper import RunbooksWrapper
from .finops.unit_economics import UnitEconomicsCalculator
from .components.validators import ProfileValidator

__all__ = ["RunbooksWrapper", "UnitEconomicsCalculator", "ProfileValidator"]
