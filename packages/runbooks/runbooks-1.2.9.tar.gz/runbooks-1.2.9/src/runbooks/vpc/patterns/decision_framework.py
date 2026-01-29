#!/usr/bin/env python3
"""
Decision Framework Pattern - Data-Driven Resource Cleanup Prioritization

Base class for calculating cleanup priority scores based on activity and cost data.

Design Pattern:
    - Abstract base class requiring _get_resources_for_scoring() implementation
    - Two-gate scoring methodology (activity + cost dimensions)
    - Configurable thresholds for business-specific criteria
    - Priority classification: MUST (0.7+), SHOULD (0.4-0.7), Could (<0.4)
    - Rich CLI table rendering for manager decision-making

Reusability:
    - VPCE Cleanup Manager (current implementation)
    - VPC Cleanup (future enhancement)
    - NAT Gateway Optimizer (future enhancement)
    - Any cost+activity-based cleanup workflow

Usage:
    class MyManager(DecisionFramework):
        def _get_resources_for_scoring(self):
            return self.endpoints  # List[VPCEndpoint]

    manager = MyManager()
    criteria = DecisionCriteria(
        idle_threshold_days=30,
        high_cost_threshold=100.0
    )
    result = manager.calculate_decision_scores(criteria)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from runbooks.common.rich_utils import (
    console,
    create_table,
    format_cost,
    print_info,
    print_success,
)


class DecisionPriority(Enum):
    """Cleanup priority classification based on score."""

    MUST = "MUST"  # Score ≥0.7: Idle + High Cost
    SHOULD = "SHOULD"  # Score 0.4-0.7: Idle OR High Cost
    COULD = "Could"  # Score <0.4: Active + Low Cost


@dataclass
class DecisionCriteria:
    """Configurable criteria for decision scoring."""

    idle_threshold_days: int = 30  # Days since last access to classify as idle
    high_cost_threshold: float = 100.0  # Monthly cost to classify as high cost
    activity_weight: float = 0.6  # Weight for activity score (0.0-1.0)
    cost_weight: float = 0.4  # Weight for cost score (0.0-1.0)


@dataclass
class DecisionScore:
    """Cleanup priority score for a single resource."""

    resource_id: str
    activity_score: float  # 0.0 (active) → 1.0 (idle)
    cost_score: float  # 0.0 (low cost) → 1.0 (high cost)
    overall_score: float  # Weighted average
    priority: DecisionPriority  # MUST / SHOULD / Could
    days_since_access: Optional[int] = None
    monthly_cost: float = 0.0
    annual_cost: float = 0.0
    rationale: str = ""  # Decision rationale for managers


@dataclass
class DecisionFrameworkResult:
    """Result from decision framework scoring."""

    total_resources: int
    must_cleanup: int  # Score ≥0.7
    should_cleanup: int  # Score 0.4-0.7
    could_cleanup: int  # Score <0.4
    scores: Dict[str, DecisionScore] = field(default_factory=dict)  # resource_id → score
    savings_potential: Dict[str, float] = field(default_factory=dict)  # priority → annual savings


class DecisionFramework(ABC):
    """
    Base class for data-driven cleanup decision scoring.

    Provides reusable methods for:
    - Two-gate scoring (activity + cost dimensions)
    - Priority classification (MUST/SHOULD/Could)
    - Configurable thresholds for business criteria
    - Rich CLI decision tables for manager review
    - Savings potential aggregation by priority

    Subclass Requirements:
        - Implement _get_resources_for_scoring() → List[Resource]
        - Resource must have:
            * id: str (resource identifier)
            * monthly_cost: float (monthly cost in USD)
            * annual_cost: float (annual cost in USD)
            * last_access: Optional[datetime] (last activity timestamp)

    Scoring Methodology:
        activity_score = min(days_since_access / idle_threshold_days, 1.0)
        cost_score = min(monthly_cost / high_cost_threshold, 1.0)
        overall_score = (activity_score × 0.6) + (cost_score × 0.4)

    Priority Classification:
        - MUST (≥0.7): Idle + High Cost → Immediate cleanup
        - SHOULD (0.4-0.7): Idle OR High Cost → Review cleanup
        - Could (<0.4): Active + Low Cost → Monitor
    """

    @abstractmethod
    def _get_resources_for_scoring(self) -> List:
        """
        Return resources for decision scoring.

        Returns:
            List[Resource] where Resource has:
                - id: str (resource identifier)
                - monthly_cost: float (monthly cost in USD)
                - annual_cost: float (annual cost in USD)
                - last_access: Optional[datetime] (last activity timestamp)
                - Additional resource-specific fields
        """
        pass

    def calculate_decision_scores(self, criteria: Optional[DecisionCriteria] = None) -> DecisionFrameworkResult:
        """
        Calculate cleanup priority scores for all resources.

        Args:
            criteria: Decision criteria (defaults to standard thresholds)

        Returns:
            DecisionFrameworkResult with scores and priority classification

        Example:
            >>> result = manager.calculate_decision_scores()
            >>> # ✅ Scored 88 resources: 23 MUST, 34 SHOULD, 31 Could cleanup
            >>> # Savings potential: MUST = $45,678/year, SHOULD = $23,456/year
        """
        if criteria is None:
            criteria = DecisionCriteria()

        resources = self._get_resources_for_scoring()

        if not resources:
            print_info("⚠️  No resources to score (empty resource list)")
            return DecisionFrameworkResult(
                total_resources=0,
                must_cleanup=0,
                should_cleanup=0,
                could_cleanup=0,
            )

        print_info(
            f"🔍 Calculating decision scores for {len(resources)} resources "
            f"(idle threshold: {criteria.idle_threshold_days} days, "
            f"high cost: ${criteria.high_cost_threshold}/month)..."
        )

        # Calculate scores
        scores = {}
        must_count = 0
        should_count = 0
        could_count = 0

        savings_by_priority = {
            DecisionPriority.MUST: 0.0,
            DecisionPriority.SHOULD: 0.0,
            DecisionPriority.COULD: 0.0,
        }

        for resource in resources:
            resource_id = getattr(resource, "id", "unknown")
            monthly_cost = getattr(resource, "monthly_cost", 0.0)
            annual_cost = getattr(resource, "annual_cost", 0.0)
            last_access = getattr(resource, "last_access", None)

            # Calculate activity score
            if last_access:
                days_since_access = (datetime.now(last_access.tzinfo) - last_access).days
                activity_score = min(days_since_access / criteria.idle_threshold_days, 1.0)
            else:
                # No activity data = assume idle
                days_since_access = None  # Preserve None to indicate no data
                activity_score = 1.0

            # Calculate cost score
            cost_score = min(monthly_cost / criteria.high_cost_threshold, 1.0)

            # Calculate overall score (weighted average)
            overall_score = activity_score * criteria.activity_weight + cost_score * criteria.cost_weight

            # Classify priority
            if overall_score >= 0.7:
                priority = DecisionPriority.MUST
                must_count += 1
            elif overall_score >= 0.4:
                priority = DecisionPriority.SHOULD
                should_count += 1
            else:
                priority = DecisionPriority.COULD
                could_count += 1

            # Generate rationale
            rationale = self._generate_rationale(
                activity_score,
                cost_score,
                days_since_access,
                monthly_cost,
                criteria,
            )

            # Store score
            scores[resource_id] = DecisionScore(
                resource_id=resource_id,
                activity_score=activity_score,
                cost_score=cost_score,
                overall_score=overall_score,
                priority=priority,
                days_since_access=days_since_access,
                monthly_cost=monthly_cost,
                annual_cost=annual_cost,
                rationale=rationale,
            )

            # Aggregate savings potential
            savings_by_priority[priority] += annual_cost

        print_success(
            f"✅ Scored {len(resources)} resources: "
            f"{must_count} MUST, {should_count} SHOULD, {could_count} Could cleanup"
        )

        # Display savings potential
        print_info(
            f"💰 Savings potential: "
            f"MUST = {format_cost(savings_by_priority[DecisionPriority.MUST])}/year, "
            f"SHOULD = {format_cost(savings_by_priority[DecisionPriority.SHOULD])}/year"
        )

        return DecisionFrameworkResult(
            total_resources=len(resources),
            must_cleanup=must_count,
            should_cleanup=should_count,
            could_cleanup=could_count,
            scores=scores,
            savings_potential={
                "MUST": savings_by_priority[DecisionPriority.MUST],
                "SHOULD": savings_by_priority[DecisionPriority.SHOULD],
                "Could": savings_by_priority[DecisionPriority.COULD],
            },
        )

    def _generate_rationale(
        self,
        activity_score: float,
        cost_score: float,
        days_since_access: Optional[int],
        monthly_cost: float,
        criteria: DecisionCriteria,
    ) -> str:
        """
        Generate human-readable rationale for decision score.

        Args:
            activity_score: Activity score (0.0-1.0)
            cost_score: Cost score (0.0-1.0)
            days_since_access: Days since last access (or None)
            monthly_cost: Monthly cost in USD
            criteria: Decision criteria

        Returns:
            Rationale string for manager review
        """
        rationale_parts = []

        # Activity component
        if days_since_access is None:
            rationale_parts.append("No activity data (assumed idle)")
        elif days_since_access >= criteria.idle_threshold_days:
            rationale_parts.append(f"Idle {days_since_access} days")
        else:
            rationale_parts.append(f"Active ({days_since_access} days since last use)")

        # Cost component
        if monthly_cost >= criteria.high_cost_threshold:
            rationale_parts.append(f"High cost (${monthly_cost:.2f}/month)")
        elif monthly_cost >= criteria.high_cost_threshold * 0.5:
            rationale_parts.append(f"Medium cost (${monthly_cost:.2f}/month)")
        else:
            rationale_parts.append(f"Low cost (${monthly_cost:.2f}/month)")

        return " + ".join(rationale_parts)

    def generate_decision_table(
        self,
        result: DecisionFrameworkResult,
        priority_filter: Optional[DecisionPriority] = None,
        limit: int = 20,
    ) -> None:
        """
        Generate Rich CLI decision table for manager review.

        Args:
            result: Decision framework result
            priority_filter: Show only specific priority (None = all)
            limit: Maximum resources to display

        Example:
            >>> manager.generate_decision_table(result, DecisionPriority.MUST)
            >>> # Displays top 20 MUST cleanup resources with scores and rationale
        """
        # Filter scores by priority
        if priority_filter:
            filtered_scores = [score for score in result.scores.values() if score.priority == priority_filter]
            table_title = f"Decision Framework - {priority_filter.value} Cleanup Priority"
        else:
            filtered_scores = list(result.scores.values())
            table_title = "Decision Framework - All Resources"

        # Sort by overall score (descending)
        filtered_scores.sort(key=lambda s: s.overall_score, reverse=True)

        # Limit results
        filtered_scores = filtered_scores[:limit]

        # Create Rich CLI table
        table = create_table(
            title=table_title,
            columns=[
                {"name": "Resource ID", "justify": "left", "style": "cyan"},
                {"name": "Priority", "justify": "center"},
                {"name": "Score", "justify": "right", "style": "yellow"},
                {"name": "Activity", "justify": "right"},
                {"name": "Cost/Month", "justify": "right", "style": "green"},
                {"name": "Rationale", "justify": "left", "style": "dim"},
            ],
        )

        for score in filtered_scores:
            # Priority styling
            if score.priority == DecisionPriority.MUST:
                priority_display = f"[bold red]{score.priority.value}[/bold red]"
            elif score.priority == DecisionPriority.SHOULD:
                priority_display = f"[bold yellow]{score.priority.value}[/bold yellow]"
            else:
                priority_display = f"[dim]{score.priority.value}[/dim]"

            # Activity display
            if score.days_since_access is None:
                activity_display = "No data"
            else:
                activity_display = f"{score.days_since_access} days"

            table.add_row(
                score.resource_id[:20] + ("..." if len(score.resource_id) > 20 else ""),
                priority_display,
                f"{score.overall_score:.2f}",
                activity_display,
                f"${score.monthly_cost:.2f}",
                score.rationale[:50] + ("..." if len(score.rationale) > 50 else ""),
            )

        console.print("\n")
        console.print(table)
        console.print(
            f"\n[dim italic]Decision Framework: Activity ({int(DecisionCriteria().activity_weight * 100)}%) + "
            f"Cost ({int(DecisionCriteria().cost_weight * 100)}%) | "
            f"Showing top {len(filtered_scores)} resources[/dim italic]\n"
        )
