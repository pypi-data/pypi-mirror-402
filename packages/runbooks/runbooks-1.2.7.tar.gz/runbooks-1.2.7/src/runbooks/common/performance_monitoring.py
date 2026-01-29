#!/usr/bin/env python3
"""
Performance Monitoring Decorators for Runbooks - Enterprise Metrics

Provides comprehensive performance tracking and optimization guidance across
all runbooks modules with enterprise-grade monitoring capabilities.

Features:
- Execution time monitoring with module-specific targets
- Memory usage tracking and optimization recommendations
- API call rate monitoring for AWS operations
- Business value correlation with performance metrics
- Executive reporting with performance dashboards

Author: Runbooks Team
Version: 1.0.0 - Enterprise Performance Monitoring
"""

import time
import tracemalloc
from functools import wraps
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import json

from runbooks.common.rich_utils import (
    console,
    print_success,
    print_warning,
    print_info,
    print_error,
    create_table,
    create_progress_bar,
    STATUS_INDICATORS,
)


@dataclass
class PerformanceMetrics:
    """Enterprise performance metrics tracking."""

    operation_name: str
    module_name: str
    start_time: float
    end_time: float
    execution_time: float = 0.0
    memory_peak_mb: float = 0.0
    memory_current_mb: float = 0.0
    api_calls_count: int = 0
    success: bool = True
    error_message: Optional[str] = None
    target_seconds: int = 30
    business_value: float = 0.0
    resources_processed: int = 0

    def __post_init__(self):
        """Calculate derived metrics."""
        self.execution_time = self.end_time - self.start_time
        self.performance_ratio = self.execution_time / self.target_seconds
        self.efficiency_score = min(100, (self.target_seconds / max(self.execution_time, 0.1)) * 100)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for export."""
        return {
            "operation": self.operation_name,
            "module": self.module_name,
            "timestamp": datetime.fromtimestamp(self.start_time).isoformat(),
            "execution_time_seconds": round(self.execution_time, 2),
            "target_seconds": self.target_seconds,
            "performance_ratio": round(self.performance_ratio, 2),
            "efficiency_score": round(self.efficiency_score, 1),
            "memory_peak_mb": round(self.memory_peak_mb, 2),
            "memory_current_mb": round(self.memory_current_mb, 2),
            "api_calls": self.api_calls_count,
            "success": self.success,
            "business_value": self.business_value,
            "resources_processed": self.resources_processed,
        }


@dataclass
class ModulePerformanceTargets:
    """Module-specific performance targets for enterprise operations."""

    finops: int = 15  # FinOps cost analysis operations
    inventory: int = 45  # Multi-account discovery operations
    operate: int = 15  # Resource operations with safety validation
    security: int = 45  # Comprehensive security assessments
    cfat: int = 60  # Cloud foundations assessments
    vpc: int = 30  # Network analysis with cost integration
    remediation: int = 15  # Automated security remediation
    sre: int = 30  # Site reliability engineering operations

    def get_target(self, module_name: str) -> int:
        """Get performance target for module."""
        return getattr(self, module_name.lower(), 30)  # Default 30s


# Global performance tracking
_performance_targets = ModulePerformanceTargets()
_performance_history: List[PerformanceMetrics] = []
_api_call_counter = 0


def track_api_call():
    """Increment API call counter for performance monitoring."""
    global _api_call_counter
    _api_call_counter += 1


def reset_api_counter():
    """Reset API call counter."""
    global _api_call_counter
    _api_call_counter = 0


def monitor_performance(
    module_name: str = "runbooks",
    operation_name: Optional[str] = None,
    target_seconds: Optional[int] = None,
    track_memory: bool = True,
):
    """
    Decorator for comprehensive performance monitoring.

    Monitors execution time, memory usage, and provides optimization
    recommendations when operations exceed enterprise targets.

    Args:
        module_name: Name of the runbooks module
        operation_name: Specific operation being monitored
        target_seconds: Custom target time (uses module default if None)
        track_memory: Enable memory usage tracking

    Usage:
        @monitor_performance(module_name="finops", operation_name="cost_analysis")
        def analyze_costs(**kwargs):
            # Your operation code here
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            global _api_call_counter, _performance_history

            # Determine operation name and target
            op_name = operation_name or f.__name__
            target = target_seconds or _performance_targets.get_target(module_name)

            # Initialize metrics
            metrics = PerformanceMetrics(
                operation_name=op_name,
                module_name=module_name,
                start_time=time.time(),
                end_time=0.0,
                target_seconds=target,
            )

            # Start memory tracking if enabled
            if track_memory:
                tracemalloc.start()
                start_memory = tracemalloc.get_traced_memory()[0]
            else:
                start_memory = 0

            # Reset API counter
            reset_api_counter()

            try:
                # Execute the function
                result = f(*args, **kwargs)

                # Mark as successful
                metrics.success = True
                metrics.end_time = time.time()

                # Extract business metrics if available
                if isinstance(result, dict):
                    metrics.business_value = result.get("annual_savings", 0.0)
                    metrics.resources_processed = result.get("resources_count", 0)

                # Capture performance data
                metrics.api_calls_count = _api_call_counter

                if track_memory:
                    current_memory, peak_memory = tracemalloc.get_traced_memory()
                    metrics.memory_current_mb = (current_memory - start_memory) / 1024 / 1024
                    metrics.memory_peak_mb = peak_memory / 1024 / 1024
                    tracemalloc.stop()

                # Performance feedback
                _provide_performance_feedback(metrics)

                # Store metrics for analysis
                _performance_history.append(metrics)

                return result

            except Exception as e:
                # Handle errors
                metrics.success = False
                metrics.error_message = str(e)
                metrics.end_time = time.time()

                if track_memory and tracemalloc.is_tracing():
                    current_memory, peak_memory = tracemalloc.get_traced_memory()
                    metrics.memory_current_mb = (current_memory - start_memory) / 1024 / 1024
                    metrics.memory_peak_mb = peak_memory / 1024 / 1024
                    tracemalloc.stop()

                # Store failed metrics
                _performance_history.append(metrics)

                print_error(f"❌ Operation failed after {metrics.execution_time:.1f}s: {str(e)}")
                raise

        return wrapper

    return decorator


def _provide_performance_feedback(metrics: PerformanceMetrics):
    """
    Provide performance feedback and optimization recommendations.

    Args:
        metrics: Performance metrics from operation
    """
    execution_time = metrics.execution_time
    target = metrics.target_seconds

    if execution_time <= target:
        # Performance target met
        print_success(
            f"⚡ Performance: {execution_time:.1f}s (target: <{target}s) - {metrics.efficiency_score:.1f}% efficient"
        )

        # Celebrate exceptional performance
        if execution_time <= target * 0.5:
            print_success("🏆 Exceptional performance - well below target!")

    else:
        # Performance target exceeded
        print_warning(
            f"⚠️ Performance: {execution_time:.1f}s (exceeded {target}s target by {execution_time - target:.1f}s)"
        )

        # Provide optimization recommendations
        _provide_optimization_recommendations(metrics)


def _provide_optimization_recommendations(metrics: PerformanceMetrics):
    """
    Provide specific optimization recommendations based on performance data.

    Args:
        metrics: Performance metrics showing degradation
    """
    print_info("🔧 Performance optimization suggestions:")

    # Time-based recommendations
    if metrics.execution_time > metrics.target_seconds * 2:
        print_info(f"  • Consider using --parallel for {metrics.operation_name}")
        print_info("  • Try a different AWS region for better API performance")

    # Memory-based recommendations
    if metrics.memory_peak_mb > 200:  # 200MB threshold
        print_info(f"  • High memory usage: {metrics.memory_peak_mb:.1f}MB")
        print_info("  • Consider processing resources in smaller batches")

    # API call recommendations
    if metrics.api_calls_count > 100:
        print_info(f"  • High API call volume: {metrics.api_calls_count} calls")
        print_info("  • Consider implementing result caching")
        print_info("  • Check for API throttling issues")

    # Module-specific recommendations
    module_recommendations = {
        "finops": [
            "Use more specific date ranges to reduce Cost Explorer data",
            "Consider account filtering for large organizations",
        ],
        "inventory": ["Use service-specific discovery instead of full scan", "Implement parallel account processing"],
        "security": ["Focus on high-priority security checks first", "Use incremental scanning for large environments"],
    }

    if metrics.module_name in module_recommendations:
        for rec in module_recommendations[metrics.module_name]:
            print_info(f"  • {rec}")


def benchmark_operation(module_name: str, operation_name: str, target_calls: int = 10):
    """
    Decorator for benchmarking operation performance over multiple runs.

    Args:
        module_name: Module being benchmarked
        operation_name: Operation being benchmarked
        target_calls: Number of benchmark runs

    Usage:
        @benchmark_operation(module_name="finops", operation_name="cost_analysis")
        def analyze_costs(**kwargs):
            # Your operation code here
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            print_info(f"🏁 Starting benchmark: {target_calls} runs of {operation_name}")

            benchmark_results = []

            for run in range(target_calls):
                print_info(f"  Run {run + 1}/{target_calls}")

                # Execute with monitoring
                monitored_func = monitor_performance(
                    module_name=module_name, operation_name=f"{operation_name}_benchmark_{run + 1}"
                )(f)

                result = monitored_func(*args, **kwargs)

                # Collect metrics from last run
                if _performance_history:
                    benchmark_results.append(_performance_history[-1])

            # Analyze benchmark results
            _analyze_benchmark_results(benchmark_results, operation_name)

            return result

        return wrapper

    return decorator


def _analyze_benchmark_results(results: List[PerformanceMetrics], operation_name: str):
    """
    Analyze and report benchmark results.

    Args:
        results: List of performance metrics from benchmark runs
        operation_name: Name of operation benchmarked
    """
    if not results:
        return

    execution_times = [r.execution_time for r in results if r.success]

    if not execution_times:
        print_error("❌ No successful benchmark runs to analyze")
        return

    # Calculate statistics
    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)

    # Create benchmark summary table
    table = create_table(
        title=f"📊 Benchmark Results: {operation_name}",
        columns=[
            {"name": "Metric", "style": "cyan"},
            {"name": "Value", "style": "green"},
            {"name": "Assessment", "style": "yellow"},
        ],
    )

    target = results[0].target_seconds

    table.add_row("Average Time", f"{avg_time:.2f}s", "✅ Good" if avg_time <= target else "⚠️ Needs optimization")
    table.add_row("Best Time", f"{min_time:.2f}s", "🏆 Excellent" if min_time <= target * 0.5 else "✅ Good")
    table.add_row("Worst Time", f"{max_time:.2f}s", "⚠️ Investigate" if max_time > target * 1.5 else "✅ Acceptable")
    table.add_row(
        "Success Rate",
        f"{len(execution_times)}/{len(results)}",
        "✅ Perfect" if len(execution_times) == len(results) else "⚠️ Some failures",
    )
    table.add_row(
        "Consistency",
        f"±{(max_time - min_time):.2f}s",
        "✅ Consistent" if (max_time - min_time) <= target * 0.2 else "⚠️ Variable",
    )

    console.print(table)


def get_performance_report(module_name: Optional[str] = None, last_n_operations: int = 10) -> Dict[str, Any]:
    """
    Generate performance report for operations.

    Args:
        module_name: Filter by specific module (None for all)
        last_n_operations: Number of recent operations to include

    Returns:
        Performance report dictionary
    """
    # Filter operations
    filtered_operations = _performance_history
    if module_name:
        filtered_operations = [op for op in filtered_operations if op.module_name == module_name]

    # Get recent operations
    recent_operations = filtered_operations[-last_n_operations:]

    if not recent_operations:
        return {"message": "No performance data available"}

    # Calculate summary statistics
    successful_ops = [op for op in recent_operations if op.success]
    failed_ops = [op for op in recent_operations if not op.success]

    avg_time = sum(op.execution_time for op in successful_ops) / len(successful_ops) if successful_ops else 0
    avg_efficiency = sum(op.efficiency_score for op in successful_ops) / len(successful_ops) if successful_ops else 0

    report = {
        "summary": {
            "total_operations": len(recent_operations),
            "successful_operations": len(successful_ops),
            "failed_operations": len(failed_ops),
            "success_rate_percent": (len(successful_ops) / len(recent_operations)) * 100,
            "average_execution_time": round(avg_time, 2),
            "average_efficiency_score": round(avg_efficiency, 1),
        },
        "operations": [op.to_dict() for op in recent_operations],
        "recommendations": _generate_performance_recommendations(recent_operations),
    }

    return report


def _generate_performance_recommendations(operations: List[PerformanceMetrics]) -> List[str]:
    """Generate performance recommendations based on operation history."""
    recommendations = []

    if not operations:
        return recommendations

    # Analyze patterns
    slow_operations = [op for op in operations if op.success and op.performance_ratio > 1.5]
    high_memory_operations = [op for op in operations if op.memory_peak_mb > 150]
    high_api_operations = [op for op in operations if op.api_calls_count > 50]

    if slow_operations:
        recommendations.append(f"⚠️ {len(slow_operations)} operations exceeded target by >50% - consider optimization")

    if high_memory_operations:
        recommendations.append(
            f"🧠 {len(high_memory_operations)} operations used >150MB memory - consider batch processing"
        )

    if high_api_operations:
        recommendations.append(f"🔄 {len(high_api_operations)} operations made >50 API calls - consider caching")

    # Success rate recommendations
    failed_ops = [op for op in operations if not op.success]
    if len(failed_ops) > len(operations) * 0.1:  # >10% failure rate
        recommendations.append("❌ High failure rate detected - review error handling and retry logic")

    return recommendations


def clear_performance_history():
    """Clear performance history for fresh tracking."""
    global _performance_history
    _performance_history.clear()
    print_info("Performance history cleared")


def export_performance_data(output_path: str = "performance_report.json") -> bool:
    """
    Export performance data to JSON file.

    Args:
        output_path: Path for output file

    Returns:
        True if export successful
    """
    try:
        report = get_performance_report()

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print_success(f"Performance data exported to {output_path}")
        return True

    except Exception as e:
        print_error(f"Failed to export performance data: {str(e)}")
        return False


# Export public interface
__all__ = [
    "PerformanceMetrics",
    "ModulePerformanceTargets",
    "monitor_performance",
    "benchmark_operation",
    "track_api_call",
    "reset_api_counter",
    "get_performance_report",
    "clear_performance_history",
    "export_performance_data",
]
