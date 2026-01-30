# LSP Computational Graph Implementation Plan

## Overview

**Project:** Add Lazy/Staged/Parallel (LSP) Computational Graph to unlockedpd
**Target Version:** 0.3.0
**Branch:** `feature/lsp-computational-graph`
**Primary Goal:** Enable lazy evaluation with parallel execution while maintaining 100% pandas API compatibility

---

## 1. Requirements Summary

### What We Are Building

An LSP (Lazy/Staged/Parallel) computational graph system that:

1. **Lazy Evaluation** - Operations build an expression graph instead of executing immediately
2. **Parallel Execution** - Leverages existing Numba kernels with optimized scheduling
3. **100% Pandas Compatibility** - Identical API, results must match pandas exactly

### Why This Matters

Current unlockedpd achieves 5-15x speedups through parallelism, but:
- Each operation allocates new memory and iterates through data
- Sequential operations miss optimization opportunities
- No ability to optimize execution order across operation chains

With LSP:
- **Reduced intermediate allocations**: No temporary DataFrames between ops
- **Better cache utilization**: Process data while it's still in L1/L2 cache
- **Foundation for future fusion**: Correct lazy execution enables future optimization

### Terminology Clarification

"LSP" in this context means:
- **L**azy: Defer execution until result is actually needed
- **S**taged: Build up a computation graph (stages) before executing
- **P**arallel: Execute the optimized graph using parallel Numba kernels

---

## 2. Acceptance Criteria

### Must Have (P0)

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 1 | Lazy mode can be enabled via `config.lazy = True` or context manager | Unit test |
| 2 | Graph captures at least: diff, pct_change, shift, rolling.mean/sum/std | Unit tests for each |
| 3 | `collect()` / `compute()` triggers execution and returns pandas DataFrame | Unit test |
| 4 | Results match pandas exactly (within floating point tolerance) | Comparison tests against pandas |
| 5 | Existing eager mode continues to work unchanged when lazy=False | Regression tests |
| 6 | Fallback to eager execution for unsupported operations | Fallback test |
| 7 | Series operations warn and fall back to eager mode | Warning + fallback test |

### Should Have (P1)

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 8 | Clear error messages when graph execution fails | Error handling tests |
| 9 | Graph can be visualized/printed for debugging | Manual verification |
| 10 | Performance improvement on chained operations vs eager | Benchmark suite |
| 11 | Mixed lazy/eager chains handled correctly with explicit materialization | Integration test |

### Nice to Have (P2)

| # | Criterion | How to Verify |
|---|-----------|---------------|
| 12 | Common subexpression elimination | Graph inspection test |
| 13 | Dead code elimination | Graph inspection test |

---

## 3. Architecture Design

### 3.1 High-Level Architecture

```
                                    User Code
                                        |
                                        v
    +------------------------------------------------------------------+
    |                         pandas API (unchanged)                     |
    +------------------------------------------------------------------+
                                        |
                                        v
    +------------------------------------------------------------------+
    |                      unlockedpd Patch Layer                       |
    |                         (_patch.py)                               |
    +------------------------------------------------------------------+
                    |                               |
          [lazy=False]                       [lazy=True]
                    |                               |
                    v                               v
    +---------------------------+    +---------------------------+
    |    Eager Execution        |    |    Graph Builder          |
    |    (current behavior)     |    |    (NEW: _graph.py)       |
    +---------------------------+    +---------------------------+
                    |                               |
                    v                               v
    +---------------------------+    +---------------------------+
    |    Numba Kernels          |    |    Expression Nodes       |
    |    (ops/*.py)             |    |    (NEW: _expr.py)        |
    +---------------------------+    +---------------------------+
                                                    |
                                                    v
                                     +---------------------------+
                                     |    Graph Executor         |
                                     |    (NEW: _executor.py)    |
                                     +---------------------------+
                                                    |
                                                    v
                                     +---------------------------+
                                     |    Numba Kernels          |
                                     |    (existing ops/*.py)    |
                                     +---------------------------+
```

### 3.2 Core Components

#### 3.2.1 Expression Nodes (`src/unlockedpd/graph/_expr.py`)

```python
# Abstract node types in the expression tree
@dataclass
class Expr:
    """Base class for all expression nodes."""
    _id: int  # Unique ID for graph operations

@dataclass
class InputExpr(Expr):
    """Leaf node representing input DataFrame."""
    df: pd.DataFrame

@dataclass
class TransformExpr(Expr):
    """Node for transform operations (diff, pct_change, shift)."""
    input: Expr
    op: str  # 'diff', 'pct_change', 'shift'
    params: dict  # {'periods': 1, 'axis': 0, 'fill_method': 'pad', ...}

# TransformExpr.params specification:
# - diff: {'periods': int, 'axis': int}
# - pct_change: {'periods': int, 'fill_method': str|None}
#   fill_method can be: 'pad', 'ffill', 'bfill', 'backfill', or None
#   When fill_method is not None, executor must apply fill BEFORE computing pct_change
# - shift: {'periods': int, 'fill_value': Any|None}

@dataclass
class RollingExpr(Expr):
    """Node for rolling window operations."""
    input: Expr
    window: int
    min_periods: int
    center: bool

@dataclass
class RollingAggExpr(Expr):
    """Node for rolling aggregation (mean, sum, std, etc.)."""
    rolling: RollingExpr
    agg: str  # 'mean', 'sum', 'std', 'var', 'min', 'max'
```

#### 3.2.2 Lazy DataFrame Wrapper (`src/unlockedpd/graph/_lazy.py`)

```python
class LazyDataFrame:
    """Wraps a computation graph, provides pandas-like API."""

    def __init__(self, expr: Expr):
        self._expr = expr

    def diff(self, periods=1, axis=0) -> 'LazyDataFrame':
        """Returns new LazyDataFrame with diff node added."""
        return LazyDataFrame(TransformExpr(
            input=self._expr,
            op='diff',
            params={'periods': periods, 'axis': axis}
        ))

    def pct_change(self, periods=1, fill_method='pad', limit=None, freq=None) -> 'LazyDataFrame':
        """Returns new LazyDataFrame with pct_change node added."""
        if limit is not None or freq is not None:
            # Fall back to eager for unsupported params
            return self._fallback_eager('pct_change', periods=periods,
                                        fill_method=fill_method, limit=limit, freq=freq)
        return LazyDataFrame(TransformExpr(
            input=self._expr,
            op='pct_change',
            params={'periods': periods, 'fill_method': fill_method}
        ))

    def rolling(self, window, min_periods=None, center=False, ...) -> 'LazyDataFrame':
        """Returns LazyDataFrame with RollingExpr attached, ready for aggregation."""
        # Store rolling params in the LazyDataFrame for next aggregation call
        rolling_expr = RollingExpr(
            input=self._expr,
            window=window,
            min_periods=min_periods if min_periods is not None else window,
            center=center
        )
        return LazyDataFrame(rolling_expr, _pending_rolling=True)

    def mean(self) -> 'LazyDataFrame':
        """If called after rolling(), creates RollingAggExpr."""
        if self._pending_rolling:
            return LazyDataFrame(RollingAggExpr(
                rolling=self._expr,  # self._expr is RollingExpr
                agg='mean'
            ))
        raise AttributeError("mean() only available after rolling()")

    # Similar for sum(), std(), var(), min(), max()

    def collect(self) -> pd.DataFrame:
        """Execute graph and return result as pandas DataFrame."""
        from ._executor import execute_graph
        return execute_graph(self._expr)

    # Alias for Polars users
    compute = collect
```

**Rolling Operations Dispatch Mechanism:**

Rolling operations in pandas use a two-step pattern: `df.rolling(window).mean()`. The `.rolling()` call returns a `Rolling` object, then `.mean()` is called on that.

For lazy mode, we intercept at the aggregation method level (`Rolling.mean()`, `Rolling.std()`, etc.) rather than creating a separate `LazyRolling` type:

```python
# In _patch.py, patch Rolling methods
def patch_rolling_method(method_name):
    original = getattr(pd.core.window.rolling.Rolling, method_name)

    @functools.wraps(original)
    def wrapper(self, *args, **kwargs):
        if not config.lazy:
            return original(self, *args, **kwargs)

        # At this point we have access to:
        # - self.obj: the underlying DataFrame
        # - self.window: window size
        # - self.min_periods: min periods
        # - self.center: center flag

        # Check if underlying object is already lazy
        underlying = self.obj
        if isinstance(underlying, LazyDataFrame):
            input_expr = underlying._expr
        else:
            input_expr = InputExpr(df=underlying)

        rolling_expr = RollingExpr(
            input=input_expr,
            window=self.window,
            min_periods=self.min_periods,
            center=self.center
        )
        return LazyDataFrame(RollingAggExpr(
            rolling=rolling_expr,
            agg=method_name
        ))

    return wrapper

# Patch rolling aggregation methods
for method in ['mean', 'sum', 'std', 'var', 'min', 'max']:
    setattr(pd.core.window.rolling.Rolling, method, patch_rolling_method(method))
```

This approach:
- Requires no new public types users must learn
- Has access to all rolling parameters at the point of aggregation
- Integrates cleanly with existing lazy DataFrames in the chain

#### 3.2.3 Graph Executor (`src/unlockedpd/graph/_executor.py`)

```python
def execute_graph(expr: Expr) -> pd.DataFrame:
    """Execute expression graph."""
    # 1. Topological sort to get execution order
    nodes = topological_sort(expr)

    # 2. Execute nodes, caching intermediate results
    cache = {}
    for node in nodes:
        result = execute_node(node, cache)
        cache[node._id] = result

    # 3. Return final result
    return cache[expr._id]

def execute_node(node: Expr, cache: dict) -> pd.DataFrame:
    """Execute a single node."""
    if isinstance(node, InputExpr):
        return node.df

    elif isinstance(node, TransformExpr):
        input_df = cache[node.input._id]
        if node.op == 'diff':
            return optimized_diff(input_df, **node.params)
        elif node.op == 'pct_change':
            # fill_method is handled inside optimized_pct_change
            return optimized_pct_change(input_df, **node.params)
        elif node.op == 'shift':
            return optimized_shift(input_df, **node.params)

    elif isinstance(node, RollingAggExpr):
        rolling_node = node.rolling
        input_df = cache[rolling_node.input._id]
        # Call existing rolling implementation
        return execute_rolling_agg(input_df, rolling_node, node.agg)
```

### 3.3 Series Handling

**Design Decision:** Series operations warn and fall back to eager execution.

When lazy mode is enabled and a Series operation is detected:

```python
# In _patch.py or relevant dispatcher
def dispatch_lazy_or_eager(obj, operation, *args, **kwargs):
    if config.lazy:
        if isinstance(obj, pd.Series):
            if config.warn_on_fallback:
                warnings.warn(
                    f"Series.{operation}() falls back to eager mode in lazy context. "
                    "Lazy mode is currently DataFrame-only.",
                    RuntimeWarning,
                    stacklevel=3
                )
            # Fall through to eager execution
        elif isinstance(obj, pd.DataFrame):
            return create_lazy_node(obj, operation, *args, **kwargs)

    # Eager path
    return eager_dispatch(obj, operation, *args, **kwargs)
```

Configuration for warnings:
```python
@dataclass
class UnlockedConfig:
    # ... existing fields ...
    _warn_on_fallback: bool = field(default=True, repr=False)

    @property
    def warn_on_fallback(self) -> bool:
        with self._lock:
            return self._warn_on_fallback
```

### 3.4 Mixed Lazy/Eager Chain Handling

**Design Decision:** Explicit materialization required at chain boundaries.

When a lazy DataFrame is used in a context that requires an eager value (like `.head()`, indexing, printing), the behavior is:

```python
# LazyDataFrame methods that force materialization
class LazyDataFrame:
    def head(self, n=5) -> pd.DataFrame:
        """Materialize and return head - EAGER operation."""
        if config.warn_on_fallback:
            warnings.warn(
                "head() forces materialization of lazy DataFrame",
                RuntimeWarning
            )
        return self.collect().head(n)

    def __getitem__(self, key):
        """Indexing forces materialization."""
        if config.warn_on_fallback:
            warnings.warn(
                "Indexing forces materialization of lazy DataFrame. "
                "Use .collect() first for explicit control.",
                RuntimeWarning
            )
        return self.collect()[key]

    def __repr__(self):
        """Repr shows graph structure, not data."""
        return f"LazyDataFrame(\n{self._expr}\n)"

    def _repr_html_(self):
        """For Jupyter: show graph, not data."""
        return f"<pre>LazyDataFrame (call .collect() to materialize)\n{self._expr}</pre>"
```

This design:
- Makes materialization explicit (users call `.collect()`)
- Provides escape hatches (`.head()`, indexing) that warn
- Prevents accidental computation in repr

### 3.5 Integration with Existing Code

#### Patching Strategy

The current `_patch.py` already has a fallback mechanism. We extend this:

```python
# In _patch.py, modify the wrapper:
@functools.wraps(original)
def wrapper(self, *args, **kwargs):
    from ._config import config

    if not config.enabled:
        return original(self, *args, **kwargs)

    # NEW: Check for lazy mode
    if config.lazy:
        if isinstance(self, pd.Series):
            if config.warn_on_fallback:
                warnings.warn(
                    f"Series operations fall back to eager mode in lazy context",
                    RuntimeWarning
                )
            # Fall through to eager
        elif isinstance(self, pd.DataFrame):
            from .graph import to_lazy
            return to_lazy(self).operation(*args, **kwargs)

    # Existing eager path
    try:
        return optimized_func(self, *args, **kwargs)
    except Exception as e:
        ...
```

#### Configuration Extension

Extend `_config.py`:

```python
@dataclass
class UnlockedConfig:
    # Existing fields...
    _lazy: bool = field(default=False, repr=False)
    _warn_on_fallback: bool = field(default=True, repr=False)

    @property
    def lazy(self) -> bool:
        """Whether lazy evaluation mode is enabled."""
        with self._lock:
            return self._lazy

    @lazy.setter
    def lazy(self, value: bool) -> None:
        with self._lock:
            self._lazy = bool(value)

    @property
    def warn_on_fallback(self) -> bool:
        with self._lock:
            return self._warn_on_fallback

    @warn_on_fallback.setter
    def warn_on_fallback(self, value: bool) -> None:
        with self._lock:
            self._warn_on_fallback = bool(value)
```

### 3.6 File Structure

```
src/unlockedpd/
├── __init__.py              # Add lazy context manager
├── _config.py               # Add lazy config option
├── _patch.py                # Add lazy mode dispatch
├── graph/                   # NEW: Graph module
│   ├── __init__.py          # Public API
│   ├── _expr.py             # Expression node definitions
│   ├── _lazy.py             # LazyDataFrame wrapper
│   └── _executor.py         # Graph execution engine
└── ops/                     # Existing operations (unchanged)
```

---

## 4. Implementation Tasks

### Phase 1: Foundation (MVP)

#### Task 0.1: Git Branch Setup
**Effort:** 5 minutes

- [ ] Create feature branch: `git checkout -b feature/lsp-computational-graph`
- [ ] Push branch to remote: `git push -u origin feature/lsp-computational-graph`

**Acceptance:** Branch exists and is tracking remote

---

#### Task 1.1: Configuration Extension
**File:** `src/unlockedpd/_config.py`
**Effort:** 1 hour

- [ ] Add `_lazy` field with thread-safe property
- [ ] Add `_warn_on_fallback` field with thread-safe property
- [ ] Add `UNLOCKEDPD_LAZY` environment variable support
- [ ] Unit test for lazy config toggle

**Acceptance:** `config.lazy = True` and `config.warn_on_fallback = False` work thread-safely

---

#### Task 1.2: Expression Node Types
**File:** `src/unlockedpd/graph/_expr.py`
**Effort:** 2-3 hours

- [ ] Define base `Expr` class with unique ID generation
- [ ] Implement `InputExpr` for leaf nodes
- [ ] Implement `TransformExpr` for diff/pct_change/shift with full params:
  - diff: `{'periods': int, 'axis': int}`
  - pct_change: `{'periods': int, 'fill_method': str|None}`
  - shift: `{'periods': int, 'fill_value': Any|None}`
- [ ] Implement `RollingExpr` and `RollingAggExpr`
- [ ] Add `__repr__` for debugging
- [ ] Unit tests for node creation and equality

**Acceptance:** Can create expression trees programmatically with all parameters

---

#### Task 1.3: LazyDataFrame Core
**File:** `src/unlockedpd/graph/_lazy.py`
**Effort:** 3-4 hours

- [ ] Implement `LazyDataFrame` class
- [ ] Add `diff()` with axis parameter
- [ ] Add `pct_change()` with fill_method parameter (fallback for limit/freq)
- [ ] Add `shift()` with fill_value parameter
- [ ] Implement rolling aggregation dispatch (mean, sum, std, var, min, max)
- [ ] Add `collect()` / `compute()` methods
- [ ] Add `explain()` method to print graph structure
- [ ] Add `head()`, `__getitem__` with materialization + warning
- [ ] Add `__repr__` and `_repr_html_` showing graph, not data
- [ ] Unit tests for method chaining

**Acceptance:** `lazy_df.diff().pct_change(fill_method=None).rolling(5).mean()` builds correct graph

---

#### Task 1.4: Basic Executor
**File:** `src/unlockedpd/graph/_executor.py`
**Effort:** 3-4 hours

- [ ] Implement topological sort for expression DAG
- [ ] Implement `execute_node()` dispatcher
- [ ] Handle `TransformExpr` with all params (especially pct_change fill_method)
- [ ] Hook into existing Numba kernels for execution
- [ ] Implement result caching for intermediate nodes
- [ ] Handle edge cases (empty DataFrame, single column, etc.)
- [ ] Unit tests for single-operation execution

**Acceptance:** `LazyDataFrame(df).pct_change(fill_method='bfill').collect()` returns correct result

---

#### Task 1.5: Rolling Operations Integration
**File:** `src/unlockedpd/_patch.py` (extension)
**Effort:** 2-3 hours

- [ ] Patch `Rolling.mean()`, `Rolling.sum()`, `Rolling.std()`, etc.
- [ ] Intercept at aggregation level with access to rolling params
- [ ] Create `RollingAggExpr` nodes with correct `RollingExpr` parents
- [ ] Test that `df.rolling(20).mean()` works in lazy mode
- [ ] Test chained: `df.diff().rolling(20).mean()` builds correct graph

**Acceptance:** Rolling operations captured in graph via patched aggregation methods

---

#### Task 1.6: Series Fallback with Warning
**File:** `src/unlockedpd/_patch.py`
**Effort:** 1 hour

- [ ] Detect Series input in lazy dispatch
- [ ] Issue `RuntimeWarning` when `config.warn_on_fallback=True`
- [ ] Fall back to eager execution for Series
- [ ] Unit test for warning emission
- [ ] Unit test for correct eager result

**Acceptance:** `series.diff()` in lazy mode warns and returns correct eager result

---

#### Task 1.7: Integration with Patch Layer
**File:** `src/unlockedpd/_patch.py`
**Effort:** 2 hours

- [ ] Modify wrapper to check `config.lazy`
- [ ] Return LazyDataFrame when lazy=True and input is DataFrame
- [ ] Ensure eager mode unchanged when lazy=False
- [ ] Handle fallback for unsupported operations
- [ ] Integration tests

**Acceptance:** `df.diff()` returns LazyDataFrame when `config.lazy=True`

---

#### Task 1.8: Lazy Context Manager
**File:** `src/unlockedpd/__init__.py`
**Effort:** 1 hour

- [ ] Add `lazy()` context manager for scoped lazy mode
- [ ] Add `to_lazy(df)` function for explicit conversion
- [ ] Update `__all__` exports

**Acceptance:**
```python
with unlockedpd.lazy():
    result = df.diff().pct_change().collect()
```

---

### Phase 2: Robustness

#### Task 2.1: Comprehensive Testing
**Files:** `tests/test_graph_*.py`
**Effort:** 4-6 hours

- [ ] Test all supported operations in lazy mode
- [ ] Test all combinations with pandas reference
- [ ] Test edge cases (NaN, empty, single row/col)
- [ ] Test mixed dtype DataFrames
- [ ] Test fallback behavior for unsupported ops
- [ ] Test Series fallback with warning capture
- [ ] Test pct_change with all fill_method variants

**Acceptance:** 100% test coverage for graph module

---

#### Task 2.2: Error Handling
**Files:** Multiple
**Effort:** 2-3 hours

- [ ] Clear error for unsupported operations
- [ ] Graceful fallback with warning
- [ ] Graph execution error context (which node failed)
- [ ] Test error paths

**Acceptance:** Errors are actionable, not cryptic

---

#### Task 2.3: Documentation
**Files:** `README.md`, docstrings
**Effort:** 2-3 hours

- [ ] Document lazy mode usage
- [ ] Document Series limitation (warns, falls back)
- [ ] Add examples to README
- [ ] Docstrings for public API
- [ ] Document materialization behavior

**Acceptance:** New user can use lazy mode from docs alone

---

### Phase 3: Performance Validation

#### Task 3.1: Benchmark Suite
**File:** `benchmarks/bench_graph.py`
**Effort:** 2-3 hours

- [ ] Benchmark single operations: eager vs lazy
- [ ] Benchmark chained operations: eager vs lazy
- [ ] Memory allocation tracking
- [ ] Generate comparison report

**Acceptance:** Documented performance characteristics

---

### Phase 4: Future Optimizations (P2 - Nice to Have)

**NOTE:** These tasks are deferred to a future release. Phase 1-3 establishes correct lazy execution; fusion and advanced optimizations come later.

#### Task 4.1: Optimizer Framework
**File:** `src/unlockedpd/graph/_optimize.py`
**Effort:** 2 hours

- [ ] Implement `optimize()` dispatcher
- [ ] Implement tree traversal utilities (map, fold)
- [ ] Add optimization pass infrastructure

---

#### Task 4.2: Common Subexpression Elimination
**Effort:** 3-4 hours

- [ ] Detect identical subexpressions
- [ ] Share computation results

---

#### Task 4.3: Transform Fusion (FUTURE)
**Effort:** 6-8 hours

- [ ] Mathematical proof of fusion formulas
- [ ] Detect fusible patterns
- [ ] Implement fused kernels
- [ ] Comprehensive correctness tests

**Note:** Fusion is complex and requires mathematical validation. Deferring to ensure correctness first.

---

## 5. Guardrails

### Must Have

- [x] All existing tests must pass (regression)
- [x] `config.lazy = False` (default) preserves exact current behavior
- [x] Results match pandas within float tolerance (1e-10)
- [x] Thread-safe configuration
- [x] No breaking changes to public API
- [x] Series operations warn and fall back (do not break)

### Must NOT Have

- [ ] Do NOT modify existing Numba kernels in `ops/` (only add new ones if needed)
- [ ] Do NOT change behavior when `config.enabled = False`
- [ ] Do NOT introduce dependencies beyond existing (numpy, numba, pandas)
- [ ] Do NOT make lazy mode the default in this release
- [ ] Do NOT implement fusion until correctness is validated (Phase 4)

---

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Graph execution slower than eager for simple cases | Medium | Medium | Add heuristic to execute eagerly for single operations |
| Memory usage higher (graph storage) | Low | Low | Graphs are lightweight; optimize if needed |
| API divergence from pandas | Low | High | Test against pandas 2.x API surface |
| Numba compilation overhead | Medium | Medium | Use existing cached kernels |
| pct_change fill_method edge cases | Medium | Medium | Test all fill_method variants against pandas |

---

## 7. Commit Strategy

### Branch: `feature/lsp-computational-graph`

1. **Branch setup**: Create branch, push to remote
2. **Setup commit**: Create graph module structure, add config options
3. **Expression nodes**: Implement `_expr.py` with all node types and params
4. **LazyDataFrame**: Implement `_lazy.py` with method chaining
5. **Basic executor**: Implement `_executor.py` with single-op execution
6. **Rolling integration**: Patch Rolling aggregation methods
7. **Series fallback**: Add Series detection, warning, and fallback
8. **Integration**: Hook into `_patch.py`, add context manager
9. **Tests (MVP)**: Add tests for basic lazy mode
10. **Full test suite**: Comprehensive tests including edge cases
11. **Documentation**: Update README, docstrings
12. **Release prep**: Version bump, changelog

---

## 8. Verification Steps

### Unit Tests

```bash
# Run all tests including new graph tests
pytest tests/ -v

# Run only graph tests
pytest tests/test_graph*.py -v

# Run with coverage
pytest tests/ --cov=unlockedpd --cov-report=html
```

### Integration Tests

```python
# Test that lazy and eager produce identical results
import pandas as pd
import numpy as np
import unlockedpd

df = pd.DataFrame(np.random.randn(1000, 100))

# Eager
unlockedpd.config.lazy = False
eager_result = df.diff().pct_change()

# Lazy
unlockedpd.config.lazy = True
lazy_result = df.diff().pct_change().collect()

pd.testing.assert_frame_equal(eager_result, lazy_result, rtol=1e-10)

# Test fill_method handling
unlockedpd.config.lazy = False
eager_bfill = df.pct_change(fill_method='bfill')

unlockedpd.config.lazy = True
lazy_bfill = df.pct_change(fill_method='bfill').collect()

pd.testing.assert_frame_equal(eager_bfill, lazy_bfill, rtol=1e-10)
```

### Series Fallback Test

```python
import warnings
import pandas as pd
import unlockedpd

series = pd.Series([1, 2, 3, 4, 5])
unlockedpd.config.lazy = True
unlockedpd.config.warn_on_fallback = True

with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    result = series.diff()
    assert len(w) == 1
    assert "Series" in str(w[0].message)
    assert "eager" in str(w[0].message)

# Result should be correct (eager computation)
pd.testing.assert_series_equal(result, pd.Series([float('nan'), 1, 1, 1, 1]))
```

### Performance Validation

```python
# Benchmark script
import time

# Should see improvement for chained operations
%timeit df.diff().pct_change().rolling(20).mean()  # eager
%timeit df.diff().pct_change().rolling(20).mean().collect()  # lazy

# Memory: lazy should use less peak memory for chains
```

---

## 9. Definition of Done

- [ ] All P0 acceptance criteria met
- [ ] All tests pass (existing + new)
- [ ] No regressions in eager mode performance
- [ ] Series operations handled gracefully (warn + fallback)
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] Changelog entry added
- [ ] Version bumped to 0.3.0

---

## 10. Resolved Design Decisions

These questions were raised during planning and have been resolved:

| Question | Decision | Rationale |
|----------|----------|-----------|
| Operation Priority | diff, pct_change, shift, rolling.{mean,sum,std,var,min,max} for v1 | Core transforms; expanding/ewm deferred |
| Materialization Trigger | Explicit `.collect()` required; `.head()` and indexing warn and materialize | Explicit > implicit for lazy semantics |
| Naming | Both `collect()` and `compute()` supported as aliases | Familiar to both Polars and Dask users |
| Default Mode | No per-project default in v1 | Keep simple; environment var is enough |
| Series Support | Warn and fall back to eager | DataFrame-only for v1; Series in v2 if needed |
| Rolling dispatch | Intercept at `Rolling.mean()` level | Access to all params, no new public types |
| Fusion | Deferred to Phase 4 (P2) | Correctness before optimization |
| Mixed chains | Materialization required; escape hatches warn | Prevents hidden computation |

---

*Plan generated by Prometheus - Strategic Planning Consultant*
*Timestamp: 2026-01-20*
*Revision: 2 (Critic feedback incorporated)*
