#!/usr/bin/env python3
"""
VPC Endpoint Cleanup Orchestrator - Wave-Based Decommission Framework
======================================================================

Orchestrates phased VPC endpoint cleanup with approval gates and cost savings projections.

Wave-Based Cleanup Strategy (JIRA AWSO-66):
- Wave 4 (MUST): 80-100 points → Immediate decommission candidates
- Wave 5 (SHOULD): 50-79 points → Strong candidates requiring review
- Wave 6 (COULD): 25-49 points → Manual review candidates

VPC Endpoint Decommission Signals (V1-V5):
- V1: No CloudTrail API calls (45 points) - Primary indicator from Track 1
- V2: High ENI count (25 points) - Cost impact (3+ ENIs = 3× hourly cost)
- V3: Interface type (15 points) - Gateway endpoints are FREE
- V4: Single VPC attachment (10 points) - Isolated endpoint indicator
- V5: No tags/owner (5 points) - Governance/ownership indicator

Cost Calculation:
- Interface VPCE: $0.01/hour per ENI × 8760 hours/year
- Gateway VPCE: FREE (excluded from cleanup)
- Annual savings = ENI count × $0.01 × 8760

Business Value (JIRA AWSO-66):
- 65 VPC endpoints identified for cleanup
- $18,457.68 projected annual savings
- 585 hours remediation effort

Pattern: Reuses FinOps decommission_scorer.py framework (E1-E7, W1-W6 proven patterns)

Usage:
    from runbooks.vpc.endpoint_cleanup_orchestrator import VPCEndpointCleanupOrchestrator

    # Initialize orchestrator
    orchestrator = VPCEndpointCleanupOrchestrator(
        profile="CENTRALISED_OPS_PROFILE",
        wave="wave4",
        dry_run=True
    )

    # Load Track 1 activity analysis
    vpce_df = orchestrator.load_activity_analysis("/tmp/vpce-activity-analysis.xlsx")

    # Classify into waves
    vpce_df = orchestrator.classify_wave_candidates(vpce_df)

    # Generate cleanup plan
    cleanup_plan = orchestrator.generate_cleanup_plan(vpce_df)

    # Execute with approval gates
    orchestrator.execute_cleanup(cleanup_plan, approval_required=True)

CLI Usage:
    # Wave 4: MUST decommission (80-100 points)
    runbooks vpc cleanup-endpoints --wave 4 --dry-run

    # Wave 5: SHOULD decommission (50-79 points)
    runbooks vpc cleanup-endpoints --wave 5 --approval-required

    # Wave 6: COULD decommission (25-49 points)
    runbooks vpc cleanup-endpoints --wave 6 --dry-run
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3
import click
import pandas as pd
from botocore.config import Config

from ..common.rich_utils import (
    console,
    create_table,
    print_error,
    print_info,
    print_success,
    print_warning,
)

logger = logging.getLogger(__name__)

# VPC Endpoint Decommission Signal Weights (V1-V5, 0-100 scale)
# Pattern: Follows FinOps decommission_scorer.py (E1-E7, W1-W6)
DEFAULT_VPCE_WEIGHTS = {
    "V1": 45,  # No CloudTrail API calls (90 days) - Track 1 activity analyzer output
    "V2": 25,  # High ENI count (3+ interfaces) - Cost impact multiplier
    "V3": 15,  # Interface type (vs Gateway FREE) - Cost relevance
    "V4": 10,  # Single VPC attachment - Isolation/sharing indicator
    "V5": 5,  # No tags/owner - Governance indicator
}

# Wave Tier Thresholds (matches FinOps pattern)
TIER_THRESHOLDS = {
    "MUST": (80, 100),  # Wave 4: Immediate decommission
    "SHOULD": (50, 79),  # Wave 5: Strong candidates
    "COULD": (25, 49),  # Wave 6: Manual review required
    "KEEP": (0, 24),  # Active endpoints
}

# Pricing constants (ap-southeast-2)
VPCE_INTERFACE_HOURLY_RATE = 0.01  # $0.01/hour per ENI
HOURS_PER_YEAR = 8760
HOURS_PER_MONTH = 720


class VPCEndpointCleanupOrchestrator:
    """
    Orchestrate wave-based VPC endpoint cleanup with approval gates.

    Implements enterprise workflow orchestration patterns:
    - Wave-based classification (4/5/6)
    - Approval gate integration
    - Dry-run mode (safe default)
    - Cost savings projection
    - Audit trail generation

    Strategic Alignment:
    - JIRA AWSO-66: 65 endpoints, $18K annual savings
    - Enterprise SDLC: Evidence-based decommissioning
    - KISS/DRY/LEAN: Reuse FinOps scorer patterns
    """

    WAVE_DEFINITIONS = {
        "wave4": {
            "threshold": 80,
            "tier": "MUST",
            "description": "Immediate decommission candidates (80-100 points)",
            "action": "Create change request → Delete endpoint",
            "approval": "Manager approval required",
        },
        "wave5": {
            "threshold": 50,
            "tier": "SHOULD",
            "description": "Strong candidates requiring review (50-79 points)",
            "action": "Review with stakeholders → Schedule deletion",
            "approval": "Stakeholder approval + Manager sign-off",
        },
        "wave6": {
            "threshold": 25,
            "tier": "COULD",
            "description": "Manual review candidates (25-49 points)",
            "action": "Manual assessment → Optimize or retain",
            "approval": "Architecture review + Business justification",
        },
    }

    def __init__(self, profile: str, wave: str = "wave4", dry_run: bool = True, region: str = "ap-southeast-2"):
        """
        Initialize VPC endpoint cleanup orchestrator.

        Args:
            profile: AWS profile name (e.g., CENTRALISED_OPS_PROFILE)
            wave: Wave identifier (wave4, wave5, wave6)
            dry_run: Dry-run mode (default: True for safety)
            region: AWS region (default: ap-southeast-2)
        """
        self.profile = profile
        self.wave = wave
        self.dry_run = dry_run
        self.region = region

        # Validate wave
        if wave not in self.WAVE_DEFINITIONS:
            raise ValueError(f"Invalid wave: {wave}. Must be one of: {list(self.WAVE_DEFINITIONS.keys())}")

        # Initialize AWS clients with enhanced configuration
        try:
            session = boto3.Session(profile_name=profile)
            config = Config(retries={"max_attempts": 3, "mode": "adaptive"}, region_name=region)
            self.ec2_client = session.client("ec2", config=config)
            self.cloudtrail_client = session.client("cloudtrail", config=config)

            print_info(f"🔧 Initialized cleanup orchestrator: {wave} ({self.WAVE_DEFINITIONS[wave]['tier']})")
            print_info(f"   Profile: {profile} | Region: {region} | Dry-run: {dry_run}")

        except Exception as e:
            print_error(f"❌ Failed to initialize AWS clients: {e}")
            raise

    def load_activity_analysis(self, input_file: str) -> pd.DataFrame:
        """
        Load Track 1 output (VPC endpoint activity analysis).

        Expected CSV/Excel columns from Track 1:
        - vpce_id: VPC endpoint ID (e.g., vpce-1234567890abcdef0)
        - vpc_id: VPC ID
        - account_id: AWS account ID
        - eni_count: Number of ENIs (Elastic Network Interfaces)
        - service_name: AWS service (e.g., com.amazonaws.ap-southeast-2.s3)
        - endpoint_type: Interface or Gateway
        - days_since_activity: Days since last CloudTrail activity (V1 signal)
        - tags: Resource tags (for V5 signal)

        Args:
            input_file: Path to Track 1 output file (CSV or Excel)

        Returns:
            DataFrame with VPC endpoint activity data

        Example:
            >>> orchestrator = VPCEndpointCleanupOrchestrator(profile='ops')
            >>> df = orchestrator.load_activity_analysis('/tmp/vpce-activity.xlsx')
            >>> print(f"Loaded {len(df)} VPC endpoints")
        """
        try:
            input_path = Path(input_file)

            if not input_path.exists():
                print_error(f"❌ Input file not found: {input_file}")
                raise FileNotFoundError(f"Input file not found: {input_file}")

            # Load based on file extension
            if input_path.suffix == ".csv":
                df = pd.read_csv(input_path)
            elif input_path.suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(input_path)
            else:
                raise ValueError(f"Unsupported file format: {input_path.suffix}. Use CSV or Excel.")

            # Validate required columns
            required_cols = ["vpce_id", "eni_count", "endpoint_type"]
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                print_error(f"❌ Missing required columns: {missing_cols}")
                raise ValueError(f"Missing required columns: {missing_cols}")

            print_success(f"✅ Loaded {len(df)} VPC endpoints from {input_file}")

            # Display summary statistics
            interface_count = len(df[df["endpoint_type"] == "Interface"])
            gateway_count = len(df[df["endpoint_type"] == "Gateway"])

            print_info(f"   Interface endpoints: {interface_count} (cost-relevant)")
            print_info(f"   Gateway endpoints: {gateway_count} (FREE)")

            return df

        except Exception as e:
            print_error(f"❌ Failed to load activity analysis: {e}")
            logger.error(f"Load error: {e}", exc_info=True)
            raise

    def classify_wave_candidates(self, vpce_df: pd.DataFrame) -> pd.DataFrame:
        """
        Classify VPC endpoints into waves based on decommission score (V1-V5 signals).

        Signal Breakdown:
        - V1 (45 pts): No CloudTrail API calls for 90 days (from Track 1 days_since_activity)
        - V2 (25 pts): High ENI count (3+ ENIs = cost multiplier)
        - V3 (15 pts): Interface type (Gateway FREE, skip Interface candidates)
        - V4 (10 pts): Single VPC attachment (isolated endpoint)
        - V5 (5 pts): No tags/owner (governance gap)

        Wave Classification:
        - 80-100 points → Wave 4 (MUST decommission)
        - 50-79 points → Wave 5 (SHOULD decommission)
        - 25-49 points → Wave 6 (COULD decommission)
        - 0-24 points → KEEP (active endpoint)

        Args:
            vpce_df: DataFrame with VPC endpoint data from Track 1

        Returns:
            DataFrame with 4 new columns:
            - decommission_score (0-100)
            - decommission_tier (MUST/SHOULD/COULD/KEEP)
            - wave_assignment (wave4/wave5/wave6/none)
            - signal_breakdown (JSON string of V1-V5 signals)

        Example:
            >>> df = orchestrator.load_activity_analysis('/tmp/vpce-activity.xlsx')
            >>> df = orchestrator.classify_wave_candidates(df)
            >>> wave4_df = df[df['wave_assignment'] == 'wave4']
            >>> print(f"Wave 4 candidates: {len(wave4_df)}")
        """
        try:
            print_info("🔍 Classifying VPC endpoints into waves...")

            # Initialize scoring columns
            vpce_df["decommission_score"] = 0
            vpce_df["decommission_tier"] = "KEEP"
            vpce_df["wave_assignment"] = "none"
            vpce_df["signal_breakdown"] = "{}"

            scored_count = 0

            for idx, row in vpce_df.iterrows():
                # Skip Gateway endpoints (FREE, no cleanup needed)
                if row.get("endpoint_type", "") == "Gateway":
                    vpce_df.at[idx, "decommission_score"] = 0
                    vpce_df.at[idx, "decommission_tier"] = "KEEP"
                    vpce_df.at[idx, "wave_assignment"] = "none"
                    vpce_df.at[idx, "signal_breakdown"] = json.dumps({"reason": "Gateway endpoint (FREE)"})
                    continue

                # Calculate V1-V5 signals
                signals = {}
                score = 0

                # V1: No CloudTrail API calls (45 points)
                days_since_activity = row.get("days_since_activity", 0)
                if days_since_activity >= 90:
                    signals["V1"] = 45
                    score += 45
                else:
                    signals["V1"] = 0

                # V2: High ENI count (25 points)
                eni_count = row.get("eni_count", 0)
                if eni_count >= 3:
                    signals["V2"] = 25
                    score += 25
                else:
                    signals["V2"] = 0

                # V3: Interface type (15 points)
                # Already confirmed Interface type (Gateway skipped above)
                signals["V3"] = 15
                score += 15

                # V4: Single VPC attachment (10 points)
                # Heuristic: If only 1 VPC in vpc_id field, likely isolated
                vpc_attachments = row.get("vpc_attachment_count", 1)
                if vpc_attachments == 1:
                    signals["V4"] = 10
                    score += 10
                else:
                    signals["V4"] = 0

                # V5: No tags/owner (5 points)
                tags = row.get("tags", "")
                if not tags or tags == "" or pd.isna(tags):
                    signals["V5"] = 5
                    score += 5
                else:
                    signals["V5"] = 0

                # Determine tier
                if score >= 80:
                    tier = "MUST"
                    wave = "wave4"
                elif score >= 50:
                    tier = "SHOULD"
                    wave = "wave5"
                elif score >= 25:
                    tier = "COULD"
                    wave = "wave6"
                else:
                    tier = "KEEP"
                    wave = "none"

                # Update DataFrame
                vpce_df.at[idx, "decommission_score"] = score
                vpce_df.at[idx, "decommission_tier"] = tier
                vpce_df.at[idx, "wave_assignment"] = wave
                vpce_df.at[idx, "signal_breakdown"] = json.dumps(signals)

                scored_count += 1

            # Display wave distribution
            wave_counts = vpce_df["wave_assignment"].value_counts()

            print_success(f"✅ Classification complete: {scored_count}/{len(vpce_df)} endpoints")
            print_info(f"   Wave 4 (MUST): {wave_counts.get('wave4', 0)} endpoints")
            print_info(f"   Wave 5 (SHOULD): {wave_counts.get('wave5', 0)} endpoints")
            print_info(f"   Wave 6 (COULD): {wave_counts.get('wave6', 0)} endpoints")
            print_info(f"   KEEP: {wave_counts.get('none', 0)} endpoints")

            return vpce_df

        except Exception as e:
            print_error(f"❌ Wave classification failed: {e}")
            logger.error(f"Classification error: {e}", exc_info=True)
            return vpce_df

    def generate_cleanup_plan(self, vpce_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate cleanup plan with cost savings projection.

        Cost Calculation:
        - Annual savings per endpoint = ENI count × $0.01/hr × 8760 hrs
        - Total annual savings = Sum of all endpoint savings

        Cleanup Plan Structure:
        {
            'wave': 'wave4',
            'tier': 'MUST',
            'endpoint_count': 15,
            'total_eni_count': 45,
            'monthly_savings': 324.00,
            'annual_savings': 3888.00,
            'endpoints': [
                {
                    'vpce_id': 'vpce-1234567890abcdef0',
                    'vpc_id': 'vpc-0987654321fedcba0',
                    'account_id': '123456789012',
                    'eni_count': 3,
                    'score': 85,
                    'tier': 'MUST',
                    'signals': {'V1': 45, 'V2': 25, 'V3': 15, 'V4': 0, 'V5': 0},
                    'monthly_savings': 21.60,
                    'annual_savings': 259.20
                }
            ]
        }

        Args:
            vpce_df: DataFrame with classified wave assignments

        Returns:
            Dictionary with cleanup plan details

        Example:
            >>> df = orchestrator.classify_wave_candidates(vpce_df)
            >>> plan = orchestrator.generate_cleanup_plan(df)
            >>> print(f"Annual savings: ${plan['annual_savings']:,.2f}")
        """
        try:
            print_info(f"📋 Generating cleanup plan for {self.wave}...")

            # Filter to current wave
            wave_df = vpce_df[vpce_df["wave_assignment"] == self.wave]

            if len(wave_df) == 0:
                print_warning(f"⚠️  No endpoints found for {self.wave}")
                return {
                    "wave": self.wave,
                    "tier": self.WAVE_DEFINITIONS[self.wave]["tier"],
                    "endpoint_count": 0,
                    "total_eni_count": 0,
                    "monthly_savings": 0.0,
                    "annual_savings": 0.0,
                    "endpoints": [],
                }

            # Build cleanup plan
            endpoints = []
            total_eni_count = 0
            total_annual_savings = 0.0

            for idx, row in wave_df.iterrows():
                eni_count = row.get("eni_count", 0)
                monthly_cost = eni_count * VPCE_INTERFACE_HOURLY_RATE * HOURS_PER_MONTH
                annual_cost = eni_count * VPCE_INTERFACE_HOURLY_RATE * HOURS_PER_YEAR

                total_eni_count += eni_count
                total_annual_savings += annual_cost

                # Parse signals
                signals = json.loads(row.get("signal_breakdown", "{}"))

                endpoint_detail = {
                    "vpce_id": row.get("vpce_id", "N/A"),
                    "vpc_id": row.get("vpc_id", "N/A"),
                    "account_id": row.get("account_id", "N/A"),
                    "service_name": row.get("service_name", "N/A"),
                    "eni_count": eni_count,
                    "score": row.get("decommission_score", 0),
                    "tier": row.get("decommission_tier", "KEEP"),
                    "signals": signals,
                    "monthly_savings": round(monthly_cost, 2),
                    "annual_savings": round(annual_cost, 2),
                    "days_since_activity": row.get("days_since_activity", 0),
                }

                endpoints.append(endpoint_detail)

            # Sort by score (highest first)
            endpoints.sort(key=lambda x: x["score"], reverse=True)

            cleanup_plan = {
                "wave": self.wave,
                "tier": self.WAVE_DEFINITIONS[self.wave]["tier"],
                "description": self.WAVE_DEFINITIONS[self.wave]["description"],
                "action": self.WAVE_DEFINITIONS[self.wave]["action"],
                "approval": self.WAVE_DEFINITIONS[self.wave]["approval"],
                "endpoint_count": len(endpoints),
                "total_eni_count": total_eni_count,
                "monthly_savings": round(total_eni_count * VPCE_INTERFACE_HOURLY_RATE * HOURS_PER_MONTH, 2),
                "annual_savings": round(total_annual_savings, 2),
                "endpoints": endpoints,
                "dry_run": self.dry_run,
                "profile": self.profile,
                "region": self.region,
            }

            print_success(f"✅ Cleanup plan generated")
            print_info(f"   Endpoints: {cleanup_plan['endpoint_count']}")
            print_info(f"   Total ENIs: {cleanup_plan['total_eni_count']}")
            print_info(f"   Monthly savings: ${cleanup_plan['monthly_savings']:,.2f}")
            print_info(f"   Annual savings: ${cleanup_plan['annual_savings']:,.2f}")

            return cleanup_plan

        except Exception as e:
            print_error(f"❌ Cleanup plan generation failed: {e}")
            logger.error(f"Plan generation error: {e}", exc_info=True)
            return {}

    def execute_cleanup(self, cleanup_plan: Dict[str, Any], approval_required: bool = True) -> Dict[str, Any]:
        """
        Execute cleanup plan with approval gates.

        Approval Workflow:
        1. Display cleanup plan summary
        2. Request user approval (if approval_required=True)
        3. Execute deletions (dry-run or actual)
        4. Generate execution report

        Dry-Run Mode (default):
        - No actual deletions performed
        - Displays what WOULD be deleted
        - Safe for validation and cost projection

        Execution Mode (--approve flag):
        - Performs actual VPC endpoint deletions
        - Requires explicit user confirmation
        - Audit trail generated

        Args:
            cleanup_plan: Cleanup plan from generate_cleanup_plan()
            approval_required: Require user confirmation (default: True)

        Returns:
            Dictionary with execution results:
            {
                'dry_run': True,
                'approved': False,
                'executed_count': 0,
                'failed_count': 0,
                'skipped_count': 15,
                'total_savings': 3888.00,
                'execution_log': []
            }

        Example:
            >>> plan = orchestrator.generate_cleanup_plan(df)
            >>> result = orchestrator.execute_cleanup(plan, approval_required=True)
            >>> print(f"Executed: {result['executed_count']}")
        """
        try:
            if self.dry_run:
                console.print("\n" + "=" * 70)
                console.print("[bold yellow]🚨 DRY-RUN MODE: No changes will be made[/bold yellow]")
                console.print("=" * 70 + "\n")
                self._print_cleanup_plan(cleanup_plan)
                return {
                    "dry_run": True,
                    "approved": False,
                    "executed_count": 0,
                    "failed_count": 0,
                    "skipped_count": cleanup_plan["endpoint_count"],
                    "total_savings": cleanup_plan["annual_savings"],
                    "execution_log": ["Dry-run mode: No deletions performed"],
                }

            # Execution mode
            console.print("\n" + "=" * 70)
            console.print("[bold red]⚠️  EXECUTION MODE: Changes will be made[/bold red]")
            console.print("=" * 70 + "\n")

            self._print_cleanup_plan(cleanup_plan)

            # Request approval
            if approval_required:
                console.print("\n[bold yellow]Approval required to proceed with cleanup[/bold yellow]")
                approval = click.confirm(
                    f"Delete {cleanup_plan['endpoint_count']} VPC endpoints "
                    f"(${cleanup_plan['annual_savings']:,.2f} annual savings)?",
                    default=False,
                )

                if not approval:
                    print_warning("❌ Cleanup aborted by user")
                    return {
                        "dry_run": False,
                        "approved": False,
                        "executed_count": 0,
                        "failed_count": 0,
                        "skipped_count": cleanup_plan["endpoint_count"],
                        "total_savings": 0.0,
                        "execution_log": ["User declined approval"],
                    }

            # Execute deletions
            return self._delete_vpc_endpoints(cleanup_plan)

        except Exception as e:
            print_error(f"❌ Cleanup execution failed: {e}")
            logger.error(f"Execution error: {e}", exc_info=True)
            return {
                "dry_run": self.dry_run,
                "approved": False,
                "executed_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "total_savings": 0.0,
                "execution_log": [f"Execution error: {str(e)}"],
            }

    def _print_cleanup_plan(self, cleanup_plan: Dict[str, Any]) -> None:
        """Display cleanup plan with Rich CLI formatting."""
        # Summary table
        summary_table = create_table(
            title=f"Cleanup Plan: {cleanup_plan['wave'].upper()} ({cleanup_plan['tier']})",
            columns=[{"header": "Metric", "style": "cyan bold"}, {"header": "Value", "style": "yellow"}],
        )

        summary_table.add_row("Wave", cleanup_plan["wave"])
        summary_table.add_row("Tier", cleanup_plan["tier"])
        summary_table.add_row("Endpoints", str(cleanup_plan["endpoint_count"]))
        summary_table.add_row("Total ENIs", str(cleanup_plan["total_eni_count"]))
        summary_table.add_row("Monthly Savings", f"${cleanup_plan['monthly_savings']:,.2f}")
        summary_table.add_row("Annual Savings", f"${cleanup_plan['annual_savings']:,.2f}")
        summary_table.add_row("Action", cleanup_plan["action"])
        summary_table.add_row("Approval", cleanup_plan["approval"])

        console.print(summary_table)

        # Top 10 endpoints by score
        if cleanup_plan["endpoints"]:
            console.print("\n[bold cyan]Top 10 Decommission Candidates:[/bold cyan]\n")

            endpoints_table = create_table(
                title=None,
                columns=[
                    {"header": "VPCE ID", "style": "cyan"},
                    {"header": "Score", "style": "yellow"},
                    {"header": "ENIs", "style": "green"},
                    {"header": "Annual $", "style": "magenta"},
                    {"header": "Inactive Days", "style": "red"},
                ],
            )

            for endpoint in cleanup_plan["endpoints"][:10]:
                endpoints_table.add_row(
                    endpoint["vpce_id"][:24],
                    str(endpoint["score"]),
                    str(endpoint["eni_count"]),
                    f"${endpoint['annual_savings']:,.2f}",
                    str(endpoint["days_since_activity"]),
                )

            console.print(endpoints_table)

    def _delete_vpc_endpoints(self, cleanup_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute VPC endpoint deletions with error handling."""
        executed_count = 0
        failed_count = 0
        execution_log = []

        console.print("\n[bold cyan]Executing VPC endpoint deletions...[/bold cyan]\n")

        for endpoint in cleanup_plan["endpoints"]:
            vpce_id = endpoint["vpce_id"]

            try:
                # Delete VPC endpoint
                self.ec2_client.delete_vpc_endpoints(VpcEndpointIds=[vpce_id])

                executed_count += 1
                execution_log.append(f"✅ Deleted: {vpce_id} (${endpoint['annual_savings']}/year)")
                print_success(f"✅ Deleted: {vpce_id}")

            except Exception as e:
                failed_count += 1
                execution_log.append(f"❌ Failed: {vpce_id} - {str(e)}")
                print_error(f"❌ Failed: {vpce_id} - {str(e)}")

        # Summary
        console.print("\n" + "=" * 70)
        print_success(f"✅ Cleanup execution complete")
        print_info(f"   Executed: {executed_count}/{cleanup_plan['endpoint_count']}")
        print_info(f"   Failed: {failed_count}")
        print_info(f"   Total savings: ${cleanup_plan['annual_savings']:,.2f}/year")

        return {
            "dry_run": False,
            "approved": True,
            "executed_count": executed_count,
            "failed_count": failed_count,
            "skipped_count": 0,
            "total_savings": cleanup_plan["annual_savings"],
            "execution_log": execution_log,
        }
