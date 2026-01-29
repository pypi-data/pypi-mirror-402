"""
Enterprise FinOps Platform - RunbooksWrapper
Provides unified access to all runbooks CLI commands with MCP validation and Rich output
"""

import subprocess
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import pandas as pd

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()


class RunbooksWrapper:
    """
    Enterprise wrapper for runbooks CLI commands with MCP validation and Rich output.

    Provides Jupyter-friendly interface to all runbooks functionality:
    - Inventory collection and analysis
    - FinOps cost analysis and optimization
    - Security assessments and remediation
    - CFAT well-architected evaluations
    - Operations automation
    - Organization management
    """

    def __init__(self, default_profile: Optional[str] = None):
        """Initialize wrapper with optional default AWS profile."""
        self.default_profile = default_profile
        self.console = Console()

    def _execute_command(self, command: str, capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute runbooks command with error handling and rich output.

        Args:
            command: Full runbooks command to execute
            capture_output: Whether to capture command output

        Returns:
            Dictionary with command result, output, and metadata
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(description="Executing command...", total=None)

                result = subprocess.run(
                    command.split(),
                    capture_output=capture_output,
                    text=True,
                    timeout=300,  # 5 minute timeout
                )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
                "timestamp": datetime.now().isoformat(),
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Command timed out after 5 minutes",
                "command": command,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"success": False, "error": str(e), "command": command, "timestamp": datetime.now().isoformat()}

    # Inventory Operations
    def inventory_collect(
        self,
        resources: List[str] = None,
        profile: str = None,
        all_accounts: bool = False,
        include_costs: bool = False,
        regions: List[str] = None,
    ) -> pd.DataFrame:
        """
        Collect inventory across AWS accounts and services.

        Args:
            resources: List of AWS resources (ec2, s3, rds, lambda, etc.)
            profile: AWS profile to use
            all_accounts: Scan all accounts in organization
            include_costs: Include cost analysis
            regions: Specific regions to scan

        Returns:
            DataFrame with inventory results
        """
        cmd_parts = ["runbooks", "inventory", "collect"]

        if resources:
            cmd_parts.extend(["-r", ",".join(resources)])
        if profile or self.default_profile:
            cmd_parts.extend(["--profile", profile or self.default_profile])
        if all_accounts:
            cmd_parts.append("--all-profiles")
        if include_costs:
            cmd_parts.append("--include-costs")
        if regions:
            cmd_parts.extend(["--regions", ",".join(regions)])

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            try:
                # Parse JSON output to DataFrame
                data = json.loads(result["stdout"])
                df = pd.DataFrame(data.get("resources", []))
                self._display_inventory_summary(df)
                return df
            except json.JSONDecodeError:
                console.print("[yellow]Warning: Could not parse JSON output, returning raw text[/yellow]")
                return pd.DataFrame({"output": [result["stdout"]]})
        else:
            console.print(
                f"[red]Error executing inventory command: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]"
            )
            return pd.DataFrame()

    # FinOps Operations
    def finops_analyze(
        self,
        profile: str = None,
        all_accounts: bool = False,
        target_reduction: str = "20-40%",
        breakdown_by: List[str] = None,
        export_format: str = "json",
    ) -> Dict[str, Any]:
        """
        Perform FinOps cost analysis and optimization recommendations.

        Args:
            profile: AWS billing profile
            all_accounts: Analyze all accounts
            target_reduction: Target cost reduction percentage
            breakdown_by: Breakdown by service, account, region
            export_format: Export format (json, csv, html)

        Returns:
            Dictionary with cost analysis results
        """
        cmd_parts = ["runbooks", "finops", "--analyze"]

        if profile or self.default_profile:
            cmd_parts.extend(["--profile", profile or self.default_profile])
        if all_accounts:
            cmd_parts.append("--all-profiles")
        if target_reduction:
            cmd_parts.extend(["--target-reduction", target_reduction])
        if breakdown_by:
            cmd_parts.extend(["--breakdown-by", ",".join(breakdown_by)])
        if export_format:
            cmd_parts.extend(["--export", export_format])

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                self._display_finops_summary(data)
                return data
            except json.JSONDecodeError:
                console.print("[yellow]Warning: Could not parse JSON output[/yellow]")
                return {"raw_output": result["stdout"]}
        else:
            console.print(
                f"[red]Error executing FinOps analysis: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]"
            )
            return {}

    # Security Operations
    def security_assess(
        self,
        profile: str = None,
        all_accounts: bool = False,
        checks: str = "all",
        language: str = "EN",
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Perform security assessment across accounts.

        Args:
            profile: AWS profile to use
            all_accounts: Assess all accounts
            checks: Specific security checks or "all"
            language: Report language (EN, JP, KR, VN)
            format: Output format (json, html, csv)

        Returns:
            Dictionary with security assessment results
        """
        cmd_parts = ["runbooks", "security", "assess"]

        if profile or self.default_profile:
            cmd_parts.extend(["--profile", profile or self.default_profile])
        if all_accounts:
            cmd_parts.append("--all-profiles")
        if checks:
            cmd_parts.extend(["--checks", checks])
        if language:
            cmd_parts.extend(["--language", language])
        if format:
            cmd_parts.extend(["--format", format])

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                self._display_security_summary(data)
                return data
            except json.JSONDecodeError:
                return {"raw_output": result["stdout"]}
        else:
            console.print(
                f"[red]Error executing security assessment: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]"
            )
            return {}

    # CFAT Operations
    def cfat_assess(
        self,
        profile: str = None,
        compliance_framework: str = "AWS Well-Architected",
        output_format: str = "json",
        serve_web: bool = False,
        port: int = 8080,
    ) -> Dict[str, Any]:
        """
        Perform Cloud Foundation Assessment Tool evaluation.

        Args:
            profile: AWS profile to use
            compliance_framework: Framework to assess against
            output_format: Output format
            serve_web: Start web server for results
            port: Web server port

        Returns:
            Dictionary with CFAT assessment results
        """
        cmd_parts = ["runbooks", "cfat", "assess"]

        if profile or self.default_profile:
            cmd_parts.extend(["--profile", profile or self.default_profile])
        if compliance_framework:
            cmd_parts.extend(["--compliance-framework", f'"{compliance_framework}"'])
        if output_format:
            cmd_parts.extend(["--output", output_format])
        if serve_web:
            cmd_parts.extend(["--serve-web", "--port", str(port)])

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                self._display_cfat_summary(data)
                return data
            except json.JSONDecodeError:
                return {"raw_output": result["stdout"]}
        else:
            console.print(
                f"[red]Error executing CFAT assessment: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]"
            )
            return {}

    # Operations
    def operate_ec2(
        self, action: str, instance_ids: List[str], profile: str = None, dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Perform EC2 operations (start, stop, terminate).

        Args:
            action: Action to perform (start, stop, terminate)
            instance_ids: List of instance IDs
            profile: AWS profile to use
            dry_run: Perform dry run only

        Returns:
            Dictionary with operation results
        """
        cmd_parts = ["runbooks", "operate", "ec2", action]
        cmd_parts.extend(["--instance-ids"] + instance_ids)

        if profile or self.default_profile:
            cmd_parts.extend(["--profile", profile or self.default_profile])
        if dry_run:
            cmd_parts.append("--dry-run")

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            console.print(f"[green]✅ EC2 {action} operation completed successfully[/green]")
            return {"success": True, "output": result["stdout"]}
        else:
            console.print(
                f"[red]❌ EC2 {action} operation failed: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]"
            )
            return {"success": False, "error": result.get("error", result.get("stderr"))}

    # Organization Management
    def org_list_ous(self, profile: str = None, output_format: str = "table") -> pd.DataFrame:
        """
        List organizational units in AWS Organizations.

        Args:
            profile: AWS management profile
            output_format: Output format (table, json)

        Returns:
            DataFrame with OU information
        """
        cmd_parts = ["runbooks", "org", "list-ous"]

        if profile or self.default_profile:
            cmd_parts.extend(["--profile", profile or self.default_profile])
        if output_format:
            cmd_parts.extend(["--output", output_format])

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            try:
                if output_format == "json":
                    data = json.loads(result["stdout"])
                    df = pd.DataFrame(data.get("organizational_units", []))
                else:
                    # Parse table output
                    df = pd.DataFrame({"output": [result["stdout"]]})
                return df
            except json.JSONDecodeError:
                return pd.DataFrame({"output": [result["stdout"]]})
        else:
            console.print(f"[red]Error listing OUs: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]")
            return pd.DataFrame()

    # MCP Validation
    def validate_mcp_servers(self, billing_profile: str = None) -> Dict[str, Any]:
        """
        Validate MCP servers connectivity and accuracy.

        Args:
            billing_profile: Billing profile for validation

        Returns:
            Dictionary with validation results
        """
        cmd_parts = ["runbooks", "validate", "mcp-servers"]

        if billing_profile or self.default_profile:
            cmd_parts.extend(["--billing-profile", billing_profile or self.default_profile])

        command = " ".join(cmd_parts)
        result = self._execute_command(command)

        if result["success"]:
            try:
                data = json.loads(result["stdout"])
                self._display_mcp_validation_summary(data)
                return data
            except json.JSONDecodeError:
                return {"raw_output": result["stdout"]}
        else:
            console.print(
                f"[red]Error validating MCP servers: {result.get('error', result.get('stderr', 'Unknown error'))}[/red]"
            )
            return {}

    # Rich Display Methods
    def _display_inventory_summary(self, df: pd.DataFrame):
        """Display inventory results summary with Rich formatting."""
        if df.empty:
            console.print("[yellow]No inventory data to display[/yellow]")
            return

        table = Table(title="📊 Inventory Summary", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Count", justify="right", style="green")

        total_resources = len(df)
        resource_types = df.get("ResourceType", pd.Series()).nunique() if "ResourceType" in df.columns else 0
        accounts = df.get("AccountId", pd.Series()).nunique() if "AccountId" in df.columns else 0

        table.add_row("Total Resources", str(total_resources))
        table.add_row("Resource Types", str(resource_types))
        table.add_row("AWS Accounts", str(accounts))

        console.print(table)

    def _display_finops_summary(self, data: Dict[str, Any]):
        """Display FinOps analysis summary with Rich formatting."""
        panel_content = []

        if "total_cost" in data:
            panel_content.append(f"💰 Total Monthly Cost: ${data['total_cost']:,.2f}")
        if "potential_savings" in data:
            panel_content.append(f"💸 Potential Savings: ${data['potential_savings']:,.2f}")
        if "optimization_recommendations" in data:
            panel_content.append(f"📋 Recommendations: {len(data['optimization_recommendations'])}")

        content = "\n".join(panel_content) if panel_content else "FinOps analysis completed"

        console.print(Panel(content, title="💰 FinOps Analysis Summary", border_style="green"))

    def _display_security_summary(self, data: Dict[str, Any]):
        """Display security assessment summary with Rich formatting."""
        panel_content = []

        if "total_checks" in data:
            panel_content.append(f"🔍 Total Checks: {data['total_checks']}")
        if "passed_checks" in data:
            panel_content.append(f"✅ Passed: {data['passed_checks']}")
        if "failed_checks" in data:
            panel_content.append(f"❌ Failed: {data['failed_checks']}")
        if "compliance_score" in data:
            panel_content.append(f"📊 Compliance Score: {data['compliance_score']}%")

        content = "\n".join(panel_content) if panel_content else "Security assessment completed"

        console.print(Panel(content, title="🔒 Security Assessment Summary", border_style="red"))

    def _display_cfat_summary(self, data: Dict[str, Any]):
        """Display CFAT assessment summary with Rich formatting."""
        panel_content = []

        if "well_architected_score" in data:
            panel_content.append(f"🏗️ Well-Architected Score: {data['well_architected_score']}%")
        if "pillars_assessed" in data:
            panel_content.append(f"📋 Pillars Assessed: {len(data['pillars_assessed'])}")
        if "high_risk_findings" in data:
            panel_content.append(f"⚠️ High Risk Findings: {data['high_risk_findings']}")

        content = "\n".join(panel_content) if panel_content else "CFAT assessment completed"

        console.print(Panel(content, title="🏗️ CFAT Assessment Summary", border_style="blue"))

    def _display_mcp_validation_summary(self, data: Dict[str, Any]):
        """Display MCP validation summary with Rich formatting."""
        panel_content = []

        if "accuracy_rate" in data:
            panel_content.append(f"🎯 Accuracy Rate: {data['accuracy_rate']}%")
        if "servers_validated" in data:
            panel_content.append(f"🖥️ Servers Validated: {data['servers_validated']}")
        if "validation_time" in data:
            panel_content.append(f"⏱️ Validation Time: {data['validation_time']}s")

        content = "\n".join(panel_content) if panel_content else "MCP validation completed"

        color = "green" if data.get("accuracy_rate", 0) >= 99.5 else "yellow"

        console.print(Panel(content, title="🔍 MCP Validation Summary", border_style=color))
