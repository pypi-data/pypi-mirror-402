"""
VPC Commands Module - Network Operations & Cost Optimization

KISS Principle: Focused on VPC networking operations and cost optimization
DRY Principle: Centralized networking patterns and cost analysis

Extracted from main.py lines 7500-9000 for modular architecture.
Preserves 100% functionality while reducing main.py context overhead.
"""

import click
import os

# Import common utilities and decorators
from runbooks.common.decorators import common_aws_options, common_output_options
from runbooks.common.rich_utils import Console

console = Console()


def create_vpc_group():
    """
    Create the vpc command group with all subcommands.

    Returns:
        Click Group object with all vpc commands

    Performance: Lazy creation only when needed by DRYCommandRegistry
    Context Reduction: ~1500 lines extracted from main.py
    """

    # Custom Group class with Rich Tree/Table help formatting
    class RichVPCGroup(click.Group):
        """Custom Click Group with Rich Tree/Table help display."""

        def format_help(self, ctx, formatter):
            """Format help text with Rich Tree/Table categorization."""
            from rich.tree import Tree
            from rich.table import Table as RichTable

            # Check for TEST_MODE environment variable for backward compatibility
            test_mode = os.environ.get("RUNBOOKS_TEST_MODE", "0") == "1"

            if test_mode:
                # Plain text fallback for testing
                click.echo("Usage: runbooks vpc [OPTIONS] COMMAND [ARGS]...")
                click.echo("")
                click.echo("  VPC networking operations and cost optimization.")
                click.echo("")
                click.echo("Commands:")
                click.echo("  analyze                    Comprehensive VPC analysis")
                click.echo("  nat-gateway                NAT Gateway cost optimization")
                click.echo("  topology                   Network topology generation")
                click.echo("  network-discover           Multi-account network discovery")
                click.echo("  discover-firewall-bypass   Firewall bypass detection")
                click.echo("  vpce-cleanup               VPC Endpoint cleanup")
                return

            # Categorize commands based on business function
            categories = {
                "📊 Network Analysis": [
                    ("analyze", "Comprehensive VPC analysis with cost optimization"),
                    ("topology", "Network topology discovery and visualization"),
                    ("network-discover", "Multi-account network discovery with diagrams"),
                    ("discover-firewall-bypass", "Security group firewall bypass detection"),
                ],
                "💰 Cost Optimization": [
                    ("nat-gateway", "NAT Gateway cost optimization (Epic 2 target)"),
                    ("vpce-cleanup", "VPC Endpoint cleanup and cost reduction"),
                ],
            }

            # Phase 1: Pre-calculate max column widths across ALL categories
            max_cmd_len = 0
            for category_commands in categories.values():
                for cmd, desc in category_commands:
                    max_cmd_len = max(max_cmd_len, len(cmd))

            # Set command column width with padding
            cmd_width = max_cmd_len + 2

            # Create Rich Tree
            tree = Tree("[bold cyan]VPC Commands[/bold cyan] (5 commands)")

            # Add each category with fixed-width tables
            for category_name, commands in categories.items():
                category_branch = tree.add(
                    f"[bold green]{category_name}[/bold green] [dim]({len(commands)} commands)[/dim]"
                )

                # Create table with FIXED command width for vertical alignment, flexible description
                table = RichTable(show_header=True, box=None, padding=(0, 2))
                table.add_column("Command", style="cyan", no_wrap=True, min_width=cmd_width, max_width=cmd_width)
                table.add_column("Description", style="dim", no_wrap=False, overflow="fold")

                # Add rows
                for cmd, desc in commands:
                    table.add_row(cmd, desc)

                category_branch.add(table)

            # Display the tree
            console.print(tree)
            console.print("\n[blue]💡 Usage: runbooks vpc [COMMAND] [OPTIONS][/blue]")
            console.print(
                "[blue]📖 Example: runbooks vpc analyze --profile ops-profile --output /tmp/vpc-analysis.csv[/blue]\n"
            )

    @click.group(cls=RichVPCGroup, invoke_without_command=True)
    @common_aws_options
    @click.pass_context
    def vpc(ctx, profile, region, dry_run):
        """
        VPC networking operations and cost optimization.

        Comprehensive VPC analysis, network cost optimization, and topology
        management with enterprise-grade safety and reporting capabilities.

        Network Operations:
        • VPC cost analysis and optimization recommendations
        • NAT Gateway rightsizing and cost reduction
        • Network topology analysis and security assessment
        • Multi-account network discovery and management

        Examples:
            runbooks vpc analyze --cost-optimization
            runbooks vpc nat-gateway --analyze --savings-target 0.3
            runbooks vpc topology --export-format pdf
        """
        ctx.obj.update({"profile": profile, "region": region, "dry_run": dry_run})

        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())

    @vpc.command()
    @common_aws_options
    @common_output_options
    @click.option("--cost-optimization", is_flag=True, help="Include cost optimization analysis")
    @click.option("--topology-analysis", is_flag=True, help="Include network topology analysis")
    @click.option("--security-assessment", is_flag=True, help="Include security configuration review")
    @click.option(
        "--savings-target",
        type=click.FloatRange(0.1, 0.8),
        default=0.3,
        help="Target savings percentage for optimization",
    )
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account VPC analysis")
    @click.option(
        "--config",
        type=click.Path(exists=True),
        help="Path to YAML campaign configuration file (config-driven analysis)",
    )
    @click.pass_context
    def analyze(
        ctx,
        profile,
        region,
        dry_run,
        output_format,
        output_file,
        cost_optimization,
        topology_analysis,
        security_assessment,
        savings_target,
        all,
        config,
    ):
        """
        Comprehensive VPC network analysis with cost optimization.

        \b
        🔍 ANALYSIS DIMENSIONS
        ├── 🌐 Network Architecture
        │   └── VPC configuration, subnets, route tables, NACLs
        ├── 💰 Cost Optimization
        │   └── NAT Gateways, VPC Endpoints, unused ENIs
        ├── 🔒 Security Posture
        │   └── Security groups, firewall bypass, public exposure
        └── 📊 Utilization Metrics
            └── Traffic patterns, bandwidth, connection tracking

        💡 Epic 2 Focus: NAT Gateway optimization (25-50% network cost savings)
        📖 Example: runbooks vpc analyze --profile ops --output /tmp/vpc-analysis.csv
        """
        try:
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import handle_output_format

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            # NEW: Config-driven campaign analysis
            if config:
                from runbooks.vpc import VPCCleanupFramework
                from runbooks.vpc.cleanup_wrapper import display_config_campaign_results

                cleanup_framework = VPCCleanupFramework(profile=resolved_profile, region=region, safety_mode=True)

                results = cleanup_framework.analyze_from_config(config)
                display_config_campaign_results(results)

                # Export if requested
                if output_file:
                    handle_output_format(
                        data=results,
                        output_format=output_format,
                        output_file=output_file,
                        title=f"Campaign {results.get('campaign_metadata', {}).get('campaign_id', 'Unknown')} Results",
                    )

                return results

            # EXISTING: Standard VPC analysis (unchanged)
            from runbooks.vpc.analyzer import VPCAnalyzer

            analyzer = VPCAnalyzer(
                profile=resolved_profile,
                region=region,
                cost_optimization=cost_optimization,
                topology_analysis=topology_analysis,
                security_assessment=security_assessment,
                savings_target=savings_target,
            )

            analysis_results = analyzer.run_comprehensive_analysis()

            # Use unified format handling
            handle_output_format(
                data=analysis_results,
                output_format=output_format,
                output_file=output_file,
                title="VPC Analysis Results",
            )

            return analysis_results

        except ImportError as e:
            console.print(f"[red]❌ VPC analyzer module not available: {e}[/red]")
            raise click.ClickException("VPC analysis functionality not available")
        except Exception as e:
            console.print(f"[red]❌ VPC analysis failed: {e}[/red]")
            raise click.ClickException(str(e))

    @vpc.command("nat-gateway")
    @common_aws_options
    @common_output_options
    @click.option("--analyze", is_flag=True, help="Analyze NAT Gateway usage and costs")
    @click.option("--optimize", is_flag=True, help="Generate optimization recommendations")
    @click.option("--savings-target", type=click.FloatRange(0.1, 0.8), default=0.3, help="Target savings percentage")
    @click.option("--include-alternatives", is_flag=True, help="Include NAT instance alternatives")
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account NAT Gateway analysis")
    @click.pass_context
    def nat_gateway_operations(
        ctx,
        profile,
        region,
        dry_run,
        output_format,
        output_file,
        analyze,
        optimize,
        savings_target,
        include_alternatives,
        all,
    ):
        """
        NAT Gateway cost optimization and rightsizing analysis.

        \b
        🎯 EPIC 2: NAT GATEWAY OPTIMIZATION TARGETS
        ┌────────────────────────────────────────────┐
        │ Cost Reduction: 25-50% network savings     │
        │ Utilization Target: >70% bandwidth usage   │
        │ Consolidation: Multi-AZ → Single-AZ        │
        │ Replacement: NAT Gateway → NAT Instance    │
        └────────────────────────────────────────────┘

        \b
        🔄 Analysis Workflow:
        1. Discover all NAT Gateways across VPCs
        2. Analyze CloudWatch metrics (bandwidth, connections)
        3. Calculate cost per GB transferred
        4. Identify consolidation opportunities
        5. Generate rightsizing recommendations

        💰 Typical Savings: $500-2000/month per optimized NAT Gateway
        📖 Example: runbooks vpc nat-gateway --profile ops --output /tmp/nat-optimization.csv
        """
        try:
            from runbooks.vpc.nat_gateway_optimizer import NATGatewayOptimizer
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import handle_output_format

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            optimizer = NATGatewayOptimizer(
                profile=resolved_profile,
                region=region,
                analyze=analyze,
                optimize=optimize,
                savings_target=savings_target,
                include_alternatives=include_alternatives,
            )

            optimization_results = optimizer.run_nat_gateway_optimization()

            # Use unified format handling
            handle_output_format(
                data=optimization_results,
                output_format=output_format,
                output_file=output_file,
                title="NAT Gateway Optimization Results",
            )

            return optimization_results

        except ImportError as e:
            console.print(f"[red]❌ NAT Gateway optimizer module not available: {e}[/red]")
            raise click.ClickException("NAT Gateway optimization functionality not available")
        except Exception as e:
            console.print(f"[red]❌ NAT Gateway optimization failed: {e}[/red]")
            raise click.ClickException(str(e))

    @vpc.command()
    @common_aws_options
    @common_output_options
    @click.option("--include-costs", is_flag=True, help="Include cost analysis in topology")
    @click.option(
        "--detail-level",
        type=click.Choice(["basic", "detailed", "comprehensive"]),
        default="detailed",
        help="Topology detail level",
    )
    @click.option("--output-dir", default="./vpc_topology", help="Output directory")
    @click.option("--all", is_flag=True, help="Use all available AWS profiles for multi-account topology generation")
    @click.pass_context
    def topology(
        ctx, profile, region, dry_run, output_format, output_file, include_costs, detail_level, output_dir, all
    ):
        """
        Generate network topology diagrams with cost correlation and universal profile support.

        Topology Analysis Features:
        • Visual network topology with cost overlay
        • Security group and routing visualization
        • Multi-account network relationships
        • Cost flow analysis and optimization opportunities
        • Cross-account topology generation with --all flag

        Examples:
            runbooks vpc topology --include-costs --export-format pdf
            runbooks vpc topology --detail-level comprehensive
            runbooks vpc topology --all --include-costs  # Multi-account topology
        """
        try:
            from runbooks.vpc.topology_generator import NetworkTopologyGenerator
            from runbooks.common.profile_utils import get_profile_for_operation
            from runbooks.common.rich_utils import handle_output_format

            # Use ProfileManager for dynamic profile resolution
            resolved_profile = get_profile_for_operation("operational", profile)

            topology_generator = NetworkTopologyGenerator(
                profile=resolved_profile,
                region=region,
                include_costs=include_costs,
                detail_level=detail_level,
                output_dir=output_dir,
            )

            topology_results = topology_generator.generate_network_topology()

            # Use unified format handling
            handle_output_format(
                data=topology_results,
                output_format=output_format,
                output_file=output_file,
                title="Network Topology Analysis",
            )

            console.print(f"[green]✅ Network topology generated successfully[/green]")
            console.print(f"[dim]Output directory: {output_dir}[/dim]")

            return topology_results

        except ImportError as e:
            console.print(f"[red]❌ VPC topology module not available: {e}[/red]")
            raise click.ClickException("VPC topology functionality not available")
        except Exception as e:
            console.print(f"[red]❌ VPC topology generation failed: {e}[/red]")
            raise click.ClickException(str(e))

    @vpc.command("discover-firewall-bypass")
    @click.option("--management-profile", required=True, help="AWS profile for Organizations access")
    @click.option("--operational-profile", required=True, help="AWS profile for networking resources")
    @click.option("--billing-profile", required=True, help="AWS profile for cost analysis")
    @click.option("--regions", multiple=True, default=("ap-southeast-2",), help="AWS regions to scan")
    @click.option("--export", type=click.Choice(["csv", "excel", "json", "all"]), default="all", help="Export format")
    @click.option("--output-dir", type=click.Path(), default="data", help="Output directory for exports")
    @click.pass_context
    def discover_firewall_bypass(
        ctx,
        management_profile: str,
        operational_profile: str,
        billing_profile: str,
        regions: tuple,
        export: str,
        output_dir: str,
    ):
        """
        Discover VPCs NOT routing through central firewall for inspection.

        Identifies VPCs bypassing centralized security inspection by analyzing:
        - VPC peering connections to central firewall VPC
        - Route table configurations for ingress/egress traffic
        - Cost impact of non-compliant network traffic

        Examples:
            runbooks vpc discover-firewall-bypass \\
                --management-profile ${MANAGEMENT_PROFILE} \\
                --operational-profile ${CENTRALISED_OPS_PROFILE} \\
                --billing-profile ${BILLING_PROFILE}

            runbooks vpc discover-firewall-bypass \\
                --management-profile Management \\
                --operational-profile Ops \\
                --billing-profile Billing \\
                --regions ap-southeast-2 --regions ap-southeast-6 \\
                --export excel
        """
        from pathlib import Path
        from datetime import datetime
        from runbooks.common.rich_utils import print_header, print_info, print_success, print_error, create_table

        print_header("VPC Central Firewall Bypass Discovery", "1.1.x")

        print_info(f"Management Profile: {management_profile}")
        print_info(f"Operational Profile: {operational_profile}")
        print_info(f"Billing Profile: {billing_profile}")
        print_info(f"Regions: {', '.join(regions)}\n")

        try:
            # Import the core discovery module (will be provided by Track 1)
            from runbooks.vpc.firewall_bypass_discovery import FirewallBypassDiscovery

            # Execute discovery
            console.print("[bold cyan]Executing VPC firewall bypass discovery...[/bold cyan]\n")

            discovery = FirewallBypassDiscovery(
                management_profile=management_profile,
                operational_profile=operational_profile,
                billing_profile=billing_profile,
                regions=list(regions),
            )

            vpcs = discovery.discover_all()

            # Display summary
            no_inspection = [v for v in vpcs if v.inspection_status.value == "none"]
            egress_only = [v for v in vpcs if v.inspection_status.value == "egress_only"]
            full_inspection = [v for v in vpcs if v.inspection_status.value == "ingress_egress"]

            from rich import box

            table = create_table(title="Firewall Bypass Discovery Summary", box_style=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="bright_yellow", justify="right")

            table.add_row("Total VPCs", str(len(vpcs)))
            table.add_row("No Inspection", str(len(no_inspection)), style="bright_red")
            table.add_row("Egress Only", str(len(egress_only)), style="bright_yellow")
            table.add_row("Full Inspection", str(len(full_inspection)), style="bright_green")

            if len(vpcs) > 0:
                compliance_pct = len(full_inspection) / len(vpcs) * 100
                table.add_row("Compliance %", f"{compliance_pct:.1f}%")
            else:
                table.add_row("Compliance %", "N/A")

            console.print(table)

            # Export results
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

            exported_files = []

            if export in ["csv", "all"]:
                csv_file = output_path / f"vpc-firewall-bypass-{timestamp}.csv"
                discovery.export_to_csv(csv_file)
                exported_files.append(str(csv_file))
                print_success(f"CSV exported: {csv_file}")

            if export in ["excel", "all"]:
                excel_file = output_path / f"vpc-firewall-bypass-{timestamp}.xlsx"
                discovery.export_to_excel(excel_file)
                exported_files.append(str(excel_file))
                print_success(f"Excel exported: {excel_file}")

            if export in ["json", "all"]:
                json_file = output_path / f"vpc-firewall-bypass-{timestamp}.json"
                discovery.export_to_json(json_file)
                exported_files.append(str(json_file))
                print_success(f"JSON exported: {json_file}")

            print_success(f"\nDiscovery complete! Exported {len(exported_files)} file(s).")

        except ImportError as e:
            print_error(f"Required module not available: {e}")
            console.print("\n[yellow]⚠️  This command requires the firewall_bypass_discovery module.[/yellow]")
            console.print("[yellow]   Track 1 must complete core engine implementation first.[/yellow]")
        except Exception as e:
            print_error(f"Failed to execute firewall bypass discovery: {e}")

    @vpc.command("vpce-cleanup")
    @common_aws_options
    @click.option("--csv-file", type=click.Path(exists=True), required=True, help="CSV file with VPCE cleanup data")
    @click.option("--validate", is_flag=True, help="Validate VPCEs exist via AWS API")
    @click.option("--generate-commands", is_flag=True, help="Generate cleanup script")
    @click.option("--claimed-annual", type=float, help="Claimed annual savings for comparison")
    @click.option("--output-dir", type=click.Path(), default="tmp", help="Output directory")
    @click.pass_context
    def vpce_cleanup(ctx, profile, region, dry_run, csv_file, validate, generate_commands, claimed_annual, output_dir):
        """Analyze VPC endpoint cleanup candidates and calculate savings."""
        try:
            from pathlib import Path
            import boto3
            from runbooks.vpc.vpce_analyzer import VPCEndpointAnalyzer
            from runbooks.common.rich_utils import print_header, print_success, print_error

            print_header("VPC Endpoint Cleanup Analysis", "1.2.0")

            # Load and analyze VPCE data
            analyzer = VPCEndpointAnalyzer()
            endpoint_count = analyzer.load_from_csv(Path(csv_file))

            if endpoint_count == 0:
                print_error("No endpoints loaded from CSV")
                return

            # Calculate costs
            analyzer.calculate_costs()
            analyzer.aggregate_by_account()

            # Display summary
            analyzer.display_summary(claimed_annual=claimed_annual)

            # Validate with AWS APIs
            if validate:
                console.print("\n" + "=" * 70)
                console.print("[bold cyan]AWS API VALIDATION[/bold cyan]")
                console.print("=" * 70 + "\n")

                if not profile:
                    print_error("⚠️  No profile specified, skipping validation")
                else:
                    try:
                        from runbooks.common.profile_utils import get_profile_for_operation

                        resolved_profile = get_profile_for_operation("operational", profile)
                        session = boto3.Session(profile_name=resolved_profile)
                        ec2 = session.client("ec2", region_name=region or "ap-southeast-2")

                        # Validate sample endpoints (first 5)
                        sample_endpoints = analyzer.endpoints[:5]
                        sample_vpce_ids = [e.vpce_id for e in sample_endpoints]

                        response = ec2.describe_vpc_endpoints(VpcEndpointIds=sample_vpce_ids)
                        existing_ids = [e["VpcEndpointId"] for e in response["VpcEndpoints"]]

                        console.print(f"Validated {len(sample_vpce_ids)} endpoints:\n")
                        for vpce_id in sample_vpce_ids:
                            status = "✅ EXISTS" if vpce_id in existing_ids else "❌ NOT FOUND"
                            console.print(f"  {vpce_id}: {status}")

                        print_success(
                            f"\n✅ AWS API validation complete ({len(existing_ids)}/{len(sample_vpce_ids)} found)"
                        )

                    except Exception as e:
                        print_error(f"❌ Validation failed: {e}")

            # Generate cleanup commands
            if generate_commands:
                output_path = Path(output_dir)
                commands_file = output_path / "vpce-cleanup-commands.sh"

                command_count = analyzer.generate_cleanup_commands(commands_file, dry_run=dry_run)

                # Also generate summary CSV
                summary_file = output_path / "vpce-cleanup-summary.csv"
                analyzer.export_summary_csv(summary_file)

                print_success(f"\n✅ Generated {command_count} cleanup commands")

        except ImportError as e:
            console.print(f"[red]❌ VPCE analyzer module not available: {e}[/red]")
            raise click.ClickException("VPCE cleanup functionality not available")
        except Exception as e:
            console.print(f"[red]❌ VPCE cleanup analysis failed: {e}[/red]")
            raise click.ClickException(str(e))

    @vpc.command("analyze-endpoint-activity")
    @click.option("--profile", envvar="AWS_PROFILE", required=True, help="AWS profile for VPC endpoint discovery")
    @click.option("--management-profile", help="AWS profile for CloudTrail access (default: profile)")
    @click.option("--regions", multiple=True, default=("ap-southeast-2",), help="AWS regions to scan")
    @click.option("--lookback-days", type=int, default=90, help="CloudTrail lookback period (max: 90 days)")
    @click.option("--output-format", type=click.Choice(["csv", "xlsx", "json"]), default="xlsx", help="Export format")
    @click.option(
        "--output-file", type=click.Path(), default="/tmp/vpce-activity-analysis.xlsx", help="Output file path"
    )
    def analyze_endpoint_activity(
        profile: str, management_profile: str, regions: tuple, lookback_days: int, output_format: str, output_file: str
    ):
        """
        Analyze VPC endpoint activity via CloudTrail (90-day lookback).

        Identifies inactive VPC endpoints (no API calls in lookback period) for
        decommissioning decisions. Supports JIRA AWSO-66: 65 endpoints, $18K annual
        savings potential.

        Signals:
            - V1: No CloudTrail API calls (90 days) - 45 points (decommission candidate)
            - Activity count: Number of API calls in lookback period
            - Last activity date: Most recent CloudTrail event

        Examples:
            # Basic analysis (ap-southeast-2, 90-day lookback)
            runbooks vpc analyze-endpoint-activity --profile CENTRALISED_OPS_PROFILE

            # Multi-region with custom lookback
            runbooks vpc analyze-endpoint-activity \\
                --profile CENTRALISED_OPS_PROFILE \\
                --management-profile MANAGEMENT_PROFILE \\
                --regions ap-southeast-2 --regions ap-southeast-6 \\
                --lookback-days 60

            # CSV export to custom location
            runbooks vpc analyze-endpoint-activity \\
                --profile CENTRALISED_OPS_PROFILE \\
                --output-format csv \\
                --output-file /tmp/vpce-activity.csv
        """
        try:
            from runbooks.common.rich_utils import print_header, print_info, print_success, print_error
            from runbooks.vpc.cloudtrail_activity_analyzer import analyze_vpc_endpoint_activity

            print_header("VPC Endpoint Activity Analyzer", "v1.1.19")

            print_info(f"Profile: {profile}")
            print_info(f"Management Profile: {management_profile or profile}")
            print_info(f"Regions: {', '.join(regions)}")
            print_info(f"Lookback Period: {lookback_days} days")
            print_info(f"Output Format: {output_format}")
            print_info(f"Output File: {output_file}\n")

            # Execute analysis
            result = analyze_vpc_endpoint_activity(
                profile=profile,
                regions=list(regions),
                lookback_days=lookback_days,
                output_file=output_file,
                output_format=output_format,
                management_profile=management_profile,
            )

            if result["success"]:
                print_success(f"\n✅ Analysis complete!")
                print_info(f"   Total endpoints: {result['total_endpoints']}")
                print_info(f"   Active (>0 calls): {result['active_endpoints']}")
                print_info(f"   Inactive (0 calls): {result['inactive_endpoints']}")
                print_info(f"   Decommission candidates: {result['decommission_candidates']}")
                print_info(f"   Output: {result['output_file']}")
            else:
                print_error(f"❌ Analysis failed: {result.get('error', 'unknown')}")

        except ImportError as e:
            console.print(f"[red]❌ CloudTrail activity analyzer module not available: {e}[/red]")
            raise click.ClickException("VPC endpoint activity analysis functionality not available")
        except Exception as e:
            console.print(f"[red]❌ VPC endpoint activity analysis failed: {e}[/red]")
            raise click.ClickException(str(e))

    @vpc.command("network-discover")
    @click.option("--profiles", "-p", multiple=True, required=True, help="AWS profile(s) to discover")
    @click.option("--region", "-r", default="ap-southeast-2", help="AWS region")
    @click.option("--output-dir", type=click.Path(), default="artifacts/network-discovery", help="Output directory")
    @click.option(
        "--export", type=click.Choice(["all", "json", "excel", "diagrams"]), default="all", help="Export format"
    )
    @click.option("--diagrams/--no-diagrams", default=True, help="Generate architecture diagrams (PNG+SVG)")
    @click.pass_context
    def network_discover(ctx, profiles, region, output_dir, export, diagrams):
        """
        Multi-account network discovery with architecture diagrams.

        \b
        🔍 DISCOVERY SCOPE
        ├── 🌐 Network Resources
        │   └── VPCs, Subnets, NAT Gateways, Internet Gateways
        ├── 🔗 Connectivity
        │   └── Transit Gateways, VPC Endpoints, Route Tables
        ├── 🔒 Security
        │   └── Security Groups, Network Interfaces
        └── 📊 Exports
            └── JSON, Excel (9 sheets), PNG/SVG diagrams

        \b
        📖 Examples:
            # Single account discovery
            runbooks vpc network-discover --profiles my-profile

            # Multi-account discovery
            runbooks vpc network-discover -p profile1 -p profile2

            # JSON-only export (no diagrams)
            runbooks vpc network-discover -p my-profile --export json --no-diagrams
        """
        try:
            from runbooks.vpc.cli import network_discover as vpc_network_discover
            from click.testing import CliRunner

            # Build command arguments
            args = []
            for p in profiles:
                args.extend(["--profiles", p])
            args.extend(["--region", region])
            args.extend(["--output-dir", output_dir])
            args.extend(["--export", export])
            if diagrams:
                args.append("--diagrams")
            else:
                args.append("--no-diagrams")

            # Invoke the VPC module's network_discover command
            runner = CliRunner()
            result = runner.invoke(vpc_network_discover, args)

            # Output result
            if result.output:
                click.echo(result.output)

            if result.exit_code != 0:
                raise click.ClickException(f"Network discovery failed: {result.output}")

        except ImportError as e:
            console.print(f"[red]❌ Network discovery module not available: {e}[/red]")
            raise click.ClickException("Network discovery functionality not available")
        except Exception as e:
            console.print(f"[red]❌ Network discovery failed: {e}[/red]")
            raise click.ClickException(str(e))

    return vpc
