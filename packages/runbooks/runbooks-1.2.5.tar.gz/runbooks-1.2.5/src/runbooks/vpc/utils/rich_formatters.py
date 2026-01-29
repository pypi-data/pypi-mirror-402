"""
VPC Rich CLI Formatters - Manager-friendly table formatting

Manager output format (15 columns):
VPC ID | Account | Env | NAT | VPCE(I) | VPCE(G) | ENI | TGW | EC2 | Lambda | Cost/Mo | Tech | Biz | Three-Bucket | Recommendation | Rationale
"""

from typing import List
from rich.table import Table
from runbooks.common.rich_utils import console, create_table, format_cost
from runbooks.vpc.models import VPCAnalysis


class VPCTableFormatter:
    """Format VPC analysis results using Rich CLI."""

    def create_decision_matrix_table(self, analyses: List[VPCAnalysis]) -> Table:
        """
        Create manager-friendly decision matrix table (15 columns).

        Columns:
        1. VPC ID
        2. Account
        3. Env
        4. NAT (count)
        5. VPCE(I) (Interface VPCEs)
        6. VPCE(G) (Gateway VPCEs - FREE)
        7. ENI (network interfaces)
        8. TGW (Transit Gateway attachments)
        9. EC2 (instances)
        10. Lambda (functions)
        11. Cost/Mo (monthly cost)
        12. Tech (technical score)
        13. Biz (business score)
        14. Three-Bucket (MUST/COULD/SHOULD NOT DELETE)
        15. Recommendation
        16. Rationale (WHY)
        """
        table = create_table(
            title="VPC Decommissioning Decision Matrix",
            columns=[
                {"name": "VPC ID", "justify": "left"},
                {"name": "Account", "justify": "left"},
                {"name": "Env", "justify": "left"},
                {"name": "NAT", "justify": "right"},
                {"name": "VPCE(I)", "justify": "right"},
                {"name": "VPCE(G)", "justify": "right"},
                {"name": "ENI", "justify": "right"},
                {"name": "TGW", "justify": "right"},
                {"name": "EC2", "justify": "right"},
                {"name": "Lambda", "justify": "right"},
                {"name": "Cost/Mo", "justify": "right"},
                {"name": "Tech", "justify": "right"},
                {"name": "Biz", "justify": "right"},
                {"name": "Three-Bucket", "justify": "left"},
                {"name": "Recommendation", "justify": "left"},
                {"name": "Rationale", "justify": "left"},
            ],
        )

        # Sort by cost (descending)
        sorted_analyses = sorted(analyses, key=lambda a: a.cost_breakdown.total_monthly_cost, reverse=True)

        for analysis in sorted_analyses:
            r = analysis.resources
            m = analysis.metadata
            c = analysis.cost_breakdown

            # Color-code three-bucket status
            if analysis.three_bucket == "MUST DELETE":
                status_color = "[red]🔴 MUST DELETE[/red]"
            elif analysis.three_bucket == "COULD DELETE":
                status_color = "[yellow]🟡 COULD DELETE[/yellow]"
            else:
                status_color = "[green]🟢 RETAIN[/green]"

            table.add_row(
                m.vpc_id,
                m.account_id,
                m.environment,
                str(r.nat_gateways),
                str(r.vpce_interface),
                str(r.vpce_gateway),
                str(r.enis),
                str(r.tgw_attachments),
                str(r.ec2_instances),
                str(r.lambda_functions),
                format_cost(float(c.total_monthly_cost)),
                str(analysis.technical_score),
                str(analysis.business_score),
                status_color,
                analysis.recommendation,
                analysis.rationale,
            )

        return table

    def print_summary_statistics(self, analyses: List[VPCAnalysis]) -> None:
        """Print summary statistics."""
        total_cost = sum(a.cost_breakdown.total_monthly_cost for a in analyses)
        must_delete = [a for a in analyses if a.three_bucket == "MUST DELETE"]
        could_delete = [a for a in analyses if a.three_bucket == "COULD DELETE"]
        should_not = [a for a in analyses if a.three_bucket == "SHOULD NOT DELETE"]

        console.print("\n[bold]Summary Statistics:[/bold]")
        console.print(f"Total Monthly Cost: {format_cost(float(total_cost))} (${total_cost * 12:.2f}/year)")
        console.print(
            f"MUST DELETE: {len(must_delete)} VPCs ({format_cost(float(sum(a.cost_breakdown.total_monthly_cost for a in must_delete)))})"
        )
        console.print(
            f"COULD DELETE: {len(could_delete)} VPCs ({format_cost(float(sum(a.cost_breakdown.total_monthly_cost for a in could_delete)))})"
        )
        console.print(
            f"SHOULD NOT DELETE: {len(should_not)} VPCs ({format_cost(float(sum(a.cost_breakdown.total_monthly_cost for a in should_not)))})"
        )
