# Specification: Fix Behavioral Differences in MyNumbaDataFrame

## Problem Statement

The `unlockedpd` library (a Numba-accelerated pandas optimization layer) has behavioral differences from pandas that cause "Weights are all zero" errors in downstream applications (vibequant backtests).

## Root Cause Analysis

From the error logs:
- `RuntimeWarning: Degrees of freedom <= 0 for slice` - numpy nanstd/nanvar edge case
- `RuntimeWarning: Mean of empty slice` - operations on all-NaN data
- `RuntimeWarning: invalid value encountered in divide` - division by zero or NaN
- `Error: Weights are all zero` - cascading failure from above issues

## Functional Requirements

### FR1: Fix Rolling Skew/Kurt Zero Variance Handling
**Current behavior:** Returns `0.0` when variance is near zero (`m2 > 1e-14`)
**Expected behavior:** Return `NaN` to match pandas

Files affected:
- `src/unlockedpd/ops/rolling.py` lines 779-786, 888-897

### FR2: Fix Expanding Skew/Kurt Zero Variance Handling
**Current behavior:** Computes result when `variance > 0`, returns nothing otherwise
**Expected behavior:** Return `NaN` when variance is near zero to match pandas

Files affected:
- `src/unlockedpd/ops/expanding.py` lines 246-250, 294-298

### FR3: Fix Rolling Skew/Kurt Bias Correction Formula
**Current behavior:** Uses formula that may differ from pandas for small sample sizes
**Expected behavior:** Match pandas exact bias correction formula

Files affected:
- `src/unlockedpd/ops/rolling.py` lines 778-784, 889-895

### FR4: Fix Expanding Skew/Kurt Bias Correction Formula
**Current behavior:** Uses different bias correction than pandas
**Expected behavior:** Match pandas exact formula

Files affected:
- `src/unlockedpd/ops/expanding.py` lines 248-250, 296-298

### FR5: Add Comprehensive Edge Case Tests
Create tests comparing unlockedpd vs pandas for:
- All-NaN columns
- Single value columns
- Zero variance columns (all identical values)
- Near-zero variance (numerical edge case)
- Empty DataFrames
- Window larger than data

## Non-Functional Requirements

### NFR1: Pandas Compatibility
All operations must match pandas output within `rtol=1e-10` for identical inputs.

### NFR2: Performance Preservation
No more than 5% regression in benchmark times after fixes.

### NFR3: Warning-Free Execution
Operations should not raise RuntimeWarnings for valid inputs.

## Technical Specification

### Key Findings

1. **Rolling skew/kurt** (rolling.py:738-956):
   - Returns `0.0` for zero variance instead of `NaN`
   - Bias correction formula differs from pandas

2. **Expanding skew/kurt** (expanding.py:211-300):
   - Same zero variance issue
   - Different bias correction formula
   - Uses `variance > 0` check instead of checking for near-zero

3. **DataFrame stats skew/kurt** (stats.py:1-733):
   - Uses `variance < 1e-14` threshold correctly
   - Bias correction formula matches pandas

### Implementation Approach

1. **Fix zero variance handling**:
   - Change `result[row, col] = 0.0` to `result[row, col] = np.nan`
   - This matches pandas which returns NaN for zero-variance windows

2. **Fix bias correction**:
   - Rolling skew: `adjust = np.sqrt(count * (count - 1)) / (count - 2)`
   - Rolling kurt: Use same formula as in stats.py (already correct there)

3. **Add tests**:
   - Create comprehensive edge case tests
   - Test against pandas with identical inputs

### Files to Modify

| File | Lines | Change |
|------|-------|--------|
| `src/unlockedpd/ops/rolling.py` | 779-786, 833-840 | Fix skew zero variance |
| `src/unlockedpd/ops/rolling.py` | 888-897, 945-954 | Fix kurt zero variance |
| `src/unlockedpd/ops/expanding.py` | 246-250, 505-508 | Fix skew zero variance |
| `src/unlockedpd/ops/expanding.py` | 294-298, 545-548 | Fix kurt zero variance |
| `tests/test_edge_cases.py` | NEW | Edge case tests |

## Acceptance Criteria

1. `pd.testing.assert_frame_equal(result, expected, rtol=1e-10)` passes for all operations
2. Zero `RuntimeWarning` during normal operations
3. All edge cases (all-NaN, single value, zero variance) match pandas behavior
4. Vibequant backtests run without "Weights are all zero" errors

## Out of Scope

- Apply/transform/pipe/agg operations (marked as not yet implemented)
- New feature additions
- Performance optimizations beyond maintaining current levels
