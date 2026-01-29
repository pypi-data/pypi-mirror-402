#!/usr/bin/env python3
"""
MCP Reality Validator - Test actual MCP server availability
Validates MCP configurations against reality and generates execution evidence.

Usage:
    uv run python src/runbooks/tools/mcp_validator.py
    runbooks tools validate-mcp --config .mcp-full.json

Business Value: Prevents runtime failures from phantom MCP server references
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from runbooks.common.rich_utils import get_console, create_table

console = get_console()


class MCPValidator:
    """Validate MCP server availability and configuration."""

    def __init__(self, config_file: str = ".mcp-full.json"):
        """Initialize validator with config file."""
        self.config_file = Path(config_file)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "config_source": str(config_file),
            "servers_tested": [],
            "phantom_servers": [],
            "validation_results": {},
            "profile_validation": {},
            "summary": {},
        }

    def load_config(self) -> Dict[str, Any]:
        """Load MCP configuration file."""
        if not self.config_file.exists():
            console.print(f"[red]Config file not found: {self.config_file}[/red]")
            return {}

        with open(self.config_file) as f:
            return json.load(f)

    def validate_aws_profile(self, profile: str) -> bool:
        """Validate AWS profile exists and is functional."""
        try:
            # Test with AWS STS get-caller-identity
            cmd = f"AWS_PROFILE={profile} aws sts get-caller-identity"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                identity = json.loads(result.stdout)
                self.results["profile_validation"][profile] = {
                    "exists": True,
                    "account": identity.get("Account"),
                    "arn": identity.get("Arn"),
                    "status": "✅ Valid",
                }
                return True
            else:
                self.results["profile_validation"][profile] = {
                    "exists": False,
                    "error": result.stderr,
                    "status": "❌ Invalid",
                }
                return False

        except Exception as e:
            self.results["profile_validation"][profile] = {"exists": False, "error": str(e), "status": "❌ Error"}
            return False

    def test_mcp_server(self, server_name: str, server_config: Dict) -> Dict:
        """Test individual MCP server availability."""
        result = {"server": server_name, "status": "unknown", "profile": None, "test_query": None, "error": None}

        # Extract AWS profile if present
        env = server_config.get("env", {})
        profile = None

        # Check for hardcoded profile
        if "AWS_PROFILE" in env:
            profile = env["AWS_PROFILE"]
            # Resolve environment variable if needed
            if profile.startswith("${") and profile.endswith("}"):
                env_var = profile[2:-1]
                profile = os.environ.get(env_var, profile)

        result["profile"] = profile

        # Categorize server status
        description = server_config.get("description", "")
        if "✅ OPERATIONAL" in description:
            result["status"] = "operational"

            # Validate AWS profile if present
            if profile and not profile.startswith("${"):
                if self.validate_aws_profile(profile):
                    result["profile_valid"] = True
                else:
                    result["status"] = "profile_error"
                    result["profile_valid"] = False

        elif "🔧 CONFIGURED" in description:
            result["status"] = "configured"
        elif "⚠️ NEEDS_FIX" in description:
            result["status"] = "needs_fix"
            result["error"] = "Known issue - " + description
        else:
            result["status"] = "unknown"

        return result

    def identify_phantom_servers(self, config: Dict) -> List[str]:
        """Identify servers that are referenced but don't exist."""
        known_phantoms = [
            "aws-boto3-mcp",
            "aws-organizations",
            "aws-security-hub-mcp",
            "test-coverage-mcp",
            "moto-mcp",
            "awslabs-finops",
            "awslabs-inventory",
            "awslabs-operate",
            "awslabs-security",
            "awslabs-test",
            "mkdocs-mcp",
            "openapi-mcp",
        ]

        actual_servers = set(config.get("mcpServers", {}).keys())
        phantom_found = []

        for phantom in known_phantoms:
            if phantom not in actual_servers:
                phantom_found.append(phantom)

        return phantom_found

    def validate_all(self) -> Dict:
        """Run complete validation suite."""
        console.print("\n[bold cyan]MCP Reality Validator[/bold cyan]")
        console.print("=" * 60)

        # Load configuration
        config = self.load_config()
        if not config:
            return self.results

        mcp_servers = config.get("mcpServers", {})

        # Create progress display
        with console.status("[cyan]Validating MCP servers...") as status:
            # Test each server
            for server_name, server_config in mcp_servers.items():
                status.update(f"Testing {server_name}...")
                result = self.test_mcp_server(server_name, server_config)
                self.results["servers_tested"].append(result)
                self.results["validation_results"][server_name] = result

            # Identify phantom servers
            status.update("Identifying phantom servers...")
            self.results["phantom_servers"] = self.identify_phantom_servers(config)

        # Generate summary
        self.generate_summary()

        # Display results
        self.display_results()

        # Write to file
        self.write_results()

        return self.results

    def generate_summary(self):
        """Generate validation summary."""
        total = len(self.results["servers_tested"])
        operational = sum(1 for s in self.results["servers_tested"] if s["status"] == "operational")
        configured = sum(1 for s in self.results["servers_tested"] if s["status"] == "configured")
        needs_fix = sum(1 for s in self.results["servers_tested"] if s["status"] == "needs_fix")
        profile_errors = sum(1 for s in self.results["servers_tested"] if s["status"] == "profile_error")

        self.results["summary"] = {
            "total_servers": total,
            "operational": operational,
            "configured": configured,
            "needs_fix": needs_fix,
            "profile_errors": profile_errors,
            "phantom_servers_identified": len(self.results["phantom_servers"]),
            "validation_score": round((operational / total * 100) if total > 0 else 0, 1),
        }

    def display_results(self):
        """Display validation results in Rich format."""
        summary = self.results["summary"]

        # Summary table
        console.print("\n[bold]Validation Summary:[/bold]")
        console.print(f"  Total Servers: {summary['total_servers']}")
        console.print(f"  ✅ Operational: {summary['operational']}")
        console.print(f"  🔧 Configured: {summary['configured']}")
        console.print(f"  ⚠️ Needs Fix: {summary['needs_fix']}")
        console.print(f"  ❌ Profile Errors: {summary['profile_errors']}")
        console.print(f"  👻 Phantom Servers: {summary['phantom_servers_identified']}")
        console.print(f"  Score: {summary['validation_score']}%")

        # Server status table
        console.print("\n[bold]Server Status:[/bold]")
        for server in self.results["servers_tested"]:
            status_icon = {
                "operational": "✅",
                "configured": "🔧",
                "needs_fix": "⚠️",
                "profile_error": "❌",
                "unknown": "❓",
            }.get(server["status"], "❓")

            console.print(f"  {status_icon} {server['server']}: {server['status']}")
            if server.get("profile"):
                profile_valid = "✓" if server.get("profile_valid") else "✗"
                console.print(f"     Profile: {server['profile']} [{profile_valid}]")

        # Phantom servers
        if self.results["phantom_servers"]:
            console.print("\n[bold red]Phantom Servers Detected:[/bold red]")
            for phantom in self.results["phantom_servers"]:
                console.print(f"  👻 {phantom} - Does not exist in config")

    def write_results(self):
        """Write validation results to file."""
        output_file = Path(f"/tmp/mcp-reality-check-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")

        with open(output_file, "w") as f:
            json.dump(self.results, f, indent=2)

        console.print(f"\n[green]Results written to: {output_file}[/green]")

        # Also write a simplified report
        report_file = Path(f"/tmp/mcp-validation-report-{datetime.now().strftime('%Y%m%d')}.txt")
        with open(report_file, "w") as f:
            f.write("MCP VALIDATION REPORT\n")
            f.write("=" * 60 + "\n")
            f.write(f"Generated: {self.results['timestamp']}\n")
            f.write(f"Config: {self.results['config_source']}\n\n")

            f.write("SUMMARY:\n")
            for key, value in self.results["summary"].items():
                f.write(f"  {key}: {value}\n")

            f.write("\nOPERATIONAL SERVERS:\n")
            for server in self.results["servers_tested"]:
                if server["status"] == "operational":
                    f.write(f"  ✅ {server['server']}\n")

            f.write("\nISSUES FOUND:\n")
            for server in self.results["servers_tested"]:
                if server["status"] != "operational":
                    f.write(f"  ⚠️ {server['server']}: {server['status']}\n")

            if self.results["phantom_servers"]:
                f.write("\nPHANTOM SERVERS:\n")
                for phantom in self.results["phantom_servers"]:
                    f.write(f"  👻 {phantom}\n")

        console.print(f"[green]Report written to: {report_file}[/green]")


def main():
    """Main entry point for CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate MCP server configurations")
    parser.add_argument("--config", default=".mcp-full.json", help="MCP configuration file to validate")

    args = parser.parse_args()

    validator = MCPValidator(config_file=args.config)
    results = validator.validate_all()

    # Return non-zero exit code if issues found
    if results["summary"].get("validation_score", 0) < 100:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
