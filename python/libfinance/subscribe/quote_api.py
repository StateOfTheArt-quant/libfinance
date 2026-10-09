"""
quote_api.py — dynamics 实时行情订阅（纯 Python，XTP 风格，协议 v3）

    from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

    class MySpi(QuoteSpi):
        def on_rsp_login(self, rsp, _):
            if rsp.error_id == 0:
                api.subscribe(["600519.XSHG", "000001.XSHE"])   # 写在这里：重连后自动重订阅并续传
        def on_depth_market_data(self, quote, envelope):
            print(quote.order_book_id, quote.last_price)

    api = QuoteApi()
    api.register_spi(MySpi())
    api.connect()          # 不必登录：自动向 libfinance 服务端 取票据，网关地址也由它给出

**不需要登录。** 行情网关（dynamics）只认 libfinance 服务端 签发的短期票据；SDK 在首次连接、每次重连、
票据到期前自动调用 `libfinance.client` 的 `issue_quote_ticket` 取票据并续期，订阅不中断。
没有登录的调用方按 IP 拿到最小一档的额度（订阅数、市场、连接数、每秒消息数）；已登录的按账号等级。
也可以 `login(token)` / `login(provider)` 自己提供票据，或 `connect("host:port,host:port")` 指定网关地址。

代码是 libfinance 统一的 order_book_id（``600519.XSHG``），与 get_price、instruments 等函数同一种写法；
一次订阅可混合交易所。后缀即交易所（order_book_id 的后缀）：XSHG(上交所) / XSHE(深交所) / XBSE(北交所) 及期货交易所，
如 000001.XSHG 是上证指数、000001.XSHE 是平安银行。行情、回执与缺口通知都带 ``order_book_id``。

断线自愈（7×24）：连接断开后自动重连（多个网关地址时立即切到下一个），自动重新登录，并按 seq
**续传**断线期间的记录（不重不漏）。把订阅写在 on_rsp_login 里即可在重连后自动重放。

质量：每条行情附带定序信封（RecordEnvelope：stream / seq / inst_seq / 时间戳）；同一 (合约, 数据类型)
的 inst_seq 不连续说明中间有记录没送达，经 on_sequence_gap 回调；源陈旧 / 恢复经 on_stream_status 回调。

错误码见 md_protocol.ErrorCode：4=无可用源，5=路由冲突或指定源不可用，6=订阅数达到上限，
7=市场不在授权内，8=没有整市场订阅授权，9=续期后授权收缩、订阅被撤销，20~24=票据问题。
"""

import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union

from libfinance.subscribe.md_protocol import (
    MAGIC, VERSION, HEADER_SIZE, MAX_BODY_LEN, HEARTBEAT_INTERVAL, HEARTBEAT_TIMEOUT, MAX_TOKEN_BYTES,
    MsgType, RecordTag, ErrorCode, SessionCloseReason,
    MarketType, SubscribeInstrumentType, SubscribeDataType,
    unpack_header, make_frame, make_heartbeat, instrument_hash, split_order_book_id, _Coded,
    pack_login_req, pack_reauth_req, pack_sub_req, pack_sub_all_req, pack_resume_positions,
    unpack_login_rsp, unpack_sub_rsp, unpack_sub_all_rsp, unpack_source_dir_list,
    unpack_stream_status, unpack_session_closed, iter_batch, RECORD_UNPACKERS,
    LoginRsp, SubRsp, SubAllRsp, SourceDirEntry, StreamStatus, SessionClosed,
    RecordEnvelope, Quote,
)

TokenProvider = Callable[[], str]


@dataclass
class SequenceGap(_Coded):
    """SDK 检测到的缺口：received_inst_seq - expected_inst_seq 条记录未送达。"""
    stream_id: int
    tag: int
    exchange_id: str
    instrument_id: str
    expected_inst_seq: int
    received_inst_seq: int


class QuoteSpi:
    """回调基类，用户继承并重写需要的方法。回调在 SDK 后台读线程触发，勿做重阻塞。"""
    def on_connected(self) -> None: ...
    def on_disconnected(self, reason: int) -> None: ...
    def on_rsp_login(self, rsp: LoginRsp, request_id: int) -> None: ...
    def on_rsp_reauth(self, rsp: LoginRsp) -> None: ...
    def on_session_closed(self, notice: SessionClosed) -> None: ...
    def on_rsp_subscribe(self, rsp: SubRsp, request_id: int) -> None: ...
    def on_rsp_unsubscribe(self, rsp: SubRsp, request_id: int) -> None: ...
    def on_rsp_subscribe_all(self, rsp: SubAllRsp, request_id: int) -> None: ...
    def on_rsp_unsubscribe_all(self, rsp: SubAllRsp, request_id: int) -> None: ...
    def on_rsp_query_sources(self, sources: List[SourceDirEntry], request_id: int) -> None: ...
    def on_depth_market_data(self, quote: Quote, envelope: RecordEnvelope) -> None: ...
    def on_transaction(self, transaction, envelope: RecordEnvelope) -> None: ...
    def on_entrust(self, entrust, envelope: RecordEnvelope) -> None: ...
    def on_tick(self, tick, envelope: RecordEnvelope) -> None: ...
    def on_depth(self, depth, envelope: RecordEnvelope) -> None: ...
    def on_sequence_gap(self, gap: SequenceGap) -> None: ...
    def on_stream_status(self, status: StreamStatus) -> None: ...
    def on_heartbeat(self) -> None: ...


_RECORD_CALLBACK = {
    RecordTag.QUOTE: "on_depth_market_data",
    RecordTag.TRANSACTION: "on_transaction",
    RecordTag.ENTRUST: "on_entrust",
    RecordTag.TICK: "on_tick",
    RecordTag.DEPTH: "on_depth",
}


def libfinance_ticket() -> dict:
    """向 libfinance 服务端 取一张行情票据（不登录按 IP 额度）。返回 {token, expires_at, grant, gateways}。"""
    from libfinance.client import get_client
    return get_client().call("issue_quote_ticket", {})


def _split(order_book_ids: Union[str, List[str]]) -> List[Tuple[str, str]]:
    """一个或多个 order_book_id -> [(exchange_id, instrument_id)]；全部合法才返回，不发半截订阅。"""
    codes = [order_book_ids] if isinstance(order_book_ids, str) else list(order_book_ids)
    if not codes:
        raise ValueError("order_book_ids: at least one order book id expected")
    return [split_order_book_id(code) for code in dict.fromkeys(codes)]


def _parse_addresses(addresses: str) -> List[Tuple[str, int]]:
    out = []
    for item in (addresses or "").split(","):
        item = item.strip()
        if not item:
            continue
        host, _, port = item.rpartition(":")
        out.append((host or item, int(port) if port.isdigit() else 9001))
    return out


class QuoteApi:
    def __init__(self, auto_reconnect: bool = True, client_id: str = "libfinance"):
        self._spi: Optional[QuoteSpi] = None
        self._client_id = client_id
        self._auto_reconnect = auto_reconnect

        self._endpoints: List[Tuple[str, int]] = []
        self._current = 0
        self._sock: Optional[socket.socket] = None
        self._send_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._stopping = threading.Event()
        self._connected = threading.Event()
        self._supervisor: Optional[threading.Thread] = None
        self._heartbeat: Optional[threading.Thread] = None
        self._last_received = 0.0
        self._last_sent = 0.0
        self._seq = 1

        # 登录状态（持 _state_lock）
        self._provider: Optional[TokenProvider] = None
        self._token = ""
        self._login_sent = False
        self._login_retried = False
        self._login_blocked = False   # 不可重试的登录失败 / 服务端拒绝签发票据：重连后不再自动登录

        # 续传与缺口检测（只在读线程上访问，unsubscribe 清基线时持锁）
        self._seq_lock = threading.Lock()
        self._epoch = 0
        self._last_seq_by_stream: Dict[int, int] = {}
        self._baselines: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (instrument_key, tag) -> (stream, inst_seq)

    def register_spi(self, spi: QuoteSpi) -> None:
        self._spi = spi

    # ── 连接 ──────────────────────────────────────────────────────
    def connect(self, addresses: Optional[str] = None, port: Optional[int] = None, timeout: float = 3.0) -> int:
        """连接行情网关，返回 0 = 已连上，-1 = 暂时没连上（后台持续重连），-2 = 没有网关地址（不会重试）。

        addresses 可以是 "host:port,host:port"，也可以 connect(host, port)；都不给时用 libfinance 服务端
        签发票据时返回的网关地址。没有 login 过则自动改用 libfinance 服务端 的票据。
        """
        with self._state_lock:
            if self._provider is None:
                self._provider = self._libfinance_provider
                self._login_blocked = False
        if addresses and port is not None:
            addresses = f"{addresses}:{port}"
        if not addresses:
            addresses = self._refresh_token(want_gateways=True)
        self._endpoints = _parse_addresses(addresses or "")
        if not self._endpoints:
            print("[QuoteApi] no gateway address (pass connect(\"host:port\") or configure live_quote.gateways)")
            return -2
        self._stopping.clear()
        if self._supervisor is None or not self._supervisor.is_alive():
            self._supervisor = threading.Thread(target=self._supervise, name="md-supervisor", daemon=True)
            self._heartbeat = threading.Thread(target=self._keep_alive, name="md-heartbeat", daemon=True)
            self._supervisor.start()
            self._heartbeat.start()
        return 0 if self._connected.wait(timeout) else -1

    # ── 登录（可选）──────────────────────────────────────────────────
    def login(self, token: Union[str, TokenProvider, None] = None) -> int:
        """自己提供票据：固定字符串，或 provider()（首次登录、重连、到期续期时调用）。

        不调用时 SDK 自动向 libfinance 服务端 取票据（不登录按 IP 额度）。
        """
        if token is None:
            provider = self._libfinance_provider
        elif callable(token):
            provider = token
        else:
            fixed = str(token)
            provider = lambda: fixed  # noqa: E731
        with self._state_lock:
            changed = provider is not self._provider
            self._provider = provider
            self._login_blocked = False
            if changed:
                self._login_sent = False
        self._refresh_token()
        return self._send_login()

    # ── 逐合约订阅 ────────────────────────────────────────────────
    # order_book_ids：一个或多个统一代码（600519.XSHG），可混合交易所；每只一条回执（on_rsp_subscribe）。
    # source 为空 = 无源订阅（网关按健康+优先级选源，源掉线自动灾备切换）；
    # source 非空 = 定向订阅（只推该源数据，不自动切源）。
    def subscribe(self, order_book_ids: Union[str, List[str]], *, source: str = "") -> int:
        """订阅；返回最后一条请求的序号（0 = 断线间隙，重连后在 on_rsp_login 里重放）。"""
        last = 0
        for exchange_id, code in _split(order_book_ids):
            last = self._send(MsgType.REQ_SUBSCRIBE, pack_sub_req(exchange_id, code, source))
        return last

    def unsubscribe(self, order_book_ids: Union[str, List[str]], *, source: str = "") -> int:
        last = 0
        for exchange_id, code in _split(order_book_ids):
            self._forget_baseline(instrument_hash(exchange_id, code))
            last = self._send(MsgType.REQ_UNSUBSCRIBE, pack_sub_req(exchange_id, code, source))
        return last

    # ── 整市场订阅 ────────────────────────────────────────────────
    # 一次订下「市场 × 品种 × 数据类型」命中的全部合约，任一维度取 All 表示不限。
    # 需要票据授予整市场订阅（否则 error_id=8）。
    def subscribe_all(self,
                      market: int = MarketType.All,
                      instrument_type: int = SubscribeInstrumentType.All,
                      data_type: int = SubscribeDataType.All) -> int:
        return self._send(MsgType.REQ_SUBSCRIBE_ALL,
                          pack_sub_all_req(market, instrument_type, data_type))

    def unsubscribe_all(self) -> int:
        """撤销本连接的全部整市场订阅（逐合约订阅不受影响）。"""
        with self._seq_lock:
            self._baselines.clear()
        return self._send(MsgType.REQ_UNSUBSCRIBE_ALL)

    # ── 发现 ──────────────────────────────────────────────────────
    def query_sources(self) -> int:
        """查询源目录：哪些源、各覆盖什么、是否健康。应答经 on_rsp_query_sources 返回。"""
        return self._send(MsgType.QUERY_SOURCES)

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    # ── 断开 ──────────────────────────────────────────────────────
    def disconnect(self) -> None:
        self._stopping.set()
        self._close_socket()
        for t in (self._supervisor, self._heartbeat):
            if t and t.is_alive() and t is not threading.current_thread():
                t.join(timeout=2.0)

    # ── 内部：票据 ────────────────────────────────────────────────
    def _libfinance_provider(self) -> str:
        return self._libfinance_ticket()[0]

    def _libfinance_ticket(self) -> Tuple[str, str]:
        ticket = libfinance_ticket()
        return ticket["token"], ticket.get("gateways", "")

    def _refresh_token(self, want_gateways: bool = False) -> str:
        """向 provider 取一张票据缓存起来（不持锁调用 provider）。返回 libfinance 服务端 给出的网关地址。"""
        with self._state_lock:
            provider = self._provider
        if provider is None:
            return ""
        gateways = ""
        try:
            if provider == self._libfinance_provider:
                token, gateways = self._libfinance_ticket()
            else:
                token = provider()
        except Exception as e:   # noqa: BLE001 —— 取不到票据不该打断读线程
            if getattr(e, "kind", None) == "PermissionError":
                # 服务端明确拒绝给这个调用方签票据（被封禁 / 等级不够）：不再自动重试，等用户再次 login / connect
                with self._state_lock:
                    self._login_blocked = True
                print(f"[QuoteApi] quote tickets refused for this caller: {e}")
            else:   # 暂时取不到（服务不可达等）：这次不登录，下次重连再取
                print(f"[QuoteApi] cannot obtain a quote ticket: {e}")
            return ""
        if len(token.encode()) > MAX_TOKEN_BYTES:
            print("[QuoteApi] ticket too long, ignored")
            return gateways
        with self._state_lock:
            self._token = token
        return gateways

    def _send_login(self) -> int:
        with self._state_lock:
            if self._provider is None or self._login_blocked or self._login_sent or not self._connected.is_set():
                return 0
            if not self._token:   # 没有可用票据（被吊销后还没换到新的）：不拿空票据去登录
                return 0
            self._login_sent = True
            token = self._token
        return self._send(MsgType.REQ_LOGIN, pack_login_req(token, self._client_id))

    # ── 内部：连接管理 ────────────────────────────────────────────
    def _supervise(self) -> None:
        backoff = 0.2
        failures = 0
        while not self._stopping.is_set():
            host, port = self._endpoints[self._current % len(self._endpoints)]
            if not self._open_socket(host, port):
                self._current += 1
                failures += 1
                if failures >= len(self._endpoints):   # 整轮都连不上才退避
                    failures = 0
                    self._stopping.wait(backoff)
                    backoff = min(backoff * 2, 1.0 if len(self._endpoints) > 1 else 5.0)
                continue
            failures = 0
            connected_at = time.monotonic()
            with self._state_lock:
                self._login_sent = False
                self._login_retried = False
                blocked = self._login_blocked
            spi = self._spi
            if spi:
                self._safe(spi.on_connected)
            if not blocked:
                self._refresh_token()
                self._send_login()
            self._read_loop()
            self._close_socket()
            if self._stopping.is_set():
                return
            if spi:
                self._safe(spi.on_disconnected, 0)
            if not self._auto_reconnect:
                return
            if time.monotonic() - connected_at >= 10:
                backoff = 0.2
            if len(self._endpoints) > 1:
                self._current += 1                      # 有备选地址：立即切过去
            else:
                self._stopping.wait(backoff)
                backoff = min(backoff * 2, 5.0)

    def _open_socket(self, host: str, port: int) -> bool:
        try:
            sock = socket.create_connection((host, port), timeout=3.0)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(1.0)
        except OSError:
            return False
        self._sock = sock
        self._last_received = self._last_sent = time.monotonic()
        self._connected.set()
        return True

    def _close_socket(self) -> None:
        self._connected.clear()
        sock, self._sock = self._sock, None
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()

    def _keep_alive(self) -> None:
        while not self._stopping.wait(1.0):
            if not self._connected.is_set():
                continue
            now = time.monotonic()
            if now - self._last_received > HEARTBEAT_TIMEOUT:
                print(f"[QuoteApi] no frame from the gateway for {HEARTBEAT_TIMEOUT:.0f}s, reconnecting")
                self._close_socket()          # 读循环随之退出，监督线程重连
            elif now - self._last_sent >= HEARTBEAT_INTERVAL:
                self._send(MsgType.HEARTBEAT)

    def _next_seq(self) -> int:
        with self._state_lock:
            s = self._seq
            self._seq += 1
            return s

    def _send(self, msg_type: int, body: bytes = b"") -> int:
        seq = self._next_seq()
        sock = self._sock
        if sock is None:
            return 0          # 断线间隙静默丢弃；重连后由 on_rsp_login 重放订阅
        try:
            with self._send_lock:
                sock.sendall(make_frame(msg_type, seq, body))
            self._last_sent = time.monotonic()
        except OSError:
            return 0
        return seq

    # ── 内部：收帧 ────────────────────────────────────────────────
    def _recv_exact(self, n: int) -> Optional[bytes]:
        buf = bytearray()
        while len(buf) < n:
            sock = self._sock
            if sock is None or self._stopping.is_set():
                return None
            try:
                chunk = sock.recv(n - len(buf))
            except socket.timeout:
                continue
            except OSError:
                return None
            if not chunk:
                return None
            buf.extend(chunk)
        return bytes(buf)

    def _read_loop(self) -> None:
        while not self._stopping.is_set():
            hdr = self._recv_exact(HEADER_SIZE)
            if hdr is None:
                return
            magic, ver, msg_type, seq_no, body_len = unpack_header(hdr)
            if magic != MAGIC or ver != VERSION or body_len > MAX_BODY_LEN:
                print(f"[QuoteApi] bad frame: magic=0x{magic:08X} version={ver} body_len={body_len}")
                return
            body = b""
            if body_len:
                body = self._recv_exact(body_len)
                if body is None:
                    return
            self._last_received = time.monotonic()
            self._dispatch(msg_type, seq_no, body)

    @staticmethod
    def _safe(fn, *args) -> None:
        """回调异常只打印，不中断读线程。"""
        try:
            fn(*args)
        except Exception as e:   # noqa: BLE001
            print(f"[QuoteApi] callback {getattr(fn, '__name__', fn)} raised {e!r}")

    def _dispatch(self, msg_type: int, seq_no: int, body: bytes) -> None:
        spi = self._spi
        if msg_type == MsgType.RECORD_BATCH:
            if spi:
                self._dispatch_batch(body, spi)
        elif msg_type == MsgType.RSP_LOGIN:
            self._on_login(unpack_login_rsp(body), seq_no, spi)
        elif msg_type == MsgType.RSP_REAUTH:
            if spi:
                self._safe(spi.on_rsp_reauth, unpack_login_rsp(body))
        elif msg_type == MsgType.NOTIFY_SESSION_EXPIRING:
            self._refresh_token()                      # 换一张新票据续期，订阅不中断
            with self._state_lock:
                token = self._token
            self._send(MsgType.REQ_REAUTH, pack_reauth_req(token))
        elif msg_type == MsgType.NOTIFY_SESSION_CLOSED:
            notice = unpack_session_closed(body)
            if notice.reason == SessionCloseReason.REVOKED:
                # 票据被吊销（封禁，或调整额度后让客户端换票据）：丢掉这张票据，网关随后断开，重连时取新票据
                # 再登录、在 on_rsp_login 里重放订阅。被封禁的调用方取票据时会被服务端拒绝（PermissionError），
                # 到那里才停止自动重连；自己 login 的固定票据会被网关以"已吊销"拒绝登录，同样停止。
                with self._state_lock:
                    self._token = ""
            if spi:
                self._safe(spi.on_session_closed, notice)
        elif not spi:
            return
        elif msg_type == MsgType.RSP_SUBSCRIBE:
            self._safe(spi.on_rsp_subscribe, unpack_sub_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_UNSUBSCRIBE:
            rsp = unpack_sub_rsp(body)
            if rsp.error_id == ErrorCode.GRANT_SHRUNK:   # 网关撤销的订阅：该合约不再有后续记录
                self._forget_baseline(instrument_hash(rsp.exchange_id, rsp.instrument_id))
            self._safe(spi.on_rsp_unsubscribe, rsp, seq_no)
        elif msg_type == MsgType.RSP_SUBSCRIBE_ALL:
            self._safe(spi.on_rsp_subscribe_all, unpack_sub_all_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_UNSUBSCRIBE_ALL:
            self._safe(spi.on_rsp_unsubscribe_all, unpack_sub_all_rsp(body), seq_no)
        elif msg_type == MsgType.RSP_QUERY_SOURCES:
            self._safe(spi.on_rsp_query_sources, unpack_source_dir_list(body), seq_no)
        elif msg_type == MsgType.STREAM_STATUS:
            self._safe(spi.on_stream_status, unpack_stream_status(body))
        elif msg_type == MsgType.HEARTBEAT:
            self._safe(spi.on_heartbeat)
        # 其余帧（更新的网关可能新增）静默跳过而非断连

    def _on_login(self, rsp: LoginRsp, seq_no: int, spi: Optional[QuoteSpi]) -> None:
        if rsp.error_id != ErrorCode.OK:
            retry = False
            with self._state_lock:
                if rsp.error_id in (ErrorCode.TOKEN_EXPIRED, ErrorCode.TOKEN_UNKNOWN_KEY) and not self._login_retried:
                    self._login_retried = True
                    self._login_sent = False
                    retry = True
                elif rsp.error_id != ErrorCode.ALREADY_AUTHENTICATED:
                    self._login_blocked = True        # 不自动重试：等用户再次 login / connect
            if retry:
                self._refresh_token()
                self._send_login()
                return
        resuming = False
        if rsp.error_id == ErrorCode.OK:
            with self._seq_lock:
                if self._epoch != rsp.sequence_epoch_ns:  # 网关日志重建：续传位置与基线作废
                    self._epoch = rsp.sequence_epoch_ns
                    self._last_seq_by_stream.clear()
                    self._baselines.clear()
                positions = dict(self._last_seq_by_stream)
            if positions:
                self._send(MsgType.REQ_RESUME, pack_resume_positions(positions))
                resuming = True
        if spi:
            self._safe(spi.on_rsp_login, rsp, seq_no)     # 用户在这里重新订阅
        if resuming:
            self._send(MsgType.REQ_RESUME_START)

    def _forget_baseline(self, instrument_key: int) -> None:
        with self._seq_lock:
            for k in [k for k in self._baselines if k[0] == instrument_key]:
                del self._baselines[k]

    def _dispatch_batch(self, body: bytes, spi: QuoteSpi) -> None:
        for env, pod in iter_batch(body):
            unpacker = RECORD_UNPACKERS.get(env.tag)
            if unpacker is None or len(pod) < unpacker[1]:
                continue                                 # 未知数据类型：更新的网关可能新增了 schema
            record = unpacker[0](pod)
            gap = self._check_sequence(env, record)
            if gap is not None:
                self._safe(spi.on_sequence_gap, gap)
            self._safe(getattr(spi, _RECORD_CALLBACK[env.tag]), record, env)

    def _check_sequence(self, env: RecordEnvelope, record) -> Optional[SequenceGap]:
        with self._seq_lock:
            if not env.snapshot:   # 快照不代表已收到它之前的全部记录，不推进续传位置
                if env.seq > self._last_seq_by_stream.get(env.stream_id, 0):
                    self._last_seq_by_stream[env.stream_id] = env.seq
            key = (env.instrument_key, env.tag)
            previous = self._baselines.get(key)
            self._baselines[key] = (env.stream_id, env.inst_seq)
            if previous is None or env.snapshot:
                return None
            stream_id, last = previous
            if stream_id == env.stream_id and env.inst_seq > last + 1:
                return SequenceGap(env.stream_id, env.tag, record.exchange_id, record.instrument_id,
                                   last + 1, env.inst_seq)
            return None
