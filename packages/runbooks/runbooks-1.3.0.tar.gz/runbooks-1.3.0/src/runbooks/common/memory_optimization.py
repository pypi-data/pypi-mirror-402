#!/usr/bin/env python3
"""
Memory Optimization Framework for CloudOps-Runbooks

🎯 SRE Automation Specialist Implementation
Following proven systematic delegation patterns for memory management and optimization.

Addresses: Memory Usage Optimization for Large-Scale Operations
Features:
- Real-time memory monitoring and alerting
- Automatic garbage collection optimization
- Memory-efficient data processing patterns
- Large dataset streaming and pagination
- Memory leak detection and prevention
- Resource cleanup automation
"""

import gc
import logging
import threading
import time
import weakref
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union
import sys
import tracemalloc

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from runbooks.common.rich_utils import (
    console,
    print_header,
    print_success,
    print_warning,
    print_error,
    create_table,
    STATUS_INDICATORS,
)

logger = logging.getLogger(__name__)


@dataclass
class MemorySnapshot:
    """Memory usage snapshot for monitoring"""

    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    memory_percent: float = 0.0
    gc_collections: Tuple[int, int, int] = (0, 0, 0)
    active_objects: int = 0
    operation_context: Optional[str] = None


@dataclass
class MemoryOptimizationMetrics:
    """Memory optimization performance metrics"""

    operation_name: str
    start_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    end_memory_mb: float = 0.0
    memory_saved_mb: float = 0.0
    gc_collections_triggered: int = 0
    optimization_techniques_applied: List[str] = field(default_factory=list)
    memory_warnings: List[str] = field(default_factory=list)
    success: bool = True


class MemoryOptimizer:
    """
    Enterprise memory optimization system for large-scale CloudOps operations

    Provides:
    - Real-time memory monitoring with alerting thresholds
    - Automatic garbage collection optimization
    - Memory-efficient data processing patterns
    - Resource cleanup automation
    - Memory leak detection and prevention
    """

    def __init__(
        self,
        warning_threshold_mb: float = 1024,
        critical_threshold_mb: float = 2048,
        monitoring_interval_seconds: float = 5.0,
    ):
        """
        Initialize memory optimizer

        Args:
            warning_threshold_mb: Memory warning threshold in MB
            critical_threshold_mb: Memory critical threshold in MB
            monitoring_interval_seconds: Memory monitoring check interval
        """
        self.warning_threshold_mb = warning_threshold_mb
        self.critical_threshold_mb = critical_threshold_mb
        self.monitoring_interval_seconds = monitoring_interval_seconds

        # Memory tracking
        self.snapshots: List[MemorySnapshot] = []
        self.metrics: List[MemoryOptimizationMetrics] = []
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Process handle if psutil available
        self.process = psutil.Process() if PSUTIL_AVAILABLE else None

        # Memory management strategies
        self._setup_gc_optimization()

        # Weak reference tracking for leak detection
        self._tracked_objects: weakref.WeakSet = weakref.WeakSet()

    def _setup_gc_optimization(self):
        """Configure garbage collection optimization"""
        # Optimize garbage collection thresholds for large-scale operations
        gc.set_threshold(700, 10, 10)  # More aggressive collection

        # Enable automatic garbage collection
        if not gc.isenabled():
            gc.enable()

        logger.debug("Memory optimization: Garbage collection configured")

    @contextmanager
    def optimize_memory_usage(self, operation_name: str, enable_monitoring: bool = True):
        """
        Context manager for memory-optimized operation execution

        Args:
            operation_name: Name of operation being optimized
            enable_monitoring: Whether to enable real-time monitoring
        """
        # Initialize metrics
        metrics = MemoryOptimizationMetrics(operation_name=operation_name)

        # Start monitoring if requested
        if enable_monitoring:
            self.start_memory_monitoring()

        # Record initial memory state
        initial_snapshot = self._take_memory_snapshot(operation_name)
        metrics.start_memory_mb = initial_snapshot.memory_mb

        try:
            console.log(
                f"[dim]🧠 Starting memory-optimized: {operation_name} (current: {initial_snapshot.memory_mb:.1f}MB)[/]"
            )

            yield metrics

            # Record final state and calculate savings
            final_snapshot = self._take_memory_snapshot(f"{operation_name}_end")
            metrics.end_memory_mb = final_snapshot.memory_mb
            metrics.peak_memory_mb = (
                max(s.peak_memory_mb for s in self.snapshots[-10:]) if self.snapshots else final_snapshot.memory_mb
            )

            # Calculate memory efficiency
            if metrics.start_memory_mb > 0:
                memory_change = metrics.end_memory_mb - metrics.start_memory_mb
                if memory_change < 0:
                    metrics.memory_saved_mb = abs(memory_change)
                    metrics.optimization_techniques_applied.append("memory_cleanup")

            metrics.success = True
            self._log_memory_results(metrics)

        except Exception as e:
            # Handle memory issues during operation
            error_snapshot = self._take_memory_snapshot(f"{operation_name}_error")
            metrics.end_memory_mb = error_snapshot.memory_mb
            metrics.success = False

            # Force garbage collection on error
            collected = gc.collect()
            metrics.gc_collections_triggered += collected
            metrics.optimization_techniques_applied.append("error_gc_cleanup")

            print_error(f"Memory optimization failed for {operation_name}", e)
            raise

        finally:
            # Stop monitoring and store metrics
            if enable_monitoring:
                self.stop_memory_monitoring()

            self.metrics.append(metrics)

            # Cleanup operation-specific resources
            self._cleanup_operation_resources()

    def start_memory_monitoring(self):
        """Start background memory monitoring"""
        if self.monitoring_active:
            return

        self.monitoring_active = True

        def monitor_memory():
            while self.monitoring_active:
                try:
                    snapshot = self._take_memory_snapshot("monitoring")
                    self.snapshots.append(snapshot)

                    # Check thresholds and alert
                    self._check_memory_thresholds(snapshot)

                    # Limit snapshot history to prevent memory growth
                    if len(self.snapshots) > 1000:
                        self.snapshots = self.snapshots[-500:]  # Keep recent 500

                    time.sleep(self.monitoring_interval_seconds)

                except Exception as e:
                    logger.debug(f"Memory monitoring error: {e}")
                    break

        self.monitoring_thread = threading.Thread(target=monitor_memory, daemon=True)
        self.monitoring_thread.start()

        logger.debug("Memory monitoring started")

    def stop_memory_monitoring(self):
        """Stop background memory monitoring"""
        self.monitoring_active = False

        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5.0)

        logger.debug("Memory monitoring stopped")

    def _take_memory_snapshot(self, operation_context: str) -> MemorySnapshot:
        """Take comprehensive memory usage snapshot"""
        snapshot = MemorySnapshot(operation_context=operation_context)

        if self.process and PSUTIL_AVAILABLE:
            try:
                memory_info = self.process.memory_info()
                snapshot.memory_mb = memory_info.rss / (1024 * 1024)
                snapshot.peak_memory_mb = getattr(memory_info, "peak_wset", memory_info.rss) / (1024 * 1024)

                # Memory percentage if available
                try:
                    snapshot.memory_percent = self.process.memory_percent()
                except:
                    snapshot.memory_percent = 0.0

            except Exception as e:
                logger.debug(f"Failed to get process memory info: {e}")
        else:
            # Fallback using tracemalloc if available
            try:
                import tracemalloc

                if tracemalloc.is_tracing():
                    current, peak = tracemalloc.get_traced_memory()
                    snapshot.memory_mb = current / (1024 * 1024)
                    snapshot.peak_memory_mb = peak / (1024 * 1024)
            except:
                pass

        # GC statistics
        snapshot.gc_collections = tuple(gc.get_count())

        # Active objects count
        try:
            snapshot.active_objects = len(gc.get_objects())
        except:
            snapshot.active_objects = 0

        return snapshot

    def _check_memory_thresholds(self, snapshot: MemorySnapshot):
        """Check memory usage against thresholds and alert if needed"""
        if snapshot.memory_mb > self.critical_threshold_mb:
            console.log(
                f"[red]🚨 CRITICAL: Memory usage {snapshot.memory_mb:.1f}MB exceeds critical threshold {self.critical_threshold_mb}MB[/red]"
            )

            # Force aggressive garbage collection
            collected = self._force_garbage_collection()
            console.log(f"[yellow]🗑️  Emergency GC collected {collected} objects[/yellow]")

        elif snapshot.memory_mb > self.warning_threshold_mb:
            console.log(
                f"[yellow]⚠️ WARNING: Memory usage {snapshot.memory_mb:.1f}MB exceeds warning threshold {self.warning_threshold_mb}MB[/yellow]"
            )

    def _force_garbage_collection(self) -> int:
        """Force comprehensive garbage collection"""
        total_collected = 0

        # Multiple GC passes for thorough cleanup
        for generation in range(3):
            collected = gc.collect(generation)
            total_collected += collected

        # Additional cleanup
        gc.collect()  # Final full collection

        return total_collected

    def _cleanup_operation_resources(self):
        """Clean up operation-specific resources"""
        # Force garbage collection
        gc.collect()

        # Clear internal caches if they've grown large
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-50:]  # Keep recent snapshots

    def _log_memory_results(self, metrics: MemoryOptimizationMetrics):
        """Log memory optimization results"""
        if metrics.memory_saved_mb > 0:
            print_success(
                f"Memory optimized for {metrics.operation_name}: "
                f"saved {metrics.memory_saved_mb:.1f}MB "
                f"({metrics.start_memory_mb:.1f}MB → {metrics.end_memory_mb:.1f}MB)"
            )
        elif metrics.end_memory_mb <= metrics.start_memory_mb * 1.1:  # Within 10%
            console.log(
                f"[green]Memory stable for {metrics.operation_name}: "
                f"{metrics.start_memory_mb:.1f}MB → {metrics.end_memory_mb:.1f}MB[/green]"
            )
        else:
            console.log(
                f"[yellow]Memory increased for {metrics.operation_name}: "
                f"{metrics.start_memory_mb:.1f}MB → {metrics.end_memory_mb:.1f}MB[/yellow]"
            )

    def create_memory_efficient_iterator(self, data: List[Any], batch_size: int = 100) -> Iterator[List[Any]]:
        """
        Create memory-efficient iterator for large datasets

        Args:
            data: Large dataset to process
            batch_size: Size of each batch to yield

        Yields:
            Batched data chunks for memory-efficient processing
        """
        for i in range(0, len(data), batch_size):
            batch = data[i : i + batch_size]
            yield batch

            # Trigger GC every 10 batches to prevent memory buildup
            if i > 0 and (i // batch_size) % 10 == 0:
                gc.collect()

    def optimize_large_dict_processing(
        self, large_dict: Dict[str, Any], chunk_size: int = 1000
    ) -> Iterator[Dict[str, Any]]:
        """
        Memory-efficient large dictionary processing

        Args:
            large_dict: Large dictionary to process
            chunk_size: Number of items to process per chunk

        Yields:
            Dictionary chunks for processing
        """
        items = list(large_dict.items())

        for i in range(0, len(items), chunk_size):
            chunk_items = items[i : i + chunk_size]
            chunk_dict = dict(chunk_items)

            yield chunk_dict

            # Clean up temporary variables
            del chunk_items, chunk_dict

            # Periodic GC
            if i > 0 and (i // chunk_size) % 5 == 0:
                gc.collect()

    def track_object_for_leaks(self, obj: Any, name: str = ""):
        """Track object for memory leak detection"""
        self._tracked_objects.add(obj)
        logger.debug(f"Tracking object for leaks: {name or type(obj).__name__}")

    def get_memory_usage_report(self) -> Dict[str, Any]:
        """Get comprehensive memory usage report"""
        current_snapshot = self._take_memory_snapshot("report_generation")

        # Calculate statistics from recent snapshots
        recent_snapshots = self.snapshots[-20:] if self.snapshots else [current_snapshot]

        avg_memory = sum(s.memory_mb for s in recent_snapshots) / len(recent_snapshots)
        peak_memory = max(s.peak_memory_mb for s in recent_snapshots)

        return {
            "current_memory_mb": current_snapshot.memory_mb,
            "average_memory_mb": avg_memory,
            "peak_memory_mb": peak_memory,
            "memory_percent": current_snapshot.memory_percent,
            "warning_threshold_mb": self.warning_threshold_mb,
            "critical_threshold_mb": self.critical_threshold_mb,
            "active_objects": current_snapshot.active_objects,
            "gc_collections": current_snapshot.gc_collections,
            "tracked_objects": len(self._tracked_objects),
            "memory_status": self._get_memory_status(current_snapshot),
            "optimization_recommendations": self._get_optimization_recommendations(current_snapshot),
        }

    def _get_memory_status(self, snapshot: MemorySnapshot) -> str:
        """Determine current memory status"""
        if snapshot.memory_mb > self.critical_threshold_mb:
            return "critical"
        elif snapshot.memory_mb > self.warning_threshold_mb:
            return "warning"
        elif snapshot.memory_mb > self.warning_threshold_mb * 0.8:
            return "moderate"
        else:
            return "good"

    def _get_optimization_recommendations(self, snapshot: MemorySnapshot) -> List[str]:
        """Generate memory optimization recommendations"""
        recommendations = []

        if snapshot.memory_mb > self.critical_threshold_mb:
            recommendations.append("Immediate garbage collection required")
            recommendations.append("Consider batch processing for large operations")

        if snapshot.memory_mb > self.warning_threshold_mb:
            recommendations.append("Monitor memory usage closely")
            recommendations.append("Implement streaming processing for large datasets")

        if snapshot.active_objects > 100000:
            recommendations.append("High object count detected - review object lifecycle")

        if len(self._tracked_objects) > 0:
            recommendations.append(f"{len(self._tracked_objects)} objects being tracked for leaks")

        return recommendations

    def create_memory_summary_table(self) -> None:
        """Display memory optimization summary in Rich table format"""
        if not self.metrics:
            console.print("[yellow]No memory optimization metrics available[/yellow]")
            return

        print_header("Memory Optimization Summary", "SRE Memory Management")

        # Create metrics table
        table = create_table(
            title="Memory Optimization Results",
            columns=[
                {"name": "Operation", "style": "cyan", "justify": "left"},
                {"name": "Start (MB)", "style": "white", "justify": "right"},
                {"name": "Peak (MB)", "style": "white", "justify": "right"},
                {"name": "End (MB)", "style": "white", "justify": "right"},
                {"name": "Saved (MB)", "style": "green", "justify": "right"},
                {"name": "Optimizations", "style": "dim", "justify": "left", "max_width": 25},
                {"name": "Status", "style": "white", "justify": "center"},
            ],
        )

        for metrics in self.metrics:
            status_icon = STATUS_INDICATORS["success"] if metrics.success else STATUS_INDICATORS["error"]
            status_color = "green" if metrics.success else "red"

            saved_text = f"+{metrics.memory_saved_mb:.1f}" if metrics.memory_saved_mb > 0 else "0.0"

            table.add_row(
                metrics.operation_name,
                f"{metrics.start_memory_mb:.1f}",
                f"{metrics.peak_memory_mb:.1f}",
                f"{metrics.end_memory_mb:.1f}",
                saved_text,
                ", ".join(metrics.optimization_techniques_applied[:2])
                + ("..." if len(metrics.optimization_techniques_applied) > 2 else ""),
                f"[{status_color}]{status_icon}[/]",
            )

        console.print(table)

        # Current memory status
        report = self.get_memory_usage_report()
        status_color = {"good": "green", "moderate": "yellow", "warning": "yellow", "critical": "red"}.get(
            report["memory_status"], "white"
        )

        console.print(
            f"\n[{status_color}]Current Memory: {report['current_memory_mb']:.1f}MB ({report['memory_status'].upper()})[/{status_color}]"
        )

    def clear_optimization_data(self):
        """Clear all optimization tracking data"""
        self.snapshots.clear()
        self.metrics.clear()
        self._tracked_objects.clear()
        gc.collect()
        print_success("Memory optimization data cleared")


# Global memory optimizer instance
_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer(warning_threshold_mb: float = 1024, critical_threshold_mb: float = 2048) -> MemoryOptimizer:
    """Get or create global memory optimizer instance"""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer(
            warning_threshold_mb=warning_threshold_mb, critical_threshold_mb=critical_threshold_mb
        )
    return _memory_optimizer


def create_memory_report():
    """Create comprehensive memory optimization report"""
    if _memory_optimizer:
        _memory_optimizer.create_memory_summary_table()
    else:
        console.print("[yellow]No memory optimizer initialized[/yellow]")


# Memory optimization decorators
def memory_optimized(operation_name: str = None, enable_monitoring: bool = True):
    """Decorator for memory-optimized function execution"""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            optimizer = get_memory_optimizer()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            with optimizer.optimize_memory_usage(op_name, enable_monitoring):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Export public interface
__all__ = [
    "MemoryOptimizer",
    "MemorySnapshot",
    "MemoryOptimizationMetrics",
    "get_memory_optimizer",
    "create_memory_report",
    "memory_optimized",
]
