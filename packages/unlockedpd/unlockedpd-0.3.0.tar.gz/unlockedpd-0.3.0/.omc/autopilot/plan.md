# Implementation Plan: Pandas Numerical Operations Expansion

## Overview
Create a new git worktree with comprehensive pandas numerical operations using the established 3-tier dispatch pattern (serial, parallel prange, threadpool+nogil).

---

## Task Breakdown

### Task 1: Create Git Worktree
```bash
cd /home/bellman/Workspace/MyNumbaDataFrame
git worktree add ../unlockedpd-numerical-ops -b feature/numerical-ops
```

### Task 2: Implement aggregations.py
**Operations:** sum, mean, std, var, min, max, median, prod
**Pattern:** Reduction operations with axis support (0=columns, 1=rows)

Key implementation:
- Axis-aware computation
- Welford's algorithm for std/var (numerical stability)
- Column-parallel for axis=0, row-parallel for axis=1
- 3-tier dispatch based on element count

### Task 3: Implement fillna.py
**Operations:** ffill, bfill, fillna
**Pattern:** Sequential scan with memory of last valid value

Key implementation:
- ffill: forward scan, remember last valid
- bfill: backward scan, remember last valid
- fillna: scalar/dict/method dispatch
- Column-parallel with nogil chunks

### Task 4: Implement element_wise.py
**Operations:** clip, abs, round
**Pattern:** Element-wise transformation

Key implementation:
- Row-parallel for cache efficiency (C-contiguous)
- Broadcasting support for clip bounds
- In-place option for memory efficiency

### Task 5: Implement correlation.py
**Operations:** DataFrame.corr(), DataFrame.cov()
**Pattern:** Pairwise computation across all column pairs

Key implementation:
- O(n*m^2) where m=columns, n=rows
- Parallelize across column pairs
- Use Welford for stability
- Handle min_periods parameter

### Task 6: Add Tests
- test_aggregations.py: Compare with pandas for all edge cases
- test_fillna.py: Test all fill modes, NaN patterns
- test_element_wise.py: Test clip bounds, round decimals
- test_correlation.py: Test correlation/covariance matrices

### Task 7: Warmup Integration
Update _warmup.py:
- warmup_aggregations()
- warmup_fillna()
- warmup_element_wise()
- warmup_correlation()

### Task 8: Patch Registration
Update __init__.py:
- Import and call apply_*_patches() functions
- Register with _apply_all_patches()

### Task 9: Benchmarks
- bench_aggregations.py
- bench_fillna.py
- bench_element_wise.py
- bench_correlation.py

### Task 10: QA Validation
- Run all tests
- Run benchmarks
- Verify pandas compatibility
- Architect review

---

## File Manifest

### New Files to Create
1. `src/unlockedpd/ops/aggregations.py`
2. `src/unlockedpd/ops/fillna.py`
3. `src/unlockedpd/ops/element_wise.py`
4. `src/unlockedpd/ops/correlation.py`
5. `tests/test_aggregations.py`
6. `tests/test_fillna.py`
7. `tests/test_element_wise.py`
8. `tests/test_correlation.py`
9. `benchmarks/bench_aggregations.py`
10. `benchmarks/bench_fillna.py`
11. `benchmarks/bench_element_wise.py`
12. `benchmarks/bench_correlation.py`

### Files to Modify
1. `src/unlockedpd/__init__.py` - Add new patch registrations
2. `src/unlockedpd/_warmup.py` - Add warmup functions

---

## Acceptance Criteria
- [ ] Git worktree created successfully
- [ ] All operations implemented with 3-tier dispatch
- [ ] Tests pass with pandas compatibility (rtol=1e-10)
- [ ] Warmup eliminates first-call overhead
- [ ] Benchmarks show >= 2x speedup on large arrays
- [ ] Architect verification passed
