"""
Cleanup Script Generator Pattern.

Dual-format cleanup script generator (bash + boto3).
Generates per-account scripts with DryRun safety by default.

Pattern extracted from: vpce_cleanup_manager.py (generate_cleanup_scripts, generate_boto3_cleanup_script)
Reusable for: All AWS resource cleanup operations (VPCs, ENIs, NAT Gateways, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from runbooks.common.rich_utils import print_success, print_info, print_warning


@dataclass
class ScriptGenerationResult:
    """Cleanup script generation result."""

    bash_scripts: List[str]
    boto3_scripts: List[str]
    master_script: str
    file_count: int
    resource_count: int
    dry_run_enabled: bool


class CleanupScriptGenerator(ABC):
    """
    Dual-format cleanup script generator (bash + boto3).

    Generates:
    - Per-account bash scripts (AWS CLI commands)
    - Per-account boto3 Python scripts (with Rich progress)
    - Master orchestration script

    Safety: DryRun=True by default

    Usage:
        class MyManager(CleanupScriptGenerator):
            def _get_resources_for_cleanup(self):
                return [{"id": "vpc-xxx", "account": "123", "profile": "p1"}, ...]

        manager = MyManager()
        result = manager.generate_scripts(
            output_dir=Path("data/scripts"),
            dry_run=True,  # Safety: DryRun enabled
            formats=["bash", "boto3"]
        )

    Pattern Benefits:
    - Dual-format support (bash + boto3)
    - DryRun safety (True by default)
    - Per-account grouping
    - Rich CLI progress bars (boto3 scripts)
    - Master orchestration script
    - Executable permissions set (chmod 755)
    """

    @abstractmethod
    def _get_resources_for_cleanup(self) -> List[Dict]:
        """
        Return resources to include in cleanup scripts.

        Returns:
            List of dicts with keys:
                - id: Resource ID
                - account_id: AWS account ID
                - profile: AWS profile name
                - type: Resource type (for script comments, optional)
                - region: AWS region (optional, defaults to ap-southeast-2)
        """
        pass

    def generate_scripts(
        self,
        output_dir: Path,
        dry_run: bool = True,
        formats: List[str] = None,
        resource_type: str = "vpc-endpoint",
        delete_command: str = "delete-vpc-endpoints",
        id_param: str = "vpc-endpoint-ids",
        region: str = "ap-southeast-2",
    ) -> ScriptGenerationResult:
        """
        Generate cleanup scripts in specified formats.

        Args:
            output_dir: Directory to write scripts
            dry_run: Generate with DryRun=True (default: True for safety)
            formats: Script formats to generate (default: ["bash", "boto3"])
            resource_type: Resource type for script comments
            delete_command: AWS CLI delete command
            id_param: AWS CLI parameter name for resource IDs
            region: AWS region for operations

        Returns:
            ScriptGenerationResult with generated file paths
        """
        if formats is None:
            formats = ["bash", "boto3"]

        output_dir.mkdir(parents=True, exist_ok=True)
        resources = self._get_resources_for_cleanup()

        if not resources:
            print_warning("⚠️  No resources to generate cleanup scripts for")
            return ScriptGenerationResult(
                bash_scripts=[],
                boto3_scripts=[],
                master_script="",
                file_count=0,
                resource_count=0,
                dry_run_enabled=dry_run,
            )

        # Group resources by account
        by_account = {}
        for resource in resources:
            account_id = resource.get("account_id", "unknown")
            if account_id not in by_account:
                by_account[account_id] = []
            by_account[account_id].append(resource)

        bash_scripts = []
        boto3_scripts = []

        print_info(
            f"🔍 Generating cleanup scripts for {len(resources)} {resource_type}s across {len(by_account)} accounts..."
        )

        # Generate per-account scripts
        for account_id, account_resources in by_account.items():
            if "bash" in formats:
                bash_path = self._generate_bash_script(
                    account_id, account_resources, output_dir, dry_run, delete_command, id_param, region
                )
                bash_scripts.append(str(bash_path))

            if "boto3" in formats:
                boto3_path = self._generate_boto3_script(account_id, account_resources, output_dir, dry_run, region)
                boto3_scripts.append(str(boto3_path))

        # Generate master orchestration script
        master_path = self._generate_master_script(bash_scripts, output_dir)

        print_success(f"✅ Generated {len(bash_scripts)} bash + {len(boto3_scripts)} boto3 scripts")
        print_info(f"📊 DryRun: {'ENABLED' if dry_run else 'DISABLED'} (change to False for actual deletion)")

        return ScriptGenerationResult(
            bash_scripts=bash_scripts,
            boto3_scripts=boto3_scripts,
            master_script=str(master_path),
            file_count=len(bash_scripts) + len(boto3_scripts) + 1,
            resource_count=len(resources),
            dry_run_enabled=dry_run,
        )

    def _generate_bash_script(
        self,
        account_id: str,
        resources: List[Dict],
        output_dir: Path,
        dry_run: bool,
        delete_command: str,
        id_param: str,
        region: str,
    ) -> Path:
        """Generate bash script for account."""
        script_path = output_dir / f"cleanup-{account_id}.sh"
        dry_run_flag = "--dry-run" if dry_run else ""
        profile = resources[0].get("profile", "default") if resources else "default"

        lines = [
            "#!/bin/bash",
            f"# Cleanup script for account {account_id}",
            f"# Profile: {profile}",
            f"# DryRun: {dry_run}",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Total resources: {len(resources)}",
            "",
            "set -e  # Exit on error",
            "",
        ]

        for resource in resources:
            resource_id = resource.get("id")
            resource_region = resource.get("region", region)
            lines.append(f"# Delete: {resource_id}")
            lines.append(
                f"aws ec2 {delete_command} --{id_param} {resource_id} --region {resource_region} --profile {profile} {dry_run_flag}"
            )
            lines.append("")

        lines.append("echo '✅ Cleanup script completed'")

        script_path.write_text("\n".join(lines))
        script_path.chmod(0o755)
        return script_path

    def _generate_boto3_script(
        self, account_id: str, resources: List[Dict], output_dir: Path, dry_run: bool, region: str
    ) -> Path:
        """Generate boto3 Python script with Rich progress."""
        script_path = output_dir / f"cleanup-{account_id}.py"
        resource_ids = [r.get("id") for r in resources]
        profile = resources[0].get("profile", "default") if resources else "default"

        script = f'''#!/usr/bin/env python3
"""
Cleanup script for account {account_id}
Profile: {profile}
DryRun: {dry_run}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Total resources: {len(resources)}
"""
import boto3
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def delete_resources(dry_run={dry_run}):
    """Delete resources with Rich CLI progress."""
    resource_ids = {resource_ids}

    session = boto3.Session(profile_name="{profile}")
    ec2 = session.client('ec2', region_name='{region}')

    console.print(f"[bold cyan]Starting cleanup for account {account_id}[/bold cyan]")
    console.print(f"DryRun: {dry_run}")
    console.print(f"Resources to delete: {{len(resource_ids)}}")
    console.print("")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{{task.description}}"), console=console) as progress:
        task = progress.add_task(f"Deleting {{len(resource_ids)}} resources...", total=len(resource_ids))

        deleted = 0
        failed = 0

        for resource_id in resource_ids:
            try:
                console.print(f"[yellow]Deleting: {{resource_id}}[/yellow]")
                ec2.delete_vpc_endpoints(VpcEndpointIds=[resource_id], DryRun=dry_run)
                console.print(f"[green]✅ Deleted: {{resource_id}}[/green]")
                deleted += 1
            except Exception as e:
                console.print(f"[red]❌ Failed {{resource_id}}: {{e}}[/red]")
                failed += 1

            progress.advance(task)

    console.print("")
    console.print(f"[bold green]✅ Cleanup complete[/bold green]")
    console.print(f"Deleted: {{deleted}}")
    console.print(f"Failed: {{failed}}")

if __name__ == "__main__":
    delete_resources()
'''
        script_path.write_text(script)
        script_path.chmod(0o755)
        return script_path

    def _generate_master_script(self, bash_scripts: List[str], output_dir: Path) -> Path:
        """Generate master orchestration script."""
        master_path = output_dir / "cleanup-all-accounts.sh"

        lines = [
            "#!/bin/bash",
            "# Master cleanup script - Executes all account-specific scripts",
            f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# Total scripts: {len(bash_scripts)}",
            "",
            "set -e",
            "",
        ]

        for script in bash_scripts:
            lines.append(f"echo 'Executing: {script}'")
            lines.append(f"bash {script}")
            lines.append("")

        lines.append("echo '✅ All cleanup scripts executed'")

        master_path.write_text("\n".join(lines))
        master_path.chmod(0o755)
        return master_path
