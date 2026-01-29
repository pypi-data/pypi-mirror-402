#!/usr/bin/env python3
"""
Advanced Cost Optimization Engine for Enhanced FinOps Dashboard

This module provides sophisticated cost optimization analysis with:
- Service-specific optimization recommendations with actual cost impact
- ROI calculations and payback period analysis
- Priority scoring based on business impact
- Implementation guidance with specific action steps
- Risk assessment and implementation complexity scoring
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import boto3
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass
class OptimizationRecommendation:
    """Enhanced optimization recommendation with business context"""

    service_name: str
    resource_type: str
    current_monthly_cost: float
    potential_monthly_savings: float
    potential_annual_savings: float
    confidence_level: str  # HIGH, MEDIUM, LOW
    priority_score: int  # 1-10 (10 = highest priority)
    implementation_complexity: str  # SIMPLE, MODERATE, COMPLEX
    risk_level: str  # LOW, MEDIUM, HIGH
    payback_period_months: int
    roi_percentage: float
    description: str
    action_steps: List[str]
    business_impact: str
    resource_count: int = 0
    tags: Optional[Dict] = None


@dataclass
class ServiceOptimizationResults:
    """Results for a specific service optimization analysis"""

    service_name: str
    total_monthly_cost: float
    total_potential_savings: float
    recommendations: List[OptimizationRecommendation]
    optimization_percentage: float
    priority_actions: List[str]


class AdvancedOptimizationEngine:
    """
    Advanced cost optimization engine providing detailed, actionable recommendations
    with business impact analysis and implementation guidance.
    """

    def __init__(self, profile: str):
        self.profile = profile
        self.console = Console()

        # Service optimization strategies
        self.service_optimizers = {
            "ec2": self._optimize_ec2_recommendations,
            "rds": self._optimize_rds_recommendations,
            "s3": self._optimize_s3_recommendations,
            "lambda": self._optimize_lambda_recommendations,
            "cloudwatch": self._optimize_cloudwatch_recommendations,
            "dynamodb": self._optimize_dynamodb_recommendations,
            "ebs": self._optimize_ebs_recommendations,
            "nat_gateway": self._optimize_nat_gateway_recommendations,
            "data_transfer": self._optimize_data_transfer_recommendations,
            "savings_plans": self._optimize_savings_plans_recommendations,
        }

    def analyze_service_optimization(
        self, service_name: str, monthly_cost: float, previous_cost: float = 0.0
    ) -> ServiceOptimizationResults:
        """
        Analyze optimization opportunities for a specific service
        """
        service_key = self._normalize_service_name(service_name)

        if service_key in self.service_optimizers:
            return self.service_optimizers[service_key](service_name, monthly_cost, previous_cost)
        else:
            return self._generic_service_optimization(service_name, monthly_cost, previous_cost)

    def _normalize_service_name(self, service_name: str) -> str:
        """Normalize service names to match our optimization strategies"""
        service_lower = service_name.lower()

        if "ec2" in service_lower or "elastic compute" in service_lower:
            return "ec2"
        elif "rds" in service_lower or "database" in service_lower:
            return "rds"
        elif "s3" in service_lower or "simple storage" in service_lower:
            return "s3"
        elif "lambda" in service_lower:
            return "lambda"
        elif "cloudwatch" in service_lower:
            return "cloudwatch"
        elif "dynamodb" in service_lower:
            return "dynamodb"
        elif "nat" in service_lower and "gateway" in service_lower:
            return "nat_gateway"
        elif "data transfer" in service_lower or "bandwidth" in service_lower:
            return "data_transfer"
        elif "savings plan" in service_lower:
            return "savings_plans"
        elif "ebs" in service_lower or "elastic block" in service_lower:
            return "ebs"
        else:
            return "generic"

    def _optimize_ec2_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """EC2-specific optimization recommendations"""
        recommendations = []

        # High-cost EC2 optimizations
        if monthly_cost > 5000:
            # Reserved Instances recommendation
            reserved_savings = monthly_cost * 0.30  # 30% typical RI savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Reserved Instances",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=reserved_savings,
                    potential_annual_savings=reserved_savings * 12,
                    confidence_level="HIGH",
                    priority_score=9,
                    implementation_complexity="SIMPLE",
                    risk_level="LOW",
                    payback_period_months=0,  # Immediate savings
                    roi_percentage=30.0,
                    description=f"Convert {monthly_cost / 200:.0f} On-Demand instances to Reserved Instances",
                    action_steps=[
                        "1. Analyze instance usage patterns over past 3 months",
                        "2. Identify steady-state instances running >75% of time",
                        "3. Purchase 1-year Standard RIs for consistent workloads",
                        "4. Consider 3-year RIs for long-term stable workloads",
                        "5. Monitor RI utilization and adjust as needed",
                    ],
                    business_impact=f"Immediate cost reduction of ${reserved_savings:,.0f}/month with guaranteed savings",
                    resource_count=int(monthly_cost / 200),  # Assume $200/month per instance
                )
            )

            # Right-sizing recommendation
            rightsizing_savings = monthly_cost * 0.15  # 15% typical rightsizing
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Instance Right-sizing",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=rightsizing_savings,
                    potential_annual_savings=rightsizing_savings * 12,
                    confidence_level="MEDIUM",
                    priority_score=7,
                    implementation_complexity="MODERATE",
                    risk_level="MEDIUM",
                    payback_period_months=1,
                    roi_percentage=15.0,
                    description="Right-size over-provisioned EC2 instances based on utilization",
                    action_steps=[
                        "1. Enable CloudWatch detailed monitoring for all instances",
                        "2. Collect CPU, memory, and network utilization for 14 days",
                        "3. Identify instances with <40% average CPU utilization",
                        "4. Test smaller instance types in staging environment",
                        "5. Implement changes during maintenance windows",
                    ],
                    business_impact=f"Reduce monthly spend by ${rightsizing_savings:,.0f} through optimal instance sizing",
                    resource_count=int(monthly_cost / 200 * 0.3),  # 30% of instances could be rightsized
                )
            )

        # Spot instance recommendation for appropriate workloads
        if monthly_cost > 1000:
            spot_savings = monthly_cost * 0.60  # 60% typical spot savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Spot Instances",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=spot_savings,
                    potential_annual_savings=spot_savings * 12,
                    confidence_level="MEDIUM",
                    priority_score=6,
                    implementation_complexity="COMPLEX",
                    risk_level="HIGH",
                    payback_period_months=0,
                    roi_percentage=60.0,
                    description="Migrate fault-tolerant workloads to EC2 Spot Instances",
                    action_steps=[
                        "1. Identify stateless, fault-tolerant applications",
                        "2. Implement auto-scaling with mixed instance types",
                        "3. Set up spot fleet requests with multiple AZs",
                        "4. Create spot instance interruption handling",
                        "5. Monitor spot pricing trends and optimize bidding",
                    ],
                    business_impact=f"Up to ${spot_savings:,.0f}/month savings for suitable workloads",
                    resource_count=int(monthly_cost / 200 * 0.2),  # 20% suitable for spot
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "🎯 Start with Reserved Instance analysis - highest ROI, lowest risk",
            "📊 Enable detailed monitoring to identify rightsizing opportunities",
            "⚡ Evaluate spot instances for development and batch workloads",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_s3_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """S3-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 500:
            # Intelligent Tiering
            tiering_savings = monthly_cost * 0.25  # 25% typical savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Intelligent Tiering",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=tiering_savings,
                    potential_annual_savings=tiering_savings * 12,
                    confidence_level="HIGH",
                    priority_score=8,
                    implementation_complexity="SIMPLE",
                    risk_level="LOW",
                    payback_period_months=1,
                    roi_percentage=25.0,
                    description="Enable S3 Intelligent Tiering for automatic cost optimization",
                    action_steps=[
                        "1. Analyze storage access patterns using S3 Storage Lens",
                        "2. Enable Intelligent Tiering for buckets >128KB objects",
                        "3. Set up lifecycle policies for infrequent access data",
                        "4. Monitor tiering effectiveness monthly",
                        "5. Consider Deep Archive for compliance data",
                    ],
                    business_impact=f"Automatic storage optimization saving ${tiering_savings:,.0f}/month",
                    resource_count=0,
                )
            )

            # Lifecycle policies
            lifecycle_savings = monthly_cost * 0.30  # 30% savings potential
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Lifecycle Management",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=lifecycle_savings,
                    potential_annual_savings=lifecycle_savings * 12,
                    confidence_level="MEDIUM",
                    priority_score=7,
                    implementation_complexity="MODERATE",
                    risk_level="LOW",
                    payback_period_months=2,
                    roi_percentage=30.0,
                    description="Implement comprehensive lifecycle policies for data archival",
                    action_steps=[
                        "1. Audit data access patterns over 6 months",
                        "2. Define retention policies by data type",
                        "3. Create lifecycle rules: IA (30d), Glacier (90d), Deep Archive (365d)",
                        "4. Test policies on non-critical buckets first",
                        "5. Monitor cost impact and adjust rules",
                    ],
                    business_impact=f"Long-term storage optimization saving ${lifecycle_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "📦 Enable S3 Intelligent Tiering for immediate automated savings",
            "🔄 Implement lifecycle policies for long-term cost control",
            "📊 Use S3 Storage Lens for usage pattern analysis",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_rds_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """RDS-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 2000:
            # Reserved Instances for RDS
            rds_ri_savings = monthly_cost * 0.35  # 35% typical RDS RI savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="RDS Reserved Instances",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=rds_ri_savings,
                    potential_annual_savings=rds_ri_savings * 12,
                    confidence_level="HIGH",
                    priority_score=9,
                    implementation_complexity="SIMPLE",
                    risk_level="LOW",
                    payback_period_months=0,
                    roi_percentage=35.0,
                    description="Purchase RDS Reserved Instances for production databases",
                    action_steps=[
                        "1. Identify production RDS instances with consistent usage",
                        "2. Analyze historical utilization patterns",
                        "3. Purchase 1-year RDS RIs for stable workloads",
                        "4. Consider 3-year RIs for long-term databases",
                        "5. Monitor RI utilization and coverage",
                    ],
                    business_impact=f"Immediate database cost reduction of ${rds_ri_savings:,.0f}/month",
                    resource_count=int(monthly_cost / 400),  # Assume $400/month per DB instance
                )
            )

            # Right-sizing databases
            db_rightsizing = monthly_cost * 0.20  # 20% rightsizing potential
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Database Right-sizing",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=db_rightsizing,
                    potential_annual_savings=db_rightsizing * 12,
                    confidence_level="MEDIUM",
                    priority_score=7,
                    implementation_complexity="COMPLEX",
                    risk_level="HIGH",
                    payback_period_months=2,
                    roi_percentage=20.0,
                    description="Right-size RDS instances based on performance metrics",
                    action_steps=[
                        "1. Enable Enhanced Monitoring for all RDS instances",
                        "2. Analyze CPU, memory, and I/O utilization for 30 days",
                        "3. Identify over-provisioned instances (<60% utilization)",
                        "4. Test smaller instance types in staging environment",
                        "5. Schedule maintenance windows for production changes",
                    ],
                    business_impact=f"Optimize database performance and costs by ${db_rightsizing:,.0f}/month",
                    resource_count=int(monthly_cost / 400 * 0.3),
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "🗄️ Analyze RDS Reserved Instance opportunities for production workloads",
            "📊 Enable Enhanced Monitoring for performance analysis",
            "⚡ Consider Aurora Serverless for variable workloads",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_nat_gateway_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """NAT Gateway-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 200:
            # NAT Instance alternative
            nat_instance_savings = monthly_cost * 0.60  # 60% savings with NAT instances
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="NAT Instance Migration",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=nat_instance_savings,
                    potential_annual_savings=nat_instance_savings * 12,
                    confidence_level="MEDIUM",
                    priority_score=6,
                    implementation_complexity="COMPLEX",
                    risk_level="MEDIUM",
                    payback_period_months=1,
                    roi_percentage=60.0,
                    description="Migrate from NAT Gateway to NAT Instances for cost optimization",
                    action_steps=[
                        "1. Assess current NAT Gateway usage and requirements",
                        "2. Design high-availability NAT instance architecture",
                        "3. Create auto-scaling NAT instance solution",
                        "4. Test failover and performance scenarios",
                        "5. Migrate during maintenance window with rollback plan",
                    ],
                    business_impact=f"Reduce networking costs by ${nat_instance_savings:,.0f}/month",
                    resource_count=int(monthly_cost / 45),  # ~$45/month per NAT Gateway
                )
            )

            # VPC Endpoint optimization
            vpc_endpoint_savings = monthly_cost * 0.30  # 30% data transfer savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="VPC Endpoints",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=vpc_endpoint_savings,
                    potential_annual_savings=vpc_endpoint_savings * 12,
                    confidence_level="HIGH",
                    priority_score=7,
                    implementation_complexity="MODERATE",
                    risk_level="LOW",
                    payback_period_months=2,
                    roi_percentage=30.0,
                    description="Implement VPC Endpoints to reduce NAT Gateway data transfer",
                    action_steps=[
                        "1. Identify high-traffic AWS services (S3, DynamoDB, etc.)",
                        "2. Create VPC endpoints for frequently accessed services",
                        "3. Update route tables and security groups",
                        "4. Monitor data transfer cost reduction",
                        "5. Expand VPC endpoints to additional services",
                    ],
                    business_impact=f"Reduce data transfer costs by ${vpc_endpoint_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "🌐 Implement VPC Endpoints for AWS services to reduce data transfer",
            "🔀 Evaluate NAT Instance alternative for high-traffic scenarios",
            "📊 Monitor data transfer patterns for optimization opportunities",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_lambda_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """Lambda-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 100:
            # Memory optimization
            memory_savings = monthly_cost * 0.25  # 25% potential savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Memory Optimization",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=memory_savings,
                    potential_annual_savings=memory_savings * 12,
                    confidence_level="HIGH",
                    priority_score=8,
                    implementation_complexity="SIMPLE",
                    risk_level="LOW",
                    payback_period_months=0,
                    roi_percentage=25.0,
                    description="Optimize Lambda memory allocation for cost and performance",
                    action_steps=[
                        "1. Enable AWS Lambda Power Tuning for all functions",
                        "2. Analyze CloudWatch metrics for memory utilization",
                        "3. Test different memory configurations",
                        "4. Implement optimal memory settings",
                        "5. Monitor performance and cost impact",
                    ],
                    business_impact=f"Optimize Lambda performance and costs by ${memory_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "⚡ Use AWS Lambda Power Tuning for memory optimization",
            "📊 Monitor invocation patterns and duration metrics",
            "🔄 Consider Provisioned Concurrency for consistent workloads",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_cloudwatch_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """CloudWatch-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 100:
            # Log retention optimization
            log_savings = monthly_cost * 0.40  # 40% potential savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Log Retention Optimization",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=log_savings,
                    potential_annual_savings=log_savings * 12,
                    confidence_level="HIGH",
                    priority_score=7,
                    implementation_complexity="SIMPLE",
                    risk_level="LOW",
                    payback_period_months=0,
                    roi_percentage=40.0,
                    description="Optimize CloudWatch Logs retention policies",
                    action_steps=[
                        "1. Audit all CloudWatch Log Groups and retention settings",
                        "2. Define appropriate retention periods by log type",
                        "3. Update retention policies (30-90 days for most logs)",
                        "4. Archive critical logs to S3 for long-term retention",
                        "5. Monitor log ingestion costs monthly",
                    ],
                    business_impact=f"Reduce CloudWatch costs by ${log_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "📋 Review and optimize log retention policies",
            "📊 Use CloudWatch Insights for log analysis efficiency",
            "💾 Archive historical logs to S3 for compliance",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_dynamodb_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """DynamoDB-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 200:
            # On-Demand vs Provisioned optimization
            pricing_savings = monthly_cost * 0.25  # 25% potential savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Pricing Model Optimization",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=pricing_savings,
                    potential_annual_savings=pricing_savings * 12,
                    confidence_level="MEDIUM",
                    priority_score=6,
                    implementation_complexity="MODERATE",
                    risk_level="MEDIUM",
                    payback_period_months=1,
                    roi_percentage=25.0,
                    description="Optimize DynamoDB pricing model (On-Demand vs Provisioned)",
                    action_steps=[
                        "1. Analyze read/write capacity utilization patterns",
                        "2. Compare On-Demand vs Provisioned costs for each table",
                        "3. Switch to Provisioned for predictable workloads",
                        "4. Use Auto Scaling for variable workloads",
                        "5. Monitor and adjust capacity settings monthly",
                    ],
                    business_impact=f"Optimize DynamoDB costs by ${pricing_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "📊 Analyze read/write patterns for pricing optimization",
            "🔄 Enable Auto Scaling for Provisioned tables",
            "💾 Consider DynamoDB Standard-IA for infrequent access data",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_ebs_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """EBS-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 300:
            # EBS volume optimization
            volume_savings = monthly_cost * 0.30  # 30% potential savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Volume Type Optimization",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=volume_savings,
                    potential_annual_savings=volume_savings * 12,
                    confidence_level="HIGH",
                    priority_score=7,
                    implementation_complexity="MODERATE",
                    risk_level="LOW",
                    payback_period_months=1,
                    roi_percentage=30.0,
                    description="Optimize EBS volume types and eliminate unused volumes",
                    action_steps=[
                        "1. Identify unused and unattached EBS volumes",
                        "2. Analyze IOPS requirements vs volume types",
                        "3. Migrate gp2 to gp3 volumes for cost savings",
                        "4. Delete snapshots older than retention policy",
                        "5. Implement automated volume cleanup",
                    ],
                    business_impact=f"Reduce storage costs by ${volume_savings:,.0f}/month",
                    resource_count=int(monthly_cost / 8),  # ~$8/month per 100GB gp3
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "💾 Migrate gp2 volumes to gp3 for immediate cost savings",
            "🗑️ Clean up unused volumes and old snapshots",
            "📊 Right-size volumes based on actual usage patterns",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_data_transfer_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """Data Transfer-specific optimization recommendations"""
        recommendations = []

        if monthly_cost > 500:
            # CloudFront optimization
            cdn_savings = monthly_cost * 0.50  # 50% potential savings
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="CloudFront CDN",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=cdn_savings,
                    potential_annual_savings=cdn_savings * 12,
                    confidence_level="HIGH",
                    priority_score=8,
                    implementation_complexity="MODERATE",
                    risk_level="LOW",
                    payback_period_months=1,
                    roi_percentage=50.0,
                    description="Implement CloudFront CDN to reduce data transfer costs",
                    action_steps=[
                        "1. Analyze data transfer patterns and geographic distribution",
                        "2. Configure CloudFront distributions for static content",
                        "3. Implement caching strategies for dynamic content",
                        "4. Optimize origin request patterns",
                        "5. Monitor CloudFront vs direct transfer costs",
                    ],
                    business_impact=f"Reduce data transfer costs by ${cdn_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "🌐 Implement CloudFront CDN for frequently accessed content",
            "🔗 Use VPC Endpoints to avoid internet data transfer charges",
            "📊 Monitor and optimize cross-region data transfer patterns",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _optimize_savings_plans_recommendations(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """Savings Plans optimization recommendations"""
        recommendations = []

        if monthly_cost > 5000:
            # Additional Savings Plans coverage
            additional_savings = monthly_cost * 0.20  # 20% additional potential
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="Enhanced Savings Plans",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=additional_savings,
                    potential_annual_savings=additional_savings * 12,
                    confidence_level="HIGH",
                    priority_score=9,
                    implementation_complexity="SIMPLE",
                    risk_level="LOW",
                    payback_period_months=0,
                    roi_percentage=20.0,
                    description="Optimize Savings Plans coverage and commitment levels",
                    action_steps=[
                        "1. Analyze current Savings Plans utilization and coverage",
                        "2. Review Cost Explorer recommendations for additional plans",
                        "3. Consider EC2 Instance Savings Plans for specific workloads",
                        "4. Purchase additional Compute Savings Plans if coverage <80%",
                        "5. Monitor utilization and adjust future purchases",
                    ],
                    business_impact=f"Additional savings of ${additional_savings:,.0f}/month through optimized coverage",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            "📊 Review Savings Plans utilization and coverage regularly",
            "💰 Consider 3-year commitments for stable long-term workloads",
            "🔄 Use Cost Explorer recommendations for optimal planning",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def _generic_service_optimization(
        self, service_name: str, monthly_cost: float, previous_cost: float
    ) -> ServiceOptimizationResults:
        """Generic optimization recommendations for services without specific strategies"""
        recommendations = []

        if monthly_cost > 100:
            # General optimization
            generic_savings = monthly_cost * 0.15  # 15% generic potential
            recommendations.append(
                OptimizationRecommendation(
                    service_name=service_name,
                    resource_type="General Optimization",
                    current_monthly_cost=monthly_cost,
                    potential_monthly_savings=generic_savings,
                    potential_annual_savings=generic_savings * 12,
                    confidence_level="MEDIUM",
                    priority_score=5,
                    implementation_complexity="MODERATE",
                    risk_level="MEDIUM",
                    payback_period_months=2,
                    roi_percentage=15.0,
                    description=f"Review {service_name} usage patterns and optimize configuration",
                    action_steps=[
                        "1. Review service usage patterns and metrics",
                        "2. Identify unused or underutilized resources",
                        "3. Optimize service configuration settings",
                        "4. Consider alternative pricing models if available",
                        "5. Monitor and adjust based on performance impact",
                    ],
                    business_impact=f"Potential optimization savings of ${generic_savings:,.0f}/month",
                    resource_count=0,
                )
            )

        total_potential = sum(rec.potential_monthly_savings for rec in recommendations)
        optimization_percentage = (total_potential / monthly_cost * 100) if monthly_cost > 0 else 0

        priority_actions = [
            f"📊 Analyze {service_name} usage patterns for optimization opportunities",
            "🔍 Review AWS documentation for service-specific best practices",
            "💡 Consider AWS Trusted Advisor recommendations",
        ]

        return ServiceOptimizationResults(
            service_name=service_name,
            total_monthly_cost=monthly_cost,
            total_potential_savings=total_potential,
            recommendations=recommendations,
            optimization_percentage=optimization_percentage,
            priority_actions=priority_actions,
        )

    def create_optimization_summary_table(self, optimization_results: List[ServiceOptimizationResults]) -> Table:
        """Create a Rich table summarizing optimization opportunities across all services"""

        table = Table(
            title="💰 Comprehensive Optimization Opportunities",
            show_header=True,
            header_style="bold cyan",
            show_lines=True,
        )

        table.add_column("Service", style="white", width=15)
        table.add_column("Current Cost", style="yellow", width=12, justify="right")
        table.add_column("Potential Savings", style="green", width=15, justify="right")
        table.add_column("Optimization %", style="bright_green", width=12, justify="center")
        table.add_column("Top Priority Action", style="cyan", width=40)

        total_current = 0
        total_savings = 0

        # Sort by potential savings (highest first)
        sorted_results = sorted(optimization_results, key=lambda x: x.total_potential_savings, reverse=True)

        for result in sorted_results:
            if result.total_potential_savings > 0:  # Only show services with optimization potential
                total_current += result.total_monthly_cost
                total_savings += result.total_potential_savings

                # Get the highest priority action
                top_action = result.priority_actions[0] if result.priority_actions else "Review usage patterns"

                table.add_row(
                    result.service_name,
                    f"${result.total_monthly_cost:,.0f}",
                    f"${result.total_potential_savings:,.0f}",
                    f"{result.optimization_percentage:.1f}%",
                    top_action,
                )

        # Add summary row
        if total_current > 0:
            overall_percentage = total_savings / total_current * 100
            table.add_row(
                "[bold]TOTAL[/bold]",
                f"[bold]${total_current:,.0f}[/bold]",
                f"[bold green]${total_savings:,.0f}[/bold green]",
                f"[bold green]{overall_percentage:.1f}%[/bold green]",
                f"[bold]Annual Potential: ${total_savings * 12:,.0f}[/bold]",
            )

        return table

    def create_priority_recommendations_panel(self, optimization_results: List[ServiceOptimizationResults]) -> Panel:
        """Create a Rich panel with top priority recommendations"""

        # Collect all recommendations and sort by priority score and savings
        all_recommendations = []
        for result in optimization_results:
            all_recommendations.extend(result.recommendations)

        # Sort by priority score (highest first), then by savings
        top_recommendations = sorted(
            all_recommendations, key=lambda x: (x.priority_score, x.potential_monthly_savings), reverse=True
        )[:10]  # Top 10 recommendations

        content = "[bold cyan]🎯 Top 10 Priority Optimization Actions[/bold cyan]\n\n"

        for i, rec in enumerate(top_recommendations, 1):
            priority_color = "red" if rec.priority_score >= 8 else "yellow" if rec.priority_score >= 6 else "green"
            risk_emoji = "🔴" if rec.risk_level == "HIGH" else "🟡" if rec.risk_level == "MEDIUM" else "🟢"
            complexity_emoji = (
                "🔧"
                if rec.implementation_complexity == "SIMPLE"
                else "⚙️"
                if rec.implementation_complexity == "MODERATE"
                else "🛠️"
            )

            content += (
                f"[bold {priority_color}]{i:2d}. {rec.description}[/bold {priority_color}]\n"
                f"    💰 Monthly Savings: [green]${rec.potential_monthly_savings:,.0f}[/green] "
                f"| 📅 ROI: [bright_green]{rec.roi_percentage:.0f}%[/bright_green] "
                f"| {risk_emoji} Risk: {rec.risk_level} "
                f"| {complexity_emoji} {rec.implementation_complexity}\n"
                f"    🎯 Next Step: {rec.action_steps[0] if rec.action_steps else 'Review implementation plan'}\n\n"
            )

        return Panel(content, title="🚀 Implementation Roadmap", style="bright_cyan")


def create_enhanced_optimization_display(cost_data: Dict[str, float], profile: str = "default") -> None:
    """
    Create enhanced optimization display for the FinOps dashboard
    """
    console.print("\n[bold cyan]🔍 Advanced Cost Optimization Analysis[/bold cyan]")

    # Initialize optimization engine
    optimizer = AdvancedOptimizationEngine(profile)

    # Analyze each service
    optimization_results = []
    for service_name, monthly_cost in cost_data.items():
        if monthly_cost > 0:  # Only analyze services with costs
            result = optimizer.analyze_service_optimization(service_name, monthly_cost)
            optimization_results.append(result)

    # Display optimization summary table
    if optimization_results:
        summary_table = optimizer.create_optimization_summary_table(optimization_results)
        console.print(summary_table)

        # Display priority recommendations
        priority_panel = optimizer.create_priority_recommendations_panel(optimization_results)
        console.print(priority_panel)

        # Calculate and display total business impact
        total_monthly_savings = sum(result.total_potential_savings for result in optimization_results)
        total_annual_savings = total_monthly_savings * 12

        if total_monthly_savings > 0:
            business_impact_panel = Panel.fit(
                f"[bold green]💼 Total Business Impact[/bold green]\n\n"
                f"💰 Monthly Optimization Potential: [yellow]${total_monthly_savings:,.0f}[/yellow]\n"
                f"📅 Annual Savings Potential: [bright_green]${total_annual_savings:,.0f}[/bright_green]\n"
                f"🎯 Implementation Priority: Start with highest ROI, lowest risk actions\n"
                f"⏱️ Estimated Implementation Time: 2-6 weeks for top recommendations",
                title="🚀 Executive Summary",
                style="bright_green",
            )
            console.print(business_impact_panel)

    else:
        console.print("[yellow]📊 No significant optimization opportunities identified in current cost data[/yellow]")
