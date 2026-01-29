"""
Enterprise TDD CLI Module

Provides command-line interface for Test-Driven Development framework,
integrated with existing runbooks CLI architecture and enterprise standards.

Agent Coordination:
- python-runbooks-engineer [1]: CLI implementation and integration
- qa-testing-specialist [3]: Test framework validation and quality gates
- enterprise-product-owner [0]: Strategic oversight and business alignment
"""

from .cli import tdd_group

__all__ = ["tdd_group"]
