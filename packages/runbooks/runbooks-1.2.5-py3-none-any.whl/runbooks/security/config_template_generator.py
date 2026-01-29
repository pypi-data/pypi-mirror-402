#!/usr/bin/env python3
"""
Configuration Template Generator for Security and Remediation Modules
====================================================================

This utility generates configuration templates for enterprise security and
remediation operations, eliminating the need for hardcoded values.

Features:
- Compliance weight configuration templates
- Account discovery configuration templates
- Framework threshold configuration templates
- Environment variable examples
- Complete setup documentation

Author: DevOps Security Engineer (Claude Code Enterprise Team)
Version: 1.0.0 - Universal Configuration Templates
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import click

from runbooks.common.rich_utils import console, create_panel, print_info, print_success


class SecurityConfigTemplateGenerator:
    """Generate configuration templates for security and remediation modules."""

    def __init__(self, output_dir: str = "./artifacts/security/config"):
        """Initialize template generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_compliance_config_template(self) -> Dict:
        """Generate compliance configuration template."""
        return {
            "_description": "Universal Compliance Configuration Template",
            "_usage": "Set COMPLIANCE_CONFIG_PATH environment variable to point to this file",
            "control_weights": {
                "_description": "Control weights for compliance scoring (1.0 = normal, 2.0 = double weight)",
                "aws_well_architected": {
                    "sec-1": 2.0,  # Identity Foundation
                    "sec-2": 1.5,  # Security at All Layers
                    "sec-3": 2.5,  # Data Protection
                    "sec-4": 1.8,  # Incident Response
                    "sec-5": 1.2,  # Network Security
                },
                "soc2_type_ii": {
                    "cc6-1": 3.0,  # Access Controls (Critical)
                    "cc6-2": 2.5,  # Authentication
                    "cc6-3": 2.0,  # Authorization
                    "cc7-1": 2.2,  # System Operations
                    "cc8-1": 1.8,  # Change Management
                },
                "pci_dss": {
                    "pci-1": 2.0,  # Network Security
                    "pci-2": 2.5,  # System Security
                    "pci-3": 3.0,  # Data Protection (Critical)
                    "pci-4": 2.0,  # Transmission Security
                    "pci-6": 1.5,  # Secure Systems
                },
                "hipaa": {
                    "hipaa-164-312-a-1": 2.5,  # Access Control
                    "hipaa-164-312-a-2": 2.0,  # Assigned Security
                    "hipaa-164-312-b": 3.0,  # Audit Controls (Critical)
                    "hipaa-164-312-c": 2.8,  # Integrity
                    "hipaa-164-312-d": 1.5,  # Person Authentication
                },
            },
            "framework_thresholds": {
                "_description": "Minimum compliance scores required for each framework (percentage)",
                "aws-well-architected": 90.0,
                "soc2-type-ii": 95.0,
                "pci-dss": 100.0,  # PCI DSS requires perfect compliance
                "hipaa": 95.0,
                "nist-cybersecurity": 90.0,
                "iso-27001": 90.0,
                "cis-benchmarks": 88.0,
            },
            "assessment_frequencies": {
                "_description": "How often to assess each control type",
                "critical-controls": "weekly",
                "high-controls": "monthly",
                "medium-controls": "quarterly",
                "low-controls": "annually",
            },
            "remediation_priorities": {
                "_description": "Remediation priority levels (1=highest, 5=lowest)",
                "critical-controls": 1,
                "high-controls": 2,
                "medium-controls": 3,
                "low-controls": 4,
            },
        }

    def generate_account_config_template(self) -> Dict:
        """Generate account discovery configuration template."""
        return {
            "_description": "Universal Account Discovery Configuration Template",
            "_usage": "Set REMEDIATION_ACCOUNT_CONFIG environment variable to point to this file",
            "target_accounts": [
                {
                    "account_id": "111122223333",
                    "account_name": "Production Environment",
                    "status": "ACTIVE",
                    "email": "prod@company.com",
                    "profile_name": "prod-profile",
                    "environment": "production",
                    "criticality": "high",
                },
                {
                    "account_id": "444455556666",
                    "account_name": "Staging Environment",
                    "status": "ACTIVE",
                    "email": "staging@company.com",
                    "profile_name": "staging-profile",
                    "environment": "staging",
                    "criticality": "medium",
                },
                {
                    "account_id": "777788889999",
                    "account_name": "Development Environment",
                    "status": "ACTIVE",
                    "email": "dev@company.com",
                    "profile_name": "dev-profile",
                    "environment": "development",
                    "criticality": "low",
                },
            ],
            "discovery_settings": {
                "max_concurrent_accounts": 10,
                "validation_timeout_seconds": 30,
                "include_suspended_accounts": False,
                "auto_discover_via_organizations": True,
                "fallback_to_current_account": True,
            },
            "filtering_rules": {
                "include_patterns": ["prod-*", "staging-*"],
                "exclude_patterns": ["test-*", "sandbox-*"],
                "max_accounts": 50,
            },
        }

    def generate_environment_variables_template(self) -> str:
        """Generate environment variables template."""
        return """# Universal Security and Remediation Configuration
# ================================================

# Profile Configuration (Universal Profile Management)
# Use any AWS profile name - no hardcoded requirements
export AWS_PROFILE="your-aws-profile-name"

# Compliance Configuration
export COMPLIANCE_CONFIG_PATH="/path/to/compliance_config.json"

# Alternative: Individual compliance weight overrides
export COMPLIANCE_WEIGHT_SEC_1="2.0"
export COMPLIANCE_WEIGHT_CC6_1="3.0" 
export COMPLIANCE_WEIGHT_PCI_3="3.0"

# Framework threshold overrides
export COMPLIANCE_THRESHOLD_PCI_DSS="100.0"
export COMPLIANCE_THRESHOLD_SOC2_TYPE_II="95.0"
export COMPLIANCE_THRESHOLD_AWS_WELL_ARCHITECTED="90.0"

# Account Discovery Configuration
export REMEDIATION_ACCOUNT_CONFIG="/path/to/account_config.json"

# Alternative: Simple comma-separated account list
export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666,777788889999"

# Security Assessment Configuration
export SECURITY_OUTPUT_DIR="./artifacts/security"
export SECURITY_EXPORT_FORMATS="json,csv,html,pdf"
export SECURITY_ASSESSMENT_LANGUAGE="en"

# Remediation Configuration  
export REMEDIATION_OUTPUT_DIR="./artifacts/remediation"
export REMEDIATION_MAX_CONCURRENT="10"
export REMEDIATION_DRY_RUN="true"

# Multi-Account Configuration
export ORGANIZATIONS_MANAGEMENT_ROLE="OrganizationAccountAccessRole"
export CROSS_ACCOUNT_ROLE="SecurityAuditRole"

# Performance Tuning
export SECURITY_MAX_WORKERS="10"
export REMEDIATION_TIMEOUT_SECONDS="300"
export COMPLIANCE_CACHE_TTL="3600"

# Example Usage Commands
# =====================

# Security baseline assessment with custom profile
# runbooks security assess --profile your-profile --frameworks aws-well-architected,soc2-type-ii

# Multi-account remediation with discovered accounts
# runbooks remediation s3-security --all --operations block_public_access,enforce_ssl

# Custom compliance assessment with specific accounts  
# runbooks security assess --accounts 111122223333,444455556666 --scope critical

# Export compliance configuration template
# runbooks security export-config-template --output-dir ./config
"""

    def generate_setup_documentation(self) -> str:
        """Generate complete setup documentation."""
        return """# Universal Security and Remediation Module Setup Guide
======================================================

This guide helps you configure the security and remediation modules for ANY AWS environment without hardcoded values.

## Quick Start

1. **Basic Setup (Single Account)**
   ```bash
   export AWS_PROFILE="your-aws-profile"
   runbooks security assess
   ```

2. **Multi-Account Setup (Organizations)**
   ```bash
   export AWS_PROFILE="your-management-account-profile"
   runbooks security assess --all
   ```

3. **Custom Configuration**
   ```bash
   export COMPLIANCE_CONFIG_PATH="./compliance_config.json"
   export REMEDIATION_ACCOUNT_CONFIG="./account_config.json"
   runbooks security assess --frameworks pci-dss,hipaa
   ```

## Configuration Methods

### Method 1: Environment Variables (Simple)
Best for: Quick setup, CI/CD pipelines, simple environments

```bash
export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666"
export COMPLIANCE_THRESHOLD_PCI_DSS="100.0"
```

### Method 2: Configuration Files (Recommended)
Best for: Enterprise environments, complex setups, team collaboration

```bash
export COMPLIANCE_CONFIG_PATH="./config/compliance.json"
export REMEDIATION_ACCOUNT_CONFIG="./config/accounts.json"
```

### Method 3: AWS Organizations (Automatic)
Best for: Large organizations, dynamic account discovery

```bash
export AWS_PROFILE="management-account-profile"
# No additional configuration needed - automatic discovery
```

## Universal Profile Support

The modules work with ANY AWS profile configuration:

- **Single Account**: Use any profile name
- **Multi-Account**: Use management account profile
- **AWS SSO**: Full support for SSO profiles  
- **Cross-Account Roles**: Automatic role assumption
- **Mixed Environments**: Supports any AWS setup

## Compliance Framework Configuration

### Supported Frameworks
- AWS Well-Architected Security Pillar
- SOC2 Type II
- PCI DSS (Payment Card Industry)
- HIPAA (Healthcare compliance)
- NIST Cybersecurity Framework
- ISO 27001 (Information Security)
- CIS Benchmarks (Security benchmarks)

### Custom Weights and Thresholds
Configure compliance scoring to match your requirements:

```json
{
  "control_weights": {
    "sec-1": 2.0,  // Double weight for critical controls
    "cc6-1": 3.0   // Triple weight for access controls
  },
  "framework_thresholds": {
    "pci-dss": 100.0,  // PCI requires perfect compliance
    "hipaa": 95.0       // HIPAA requires high compliance
  }
}
```

## Account Discovery Configuration

### Automatic Discovery (Recommended)
The system automatically discovers accounts using:
1. Environment variables (REMEDIATION_TARGET_ACCOUNTS)
2. Configuration files (REMEDIATION_ACCOUNT_CONFIG)
3. AWS Organizations API (if available)
4. Current account (single account fallback)

### Manual Configuration
For specific account targeting:

```json
{
  "target_accounts": [
    {
      "account_id": "111122223333",
      "account_name": "Production",
      "profile_name": "prod-profile"
    }
  ]
}
```

## Security Operations

### Assessment Commands
```bash
# Single framework assessment
runbooks security assess --frameworks aws-well-architected

# Multi-framework assessment
runbooks security assess --frameworks soc2-type-ii,pci-dss,hipaa

# All accounts assessment
runbooks security assess --all --scope full

# Specific accounts assessment
runbooks security assess --accounts 111122223333,444455556666
```

### Remediation Commands
```bash
# S3 security remediation
runbooks remediation s3-security --operations block_public_access,enforce_ssl

# Multi-account remediation
runbooks remediation s3-security --all --operations enable_encryption

# Specific account remediation
runbooks remediation s3-security --accounts 111122223333
```

## Troubleshooting

### Common Issues

1. **Profile Not Found**
   ```bash
   aws configure list-profiles  # Check available profiles
   export AWS_PROFILE="correct-profile-name"
   ```

2. **Organizations Access Denied**
   ```bash
   # Falls back to environment/config discovery automatically
   export REMEDIATION_TARGET_ACCOUNTS="111122223333,444455556666"
   ```

3. **Compliance Threshold Too High**
   ```bash
   export COMPLIANCE_THRESHOLD_AWS_WELL_ARCHITECTED="85.0"
   ```

### Validation Commands
```bash
# Validate profile access
runbooks security validate-profile --profile your-profile

# Test account discovery
runbooks security discover-accounts --profile your-profile

# Validate compliance configuration
runbooks security validate-config --config-path ./compliance.json
```

## Enterprise Integration

### CI/CD Pipeline Integration
```yaml
# Example GitHub Actions workflow
env:
  AWS_PROFILE: "ci-cd-profile"
  COMPLIANCE_CONFIG_PATH: "./config/compliance.json"
  REMEDIATION_TARGET_ACCOUNTS: "111122223333,444455556666"

steps:
  - name: Security Assessment
    run: runbooks security assess --frameworks aws-well-architected,soc2-type-ii
  
  - name: Automated Remediation  
    run: runbooks remediation s3-security --operations block_public_access
```

### Monitoring Integration
```bash
# Export compliance metrics for monitoring
runbooks security assess --export-formats json,csv
runbooks security export-metrics --output ./metrics/
```

This configuration system eliminates ALL hardcoded values and provides universal compatibility with any AWS environment.
"""

    def generate_all_templates(self) -> None:
        """Generate all configuration templates."""
        console.print(
            create_panel(
                "[bold cyan]Generating Universal Security Configuration Templates[/bold cyan]\n\n"
                "[dim]Creating configuration templates for enterprise security operations...[/dim]",
                title="🔧 Configuration Template Generator",
                border_style="cyan",
            )
        )

        # Generate compliance configuration
        compliance_config = self.generate_compliance_config_template()
        compliance_path = self.output_dir / "compliance_config.json"
        with open(compliance_path, "w") as f:
            json.dump(compliance_config, f, indent=2)
        print_success(f"Generated compliance configuration: {compliance_path}")

        # Generate account configuration
        account_config = self.generate_account_config_template()
        account_path = self.output_dir / "account_config.json"
        with open(account_path, "w") as f:
            json.dump(account_config, f, indent=2)
        print_success(f"Generated account configuration: {account_path}")

        # Generate environment variables template
        env_template = self.generate_environment_variables_template()
        env_path = self.output_dir / "environment_variables.sh"
        with open(env_path, "w") as f:
            f.write(env_template)
        print_success(f"Generated environment variables template: {env_path}")

        # Generate setup documentation
        setup_docs = self.generate_setup_documentation()
        docs_path = self.output_dir / "SETUP_GUIDE.md"
        with open(docs_path, "w") as f:
            f.write(setup_docs)
        print_success(f"Generated setup documentation: {docs_path}")

        # Generate summary
        console.print(
            "\n"
            + create_panel(
                f"[bold green]Configuration templates generated successfully![/bold green]\n\n"
                f"[cyan]Files created in {self.output_dir}:[/cyan]\n"
                f"• compliance_config.json - Compliance weights and thresholds\n"
                f"• account_config.json - Account discovery configuration\n"
                f"• environment_variables.sh - Environment variable examples\n"
                f"• SETUP_GUIDE.md - Complete setup documentation\n\n"
                f"[yellow]Next steps:[/yellow]\n"
                f"1. Review and customize the configuration files\n"
                f"2. Set environment variables or use config files\n"
                f"3. Run: runbooks security assess --help\n"
                f"4. Run: runbooks remediation --help",
                title="✅ Templates Ready",
                border_style="green",
            )
        )


@click.command()
@click.option(
    "--output-dir", default="./artifacts/security/config", help="Output directory for configuration templates"
)
def generate_config_templates(output_dir: str):
    """Generate universal configuration templates for security and remediation modules."""
    generator = SecurityConfigTemplateGenerator(output_dir)
    generator.generate_all_templates()


if __name__ == "__main__":
    generate_config_templates()
