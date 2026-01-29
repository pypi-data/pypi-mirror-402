"""Statistical analysis utilities.

This module provides statistical significance testing and analysis
utilities for profile comparison and data quality assessment.

Features:
    - T-test for comparing means
    - Mann-Whitney U test for non-parametric comparison
    - Chi-square test for categorical data
    - Effect size calculation (Cohen's d)
    - Confidence interval estimation
    - Trend significance detection
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class SignificanceLevel(str, Enum):
    """Statistical significance levels."""

    NOT_SIGNIFICANT = "not_significant"
    MARGINALLY_SIGNIFICANT = "marginally_significant"  # p < 0.10
    SIGNIFICANT = "significant"  # p < 0.05
    HIGHLY_SIGNIFICANT = "highly_significant"  # p < 0.01
    VERY_HIGHLY_SIGNIFICANT = "very_highly_significant"  # p < 0.001


class EffectSize(str, Enum):
    """Cohen's d effect size interpretation."""

    NEGLIGIBLE = "negligible"  # < 0.2
    SMALL = "small"  # 0.2 - 0.5
    MEDIUM = "medium"  # 0.5 - 0.8
    LARGE = "large"  # > 0.8


@dataclass
class StatisticalTestResult:
    """Result of a statistical significance test."""

    test_name: str
    statistic: float
    p_value: float
    significance_level: SignificanceLevel
    effect_size: float | None = None
    effect_interpretation: EffectSize | None = None
    confidence_interval: tuple[float, float] | None = None
    sample_sizes: tuple[int, int] | None = None
    is_significant: bool = False
    interpretation: str = ""


def _compute_mean(values: Sequence[float]) -> float:
    """Compute mean of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def _compute_variance(values: Sequence[float], ddof: int = 1) -> float:
    """Compute variance with degrees of freedom adjustment."""
    if len(values) <= ddof:
        return 0.0
    mean = _compute_mean(values)
    squared_diffs = [(x - mean) ** 2 for x in values]
    return sum(squared_diffs) / (len(values) - ddof)


def _compute_std(values: Sequence[float], ddof: int = 1) -> float:
    """Compute standard deviation."""
    return math.sqrt(_compute_variance(values, ddof))


def _pooled_std(
    values1: Sequence[float],
    values2: Sequence[float],
) -> float:
    """Compute pooled standard deviation for two groups."""
    n1 = len(values1)
    n2 = len(values2)

    if n1 <= 1 or n2 <= 1:
        return 0.0

    var1 = _compute_variance(values1, ddof=1)
    var2 = _compute_variance(values2, ddof=1)

    # Pooled variance formula
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    return math.sqrt(pooled_var)


def cohens_d(
    values1: Sequence[float],
    values2: Sequence[float],
) -> float:
    """Calculate Cohen's d effect size.

    Args:
        values1: First group values.
        values2: Second group values.

    Returns:
        Cohen's d effect size.
    """
    mean1 = _compute_mean(values1)
    mean2 = _compute_mean(values2)
    pooled = _pooled_std(values1, values2)

    if pooled == 0:
        return 0.0

    return abs(mean1 - mean2) / pooled


def interpret_effect_size(d: float) -> EffectSize:
    """Interpret Cohen's d effect size.

    Args:
        d: Cohen's d value.

    Returns:
        Effect size interpretation.
    """
    abs_d = abs(d)
    if abs_d < 0.2:
        return EffectSize.NEGLIGIBLE
    elif abs_d < 0.5:
        return EffectSize.SMALL
    elif abs_d < 0.8:
        return EffectSize.MEDIUM
    else:
        return EffectSize.LARGE


def interpret_p_value(p_value: float) -> SignificanceLevel:
    """Interpret p-value significance level.

    Args:
        p_value: P-value from statistical test.

    Returns:
        Significance level interpretation.
    """
    if p_value >= 0.10:
        return SignificanceLevel.NOT_SIGNIFICANT
    elif p_value >= 0.05:
        return SignificanceLevel.MARGINALLY_SIGNIFICANT
    elif p_value >= 0.01:
        return SignificanceLevel.SIGNIFICANT
    elif p_value >= 0.001:
        return SignificanceLevel.HIGHLY_SIGNIFICANT
    else:
        return SignificanceLevel.VERY_HIGHLY_SIGNIFICANT


def _t_distribution_cdf(t: float, df: int) -> float:
    """Approximate CDF of t-distribution using normal approximation.

    For large df, t-distribution approaches normal.
    This is a simplified implementation without scipy.
    """
    # Use normal approximation for large df
    if df > 100:
        # Approximate using normal distribution
        return _normal_cdf(t)

    # For smaller df, use a simple approximation
    # This is not exact but provides reasonable estimates
    x = t / math.sqrt(df)
    a = 0.5 * (1 + x / math.sqrt(1 + x * x))
    return a


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF using error function approximation."""
    # Approximation of standard normal CDF
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def welch_t_test(
    values1: Sequence[float],
    values2: Sequence[float],
    alpha: float = 0.05,
) -> StatisticalTestResult:
    """Perform Welch's t-test for comparing two group means.

    Welch's t-test is more robust than Student's t-test when
    variances are unequal (heteroscedastic data).

    Args:
        values1: First group values.
        values2: Second group values.
        alpha: Significance level.

    Returns:
        Statistical test result.
    """
    n1, n2 = len(values1), len(values2)

    if n1 < 2 or n2 < 2:
        return StatisticalTestResult(
            test_name="Welch's t-test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Insufficient data for t-test (need at least 2 samples per group)",
            sample_sizes=(n1, n2),
        )

    mean1 = _compute_mean(values1)
    mean2 = _compute_mean(values2)
    var1 = _compute_variance(values1)
    var2 = _compute_variance(values2)

    # Welch's t-statistic
    se1 = var1 / n1
    se2 = var2 / n2
    se_diff = math.sqrt(se1 + se2)

    if se_diff == 0:
        return StatisticalTestResult(
            test_name="Welch's t-test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Zero variance in both groups",
            sample_sizes=(n1, n2),
        )

    t_stat = (mean1 - mean2) / se_diff

    # Welch-Satterthwaite degrees of freedom
    if se1 + se2 == 0:
        df = n1 + n2 - 2
    else:
        df_num = (se1 + se2) ** 2
        df_denom = (se1 ** 2) / (n1 - 1) + (se2 ** 2) / (n2 - 1)
        if df_denom == 0:
            df = n1 + n2 - 2
        else:
            df = df_num / df_denom

    # Two-tailed p-value (approximation)
    p_value = 2 * (1 - _t_distribution_cdf(abs(t_stat), int(df)))
    p_value = max(0.0, min(1.0, p_value))  # Clamp to [0, 1]

    # Effect size
    d = cohens_d(values1, values2)
    effect_interp = interpret_effect_size(d)

    # Confidence interval for difference in means
    se = se_diff
    # Use z-value approximation for large samples
    z = 1.96 if alpha == 0.05 else 2.576 if alpha == 0.01 else 1.645
    ci_low = (mean1 - mean2) - z * se
    ci_high = (mean1 - mean2) + z * se

    # Interpret results
    sig_level = interpret_p_value(p_value)
    is_significant = p_value < alpha

    if is_significant:
        direction = "higher" if mean1 > mean2 else "lower"
        interp = (
            f"Statistically significant difference (p={p_value:.4f}). "
            f"Group 1 mean ({mean1:.2f}) is {direction} than Group 2 mean ({mean2:.2f}). "
            f"Effect size: {effect_interp.value} (d={d:.2f})"
        )
    else:
        interp = (
            f"No statistically significant difference (p={p_value:.4f}). "
            f"Group 1 mean: {mean1:.2f}, Group 2 mean: {mean2:.2f}"
        )

    return StatisticalTestResult(
        test_name="Welch's t-test",
        statistic=t_stat,
        p_value=p_value,
        significance_level=sig_level,
        effect_size=d,
        effect_interpretation=effect_interp,
        confidence_interval=(ci_low, ci_high),
        sample_sizes=(n1, n2),
        is_significant=is_significant,
        interpretation=interp,
    )


def mann_whitney_u_test(
    values1: Sequence[float],
    values2: Sequence[float],
    alpha: float = 0.05,
) -> StatisticalTestResult:
    """Perform Mann-Whitney U test (non-parametric).

    Non-parametric alternative to t-test that doesn't assume
    normal distribution. Tests whether one group tends to have
    larger values than the other.

    Args:
        values1: First group values.
        values2: Second group values.
        alpha: Significance level.

    Returns:
        Statistical test result.
    """
    n1, n2 = len(values1), len(values2)

    if n1 < 1 or n2 < 1:
        return StatisticalTestResult(
            test_name="Mann-Whitney U test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Insufficient data for Mann-Whitney test",
            sample_sizes=(n1, n2),
        )

    # Combine and rank all values
    combined = [(v, 1) for v in values1] + [(v, 2) for v in values2]
    combined.sort(key=lambda x: x[0])

    # Assign ranks (handle ties with average rank)
    ranks: dict[int, float] = {}
    i = 0
    while i < len(combined):
        j = i
        # Find all tied values
        while j < len(combined) and combined[j][0] == combined[i][0]:
            j += 1
        # Assign average rank to all tied values
        avg_rank = (i + j + 1) / 2  # Ranks are 1-based
        for k in range(i, j):
            ranks[k] = avg_rank
        i = j

    # Sum ranks for each group
    r1 = sum(ranks[i] for i, (_, group) in enumerate(combined) if group == 1)

    # Calculate U statistic
    u1 = r1 - n1 * (n1 + 1) / 2
    u2 = n1 * n2 - u1
    u = min(u1, u2)

    # Normal approximation for large samples
    mu = n1 * n2 / 2

    # Tie correction for standard deviation
    n = n1 + n2
    tie_sum = 0
    unique_values: dict[float, int] = {}
    for v, _ in combined:
        unique_values[v] = unique_values.get(v, 0) + 1
    for count in unique_values.values():
        if count > 1:
            tie_sum += count ** 3 - count

    sigma = math.sqrt(
        (n1 * n2 / 12) * (n + 1 - tie_sum / (n * (n - 1)))
        if n > 1 else 0
    )

    if sigma == 0:
        z = 0
        p_value = 1.0
    else:
        z = (u - mu) / sigma
        p_value = 2 * (1 - _normal_cdf(abs(z)))
        p_value = max(0.0, min(1.0, p_value))

    # Calculate effect size (rank-biserial correlation)
    # r = 1 - (2*U)/(n1*n2)
    if n1 * n2 > 0:
        r = 1 - (2 * u) / (n1 * n2)
    else:
        r = 0.0

    # Interpret effect size
    abs_r = abs(r)
    if abs_r < 0.1:
        effect_interp = EffectSize.NEGLIGIBLE
    elif abs_r < 0.3:
        effect_interp = EffectSize.SMALL
    elif abs_r < 0.5:
        effect_interp = EffectSize.MEDIUM
    else:
        effect_interp = EffectSize.LARGE

    sig_level = interpret_p_value(p_value)
    is_significant = p_value < alpha

    if is_significant:
        median1 = sorted(values1)[n1 // 2] if n1 > 0 else 0
        median2 = sorted(values2)[n2 // 2] if n2 > 0 else 0
        direction = "tends to be higher" if u1 > u2 else "tends to be lower"
        interp = (
            f"Statistically significant difference (p={p_value:.4f}). "
            f"Group 1 (median={median1:.2f}) {direction} than Group 2 (median={median2:.2f}). "
            f"Effect size: {effect_interp.value} (r={r:.2f})"
        )
    else:
        interp = (
            f"No statistically significant difference (p={p_value:.4f}). "
            f"Distributions are similar."
        )

    return StatisticalTestResult(
        test_name="Mann-Whitney U test",
        statistic=u,
        p_value=p_value,
        significance_level=sig_level,
        effect_size=r,
        effect_interpretation=effect_interp,
        sample_sizes=(n1, n2),
        is_significant=is_significant,
        interpretation=interp,
    )


def chi_square_test(
    observed1: Sequence[int],
    observed2: Sequence[int],
    alpha: float = 0.05,
) -> StatisticalTestResult:
    """Perform chi-square test for comparing categorical distributions.

    Args:
        observed1: First group category counts.
        observed2: Second group category counts.
        alpha: Significance level.

    Returns:
        Statistical test result.
    """
    if len(observed1) != len(observed2):
        return StatisticalTestResult(
            test_name="Chi-square test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Categories must match between groups",
        )

    k = len(observed1)  # Number of categories

    if k < 2:
        return StatisticalTestResult(
            test_name="Chi-square test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Need at least 2 categories",
        )

    total1 = sum(observed1)
    total2 = sum(observed2)
    total = total1 + total2

    if total == 0:
        return StatisticalTestResult(
            test_name="Chi-square test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="No observations",
        )

    # Calculate chi-square statistic
    chi2 = 0.0
    for i in range(k):
        row_total = observed1[i] + observed2[i]

        # Expected values under null hypothesis
        expected1 = (row_total * total1) / total if total > 0 else 0
        expected2 = (row_total * total2) / total if total > 0 else 0

        if expected1 > 0:
            chi2 += (observed1[i] - expected1) ** 2 / expected1
        if expected2 > 0:
            chi2 += (observed2[i] - expected2) ** 2 / expected2

    # Degrees of freedom
    df = k - 1

    # Approximate p-value using chi-square distribution
    # Using Wilson-Hilferty approximation
    if df > 0:
        z = ((chi2 / df) ** (1/3) - (1 - 2 / (9 * df))) / math.sqrt(2 / (9 * df))
        p_value = 1 - _normal_cdf(z)
        p_value = max(0.0, min(1.0, p_value))
    else:
        p_value = 1.0

    # Effect size (Cramer's V)
    min_dim = 1  # 2 groups - 1
    if total > 0 and min_dim > 0:
        cramers_v = math.sqrt(chi2 / (total * min_dim))
    else:
        cramers_v = 0.0

    # Interpret effect size
    if cramers_v < 0.1:
        effect_interp = EffectSize.NEGLIGIBLE
    elif cramers_v < 0.3:
        effect_interp = EffectSize.SMALL
    elif cramers_v < 0.5:
        effect_interp = EffectSize.MEDIUM
    else:
        effect_interp = EffectSize.LARGE

    sig_level = interpret_p_value(p_value)
    is_significant = p_value < alpha

    if is_significant:
        interp = (
            f"Statistically significant difference in distributions (p={p_value:.4f}, "
            f"χ²={chi2:.2f}, df={df}). Effect size: {effect_interp.value} (V={cramers_v:.2f})"
        )
    else:
        interp = (
            f"No significant difference in distributions (p={p_value:.4f}, "
            f"χ²={chi2:.2f}, df={df})"
        )

    return StatisticalTestResult(
        test_name="Chi-square test",
        statistic=chi2,
        p_value=p_value,
        significance_level=sig_level,
        effect_size=cramers_v,
        effect_interpretation=effect_interp,
        sample_sizes=(int(total1), int(total2)),
        is_significant=is_significant,
        interpretation=interp,
    )


def trend_significance_test(
    values: Sequence[float],
    timestamps: Sequence[float] | None = None,
    alpha: float = 0.05,
) -> StatisticalTestResult:
    """Test for significant trend over time using linear regression.

    Args:
        values: Time series values.
        timestamps: Optional timestamps (uses indices if not provided).
        alpha: Significance level.

    Returns:
        Statistical test result.
    """
    n = len(values)

    if n < 3:
        return StatisticalTestResult(
            test_name="Trend significance test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Need at least 3 data points for trend analysis",
            sample_sizes=(n, 0),
        )

    # Use indices if no timestamps provided
    x = list(timestamps) if timestamps else list(range(n))
    y = list(values)

    # Calculate linear regression
    mean_x = _compute_mean(x)
    mean_y = _compute_mean(y)

    # Slope and intercept
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominator = sum((xi - mean_x) ** 2 for xi in x)

    if denominator == 0:
        return StatisticalTestResult(
            test_name="Trend significance test",
            statistic=0.0,
            p_value=1.0,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            is_significant=False,
            interpretation="Cannot calculate trend (constant x values)",
            sample_sizes=(n, 0),
        )

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x

    # Calculate residuals and standard error
    residuals = [yi - (slope * xi + intercept) for xi, yi in zip(x, y)]
    sse = sum(r ** 2 for r in residuals)
    mse = sse / (n - 2) if n > 2 else 0

    se_slope = math.sqrt(mse / denominator) if mse > 0 and denominator > 0 else 0

    # T-statistic for slope
    if se_slope > 0:
        t_stat = slope / se_slope
        df = n - 2
        p_value = 2 * (1 - _t_distribution_cdf(abs(t_stat), df))
        p_value = max(0.0, min(1.0, p_value))
    else:
        t_stat = 0.0
        p_value = 1.0

    # R-squared
    ss_total = sum((yi - mean_y) ** 2 for yi in y)
    r_squared = 1 - (sse / ss_total) if ss_total > 0 else 0

    sig_level = interpret_p_value(p_value)
    is_significant = p_value < alpha

    # Interpret trend direction
    if slope > 0:
        direction = "increasing"
    elif slope < 0:
        direction = "decreasing"
    else:
        direction = "flat"

    if is_significant:
        interp = (
            f"Statistically significant {direction} trend (p={p_value:.4f}). "
            f"Slope: {slope:.4f} per unit, R²={r_squared:.2f}"
        )
    else:
        interp = (
            f"No significant trend detected (p={p_value:.4f}). "
            f"Slope: {slope:.4f}, R²={r_squared:.2f}"
        )

    return StatisticalTestResult(
        test_name="Trend significance test",
        statistic=t_stat,
        p_value=p_value,
        significance_level=sig_level,
        effect_size=slope,
        sample_sizes=(n, 0),
        is_significant=is_significant,
        interpretation=interp,
    )


@dataclass
class ComparisonResult:
    """Result of comparing two data series with multiple tests."""

    t_test: StatisticalTestResult
    mann_whitney: StatisticalTestResult
    recommended_test: str
    overall_significant: bool
    summary: str


def comprehensive_comparison(
    values1: Sequence[float],
    values2: Sequence[float],
    alpha: float = 0.05,
) -> ComparisonResult:
    """Perform comprehensive statistical comparison.

    Runs multiple tests and provides recommendation based on data characteristics.

    Args:
        values1: First group values.
        values2: Second group values.
        alpha: Significance level.

    Returns:
        Comprehensive comparison result.
    """
    t_result = welch_t_test(values1, values2, alpha)
    mw_result = mann_whitney_u_test(values1, values2, alpha)

    n1, n2 = len(values1), len(values2)

    # Recommend test based on sample size and distribution
    if n1 < 30 or n2 < 30:
        # Small samples - use non-parametric
        recommended = "Mann-Whitney U test"
        primary_result = mw_result
    else:
        # Large samples - t-test is robust
        recommended = "Welch's t-test"
        primary_result = t_result

    # Overall significance
    overall = primary_result.is_significant

    # Summary
    if overall:
        summary = f"Significant difference detected ({recommended}, p={primary_result.p_value:.4f})"
    else:
        summary = f"No significant difference ({recommended}, p={primary_result.p_value:.4f})"

    return ComparisonResult(
        t_test=t_result,
        mann_whitney=mw_result,
        recommended_test=recommended,
        overall_significant=overall,
        summary=summary,
    )
