"""
quote_api.py — Python 客户端 SDK（XTP 风格，对齐 C++ client/quote_api.h）

用法：
    api = QuoteApi()
    api.register_spi(my_spi)
    api.connect("127.0.0.1", 9001)
    api.login("trader1", "pass1234")
    # 按行情源订阅（一条连接可混订多源，回调里 quote.source 区分）
    api.subscribe(["600519"], "SSE", source="webquote")
    api.subscribe(["600519"], "SSE", source="sim")
"""

import socket
import threading
import time
from typing import List, Optional

from libfinance.subscribe.md_protocol import (
    MAGIC, HEADER_SIZE, MsgType,
    unpack_header, pack_login_req, pack_sub_req,
    unpack_login_rsp, unpack_sub_rsp, unpack_quote,
    make_frame, make_heartbeat,
    LoginRsp, SubRsp, Quote,
    LOGIN_REQ_SIZE, SUB_REQ_SIZE,
)


class QuoteSpi:
    """回调基类，用户继承并重写需要的方法。"""
    def on_connected(self) -> None: ...
    def on_disconnected(self, reason: int) -> None: ...
    def on_rsp_login(self, rsp: LoginRsp, request_id: int) -> None: ...
    def on_rsp_subscribe(self, rsp: SubRsp, request_id: int) -> None: ...
    def on_rsp_unsubscribe(self, rsp: SubRsp, request_id: int) -> None: ...
    def on_depth_market_data(self, quote: Quote) -> None: ...
    def on_heartbeat(self) -> None: ...


class QuoteApi:
    def __init__(self):
        self._spi: Optional[QuoteSpi] = None
        self._sock: Optional[socket.socket] = None
        self._connected = False
        self._seq = 1
        self._seq_lock = threading.Lock()

        self._write_queue: list[bytes] = []
        self._write_cond = threading.Condition()
        self._write_stop = False

        self._read_thread: Optional[threading.Thread] = None
        self._write_thread: Optional[threading.Thread] = None
        self._hb_thread: Optional[threading.Thread] = None

    def register_spi(self, spi: QuoteSpi) -> None:
        self._spi = spi

    # ── 连接 ──────────────────────────────────────────────────────
    def connect(self, ip: str, port: int, timeout: float = 3.0) -> int:
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(timeout)
            self._sock.connect((ip, port))
            self._sock.settimeout(60.0)
        except OSError as e:
            print(f"[QuoteApi] connect failed: {e}")
            return -1

        self._connected = True
        self._write_stop = False

        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._write_thread = threading.Thread(target=self._write_loop, daemon=True)
        self._hb_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._read_thread.start()
        self._write_thread.start()
        self._hb_thread.start()

        if self._spi:
            self._spi.on_connected()
        return 0

    # ── 登录 ──────────────────────────────────────────────────────
    def login(self, user_id: str, password: str) -> int:
        seq = self._next_seq()
        body = pack_login_req(user_id, password)
        self._enqueue(make_frame(MsgType.REQ_LOGIN, seq, body))
        return seq

    # ── 订阅 ──────────────────────────────────────────────────────
    # source：行情源（sim / cxxquote / webquote / ...）。空 = 网关默认源。
    # 一条连接可对不同 source 分别 subscribe，行情回调里靠 quote.source 区分。
    def subscribe(self, instruments: List[str], exchange_id: str, source: str = "") -> int:
        last = 0
        for inst in instruments:
            seq = self._next_seq()
            body = pack_sub_req(exchange_id, inst, source)
            self._enqueue(make_frame(MsgType.REQ_SUBSCRIBE, seq, body))
            last = seq
        return last

    # ── 全市场订阅（按 source）────────────────────────────────────
    # 一条请求让网关触发该源 subscribe_all（webquote→yunhq 全量 list，覆盖全沪深 ~5000+ 只），
    # 之后本连接收到该源所有 instrument 的行情，无需逐只订阅。须已登录。
    def subscribe_all(self, source: str = "") -> int:
        seq = self._next_seq()
        body = pack_sub_req("", "", source)
        self._enqueue(make_frame(MsgType.REQ_SUBSCRIBE_ALL, seq, body))
        return seq

    # ── 退订 ──────────────────────────────────────────────────────
    def unsubscribe(self, instruments: List[str], exchange_id: str, source: str = "") -> int:
        last = 0
        for inst in instruments:
            seq = self._next_seq()
            body = pack_sub_req(exchange_id, inst, source)
            self._enqueue(make_frame(MsgType.REQ_UNSUBSCRIBE, seq, body))
            last = seq
        return last

    # ── 断开 ──────────────────────────────────────────────────────
    def disconnect(self) -> None:
        self._connected = False
        self._write_stop = True
        with self._write_cond:
            self._write_cond.notify_all()
        # 先等 write 线程退出，再关 socket，避免 sendall 时 _sock 已为 None
        if self._write_thread and self._write_thread.is_alive():
            self._write_thread.join(timeout=2.0)
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self._sock.close()
            self._sock = None
        for t in (self._read_thread, self._hb_thread):
            if t and t.is_alive():
                t.join(timeout=2.0)

    # ── 内部实现 ──────────────────────────────────────────────────
    def _next_seq(self) -> int:
        with self._seq_lock:
            s = self._seq
            self._seq += 1
            return s

    def _enqueue(self, data: bytes) -> None:
        with self._write_cond:
            self._write_queue.append(data)
            self._write_cond.notify()

    def _recv_exact(self, n: int) -> Optional[bytes]:
        buf = bytearray()
        while len(buf) < n:
            sock = self._sock
            if sock is None:
                return None
            try:
                chunk = sock.recv(n - len(buf))
            except OSError:
                return None
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    def _send_exact(self, data: bytes) -> bool:
        sock = self._sock
        if sock is None:
            return False
        try:
            sock.sendall(data)
            return True
        except OSError:
            return False

    def _read_loop(self) -> None:
        while self._connected:
            hdr_data = self._recv_exact(HEADER_SIZE)
            if hdr_data is None:
                break
            magic, _ver, msg_type, seq_no, body_len = unpack_header(hdr_data)
            if magic != MAGIC:
                print("[QuoteApi] bad magic")
                break
            body = b""
            if body_len > 0:
                body = self._recv_exact(body_len)
                if body is None:
                    break
            self._dispatch(msg_type, seq_no, body)
        if self._spi:
            self._spi.on_disconnected(0)

    def _write_loop(self) -> None:
        while True:
            with self._write_cond:
                self._write_cond.wait_for(
                    lambda: self._write_queue or self._write_stop
                )
                if self._write_stop and not self._write_queue:
                    break
                batch = list(self._write_queue)
                self._write_queue.clear()
            for data in batch:
                if not self._send_exact(data):
                    return

    def _heartbeat_loop(self) -> None:
        while self._connected:
            time.sleep(10)
            if not self._connected:
                break
            self._enqueue(make_heartbeat(self._next_seq()))

    def _dispatch(self, msg_type: int, seq_no: int, body: bytes) -> None:
        if not self._spi:
            return
        t = MsgType(msg_type)
        if t == MsgType.RSP_LOGIN:
            self._spi.on_rsp_login(unpack_login_rsp(body), seq_no)
        elif t == MsgType.RSP_SUBSCRIBE or t == MsgType.RSP_SUBSCRIBE_ALL:
            self._spi.on_rsp_subscribe(unpack_sub_rsp(body), seq_no)
        elif t == MsgType.RSP_UNSUBSCRIBE:
            self._spi.on_rsp_unsubscribe(unpack_sub_rsp(body), seq_no)
        elif t == MsgType.MD_QUOTE:
            self._spi.on_depth_market_data(unpack_quote(body))
        elif t == MsgType.HEARTBEAT:
            self._spi.on_heartbeat()
