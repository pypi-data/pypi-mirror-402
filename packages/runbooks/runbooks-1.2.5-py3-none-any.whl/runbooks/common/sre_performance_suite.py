#!/usr/bin/env python3
"""
SRE Performance Optimization Suite - Comprehensive Performance Enhancement

🎯 Enterprise SRE Automation Specialist Implementation
Following proven systematic delegation patterns for production reliability optimization.

This suite integrates all performance optimizations identified from PDCA analysis:

CRITICAL PERFORMANCE BOTTLENECKS ADDRESSED:
1. Organization Discovery Performance: 52.3s -> <30s target
2. VPC Analysis Timeout Issues: Network operations optimization
3. Memory Usage Optimization: Large-scale operation memory management
4. Concurrent Processing: Multi-account parallel processing with rate limiting

ENTERPRISE FEATURES:
- Unified performance monitoring dashboard
- Intelligent caching with TTL management
- Connection pooling for AWS API calls
- Memory-efficient batch processing
- Progress indicators for long-running operations
- Automatic retry with exponential backoff
- Performance degradation detection and alerting
- Comprehensive metrics collection and reporting
"""

import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.layout import Layout
from rich.live import Live

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_warning,
    print_error,
    create_table,
    STATUS_INDICATORS,
)

from runbooks.common.performance_optimization_engine import (
    PerformanceOptimizationEngine,
    OptimizationMetrics,
    get_optimization_engine,
)

from runbooks.common.memory_optimization import MemoryOptimizer, get_memory_optimizer

from runbooks.common.performance_monitor import PerformanceBenchmark, get_performance_benchmark

logger = logging.getLogger(__name__)


@dataclass
class SREPerformanceMetrics:
    """Comprehensive SRE performance metrics"""

    operation_name: str
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    target_duration_seconds: float = 30.0

    # Performance optimization metrics
    optimization_metrics: Optional[OptimizationMetrics] = None
    memory_peak_mb: float = 0.0
    memory_saved_mb: float = 0.0

    # Infrastructure metrics
    aws_api_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    parallel_workers_used: int = 0

    # Success metrics
    success: bool = False
    error_message: Optional[str] = None
    performance_grade: str = "F"
    optimizations_applied: List[str] = field(default_factory=list)

    def calculate_performance_improvement(self) -> float:
        """Calculate performance improvement percentage"""
        if self.target_duration_seconds <= 0 or self.total_duration_seconds <= 0:
            return 0.0
        return max(0, (self.target_duration_seconds - self.total_duration_seconds) / self.target_duration_seconds * 100)

    def get_cache_efficiency(self) -> float:
        """Calculate cache efficiency percentage"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0


class SREPerformanceSuite:
    """
    Comprehensive SRE performance optimization suite

    Integrates all performance optimization components:
    - Performance optimization engine for AWS API optimization
    - Memory optimization for large-scale operations
    - Performance monitoring and benchmarking
    - Real-time performance dashboard
    - Automated performance reporting
    """

    def __init__(
        self,
        max_workers: int = 20,
        memory_limit_mb: int = 2048,
        cache_ttl_minutes: int = 30,
        performance_target_seconds: float = 30.0,
    ):
        """
        Initialize comprehensive SRE performance suite

        Args:
            max_workers: Maximum concurrent workers for parallel operations
            memory_limit_mb: Memory usage limit in MB
            cache_ttl_minutes: Cache TTL in minutes
            performance_target_seconds: Default performance target in seconds
        """
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb
        self.cache_ttl_minutes = cache_ttl_minutes
        self.performance_target_seconds = performance_target_seconds

        # Initialize optimization components
        self.optimization_engine = get_optimization_engine(
            max_workers=max_workers, cache_ttl_minutes=cache_ttl_minutes, memory_limit_mb=memory_limit_mb
        )

        self.memory_optimizer = get_memory_optimizer(
            warning_threshold_mb=memory_limit_mb * 0.7, critical_threshold_mb=memory_limit_mb * 0.9
        )

        # Performance tracking
        self.performance_metrics: List[SREPerformanceMetrics] = []
        self.current_operation: Optional[SREPerformanceMetrics] = None

    @contextmanager
    def optimized_operation(
        self,
        operation_name: str,
        target_seconds: Optional[float] = None,
        enable_memory_monitoring: bool = True,
        enable_caching: bool = True,
    ):
        """
        Context manager for comprehensive SRE-optimized operations

        Integrates:
        - Performance optimization engine
        - Memory optimization and monitoring
        - Performance benchmarking
        - Real-time metrics collection
        """
        target = target_seconds or self.performance_target_seconds

        # Initialize comprehensive metrics
        metrics = SREPerformanceMetrics(operation_name=operation_name, target_duration_seconds=target)
        self.current_operation = metrics

        # Start all optimization components
        with self.optimization_engine.optimize_operation(operation_name, target) as opt_metrics:
            with self.memory_optimizer.optimize_memory_usage(operation_name, enable_memory_monitoring) as mem_metrics:
                # Start performance benchmark
                benchmark = get_performance_benchmark("sre_suite")

                with benchmark.measure_operation(operation_name, show_progress=True) as perf_metrics:
                    try:
                        console.log(f"[cyan]🚀 SRE-optimized operation: {operation_name} (target: {target}s)[/cyan]")

                        yield metrics

                        # Operation succeeded - collect metrics
                        metrics.end_time = datetime.now(timezone.utc)
                        metrics.total_duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
                        metrics.success = True

                        # Collect optimization metrics
                        metrics.optimization_metrics = opt_metrics
                        metrics.memory_peak_mb = mem_metrics.memory_peak_mb
                        metrics.memory_saved_mb = mem_metrics.memory_saved_mb
                        metrics.optimizations_applied = list(
                            set(opt_metrics.optimization_applied + mem_metrics.optimization_techniques_applied)
                        )

                        # Calculate performance grade
                        improvement = metrics.calculate_performance_improvement()
                        if improvement >= 20:
                            metrics.performance_grade = "A"
                        elif improvement >= 10:
                            metrics.performance_grade = "B"
                        elif metrics.total_duration_seconds <= target:
                            metrics.performance_grade = "C"
                        else:
                            metrics.performance_grade = "D"

                        self._log_comprehensive_results(metrics)

                    except Exception as e:
                        # Handle operation failure
                        metrics.end_time = datetime.now(timezone.utc)
                        metrics.total_duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
                        metrics.success = False
                        metrics.error_message = str(e)
                        metrics.performance_grade = "F"

                        print_error(f"SRE-optimized operation failed: {operation_name}", e)
                        raise

                    finally:
                        # Store metrics and cleanup
                        self.performance_metrics.append(metrics)
                        self.current_operation = None

    async def optimize_organization_discovery(
        self, management_profile: str, target_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Optimize organization discovery with comprehensive SRE patterns

        Addresses: Organization Discovery Performance (52.3s -> <30s target)
        """
        with self.optimized_operation("organization_discovery_optimization", target_seconds):
            # Use optimized discovery function from performance engine
            optimized_discovery = self.optimization_engine.optimize_organization_discovery(
                management_profile=management_profile, use_parallel_processing=True, batch_size=20
            )

            # Execute optimized discovery
            result = optimized_discovery()

            # Update metrics
            if self.current_operation:
                self.current_operation.aws_api_calls = result.get("api_calls", 0)
                self.current_operation.cache_hits = self.optimization_engine.cache.hits
                self.current_operation.cache_misses = self.optimization_engine.cache.misses

            return {
                "discovery_result": result,
                "performance_metrics": self.current_operation,
                "optimization_summary": {
                    "target_achieved": self.current_operation.total_duration_seconds <= target_seconds,
                    "performance_improvement": self.current_operation.calculate_performance_improvement(),
                    "optimizations_applied": self.current_operation.optimizations_applied,
                },
            }

    async def optimize_vpc_analysis(
        self, operational_profile: str, regions: Optional[List[str]] = None, target_seconds: float = 180.0
    ) -> Dict[str, Any]:
        """
        Optimize VPC analysis with comprehensive SRE patterns

        Addresses: VPC Analysis Timeout Issues
        """
        with self.optimized_operation("vpc_analysis_optimization", target_seconds):
            # Import and use the optimized VPC analyzer
            from runbooks.vpc.performance_optimized_analyzer import create_optimized_vpc_analyzer

            analyzer = create_optimized_vpc_analyzer(
                operational_profile=operational_profile,
                max_workers=min(self.max_workers, 15),  # Limit workers for VPC analysis
            )

            # Execute optimized global VPC analysis
            result = await analyzer.analyze_vpcs_globally(regions=regions, include_detailed_analysis=True)

            # Update metrics
            if self.current_operation:
                analysis_summary = result.get("analysis_summary", {})
                perf_metrics = result.get("performance_metrics", {})

                self.current_operation.aws_api_calls = perf_metrics.get("total_api_calls", 0)
                self.current_operation.parallel_workers_used = self.max_workers

            return {
                "vpc_analysis_result": result,
                "performance_metrics": self.current_operation,
                "optimization_summary": {
                    "target_achieved": self.current_operation.total_duration_seconds <= target_seconds,
                    "regions_analyzed": result.get("analysis_summary", {}).get("total_regions_analyzed", 0),
                    "vpcs_discovered": result.get("analysis_summary", {}).get("total_vpcs_discovered", 0),
                    "performance_grade": result.get("analysis_summary", {}).get("performance_grade", "N/A"),
                },
            }

    def create_performance_dashboard(self) -> None:
        """Create comprehensive SRE performance dashboard"""
        print_header("SRE Performance Optimization Dashboard", "Enterprise Performance Suite")

        if not self.performance_metrics:
            console.print("[yellow]No performance metrics available yet[/yellow]")
            return

        # Performance summary table
        self._create_performance_summary_table()

        # Optimization details table
        self._create_optimization_details_table()

        # System resource status
        self._create_resource_status_panel()

        # Performance recommendations
        self._create_performance_recommendations()

    def _create_performance_summary_table(self):
        """Create performance summary table"""
        table = create_table(
            title="SRE Performance Summary",
            columns=[
                {"name": "Operation", "style": "cyan", "justify": "left"},
                {"name": "Duration", "style": "white", "justify": "right"},
                {"name": "Target", "style": "white", "justify": "right"},
                {"name": "Grade", "style": "white", "justify": "center"},
                {"name": "Improvement", "style": "green", "justify": "right"},
                {"name": "Memory (MB)", "style": "blue", "justify": "right"},
                {"name": "API Calls", "style": "yellow", "justify": "right"},
                {"name": "Status", "style": "white", "justify": "center"},
            ],
        )

        for metrics in self.performance_metrics:
            improvement = metrics.calculate_performance_improvement()
            status_icon = STATUS_INDICATORS["success"] if metrics.success else STATUS_INDICATORS["error"]
            status_color = "green" if metrics.success else "red"

            # Grade color coding
            grade_colors = {"A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red"}
            grade_color = grade_colors.get(metrics.performance_grade, "white")

            table.add_row(
                metrics.operation_name,
                f"{metrics.total_duration_seconds:.1f}s",
                f"{metrics.target_duration_seconds:.1f}s",
                f"[{grade_color}]{metrics.performance_grade}[/{grade_color}]",
                f"+{improvement:.1f}%" if improvement > 0 else f"{improvement:.1f}%",
                f"{metrics.memory_peak_mb:.1f}",
                str(metrics.aws_api_calls),
                f"[{status_color}]{status_icon}[/{status_color}]",
            )

        console.print(table)

    def _create_optimization_details_table(self):
        """Create optimization details table"""
        table = create_table(
            title="Optimization Techniques Applied",
            columns=[
                {"name": "Operation", "style": "cyan", "justify": "left"},
                {"name": "Cache Efficiency", "style": "blue", "justify": "right"},
                {"name": "Memory Saved", "style": "green", "justify": "right"},
                {"name": "Workers Used", "style": "yellow", "justify": "right"},
                {"name": "Optimizations", "style": "dim", "justify": "left", "max_width": 40},
            ],
        )

        for metrics in self.performance_metrics:
            cache_efficiency = metrics.get_cache_efficiency()
            memory_saved = f"+{metrics.memory_saved_mb:.1f}MB" if metrics.memory_saved_mb > 0 else "0MB"

            table.add_row(
                metrics.operation_name,
                f"{cache_efficiency:.1f}%",
                memory_saved,
                str(metrics.parallel_workers_used),
                ", ".join(metrics.optimizations_applied[:3])
                + ("..." if len(metrics.optimizations_applied) > 3 else ""),
            )

        console.print(table)

    def _create_resource_status_panel(self):
        """Create system resource status panel"""
        # Get current resource status
        memory_report = self.memory_optimizer.get_memory_usage_report()
        cache_stats = self.optimization_engine.cache.get_stats()

        # Status colors
        memory_color = {"good": "green", "moderate": "yellow", "warning": "yellow", "critical": "red"}.get(
            memory_report.get("memory_status", "good"), "white"
        )

        status_text = f"""
[bold cyan]💾 Memory Status:[/bold cyan] [{memory_color}]{memory_report["memory_status"].upper()}[/{memory_color}] ({memory_report["current_memory_mb"]:.1f}MB / {memory_report["critical_threshold_mb"]:.0f}MB)

[bold blue]🗄️  Cache Performance:[/bold blue] {cache_stats["hit_rate"]:.1f}% hit rate ({cache_stats["hits"]} hits, {cache_stats["misses"]} misses)

[bold yellow]🔧 System Resources:[/bold yellow] {cache_stats["size"]}/{cache_stats["max_size"]} cache entries, {memory_report["active_objects"]:,} active objects
        """

        console.print(
            Panel(status_text.strip(), title="[bold]System Resource Status[/bold]", border_style=memory_color)
        )

    def _create_performance_recommendations(self):
        """Create performance optimization recommendations"""
        recommendations = []

        # Analyze recent performance metrics
        if self.performance_metrics:
            recent_metrics = self.performance_metrics[-5:]  # Last 5 operations

            # Check for performance issues
            slow_operations = [m for m in recent_metrics if m.total_duration_seconds > m.target_duration_seconds]
            if slow_operations:
                recommendations.append(f"🐌 {len(slow_operations)} operations exceeded target duration")

            # Check memory usage
            high_memory_ops = [m for m in recent_metrics if m.memory_peak_mb > self.memory_limit_mb * 0.8]
            if high_memory_ops:
                recommendations.append(f"🧠 {len(high_memory_ops)} operations had high memory usage")

            # Check cache efficiency
            low_cache_ops = [m for m in recent_metrics if m.get_cache_efficiency() < 50]
            if low_cache_ops:
                recommendations.append(f"📦 {len(low_cache_ops)} operations had low cache efficiency")

        # System-level recommendations
        memory_report = self.memory_optimizer.get_memory_usage_report()
        recommendations.extend(memory_report.get("optimization_recommendations", []))

        if recommendations:
            recommendations_text = "\n".join(f"• {rec}" for rec in recommendations[:8])
            console.print(
                Panel(
                    recommendations_text,
                    title="[bold yellow]Performance Recommendations[/bold yellow]",
                    border_style="yellow",
                )
            )
        else:
            console.print(
                Panel(
                    "[green]✅ System performance is optimal - no recommendations at this time[/green]",
                    title="[bold green]Performance Status[/bold green]",
                    border_style="green",
                )
            )

    def _log_comprehensive_results(self, metrics: SREPerformanceMetrics):
        """Log comprehensive SRE optimization results"""
        improvement = metrics.calculate_performance_improvement()
        cache_efficiency = metrics.get_cache_efficiency()

        if metrics.success:
            if improvement > 0:
                print_success(
                    f"SRE optimization completed: {metrics.operation_name} "
                    f"({metrics.total_duration_seconds:.1f}s, {improvement:+.1f}% improvement, Grade: {metrics.performance_grade})"
                )
            else:
                console.log(
                    f"[green]SRE operation completed: {metrics.operation_name} "
                    f"({metrics.total_duration_seconds:.1f}s, Grade: {metrics.performance_grade})[/green]"
                )

        # Log optimization details
        if metrics.optimizations_applied:
            console.log(f"[dim]🔧 Optimizations: {', '.join(metrics.optimizations_applied)}[/dim]")

        if cache_efficiency > 0:
            console.log(f"[dim]📦 Cache: {cache_efficiency:.1f}% efficiency ({metrics.cache_hits} hits)[/dim]")

        if metrics.memory_saved_mb > 0:
            console.log(
                f"[dim]🧠 Memory: {metrics.memory_saved_mb:.1f}MB saved (peak: {metrics.memory_peak_mb:.1f}MB)[/dim]"
            )

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.performance_metrics:
            return {"status": "no_data", "message": "No performance metrics available"}

        # Calculate aggregate statistics
        successful_ops = [m for m in self.performance_metrics if m.success]
        total_ops = len(self.performance_metrics)

        avg_duration = (
            sum(m.total_duration_seconds for m in successful_ops) / len(successful_ops) if successful_ops else 0
        )
        avg_improvement = (
            sum(m.calculate_performance_improvement() for m in successful_ops) / len(successful_ops)
            if successful_ops
            else 0
        )
        success_rate = len(successful_ops) / total_ops if total_ops > 0 else 0

        # Performance grade distribution
        grade_counts = {}
        for metrics in self.performance_metrics:
            grade_counts[metrics.performance_grade] = grade_counts.get(metrics.performance_grade, 0) + 1

        return {
            "status": "active",
            "total_operations": total_ops,
            "successful_operations": len(successful_ops),
            "success_rate": success_rate,
            "average_duration_seconds": avg_duration,
            "average_improvement_percent": avg_improvement,
            "performance_grade_distribution": grade_counts,
            "system_resources": {
                "memory_status": self.memory_optimizer.get_memory_usage_report(),
                "cache_status": self.optimization_engine.cache.get_stats(),
            },
            "recent_operations": [
                {
                    "name": m.operation_name,
                    "duration": m.total_duration_seconds,
                    "grade": m.performance_grade,
                    "success": m.success,
                }
                for m in self.performance_metrics[-5:]
            ],
        }

    def clear_performance_data(self):
        """Clear all performance tracking data"""
        self.performance_metrics.clear()
        self.optimization_engine.clear_caches()
        self.memory_optimizer.clear_optimization_data()
        print_success("SRE performance data cleared")


# Global SRE performance suite instance
_sre_performance_suite: Optional[SREPerformanceSuite] = None


def get_sre_performance_suite(
    max_workers: int = 20, memory_limit_mb: int = 2048, cache_ttl_minutes: int = 30
) -> SREPerformanceSuite:
    """Get or create global SRE performance suite instance"""
    global _sre_performance_suite
    if _sre_performance_suite is None:
        _sre_performance_suite = SREPerformanceSuite(
            max_workers=max_workers, memory_limit_mb=memory_limit_mb, cache_ttl_minutes=cache_ttl_minutes
        )
    return _sre_performance_suite


def create_sre_performance_dashboard():
    """Create comprehensive SRE performance dashboard"""
    suite = get_sre_performance_suite()
    suite.create_performance_dashboard()


# Export public interface
__all__ = [
    "SREPerformanceSuite",
    "SREPerformanceMetrics",
    "get_sre_performance_suite",
    "create_sre_performance_dashboard",
]
