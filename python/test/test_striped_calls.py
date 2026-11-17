# -*- coding: utf-8 -*-
"""Large queries split across connections (PERF-03), offline against a loopback server.

Each TCP connection over a cross-border path is fast for its first megabytes and then throttled to
50-80 KB/s (measured 2026-11-17), so get_price splits a large query by code into parts that run on
sibling connections carrying the same login.
"""
import socket
import struct
import threading

import msgpack
import pandas as pd
import pytest

import libfinance.client as client_module
from libfinance.api import get_price as get_price_module
from libfinance.client import RpcClient, RpcError


class EchoServer:
    """Every connection: ``login`` (password "right" -> level 100) and an echo of the call's args with
    the connection's number and level; a ``codes`` arg containing "BAD" is refused."""

    def __init__(self):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(16)
        self.port = self.listener.getsockname()[1]
        self.connections = 0
        self.lock = threading.Lock()
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
            with self.lock:
                self.connections += 1
                number = self.connections
            threading.Thread(target=self._serve, args=(sock, number), daemon=True).start()

    def _serve(self, sock, number):
        import lz4.frame
        level = 0
        try:
            while True:
                (length,) = struct.unpack("!I", self._recv(sock, 4))
                body = self._recv(sock, length)
                if body[0] != 0x01:
                    continue
                request_id = struct.unpack("!I", body[1:5])[0]
                payload = body[6:]
                request = msgpack.unpackb(lz4.frame.decompress(payload) if body[5] & 1 else payload, raw=False)
                args = request["args"]
                if request["function"] == "login":
                    level = 100 if args.get("password") == "right" else 0
                    envelope = {"status": "ok", "code": 0, "result": {"status": "successful", "level": level}}
                elif "BAD" in (args.get("codes") or []):
                    envelope = {"status": "error", "code": 2001, "message": "refused BAD"}
                else:
                    envelope = {"status": "ok", "code": 0,
                                "result": {"codes": args.get("codes"), "connection": number, "level": level}}
                answer = msgpack.packb(envelope, use_bin_type=True)
                sock.sendall(struct.pack("!I", 6 + len(answer)) + bytes([0x02]) + struct.pack("!I", request_id)
                             + bytes([0x00]) + answer)
        except (ConnectionError, OSError):
            pass

    def close(self):
        self.listener.close()


@pytest.fixture
def server():
    srv = EchoServer()
    yield srv
    srv.close()


def test_map_calls_runs_each_part_on_its_own_connection_in_order(server):
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    results = client.map_calls("echo", [{"codes": ["A"]}, {"codes": ["B"]}, {"codes": ["C"]}])
    assert [r["codes"] for r in results] == [["A"], ["B"], ["C"]]
    assert len({r["connection"] for r in results}) == 3
    # the siblings are kept for the next call, not reopened
    again = client.map_calls("echo", [{"codes": ["D"]}, {"codes": ["E"]}, {"codes": ["F"]}])
    assert {r["connection"] for r in again} == {r["connection"] for r in results}
    assert server.connections == 3


def test_the_siblings_carry_the_login(server):
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    assert {r["level"] for r in client.map_calls("echo", [{"codes": ["A"]}, {"codes": ["B"]}])} == {0}
    client.login("admin", "right")
    # a sibling opened anonymously before the login is started over with it
    assert {r["level"] for r in client.map_calls("echo", [{"codes": ["A"]}, {"codes": ["B"]}])} == {100}


def test_a_refused_part_is_raised_after_all_parts_finish(server):
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    with pytest.raises(RpcError, match="refused BAD"):
        client.map_calls("echo", [{"codes": ["A"]}, {"codes": ["BAD"]}, {"codes": ["C"]}])
    # the connections stay usable
    assert [r["codes"] for r in client.map_calls("echo", [{"codes": ["A"]}, {"codes": ["B"]}])] == [["A"], ["B"]]


def test_a_single_part_uses_this_connection_only(server):
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    assert client.map_calls("echo", [{"codes": ["A"]}])[0]["connection"] == 1
    assert server.connections == 1


def test_parts_split_only_large_queries(monkeypatch):
    monkeypatch.setattr(client_module, "PARALLEL_CONNECTIONS", 8)
    ids = ["%06d.XSHE" % i for i in range(300)]
    # 300 codes x ~1 year of weekdays ~ 78 000 rows: 8 parts, every code exactly once, in order
    parts = get_price_module._parts(ids, "2023-07-01", "2024-06-28")
    assert len(parts) == 8 and sum(parts, []) == ids
    # one code over a month, or 30 codes over a week: one part
    assert len(get_price_module._parts(ids[:1], "2024-05-01", "2024-05-31")) == 1
    assert len(get_price_module._parts(ids[:30], "2024-05-06", "2024-05-10")) == 1
    # never more parts than codes, and LIBFINANCE_PARALLEL=1 keeps one
    monkeypatch.setattr(get_price_module, "_ROWS_PER_PART", 1)
    assert len(get_price_module._parts(ids[:3], "2024-05-06", "2024-05-31")) == 3
    monkeypatch.setattr(client_module, "PARALLEL_CONNECTIONS", 1)
    assert len(get_price_module._parts(ids, "2023-07-01", "2024-06-28")) == 1


def test_get_price_merges_the_parts_into_one_panel(monkeypatch):
    monkeypatch.setattr(client_module, "PARALLEL_CONNECTIONS", 4)
    monkeypatch.setattr(get_price_module, "_ROWS_PER_PART", 1)
    calls = []

    class Client(RpcClient):
        def map_calls(self, function_name, args_list, timeout=None):
            calls.append([args["order_book_ids"] for args in args_list])
            return [pd.DataFrame({"order_book_id": args["order_book_ids"],
                                  "session_date": ["2024-05-06"] * len(args["order_book_ids"]),
                                  "close": [1.0] * len(args["order_book_ids"])}) for args in args_list]

    monkeypatch.setattr(get_price_module, "get_client", lambda: Client())
    panel = get_price_module.get_price(["B.XSHE", "A.XSHE", "D.XSHE", "C.XSHE"], "2024-05-06", "2024-05-06")
    assert calls == [[["B.XSHE"], ["A.XSHE"], ["D.XSHE"], ["C.XSHE"]]]
    assert list(panel.index.get_level_values("order_book_id")) == ["A.XSHE", "B.XSHE", "C.XSHE", "D.XSHE"]
