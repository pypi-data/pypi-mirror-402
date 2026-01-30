"""Performance benchmarks for unlockedpd operations.

This module establishes baseline performance metrics for all operation categories:
- Aggregations (sum, mean, std, var, min, max, median, prod)
- Rolling operations (window=20 on 10000 rows)
- Expanding operations (on 10000 rows)
- EWM operations (span=20 on 10000 rows)
- Transform operations (diff, pct_change, shift)
- Cumulative operations (cumsum, cumprod, cummin, cummax)
"""
import pytest
import pandas as pd
import numpy as np

# Import unlockedpd to enable optimizations
import unlockedpd


@pytest.fixture
def standard_df():
    """Standard DataFrame for benchmarking - 10000 rows, 10 columns."""
    np.random.seed(42)
    return pd.DataFrame(
        np.random.randn(10000, 10),
        columns=[f'col_{i}' for i in range(10)]
    )


@pytest.fixture
def large_df():
    """Large DataFrame for benchmarking - 100000 rows, 50 columns."""
    np.random.seed(42)
    return pd.DataFrame(
        np.random.randn(100000, 50),
        columns=[f'col_{i}' for i in range(50)]
    )


class TestAggregationBenchmarks:
    """Benchmarks for aggregation operations."""

    def test_bench_sum(self, benchmark, standard_df):
        """Benchmark sum aggregation."""
        benchmark(standard_df.sum)

    def test_bench_mean(self, benchmark, standard_df):
        """Benchmark mean aggregation."""
        benchmark(standard_df.mean)

    def test_bench_std(self, benchmark, standard_df):
        """Benchmark std aggregation."""
        benchmark(standard_df.std)

    def test_bench_var(self, benchmark, standard_df):
        """Benchmark var aggregation."""
        benchmark(standard_df.var)

    def test_bench_min(self, benchmark, standard_df):
        """Benchmark min aggregation."""
        benchmark(standard_df.min)

    def test_bench_max(self, benchmark, standard_df):
        """Benchmark max aggregation."""
        benchmark(standard_df.max)

    def test_bench_median(self, benchmark, standard_df):
        """Benchmark median aggregation."""
        benchmark(standard_df.median)

    def test_bench_prod(self, benchmark, standard_df):
        """Benchmark prod aggregation."""
        benchmark(standard_df.prod)


class TestRollingBenchmarks:
    """Benchmarks for rolling operations."""

    def test_bench_rolling_sum(self, benchmark, standard_df):
        """Benchmark rolling sum with window=20."""
        benchmark(lambda: standard_df.rolling(20).sum())

    def test_bench_rolling_mean(self, benchmark, standard_df):
        """Benchmark rolling mean with window=20."""
        benchmark(lambda: standard_df.rolling(20).mean())

    def test_bench_rolling_std(self, benchmark, standard_df):
        """Benchmark rolling std with window=20."""
        benchmark(lambda: standard_df.rolling(20).std())

    def test_bench_rolling_var(self, benchmark, standard_df):
        """Benchmark rolling var with window=20."""
        benchmark(lambda: standard_df.rolling(20).var())

    def test_bench_rolling_min(self, benchmark, standard_df):
        """Benchmark rolling min with window=20."""
        benchmark(lambda: standard_df.rolling(20).min())

    def test_bench_rolling_max(self, benchmark, standard_df):
        """Benchmark rolling max with window=20."""
        benchmark(lambda: standard_df.rolling(20).max())

    def test_bench_rolling_median(self, benchmark, standard_df):
        """Benchmark rolling median with window=20."""
        benchmark(lambda: standard_df.rolling(20).median())


class TestExpandingBenchmarks:
    """Benchmarks for expanding operations."""

    def test_bench_expanding_sum(self, benchmark, standard_df):
        """Benchmark expanding sum."""
        benchmark(lambda: standard_df.expanding().sum())

    def test_bench_expanding_mean(self, benchmark, standard_df):
        """Benchmark expanding mean."""
        benchmark(lambda: standard_df.expanding().mean())

    def test_bench_expanding_std(self, benchmark, standard_df):
        """Benchmark expanding std."""
        benchmark(lambda: standard_df.expanding().std())

    def test_bench_expanding_var(self, benchmark, standard_df):
        """Benchmark expanding var."""
        benchmark(lambda: standard_df.expanding().var())

    def test_bench_expanding_min(self, benchmark, standard_df):
        """Benchmark expanding min."""
        benchmark(lambda: standard_df.expanding().min())

    def test_bench_expanding_max(self, benchmark, standard_df):
        """Benchmark expanding max."""
        benchmark(lambda: standard_df.expanding().max())


class TestEWMBenchmarks:
    """Benchmarks for exponentially weighted moving operations."""

    def test_bench_ewm_mean(self, benchmark, standard_df):
        """Benchmark EWM mean with span=20."""
        benchmark(lambda: standard_df.ewm(span=20).mean())

    def test_bench_ewm_std(self, benchmark, standard_df):
        """Benchmark EWM std with span=20."""
        benchmark(lambda: standard_df.ewm(span=20).std())

    def test_bench_ewm_var(self, benchmark, standard_df):
        """Benchmark EWM var with span=20."""
        benchmark(lambda: standard_df.ewm(span=20).var())


class TestTransformBenchmarks:
    """Benchmarks for transform operations."""

    def test_bench_diff(self, benchmark, standard_df):
        """Benchmark diff operation."""
        benchmark(standard_df.diff)

    def test_bench_pct_change(self, benchmark, standard_df):
        """Benchmark pct_change operation."""
        benchmark(standard_df.pct_change)

    def test_bench_shift(self, benchmark, standard_df):
        """Benchmark shift operation."""
        benchmark(lambda: standard_df.shift(1))


class TestCumulativeBenchmarks:
    """Benchmarks for cumulative operations."""

    def test_bench_cumsum(self, benchmark, standard_df):
        """Benchmark cumsum operation."""
        benchmark(standard_df.cumsum)

    def test_bench_cumprod(self, benchmark, standard_df):
        """Benchmark cumprod operation."""
        benchmark(standard_df.cumprod)

    def test_bench_cummin(self, benchmark, standard_df):
        """Benchmark cummin operation."""
        benchmark(standard_df.cummin)

    def test_bench_cummax(self, benchmark, standard_df):
        """Benchmark cummax operation."""
        benchmark(standard_df.cummax)


class TestLargeDataBenchmarks:
    """Benchmarks using large dataset to stress test parallelization."""

    def test_bench_large_sum(self, benchmark, large_df):
        """Benchmark sum on large dataset."""
        benchmark(large_df.sum)

    def test_bench_large_rolling_mean(self, benchmark, large_df):
        """Benchmark rolling mean on large dataset."""
        benchmark(lambda: large_df.rolling(20).mean())

    def test_bench_large_pct_change(self, benchmark, large_df):
        """Benchmark pct_change on large dataset."""
        benchmark(large_df.pct_change)

    def test_bench_large_cumsum(self, benchmark, large_df):
        """Benchmark cumsum on large dataset."""
        benchmark(large_df.cumsum)


class TestRankBenchmarks:
    """Benchmarks for rank operations."""

    def test_bench_rank_axis0(self, benchmark, standard_df):
        """Benchmark rank along axis=0."""
        benchmark(lambda: standard_df.rank(axis=0))

    def test_bench_rank_axis1(self, benchmark, standard_df):
        """Benchmark rank along axis=1."""
        benchmark(lambda: standard_df.rank(axis=1))


if __name__ == '__main__':
    # Verify imports work correctly
    print("Successfully imported bench_baseline module")
    print(f"unlockedpd version: {unlockedpd.__version__}")
    print(f"unlockedpd enabled: {unlockedpd.config.enabled}")
