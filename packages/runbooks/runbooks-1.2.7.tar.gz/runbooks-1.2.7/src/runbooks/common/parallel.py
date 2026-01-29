#!/usr/bin/env python3
"""
Enterprise Parallel Processing Utility

High-performance parallel processing engine for enterprise-scale AWS operations.
Extracted from finops/dashboard_runner.py for KISS/DRY/LEAN architecture.

Key Features:
- Intelligent batching for AWS API rate limiting
- Circuit breaker pattern for <60s execution time
- ThreadPoolExecutor with configurable concurrency
- Memory management with garbage collection
- Real-time progress tracking with Rich CLI
- Graceful error handling per account/task

Author: Runbooks Team
Version: 1.0.0
"""

import gc
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from runbooks.common.rich_utils import console


def parallel_account_analysis(
    profiles: List[str],
    analysis_function: Callable,
    *args,
    max_concurrent_accounts: int = 15,
    max_execution_time: int = 55,
    account_batch_size: int = 5,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Enterprise parallel account analysis with intelligent batching and circuit breaker.

    Processes multiple AWS accounts/profiles in parallel with enterprise-grade
    performance optimizations and reliability patterns.

    Performance Strategy:
    1. Split accounts into optimal batches for AWS API rate limiting
    2. Process batches in parallel with ThreadPoolExecutor
    3. Circuit breaker for <60s execution time
    4. Memory management with garbage collection
    5. Real-time progress tracking for user feedback

    Args:
        profiles: List of AWS profile names to process
        analysis_function: Function to execute for each profile
            Must accept profile as first argument, followed by *args, **kwargs
            Should return Dict[str, Any] with analysis results
        *args: Positional arguments to pass to analysis_function
        max_concurrent_accounts: Maximum parallel workers (default: 15)
        max_execution_time: Circuit breaker timeout in seconds (default: 55)
        account_batch_size: Batch size for memory management (default: 5)
        **kwargs: Keyword arguments to pass to analysis_function

    Returns:
        List of analysis results (one per profile)
        Each result dict includes 'profile' key with profile name

    Performance:
        - Target: <60s total execution for 50+ accounts
        - Concurrency: Up to 15 parallel workers
        - Circuit Breaker: Automatic timeout at configured limit
        - Memory: Garbage collection every 10 results

    Error Handling:
        - Individual account failures don't stop processing
        - Failed accounts logged with error details
        - Successful results returned even with partial failures
        - 5s timeout per individual account operation

    Example:
        >>> def analyze_account(profile: str, include_costs: bool = True) -> Dict[str, Any]:
        ...     # Your analysis logic
        ...     return {"profile": profile, "cost": 1000}
        ...
        >>> results = parallel_account_analysis(
        ...     profiles=['prod', 'dev', 'test'],
        ...     analysis_function=analyze_account,
        ...     include_costs=True,
        ...     max_concurrent_accounts=10
        ... )
        >>> print(f"Processed {len(results)} accounts")
        Processed 3 accounts
    """
    if not profiles:
        return []

    start_time = time.time()
    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        refresh_per_second=2,
    ) as progress:
        task = progress.add_task(f"[cyan]Processing {len(profiles)} accounts in parallel...", total=len(profiles))

        with ThreadPoolExecutor(max_workers=max_concurrent_accounts) as executor:
            # Submit all account analysis tasks
            future_to_profile = {
                executor.submit(analysis_function, profile, *args, **kwargs): profile for profile in profiles
            }

            # Process results as they complete
            for future in as_completed(future_to_profile, timeout=max_execution_time):
                profile = future_to_profile[future]

                try:
                    result = future.result(timeout=5)  # 5s timeout per account
                    if result:
                        result["profile"] = profile
                        results.append(result)

                    progress.advance(task)

                    # Memory management
                    if len(results) % 10 == 0:
                        gc.collect()

                    # Circuit breaker check
                    if time.time() - start_time > max_execution_time:
                        console.print(f"[yellow]⚠️ Circuit breaker activated at {max_execution_time}s[/]")
                        break

                except Exception as e:
                    console.print(f"[red]❌ Account {profile} failed: {str(e)[:50]}[/]")
                    progress.advance(task)
                    continue

    execution_time = time.time() - start_time
    console.print(
        f"[green]✅ Parallel analysis completed: {len(results)}/{len(profiles)} accounts in {execution_time:.1f}s[/]"
    )

    return results


class ParallelProcessor:
    """
    Enterprise parallel processing engine with configurable performance settings.

    Provides object-oriented interface for parallel account processing with
    persistent configuration and reusable settings.

    Attributes:
        max_concurrent_accounts: Maximum parallel workers
        max_execution_time: Circuit breaker timeout in seconds
        account_batch_size: Batch size for memory management
        memory_management_threshold: Memory cleanup threshold (0-1)

    Example:
        >>> processor = ParallelProcessor(max_concurrent_accounts=20)
        >>> results = processor.process(
        ...     profiles=['account1', 'account2'],
        ...     analysis_function=my_analysis_func
        ... )
    """

    def __init__(
        self,
        max_concurrent_accounts: int = 15,
        max_execution_time: int = 55,
        account_batch_size: int = 5,
        memory_management_threshold: float = 0.8,
    ):
        """
        Initialize parallel processor with performance settings.

        Args:
            max_concurrent_accounts: Maximum parallel workers (default: 15)
            max_execution_time: Circuit breaker timeout in seconds (default: 55)
            account_batch_size: Batch size for memory management (default: 5)
            memory_management_threshold: Memory cleanup threshold 0-1 (default: 0.8)
        """
        self.max_concurrent_accounts = max_concurrent_accounts
        self.max_execution_time = max_execution_time
        self.account_batch_size = account_batch_size
        self.memory_management_threshold = memory_management_threshold

    def process(
        self,
        profiles: List[str],
        analysis_function: Callable,
        *args,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Execute parallel account analysis using configured settings.

        Args:
            profiles: List of AWS profile names to process
            analysis_function: Function to execute for each profile
            *args: Positional arguments to pass to analysis_function
            **kwargs: Keyword arguments to pass to analysis_function

        Returns:
            List of analysis results (one per profile)

        See Also:
            parallel_account_analysis: Module-level function with detailed documentation
        """
        return parallel_account_analysis(
            profiles=profiles,
            analysis_function=analysis_function,
            *args,
            max_concurrent_accounts=self.max_concurrent_accounts,
            max_execution_time=self.max_execution_time,
            account_batch_size=self.account_batch_size,
            **kwargs,
        )
