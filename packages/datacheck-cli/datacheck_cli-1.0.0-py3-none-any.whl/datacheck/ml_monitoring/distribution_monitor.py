"""Distribution monitoring module.

Provides statistical distribution profiling and comparison capabilities.
"""

from dataclasses import dataclass, field
from typing import Any
import pandas as pd
import numpy as np
from datetime import datetime
import json


@dataclass
class DistributionProfile:
    """Statistical profile of a data distribution."""

    column: str
    dtype: str
    count: int
    null_count: int
    null_percentage: float

    # Numeric stats
    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    median: float | None = None
    q1: float | None = None
    q3: float | None = None
    skewness: float | None = None
    kurtosis: float | None = None

    # Categorical stats
    unique_count: int | None = None
    top_values: dict[str, int] | None = None
    value_frequencies: dict[str, float] | None = None

    # Histogram data
    histogram_bins: list[float] | None = None
    histogram_counts: list[int] | None = None

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "column": self.column,
            "dtype": self.dtype,
            "count": self.count,
            "null_count": self.null_count,
            "null_percentage": self.null_percentage,
            "mean": self.mean,
            "std": self.std,
            "min": self.min,
            "max": self.max,
            "median": self.median,
            "q1": self.q1,
            "q3": self.q3,
            "skewness": self.skewness,
            "kurtosis": self.kurtosis,
            "unique_count": self.unique_count,
            "top_values": self.top_values,
            "value_frequencies": self.value_frequencies,
            "histogram_bins": self.histogram_bins,
            "histogram_counts": self.histogram_counts,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DistributionProfile":
        """Create from dictionary."""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    def is_numeric(self) -> bool:
        """Check if this is a numeric distribution."""
        return self.mean is not None


@dataclass
class DistributionComparison:
    """Comparison between two distribution profiles."""

    column: str
    baseline_profile: DistributionProfile
    current_profile: DistributionProfile

    # Change metrics
    mean_change: float | None = None
    mean_change_pct: float | None = None
    std_change: float | None = None
    std_change_pct: float | None = None
    null_rate_change: float | None = None

    # Distribution similarity
    histogram_overlap: float | None = None
    value_frequency_diff: dict[str, float] | None = None

    # Flags
    significant_change: bool = False
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "column": self.column,
            "baseline_profile": self.baseline_profile.to_dict(),
            "current_profile": self.current_profile.to_dict(),
            "mean_change": self.mean_change,
            "mean_change_pct": self.mean_change_pct,
            "std_change": self.std_change,
            "std_change_pct": self.std_change_pct,
            "null_rate_change": self.null_rate_change,
            "histogram_overlap": self.histogram_overlap,
            "value_frequency_diff": self.value_frequency_diff,
            "significant_change": self.significant_change,
            "alerts": self.alerts,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [f"Distribution Comparison: {self.column}"]

        if self.mean_change is not None:
            lines.append(f"  Mean: {self.baseline_profile.mean:.4f} -> {self.current_profile.mean:.4f} ({self.mean_change_pct:+.2f}%)")

        if self.std_change is not None:
            lines.append(f"  Std: {self.baseline_profile.std:.4f} -> {self.current_profile.std:.4f} ({self.std_change_pct:+.2f}%)")

        if self.null_rate_change is not None:
            lines.append(f"  Null Rate: {self.baseline_profile.null_percentage:.2f}% -> {self.current_profile.null_percentage:.2f}% ({self.null_rate_change:+.2f}%)")

        if self.alerts:
            lines.append("  Alerts:")
            for alert in self.alerts:
                lines.append(f"    - {alert}")

        return "\n".join(lines)


class DistributionMonitor:
    """Monitor for tracking data distributions over time.

    Tracks statistical properties of data columns and detects
    significant changes from baseline.
    """

    def __init__(
        self,
        n_histogram_bins: int = 50,
        top_n_values: int = 20,
        mean_change_threshold: float = 0.1,
        std_change_threshold: float = 0.2,
        null_rate_threshold: float = 0.05,
    ):
        """Initialize distribution monitor.

        Args:
            n_histogram_bins: Number of bins for histograms
            top_n_values: Number of top values to track for categorical
            mean_change_threshold: Threshold for significant mean change (relative)
            std_change_threshold: Threshold for significant std change (relative)
            null_rate_threshold: Threshold for significant null rate change (absolute)
        """
        self.n_histogram_bins = n_histogram_bins
        self.top_n_values = top_n_values
        self.mean_change_threshold = mean_change_threshold
        self.std_change_threshold = std_change_threshold
        self.null_rate_threshold = null_rate_threshold
        self._baseline_profiles: dict[str, DistributionProfile] = {}

    def profile_column(
        self,
        data: pd.Series,
        column_name: str | None = None,
    ) -> DistributionProfile:
        """Create distribution profile for a column.

        Args:
            data: Series to profile
            column_name: Name for the column (default: series name)

        Returns:
            DistributionProfile with statistics
        """
        column = column_name or data.name or "unknown"
        count = len(data)
        null_count = int(data.isna().sum())
        null_percentage = (null_count / count * 100) if count > 0 else 0.0

        profile = DistributionProfile(
            column=column,
            dtype=str(data.dtype),
            count=count,
            null_count=null_count,
            null_percentage=null_percentage,
        )

        # Remove nulls for statistics
        data_clean = data.dropna()

        if len(data_clean) == 0:
            return profile

        # Treat boolean as categorical, not numeric
        if pd.api.types.is_bool_dtype(data):
            self._add_categorical_stats(profile, data_clean)
        elif pd.api.types.is_numeric_dtype(data):
            self._add_numeric_stats(profile, data_clean)
        else:
            self._add_categorical_stats(profile, data_clean)

        return profile

    def _add_numeric_stats(
        self,
        profile: DistributionProfile,
        data: pd.Series,
    ) -> None:
        """Add numeric statistics to profile."""
        profile.mean = float(data.mean())
        profile.std = float(data.std())
        profile.min = float(data.min())
        profile.max = float(data.max())
        profile.median = float(data.median())
        profile.q1 = float(data.quantile(0.25))
        profile.q3 = float(data.quantile(0.75))

        # Skewness and kurtosis
        try:
            profile.skewness = float(data.skew())
            profile.kurtosis = float(data.kurtosis())
        except Exception:
            pass

        # Histogram
        try:
            counts, bins = np.histogram(data, bins=self.n_histogram_bins)
            profile.histogram_bins = [float(b) for b in bins]
            profile.histogram_counts = [int(c) for c in counts]
        except Exception:
            pass

        profile.unique_count = int(data.nunique())

    def _add_categorical_stats(
        self,
        profile: DistributionProfile,
        data: pd.Series,
    ) -> None:
        """Add categorical statistics to profile."""
        profile.unique_count = int(data.nunique())

        value_counts = data.value_counts()
        profile.top_values = {
            str(k): int(v) for k, v in value_counts.head(self.top_n_values).items()
        }

        total = len(data)
        profile.value_frequencies = {
            str(k): float(v / total) for k, v in value_counts.items()
        }

    def profile_dataframe(
        self,
        data: pd.DataFrame,
        columns: list[str] | None = None,
    ) -> dict[str, DistributionProfile]:
        """Create profiles for all columns in DataFrame.

        Args:
            data: DataFrame to profile
            columns: Specific columns to profile (default: all)

        Returns:
            Dictionary mapping column names to profiles
        """
        if columns is None:
            columns = list(data.columns)

        profiles = {}
        for col in columns:
            if col in data.columns:
                profiles[col] = self.profile_column(data[col], col)

        return profiles

    def set_baseline(
        self,
        data: pd.DataFrame,
        columns: list[str] | None = None,
    ) -> dict[str, DistributionProfile]:
        """Set baseline profiles from DataFrame.

        Args:
            data: Baseline DataFrame
            columns: Specific columns (default: all)

        Returns:
            Baseline profiles
        """
        self._baseline_profiles = self.profile_dataframe(data, columns)
        return self._baseline_profiles

    def compare(
        self,
        current_data: pd.DataFrame,
        columns: list[str] | None = None,
    ) -> dict[str, DistributionComparison]:
        """Compare current data to baseline.

        Args:
            current_data: Current DataFrame
            columns: Specific columns to compare

        Returns:
            Dictionary of comparisons
        """
        if not self._baseline_profiles:
            raise ValueError("No baseline set. Call set_baseline() first.")

        if columns is None:
            columns = list(self._baseline_profiles.keys())

        current_profiles = self.profile_dataframe(current_data, columns)
        comparisons = {}

        for col in columns:
            if col not in self._baseline_profiles:
                continue
            if col not in current_profiles:
                continue

            baseline = self._baseline_profiles[col]
            current = current_profiles[col]

            comparison = self._compare_profiles(baseline, current)
            comparisons[col] = comparison

        return comparisons

    def _compare_profiles(
        self,
        baseline: DistributionProfile,
        current: DistributionProfile,
    ) -> DistributionComparison:
        """Compare two profiles."""
        comparison = DistributionComparison(
            column=baseline.column,
            baseline_profile=baseline,
            current_profile=current,
        )

        alerts = []

        # Null rate change
        comparison.null_rate_change = current.null_percentage - baseline.null_percentage
        if abs(comparison.null_rate_change) > self.null_rate_threshold * 100:
            alerts.append(f"Null rate changed by {comparison.null_rate_change:+.2f}%")

        if baseline.is_numeric() and current.is_numeric():
            # Mean change
            if baseline.mean and baseline.mean != 0:
                comparison.mean_change = current.mean - baseline.mean
                comparison.mean_change_pct = (comparison.mean_change / abs(baseline.mean)) * 100

                if abs(comparison.mean_change_pct) > self.mean_change_threshold * 100:
                    alerts.append(f"Mean changed by {comparison.mean_change_pct:+.2f}%")

            # Std change
            if baseline.std and baseline.std != 0:
                comparison.std_change = current.std - baseline.std
                comparison.std_change_pct = (comparison.std_change / abs(baseline.std)) * 100

                if abs(comparison.std_change_pct) > self.std_change_threshold * 100:
                    alerts.append(f"Std changed by {comparison.std_change_pct:+.2f}%")

            # Histogram overlap
            if baseline.histogram_counts and current.histogram_counts:
                comparison.histogram_overlap = self._calculate_histogram_overlap(
                    baseline.histogram_counts,
                    current.histogram_counts,
                )

        else:
            # Categorical comparison
            if baseline.value_frequencies and current.value_frequencies:
                comparison.value_frequency_diff = {}
                all_keys = set(baseline.value_frequencies.keys()) | set(current.value_frequencies.keys())

                for key in all_keys:
                    base_freq = baseline.value_frequencies.get(key, 0.0)
                    curr_freq = current.value_frequencies.get(key, 0.0)
                    diff = curr_freq - base_freq
                    if abs(diff) > 0.01:  # Only track significant diffs
                        comparison.value_frequency_diff[key] = diff

        comparison.alerts = alerts
        comparison.significant_change = len(alerts) > 0

        return comparison

    def _calculate_histogram_overlap(
        self,
        hist1: list[int],
        hist2: list[int],
    ) -> float:
        """Calculate overlap between two histograms."""
        # Normalize histograms
        h1 = np.array(hist1, dtype=float)
        h2 = np.array(hist2, dtype=float)

        if h1.sum() > 0:
            h1 = h1 / h1.sum()
        if h2.sum() > 0:
            h2 = h2 / h2.sum()

        # Calculate overlap (intersection)
        min_len = min(len(h1), len(h2))
        overlap = np.sum(np.minimum(h1[:min_len], h2[:min_len]))

        return float(overlap)

    def get_baseline_profiles(self) -> dict[str, DistributionProfile]:
        """Get current baseline profiles."""
        return self._baseline_profiles.copy()

    def save_baseline(self, filepath: str) -> None:
        """Save baseline profiles to JSON file."""
        data = {
            col: profile.to_dict()
            for col, profile in self._baseline_profiles.items()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_baseline(self, filepath: str) -> None:
        """Load baseline profiles from JSON file."""
        with open(filepath) as f:
            data = json.load(f)

        self._baseline_profiles = {
            col: DistributionProfile.from_dict(profile_data)
            for col, profile_data in data.items()
        }


def create_baseline_profile(
    data: pd.DataFrame,
    columns: list[str] | None = None,
) -> dict[str, DistributionProfile]:
    """Convenience function to create baseline profiles.

    Args:
        data: DataFrame to profile
        columns: Specific columns (default: all)

    Returns:
        Dictionary of column profiles
    """
    monitor = DistributionMonitor()
    return monitor.profile_dataframe(data, columns)
