# AWS VPC Networking Operations (CLI)

The AWS VPC Networking Operations module is an enterprise-grade command-line tool for AWS VPC analysis, cost optimization, and network management. Built with the Rich library for beautiful terminal output, it provides comprehensive VPC insights with cost analysis, security assessment, and automated optimization recommendations.

## 📈 *vpc-runbooks*.md Enterprise Rollout

Following proven **99/100 manager score** success patterns established in FinOps:

### **Rollout Strategy**: Progressive *-runbooks*.md standardization 
- **Phase 3**: VPC rollout with *vpc-runbooks*.md framework ✅
- **Phase 4**: Enhanced networking operations with enterprise patterns (Next)
- **Integration**: Complete cost optimization with FinOps module alignment

## Why AWS VPC Networking Operations?

Managing VPC networking across multiple AWS accounts requires sophisticated analysis and optimization capabilities. The VPC Operations CLI provides enterprise-grade network analysis, cost optimization insights, and security assessment tools designed for cloud architects and network engineers.

Key capabilities include:
- **VPC Cost Analysis**: Detailed cost breakdown and optimization recommendations
- **Network Security Assessment**: Comprehensive security group and NACL analysis
- **Resource Utilization**: Unused resource identification and cleanup recommendations
- **Multi-Account Support**: Cross-account VPC analysis and management
- **Rich Terminal UI**: Professional console output with charts and detailed reporting

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [AWS CLI Profile Setup](#aws-cli-profile-setup)
- [Command Line Usage](#command-line-usage)
  - [Options](#command-line-options)
  - [Examples](#examples)
- [VPC Analysis Operations](#vpc-analysis-operations)
  - [Cost Analysis](#cost-analysis)
  - [Network Security Assessment](#network-security-assessment)
  - [Resource Optimization](#resource-optimization)
  - [Multi-Account Operations](#multi-account-operations)
- [Configuration](#configuration)
- [Export Formats](#export-formats)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **VPC Cost Analysis**: 
  - Detailed cost breakdown by service and resource type
  - NAT Gateway cost optimization recommendations (up to 30% savings)
  - Unused resource identification and cleanup suggestions
  - Historical cost trending and projection analysis
- **Network Security Assessment**: 
  - Security group rule analysis and optimization
  - Network ACL configuration validation
  - VPC Flow Logs compliance checking
  - Public access exposure identification
- **Resource Optimization**: 
  - Unused Elastic IP identification
  - Idle Load Balancer detection
  - VPC Endpoint optimization recommendations
  - Subnet utilization analysis
- **Multi-Account Support**:
  - Cross-account VPC analysis
  - AWS Organizations integration
  - Consolidated reporting across accounts
  - Role-based access management
- **Configuration Management**:
  - Centralized configuration via TOML files
  - Environment-specific settings
  - Profile-based authentication management
  - **NEW**: YAML campaign configuration for multi-Landing Zone VPC cleanup analysis
- **Rich Terminal UI**: Beautiful terminal output with progress indicators and charts
- **Export Options**:
  - JSON export for automation integration
  - CSV export for spreadsheet analysis  
  - HTML reports for stakeholder communication
  - PDF reports for executive summaries

---

## Prerequisites

- **Python 3.8 or later**: Ensure you have the required Python version installed
- **AWS CLI configured with named profiles**: Set up your AWS CLI profiles for seamless integration
- **AWS credentials with permissions**:
  - `ec2:Describe*` (for VPC and networking resource discovery)
  - `ce:GetCostAndUsage` (for cost analysis)
  - `ce:GetUsageReport` (for usage analysis)
  - `organizations:List*` (for multi-account operations)
  - `sts:AssumeRole` (for cross-account access)
  - `sts:GetCallerIdentity` (for identity validation)

---

## Installation

There are several ways to install the AWS VPC Operations CLI:

### Option 1: Using uv (Fast Python Package Installer)
[uv](https://github.com/astral-sh/uv) is a modern Python package installer and resolver that's extremely fast.

```bash
# Install runbooks with VPC operations
uv pip install runbooks
```

### Option 2: Using pip
```bash
# Install runbooks package
pip install runbooks
```

---

## AWS CLI Profile Setup

Configure your named profiles for VPC operations:

```bash
aws configure --profile vpc-production
aws configure --profile vpc-development  
aws configure --profile vpc-management
# ... etc ...
```

For multi-account VPC analysis, ensure cross-account roles are properly configured.

---

## Command Line Usage

Run VPC operations using `runbooks vpc` followed by options:

```bash
runbooks vpc [operation] [options]
```

### Command Line Options

| Flag | Description |
|---|---|
| `--profile`, `-p` | AWS profile to use for operations |
| `--region`, `-r` | AWS region to analyze (default: ap-southeast-2) |
| `--all-regions` | Analyze VPCs across all available regions |
| `--account-id` | Specific AWS account to analyze |
| `--output-format` | Output format: table, json, csv, html |
| `--output-file` | Save results to specified file |
| `--cost-analysis` | Include detailed cost analysis |
| `--security-analysis` | Include security assessment |
| `--optimization-recommendations` | Generate optimization recommendations |

### Examples

```bash
# Basic VPC analysis
runbooks vpc analyze --profile production

# Multi-region VPC analysis with cost breakdown
runbooks vpc analyze --profile production --all-regions --cost-analysis

# Security-focused VPC assessment
runbooks vpc analyze --profile production --security-analysis --output-format html

# Optimization recommendations
runbooks vpc optimize --profile production --region ap-southeast-2

# Multi-account VPC analysis
runbooks vpc analyze --profile management-account --organization-wide
```

---

## VPC Analysis Operations

### Cost Analysis

**Comprehensive Cost Breakdown**:
```bash
# Detailed VPC cost analysis
runbooks vpc analyze --cost-analysis --profile production --region ap-southeast-2

# Multi-region cost analysis
runbooks vpc analyze --cost-analysis --all-regions --profile production

# NAT Gateway cost optimization
runbooks vpc optimize --focus nat-gateways --profile production
```

**Expected Output**:
```
╭─ VPC Cost Analysis Summary ─╮
│ Total Monthly Cost: $2,847.50 │
│ NAT Gateway Costs: $1,245.60  │  
│ Data Transfer: $892.30        │
│ Load Balancers: $709.60       │
│                               │
│ 💡 Optimization Potential:    │
│ • NAT Gateway: 30% savings    │
│ • Unused EIPs: $45.60/month   │
│ • Idle LBs: $180.20/month     │
╰───────────────────────────────╯
```

### Network Security Assessment

**Security Group Analysis**:
```bash
# Comprehensive security assessment
runbooks vpc analyze --security-analysis --profile production

# Focus on public access exposure
runbooks vpc security --check-public-exposure --profile production

# Security group rule optimization
runbooks vpc security --optimize-rules --profile production
```

**Security Assessment Report**:
```
╭─ VPC Security Assessment ─╮
│ Security Groups: 47        │
│ • Compliant: 42 (89%)      │
│ • Issues Found: 5 (11%)    │
│                            │
│ Network ACLs: 12           │
│ • Default: 8               │
│ • Custom: 4                │
│                            │
│ 🚨 Critical Issues:        │
│ • Open SSH (0.0.0.0/0): 2  │
│ • Open RDP (0.0.0.0/0): 1  │
╰────────────────────────────╯
```

### Resource Optimization

**Unused Resource Detection**:
```bash
# Find unused VPC resources
runbooks vpc optimize --find-unused --profile production

# Cleanup recommendations
runbooks vpc cleanup --dry-run --profile production

# Resource utilization analysis
runbooks vpc analyze --utilization --profile production
```

### **NEW: Config-Driven VPC Cleanup Campaign Analysis**

**AWS-25 Campaign Example** ($101,247.67/year realized savings):

```bash
# Config-driven multi-VPC cleanup analysis
runbooks vpc analyze \
  --config examples/vpc-cleanup/aws25-campaign-config.yaml \
  --profile ${BILLING_PROFILE}
```

**Campaign Results Output**:
```
╭─ VPC Cleanup Campaign: AWS-25 ─────────────────────────╮
│ AWS Profile: ${BILLING_PROFILE} │
│ VPCs Analyzed: 6                                        │
│ Accounts: 909135376185, 335083429030                   │
│ Regions: ap-southeast-2                                │
╰─────────────────────────────────────────────────────────╯

╭─ Campaign Results ──────────────────────────────────────╮
│ VPC ID              Account      Deletion    Annual     │
│                                  Date        Savings    │
├─────────────────────────────────────────────────────────┤
│ vpc-0e113622eb4... 909135376185 2025-09-10  $0.00      │
│ vpc-090b313795... 909135376185 2025-09-08  $0.00      │
│ vpc-016a2f1e86... 909135376185 2025-08-04  $88,215.38 │
│ vpc-08df1f9529... 335083429030 2025-09-10  $241.53    │
│ vpc-0eabfc3260... 335083429030 2025-09-08  $110.65    │
│ vpc-0f1a336ec8... 335083429030 2025-08-04  $12,680.11 │
╰─────────────────────────────────────────────────────────╯

✓ Total Campaign Savings: $101,247.67/year
```

**Campaign Config Schema** (YAML):
```yaml
campaign_metadata:
  campaign_id: "AWS-25"
  aws_billing_profile: "${BILLING_PROFILE}"

deleted_vpcs:
  - vpc_id: "vpc-0e113622eb492c654"
    account_id: "909135376185"
    region: "ap-southeast-2"
    deletion_date: "2025-09-10"

cost_explorer_config:
  metrics: ["UnblendedCost"]
  granularity_monthly: "MONTHLY"

attribution_rules:
  vpc_specific_services:
    attribution_percentage: 100
    confidence_level: "HIGH (95%)"
```

**Multi-Landing Zone Deployment**:
```bash
# Create custom campaign config
cp examples/vpc-cleanup/aws25-campaign-config.yaml config/my_lz_config.yaml

# Update VPC list and campaign metadata
vim config/my_lz_config.yaml

# Execute analysis
runbooks vpc analyze --config config/my_lz_config.yaml --profile my-billing-profile
```

---

## Multi-Landing Zone Deployment Patterns

### Deployment Patterns Overview

#### Pattern Comparison Matrix

| Pattern | Use Case | Complexity | VPC Count | Account Count | Execution Time |
|---------|----------|------------|-----------|---------------|----------------|
| **Single-Account LZ** | Single AWS account cleanup | Low | 1-10 | 1 | 5-15 min |
| **Multi-Account Org** | AWS Organizations cleanup | Medium | 10-50 | 3-20 | 30-90 min |
| **Custom Attribution** | Fine-tuned confidence rules | Medium | Any | Any | Same as base |
| **Large-Scale LZ** | Enterprise-wide cleanup | High | 50+ | 20+ | 2-4 hours |

---

### Pattern 1: Single-Account Landing Zone

**Use Case**: Single AWS account with multiple VPCs deleted over time period.

**Typical Scenarios**:
- Dev/Test account cleanup
- Single-account sandbox decommission
- Departmental AWS account cleanup

#### Prerequisites

**Identify Deleted VPCs via CloudTrail**:
```bash
# Query CloudTrail for DeleteVpc events
AWS_PROFILE=account-profile aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteVpc \
  --start-time "2025-07-01" \
  --end-time "2025-10-01"
```

**MCP Alternative**:
```bash
# Using MCP CloudTrail tool
mcp__cloudtrail__lookup_events \
  --attribute-key EventName \
  --attribute-value DeleteVpc \
  --start-time "30 days ago"
```

#### Deployment Steps

**Create Campaign Config**:
```yaml
# config/lz_acme_dev_config.yaml
campaign_metadata:
  campaign_id: "LZ-ACME-DEV-Q3-2025"
  campaign_name: "ACME Dev Account VPC Cleanup - Q3 2025"
  aws_billing_profile: "acme-dev-billing-readonly"

deleted_vpcs:
  - vpc_id: "vpc-0abc123def456789a"
    account_id: "123456789012"
    deletion_date: "2025-09-15"
    deletion_principal: "devops-team@acme.com"
    pre_deletion_baseline_months: 3

cost_explorer_config:
  metrics: ["UnblendedCost"]
  pre_deletion_baseline:
    granularity_monthly: "MONTHLY"
    months_before_deletion: 3
  post_deletion_validation:
    days_after_deletion: 30

attribution_rules:
  vpc_specific_services:
    confidence_level: "HIGH (95%)"
    attribution_percentage: 100
    service_patterns: ["Amazon Virtual Private Cloud", "AWS PrivateLink"]
  vpc_related_services:
    confidence_level: "MEDIUM (85%)"
    attribution_percentage: 70
    service_patterns: ["Amazon Elastic Compute Cloud - Compute"]
```

**Execute Analysis**:
```bash
./run_vpc_savings_analysis.sh ../config/lz_acme_dev_config.yaml
```

---

### Pattern 2: Multi-Account Organization

**Use Case**: AWS Organizations with VPCs deleted across multiple member accounts.

**Typical Scenarios**:
- Organization-wide quarterly cleanup
- Multi-account migration completion
- Cross-account infrastructure decommission

#### Prerequisites
1. **Centralized Billing Account**: Master payer with Cost Explorer enabled
2. **Multi-Account CloudTrail**: Query across all member accounts
3. **IAM Permissions**: Read-only Cost Explorer in master account

#### Deployment Steps

**Query CloudTrail Across Organization**:
```bash
# Query each account for VPC deletions
for profile in billing-account ops-account dev-account; do
  AWS_PROFILE=$profile aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=DeleteVpc \
    --start-time "2025-07-01"
done > vpc_deletions_org_wide.json
```

**Create Multi-Account Config**:
```yaml
# config/org_q3_cleanup_config.yaml
campaign_metadata:
  campaign_id: "ORG-WIDE-CLEANUP-Q3-2025"
  aws_billing_profile: "org-master-billing-readonly"

deleted_vpcs:
  # Operations Account VPCs
  - vpc_id: "vpc-ops-001-primary"
    account_id: "111111111111"
    deletion_date: "2025-08-10"

  # Development Account VPCs
  - vpc_id: "vpc-dev-001-sandbox"
    account_id: "222222222222"
    deletion_date: "2025-08-15"

  # Production Account VPCs
  - vpc_id: "vpc-prod-legacy-001"
    account_id: "444444444444"
    deletion_date: "2025-09-05"
    pre_deletion_baseline_months: 6  # Longer baseline for prod
```

**Execute with Organization Billing**:
```bash
./run_vpc_savings_analysis.sh ../config/org_q3_cleanup_config.yaml
```

**Analyze Consolidated Results**:
```bash
# Calculate total savings by account
awk -F',' 'NR>1 {sum[$2]+=$(NF-5)} END {for (acct in sum) print acct, sum[acct]}' \
  ../artifacts/org_q3_vpc_cleanup_savings.csv
```

**Expected Output**:
```
111111111111  $15,234.56/year  (Ops Account)
222222222222  $23,456.78/year  (Dev Account)
444444444444  $45,678.90/year  (Prod Account)
---
Total: $93,271.47/year
```

---

### Pattern 3: Custom Attribution Rules

**Use Case**: Adjust attribution percentages for specific environments.

#### Scenario A: Single-VPC Account (Higher Confidence)

**Rationale**: When account only had one VPC, attribution more accurate.

```yaml
attribution_rules:
  vpc_specific_services:
    confidence_level: "HIGH (98%)"
    attribution_percentage: 100
  vpc_related_services:
    confidence_level: "MEDIUM (90%)"
    attribution_percentage: 85  # Increased from default 70%
  other_services:
    confidence_level: "MEDIUM (85%)"
    attribution_percentage: 50  # Increased from default 30%
```

#### Scenario B: Kubernetes/EKS Cluster Cleanup

**Rationale**: EKS workloads have most services VPC-bound.

```yaml
attribution_rules:
  vpc_related_services:
    confidence_level: "HIGH (92%)"
    attribution_percentage: 90  # Higher for EKS
    service_patterns:
      - "Amazon Elastic Compute Cloud - Compute"
      - "Amazon Elastic Container Service for Kubernetes"
      - "Amazon EKS"
```

#### Scenario C: Data Processing Workload (S3-Heavy)

**Rationale**: S3 data lake workloads have high non-VPC costs.

```yaml
attribution_rules:
  other_services:
    confidence_level: "LOW (<75%)"
    attribution_percentage: 15  # Lower - S3 costs not VPC-related
```

---

### Best Practices

#### 1. Config Organization
```
config/
├── aws25_campaign_config.yaml         # Reference template
├── lz_dev_q3_2025_config.yaml        # Dev account Q3
├── lz_prod_q3_2025_config.yaml       # Prod account Q3
└── org_wide_q3_2025_config.yaml      # Organization-wide
```

#### 2. Naming Conventions
- **Campaign ID**: `[SCOPE]-[NAME]-[TIME]` (e.g., `LZ-ACME-DEV-Q3-2025`)
- **Config File**: `[lz]_[account]_[period]_config.yaml`
- **Output File**: `[campaign_id]_savings.csv`

#### 3. Attribution Tuning
- **Single-VPC Accounts**: Increase attribution percentages (85% → 90%)
- **Multi-VPC Accounts**: Keep conservative defaults (70%, 30%)
- **EKS Clusters**: Increase vpc_related to 90%
- **S3-Heavy Workloads**: Decrease other_services to 15%

---

## Troubleshooting

### Cost Explorer Issues

#### Issue: VPC Not in Cost Explorer Results

**Symptom**: `$0.00` savings for VPCs known to have costs.

**Root Cause**: Cost Explorer provides account-level costs, cannot filter by VPC ID.

**Explanation**:

AWS Cost Explorer API does **not** support filtering by VPC ID. The framework uses:

1. **Account-level cost aggregation**: Total costs for entire AWS account
2. **Service-based filtering**: Costs grouped by AWS service (EC2, VPC, ELB, etc.)
3. **Conservative attribution methodology**: Infer VPC-specific costs from service patterns

**Attribution Methodology**:

| Service Category | Attribution % | Confidence | Logic |
|------------------|---------------|------------|-------|
| **VPC-specific** (Amazon VPC, PrivateLink) | 100% | HIGH (95%) | Directly attributable to VPC |
| **VPC-related** (EC2, ELB, Lambda) | 70% | MEDIUM (85%) | Likely VPC-related |
| **Other services** (S3, DynamoDB, etc.) | 30% | LOW (<85%) | May be VPC-related |

**Solution**: Results are lower-bound estimates. Review `Service_Analysis` column in CSV for breakdown.

---

#### Issue: Cost Explorer Data Retention Limit

**Error**:
```
ERROR: Cost data not available for date 2024-06-15
Cost Explorer retention: 13 months (395 days)
```

**Root Cause**: VPC deletion date older than Cost Explorer retention window.

**Cost Explorer Retention**: 13 months (395 days) from current date

**Solution**:

**Check Deletion Date**:
```bash
# Calculate days since deletion
deletion_date="2024-06-15"
current_date=$(date +%Y-%m-%d)
days_diff=$(( ($(date -jf "%Y-%m-%d" "$current_date" +%s) - $(date -jf "%Y-%m-%d" "$deletion_date" +%s)) / 86400 ))

echo "Days since deletion: $days_diff"
echo "Cost Explorer retention: 395 days"

if [ $days_diff -gt 395 ]; then
  echo "ERROR: Deletion date too old for Cost Explorer"
else
  echo "OK: Within Cost Explorer retention window"
fi
```

**Alternative Data Sources**:
- AWS Cost and Usage Reports (CUR) - 12-month+ retention
- CloudWatch Metrics - 15-month retention
- S3 exported billing reports

---

#### Issue: No Post-Deletion Data Available

**Error**:
```
WARNING: No post-deletion data available for vpc-abc123
VPC deleted 5 days ago, framework requires 30 days post-deletion
```

**Root Cause**: VPC deleted too recently for post-deletion analysis.

**Post-Deletion Requirements**:
- Default: 30 days of post-deletion data
- Minimum: 7 days for initial analysis

**Solution Options**:

**Option 1**: Adjust config to use fewer post-deletion days:
```yaml
cost_explorer_config:
  post_deletion_validation:
    granularity_daily: "DAILY"
    days_after_deletion: 7  # Reduced from 30
```

**Option 2**: Wait until sufficient post-deletion data available.

**Option 3**: Run preliminary analysis, re-run after 30 days:
```bash
# Preliminary analysis (7 days post-deletion)
python3 execute_cost_queries_boto3.py --config ../config/recent_deletion_config.yaml

# Re-run after 30 days (more accurate)
python3 execute_cost_queries_boto3.py --config ../config/recent_deletion_config.yaml
```

---

#### Issue: Cost Explorer Rate Limiting

**Error**:
```
ERROR: ThrottlingException - Rate exceeded for Cost Explorer API
```

**Root Cause**: Exceeded AWS Cost Explorer API rate limit (~5 requests/second).

**Framework Rate Limiting**: 0.3 seconds between queries (default).

**Solution**:

**Option 1**: Framework automatically handles rate limiting with delays.

**Option 2**: Increase delay in code:
```python
# In execute_cost_queries_boto3.py
RATE_LIMIT_DELAY = 0.5  # Increase from 0.3 to 0.5 seconds
```

**Option 3**: Retry after delay:
```bash
# If execution fails due to rate limiting
sleep 60  # Wait 1 minute
./run_vpc_savings_analysis.sh ../config/aws25_campaign_config.yaml
```

---

### Low Confidence Results

#### Issue: All VPCs Marked LOW Confidence (<85%)

**Symptom**: All VPCs in CSV have `LOW (<85%)` confidence level.

**Root Cause**: Multi-VPC accounts or increased post-deletion activity.

**Common Scenarios**:

1. **Multi-VPC Account**: Account has/had multiple VPCs, difficult to attribute costs to specific VPC
2. **Post-Deletion Activity Increase**: New infrastructure provisioned after VPC deletion
3. **Baseline Variability**: High cost fluctuation during pre-deletion period

**Review Notes Column**:
```csv
VPC_ID,Confidence_Level,Notes
vpc-abc123,LOW (<85%),"Multi-VPC account, other VPCs active during baseline"
vpc-def456,LOW (<85%),"Post-deletion costs increased (new EC2 instances launched)"
vpc-ghi789,LOW (<85%),"High baseline variability, seasonality detected"
```

**Solution Options**:

**Option 1**: Accept LOW confidence as lower-bound estimate.

**Option 2**: Cross-validate with CloudWatch metrics:
```bash
# Check EC2 instance count trend
AWS_PROFILE=your-profile aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name InstanceCount \
  --start-time 2025-07-01T00:00:00Z \
  --end-time 2025-10-01T00:00:00Z \
  --period 86400 \
  --statistics Average
```

**Option 3**: Manual validation with billing team for specific services.

---

#### Issue: VPC Deletion Savings Negative

**Symptom**: `Monthly_Savings_Realized: -$500.00` (negative savings).

**Root Cause**: Costs increased after VPC deletion.

**Common Scenarios**:

1. **New Infrastructure**: New resources provisioned post-deletion
2. **Cost Migration**: Costs migrated to other VPCs/accounts
3. **Baseline Noise**: Pre-deletion baseline was unusually low

**Framework Logic**: Reports negative savings (no zero-clamping).

**CSV Example**:
```csv
VPC_ID,Pre_Deletion_Monthly_Avg,Post_Deletion_Monthly_Avg,Monthly_Savings_Realized,Notes
vpc-abc123,$1000.00,$1500.00,-$500.00,"Costs increased post-deletion, new EC2 instances"
```

**Solution**:

1. **Review Service_Analysis Column**: Identify which services increased.
2. **Check CloudTrail for New Resources**: Post-deletion resource creation.
3. **Exclude from Savings Report**: Negative savings indicate no VPC-related savings.

---

### VPC Not Found in Results

#### Issue: VPC Missing from CSV Output

**Symptom**: Expected 6 VPCs, only 5 in CSV.

**Root Cause**: Query failed for specific VPC or cost data unavailable.

**Solution**:

**Check Logs/Console Output** for errors:
```bash
./run_vpc_savings_analysis.sh ../config/aws25_campaign_config.yaml 2>&1 | tee execution.log

# Search for errors
grep -i "error\|warning" execution.log
```

**Check JSON Results**:
```bash
# View raw Cost Explorer results
cat ../artifacts/cost_explorer_results.json | jq '.vpc_queries[] | select(.vpc_id == "vpc-abc123")'
```

**Verify VPC Deletion Date**:
```bash
# Query CloudTrail for exact deletion event
AWS_PROFILE=your-profile aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=vpc-abc123
```

---

### Common Error Messages Reference

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `AccessDeniedException` | No Cost Explorer permissions | Add IAM policy with ce:GetCostAndUsage |
| `NoCredentialsError` | AWS credentials not configured | Configure AWS profile |
| `InvalidVpcId` | VPC ID format invalid | Use vpc-* format |
| `ThrottlingException` | API rate limit exceeded | Framework retries automatically |
| `ValidationError` | YAML schema validation failed | Check required fields |
| `ExpiredTokenException` | STS credentials expired | Re-authenticate |

---

## Configuration Reference

### CLI Parameters

#### All Scripts Accept

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--config` | Path to campaign config YAML | `../config/aws25_campaign_config.yaml` |
| `--profile` | AWS profile override | From config `aws_billing_profile` |
| `--output-dir` | Output directory override | `../artifacts/` |

#### Script-Specific Parameters

**execute_cost_queries_boto3.py**:
- `--skip-queries`: Skip query execution, analyze existing results

**run_vpc_savings_analysis.sh**:
- First argument: Config file path (optional)
- Second argument: AWS profile override (optional)

---

### Advanced Configuration Examples

#### Custom Attribution Rules

Fine-tune confidence levels and attribution percentages:

```yaml
attribution_rules:
  vpc_specific_services:
    confidence_level: "HIGH (98%)"      # Custom confidence
    attribution_percentage: 95          # Conservative 95%
    service_patterns:
      - "Amazon Virtual Private Cloud"
      - "Amazon VPC"
      - "AWS PrivateLink"
      - "VPC Endpoint"                  # Add custom patterns
```

#### Custom Output Columns

Customize CSV output columns:

```yaml
output_config:
  csv_columns:
    - "VPC_ID"
    - "Account_ID"
    - "Region"                          # Add region
    - "Deletion_Principal"              # Add who deleted
    - "Monthly_Savings_Realized"
    - "Annual_Savings_Realized"
    - "Confidence_Level"
    - "Service_Analysis"                # Add detailed breakdown
```

---

**Optimization Recommendations**:
```
╭─ VPC Optimization Recommendations ─╮
│                                     │
│ 💰 Cost Savings Opportunities:      │
│ • Replace NAT Gateway with NAT      │
│   Instance: $372.60/month savings   │
│ • Remove 8 unused Elastic IPs:     │
│   $36.48/month savings             │
│ • Terminate idle Load Balancer:    │
│   $180.20/month savings            │
│                                     │
│ 🛠️  Implementation Priority:        │
│ 1. High Impact: NAT optimization    │
│ 2. Medium Impact: EIP cleanup       │
│ 3. Low Impact: LB consolidation     │
╰─────────────────────────────────────╯
```

### Multi-Account Operations

**Organization-Wide Analysis**:
```bash
# Analyze VPCs across AWS Organization
runbooks vpc analyze --organization-wide --profile management-account

# Cross-account cost comparison
runbooks vpc cost-comparison --accounts prod,dev,staging --profile management-account

# Organization security assessment
runbooks vpc security --organization-wide --profile management-account
```

---

## Configuration

### Configuration File Support

Create a `vpc_config.toml` file for centralized configuration:

```toml
# vpc_config.toml
[profiles]
production = "vpc-prod-profile"
development = "vpc-dev-profile"
management = "vpc-mgmt-profile"

[regions]
primary = ["ap-southeast-2", "ap-southeast-6"]
secondary = ["eu-west-1", "ap-southeast-2"]

[cost_analysis]
include_data_transfer = true
include_nat_gateway_hours = true
currency = "USD"

[optimization]
nat_gateway_threshold = 1000.0  # Monthly cost threshold
eip_unused_days = 7
load_balancer_idle_threshold = 0.01  # Request per minute

[security]
check_public_access = true
validate_flow_logs = true
assess_nacls = true

[output]
default_format = "table"
export_directory = "./vpc-reports"
```

**Using Configuration File**:
```bash
runbooks vpc analyze --config vpc_config.toml
```

### Environment-Specific Configuration

**Development Environment**:
```bash
runbooks vpc analyze --profile development --config dev_vpc.toml
```

**Production Environment**:
```bash  
runbooks vpc analyze --profile production --config prod_vpc.toml --security-analysis
```

---

## Export Formats

### JSON Output Format

```bash
runbooks vpc analyze --output-format json --output-file vpc_analysis.json --profile production
```

```json
{
  "vpc_analysis": {
    "timestamp": "2024-01-15T10:30:00Z",
    "account_id": "123456789012",
    "region": "ap-southeast-2",
    "total_vpcs": 5,
    "cost_analysis": {
      "total_monthly_cost": 2847.50,
      "nat_gateway_cost": 1245.60,
      "data_transfer_cost": 892.30,
      "load_balancer_cost": 709.60
    },
    "optimization_recommendations": [
      {
        "type": "nat_gateway_optimization",
        "potential_savings": 372.60,
        "priority": "high"
      }
    ]
  }
}
```

### CSV Output Format

```bash
runbooks vpc analyze --output-format csv --output-file vpc_analysis.csv --profile production
```

### HTML Report Format

```bash
runbooks vpc analyze --output-format html --output-file vpc_report.html --profile production
```

---

## 💰 VPC Cost Optimization Framework

### NAT Gateway Optimization

**30% Cost Savings Strategy**:
```bash
# Analyze NAT Gateway costs
runbooks vpc optimize --focus nat-gateways --profile production

# Implement NAT instance alternative
runbooks vpc optimize --implement nat-instance --profile production --dry-run
```

### Resource Cleanup

**Unused Resource Management**:
```bash
# Identify unused Elastic IPs
runbooks vpc cleanup --resource-type eip --profile production

# Clean up unused security groups
runbooks vpc cleanup --resource-type security-groups --profile production --dry-run
```

### Multi-Account Cost Comparison

**Enterprise Cost Management**:
```bash
# Compare costs across accounts
runbooks vpc cost-comparison --accounts all --profile management-account

# Generate executive cost report
runbooks vpc cost-report --format executive --profile management-account
```

---

## Integration with Other Modules

### FinOps Integration

**Combined Cost Analysis**:
```bash
# Run VPC analysis alongside FinOps dashboard
runbooks vpc analyze --profile production --integration finops

# Export for FinOps dashboard consumption
runbooks vpc analyze --output-format json --finops-compatible --profile production
```

### Security Module Integration

**Comprehensive Security Assessment**:
```bash
# Combined VPC and security baseline analysis
runbooks vpc analyze --security-analysis --integration security --profile production
```

---

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](../../../CONTRIBUTING.md) for details.

### Development Setup
```bash
git clone https://github.com/1xOps/CloudOps-Runbooks.git
cd CloudOps-Runbooks
uv sync --all-extras
uv run python -m runbooks vpc --help
```

### Running Tests
```bash
uv run pytest tests/vpc/ -v
```

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](../../../LICENSE) file for details.

---

## Enterprise Support

For enterprise support, professional services, and custom integrations:
- **Email**: [info@oceansoft.io](mailto:info@oceansoft.io)
- **GitHub**: [Runbooks Issues](https://github.com/1xOps/CloudOps-Runbooks/issues)
- **Documentation**: [Enterprise VPC Documentation](https://docs.cloudops-runbooks.io/vpc)

Let's optimize your AWS networking costs together. 🚀