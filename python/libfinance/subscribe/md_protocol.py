"""
md_protocol.py — dynamics 行情分发系统的二进制帧协议（纯 Python 实现，协议 v3）

libfinance 的订阅模块是 dynamics 的独立客户端，只依赖标准库，不依赖 libdynamics。
本文件严格对齐服务端 `#pragma pack(1)` 的结构体布局（dynamics/framework/core/src/include/dynamics/proto）。

帧 = FrameHeader(16B) + body：
  - 控制帧：msg_type ∈ 0xF0xx，body 为下面定义的结构体；
  - 数据帧：只有 RECORD_BATCH 一种：RecordBatchHeader + N × (RecordEnvelope + 行情 POD + 8 字节对齐填充)。
    RecordEnvelope 是网关的定序信封（stream / seq / inst_seq / 时间戳），续传与缺口检测都靠它。

v3（相对 v1）：登录只接受 PDP（libfinance 服务端）签发的票据；数据只走批量帧；心跳双向强制
（5 s 一帧，15 s 没收到对端任何帧即判定连接失效）；断线后按 seq 续传。

每个结构体都带 `assert struct.calcsize(...) == <服务端 sizeof>`，一旦服务端改了线格式，
import 时立刻报错，而不是解包出乱码才发现。
"""

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Iterator, List, Tuple

# ── 常量 ──────────────────────────────────────────────────────────
MAGIC = 0x44594E31   # "DYN1"
VERSION = 3
HEADER_SIZE = 16
MAX_BODY_LEN = 16 * 1024 * 1024   # 与服务端一致：拒绝异常帧诱导的超大分配
HEARTBEAT_INTERVAL = 5.0          # 秒：至少这么久发一帧
HEARTBEAT_TIMEOUT = 15.0          # 秒：这么久没收到对端任何帧即判定连接失效

SOURCE_LEN = 16
EXCHANGE_ID_LEN = 16
INSTRUMENT_ID_LEN = 32
TRADING_PHASE_CODE_LEN = 8
MAX_TOKEN_BYTES = 2048

RECORD_SNAPSHOT = 1   # RecordEnvelope.flags：订阅时补发的最新值（不是新发生的事件）


# ── 消息类型 ──────────────────────────────────────────────────────
class MsgType(IntEnum):
    REQ_LOGIN               = 0xF001
    RSP_LOGIN               = 0xF002
    REQ_SUBSCRIBE           = 0xF003
    RSP_SUBSCRIBE           = 0xF004
    REQ_UNSUBSCRIBE         = 0xF005
    RSP_UNSUBSCRIBE         = 0xF006
    REQ_SUBSCRIBE_ALL       = 0xF007
    RSP_SUBSCRIBE_ALL       = 0xF008
    QUERY_SOURCES           = 0xF012
    RSP_QUERY_SOURCES       = 0xF013
    REQ_UNSUBSCRIBE_ALL     = 0xF014
    RSP_UNSUBSCRIBE_ALL     = 0xF015
    RECORD_BATCH            = 0xF020
    STREAM_STATUS           = 0xF021
    REQ_RESUME              = 0xF022
    REQ_RESUME_START        = 0xF023
    REQ_REAUTH              = 0xF030
    RSP_REAUTH              = 0xF031
    NOTIFY_SESSION_EXPIRING = 0xF032
    NOTIFY_SESSION_CLOSED   = 0xF033
    HEARTBEAT               = 0xF0FF


class RecordTag(IntEnum):
    QUOTE       = 401
    ENTRUST     = 402
    TRANSACTION = 403
    DEPTH       = 405
    TICK        = 406


class ErrorCode(IntEnum):
    """应答 error_id（dynamics proto/errors.h）。"""
    OK = 0
    MALFORMED = 1
    NOT_AUTHENTICATED = 3
    NO_SOURCE = 4                 # 无健康源 / 无可承接整市场的源
    SOURCE_UNAVAILABLE = 5        # 指定源不可用或路由冲突
    SUBSCRIPTION_LIMIT = 6        # 订阅数达到票据上限
    MARKET_NOT_GRANTED = 7        # 市场不在票据授权内
    WHOLE_MARKET_NOT_GRANTED = 8  # 票据没有整市场订阅授权
    GRANT_SHRUNK = 9              # 续期后授权收缩，该订阅被网关撤销
    TOKEN_INVALID = 20
    TOKEN_EXPIRED = 21
    TOKEN_UNKNOWN_KEY = 22
    TOKEN_REVOKED = 23
    TOO_MANY_CONNECTIONS = 24
    SUBJECT_MISMATCH = 25
    ALREADY_AUTHENTICATED = 26


class SessionCloseReason(IntEnum):
    EXPIRED = 1
    REVOKED = 2


# ── 订阅枚举（取值照抄服务端 schema/enums.h）────────────────────────
class MarketType(IntEnum):
    All = 0
    BSE = 1
    SHFE = 2
    CFFEX = 3
    DCE = 4
    CZCE = 5
    INE = 6
    SSE = 7      # 上交所 → XSHG
    SZE = 8      # 深交所 → XSHE


class SubscribeInstrumentType(IntEnum):
    All = 0x00           # 不限品种
    Stock = 0x01
    Future = 0x02
    Bond = 0x04
    StockOption = 0x08
    FutureOption = 0x10
    Fund = 0x20
    Index = 0x40
    HKT = 0x80


class SubscribeDataType(IntEnum):
    All = 0x00           # 不限数据类型
    Snapshot = 0x01
    Entrust = 0x02
    Transaction = 0x04
    Tree = 0x08
    Tick = 0x16
    Depth = 0x32


class InstrumentType(IntEnum):
    """行情记录里的 instrument_type 字段（服务端按 交易所+代码 推导）。"""
    Unknown = 0
    Stock = 1
    StockOption = 2
    TechStock = 3        # 科创板，订阅过滤时归入 Stock 品种位
    Future = 4
    Bond = 5
    Fund = 6
    Index = 7
    Repo = 8
    Crypto = 9
    CryptoFuture = 10
    CryptoUFuture = 11


# 交易所标识：全系统统一 rqdata 风格（order_book_id 后缀）。
EXCHANGE_OF_MARKET = {
    MarketType.SSE: "XSHG",
    MarketType.SZE: "XSHE",
    MarketType.BSE: "XBSE",
    MarketType.SHFE: "XSGE",
    MarketType.CFFEX: "CCFX",
    MarketType.DCE: "XDCE",
    MarketType.CZCE: "XZCE",
    MarketType.INE: "XINE",
}


#: 网关承接的交易所（order_book_id 后缀）。
EXCHANGES = frozenset(EXCHANGE_OF_MARKET.values())


def split_order_book_id(order_book_id: str) -> Tuple[str, str]:
    """``600519.XSHG`` -> (``XSHG``, ``600519``)：线上的 (exchange_id, instrument_id)。

    与 libfinance 其余函数同一种代码；后缀必须是网关承接的交易所（EXCHANGES）。"""
    if not isinstance(order_book_id, str):
        raise TypeError("order_book_id must be a string, got {!r}".format(order_book_id))
    code, dot, exchange = order_book_id.rpartition(".")
    if not dot or not code or not exchange:
        raise ValueError("{!r} is not <code>.<exchange>, e.g. 600519.XSHG".format(order_book_id))
    if exchange not in EXCHANGES:
        raise ValueError("{!r}: the quote gateway serves {} only".format(order_book_id, sorted(EXCHANGES)))
    if len(code.encode()) >= INSTRUMENT_ID_LEN:
        raise ValueError("{!r}: the code is longer than the gateway takes".format(order_book_id))
    return exchange, code


class _Coded:
    """行情记录、回执与缺口通知共有的 order_book_id（由 instrument_id 与 exchange_id 拼成）。"""

    @property
    def order_book_id(self) -> str:
        """rqdata 风格标识，如 600519.XSHG。"""
        return "{}.{}".format(self.instrument_id, self.exchange_id) if self.instrument_id else ""


def instrument_hash(exchange_id: str, instrument_id: str) -> int:
    """与服务端 instrument_hash 一致（FNV-1a 64，交易所与代码之间以 0x1f 分隔）= RecordEnvelope.instrument_key。"""
    h = 14695981039346656037
    for b in exchange_id.encode() + b"\x1f" + instrument_id.encode():
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return h


# ── FrameHeader (16 bytes) ────────────────────────────────────────
# uint32 magic, uint16 version, uint16 msg_type, uint32 seq_no, uint32 body_len
HEADER_FMT = "<IHHII"
assert struct.calcsize(HEADER_FMT) == HEADER_SIZE


def pack_header(msg_type: int, seq_no: int, body_len: int) -> bytes:
    return struct.pack(HEADER_FMT, MAGIC, VERSION, msg_type, seq_no, body_len)


def unpack_header(data: bytes):
    magic, ver, msg_type, seq_no, body_len = struct.unpack(HEADER_FMT, data)
    return magic, ver, msg_type, seq_no, body_len


def _s(raw: bytes) -> str:
    """定长 char 数组 → str（遇 '\\0' 截断）。"""
    return raw.split(b"\x00", 1)[0].decode(errors="replace")


def _fix(text: str, n: int) -> bytes:
    """str → 定长 char 数组（截断 + 零填充）。"""
    return text.encode()[: n - 1].ljust(n, b"\x00")


# ── 登录 / 续期 ────────────────────────────────────────────────────
# REQ_LOGIN: LoginRequest{char client_id[32]; u32 token_len; u32 _pad} + token
LOGIN_REQ_FMT = "<32sII"
assert struct.calcsize(LOGIN_REQ_FMT) == 40
# REQ_REAUTH: TokenHeader{u32 token_len; u32 _pad} + token
TOKEN_HEADER_FMT = "<II"
assert struct.calcsize(TOKEN_HEADER_FMT) == 8


def pack_login_req(token: str, client_id: str = "libfinance") -> bytes:
    raw = token.encode()
    return struct.pack(LOGIN_REQ_FMT, _fix(client_id, 32), len(raw), 0) + raw


def pack_reauth_req(token: str) -> bytes:
    raw = token.encode()
    return struct.pack(TOKEN_HEADER_FMT, len(raw), 0) + raw


LOGIN_RSP_FMT = "<i64sQqiiiB3xQq"
LOGIN_RSP_SIZE = struct.calcsize(LOGIN_RSP_FMT)
assert LOGIN_RSP_SIZE == 116


@dataclass
class LoginRsp:
    """RSP_LOGIN / RSP_REAUTH。回显票据里的授权（资源数字），不含任何等级语义。"""
    error_id: int
    error_msg: str
    session_id: int
    expires_at_ms: int        # 票据到期时刻（SDK 到期前自动续期）
    max_subscriptions: int    # -1 = 不限
    max_conns: int
    max_msgs_per_sec: int
    sub_all: bool             # 能否整市场订阅
    market_mask: int          # bit(MarketType)
    sequence_epoch_ns: int    # 序号纪元：变化说明网关日志重建，续传位置作废


def unpack_login_rsp(data: bytes) -> LoginRsp:
    f = struct.unpack(LOGIN_RSP_FMT, data[:LOGIN_RSP_SIZE])
    return LoginRsp(f[0], _s(f[1]), f[2], f[3], f[4], f[5], f[6], bool(f[7]), f[8], f[9])


SESSION_EXPIRING_FMT = "<q"
SESSION_CLOSED_FMT = "<i64s"
assert struct.calcsize(SESSION_CLOSED_FMT) == 68


@dataclass
class SessionClosed:
    reason: int      # SessionCloseReason
    message: str


def unpack_session_closed(data: bytes) -> SessionClosed:
    reason, msg = struct.unpack(SESSION_CLOSED_FMT, data[:68])
    return SessionClosed(reason, _s(msg))


# ── SubReq / SubRsp ───────────────────────────────────────────────
# source 为空 = 无源订阅（网关按健康+优先级自动选源，支持灾备重路由）；
# source 非空 = 定向订阅（只推该源数据，不自动切源）。
SUB_REQ_FMT = "<16s16s32s"
SUB_REQ_SIZE = struct.calcsize(SUB_REQ_FMT)
assert SUB_REQ_SIZE == 64

SUB_RSP_FMT = "<16s16s32si64sii"
SUB_RSP_SIZE = struct.calcsize(SUB_RSP_FMT)
assert SUB_RSP_SIZE == 140


def pack_sub_req(exchange_id: str, instrument_id: str, source: str = "") -> bytes:
    return struct.pack(
        SUB_REQ_FMT,
        _fix(source, SOURCE_LEN),
        _fix(exchange_id, EXCHANGE_ID_LEN),
        _fix(instrument_id, INSTRUMENT_ID_LEN),
    )


@dataclass
class SubRsp(_Coded):
    source: str          # 回显：无源订阅时是网关实际选中的源
    exchange_id: str
    instrument_id: str
    error_id: int        # ErrorCode
    error_msg: str
    current_subs: int
    max_subs: int


def unpack_sub_rsp(data: bytes) -> SubRsp:
    src, exch, inst, err, msg, cur, mx = struct.unpack(SUB_RSP_FMT, data[:SUB_RSP_SIZE])
    return SubRsp(_s(src), _s(exch), _s(inst), err, _s(msg), cur, mx)


# ── SubAllReq / SubAllRsp（整市场订阅）─────────────────────────────
SUB_ALL_REQ_FMT = "<b7xQQ"
SUB_ALL_REQ_SIZE = struct.calcsize(SUB_ALL_REQ_FMT)
assert SUB_ALL_REQ_SIZE == 24

SUB_ALL_RSP_FMT = "<16si64s"
SUB_ALL_RSP_SIZE = struct.calcsize(SUB_ALL_RSP_FMT)
assert SUB_ALL_RSP_SIZE == 84


def pack_sub_all_req(market: int = MarketType.All,
                     instrument_type: int = SubscribeInstrumentType.All,
                     data_type: int = SubscribeDataType.All) -> bytes:
    return struct.pack(SUB_ALL_REQ_FMT, int(market), int(instrument_type), int(data_type))


@dataclass
class SubAllRsp:
    source: str          # 承接整市场推送的源（失败或退订回执为空）
    error_id: int        # 4=无可承接的源 7=市场不在授权内 8=票据没有整市场授权 9=续期后授权收缩被撤销
    error_msg: str


def unpack_sub_all_rsp(data: bytes) -> SubAllRsp:
    src, err, msg = struct.unpack(SUB_ALL_RSP_FMT, data[:SUB_ALL_RSP_SIZE])
    return SubAllRsp(_s(src), err, _s(msg))


# ── SourceDirEntry（QuerySources 应答）──────────────────────────────
SOURCE_DIR_FMT = "<16siBBBxQQQ"
SOURCE_DIR_SIZE = struct.calcsize(SOURCE_DIR_FMT)
assert SOURCE_DIR_SIZE == 48


@dataclass
class SourceDirEntry:
    source: str
    priority: int          # 值大者优先
    whole_market: bool     # 能否承接整市场推送
    health: bool           # True=ready 可选中
    directed_only: bool    # True=仅定向可选，不参与自动选源/灾备
    market_mask: int       # 0 = 不限该维度
    instrument_mask: int
    data_type_mask: int


def unpack_source_dir_list(body: bytes) -> List[SourceDirEntry]:
    """RSP_QUERY_SOURCES body = uint32 count + count × SourceDirEntry。"""
    if len(body) < 4:
        return []
    (count,) = struct.unpack_from("<I", body, 0)
    need = 4 + count * SOURCE_DIR_SIZE
    if len(body) < need:
        return []   # 帧不完整，丢弃
    out = []
    for i in range(count):
        src, pri, whole, health, directed, mm, im, dm = struct.unpack_from(
            SOURCE_DIR_FMT, body, 4 + i * SOURCE_DIR_SIZE)
        out.append(SourceDirEntry(_s(src), pri, bool(whole), bool(health),
                                  bool(directed), mm, im, dm))
    return out


# ── 流状态 / 续传 ──────────────────────────────────────────────────
STREAM_STATUS_FMT = "<IB3x16sq"
assert struct.calcsize(STREAM_STATUS_FMT) == 32


@dataclass
class StreamStatus:
    stream_id: int
    stale: bool              # True = 该源在交易时段内陈旧（没有新数据）
    source: str
    last_received_ns: int


def unpack_stream_status(data: bytes) -> StreamStatus:
    sid, fresh, src, last = struct.unpack(STREAM_STATUS_FMT, data[:32])
    return StreamStatus(sid, fresh == 1, _s(src), last)


RESUME_POSITION_FMT = "<IIQ"
assert struct.calcsize(RESUME_POSITION_FMT) == 16


def pack_resume_positions(positions: dict) -> bytes:
    """REQ_RESUME body = uint32 count + count × ResumePosition{u32 stream_id; u32 _pad; u64 last_seq}。"""
    body = struct.pack("<I", len(positions))
    for stream_id, seq in positions.items():
        body += struct.pack(RESUME_POSITION_FMT, stream_id, 0, seq)
    return body


# ── 批量帧与定序信封 ────────────────────────────────────────────────
ENVELOPE_FMT = "<IHHIIQQQqq"
ENVELOPE_SIZE = struct.calcsize(ENVELOPE_FMT)
assert ENVELOPE_SIZE == 56
BATCH_HEADER_FMT = "<II"


@dataclass
class RecordEnvelope:
    """网关定序信封：每条行情都带着它。"""
    stream_id: int        # 每个源一个 stream
    tag: int              # RecordTag
    flags: int
    seq: int              # stream 内连续序号（续传位置）
    inst_seq: int         # (stream, 合约, 数据类型) 内连续序号（缺口检测）
    instrument_key: int   # = instrument_hash(交易所, 代码)
    received_ns: int      # 网关收到的时刻（CLOCK_REALTIME ns）
    sequenced_ns: int     # 定序并写入日志的时刻

    @property
    def snapshot(self) -> bool:
        """订阅时补发的最新值（或慢消费者合并后的当前值），不是新发生的事件。"""
        return bool(self.flags & RECORD_SNAPSHOT)


def iter_batch(body: bytes) -> Iterator[Tuple[RecordEnvelope, bytes]]:
    """RECORD_BATCH body → (信封, 行情 POD 字节)。格式错误时停止（不抛异常）。"""
    if len(body) < 8:
        return
    (count, _pad) = struct.unpack_from(BATCH_HEADER_FMT, body, 0)
    off = 8
    for _ in range(count):
        if len(body) - off < ENVELOPE_SIZE:
            return
        sid, tag, ln, flags, _r, seq, iseq, key, rns, sns = struct.unpack_from(ENVELOPE_FMT, body, off)
        entry = (ENVELOPE_SIZE + ln + 7) & ~7
        if len(body) - off < entry:
            return
        pod = body[off + ENVELOPE_SIZE: off + ENVELOPE_SIZE + ln]
        yield RecordEnvelope(sid, tag, flags, seq, iseq, key, rns, sns), pod
        off += entry


# ── Quote（tag 401，快照 + 10 档盘口）──────────────────────────────
QUOTE_FMT = (
    "<"
    "q"      # data_time
    "32s"    # instrument_id
    "16s"    # exchange_id
    "b"      # instrument_type (int8)
    "17d"    # pre_close, pre_settlement, last, volume, turnover,
             # pre_open_interest, open_interest, open, high, low,
             # upper_limit, lower_limit, close, settlement, iopv,
             # total_bid_volume, total_ask_volume
    "q"      # total_trade_num
    "40d"    # bid_price[10] ask_price[10] bid_volume[10] ask_volume[10]
    "8s"     # trading_phase_code
)
QUOTE_SIZE = struct.calcsize(QUOTE_FMT)
assert QUOTE_SIZE == 529


@dataclass
class Quote(_Coded):
    data_time: int
    instrument_id: str
    exchange_id: str
    instrument_type: int
    pre_close_price: float
    pre_settlement_price: float
    last_price: float
    volume: float
    turnover: float
    pre_open_interest: float
    open_interest: float
    open_price: float
    high_price: float
    low_price: float
    upper_limit_price: float
    lower_limit_price: float
    close_price: float
    settlement_price: float
    iopv: float
    total_bid_volume: float
    total_ask_volume: float
    total_trade_num: int
    bid_price: List[float] = field(default_factory=list)    # [10]
    ask_price: List[float] = field(default_factory=list)    # [10]
    bid_volume: List[float] = field(default_factory=list)   # [10]
    ask_volume: List[float] = field(default_factory=list)   # [10]
    trading_phase_code: str = ""


def unpack_quote(data: bytes) -> Quote:
    f = struct.unpack(QUOTE_FMT, data[:QUOTE_SIZE])
    return Quote(
        data_time=f[0],
        instrument_id=_s(f[1]),
        exchange_id=_s(f[2]),
        instrument_type=f[3],
        pre_close_price=f[4],
        pre_settlement_price=f[5],
        last_price=f[6],
        volume=f[7],
        turnover=f[8],
        pre_open_interest=f[9],
        open_interest=f[10],
        open_price=f[11],
        high_price=f[12],
        low_price=f[13],
        upper_limit_price=f[14],
        lower_limit_price=f[15],
        close_price=f[16],
        settlement_price=f[17],
        iopv=f[18],
        total_bid_volume=f[19],
        total_ask_volume=f[20],
        total_trade_num=f[21],
        bid_price=list(f[22:32]),
        ask_price=list(f[32:42]),
        bid_volume=list(f[42:52]),
        ask_volume=list(f[52:62]),
        trading_phase_code=_s(f[62]),
    )


# ── 逐笔委托 / 逐笔成交 / 盘口 / 深度 ──────────────────────────────
ENTRUST_FMT = "<q32s16sbddbbqqqq"
assert struct.calcsize(ENTRUST_FMT) == 107
TRANSACTION_FMT = "<q32s16sbddqqbbqqq"
assert struct.calcsize(TRANSACTION_FMT) == 115
TICK_FMT = "<q32s16sbdddd"
assert struct.calcsize(TICK_FMT) == 89
DEPTH_FMT = "<q32s16sbddb"
assert struct.calcsize(DEPTH_FMT) == 74


@dataclass
class Entrust(_Coded):
    data_time: int
    instrument_id: str
    exchange_id: str
    instrument_type: int
    price: float
    volume: float
    side: int
    price_type: int
    main_seq: int
    seq: int
    orig_order_no: int
    biz_index: int


@dataclass
class Transaction(_Coded):
    data_time: int
    instrument_id: str
    exchange_id: str
    instrument_type: int
    price: float
    volume: float
    bid_no: int
    ask_no: int
    exec_type: int
    side: int
    main_seq: int
    seq: int
    biz_index: int


@dataclass
class Tick(_Coded):
    data_time: int
    instrument_id: str
    exchange_id: str
    instrument_type: int
    bid_price: float
    bid_volume: float
    ask_price: float
    ask_volume: float


@dataclass
class Depth(_Coded):
    data_time: int
    instrument_id: str
    exchange_id: str
    instrument_type: int
    price: float
    volume: float
    side: int


def _unpack(cls, fmt, data):
    f = list(struct.unpack(fmt, data[:struct.calcsize(fmt)]))
    f[1], f[2] = _s(f[1]), _s(f[2])
    return cls(*f)


def unpack_entrust(data: bytes) -> Entrust:
    return _unpack(Entrust, ENTRUST_FMT, data)


def unpack_transaction(data: bytes) -> Transaction:
    return _unpack(Transaction, TRANSACTION_FMT, data)


def unpack_tick(data: bytes) -> Tick:
    return _unpack(Tick, TICK_FMT, data)


def unpack_depth(data: bytes) -> Depth:
    return _unpack(Depth, DEPTH_FMT, data)


RECORD_UNPACKERS = {
    RecordTag.QUOTE: (unpack_quote, QUOTE_SIZE),
    RecordTag.ENTRUST: (unpack_entrust, 107),
    RecordTag.TRANSACTION: (unpack_transaction, 115),
    RecordTag.TICK: (unpack_tick, 89),
    RecordTag.DEPTH: (unpack_depth, 74),
}


# ── 帧构造辅助 ───────────────────────────────────────────────────
def make_frame(msg_type: int, seq_no: int, body: bytes = b"") -> bytes:
    return pack_header(msg_type, seq_no, len(body)) + body


def make_heartbeat(seq_no: int = 0) -> bytes:
    return make_frame(MsgType.HEARTBEAT, seq_no)
