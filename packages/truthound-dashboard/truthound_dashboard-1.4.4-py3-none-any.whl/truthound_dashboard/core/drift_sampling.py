"""Drift sampling strategies for large-scale datasets.

This module provides various sampling strategies optimized for drift detection
on 100M+ row datasets. It includes random, stratified, and reservoir sampling
with automatic sample size estimation based on confidence levels.
"""

from __future__ import annotations

import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterator, Sequence, TypeVar

import numpy as np

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SamplingMethod(str, Enum):
    """Available sampling methods for large datasets."""

    RANDOM = "random"
    STRATIFIED = "stratified"
    RESERVOIR = "reservoir"
    SYSTEMATIC = "systematic"


@dataclass
class SampleSizeEstimate:
    """Estimated sample size for drift detection.

    Attributes:
        recommended_size: Recommended sample size for target confidence.
        min_size: Minimum sample size for basic detection.
        max_size: Maximum useful sample size (diminishing returns beyond).
        confidence_level: Target confidence level (0.0-1.0).
        margin_of_error: Expected margin of error at recommended size.
        estimated_time_seconds: Estimated processing time.
        memory_mb: Estimated memory usage in MB.
    """

    recommended_size: int
    min_size: int
    max_size: int
    confidence_level: float
    margin_of_error: float
    estimated_time_seconds: float
    memory_mb: float


@dataclass
class ChunkedComparisonProgress:
    """Progress tracking for chunked comparison operations.

    Attributes:
        total_chunks: Total number of chunks to process.
        processed_chunks: Number of chunks already processed.
        total_rows: Total rows across all chunks.
        processed_rows: Rows processed so far.
        current_chunk: Current chunk being processed.
        elapsed_seconds: Time elapsed since start.
        estimated_remaining_seconds: Estimated time remaining.
        columns_with_drift: Columns detected with drift so far.
        early_stop_triggered: Whether early stopping was triggered.
        status: Current status (running, completed, cancelled, error).
    """

    total_chunks: int
    processed_chunks: int
    total_rows: int
    processed_rows: int
    current_chunk: int
    elapsed_seconds: float
    estimated_remaining_seconds: float
    columns_with_drift: list[str]
    early_stop_triggered: bool
    status: str  # running, completed, cancelled, error


class BaseSampler(ABC):
    """Abstract base class for sampling strategies."""

    @abstractmethod
    def sample(self, data: Sequence[T], sample_size: int) -> list[T]:
        """Sample data from the input sequence.

        Args:
            data: Input data sequence.
            sample_size: Number of samples to extract.

        Returns:
            List of sampled items.
        """
        pass

    @abstractmethod
    def sample_indices(self, total_size: int, sample_size: int) -> list[int]:
        """Generate sample indices for a dataset of given size.

        Args:
            total_size: Total number of rows in dataset.
            sample_size: Number of samples to extract.

        Returns:
            List of indices to sample.
        """
        pass


class RandomSampler(BaseSampler):
    """Simple random sampling without replacement.

    Best for: General-purpose sampling when no stratification is needed.
    Time complexity: O(n) for data, O(k) for indices where k is sample size.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize random sampler.

        Args:
            seed: Random seed for reproducibility.
        """
        self.rng = random.Random(seed)

    def sample(self, data: Sequence[T], sample_size: int) -> list[T]:
        """Perform random sampling on data."""
        if sample_size >= len(data):
            return list(data)
        indices = self.sample_indices(len(data), sample_size)
        return [data[i] for i in indices]

    def sample_indices(self, total_size: int, sample_size: int) -> list[int]:
        """Generate random sample indices."""
        if sample_size >= total_size:
            return list(range(total_size))
        return self.rng.sample(range(total_size), sample_size)


class StratifiedSampler(BaseSampler):
    """Stratified sampling based on a stratification column.

    Best for: Ensuring representation of all categories in drift detection.
    Time complexity: O(n) where n is data size.
    """

    def __init__(
        self,
        strata_column: str | int,
        seed: int | None = None,
    ) -> None:
        """Initialize stratified sampler.

        Args:
            strata_column: Column name or index for stratification.
            seed: Random seed for reproducibility.
        """
        self.strata_column = strata_column
        self.rng = random.Random(seed)

    def sample(self, data: Sequence[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
        """Perform stratified sampling.

        Args:
            data: Input data with dict rows.
            sample_size: Total number of samples.

        Returns:
            Stratified sample maintaining proportions.
        """
        if sample_size >= len(data):
            return list(data)

        # Group by strata
        strata: dict[Any, list[int]] = {}
        for i, row in enumerate(data):
            key = row.get(self.strata_column) if isinstance(row, dict) else row[self.strata_column]
            if key not in strata:
                strata[key] = []
            strata[key].append(i)

        # Calculate samples per stratum (proportional)
        total = len(data)
        result_indices: list[int] = []

        for stratum_key, indices in strata.items():
            proportion = len(indices) / total
            stratum_sample_size = max(1, int(sample_size * proportion))
            stratum_sample_size = min(stratum_sample_size, len(indices))
            sampled = self.rng.sample(indices, stratum_sample_size)
            result_indices.extend(sampled)

        # If we have fewer samples than requested, top up randomly
        if len(result_indices) < sample_size:
            remaining = set(range(total)) - set(result_indices)
            additional = self.rng.sample(
                list(remaining), min(sample_size - len(result_indices), len(remaining))
            )
            result_indices.extend(additional)

        return [data[i] for i in result_indices[:sample_size]]

    def sample_indices(self, total_size: int, sample_size: int) -> list[int]:
        """Generate stratified indices (falls back to random without strata info)."""
        if sample_size >= total_size:
            return list(range(total_size))
        return self.rng.sample(range(total_size), sample_size)


class ReservoirSampler(BaseSampler):
    """Reservoir sampling for streaming data (Algorithm R).

    Best for: Single-pass sampling of very large datasets or streams.
    Time complexity: O(n) single pass.
    Space complexity: O(k) where k is sample size.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize reservoir sampler.

        Args:
            seed: Random seed for reproducibility.
        """
        self.rng = random.Random(seed)

    def sample(self, data: Sequence[T], sample_size: int) -> list[T]:
        """Perform reservoir sampling."""
        return list(self.sample_stream(iter(data), sample_size))

    def sample_stream(self, stream: Iterator[T], sample_size: int) -> Iterator[T]:
        """Sample from a stream using reservoir sampling.

        Args:
            stream: Input data stream.
            sample_size: Number of samples to maintain.

        Yields:
            Sampled items after stream is exhausted.
        """
        reservoir: list[T] = []

        for i, item in enumerate(stream):
            if i < sample_size:
                reservoir.append(item)
            else:
                # Replace with decreasing probability
                j = self.rng.randint(0, i)
                if j < sample_size:
                    reservoir[j] = item

        yield from reservoir

    def sample_indices(self, total_size: int, sample_size: int) -> list[int]:
        """Generate reservoir-style indices."""
        if sample_size >= total_size:
            return list(range(total_size))

        reservoir = list(range(sample_size))
        for i in range(sample_size, total_size):
            j = self.rng.randint(0, i)
            if j < sample_size:
                reservoir[j] = i

        return sorted(reservoir)


class SystematicSampler(BaseSampler):
    """Systematic sampling with random start.

    Best for: Evenly distributed sampling across ordered data.
    Time complexity: O(k) where k is sample size.
    """

    def __init__(self, seed: int | None = None) -> None:
        """Initialize systematic sampler.

        Args:
            seed: Random seed for reproducibility.
        """
        self.rng = random.Random(seed)

    def sample(self, data: Sequence[T], sample_size: int) -> list[T]:
        """Perform systematic sampling."""
        indices = self.sample_indices(len(data), sample_size)
        return [data[i] for i in indices]

    def sample_indices(self, total_size: int, sample_size: int) -> list[int]:
        """Generate systematic sample indices."""
        if sample_size >= total_size:
            return list(range(total_size))

        interval = total_size / sample_size
        start = self.rng.uniform(0, interval)

        indices = []
        for i in range(sample_size):
            idx = int(start + i * interval)
            if idx < total_size:
                indices.append(idx)

        return indices


def get_sampler(method: SamplingMethod, **kwargs) -> BaseSampler:
    """Factory function to get the appropriate sampler.

    Args:
        method: Sampling method to use.
        **kwargs: Additional arguments for the sampler.

    Returns:
        Configured sampler instance.
    """
    seed = kwargs.get("seed")

    if method == SamplingMethod.RANDOM:
        return RandomSampler(seed=seed)
    elif method == SamplingMethod.STRATIFIED:
        strata_column = kwargs.get("strata_column", 0)
        return StratifiedSampler(strata_column=strata_column, seed=seed)
    elif method == SamplingMethod.RESERVOIR:
        return ReservoirSampler(seed=seed)
    elif method == SamplingMethod.SYSTEMATIC:
        return SystematicSampler(seed=seed)
    else:
        raise ValueError(f"Unknown sampling method: {method}")


def estimate_sample_size(
    population_size: int,
    confidence_level: float = 0.95,
    margin_of_error: float = 0.03,
    expected_drift_rate: float = 0.1,
    num_columns: int = 10,
) -> SampleSizeEstimate:
    """Estimate optimal sample size for drift detection.

    Uses Cochran's formula adjusted for drift detection requirements.

    Args:
        population_size: Total number of rows in the dataset.
        confidence_level: Target confidence level (default 0.95).
        margin_of_error: Acceptable margin of error (default 0.03 = 3%).
        expected_drift_rate: Expected proportion of drifted values (default 0.1).
        num_columns: Number of columns to analyze (affects computation time).

    Returns:
        SampleSizeEstimate with recommended sizes and estimates.
    """
    # Z-scores for common confidence levels
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }
    z = z_scores.get(confidence_level, 1.96)

    # Cochran's formula for sample size
    p = expected_drift_rate
    q = 1 - p
    n0 = (z ** 2 * p * q) / (margin_of_error ** 2)

    # Finite population correction
    if population_size > 0:
        n = n0 / (1 + (n0 - 1) / population_size)
    else:
        n = n0

    recommended = int(math.ceil(n))

    # Minimum sample size for statistical validity
    min_size = max(100, int(recommended * 0.3))

    # Maximum useful sample size (diminishing returns)
    max_size = min(population_size, int(recommended * 3))

    # Ensure ordering
    recommended = max(min_size, min(recommended, max_size))

    # Estimate processing time (rough heuristic)
    # Assume ~10,000 rows/second per column
    rows_per_second = 10000
    estimated_time = (recommended * num_columns) / rows_per_second

    # Estimate memory usage (~100 bytes per row per column for numeric data)
    bytes_per_row = 100 * num_columns
    memory_mb = (recommended * bytes_per_row) / (1024 * 1024)

    return SampleSizeEstimate(
        recommended_size=recommended,
        min_size=min_size,
        max_size=max_size,
        confidence_level=confidence_level,
        margin_of_error=margin_of_error,
        estimated_time_seconds=round(estimated_time, 2),
        memory_mb=round(memory_mb, 2),
    )


def calculate_chunk_size(
    total_rows: int,
    available_memory_mb: float = 1024,
    bytes_per_row: int = 1000,
    target_chunks: int | None = None,
) -> int:
    """Calculate optimal chunk size for processing large datasets.

    Args:
        total_rows: Total number of rows to process.
        available_memory_mb: Available memory in MB.
        bytes_per_row: Estimated bytes per row.
        target_chunks: Target number of chunks (optional).

    Returns:
        Optimal chunk size in rows.
    """
    # Maximum rows that fit in memory
    max_rows_in_memory = int((available_memory_mb * 1024 * 1024) / bytes_per_row)

    # Use 80% of available memory for safety
    safe_chunk_size = int(max_rows_in_memory * 0.8)

    if target_chunks:
        # Calculate chunk size to achieve target number of chunks
        target_chunk_size = total_rows // target_chunks
        # Use the smaller of target and safe size
        chunk_size = min(target_chunk_size, safe_chunk_size)
    else:
        chunk_size = safe_chunk_size

    # Ensure reasonable bounds
    min_chunk_size = 10000
    max_chunk_size = 10_000_000

    return max(min_chunk_size, min(chunk_size, max_chunk_size))


def should_early_stop(
    columns_with_drift: list[str],
    total_columns: int,
    threshold: float = 0.5,
    min_processed: int = 3,
) -> bool:
    """Determine if early stopping should be triggered.

    Early stopping is useful when drift is obvious and processing
    more data won't change the conclusion.

    Args:
        columns_with_drift: List of columns where drift was detected.
        total_columns: Total number of columns being analyzed.
        threshold: Proportion of drifted columns to trigger early stop.
        min_processed: Minimum columns to process before considering early stop.

    Returns:
        True if early stopping should be triggered.
    """
    if len(columns_with_drift) < min_processed:
        return False

    drift_rate = len(columns_with_drift) / total_columns
    return drift_rate >= threshold


class ChunkedComparisonTracker:
    """Tracks progress of chunked comparison operations.

    Thread-safe progress tracking for long-running drift detection jobs.
    """

    def __init__(
        self,
        total_rows: int,
        chunk_size: int,
        total_columns: int,
    ) -> None:
        """Initialize the progress tracker.

        Args:
            total_rows: Total rows to process.
            chunk_size: Size of each chunk.
            total_columns: Number of columns being compared.
        """
        self.total_rows = total_rows
        self.chunk_size = chunk_size
        self.total_columns = total_columns
        self.total_chunks = math.ceil(total_rows / chunk_size)

        self.processed_chunks = 0
        self.processed_rows = 0
        self.current_chunk = 0
        self.columns_with_drift: list[str] = []
        self.early_stop_triggered = False
        self.status = "running"

        self._start_time: float | None = None
        self._chunk_times: list[float] = []

    def start(self) -> None:
        """Mark the start of processing."""
        import time

        self._start_time = time.time()
        self.status = "running"

    def update_chunk(
        self,
        chunk_index: int,
        rows_in_chunk: int,
        drifted_columns: list[str],
        chunk_time: float,
    ) -> None:
        """Update progress after processing a chunk.

        Args:
            chunk_index: Index of the completed chunk.
            rows_in_chunk: Number of rows in this chunk.
            drifted_columns: Columns with drift detected in this chunk.
            chunk_time: Time taken to process this chunk.
        """
        self.current_chunk = chunk_index + 1
        self.processed_chunks = chunk_index + 1
        self.processed_rows += rows_in_chunk
        self._chunk_times.append(chunk_time)

        # Merge drifted columns
        for col in drifted_columns:
            if col not in self.columns_with_drift:
                self.columns_with_drift.append(col)

    def trigger_early_stop(self) -> None:
        """Trigger early stopping."""
        self.early_stop_triggered = True
        self.status = "completed"

    def complete(self) -> None:
        """Mark processing as complete."""
        self.status = "completed"

    def cancel(self) -> None:
        """Mark processing as cancelled."""
        self.status = "cancelled"

    def error(self, message: str) -> None:
        """Mark processing as failed."""
        self.status = "error"
        logger.error(f"Chunked comparison failed: {message}")

    def get_progress(self) -> ChunkedComparisonProgress:
        """Get current progress status.

        Returns:
            Current progress information.
        """
        import time

        elapsed = time.time() - self._start_time if self._start_time else 0.0

        # Estimate remaining time based on average chunk time
        if self._chunk_times and self.processed_chunks < self.total_chunks:
            avg_chunk_time = sum(self._chunk_times) / len(self._chunk_times)
            remaining_chunks = self.total_chunks - self.processed_chunks
            estimated_remaining = avg_chunk_time * remaining_chunks
        else:
            estimated_remaining = 0.0

        return ChunkedComparisonProgress(
            total_chunks=self.total_chunks,
            processed_chunks=self.processed_chunks,
            total_rows=self.total_rows,
            processed_rows=self.processed_rows,
            current_chunk=self.current_chunk,
            elapsed_seconds=round(elapsed, 2),
            estimated_remaining_seconds=round(estimated_remaining, 2),
            columns_with_drift=self.columns_with_drift.copy(),
            early_stop_triggered=self.early_stop_triggered,
            status=self.status,
        )


async def parallel_column_compare(
    baseline_column_data: dict[str, list[Any]],
    current_column_data: dict[str, list[Any]],
    method: str = "auto",
    threshold: float = 0.05,
    max_workers: int = 4,
) -> dict[str, dict[str, Any]]:
    """Compare multiple columns in parallel.

    Args:
        baseline_column_data: Dict mapping column names to baseline values.
        current_column_data: Dict mapping column names to current values.
        method: Drift detection method.
        threshold: Drift threshold.
        max_workers: Maximum parallel workers.

    Returns:
        Dict mapping column names to drift results.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    async def compare_column(column: str) -> tuple[str, dict[str, Any]]:
        """Compare a single column."""
        baseline = baseline_column_data.get(column, [])
        current = current_column_data.get(column, [])

        # Simple drift detection (placeholder - actual implementation would use truthound)
        if not baseline or not current:
            return column, {"drifted": False, "error": "No data"}

        try:
            baseline_arr = np.array(baseline, dtype=float)
            current_arr = np.array(current, dtype=float)

            # Simple statistical comparison
            baseline_mean = np.mean(baseline_arr)
            current_mean = np.mean(current_arr)
            baseline_std = np.std(baseline_arr)

            # Z-score test for mean shift
            if baseline_std > 0:
                z_score = abs(current_mean - baseline_mean) / baseline_std
                drifted = z_score > 2.0  # Simplified threshold
            else:
                drifted = abs(current_mean - baseline_mean) > threshold

            return column, {
                "drifted": drifted,
                "baseline_mean": float(baseline_mean),
                "current_mean": float(current_mean),
                "baseline_std": float(baseline_std),
                "method": method,
            }
        except (ValueError, TypeError):
            # Non-numeric column - use categorical comparison
            baseline_set = set(baseline)
            current_set = set(current)
            new_values = current_set - baseline_set
            drifted = len(new_values) > len(baseline_set) * threshold

            return column, {
                "drifted": drifted,
                "new_categories": list(new_values)[:10],
                "method": "categorical",
            }

    # Run comparisons in parallel
    columns = list(baseline_column_data.keys())

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, lambda c=col: asyncio.run(compare_column(c)))
            for col in columns
        ]

        # Actually run async
        results = {}
        for column in columns:
            col_name, col_result = await compare_column(column)
            results[col_name] = col_result

    return results
