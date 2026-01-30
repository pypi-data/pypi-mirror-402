# Pandas Compatibility Enhancement - Complete Plan

## Context

### Original Request
Comprehensive pandas compatibility enhancement covering:
1. Phase 1: Edge case compatibility for existing operations (already planned)
2. Phase 2: Implement missing operations
3. Phase 3: Additional improvements identified during analysis

### Codebase Analysis Summary

**Currently Implemented Operations:**
- **Aggregations:** sum, mean, std, var, min, max, median, prod (8 operations)
- **Rolling:** sum, mean, std, var, min, max, skew, kurt, count, median, quantile (11 operations)
- **Expanding:** sum, mean, std, var, min, max, count, skew, kurt (9 operations)
- **EWM:** mean, std, var (3 operations)
- **Transform:** diff, pct_change, shift (3 operations)
- **Stats:** skew, kurt, sem (3 operations)
- **Cumulative:** cumsum, cumprod, cummin, cummax (4 operations)
- **Rank:** rank (both axis=0 and axis=1)
- **Pairwise Rolling:** corr, cov (2 operations)
- **DataFrame Transform:** abs, sqrt, exp, log, log10, log2, sin, cos, tan, ceil, floor (11 ufuncs)

**Implementation Patterns Identified:**
1. Numba `@njit` with `parallel=True` and `prange` for column-parallel operations
2. ThreadPool + `nogil=True` kernels for very large arrays (>10M elements)
3. 3-tier dispatch: serial (small), parallel (medium), threadpool (large)
4. `_compat.py` provides utilities: `get_numeric_columns_fast`, `wrap_result`, `ensure_float64`
5. Welford's algorithm for numerically stable variance calculations

**Test Infrastructure:**
- 52+ existing pandas compatibility tests
- Tests use `rtol=1e-10` for strict numerical equivalence
- Pattern: enable/disable unlockedpd, compare results via `pd.testing.assert_*`

---

## Phase 1: Edge Case Compatibility (Reference)

**Status:** Already planned in `.omc/plans/pandas-compatibility.md`

**Summary:** Comprehensive edge case testing and fixes for existing operations:
- inf/-inf handling
- Empty/minimal DataFrames (including 0x0)
- NaN patterns
- Numerical precision edge cases
- Performance baselines

**Estimated Tasks:** 6 tasks (Task 0-6)

---

## Phase 2: Implement Missing Operations

### 2.1 Missing Aggregations

| Operation | Pandas Method | Priority | Numba Benefit? | Notes |
|-----------|---------------|----------|----------------|-------|
| `count` | `df.count()` | HIGH | YES | Count non-NaN values, simple parallelizable |
| `idxmin` | `df.idxmin()` | HIGH | YES | Index of minimum value |
| `idxmax` | `df.idxmax()` | HIGH | YES | Index of maximum value |
| `all` | `df.all()` | MEDIUM | YES | Boolean AND reduction |
| `any` | `df.any()` | MEDIUM | YES | Boolean OR reduction |
| `nunique` | `df.nunique()` | MEDIUM | YES | Count unique values (sort-based O(n log n)) |
| `quantile` | `df.quantile()` | HIGH | YES | Already in rolling, extend to DataFrame |
| `value_counts` | `df.value_counts()` | MEDIUM | YES | Frequency counts (sort-based, pairs with nunique) |

**Out of Scope for Phase 2:**
| Operation | Rationale |
|-----------|-----------|
| `first` / `last` | Limited Numba benefit (simple linear scan), low priority - defer to future phase |
| `describe()` | Composition of existing ops (mean, std, min, max, quantile) - thin Python wrapper, no new Numba code needed |
| `nlargest` / `nsmallest` | Requires partial sort or heap - separate optimization problem |

### 2.2 Missing DataFrame Operations

| Operation | Pandas Method | Priority | Numba Benefit? | Notes |
|-----------|---------------|----------|----------------|-------|
| `clip` | `df.clip()` | HIGH | YES | Clip values to bounds, parallelizable |
| `round` | `df.round()` | HIGH | LIMITED | Round to decimal places |
| `fillna` | `df.fillna()` | CRITICAL | YES | Fill NaN values, highly requested |
| `dropna` | `df.dropna()` | HIGH | LIMITED | Drop NaN rows/columns |
| `isna`/`isnull` | `df.isna()` | MEDIUM | YES | Detect NaN values |
| `notna`/`notnull` | `df.notna()` | MEDIUM | YES | Detect non-NaN values |
| `corr` | `df.corr()` | HIGH | YES | Correlation matrix (not rolling) |
| `cov` | `df.cov()` | HIGH | YES | Covariance matrix (not rolling) |

### 2.3 Missing Rolling/Expanding Operations

| Operation | Pandas Method | Priority | Numba Benefit? | Notes |
|-----------|---------------|----------|----------------|-------|
| `apply` | `.rolling().apply()` | LOW | NO | Custom functions, hard to optimize |
| `sem` | `.rolling().sem()` | MEDIUM | YES | Standard error of mean |

**Out of Scope for Phase 2:**
| Operation | Rationale |
|-----------|-----------|
| `rolling().rank()` | Complex windowed ranking algorithm - defer to future phase |

### 2.4 Missing EWM Operations

| Operation | Pandas Method | Priority | Numba Benefit? | Notes |
|-----------|---------------|----------|----------------|-------|
| `corr` | `.ewm().corr()` | LOW | YES | EWM pairwise correlation |
| `cov` | `.ewm().cov()` | LOW | YES | EWM pairwise covariance |

---

## Phase 2 Detailed Tasks

### Task P2-1: Implement fillna Operations (CRITICAL)

**Files to Create/Modify:**
- `src/unlockedpd/ops/fillna.py` (NEW)
- `src/unlockedpd/__init__.py` (add patch import)
- `tests/test_fillna.py` (NEW)

**Operations to Implement:**
1. `df.fillna(value)` - Fill with scalar value
2. `df.fillna(dict)` - Fill with per-column values
3. `df.ffill()` / `df.fillna(method='ffill')` - Forward fill
4. `df.bfill()` / `df.fillna(method='bfill')` - Backward fill
5. `limit` parameter support - Limit consecutive NaN fills

**Implementation Approach:**
```python
@njit(parallel=True, cache=True)
def _fillna_value_parallel(arr, fill_value):
    """Fill NaN with scalar value - parallelized across columns."""
    n_rows, n_cols = arr.shape
    result = arr.copy()
    for col in prange(n_cols):
        for row in range(n_rows):
            if np.isnan(result[row, col]):
                result[row, col] = fill_value
    return result

@njit(parallel=True, cache=True)
def _ffill_parallel(arr):
    """Forward fill NaN - parallelized across columns."""
    n_rows, n_cols = arr.shape
    result = arr.copy()
    for col in prange(n_cols):
        last_valid = np.nan
        for row in range(n_rows):
            if np.isnan(result[row, col]):
                result[row, col] = last_valid
            else:
                last_valid = result[row, col]
    return result
```

**Acceptance Criteria:**
- [ ] `fillna(value)` matches pandas for scalar values
- [ ] `fillna(dict)` matches pandas for per-column values
- [ ] `ffill()` matches pandas exactly
- [ ] `bfill()` matches pandas exactly
- [ ] `limit` parameter works correctly (limits consecutive fills)
- [ ] Handles all-NaN columns correctly
- [ ] Handles 0x0 empty DataFrame correctly (returns empty DataFrame)
- [ ] Performance equal or better than pandas for >500K elements
- [ ] Tests cover edge cases: all-NaN, no-NaN, mixed dtypes, 0x0 DataFrame

**Pandas Behavior Reference:**
```python
df = pd.DataFrame({'a': [1, np.nan, 3], 'b': [np.nan, 2, np.nan]})
df.fillna(0)     # All NaN -> 0
df.ffill()       # Forward fill: [1, 1, 3], [NaN, 2, 2]
df.bfill()       # Backward fill: [1, 3, 3], [2, 2, NaN]
```

---

### Task P2-2: Implement DataFrame corr/cov Operations

**Files to Create/Modify:**
- `src/unlockedpd/ops/dataframe_pairwise.py` (NEW)
- `src/unlockedpd/__init__.py` (add patch import)
- `tests/test_dataframe_corr_cov.py` (NEW)

**Operations to Implement:**
1. `df.corr(method='pearson')` - Correlation matrix
2. `df.cov()` - Covariance matrix

**Implementation Approach:**
- Reuse pairwise covariance kernel from `pairwise.py`
- Compute for all column pairs (n_cols * (n_cols + 1) / 2)
- Use ThreadPool for large DataFrames

**Acceptance Criteria:**
- [ ] `df.corr()` matches pandas exactly (rtol=1e-10)
- [ ] `df.cov()` matches pandas exactly (rtol=1e-10)
- [ ] Diagonal of corr is 1.0 (not NaN)
- [ ] Handles NaN correctly (pairwise deletion)
- [ ] Handles constant columns (corr = NaN, cov = 0)
- [ ] Handles 0x0 empty DataFrame correctly
- [ ] Performance benefit for >100 columns

---

### Task P2-3: Implement count/nunique/value_counts Aggregations

**Files to Modify:**
- `src/unlockedpd/ops/aggregations.py` (add count, nunique, value_counts)
- `src/unlockedpd/ops/agg.py` (add to SUPPORTED_FUNCTIONS)
- `tests/test_aggregations.py` (add tests)

**Operations to Implement:**
1. `df.count()` - Count non-NaN values per column
2. `df.nunique()` - Count unique values per column (sort-based O(n log n))
3. `df[col].value_counts()` - Frequency counts per unique value (sort-based)

**Implementation Approach:**
```python
@njit(parallel=True, cache=True)
def _count_parallel(arr, skipna):
    """Count non-NaN values - parallelized across columns."""
    n_rows, n_cols = arr.shape
    result = np.empty(n_cols, dtype=np.float64)
    for col in prange(n_cols):
        count = 0
        for row in range(n_rows):
            if not np.isnan(arr[row, col]):
                count += 1
        result[col] = count
    return result

@njit(cache=True)
def _nunique_column(arr):
    """Count unique non-NaN values using sort-based O(n log n) algorithm.

    Note: Sets are not supported in Numba nopython mode, so we use sorting.
    This is efficient for most analytics workloads with moderate cardinality.
    """
    # Filter NaN values
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return 0

    # Sort and count adjacent differences
    sorted_arr = np.sort(valid)
    count = 1
    for i in range(1, len(sorted_arr)):
        if sorted_arr[i] != sorted_arr[i-1]:
            count += 1
    return count

@njit(parallel=True, cache=True)
def _nunique_parallel(arr):
    """Count unique values per column - parallelized."""
    n_rows, n_cols = arr.shape
    result = np.empty(n_cols, dtype=np.float64)
    for col in prange(n_cols):
        col_data = arr[:, col].copy()
        result[col] = _nunique_column(col_data)
    return result
```

**Acceptance Criteria:**
- [ ] `df.count()` matches pandas exactly
- [ ] `df.nunique()` matches pandas exactly
- [ ] `df[col].value_counts()` matches pandas exactly
- [ ] All work with axis=0; count/nunique also support axis=1
- [ ] Handle all-NaN columns (count=0, nunique=0)
- [ ] Handle 0x0 empty DataFrame correctly
- [ ] nunique handles NaN correctly (NaN is not counted as unique by default)

---

### Task P2-4: Implement idxmin/idxmax Aggregations

**Files to Modify:**
- `src/unlockedpd/ops/aggregations.py` (add idxmin, idxmax)
- `tests/test_aggregations.py` (add tests)

**Operations to Implement:**
1. `df.idxmin()` - Index of minimum value per column
2. `df.idxmax()` - Index of maximum value per column

**Implementation Approach:**
- Return index labels, not integer positions
- Handle NaN (skipna=True by default)
- Handle ties (return first occurrence, matching pandas)

**Acceptance Criteria:**
- [ ] `df.idxmin()` matches pandas exactly
- [ ] `df.idxmax()` matches pandas exactly
- [ ] Returns index labels (not integers)
- [ ] Supports axis=0 (default) and axis=1
- [ ] Handles all-NaN columns (returns NaN)
- [ ] Handles 0x0 empty DataFrame correctly
- [ ] Handles ties correctly (first occurrence)

---

### Task P2-5: Implement clip/round Operations

**Note:** `abs` is already implemented in `dataframe_transform.py` (line 30).

**Files to Modify:**
- `src/unlockedpd/ops/dataframe_transform.py` (add clip, round)
- `tests/test_transform.py` (add tests)

**Operations to Implement:**
1. `df.clip(lower, upper)` - Clip values to bounds
2. `df.round(decimals)` - Round to decimal places

**Implementation Approach:**
```python
@njit(parallel=True, cache=True)
def _clip_parallel(arr, lower, upper):
    """Clip values - parallelized."""
    n_rows, n_cols = arr.shape
    result = np.empty_like(arr)
    for col in prange(n_cols):
        for row in range(n_rows):
            val = arr[row, col]
            if np.isnan(val):
                result[row, col] = val
            else:
                result[row, col] = min(max(val, lower), upper)
    return result
```

**Acceptance Criteria:**
- [ ] `df.clip(lower, upper)` matches pandas exactly
- [ ] `df.clip(lower=None)` works (clip only upper)
- [ ] `df.clip(upper=None)` works (clip only lower)
- [ ] `df.round(decimals)` matches pandas exactly
- [ ] Preserves NaN values
- [ ] Handles 0x0 empty DataFrame correctly

---

### Task P2-6: Implement isna/notna Operations

**Files to Modify:**
- `src/unlockedpd/ops/dataframe_transform.py` (add isna, notna)
- `tests/test_transform.py` (add tests)

**Operations to Implement:**
1. `df.isna()` / `df.isnull()` - Boolean mask of NaN values
2. `df.notna()` / `df.notnull()` - Boolean mask of non-NaN values

**Implementation Approach:**
- Return DataFrame with boolean dtype
- Use numpy's `np.isnan` for detection
- Parallel for large DataFrames

**Acceptance Criteria:**
- [ ] `df.isna()` matches pandas exactly
- [ ] `df.notna()` matches pandas exactly
- [ ] `isnull` is alias for `isna`
- [ ] `notnull` is alias for `notna`
- [ ] Returns boolean DataFrame
- [ ] Handles 0x0 empty DataFrame correctly

---

### Task P2-7: Implement dropna Operation

**Files to Create/Modify:**
- `src/unlockedpd/ops/fillna.py` (add dropna)
- `tests/test_fillna.py` (add tests)

**Operations to Implement:**
1. `df.dropna(axis=0, how='any')` - Drop rows with NaN
2. `df.dropna(axis=1, how='any')` - Drop columns with NaN
3. Support `how='all'` - Drop only if all values are NaN
4. Support `thresh` parameter

**Acceptance Criteria:**
- [ ] `df.dropna()` matches pandas exactly
- [ ] `dropna(axis=0)` drops rows
- [ ] `dropna(axis=1)` drops columns
- [ ] `how='any'` and `how='all'` work correctly
- [ ] `thresh` parameter works correctly
- [ ] Handles 0x0 empty DataFrame correctly (returns empty DataFrame)

---

### Task P2-8: Implement all/any Boolean Aggregations

**Files to Modify:**
- `src/unlockedpd/ops/aggregations.py` (add all, any)
- `tests/test_aggregations.py` (add tests)

**Operations to Implement:**
1. `df.all()` - True if all values are truthy
2. `df.any()` - True if any value is truthy

**Implementation Approach:**
```python
@njit(parallel=True, cache=True)
def _all_parallel(arr, skipna):
    """Boolean AND - parallelized across columns."""
    n_rows, n_cols = arr.shape
    result = np.empty(n_cols, dtype=np.bool_)
    for col in prange(n_cols):
        all_true = True
        for row in range(n_rows):
            val = arr[row, col]
            if np.isnan(val):
                if not skipna:
                    all_true = False
                    break
            elif val == 0.0:
                all_true = False
                break
        result[col] = all_true
    return result
```

**Acceptance Criteria:**
- [ ] `df.all()` matches pandas exactly
- [ ] `df.any()` matches pandas exactly
- [ ] Handle NaN with skipna parameter
- [ ] Work with axis=0 (default) and axis=1
- [ ] Handles 0x0 empty DataFrame correctly

---

### Task P2-9: Implement Rolling sem

**Files to Modify:**
- `src/unlockedpd/ops/rolling.py` (add sem)
- `tests/test_rolling.py` (add tests)

**Operations to Implement:**
1. `.rolling().sem()` - Rolling standard error of mean

**Note:** Rolling rank is out of scope for Phase 2 (complex windowed ranking algorithm).

**Implementation Approach:**
- `sem = std / sqrt(count)`
- Reuse existing Welford-based variance calculation

**Acceptance Criteria:**
- [ ] `.rolling().sem()` matches pandas exactly
- [ ] Handle ddof parameter
- [ ] Handle min_periods correctly
- [ ] Handles empty input correctly

---

### Task P2-10: Implement DataFrame quantile

**Files to Modify:**
- `src/unlockedpd/ops/aggregations.py` (add quantile)
- `tests/test_aggregations.py` (add tests)

**Operations to Implement:**
1. `df.quantile(q)` - Compute quantile along axis

**Implementation Approach:**
- Similar to median implementation
- Support scalar q and list of q values
- Use sorting-based approach (same as rolling quantile)

**Acceptance Criteria:**
- [ ] `df.quantile(0.5)` matches median exactly
- [ ] `df.quantile([0.25, 0.5, 0.75])` returns DataFrame
- [ ] Handle NaN correctly
- [ ] Support interpolation parameter (linear default)
- [ ] Supports axis=0 (default) and axis=1
- [ ] Handles 0x0 empty DataFrame correctly

---

## Phase 3: Additional Improvements

### Task P3-1: Performance Optimizations

**Files to Modify:**
- Various ops files

**Improvements:**
1. **Adaptive thresholds** - Current thresholds (500K, 10M) may not be optimal for all hardware
2. **Memory layout optimization** - Ensure F-contiguous for column operations
3. **Cache-aware chunking** - Optimize chunk sizes for L2/L3 cache

**Acceptance Criteria:**
- [ ] Benchmark on different hardware configurations
- [ ] Document optimal thresholds
- [ ] No regressions from Phase 1 baselines

---

### Task P3-2: API Consistency Improvements

**Files to Modify:**
- All wrapper functions in ops/*.py

**Improvements:**
1. **Consistent error messages** - Standardize "Optimization only for DataFrame"
2. **Parameter validation** - Validate all parameters match pandas signatures
3. **Deprecation handling** - Handle pandas deprecation warnings gracefully

**Acceptance Criteria:**
- [ ] All error messages follow consistent format
- [ ] All public functions have complete docstrings
- [ ] No deprecation warnings from pandas

---

### Task P3-3: Expanding Operations Parity

**Files to Modify:**
- `src/unlockedpd/ops/expanding.py`

**Improvements:**
Add expanding versions of rolling operations that are missing:
1. `expanding().sem()` - Standard error of mean
2. `expanding().quantile()` - Quantile (if not already present)

**Acceptance Criteria:**
- [ ] All expanding operations match their rolling counterparts
- [ ] All match pandas exactly

---

### Task P3-4: Documentation and Examples

**Files to Create:**
- `docs/compatibility.md` (NEW)
- `docs/performance.md` (NEW)

**Content:**
1. Complete list of optimized operations
2. Performance comparison tables
3. Edge case behavior documentation
4. Migration guide from vanilla pandas

**Acceptance Criteria:**
- [ ] All optimized operations documented
- [ ] Performance numbers for common use cases
- [ ] Edge case behavior clearly documented

---

## Task Flow and Dependencies

```
PHASE 1 (Edge Cases - from existing plan)
    |
    +---> [P2-1: fillna] -----------------+
    |                                      |
    +---> [P2-2: corr/cov]                 |
    |                                      |
    +---> [P2-3: count/nunique/value_counts]
    |                                      |
    +---> [P2-4: idxmin/idxmax]            |
    |                                      |
    +---> [P2-5: clip/round]               +---> PHASE 3
    |                                      |
    +---> [P2-6: isna/notna] --------------+
    |                                      |
    +---> [P2-7: dropna] ------------------+ (depends on P2-6)
    |                                      |
    +---> [P2-8: all/any]                  |
    |                                      |
    +---> [P2-9: rolling sem]              |
    |                                      |
    +---> [P2-10: quantile] ---------------+
```

**Notes:**
- Phase 1 tasks are prerequisites for Phase 2
- Most Phase 2 tasks are independent and can be parallelized
- P2-7 (dropna) depends on P2-6 (isna/notna)
- Phase 3 tasks depend on Phase 2 completion
- All Phase 2 tasks must handle 0x0 empty DataFrames correctly

---

## Commit Strategy

### Phase 2 Commits

1. **P2-1:** `feat: add fillna/ffill/bfill operations with limit parameter`
2. **P2-2:** `feat: add DataFrame.corr() and .cov() with pairwise optimization`
3. **P2-3:** `feat: add count, nunique, and value_counts aggregations`
4. **P2-4:** `feat: add idxmin and idxmax aggregations with axis support`
5. **P2-5:** `feat: add clip and round DataFrame operations`
6. **P2-6:** `feat: add isna/isnull and notna/notnull operations`
7. **P2-7:** `feat: add dropna operation`
8. **P2-8:** `feat: add all/any boolean aggregations with axis support`
9. **P2-9:** `feat: add rolling sem operation`
10. **P2-10:** `feat: add DataFrame.quantile() with axis support`

### Phase 3 Commits

1. **P3-1:** `perf: optimize thresholds and memory layout`
2. **P3-2:** `refactor: standardize API and error handling`
3. **P3-3:** `feat: add expanding sem and quantile`
4. **P3-4:** `docs: add comprehensive compatibility documentation`

---

## Success Criteria

### Quantitative (Phase 2)
- [ ] 10 task groups implemented (P2-1 through P2-10)
- [ ] 100% of new operations match pandas behavior exactly
- [ ] No regressions in existing tests
- [ ] Performance benefit for operations on >500K elements
- [ ] 0x0 empty DataFrame handling correct for ALL new operations

### Qualitative (Phase 2)
- [ ] Consistent implementation patterns across all operations
- [ ] Comprehensive test coverage for all new operations (including 0x0 edge case)
- [ ] Clear documentation for each operation
- [ ] axis=0 and axis=1 support where applicable (count, nunique, all, any, idxmin, idxmax, quantile)

### Quantitative (Phase 3)
- [ ] Performance optimizations measured and documented
- [ ] 100% API consistency
- [ ] Complete documentation

---

## Risk Identification

### Risk 1: Numba Limitations for Complex Operations
**Probability:** Medium
**Impact:** High
**Mitigation:**
- Some operations (e.g., `nunique`) require data structures not supported in Numba
- Fall back to numpy/pandas where Numba is not beneficial
- Document which operations use pure Python fallback

### Risk 2: Performance Regression from Added Operations
**Probability:** Low
**Impact:** Medium
**Mitigation:**
- Each new operation is independent
- Existing operations unchanged
- Benchmark each new operation vs pandas

### Risk 3: API Incompatibility with Future Pandas Versions
**Probability:** Medium
**Impact:** Medium
**Mitigation:**
- Pin pandas version range in dependencies
- Monitor pandas release notes
- Use abstract parameter handling (**kwargs)

### Risk 4: Test Maintenance Burden
**Probability:** High
**Impact:** Low
**Mitigation:**
- Use parameterized tests extensively
- Leverage pandas as the reference implementation
- Automate comparison testing

---

## Priority Summary

### CRITICAL (Must Have)
1. fillna (P2-1) - Most requested missing operation
2. corr/cov (P2-2) - Common data analysis operations

### HIGH (Should Have)
3. count/nunique/value_counts (P2-3)
4. idxmin/idxmax (P2-4)
5. clip/round (P2-5)
6. dropna (P2-7)
7. quantile (P2-10)

### MEDIUM (Nice to Have)
8. isna/notna (P2-6)
9. all/any (P2-8)
10. rolling sem (P2-9)

### LOW (Future / Out of Scope for Phase 2)
- EWM corr/cov
- rolling apply
- rolling rank (complex windowed ranking)
- first/last (limited Numba benefit)
- describe() (composition of existing ops)
- nlargest/nsmallest (requires partial sort/heap)

---

## Notes

1. **Implementation Order:** Start with fillna (P2-1) as it's most requested and unblocks test_extreme_edge_cases.py
2. **Reuse Patterns:** Many operations can reuse existing kernels (e.g., sem reuses variance kernel)
3. **Test Strategy:** Always test against pandas with optimizations disabled
4. **Performance Testing:** Only claim optimization for operations that show >10% improvement
5. **Fallback Strategy:** Operations that don't benefit from Numba should raise TypeError to trigger fallback
