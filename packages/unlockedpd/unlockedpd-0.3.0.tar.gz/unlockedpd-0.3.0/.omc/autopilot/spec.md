# Autopilot Specification: Pandas Numerical Operations Expansion

## User Request
Create a new worktree to cover all pandas numerical operations with nogil + ThreadPoolExecutor specialized in 2D array

---

## Requirements Analysis

### Functional Requirements

**New Operations to Implement:**

| Category | Operations | Priority |
|----------|-----------|----------|
| **Aggregations** | sum, mean, std, var, min, max, prod, median | HIGH |
| **Fill Operations** | ffill, bfill, fillna, interpolate (linear) | HIGH |
| **Element-wise Math** | abs, clip, round, pow, mod, floordiv | MEDIUM |
| **Correlation** | corr(), cov() (DataFrame-level) | MEDIUM |
| **Comparison** | eq, ne, lt, le, gt, ge, isna, notna | LOW |

### Non-Functional Requirements

- **Performance**: Minimum 2x speedup for inclusion, target 5-15x where possible
- **Compatibility**: 100% pandas API compatibility with automatic fallback
- **Memory**: No operation should use more than 2x input DataFrame memory
- **Precision**: `rtol=1e-10` for all numerical comparisons

### Implicit Requirements

- Warmup integration for all Numba functions
- Comprehensive test coverage matching pandas edge cases
- Benchmark documentation for each operation
- 3-tier dispatch: serial (<500K), parallel (500K-10M), threadpool+nogil (>10M)

### Out of Scope

- GroupBy operations (separate subsystem, high complexity)
- Resampling operations (datetime handling)
- Linear algebra (dot, matmul - BLAS is optimized)
- String/datetime operations
- describe(), value_counts(), nunique(), mode()

---

## Technical Specification

### Architecture Pattern (3-Tier Dispatch)

```python
# Tier 1: Serial (< 500K elements)
@njit(cache=True)
def _operation_serial(arr, ...): ...

# Tier 2: Parallel prange (500K - 10M elements)
@njit(parallel=True, cache=True)
def _operation_parallel(arr, ...): ...

# Tier 3: ThreadPool + nogil (>= 10M elements)
@njit(nogil=True, cache=True)
def _operation_nogil_chunk(arr, result, start_col, end_col, ...): ...

def _operation_threadpool(arr, ...):
    with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as executor:
        ...
```

### New File Structure

```
src/unlockedpd/ops/
├── aggregations.py      # sum, mean, std, var, min, max, median, prod
├── element_wise.py      # clip, abs, round, arithmetic
├── fillna.py            # ffill, bfill, fillna, interpolate
├── comparison.py        # eq, ne, lt, le, gt, ge, isna, notna
├── correlation.py       # DataFrame-level corr(), cov()
└── _reduction_utils.py  # Shared utilities for reductions

tests/
├── test_aggregations.py
├── test_element_wise.py
├── test_fillna.py
├── test_comparison.py
└── test_correlation.py

benchmarks/
├── bench_aggregations.py
├── bench_element_wise.py
├── bench_fillna.py
└── bench_correlation.py
```

### Integration Points

1. **_patch.py**: New `apply_*_patches()` functions
2. **_warmup.py**: New `warmup_*()` functions
3. **__init__.py**: Register new patches in `_apply_all_patches()`

---

## Implementation Priority

### Phase 1 (High Priority)
1. `aggregations.py` - sum, mean, std, var, min, max
2. `fillna.py` - ffill, bfill, fillna

### Phase 2 (Medium Priority)
3. `aggregations.py` - median, prod
4. `element_wise.py` - clip, abs, round
5. `correlation.py` - corr(), cov()

### Phase 3 (Lower Priority)
6. `fillna.py` - interpolate (linear)
7. `comparison.py` - eq, ne, lt, le, gt, ge, isna, notna

---

## Acceptance Criteria

- [ ] All operations achieve >= 2x speedup on 10K x 10K DataFrame
- [ ] 100% pandas compatibility tests pass at rtol=1e-10
- [ ] Warmup integration eliminates first-call overhead
- [ ] Fallback to pandas works correctly for unsupported cases
- [ ] Edge cases handled: empty DataFrame, all-NaN, single row/col
- [ ] Benchmark results documented in README format
