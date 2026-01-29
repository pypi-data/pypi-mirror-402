# MPMS Changelog

## Version 2.6.0.2

### Fixes
- Spawn-based restart now falls back to fork when the worker config cannot be serialized (e.g. bound method capturing `multiprocessing.Queue`); spawn restarts are disabled after the first failure (warn once)

## Version 2.6.0.1

### Changes
- Auto-start MPMS on first `put()` (no longer requires an explicit `start()` call)

## Version 2.6.0.0

### Fixes / Stability
- Protect shared state (`running_tasks`, counters) with a lock to avoid race conditions
- Make hard-timeout reporting idempotent and prevent duplicate counting/handling
- Improve `close(wait_for_empty=True)` reliability (best-effort qsize-based waiting + warnings)
- Fix `close()` stop-signal count (based on current process pool, not historical starts)
- Replace `os._exit(1)` on graceful-die timeout with a cleaner exit path (allow finalizers)
- Prevent silent drops when worker results/exceptions are unpickleable (safe error wrapper)
- Safer subprocess restart strategy to avoid fork-related deadlocks in multi-threaded master process
- Make `graceful_shutdown` non-blocking on `wait_for_empty` and avoid crash-heavy shutdown hangs

### Observability
- Warn when `result_q` backlog grows beyond a threshold (best-effort)

### Packaging
- Declare `cloudpickle` runtime dependency (used for spawn-based restarts)

## Version 2.5.4.0

### Fixes
- Fix error when `p.is_alive()` raises exception

## Version 2.5.0 (Unreleased)

### New Features
- **Iterator-based Result Collection**: Added `iter_results()` method as an alternative to the collector pattern
  - Provides a more Pythonic way to process task results
  - Supports timeout parameter for result retrieval
  - Cannot be used together with collector parameter
  - Must call `close()` before using `iter_results()`
  - Automatically handles Meta object creation and cleanup

### Improvements
- Result queue is now always created to support both collector and iter_results patterns
- Enhanced task tracking to support iter_results when collector is not specified
- Added comprehensive error handling for iter_results edge cases

### Examples
- Added `demo_iter_results.py` with multiple usage scenarios
- Added `test_iter_results.py` for testing the new functionality
- Added `example_iter_results_simple.py` as a simple demonstration

## Version 2.4.1
- Previous release (baseline for changes)

## Version 2.2.0
- Added lifecycle management features
  - Count-based lifecycle control
  - Time-based lifecycle control
  - Hard timeout limits for processes and tasks 
