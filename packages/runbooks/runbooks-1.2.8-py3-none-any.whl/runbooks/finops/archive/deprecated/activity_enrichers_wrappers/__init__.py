#!/usr/bin/env python3
"""
Activity Enrichers - Unified Activity Signal Architecture
==========================================================

Consolidates 14 activity enrichers into unified framework:
- Base interface: ActivityEnricherBase (abstract pattern)
- Service enrichers: EC2, S3, Lambda, DynamoDB, RDS, ECS, etc.
- Orchestrator: Parallel execution with ThreadPoolExecutor
- Signal patterns: E1-E7, S1-S7, L1-L6, D1-D7, R1-R7, etc.

Architecture Benefits:
- Single source of truth for activity enrichment
- Consistent signal patterns across services
- Thread-safe parallel execution
- Backward compatibility via re-exports

Strategic Alignment:
- KISS: Consolidate scattered enrichers into unified structure
- DRY: Single interface, no code duplication
- LEAN: Enhance existing, maintain backward compatibility

Usage:
    # Direct import from consolidated structure
    from runbooks.finops.activity_enrichers import (
        ActivityEnricherBase,
        EC2Enricher,
        S3Enricher,
        LambdaEnricher,
        DynamoDBEnricher,
        ActivityOrchestrator
    )

    # Backward compatibility - existing imports still work
    from runbooks.finops.ec2_analyzer import analyze_ec2_costs
    from runbooks.finops.s3_activity_enricher import S3ActivityEnricher

Version: 2.0.0 (Consolidated Architecture)
Epic: Track E - Activity Enrichers Consolidation
"""

from typing import Dict, List, Type

# Base interface (abstract pattern for all enrichers)
from .base import ActivityEnricherBase

# Service-specific enrichers
from .ec2_enricher import EC2Enricher
from .s3_enricher import S3Enricher
from .lambda_enricher import LambdaEnricher
from .dynamodb_enricher import DynamoDBEnricher
from .rds_enricher import RDSEnricher
from .ecs_enricher import ECSEnricher
from .workspaces_enricher import WorkSpacesEnricher
from .appstream_enricher import AppStreamEnricher
from .cloudwatch_enricher import CloudWatchEnricher
from .config_enricher import ConfigEnricher
from .cloudtrail_enricher import CloudTrailEnricher
from .asg_enricher import ASGEnricher

# Orchestrator for parallel execution
from .orchestrator import ActivityOrchestrator

# Service registry for dynamic enricher discovery
SERVICE_ENRICHERS: Dict[str, Type[ActivityEnricherBase]] = {
    "ec2": EC2Enricher,
    "s3": S3Enricher,
    "lambda": LambdaEnricher,
    "dynamodb": DynamoDBEnricher,
    "rds": RDSEnricher,
    "ecs": ECSEnricher,
    "workspaces": WorkSpacesEnricher,
    "appstream": AppStreamEnricher,
    "cloudwatch": CloudWatchEnricher,
    "config": ConfigEnricher,
    "cloudtrail": CloudTrailEnricher,
    "asg": ASGEnricher,
}

# Signal patterns registry (for documentation and validation)
SIGNAL_PATTERNS: Dict[str, List[str]] = {
    "ec2": ["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
    "s3": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
    "lambda": ["L1", "L2", "L3", "L4", "L5", "L6"],
    "dynamodb": ["D1", "D2", "D3", "D4", "D5", "D6", "D7"],
    "rds": ["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
    "ecs": ["C1", "C2", "C3", "C4", "C5", "C6", "C7"],
    "workspaces": ["W1", "W2", "W3", "W4", "W5", "W6"],
    "appstream": ["A1", "A2", "A3", "A4", "A5", "A6", "A7"],
    "cloudwatch": ["M1", "M2", "M3", "M4", "M5", "M6", "M7"],
    "config": ["CFG1", "CFG2", "CFG3", "CFG4", "CFG5"],
    "cloudtrail": ["CT1", "CT2", "CT3", "CT4", "CT5"],
    "asg": ["ASG1", "ASG2", "ASG3", "ASG4", "ASG5"],
}

__all__ = [
    # Base interface
    "ActivityEnricherBase",
    # Service enrichers
    "EC2Enricher",
    "S3Enricher",
    "LambdaEnricher",
    "DynamoDBEnricher",
    "RDSEnricher",
    "ECSEnricher",
    "WorkSpacesEnricher",
    "AppStreamEnricher",
    "CloudWatchEnricher",
    "ConfigEnricher",
    "CloudTrailEnricher",
    "ASGEnricher",
    # Orchestrator
    "ActivityOrchestrator",
    # Registries
    "SERVICE_ENRICHERS",
    "SIGNAL_PATTERNS",
]
