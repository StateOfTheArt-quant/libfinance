# -*- coding: utf-8 -*-
"""The data version is asked off the call path once one is known (stale-while-revalidate).

A user one round trip (~185 ms) from the server paid it on almost every interactive call: the
version was re-asked synchronously whenever two seconds had passed since the last ask.
"""
import threading
import time

from libfinance.utils import cache


def test_a_stale_version_answers_at_once_and_is_refreshed_in_the_background(monkeypatch):
    asked = threading.Event()
    release = threading.Event()

    def slow_ask():
        asked.set()
        release.wait(2)
        return "v2"

    cache.clear_all()
    monkeypatch.setattr(cache, "_ask_version", lambda: "v1")
    assert cache.current_data_version() == "v1"          # nothing known yet: asked synchronously

    monkeypatch.setattr(cache, "_ask_version", slow_ask)
    monkeypatch.setattr(cache, "_version_checked_at", time.time() - 10)
    started = time.perf_counter()
    assert cache.current_data_version() == "v1"          # stale: answered with what is known ...
    assert time.perf_counter() - started < 0.1           # ... without waiting for the server
    assert asked.wait(1)                                 # the refresh went out in the background
    release.set()
    for _ in range(100):
        if cache.current_data_version() == "v2":
            break
        time.sleep(0.01)
    assert cache.current_data_version() == "v2"
    cache.clear_all()


def test_force_still_asks_synchronously(monkeypatch):
    cache.clear_all()
    monkeypatch.setattr(cache, "_ask_version", lambda: "v1")
    cache.current_data_version()
    monkeypatch.setattr(cache, "_ask_version", lambda: "v9")
    assert cache.current_data_version(force=True) == "v9"
    cache.clear_all()
