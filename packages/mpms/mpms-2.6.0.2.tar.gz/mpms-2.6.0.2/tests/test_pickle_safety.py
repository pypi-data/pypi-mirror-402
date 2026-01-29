#!/usr/bin/env python3
# coding=utf-8

import threading

import pytest

from mpms import MPMS


@pytest.mark.timeout(30)
def test_unpickleable_result_is_reported_as_error():
    results = []

    def worker(_):
        # A threading.Lock is not pickleable.
        return threading.Lock()

    def collector(meta, result):
        results.append(result)

    m = MPMS(worker, collector, processes=1, threads=1)
    m.start()
    m.put(1)
    m.join()

    assert len(results) == 1
    assert isinstance(results[0], Exception)
    assert "mpms_unpickleable_result" in str(results[0])


@pytest.mark.timeout(30)
def test_unpickleable_exception_is_reported_as_error():
    results = []

    class MyErr(Exception):
        def __init__(self, msg: str):
            super().__init__(msg)
            self.lock = threading.Lock()  # unpickleable

    def worker(_):
        raise MyErr("boom")

    def collector(meta, result):
        results.append(result)

    m = MPMS(worker, collector, processes=1, threads=1)
    m.start()
    m.put(1)
    m.join()

    assert len(results) == 1
    assert isinstance(results[0], Exception)
    assert "mpms_unpickleable_result" in str(results[0])

