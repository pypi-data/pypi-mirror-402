"""FinOps cost optimizers with KISS/DRY/LEAN architecture.

Consolidates 17 optimizer files into 6-8 service-specific optimizers
using BaseOptimizer abstract class to eliminate duplication.

Author: Runbooks Team
Version: v1.1.28+
"""

from .base import BaseOptimizer, OptimizerConfig, OptimizerResult

__all__ = ["BaseOptimizer", "OptimizerConfig", "OptimizerResult"]
