# Performance Regression CI Job - Implementation Plan

## Overview

This plan outlines the implementation of a CI job to catch performance regressions in windkit. The job will test import timing, function execution benchmarks, and memory usage.

## Goals

1. **Catch regressions** in import time (target: < 1 second)
2. **Benchmark critical functions** and track performance over time
3. **Fail CI** when performance degrades beyond acceptable thresholds
4. **Provide actionable reports** showing what regressed and by how much

---

## Implementation Components

### 1. Performance Test Module

**File: `test/test_performance.py`**

```python
"""Performance regression tests for windkit."""

import sys
import time
import pytest

# Thresholds (in seconds)
IMPORT_TIME_THRESHOLD = 1.0  # Maximum acceptable import time
IMPORT_TIME_WARNING = 0.8    # Warning threshold


class TestImportPerformance:
    """Tests for import time performance."""

    def test_import_time_under_threshold(self):
        """Verify windkit imports in under 1 second."""
        # Ensure windkit is not already imported
        modules_to_remove = [k for k in sys.modules if k.startswith('windkit')]
        for mod in modules_to_remove:
            del sys.modules[mod]

        start = time.perf_counter()
        import windkit  # noqa: F401
        elapsed = time.perf_counter() - start

        assert elapsed < IMPORT_TIME_THRESHOLD, (
            f"Import time {elapsed:.3f}s exceeds threshold {IMPORT_TIME_THRESHOLD}s"
        )

    def test_lazy_imports_not_loaded(self):
        """Verify heavy optional dependencies are not loaded on import."""
        modules_to_remove = [k for k in sys.modules if k.startswith('windkit')]
        for mod in modules_to_remove:
            del sys.modules[mod]

        import windkit  # noqa: F401

        # These should NOT be loaded on import
        lazy_modules = [
            'matplotlib',
            'numba',
            'scipy.stats',
            'pystac_client',
            'pydantic_settings',
        ]

        for mod in lazy_modules:
            assert mod not in sys.modules, (
                f"Module '{mod}' should not be loaded on 'import windkit'"
            )


@pytest.mark.slow
class TestFunctionBenchmarks:
    """Benchmark tests for critical functions."""

    def test_create_bwc_performance(self, benchmark_output_locs):
        """Benchmark create_bwc function."""
        import windkit as wk

        start = time.perf_counter()
        wk.create_bwc(benchmark_output_locs, n_sectors=12, n_wsbins=30)
        elapsed = time.perf_counter() - start

        # Log timing for tracking
        print(f"create_bwc: {elapsed:.4f}s")

        # Threshold TBD based on baseline measurements
        assert elapsed < 5.0, f"create_bwc took {elapsed:.3f}s, exceeds threshold"

    def test_spatial_operations_performance(self, benchmark_dataset):
        """Benchmark spatial operations."""
        import windkit as wk

        start = time.perf_counter()
        wk.spatial.to_point(benchmark_dataset)
        elapsed = time.perf_counter() - start

        print(f"to_point: {elapsed:.4f}s")
        assert elapsed < 1.0, f"to_point took {elapsed:.3f}s, exceeds threshold"
```

### 2. Benchmark Fixtures

**File: `test/fixtures/fixture_benchmarks.py`**

```python
"""Fixtures for performance benchmarks."""

import pytest
import numpy as np


@pytest.fixture(scope="module")
def benchmark_output_locs():
    """Create a standard dataset for benchmarking."""
    import windkit as wk

    return wk.spatial.create_point(
        x=[0, 1, 2],
        y=[0, 1, 2],
        z=[10, 20, 30],
        crs=4326
    )


@pytest.fixture(scope="module")
def benchmark_dataset():
    """Create a larger dataset for spatial benchmarks."""
    import windkit as wk

    # Create a 100x100 grid for meaningful benchmarks
    x = np.linspace(0, 100, 50)
    y = np.linspace(0, 100, 50)

    return wk.spatial.create_raster(
        x=x,
        y=y,
        crs=32632
    )
```

### 3. pytest-benchmark Integration (Optional Enhancement)

**Add to `pixi.toml` feature.dev.dependencies:**

```toml
[feature.dev.dependencies]
pytest-benchmark = "*"
```

**Enhanced benchmark test using pytest-benchmark:**

```python
def test_import_time_benchmark(benchmark):
    """Benchmark import time with pytest-benchmark."""
    def import_windkit():
        modules = [k for k in sys.modules if k.startswith('windkit')]
        for mod in modules:
            del sys.modules[mod]
        import windkit
        return windkit

    result = benchmark(import_windkit)
    assert result is not None
```

### 4. CI Job Configuration

**Add to `.gitlab-ci.yml`:**

```yaml
# Performance regression tests
performance_tests:
  extends:
    - .pixi_pytest
  stage: test
  before_script:
    - mkdir -p ~/.config/windkit/
    - cp .conda_env/windkit.ini ~/.config/windkit/windkit.ini
  variables:
    PIXI_ENV: "default"
  script:
    - pixi run -e $PIXI_ENV test-performance
  artifacts:
    when: always
    paths:
      - performance_results/
    reports:
      junit: performance_junit.xml
    expire_in: 1 month
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  allow_failure: false  # Fail the pipeline on performance regression
```

### 5. Pixi Task Configuration

**Add to `pixi.toml`:**

```toml
[feature.dev.tasks]
# ... existing tasks ...

# Performance tests
test-performance = {cmd="cd test; pytest test_performance.py -v --tb=short --junitxml=../performance_junit.xml", depends-on = ["install_tests"]}

# Performance tests with benchmarks (if pytest-benchmark is added)
test-benchmark = {cmd="cd test; pytest test_performance.py -v --benchmark-only --benchmark-json=../performance_results/benchmark.json", depends-on = ["install_tests"]}
```

---

## Implementation Phases

### Phase 1: Basic Import Time Testing (Minimal)
- [ ] Create `test/test_performance.py` with import time tests
- [ ] Add `performance` marker to `pyproject.toml`
- [ ] Add `test-performance` task to `pixi.toml`
- [ ] Verify tests pass locally

### Phase 2: CI Integration
- [ ] Add `performance_tests` job to `.gitlab-ci.yml`
- [ ] Configure artifacts for performance results
- [ ] Test in MR pipeline

### Phase 3: Function Benchmarks (Optional)
- [ ] Add `pytest-benchmark` dependency
- [ ] Create benchmark fixtures
- [ ] Add benchmark tests for critical functions
- [ ] Store benchmark history for trend analysis

### Phase 4: Advanced Monitoring (Future)
- [ ] Memory profiling with `pytest-memray` or `memory_profiler`
- [ ] Benchmark comparison against main branch
- [ ] Performance dashboard/visualization
- [ ] Slack/email alerts on regression

---

## Thresholds and Metrics

| Metric | Threshold | Warning | Action on Failure |
|--------|-----------|---------|-------------------|
| Import time | < 1.0s | < 0.8s | Block merge |
| Lazy modules loaded | 0 | - | Block merge |
| create_bwc | < 5.0s | < 3.0s | Warning |
| Spatial operations | < 1.0s | < 0.5s | Warning |

---

## File Changes Summary

| File | Change |
|------|--------|
| `test/test_performance.py` | New file - performance tests |
| `test/fixtures/fixture_benchmarks.py` | New file - benchmark fixtures |
| `test/conftest.py` | Import benchmark fixtures |
| `pixi.toml` | Add test-performance task |
| `.gitlab-ci.yml` | Add performance_tests job |
| `pyproject.toml` | Add performance marker |

---

## Questions to Consider

1. **Should performance tests run on every MR or only on main?**
   - Recommendation: Run on every MR to catch regressions before merge

2. **Should we use pytest-benchmark for detailed tracking?**
   - Recommendation: Start simple, add later if needed

3. **What functions should be benchmarked?**
   - Import time (critical)
   - create_bwc, create_tswc (commonly used)
   - Spatial transformations (performance-sensitive)
   - File I/O operations (user-facing)

4. **How to handle flaky timing tests?**
   - Use generous thresholds (2x expected time)
   - Run multiple iterations and take median
   - Mark as `allow_failure` initially, tighten later

---

## Next Steps

1. Review and approve this plan
2. Implement Phase 1 (basic import time testing)
3. Test locally and in CI
4. Iterate based on results
