"""
quote_api.py — dynamics 消费端 Python SDK（XTP 风格）

    api = QuoteApi()
    api.register_spi(my_spi)
    api.connect("127.0.0.1", 9001)
    api.login("trader1", "pass1234")
    # 订阅写在 on_rsp_login 里：断线自动重连+重登录后会重放（见下）
    api.subscribe(["600519"], "XSHG")                 # 无源订阅，网关选源+灾备
    api.subscribe(["600519"], "XSHG", source="sim")   # 定向订阅指定源

交易所用 rqdata 风格后缀：XSHG(上交所) / XSHE(深交所)。同代码靠后缀区分，
如 000001.XSHG 是上证指数、000001.XSHE 是平安银行。

断线自愈：连接断开后自动重连并自动重登录，登录成功会再次触发 on_rsp_login。
把订阅逻辑写在 on_rsp_login 里即可在重连后自动重放——这是 dynamics 7×24 的约定用法。

路由语义：
  - 同一合约在网关侧只有一个聚合上游路由，不能同时混用自动与定向、也不能定向到不同源，
    冲突请求会通过 on_rsp_subscribe 明确失败（error_id=5）。
  - 行情帧不携带来源；需要知道数据来自哪个源，看订阅回执的 rsp.source，
    或用 query_sources() 查源目录。

错误码：4=无可用源/无可承接整市场的源，5=路由冲突或指定源不可用，6=订阅配额受限。
"""

import socket
import threading
import time
from typing import List, Optional

from libfinance.subscribe.md_protocol import (
    MAGIC, VERSION, HEADER_SIZE, MAX_BODY_LEN, MsgType,
    MarketType, SubscribeInstrumentType, SubscribeDataType,
    unpack_header, make_frame, make_heartbeat,
    pack_login_req, pack_sub_req, pack_sub_all_req,
    unpack_login_rsp, unpack_sub_rsp, unpack_sub_all_rsp,
    unpack_source_dir_list, unpack_quote,
    LoginRsp, SubRsp, SubAllRsp, SourceDirEntry, Quote,
)


class QuoteSpi:
    """回调基类，用户继承并重写需要的方法。回调在 SDK 后台读线程触发，勿做重阻塞。"""
    def on_connected(self) -> None: ...
    def on_disconnected(self, reason: int) -> None: ...
    def on_rsp_login(self, rsp: LoginRsp, request_id: int) -> None: ...
    def on_rsp_subscribe(self, rsp: SubRsp, request_id: int) -> None: ...
    def on_rsp_unsubscribe(self, rsp: SubRsp, request_id: int) -> None: ...
    def on_rsp_subscribe_all(self, rsp: SubAllRsp, request_id: int) -> None: ...
    def on_rsp_unsubscribe_all(self, rsp: SubAllRsp, request_id: int) -> None: ...
    def on_rsp_query_sources(self, sources: List[SourceDirEntry], request_id: int) -> None: ...
    def on_depth_market_data(self, quote: Quote) -> None: ...
    def on_heartbeat(self) -> None: ...


class QuoteApi:
    def __init__(self, auto_reconnect: bool = True):
        self._spi: Optional[QuoteSpi] = None
        self._sock: Optional[socket.socket] = None
        self._connected = False
        self._seq = 1
        self._seq_lock = threading.Lock()

        self._write_queue: List[bytes] = []
        self._write_cond = threading.Condition()

        self._read_thread: Optional[threading.Thread] = None
        self._write_thread: Optional[threading.Thread] = None
        self._hb_thread: Optional[threading.Thread] = None

        # 断线自愈：记住连接参数与登录凭据，重连后自动重放登录
        self._auto_reconnect = auto_reconnect
        self._stopping = False
        self._host = ""
        self._port = 0
        self._timeout = 3.0
        self._creds: Optional[tuple] = None
        self._state_lock = threading.Lock()

    def register_spi(self, spi: QuoteSpi) -> None:
        self._spi = spi

    # ── 连接 ──────────────────────────────────────────────────────
    def connect(self, ip: str, port: int, timeout: float = 3.0) -> int:
        self._host, self._port, self._timeout = ip, port, timeout
        self._stopping = False
        if not self._open_socket():
            return -1
        self._start_threads()
        if self._spi:
            self._spi.on_connected()
        return 0

    # ── 登录 ──────────────────────────────────────────────────────
    # 凭据被记住，断线重连后自动重登录。
    def login(self, user_id: str, password: str) -> int:
        with self._state_lock:
            self._creds = (user_id, password)
        return self._send_login()

    # ── 逐合约订阅 ────────────────────────────────────────────────
    # source 为空 = 无源订阅（网关按健康+优先级选源，源掉线自动灾备切换）；
    # source 非空 = 定向订阅（只推该源数据，不自动切源）。
    def subscribe(self, instruments: List[str], exchange_id: str, source: str = "") -> int:
        last = 0
        for inst in instruments:
            last = self._send(MsgType.REQ_SUBSCRIBE, pack_sub_req(exchange_id, inst, source))
        return last

    def unsubscribe(self, instruments: List[str], exchange_id: str, source: str = "") -> int:
        last = 0
        for inst in instruments:
            last = self._send(MsgType.REQ_UNSUBSCRIBE, pack_sub_req(exchange_id, inst, source))
        return last

    # ── 整市场订阅 ────────────────────────────────────────────────
    # 一次订下「市场 × 品种 × 数据类型」命中的全部合约，任一维度取 All 表示不限。
    # 网关会挑一个申报 whole_market 的健康源承接推送（回执 rsp.source 回显），该源掉线
    # 自动改选，客户端无感。要求账号订阅配额无限制，否则回 error_id=6。
    def subscribe_all(self,
                      market: int = MarketType.All,
                      instrument_type: int = SubscribeInstrumentType.All,
                      data_type: int = SubscribeDataType.All) -> int:
        return self._send(MsgType.REQ_SUBSCRIBE_ALL,
                          pack_sub_all_req(market, instrument_type, data_type))

    def unsubscribe_all(self) -> int:
        """撤销本连接的全部整市场订阅（逐合约订阅不受影响）。"""
        return self._send(MsgType.REQ_UNSUBSCRIBE_ALL)

    # ── 发现 ──────────────────────────────────────────────────────
    def query_sources(self) -> int:
        """查询源目录：哪些源、各覆盖什么、是否健康。应答经 on_rsp_query_sources 返回。"""
        return self._send(MsgType.QUERY_SOURCES)

    # ── 断开 ──────────────────────────────────────────────────────
    def disconnect(self) -> None:
        self._stopping = True
        self._close_socket()
        with self._write_cond:
            self._write_cond.notify_all()
        for t in (self._write_thread, self._read_thread, self._hb_thread):
            if t and t.is_alive() and t is not threading.current_thread():
                t.join(timeout=2.0)

    # ── 内部：连接管理 ────────────────────────────────────────────
    def _open_socket(self) -> bool:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self._timeout)
            sock.connect((self._host, self._port))
            sock.settimeout(None)
        except OSError as e:
            print(f"[QuoteApi] connect {self._host}:{self._port} failed: {e}")
            return False
        self._sock = sock
        self._connected = True
        return True

    def _close_socket(self) -> None:
        self._connected = False
        sock, self._sock = self._sock, None
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def _start_threads(self) -> None:
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._write_thread = threading.Thread(target=self._write_loop, daemon=True)
        self._hb_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._read_thread.start()
        self._write_thread.start()
        self._hb_thread.start()

    def _send_login(self) -> int:
        with self._state_lock:
            creds = self._creds
        if not creds:
            return 0
        return self._send(MsgType.REQ_LOGIN, pack_login_req(creds[0], creds[1]))

    def _next_seq(self) -> int:
        with self._seq_lock:
            s = self._seq
            self._seq += 1
            return s

    def _send(self, msg_type: int, body: bytes = b"") -> int:
        seq = self._next_seq()
        with self._write_cond:
            self._write_queue.append(make_frame(msg_type, seq, body))
            self._write_cond.notify()
        return seq

    # ── 内部：收发循环 ────────────────────────────────────────────
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

    def _read_loop(self) -> None:
        """收帧；断开后按指数退避重连并自动重登录（网关重启对应用无感）。"""
        backoff = 0.5
        while not self._stopping:
            if self._connected:
                if self._read_once():
                    backoff = 0.5      # 正常收到帧，重置退避
                    continue
                # 连接断了。主动 disconnect() 也会走到这里，此时不该报"意外断线"。
                self._close_socket()
                if self._stopping:
                    return
                if self._spi:
                    self._spi.on_disconnected(0)
                if not self._auto_reconnect:
                    return
            time.sleep(backoff)
            if self._stopping:
                return
            if self._open_socket():
                backoff = 0.5
                if self._spi:
                    self._spi.on_connected()
                self._send_login()     # 重登录；应用在 on_rsp_login 里重放订阅
            else:
                backoff = min(backoff * 2, 10.0)

    def _read_once(self) -> bool:
        hdr = self._recv_exact(HEADER_SIZE)
        if hdr is None:
            return False
        magic, ver, msg_type, seq_no, body_len = unpack_header(hdr)
        if magic != MAGIC or ver != VERSION or body_len > MAX_BODY_LEN:
            print(f"[QuoteApi] bad frame: magic=0x{magic:08X} version={ver} body_len={body_len}")
            return False
        body = b""
        if body_len:
            body = self._recv_exact(body_len)
            if body is None:
                return False
        self._dispatch(msg_type, seq_no, body)
        return True

    def _write_loop(self) -> None:
        while not self._stopping:
            with self._write_cond:
                self._write_cond.wait_for(lambda: self._write_queue or self._stopping, timeout=1.0)
                if self._stopping:
                    return
                if not self._write_queue:
                    continue
                batch, self._write_queue = self._write_queue, []
            sock = self._sock
            if sock is None:
                continue   # 断线间隙静默丢弃；重连后由 on_rsp_login 重放订阅
            for data in batch:
                try:
                    sock.sendall(data)
                except OSError:
                    break

    def _heartbeat_loop(self) -> None:
        while not self._stopping:
            time.sleep(10)
            if self._stopping:
                return
            if self._connected:
                self._send(MsgType.HEARTBEAT)

    # ── 内部：分派 ────────────────────────────────────────────────
    def _dispatch(self, msg_type: int, seq_no: int, body: bytes) -> None:
        spi = self._spi
        if not spi:
            return
        if msg_type == MsgType.QUOTE:
            spi.on_depth_market_data(unpack_quote(body))
        elif msg_type == MsgType.RSP_LOGIN:
            spi.on_rsp_login(unpack_login_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_SUBSCRIBE:
            spi.on_rsp_subscribe(unpack_sub_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_UNSUBSCRIBE:
            spi.on_rsp_unsubscribe(unpack_sub_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_SUBSCRIBE_ALL:
            spi.on_rsp_subscribe_all(unpack_sub_all_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_UNSUBSCRIBE_ALL:
            spi.on_rsp_unsubscribe_all(unpack_sub_all_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_QUERY_SOURCES:
            spi.on_rsp_query_sources(unpack_source_dir_list(body), seq_no)
        elif msg_type == MsgType.HEARTBEAT:
            spi.on_heartbeat()
        # 其余行情类型（Entrust/Transaction/Depth/Tick）暂不解包，静默跳过而非断连
