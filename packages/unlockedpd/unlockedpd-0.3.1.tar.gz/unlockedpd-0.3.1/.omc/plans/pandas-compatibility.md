# Pandas Compatibility Enhancement Plan

## Context

### Original Request
Cover uncovered areas of pandas operations, preserve mathematical/edge case/NaN handling behavior identical to pandas 100%.

### Scope Clarification
**This plan is PHASE 1: Edge Case Compatibility for Existing Operations.**

A separate PHASE 2 plan will cover implementing missing operations (count, first, last, idxmin, idxmax, all, any, nunique, quantile, abs, clip, round, fillna, dropna, isna, notna, corr, cov, etc.).

This plan focuses on:
- Verifying and fixing edge case behavior for all currently implemented operations
- Ensuring 100% behavioral match with pandas for inf/-inf, NaN, empty, single-value scenarios
- Establishing performance baselines before any changes

### Codebase Analysis Summary

**Currently Optimized Operations (in scope):**
- **Rolling:** sum, mean, std, var, min, max, skew, kurt, count, median, quantile (11 operations)
- **Expanding:** sum, mean, std, var, min, max, count, skew, kurt (9 operations)
- **EWM:** mean, std, var (3 operations)
- **Aggregations:** sum, mean, std, var, min, max, median, prod (8 operations via agg/aggregate)
- **Transform:** diff, pct_change, shift (3 operations)
- **Stats:** skew, kurt, sem (3 operations)
- **Cumulative:** cumsum, cumprod, cummin, cummax (4 operations)
- **Rank:** rank (both axis=0 and axis=1)

**Test Coverage:**
- 52 pandas compatibility tests currently passing
- Tests cover basic operations, NaN handling, all-NaN columns, zero variance cases
- Tests use rtol=1e-10 for strict numerical equivalence

**Known Issue in test_extreme_edge_cases.py:**
- Lines 110-130 import `unlockedpd.ops.fillna` which does not exist
- These tests must be skipped or removed in Task 1 (fillna is out of scope for Phase 1)

---

## Pandas Edge Case Behavior Reference Table

### inf/-inf in Aggregations

| Input | sum | mean | min | max | std | var | prod | median |
|-------|-----|------|-----|-----|-----|-----|------|--------|
| `[inf, 1, 2]` | inf | inf | 1.0 | inf | nan | nan | inf | 2.0 |
| `[-inf, 1, 2]` | -inf | -inf | -inf | 2.0 | nan | nan | -inf | 1.0 |
| `[inf, -inf, 1]` | nan | nan | -inf | inf | nan | nan | -inf | 1.0 |
| `[inf, inf, inf]` | inf | inf | inf | inf | nan | nan | inf | inf |

### Empty DataFrame Behavior

| Shape | sum | mean | min | max | std | var |
|-------|-----|------|-----|-----|-----|-----|
| 0 rows, N cols (typed) | 0.0 per col | nan per col | nan per col | nan per col | nan per col | nan per col |
| 0x0 (no cols) | empty Series `{}` | empty Series `{}` | empty Series `{}` | empty Series `{}` | empty Series `{}` | empty Series `{}` |

**Current unlockedpd behavior for 0x0:** TypeError - **MUST FIX to return empty Series**

### Single Element Behavior

| Input | sum | mean | std (ddof=1) | std (ddof=0) | min | max |
|-------|-----|------|--------------|--------------|-----|-----|
| `[42.0]` | 42.0 | 42.0 | nan | 0.0 | 42.0 | 42.0 |

### All-NaN Behavior

| Operation | Result | Notes |
|-----------|--------|-------|
| sum | 0.0 | Sum of nothing is 0 |
| mean | nan | No valid values |
| min/max | nan | No valid values |
| prod | 1.0 | Product of nothing is 1 |

### NaN with skipna=False

| Operation | Result |
|-----------|--------|
| sum | nan |
| mean | nan |
| Any operation | nan if any NaN present |

### Cumulative with inf

| Input | cumsum | cumprod | cummin | cummax |
|-------|--------|---------|--------|--------|
| `[1, inf, 2]` | `[1, inf, inf]` | `[1, inf, inf]` | `[1, 1, 1]` | `[1, inf, inf]` |
| `[1, inf, -inf]` | `[1, inf, nan]` | `[1, inf, -inf]` | `[1, 1, -inf]` | `[1, inf, inf]` |

### pct_change Edge Cases

| Input | Result | Notes |
|-------|--------|-------|
| `[0, 1, 0]` | `[nan, inf, -1.0]` | 1/0 = inf |
| `[inf, 1, inf]` | `[nan, -1.0, inf]` | (1-inf)/inf = -1.0 |

---

## Work Objectives

### Core Objective
Achieve 100% pandas behavioral compatibility for all implemented operations, with comprehensive edge case handling.

### Deliverables
1. Performance baseline document with benchmark numbers for each operation category
2. Comprehensive edge case test suite covering all pandas edge behaviors
3. Fixed implementations for any discovered discrepancies
4. Documentation of pandas compatibility guarantees

### Definition of Done
- [ ] Performance baselines established for all operation categories
- [ ] All edge case tests pass with rtol=1e-10
- [ ] Behavior matches pandas for: NaN, inf, -inf, empty (including 0x0), single-value, zero-variance
- [ ] No regressions in existing 52 tests
- [ ] No performance regression beyond 5% for normal cases
- [ ] Test coverage for each supported operation category

---

## Must Have

1. **Performance Baselines (Task 0):**
   - Benchmark all operation categories with normal data
   - Document baseline numbers before any changes
   - Use pytest-benchmark for repeatable measurements

2. **Edge Case Test Coverage:**
   - inf/-inf in input data for all aggregations (per reference table above)
   - Empty DataFrames: 0 rows with columns, 0x0 (no columns)
   - Single-element DataFrames (1x1, 1xN, Nx1)
   - All-NaN DataFrames (not just columns)
   - Mixed inf/NaN combinations
   - Very large values (near float64 max)
   - Very small values (subnormal numbers)
   - Integer overflow scenarios in cumulative operations

3. **Behavioral Fixes:**
   - 0x0 DataFrame must return empty Series (not TypeError)
   - All operations must match pandas behavior exactly per reference table

4. **Test Organization:**
   - Tests grouped by operation category
   - Tests parameterized for edge cases
   - Clear documentation of what each test verifies

---

## Must NOT Have

1. **Do NOT implement new operations** - This is Phase 1 (edge cases only). Phase 2 will cover new operations.
2. **Do NOT change public API** - All existing function signatures must remain unchanged
3. **Do NOT reduce performance beyond 5%** - Edge case handling must not significantly slow down normal path
4. **Do NOT use try/except for control flow** - Handle edge cases explicitly
5. **Do NOT add dependencies** - Use only existing numba, numpy, pandas
6. **Do NOT test fillna/dropna** - These are not implemented (remove from test_extreme_edge_cases.py)

---

## Task Flow and Dependencies

```
[Task 0: Establish Performance Baselines]
           |
           v
[Task 1: Create Comprehensive Edge Case Test Suite]
           |
           v
[Task 2: Run Tests Against Current Implementation]
           |
           v
[Task 3: Identify and Document Discrepancies]
           |
           +----------------+----------------+
           |                |                |
           v                v                v
[Task 4a: Fix       [Task 4b: Fix      [Task 4c: Fix
Aggregation]        Rolling/Expand]    Transform/Other]
           |                |                |
           +----------------+----------------+
           |
           v
[Task 5: Run Full Test Suite + Performance Verification]
           |
           v
[Task 6: Documentation and Verification]
```

---

## Detailed TODOs

### Task 0: Establish Performance Baselines
**Files:** `tests/benchmarks/bench_baseline.py` (new)

**Acceptance Criteria:**
- [ ] Benchmark file created with pytest-benchmark tests
- [ ] Baseline numbers captured for each operation category:
  - Aggregations (sum, mean, std, var, min, max, median, prod)
  - Rolling operations (window=20 on 10000 rows)
  - Expanding operations (on 10000 rows)
  - EWM operations (span=20 on 10000 rows)
  - Transform operations (diff, pct_change, shift)
  - Cumulative operations (cumsum, cumprod, cummin, cummax)
- [ ] Baselines documented in `.omc/notepads/pandas-compatibility/baselines.md`
- [ ] Threshold defined: No operation may regress more than 5%

**Benchmark Methodology:**
```python
import pytest
import pandas as pd
import numpy as np
from unlockedpd.ops.aggregations import optimized_sum, optimized_mean, ...

@pytest.fixture
def standard_df():
    np.random.seed(42)
    return pd.DataFrame(np.random.randn(10000, 10))

def test_bench_sum(benchmark, standard_df):
    benchmark(optimized_sum, standard_df, axis=0)

def test_bench_mean(benchmark, standard_df):
    benchmark(optimized_mean, standard_df, axis=0)
# ... etc for each operation
```

**Commands:**
```bash
pytest tests/benchmarks/bench_baseline.py --benchmark-save=baseline --benchmark-json=baseline.json
```

---

### Task 1: Create Comprehensive Edge Case Test Suite
**Files:**
- `tests/test_edge_cases_comprehensive.py` (new)
- `tests/test_extreme_edge_cases.py` (fix: remove fillna imports on lines 110-130)

**Acceptance Criteria:**
- [ ] Remove or skip fillna tests in test_extreme_edge_cases.py (lines 110-130)
- [ ] Test file created with parameterized tests for each operation category
- [ ] Tests cover ALL edge cases from the reference table above
- [ ] Tests compare unlockedpd vs pandas with rtol=1e-10

**Edge Cases to Test (mapped to reference table):**

1. **inf/-inf Handling (6 test scenarios):**
   - Single inf value in column: `[inf, 1, 2]`
   - Single -inf value in column: `[-inf, 1, 2]`
   - Mixed inf and -inf: `[inf, -inf, 1]`
   - All inf column: `[inf, inf, inf]`
   - inf in rolling/expanding windows
   - inf in EWM calculations

2. **Empty/Minimal Data (5 test scenarios):**
   - Empty DataFrame with columns (0 rows, N cols) - expect 0.0 for sum
   - 0x0 DataFrame (no rows, no cols) - expect empty Series
   - Single element (1x1)
   - Single row (1xN)
   - Single column (Nx1)

3. **NaN Patterns (5 test scenarios):**
   - All NaN DataFrame - sum=0.0, mean=nan, prod=1.0
   - Alternating NaN pattern
   - Leading/trailing NaN
   - Single NaN in large array
   - NaN with skipna=True vs skipna=False

4. **Numerical Precision (4 test scenarios):**
   - Values near float64 max/min
   - Subnormal (denormalized) numbers
   - Very small differences (catastrophic cancellation)
   - Large sums with small additions

5. **Division Edge Cases (4 test scenarios):**
   - Division by zero in pct_change: `[0, 1, 0]` -> `[nan, inf, -1.0]`
   - 0/0 scenarios
   - inf/inf scenarios
   - Very small denominators

6. **Window Edge Cases (4 test scenarios):**
   - Window larger than data
   - min_periods edge cases
   - Window of size 1
   - Window equal to data length

**Implementation Template:**
```python
import pytest
import pandas as pd
import numpy as np
from unlockedpd.ops.aggregations import (
    optimized_sum, optimized_mean, optimized_std,
    optimized_var, optimized_min, optimized_max,
    optimized_median, optimized_prod
)

AGG_FUNCS = {
    'sum': optimized_sum,
    'mean': optimized_mean,
    'std': optimized_std,
    'var': optimized_var,
    'min': optimized_min,
    'max': optimized_max,
    'median': optimized_median,
    'prod': optimized_prod,
}

INF_TEST_CASES = [
    pytest.param([np.inf, 1.0, 2.0], id='single_inf'),
    pytest.param([-np.inf, 1.0, 2.0], id='single_neg_inf'),
    pytest.param([np.inf, -np.inf, 1.0], id='mixed_inf'),
    pytest.param([np.inf, np.inf, np.inf], id='all_inf'),
]

@pytest.mark.parametrize('agg_name', AGG_FUNCS.keys())
@pytest.mark.parametrize('values', INF_TEST_CASES)
def test_inf_handling(agg_name, values):
    """Test inf handling matches pandas exactly."""
    df = pd.DataFrame({'a': values})
    func = AGG_FUNCS[agg_name]

    result = func(df, axis=0)
    expected = getattr(df, agg_name)(axis=0)

    pd.testing.assert_series_equal(result, expected, rtol=1e-10)
```

---

### Task 2: Run Tests Against Current Implementation
**Files:** N/A (execution task)

**Acceptance Criteria:**
- [ ] All new tests executed
- [ ] Results documented showing pass/fail status
- [ ] Discrepancies categorized by severity:
  - CRITICAL: Wrong result (different value)
  - HIGH: Wrong type (exception vs result)
  - MEDIUM: Different NaN behavior
  - LOW: Numerical precision difference within tolerance

**Implementation Steps:**
1. Run `pytest tests/test_edge_cases_comprehensive.py -v --tb=short`
2. Capture all failures
3. Document each failure with:
   - Operation name
   - Input data
   - Expected result (pandas)
   - Actual result (unlockedpd)
   - Severity classification

---

### Task 3: Identify and Document Discrepancies
**Files:** `.omc/notepads/pandas-compatibility/issues.md` (new)

**Acceptance Criteria:**
- [ ] All discrepancies documented with:
  - File and line number of issue
  - Exact input that triggers discrepancy
  - Expected vs actual behavior (from reference table)
  - Root cause analysis
  - Proposed fix approach
  - Severity classification

**Known Issue to Document:**
- 0x0 DataFrame returns TypeError instead of empty Series

---

### Task 4a: Fix Aggregation Operations Edge Cases
**Files:** `src/unlockedpd/ops/aggregations.py`

**Acceptance Criteria:**
- [ ] All aggregation edge case tests pass
- [ ] No performance regression beyond 5% (verified against Task 0 baselines)
- [ ] inf handling matches pandas per reference table:
  - `sum([inf, -inf, 1])` = nan
  - `std([inf, 1, 2])` = nan
  - etc.
- [ ] 0x0 DataFrame returns empty Series (not TypeError)

**Specific Fixes Required:**
- Handle 0x0 DataFrame: check if df.shape[1] == 0, return `pd.Series([], dtype=float)`
- Verify inf behavior matches reference table (may already be correct via numpy)

---

### Task 4b: Fix Rolling/Expanding/EWM Edge Cases
**Files:**
- `src/unlockedpd/ops/rolling.py`
- `src/unlockedpd/ops/expanding.py`
- `src/unlockedpd/ops/ewm.py`

**Acceptance Criteria:**
- [ ] All rolling/expanding/EWM edge case tests pass
- [ ] No performance regression beyond 5%
- [ ] Window edge cases (larger than data) handled correctly
- [ ] inf values in windows handled correctly per reference table

**Specific Fixes (if needed):**
- Rolling with window > len(data) behavior
- min_periods with edge values
- inf in Welford's algorithm for std/var (should produce nan)
- EWM with all-inf column

---

### Task 4c: Fix Transform and Other Operations Edge Cases
**Files:**
- `src/unlockedpd/ops/transform.py`
- `src/unlockedpd/ops/cumulative.py`
- `src/unlockedpd/ops/stats.py`

**Acceptance Criteria:**
- [ ] All transform edge case tests pass
- [ ] No performance regression beyond 5%
- [ ] pct_change matches reference: `[0, 1, 0]` -> `[nan, inf, -1.0]`
- [ ] cumulative operations match reference table

**Specific Fixes (if needed):**
- `pct_change` division by zero = inf (not nan)
- `cumsum([1, inf, -inf])` = `[1, inf, nan]`
- `skew`/`kurt` with inf values = nan

---

### Task 5: Run Full Test Suite + Performance Verification
**Files:** N/A (execution task)

**Acceptance Criteria:**
- [ ] All 52 original tests still pass
- [ ] All new edge case tests pass
- [ ] No warnings or deprecation issues
- [ ] Performance verification: no operation regressed more than 5%

**Commands:**
```bash
# Functional tests
pytest tests/test_pandas_compatibility.py -v
pytest tests/test_edge_cases_comprehensive.py -v
pytest tests/test_extreme_edge_cases.py -v  # after fillna fix
pytest tests/ -v --tb=short

# Performance verification
pytest tests/benchmarks/bench_baseline.py --benchmark-compare=baseline
```

**Performance Verification Criteria:**
- Compare each operation against Task 0 baseline
- Flag any operation with >5% regression
- Regression requires either fix or documented justification

---

### Task 6: Documentation and Verification
**Files:**
- `tests/test_edge_cases_comprehensive.py` (docstrings)
- `.omc/notepads/pandas-compatibility/learnings.md` (new)

**Acceptance Criteria:**
- [ ] Each test file has module-level docstring explaining coverage
- [ ] Each test function has docstring explaining what it tests
- [ ] Any known limitations documented (what's NOT compatible)
- [ ] Performance results documented

---

## Commit Strategy

1. **Commit 0:** Add performance benchmarks
   - Message: "test: add performance benchmarks for baseline measurement"

2. **Commit 1:** Add comprehensive edge case test suite
   - Message: "test: add comprehensive edge case tests for pandas compatibility"
   - Includes: fix for fillna import issue in test_extreme_edge_cases.py

3. **Commit 2:** Fix aggregation edge cases (if needed)
   - Message: "fix: handle inf/-inf and empty DataFrame edge cases in aggregations"
   - Must include: 0x0 DataFrame returns empty Series

4. **Commit 3:** Fix rolling/expanding/EWM edge cases (if needed)
   - Message: "fix: handle edge cases in rolling/expanding/EWM operations"

5. **Commit 4:** Fix transform/cumulative/stats edge cases (if needed)
   - Message: "fix: handle edge cases in transform and stat operations"

6. **Commit 5:** Final verification and documentation
   - Message: "docs: document pandas compatibility edge case coverage"

---

## Success Criteria

### Quantitative
- [ ] 100% of existing tests pass (52 tests)
- [ ] 100% of new edge case tests pass (28+ test scenarios)
- [ ] Zero behavioral discrepancies vs pandas for supported operations
- [ ] Performance within 5% of baseline for all operations

### Qualitative
- [ ] Clear documentation of what edge cases are covered
- [ ] Clear documentation of any known limitations
- [ ] Test suite is maintainable and well-organized
- [ ] Reference table makes expected behavior unambiguous

---

## Risk Identification and Mitigations

### Risk 1: Performance Regression from Edge Case Checks
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Establish baselines FIRST (Task 0)
- Add edge case checks only where needed
- Use branch prediction hints where possible
- Benchmark before/after on normal cases
- **Threshold:** No more than 5% regression allowed

### Risk 2: Numba Incompatibility with Edge Case Handling
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Test all Numba-compiled functions with edge cases
- Use np.isnan, np.isinf which are Numba-compatible
- Fall back to pandas for truly incompatible cases

### Risk 3: Subtle Numerical Differences
**Probability:** Medium
**Impact:** Low
**Mitigation:**
- Use rtol/atol in comparisons appropriately
- Reference table documents EXACT expected values
- Cross-reference with pandas source for exact formulas

### Risk 4: Test Flakiness Due to Floating Point
**Probability:** Low
**Impact:** Low
**Mitigation:**
- Use deterministic test data (fixed seeds)
- Use appropriate tolerance values
- Document any platform-specific differences

---

## Out of Scope (Phase 2)

The following are explicitly NOT covered by this plan and will require a separate Phase 2 plan:

**Missing Operations to Implement:**
- Aggregations: count, first, last, idxmin, idxmax, all, any, nunique, quantile
- DataFrame ops: abs, clip, round, fillna, dropna, isna, notna, corr, cov
- Rolling/Expanding: apply, sem, rank
- EWM: cov, corr

**Not in Scope:**
- Datetime/NaT handling (pandas supports min/max on datetime, not sum/mean)
- Non-numeric dtype support beyond what exists

---

## Notes

1. **Priority Order:** Start with Task 0 (baselines), then aggregations as they are the foundation
2. **Testing Strategy:** Use pandas as the reference for all comparisons
3. **Performance:** Task 0 baselines are MANDATORY before any implementation changes
4. **Backward Compatibility:** No changes to public API signatures
5. **Test Fix:** Remove fillna imports from test_extreme_edge_cases.py lines 110-130 before running tests
