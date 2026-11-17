# -*- coding: utf-8 -*-
"""A long answer on a slow link must not cost the connection (PERF-03, offline loopback server).

The server PINGs every 15 s and drops a connection whose last PONG is older than 45 s; its PING is
queued behind the answer being written, so a client that only answers PINGs goes silent for as long
as a large answer takes to arrive. Seen 2026-11-17: a 3.24 MB get_price over a ~15 KB/s cross-border
path took 180-240 s and every such call ended with "Server closed connection.".
"""
import socket
import struct
import threading
import time

import msgpack

import libfinance.client as client_module
from libfinance.client import FrameType, RpcClient


class TricklingServer:
    """Answers one call with ``size`` bytes sent in ``pieces`` over ``seconds``; records client frames."""

    def __init__(self, size, pieces, seconds):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(1)
        self.port = self.listener.getsockname()[1]
        self.size, self.pieces, self.seconds = size, pieces, seconds
        self.frames = []          # (time, frame type) of everything the client sent
        threading.Thread(target=self._serve, daemon=True).start()

    @staticmethod
    def _recv(sock, n):
        data = b""
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                raise ConnectionError
            data += chunk
        return data

    def _read_frames(self, sock):
        try:
            while True:
                (length,) = struct.unpack("!I", self._recv(sock, 4))
                body = self._recv(sock, length)
                self.frames.append((time.monotonic(), body[0]))
                if body[0] == FrameType.RPC_REQUEST:
                    self.request_id = struct.unpack("!I", body[1:5])[0]
                    self.got_request.set()
        except (ConnectionError, OSError):
            pass

    def _serve(self):
        self.got_request = threading.Event()
        sock, _ = self.listener.accept()
        threading.Thread(target=self._read_frames, args=(sock,), daemon=True).start()
        self.got_request.wait()
        body = msgpack.packb({"status": "ok", "code": 0, "result": {"blob": b"x" * self.size}}, use_bin_type=True)
        frame = (struct.pack("!I", 6 + len(body)) + bytes([FrameType.RPC_RESPONSE])
                 + struct.pack("!I", self.request_id) + bytes([0x00]) + body)
        self.started = time.monotonic()
        step = -(-len(frame) // self.pieces)
        for start in range(0, len(frame), step):
            sock.sendall(frame[start:start + step])
            time.sleep(self.seconds / self.pieces)
        time.sleep(0.2)
        sock.close()


def test_the_client_keeps_the_connection_alive_while_a_long_answer_arrives(monkeypatch):
    monkeypatch.setattr(client_module, "KEEPALIVE_INTERVAL", 0.3)
    server = TricklingServer(size=200_000, pieces=20, seconds=2.0)
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    try:
        answer = client.call("get_price", {}, timeout=30)
    finally:
        client.close()
    assert len(answer["blob"]) == 200_000
    pongs = [t for t, kind in server.frames if kind == FrameType.PONG and t > server.started]
    # one at least every interval while the answer trickled in (2 s / 0.3 s), none needed after it
    assert len(pongs) >= 4, server.frames
    gaps = [b - a for a, b in zip([server.started] + pongs, pongs)]
    assert max(gaps) < 1.0, gaps


def test_a_quick_answer_sends_no_keepalive(monkeypatch):
    monkeypatch.setattr(client_module, "KEEPALIVE_INTERVAL", 5.0)
    server = TricklingServer(size=50_000, pieces=2, seconds=0.1)
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    try:
        assert len(client.call("get_price", {}, timeout=30)["blob"]) == 50_000
    finally:
        client.close()
    assert [kind for _, kind in server.frames] == [FrameType.RPC_REQUEST]


def test_a_large_answer_is_received_in_linear_time():
    """``data += chunk`` re-copied the whole answer on every chunk."""
    server = TricklingServer(size=64 * 1024 * 1024, pieces=4096, seconds=0.0)
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    try:
        started = time.monotonic()
        assert len(client.call("get_price", {}, timeout=120)["blob"]) == 64 * 1024 * 1024
        assert time.monotonic() - started < 20
    finally:
        client.close()
