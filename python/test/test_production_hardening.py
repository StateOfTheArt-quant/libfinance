# -*- coding: utf-8 -*-
"""Behaviour a long-running, multi-threaded or forking process depends on (offline: a loopback server).

Each test names the failure it guards against; all of them were observed against v0.1.7.
"""
import datetime
import multiprocessing
import os
import socket
import struct
import threading
import time

import lz4.frame
import msgpack
import pandas as pd
import pytest

import libfinance
import libfinance.client as client_module
from libfinance.client import RpcClient, RpcError
from libfinance.utils import cache


class Server:
    """Answers every request with ``handler(function, args)`` (an envelope), each on its own thread."""

    def __init__(self, handler, delay=0.0):
        self.handler, self.delay = handler, delay
        self.requests = []
        self.bad_frames = 0
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(32)
        self.port = self.listener.getsockname()[1]
        threading.Thread(target=self._accept, daemon=True).start()

    @staticmethod
    def _recv(sock, n):
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError
            data += chunk
        return data

    def _accept(self):
        while True:
            try:
                sock, _ = self.listener.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(sock,), daemon=True).start()

    def _serve(self, sock):
        lock = threading.Lock()
        try:
            while True:
                (length,) = struct.unpack("!I", self._recv(sock, 4))
                body = self._recv(sock, length)
                request_id, flags = struct.unpack("!I", body[1:5])[0], body[5]
                try:
                    request = msgpack.unpackb(lz4.frame.decompress(body[6:]) if flags & 1 else body[6:], raw=False)
                except Exception:
                    self.bad_frames += 1
                    return
                self.requests.append(request["function"])

                def answer(request=request, request_id=request_id):
                    time.sleep(self.delay)
                    payload = msgpack.packb(self.handler(request["function"], request.get("args") or {}))
                    with lock:
                        sock.sendall(struct.pack("!IBIB", 6 + len(payload), 0x02, request_id, 0) + payload)

                threading.Thread(target=answer, daemon=True).start()
        except (ConnectionError, OSError):
            pass
        finally:
            sock.close()

    def close(self):
        self.listener.close()


def ok(result):
    return {"status": "ok", "code": 0, "result": result}


@pytest.fixture
def server():
    servers = []

    def make(handler, delay=0.0):
        servers.append(Server(handler, delay))
        return servers[-1]

    yield make
    for s in servers:
        s.close()


# ---------------------------------------------------------------- retries

def test_a_refusal_by_the_server_is_sent_once_and_raised_at_once(server):
    """v0.1.7 sent it 3 times with 1.2 s of sleeps: the same request gets the same refusal."""
    srv = server(lambda f, a: {"status": "error", "code": 2001, "kind": "ValueError", "message": "unknown fields"})
    client = RpcClient("127.0.0.1", srv.port)
    started = time.perf_counter()
    with pytest.raises(RpcError) as raised:
        client.get_price(fields=["nope"])
    assert time.perf_counter() - started < 0.5
    assert srv.requests == ["get_price"] and raised.value.kind == "ValueError"
    client.close()


def test_an_undecodable_answer_says_why(server):
    """v0.1.7 raised RpcError(-1, "Unknown error"); the reason went to stderr only."""
    srv = server(lambda f, a: ok(1))
    client = RpcClient("127.0.0.1", srv.port)
    client.connect()
    original = client_module.decode_payload
    client_module.decode_payload = lambda flags, payload: (_ for _ in ()).throw(ValueError("bad lz4 frame"))
    try:
        with pytest.raises(RpcError, match="bad lz4 frame"):
            client.call("f", {}, timeout=5)
    finally:
        client_module.decode_payload = original
        client.close()


def test_a_missing_private_attribute_is_not_a_remote_call(server):
    """v0.1.7 turned any attribute into an RPC: hasattr() was always true, a typo a silent call."""
    srv = server(lambda f, a: ok(1))
    client = RpcClient("127.0.0.1", srv.port)
    assert not hasattr(client, "_no_such_attribute")
    with pytest.raises(AttributeError):
        client.__no_such_dunder__
    assert client.ping() == 1 and srv.requests == ["ping"]     # public names still are
    client.close()


# ---------------------------------------------------------------- threads and processes

def test_large_requests_from_many_threads_do_not_interleave(server):
    """v0.1.7: two sendall() of frames larger than the socket buffer mixed their bytes on the stream."""
    srv = server(lambda f, a: ok(len(a["blob"])))
    client = RpcClient("127.0.0.1", srv.port)
    client.connect()
    blob, errors = os.urandom(4 * 1024 * 1024), []

    def call():
        try:
            assert client.call("echo", {"blob": blob}, timeout=30) == len(blob)
        except Exception as error:  # noqa: BLE001
            errors.append(repr(error))

    threads = [threading.Thread(target=call) for _ in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert not errors and srv.bad_frames == 0
    client.close()


def _child(port, queue):
    try:
        answer = client_module.get_client().call("whoami", {"pid": os.getpid()}, timeout=5)
        queue.put(answer == os.getpid())
    except Exception as error:  # noqa: BLE001
        queue.put(repr(error))


@pytest.mark.skipif(not hasattr(os, "fork"), reason="fork only")
def test_a_forked_child_gets_a_connection_of_its_own(server, monkeypatch):
    """v0.1.7: the child wrote on the parent's socket, the parent's reader took the answers (the child hung
    until its timeout) and the two processes' request ids collided (one got the other's answer)."""
    srv = server(lambda f, a: ok(a["pid"]), delay=0.05)
    monkeypatch.setattr(client_module, "_CLIENT", None)
    client_module.init_client("127.0.0.1", srv.port)
    parent = client_module.get_client()
    assert parent.call("whoami", {"pid": os.getpid()}) == os.getpid()

    context = multiprocessing.get_context("fork")
    queue = context.Queue()
    children = [context.Process(target=_child, args=(srv.port, queue)) for _ in range(4)]
    [c.start() for c in children]
    mine = [parent.call("whoami", {"pid": os.getpid()}, timeout=5) for _ in range(10)]
    [c.join(20) for c in children]
    assert [queue.get(timeout=2) for _ in children] == [True] * 4
    assert mine == [os.getpid()] * 10
    parent.close()


# ---------------------------------------------------------------- caches

@pytest.fixture
def versioned(monkeypatch):
    monkeypatch.setattr(cache, "current_data_version", lambda force=False: "v1")


def test_a_cached_answer_is_handed_out_as_a_copy(versioned):
    """v0.1.7 handed out the cached object: a caller's df.drop(inplace=True) changed everyone's answer."""
    @cache.versioned_cache
    def table():
        return pd.DataFrame({"order_book_id": ["a", "b", "c"]})

    @cache.versioned_cache
    def coverage():
        return {"stock": {"XSHG": {"end": "2026-01-01"}}}

    first = table()
    first.drop(first.index[:2], inplace=True)
    first["junk"] = 1
    assert list(table().columns) == ["order_book_id"] and len(table()) == 3
    coverage()["stock"].clear()
    assert coverage() == {"stock": {"XSHG": {"end": "2026-01-01"}}}


def test_concurrent_cold_misses_load_once(versioned):
    """v0.1.7: 16 threads starting cold sent the same full-table query 16 times."""
    loads = []

    @cache.versioned_cache
    def heavy():
        loads.append(1)
        time.sleep(0.2)
        return [1, 2, 3]

    answers = []
    threads = [threading.Thread(target=lambda: answers.append(heavy())) for _ in range(16)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert len(loads) == 1 and answers == [[1, 2, 3]] * 16


def test_a_failed_load_is_not_cached_and_reaches_every_waiter(versioned):
    attempts = []

    @cache.versioned_cache
    def flaky():
        attempts.append(1)
        if len(attempts) == 1:
            raise ConnectionError("down")
        return "up"

    with pytest.raises(ConnectionError):
        flaky()
    assert flaky() == "up"


# ---------------------------------------------------------------- arguments

@pytest.fixture
def calendar(monkeypatch):
    from libfinance.api import calendar as module

    sessions = pd.to_datetime(["2024-05-13", "2024-05-14", "2024-05-15", "2024-05-16", "2024-05-17"])
    monkeypatch.setattr(module, "_calendar",
                        lambda market="cn": (sessions, pd.Timestamp("2024-05-01"), pd.Timestamp("2024-05-31")))
    return module


@pytest.mark.parametrize("n", [0, -1, -5, 1.5, True, None])
def test_the_nth_trading_day_needs_a_positive_integer(calendar, n):
    """v0.1.7: n=0 answered the day itself; n=-1 indexed from the other end of the calendar."""
    for function in (calendar.get_previous_trading_date, calendar.get_next_trading_date):
        with pytest.raises(ValueError, match="positive integer"):
            function("2024-05-15", n=n)
    with pytest.raises(ValueError, match="positive integer"):
        calendar.get_n_trading_dates_until("2024-05-15", n)


def test_calendar_ranges_and_dates_are_checked(calendar):
    """v0.1.7: a reversed range counted -5 sessions; None became NaT and answered an empty range."""
    assert calendar.count_trading_dates("2024-05-13", "2024-05-17") == 5
    assert calendar.get_previous_trading_date("2024-05-15", n=2) == pd.Timestamp("2024-05-13")
    for function in (calendar.count_trading_dates, calendar.get_trading_dates):
        with pytest.raises(ValueError, match="is after"):
            function("2024-05-17", "2024-05-13")
        with pytest.raises(ValueError, match="date is required"):
            function(None, "2024-05-13")
    with pytest.raises(ValueError, match="date is required"):
        calendar.is_trading_date(None)


class Recorder:
    def __init__(self, answer=None):
        self.calls, self.answer = [], answer

    def __getattr__(self, name):
        def call(**arguments):
            self.calls.append((name, arguments))
            if name == "instruments":
                return []          # the server knows none of the codes asked
            return self.answer if self.answer is not None else pd.DataFrame()
        return call


@pytest.mark.parametrize("as_of", [datetime.date(2024, 1, 1), pd.Timestamp("2024-01-01"),
                                   datetime.datetime(2024, 1, 1, 15, 0)])
def test_pit_financials_take_a_date_as_as_of(monkeypatch, as_of):
    """v0.1.7 passed as_of to msgpack as it came: TypeError("Cannot serialize datetime.date")."""
    from libfinance.api import financials

    recorder = Recorder()
    monkeypatch.setattr(financials, "get_client", lambda: recorder)
    libfinance.get_pit_financials_ex("600000.XSHG", "revenue", "2023q1", "2023-Q4", as_of=as_of)
    sent = recorder.calls[0][1]
    assert isinstance(sent["as_of"], str) and sent["as_of"].startswith("2024-01-01")
    assert (sent["start_quarter"], sent["end_quarter"]) == ("2023q1", "2023q4")
    msgpack.packb(sent)


@pytest.mark.parametrize("quarter", ["2023q5", "2023q0", "q", "abcq1", "2023-03"])
def test_a_malformed_quarter_is_refused_before_the_request(monkeypatch, quarter):
    from libfinance.api import financials

    recorder = Recorder()
    monkeypatch.setattr(financials, "get_client", lambda: recorder)
    with pytest.raises(ValueError, match="quarter"):
        libfinance.get_pit_financials_ex("600000.XSHG", "revenue", quarter, "2023q4")
    assert recorder.calls == []


@pytest.mark.parametrize("name", ["get_instrument_industry", "get_instrument_indices", "get_instrument_themes"])
@pytest.mark.parametrize("bad", [None, [], 600000, ["600000.XSHG", 1]])
def test_reverse_lookups_need_codes(monkeypatch, name, bad):
    """v0.1.7 sent None and [] to the server, which answered an empty table."""
    import importlib

    function = getattr(libfinance, name)
    module = importlib.import_module(function.__module__)
    recorder = Recorder()
    monkeypatch.setattr(module, "get_client", lambda: recorder)
    with pytest.raises(ValueError, match="order_book_ids"):
        function(bad)
    assert recorder.calls == []


def test_get_price_refuses_an_empty_field_list_and_an_int_code():
    with pytest.raises(ValueError, match="at least one field"):
        libfinance.get_price("600000.XSHG", "2024-05-13", "2024-05-17", fields=[])
    with pytest.raises(ValueError, match="order_book_ids"):
        libfinance.get_price(600000, "2024-05-13", "2024-05-17")


def test_get_price_asks_metadata_only_when_the_answer_is_incomplete(monkeypatch):
    """v0.1.7 asked the tier limits and the coverage before every recent query: 4 round trips on a cold start."""
    from libfinance.api import get_price as module

    frame = pd.DataFrame({"order_book_id": ["600000.XSHG"], "session_date": ["2024-05-13"], "close": [7.0]})
    recorder = Recorder(frame)
    asked = []
    monkeypatch.setattr(module, "get_client", lambda: recorder)
    monkeypatch.setattr(module, "warn_if_clamped", lambda *a: asked.append("limits"))
    monkeypatch.setattr(module, "_warn_beyond_coverage", lambda *a: asked.append("coverage"))
    today = datetime.date.today().isoformat()
    module.get_price("600000.XSHG", "2024-05-13", today)
    assert [name for name, _ in recorder.calls] == ["get_price"] and asked == []

    # the answer starts after start_date: it may have been clamped, so the limits are looked up
    module.get_price("600000.XSHG", "2024-05-01", today)
    assert asked == ["limits"]

    # a code with no row at all: instruments tells an unknown code from one without bars
    recorder.calls.clear()
    with pytest.warns(UserWarning, match="999999.XSHG"):
        module.get_price(["600000.XSHG", "999999.XSHG"], "2024-05-13", today)
    assert [name for name, _ in recorder.calls] == ["get_price", "instruments"]
