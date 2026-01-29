#!/usr/bin/env python3
# coding=utf-8

import os
import time
import multiprocessing

from mpms import MPMS


class _ExecWithQueue:
    """
    Bound-method worker that captures a multiprocessing.Queue, which is not cloudpickle-able
    outside a spawning context. This is a common pattern in real apps.
    """

    def __init__(self) -> None:
        self.q = multiprocessing.Queue()

    def worker(self, x: int) -> int:
        if x == 0:
            # Kill the worker process hard to trigger restart paths.
            os._exit(1)
        return x + 100


def test_spawn_restart_falls_back_to_fork_when_worker_not_pickleable():
    exec_ = _ExecWithQueue()
    results: list[object] = []

    def collector(meta, result):
        results.append(result)

    m = MPMS(
        exec_.worker,
        collector,
        processes=1,
        threads=1,
        subproc_check_interval=0.1,
    )

    try:
        m.start()

        # First task crashes the only worker process.
        m.put(0)
        time.sleep(0.2)

        # Force a restart check. This triggers spawn+cloudpickle first; it must not raise, and must
        # disable spawn-restart and fall back to fork on serialization failure.
        m._subproc_check(force=True)
        assert m.worker_processes_pool
        assert m._disable_spawn_restart is True

        # Ensure the restarted worker can still process new tasks.
        m.put(1)
        time.sleep(0.2)

    finally:
        # Best-effort cleanup for flakiness reduction.
        try:
            m.graceful_shutdown(timeout=5.0)
        except Exception:
            pass

    assert any(r == 101 for r in results)

