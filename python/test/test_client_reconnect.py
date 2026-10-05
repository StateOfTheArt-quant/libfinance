# -*- coding: utf-8 -*-
"""RpcClient reopens a connection the server closed (offline: a loopback server that speaks the frames).

A blue-green switch drains the old instance and, at its drain limit, stops it: a long-lived client's
connection is cut. Seen 2026-10-04 against deploy-libfinanceserver: every call after that failed with
"Not connected to server." until the process was restarted.
"""
import socket
import struct
import threading

import msgpack

from libfinance.client import RpcClient


class ClosingServer:
    """Answers ``answers_per_connection`` calls on each connection, then closes it."""

    def __init__(self, answers_per_connection=1):
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(8)
        self.port = self.listener.getsockname()[1]
        self.per_connection = answers_per_connection
        self.connections = 0
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

    def _serve(self):
        while True:
            try:
                sock, _ = self.listener.accept()
            except OSError:
                return
            self.connections += 1
            try:
                for _ in range(self.per_connection):
                    (length,) = struct.unpack("!I", self._recv(sock, 4))
                    meta_and_payload = self._recv(sock, length)
                    request_id = struct.unpack("!I", meta_and_payload[1:5])[0]
                    body = msgpack.packb({"status": "ok", "code": 0, "result": {"message": "pong",
                                                                                "connection": self.connections}})
                    sock.sendall(struct.pack("!I", 6 + len(body)) + bytes([0x02]) + struct.pack("!I", request_id)
                                 + bytes([0x00]) + body)
            except ConnectionError:
                pass
            sock.close()          # what a stopped (drained) instance does to the connection

    def close(self):
        self.listener.close()


def test_a_call_after_the_server_closed_the_connection_reconnects():
    server = ClosingServer(answers_per_connection=1)
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    for expected in (1, 2, 3):
        # a raw call() does not retry: wait until the reader has seen the server close, then the next
        # call must open a new connection rather than fail with "Not connected to server."
        for _ in range(100):
            if not client.running or expected == 1:
                break
            threading.Event().wait(0.02)
        assert client.call("ping")["connection"] == expected
    client.close()
    server.close()


def test_the_api_retry_lands_on_a_new_connection():
    """libfinance.* calls go through RpcClient.__call__, which retries: after a drop it must reconnect."""
    server = ClosingServer(answers_per_connection=1)
    client = RpcClient("127.0.0.1", server.port)
    client.connect()
    answers = [client.ping()["connection"] for _ in range(4)]
    assert answers == [1, 2, 3, 4]
    client.close()
    server.close()


def test_an_unreachable_server_is_a_connection_error_not_a_hang():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    client = RpcClient("127.0.0.1", port)
    try:
        client.call("ping")
    except ConnectionError as error:
        assert "Not connected to server" in str(error)
    else:
        raise AssertionError("expected ConnectionError")
