"""Data drift detection module.

Provides statistical methods for detecting distribution shifts in data.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import pandas as pd
import numpy as np
from datetime import datetime


class DriftType(Enum):
    """Type of drift detected."""

    NONE = "none"
    COVARIATE = "covariate"  # Input feature distribution shift
    CONCEPT = "concept"  # Relationship between features and target changed
    PRIOR = "prior"  # Target distribution shift
    PREDICTION = "prediction"  # Model output distribution shift


@dataclass
class ColumnDrift:
    """Drift detection result for a single column."""

    column: str
    drift_detected: bool
    drift_score: float
    p_value: float | None = None
    statistic: float | None = None
    test_method: str = "ks"
    threshold: float = 0.05
    baseline_stats: dict[str, Any] = field(default_factory=dict)
    current_stats: dict[str, Any] = field(default_factory=dict)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "column": self.column,
            "drift_detected": self.drift_detected,
            "drift_score": self.drift_score,
            "p_value": self.p_value,
            "statistic": self.statistic,
            "test_method": self.test_method,
            "threshold": self.threshold,
            "baseline_stats": self.baseline_stats,
            "current_stats": self.current_stats,
            "message": self.message,
        }


@dataclass
class DriftResult:
    """Overall drift detection result."""

    drift_detected: bool
    drift_type: DriftType
    columns_with_drift: list[str]
    column_results: dict[str, ColumnDrift]
    overall_drift_score: float
    timestamp: datetime = field(default_factory=datetime.now)
    baseline_size: int = 0
    current_size: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "drift_detected": self.drift_detected,
            "drift_type": self.drift_type.value,
            "columns_with_drift": self.columns_with_drift,
            "column_results": {
                col: result.to_dict()
                for col, result in self.column_results.items()
            },
            "overall_drift_score": self.overall_drift_score,
            "timestamp": self.timestamp.isoformat(),
            "baseline_size": self.baseline_size,
            "current_size": self.current_size,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "Drift Detection Summary",
            "=======================",
            f"Drift Detected: {self.drift_detected}",
            f"Drift Type: {self.drift_type.value}",
            f"Overall Score: {self.overall_drift_score:.4f}",
            f"Baseline Size: {self.baseline_size:,}",
            f"Current Size: {self.current_size:,}",
        ]

        if self.columns_with_drift:
            lines.append(f"\nColumns with Drift ({len(self.columns_with_drift)}):")
            for col in self.columns_with_drift:
                result = self.column_results[col]
                p_str = f"{result.p_value:.4f}" if result.p_value is not None else "N/A"
                lines.append(f"  - {col}: score={result.drift_score:.4f}, p={p_str}")

        return "\n".join(lines)


class DriftDetector:
    """Detector for data distribution drift.

    Supports multiple statistical tests for drift detection:
    - KS test (Kolmogorov-Smirnov) for continuous variables
    - Chi-squared test for categorical variables
    - PSI (Population Stability Index) for overall stability
    - Jensen-Shannon divergence
    """

    def __init__(
        self,
        threshold: float = 0.05,
        method: str = "auto",
        categorical_threshold: int = 20,
        psi_threshold: float = 0.1,
    ):
        """Initialize drift detector.

        Args:
            threshold: P-value threshold for drift detection (default 0.05)
            method: Detection method ('ks', 'chi2', 'psi', 'js', 'auto')
            categorical_threshold: Max unique values to treat as categorical
            psi_threshold: PSI threshold for drift (0.1 = slight, 0.25 = significant)
        """
        self.threshold = threshold
        self.method = method
        self.categorical_threshold = categorical_threshold
        self.psi_threshold = psi_threshold
        self._baseline: pd.DataFrame | None = None
        self._baseline_stats: dict[str, dict[str, Any]] = {}

    def set_baseline(self, data: pd.DataFrame) -> None:
        """Set baseline data for comparison.

        Args:
            data: Baseline DataFrame to compare against
        """
        self._baseline = data.copy()
        self._baseline_stats = self._compute_stats(data)

    def _compute_stats(self, data: pd.DataFrame) -> dict[str, dict[str, Any]]:
        """Compute statistics for each column."""
        stats = {}
        for col in data.columns:
            col_stats = {
                "count": len(data[col].dropna()),
                "null_count": data[col].isna().sum(),
                "dtype": str(data[col].dtype),
            }

            if pd.api.types.is_numeric_dtype(data[col]):
                col_stats.update({
                    "mean": float(data[col].mean()) if len(data[col].dropna()) > 0 else None,
                    "std": float(data[col].std()) if len(data[col].dropna()) > 0 else None,
                    "min": float(data[col].min()) if len(data[col].dropna()) > 0 else None,
                    "max": float(data[col].max()) if len(data[col].dropna()) > 0 else None,
                    "median": float(data[col].median()) if len(data[col].dropna()) > 0 else None,
                    "is_numeric": True,
                })
            else:
                value_counts = data[col].value_counts()
                col_stats.update({
                    "unique_count": data[col].nunique(),
                    "top_values": value_counts.head(10).to_dict(),
                    "is_numeric": False,
                })

            stats[col] = col_stats

        return stats

    def detect(
        self,
        current_data: pd.DataFrame,
        columns: list[str] | None = None,
    ) -> DriftResult:
        """Detect drift between baseline and current data.

        Args:
            current_data: Current DataFrame to compare
            columns: Specific columns to check (default: all)

        Returns:
            DriftResult with drift detection details
        """
        if self._baseline is None:
            raise ValueError("Baseline not set. Call set_baseline() first.")

        if columns is None:
            columns = [c for c in self._baseline.columns if c in current_data.columns]

        current_stats = self._compute_stats(current_data[columns])
        column_results = {}
        columns_with_drift = []

        for col in columns:
            if col not in self._baseline.columns:
                continue

            baseline_col = self._baseline[col].dropna()
            current_col = current_data[col].dropna()

            if len(baseline_col) == 0 or len(current_col) == 0:
                column_results[col] = ColumnDrift(
                    column=col,
                    drift_detected=False,
                    drift_score=0.0,
                    message="Insufficient data for comparison",
                )
                continue

            # Choose method
            method = self._choose_method(baseline_col, current_col)

            if method == "ks":
                result = self._ks_test(col, baseline_col, current_col)
            elif method == "chi2":
                result = self._chi2_test(col, baseline_col, current_col)
            elif method == "psi":
                result = self._psi_test(col, baseline_col, current_col)
            elif method == "js":
                result = self._js_divergence(col, baseline_col, current_col)
            else:
                result = self._ks_test(col, baseline_col, current_col)

            result.baseline_stats = self._baseline_stats.get(col, {})
            result.current_stats = current_stats.get(col, {})
            column_results[col] = result

            if result.drift_detected:
                columns_with_drift.append(col)

        # Calculate overall drift score
        if column_results:
            scores = [r.drift_score for r in column_results.values()]
            overall_score = float(np.mean(scores))
        else:
            overall_score = 0.0

        drift_detected = len(columns_with_drift) > 0

        return DriftResult(
            drift_detected=drift_detected,
            drift_type=DriftType.COVARIATE if drift_detected else DriftType.NONE,
            columns_with_drift=columns_with_drift,
            column_results=column_results,
            overall_drift_score=overall_score,
            baseline_size=len(self._baseline),
            current_size=len(current_data),
        )

    def _choose_method(
        self,
        baseline: pd.Series,
        current: pd.Series,
    ) -> str:
        """Choose appropriate test method based on data type."""
        if self.method != "auto":
            return self.method

        if pd.api.types.is_numeric_dtype(baseline):
            return "ks"
        else:
            return "chi2"

    def _ks_test(
        self,
        column: str,
        baseline: pd.Series,
        current: pd.Series,
    ) -> ColumnDrift:
        """Kolmogorov-Smirnov test for continuous variables."""
        try:
            from scipy import stats

            statistic, p_value = stats.ks_2samp(baseline, current)
            drift_detected = p_value < self.threshold

            return ColumnDrift(
                column=column,
                drift_detected=drift_detected,
                drift_score=float(statistic),
                p_value=float(p_value),
                statistic=float(statistic),
                test_method="ks",
                threshold=self.threshold,
                message=f"KS statistic: {statistic:.4f}, p-value: {p_value:.4f}",
            )
        except ImportError:
            # Fallback to simple mean/std comparison
            return self._simple_numeric_test(column, baseline, current)

    def _simple_numeric_test(
        self,
        column: str,
        baseline: pd.Series,
        current: pd.Series,
    ) -> ColumnDrift:
        """Simple mean/std comparison when scipy not available."""
        baseline_mean = baseline.mean()
        current_mean = current.mean()
        baseline_std = baseline.std()

        if baseline_std > 0:
            z_score = abs(current_mean - baseline_mean) / baseline_std
            drift_detected = z_score > 2.0  # 2 std deviations
            drift_score = min(z_score / 4.0, 1.0)  # Normalize to 0-1
        else:
            drift_detected = baseline_mean != current_mean
            drift_score = 1.0 if drift_detected else 0.0

        return ColumnDrift(
            column=column,
            drift_detected=drift_detected,
            drift_score=float(drift_score),
            p_value=None,
            statistic=float(z_score) if baseline_std > 0 else None,
            test_method="mean_comparison",
            threshold=self.threshold,
            message=f"Mean shift: {baseline_mean:.4f} -> {current_mean:.4f}",
        )

    def _chi2_test(
        self,
        column: str,
        baseline: pd.Series,
        current: pd.Series,
    ) -> ColumnDrift:
        """Chi-squared test for categorical variables."""
        try:
            from scipy import stats

            # Get all categories
            all_categories = set(baseline.unique()) | set(current.unique())

            # Calculate frequencies
            baseline_counts = baseline.value_counts()
            current_counts = current.value_counts()

            # Align to same categories (use counts, not frequencies)
            baseline_freq = np.array([
                baseline_counts.get(cat, 0) for cat in all_categories
            ])
            current_freq = np.array([
                current_counts.get(cat, 0) for cat in all_categories
            ])

            # Add small constant to avoid zero counts (chi-square requirement)
            baseline_freq = baseline_freq + 1e-10
            current_freq = current_freq + 1e-10

            # Chi-squared statistic (using counts, not normalized frequencies)
            statistic, p_value = stats.chisquare(current_freq, baseline_freq)
            drift_detected = p_value < self.threshold

            return ColumnDrift(
                column=column,
                drift_detected=drift_detected,
                drift_score=min(float(statistic) / 100, 1.0),  # Normalize
                p_value=float(p_value),
                statistic=float(statistic),
                test_method="chi2",
                threshold=self.threshold,
                message=f"Chi2 statistic: {statistic:.4f}, p-value: {p_value:.4f}",
            )
        except ImportError:
            return self._simple_categorical_test(column, baseline, current)

    def _simple_categorical_test(
        self,
        column: str,
        baseline: pd.Series,
        current: pd.Series,
    ) -> ColumnDrift:
        """Simple category distribution comparison."""
        baseline_dist = baseline.value_counts(normalize=True)
        current_dist = current.value_counts(normalize=True)

        # Calculate max difference in proportions
        all_categories = set(baseline_dist.index) | set(current_dist.index)
        max_diff = 0.0

        for cat in all_categories:
            base_prop = baseline_dist.get(cat, 0.0)
            curr_prop = current_dist.get(cat, 0.0)
            max_diff = max(max_diff, abs(base_prop - curr_prop))

        drift_detected = max_diff > 0.1  # 10% difference threshold

        return ColumnDrift(
            column=column,
            drift_detected=drift_detected,
            drift_score=float(max_diff),
            p_value=None,
            statistic=float(max_diff),
            test_method="proportion_diff",
            threshold=0.1,
            message=f"Max proportion difference: {max_diff:.4f}",
        )

    def _psi_test(
        self,
        column: str,
        baseline: pd.Series,
        current: pd.Series,
    ) -> ColumnDrift:
        """Population Stability Index test."""
        # Create buckets
        n_buckets = min(10, len(baseline.unique()))

        if pd.api.types.is_numeric_dtype(baseline):
            # Numeric: use quantile-based buckets
            try:
                buckets = pd.qcut(baseline, q=n_buckets, duplicates='drop')
                bucket_edges = buckets.cat.categories

                baseline_counts = baseline.groupby(buckets, observed=False).count()
                current_buckets = pd.cut(current, bins=bucket_edges)
                current_counts = current.groupby(current_buckets, observed=False).count()
            except Exception:
                return self._ks_test(column, baseline, current)
        else:
            # Categorical: use value counts
            baseline_counts = baseline.value_counts()
            current_counts = current.value_counts()

            # Align
            all_cats = set(baseline_counts.index) | set(current_counts.index)
            baseline_counts = pd.Series({
                cat: baseline_counts.get(cat, 0) for cat in all_cats
            })
            current_counts = pd.Series({
                cat: current_counts.get(cat, 0) for cat in all_cats
            })

        # Calculate PSI
        baseline_pct = baseline_counts / baseline_counts.sum()
        current_pct = current_counts / current_counts.sum()

        # Add small constant to avoid log(0)
        baseline_pct = baseline_pct + 1e-10
        current_pct = current_pct + 1e-10

        psi = np.sum(
            (current_pct - baseline_pct) * np.log(current_pct / baseline_pct)
        )

        drift_detected = psi > self.psi_threshold

        return ColumnDrift(
            column=column,
            drift_detected=drift_detected,
            drift_score=float(psi),
            p_value=None,
            statistic=float(psi),
            test_method="psi",
            threshold=self.psi_threshold,
            message=f"PSI: {psi:.4f} (threshold: {self.psi_threshold})",
        )

    def _js_divergence(
        self,
        column: str,
        baseline: pd.Series,
        current: pd.Series,
    ) -> ColumnDrift:
        """Jensen-Shannon divergence test."""
        try:
            from scipy.spatial.distance import jensenshannon

            # Create histograms
            n_bins = min(50, max(10, len(baseline) // 100))

            if pd.api.types.is_numeric_dtype(baseline):
                min_val = min(baseline.min(), current.min())
                max_val = max(baseline.max(), current.max())
                bins = np.linspace(min_val, max_val, n_bins + 1)

                baseline_hist, _ = np.histogram(baseline, bins=bins, density=True)
                current_hist, _ = np.histogram(current, bins=bins, density=True)
            else:
                all_cats = list(set(baseline.unique()) | set(current.unique()))
                baseline_hist = np.array([
                    (baseline == cat).sum() / len(baseline) for cat in all_cats
                ])
                current_hist = np.array([
                    (current == cat).sum() / len(current) for cat in all_cats
                ])

            # Add small constant
            baseline_hist = baseline_hist + 1e-10
            current_hist = current_hist + 1e-10

            # Normalize
            baseline_hist = baseline_hist / baseline_hist.sum()
            current_hist = current_hist / current_hist.sum()

            js_distance = jensenshannon(baseline_hist, current_hist)
            drift_detected = js_distance > 0.1  # Threshold for JS divergence

            return ColumnDrift(
                column=column,
                drift_detected=drift_detected,
                drift_score=float(js_distance),
                p_value=None,
                statistic=float(js_distance),
                test_method="js_divergence",
                threshold=0.1,
                message=f"JS Divergence: {js_distance:.4f}",
            )
        except ImportError:
            return self._ks_test(column, baseline, current)


def detect_drift(
    baseline: pd.DataFrame,
    current: pd.DataFrame,
    columns: list[str] | None = None,
    threshold: float = 0.05,
    method: str = "auto",
) -> DriftResult:
    """Convenience function to detect drift.

    Args:
        baseline: Baseline DataFrame
        current: Current DataFrame to compare
        columns: Specific columns to check
        threshold: P-value threshold for drift detection
        method: Detection method

    Returns:
        DriftResult with drift detection details
    """
    detector = DriftDetector(threshold=threshold, method=method)
    detector.set_baseline(baseline)
    return detector.detect(current, columns=columns)
