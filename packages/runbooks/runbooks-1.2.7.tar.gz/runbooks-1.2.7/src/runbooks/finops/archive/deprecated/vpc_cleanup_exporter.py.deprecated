#!/usr/bin/env python3
"""
VPC Cleanup Exporter Module - Enterprise VPC Cleanup Result Export

This module provides export functionality for VPC cleanup analysis results,
leveraging the existing markdown_exporter infrastructure with VPC-specific formatting.

Author: Runbooks Team
Version: latest version
"""

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List

from runbooks.common.rich_utils import console

from .markdown_exporter import MarkdownExporter


class VPCCleanupExporter:
    """VPC Cleanup results exporter class."""

    def __init__(self, output_dir: str = "./"):
        """Initialize VPC cleanup exporter."""
        self.output_dir = output_dir

    def export_results(self, vpc_result: Any, export_formats: List[str]) -> Dict[str, str]:
        """Export VPC cleanup results in specified formats."""
        return export_vpc_cleanup_results(vpc_result, export_formats, self.output_dir)


def _format_tags_for_display(tags_dict: Dict[str, str]) -> str:
    """Format tags for display with priority order, emphasizing ownership tags."""
    if not tags_dict:
        return "No tags"

    # Enhanced priority keys with focus on ownership and approvals
    priority_keys = [
        "Name",
        "Owner",
        "BusinessOwner",
        "TechnicalOwner",
        "Team",
        "Contact",
        "Environment",
        "Project",
        "CostCenter",
        "CreatedBy",
        "ManagedBy",
    ]
    relevant_tags = []

    for key in priority_keys:
        if key in tags_dict and tags_dict[key]:
            relevant_tags.append(f"{key}:{tags_dict[key]}")

    # Add CloudFormation/Terraform tags for IaC detection
    iac_keys = ["aws:cloudformation:stack-name", "terraform:module", "cdktf:stack", "pulumi:project"]
    for key in iac_keys:
        if key in tags_dict and tags_dict[key] and len(relevant_tags) < 6:
            relevant_tags.append(f"IaC:{tags_dict[key]}")

    # Add other important tags
    for key, value in tags_dict.items():
        if key not in priority_keys + iac_keys and value and len(relevant_tags) < 5:
            relevant_tags.append(f"{key}:{value}")

    return "; ".join(relevant_tags) if relevant_tags else f"({len(tags_dict)} tags)"


def export_vpc_cleanup_results(vpc_result: Any, export_formats: List[str], output_dir: str = "./") -> Dict[str, str]:
    """
    Export VPC cleanup results in multiple formats.

    Args:
        vpc_result: VPC cleanup analysis result object
        export_formats: List of formats to export (markdown, csv, json, pdf)
        output_dir: Directory to save exported files

    Returns:
        Dict mapping format to exported filename
    """
    results = {}

    # Extract VPC candidates from result - use correct attribute name
    vpc_candidates = getattr(vpc_result, "cleanup_candidates", [])
    if not vpc_candidates:
        # Fallback to other possible attribute names
        vpc_candidates = getattr(vpc_result, "vpc_candidates", [])

    if "markdown" in export_formats:
        try:
            exporter = MarkdownExporter()
            markdown_filename = exporter.export_vpc_analysis_to_file(
                vpc_candidates, filename="vpc-cleanup-candidates.md", output_dir=output_dir
            )
            results["markdown"] = markdown_filename
        except Exception as e:
            console.print(f"[yellow]Warning: Markdown export failed: {e}[/yellow]")
            results["markdown"] = None

    # Real implementations for other formats
    if "csv" in export_formats:
        try:
            csv_filename = _export_vpc_candidates_csv(vpc_candidates, output_dir)
            results["csv"] = csv_filename
        except Exception as e:
            print(f"Warning: CSV export failed: {e}")
            results["csv"] = None

    if "json" in export_formats:
        try:
            json_filename = _export_vpc_candidates_json(vpc_candidates, output_dir)
            results["json"] = json_filename
        except Exception as e:
            print(f"Warning: JSON export failed: {e}")
            results["json"] = None

    if "pdf" in export_formats:
        try:
            pdf_filename = _export_vpc_candidates_pdf(vpc_candidates, output_dir)
            results["pdf"] = pdf_filename
        except Exception as e:
            print(f"Warning: PDF export failed: {e}")
            results["pdf"] = None

    return results


def _export_vpc_candidates_csv(vpc_candidates: List[Any], output_dir: str) -> str:
    """Export VPC candidates to CSV format with all 15 columns."""
    filename = os.path.join(output_dir, "vpc-cleanup-candidates.csv")

    # 15-column headers for comprehensive VPC analysis
    headers = [
        "Account_ID",
        "VPC_ID",
        "VPC_Name",
        "CIDR_Block",
        "Overlapping",
        "Is_Default",
        "ENI_Count",
        "Tags",
        "Flow_Logs",
        "TGW/Peering",
        "LBs_Present",
        "IaC",
        "Timeline",
        "Decision",
        "Owners/Approvals",
        "Notes",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for candidate in vpc_candidates:
            # Extract data with enhanced tag and owner handling
            tags_dict = getattr(candidate, "tags", {}) or {}

            # Use enhanced tag formatting function
            tags_str = _format_tags_for_display(tags_dict)

            load_balancers = getattr(candidate, "load_balancers", []) or []
            lbs_present = "Yes" if load_balancers else "No"

            # Enhanced owner extraction from multiple sources
            owners = getattr(candidate, "owners_approvals", []) or []

            # Extract owners from tags with enhanced logic
            if not owners and tags_dict:
                owner_keys = ["Owner", "BusinessOwner", "TechnicalOwner", "Team", "Contact", "CreatedBy", "ManagedBy"]
                for key in owner_keys:
                    if key in tags_dict and tags_dict[key]:
                        value = tags_dict[key]
                        if "business" in key.lower() or "manager" in value.lower():
                            owners.append(f"{value} (Business)")
                        elif "technical" in key.lower() or "engineer" in value.lower():
                            owners.append(f"{value} (Technical)")
                        elif "team" in key.lower():
                            owners.append(f"{value} (Team)")
                        else:
                            owners.append(f"{value} ({key})")

            # For default VPCs, add system indicator
            is_default = getattr(candidate, "is_default", False)
            if is_default and not owners:
                owners.append("System Default")

            if owners:
                owners_str = "; ".join(owners)
            else:
                # Enhanced fallback for CSV
                if getattr(candidate, "is_default", False):
                    owners_str = "System Default VPC"
                elif getattr(candidate, "iac_detected", False):
                    owners_str = "IaC Managed"
                else:
                    owners_str = "No owner tags found"

            row = [
                getattr(candidate, "account_id", "Unknown"),
                getattr(candidate, "vpc_id", ""),
                getattr(candidate, "vpc_name", "Unnamed"),
                getattr(candidate, "cidr_block", ""),
                "No",  # Overlapping analysis would need CIDR comparison
                "Yes" if getattr(candidate, "is_default", False) else "No",
                getattr(candidate, "dependency_analysis", {}).eni_count
                if hasattr(candidate, "dependency_analysis")
                else 0,
                tags_str,
                "Yes" if getattr(candidate, "flow_logs_enabled", False) else "No",
                "No",  # TGW/Peering analysis placeholder
                lbs_present,
                "Yes" if getattr(candidate, "iac_detected", False) else "No",
                "Unknown",  # Timeline analysis placeholder
                getattr(candidate, "cleanup_recommendation", "unknown"),
                owners_str,
                "Generated by Runbooks VPC Module",
            ]
            writer.writerow(row)

    return filename


def _export_vpc_candidates_json(vpc_candidates: List[Any], output_dir: str) -> str:
    """Export VPC candidates to JSON format with full data structure."""
    filename = os.path.join(output_dir, "vpc-cleanup-candidates.json")

    # Convert candidates to serializable format
    candidates_data = []
    for candidate in vpc_candidates:
        candidate_dict = {
            "account_id": getattr(candidate, "account_id", "Unknown"),
            "vpc_id": getattr(candidate, "vpc_id", ""),
            "vpc_name": getattr(candidate, "vpc_name", "Unnamed"),
            "cidr_block": getattr(candidate, "cidr_block", ""),
            "region": getattr(candidate, "region", "unknown"),
            "is_default": getattr(candidate, "is_default", False),
            "state": getattr(candidate, "state", "unknown"),
            "tags": getattr(candidate, "tags", {}) or {},
            "tags_summary": _format_tags_for_display(getattr(candidate, "tags", {}) or {}),
            "flow_logs_enabled": getattr(candidate, "flow_logs_enabled", False),
            "load_balancers": getattr(candidate, "load_balancers", []) or [],
            "iac_detected": getattr(candidate, "iac_detected", False),
            "owners_approvals": getattr(candidate, "owners_approvals", []) or [],
            "cleanup_bucket": getattr(candidate, "cleanup_bucket", "unknown"),
            "cleanup_recommendation": getattr(candidate, "cleanup_recommendation", "unknown"),
            "risk_assessment": getattr(candidate, "risk_assessment", "unknown"),
            "business_impact": getattr(candidate, "business_impact", "unknown"),
        }

        # Add dependency analysis if available
        if hasattr(candidate, "dependency_analysis") and candidate.dependency_analysis:
            dep_analysis = candidate.dependency_analysis
            candidate_dict["dependency_analysis"] = {
                "eni_count": getattr(dep_analysis, "eni_count", 0),
                "route_tables": getattr(dep_analysis, "route_tables", []),
                "security_groups": getattr(dep_analysis, "security_groups", []),
                "internet_gateways": getattr(dep_analysis, "internet_gateways", []),
                "nat_gateways": getattr(dep_analysis, "nat_gateways", []),
                "vpc_endpoints": getattr(dep_analysis, "vpc_endpoints", []),
                "peering_connections": getattr(dep_analysis, "peering_connections", []),
                "dependency_risk_level": getattr(dep_analysis, "dependency_risk_level", "unknown"),
            }

        candidates_data.append(candidate_dict)

    # Create export metadata
    export_data = {
        "metadata": {
            "export_timestamp": datetime.now().isoformat(),
            "total_candidates": len(candidates_data),
            "generator": "Runbooks VPC Module latest version",
        },
        "vpc_candidates": candidates_data,
    }

    with open(filename, "w", encoding="utf-8") as jsonfile:
        json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)

    return filename


def _export_vpc_candidates_pdf(vpc_candidates: List[Any], output_dir: str) -> str:
    """Export VPC candidates to PDF format for executive presentation."""
    filename = os.path.join(output_dir, "vpc-cleanup-candidates.pdf")

    try:
        # Try to use reportlab for PDF generation
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title = Paragraph("VPC Cleanup Analysis Report", styles["Title"])
        story.append(title)
        story.append(Spacer(1, 20))

        # Summary
        summary_text = f"""
        <b>Generated:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")}<br/>
        <b>Total VPC Candidates:</b> {len(vpc_candidates)}<br/>
        <b>Analysis Source:</b> Runbooks VPC Module latest version
        """
        summary = Paragraph(summary_text, styles["Normal"])
        story.append(summary)
        story.append(Spacer(1, 20))

        # Create table data
        table_data = [["Account ID", "VPC ID", "VPC Name", "CIDR", "Default", "ENI Count", "Decision"]]

        for candidate in vpc_candidates:
            row = [
                str(getattr(candidate, "account_id", "Unknown"))[:15],  # Truncate for PDF width
                str(getattr(candidate, "vpc_id", ""))[:20],
                str(getattr(candidate, "vpc_name", "Unnamed"))[:15],
                str(getattr(candidate, "cidr_block", ""))[:15],
                "Yes" if getattr(candidate, "is_default", False) else "No",
                str(
                    getattr(candidate, "dependency_analysis", {}).eni_count
                    if hasattr(candidate, "dependency_analysis")
                    else 0
                ),
                str(getattr(candidate, "cleanup_recommendation", "unknown"))[:10],
            ]
            table_data.append(row)

        # Create table
        table = Table(table_data)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        story.append(table)
        doc.build(story)

    except ImportError:
        # Fallback: create a simple text-based PDF placeholder
        with open(filename, "w", encoding="utf-8") as f:
            f.write("VPC Cleanup Analysis Report (PDF)\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            f.write(f"Total VPC Candidates: {len(vpc_candidates)}\n\n")

            for i, candidate in enumerate(vpc_candidates, 1):
                f.write(f"{i}. VPC {getattr(candidate, 'vpc_id', 'Unknown')}\n")
                f.write(f"   Account: {getattr(candidate, 'account_id', 'Unknown')}\n")
                f.write(f"   CIDR: {getattr(candidate, 'cidr_block', 'Unknown')}\n")
                f.write(
                    f"   ENI Count: {getattr(candidate, 'dependency_analysis', {}).eni_count if hasattr(candidate, 'dependency_analysis') else 0}\n"
                )
                f.write(f"   Decision: {getattr(candidate, 'cleanup_recommendation', 'unknown')}\n\n")

    return filename
