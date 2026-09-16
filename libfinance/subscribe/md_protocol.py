"""
md_protocol.py — dynamics 行情分发系统的二进制帧协议（纯 Python 实现）

libfinance 的订阅模块是 dynamics 的独立客户端，只依赖标准库，不依赖 libdynamics。
本文件严格对齐服务端 `#pragma pack(1)` 的结构体布局。

帧 = FrameHeader(16B) + body：
  - 控制帧：msg_type ∈ MsgType 的 0xF0xx 段，body 为下面定义的结构体；
  - 数据帧：msg_type = 行情类型 tag（Quote=401 / Entrust=402 / ...），body 为对应 POD。

每个结构体都带 `assert struct.calcsize(...) == <服务端 sizeof>`，一旦服务端改了线格式
（历史上 SubAllRsp 就悄悄加过 source 字段），import 时立刻报错，而不是解包出乱码才发现。
"""

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import List

# ── 常量 ──────────────────────────────────────────────────────────
MAGIC = 0x44594E31   # "DYN1"
VERSION = 1
HEADER_SIZE = 16
MAX_BODY_LEN = 16 * 1024 * 1024   # 与服务端一致：拒绝异常帧诱导的超大分配

SOURCE_LEN = 16
EXCHANGE_ID_LEN = 16
INSTRUMENT_ID_LEN = 32
TRADING_PHASE_CODE_LEN = 8


# ── 消息类型 ──────────────────────────────────────────────────────
class MsgType(IntEnum):
    # 控制帧（高位段 0xF0xx，与行情 tag 互不冲突）
    REQ_LOGIN           = 0xF001
    RSP_LOGIN           = 0xF002
    REQ_SUBSCRIBE       = 0xF003
    RSP_SUBSCRIBE       = 0xF004
    REQ_UNSUBSCRIBE     = 0xF005
    RSP_UNSUBSCRIBE     = 0xF006
    REQ_SUBSCRIBE_ALL   = 0xF007
    RSP_SUBSCRIBE_ALL   = 0xF008
    QUERY_SOURCES       = 0xF012
    RSP_QUERY_SOURCES   = 0xF013
    REQ_UNSUBSCRIBE_ALL = 0xF014
    RSP_UNSUBSCRIBE_ALL = 0xF015
    HEARTBEAT           = 0xF0FF
    # 数据帧（msg_type = 行情类型 tag）
    QUOTE       = 401
    ENTRUST     = 402
    TRANSACTION = 403
    DEPTH       = 405
    TICK        = 406


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


# ── LoginReq / LoginRsp ───────────────────────────────────────────
LOGIN_REQ_FMT = "<16s32s32s"
LOGIN_REQ_SIZE = struct.calcsize(LOGIN_REQ_FMT)
assert LOGIN_REQ_SIZE == 80

LOGIN_RSP_FMT = "<i64sQb3xi"
LOGIN_RSP_SIZE = struct.calcsize(LOGIN_RSP_FMT)
assert LOGIN_RSP_SIZE == 84


def pack_login_req(user_id: str, password: str, client_id: str = "libfinance") -> bytes:
    return struct.pack(LOGIN_REQ_FMT, _fix(user_id, 16), _fix(password, 32), _fix(client_id, 32))


@dataclass
class LoginRsp:
    error_id: int
    error_msg: str
    session_id: int
    user_level: int
    max_subscriptions: int   # -1 表示无限制；整市场订阅要求此值为 -1


def unpack_login_rsp(data: bytes) -> LoginRsp:
    error_id, msg, session_id, level, max_subs = struct.unpack(LOGIN_RSP_FMT, data[:LOGIN_RSP_SIZE])
    return LoginRsp(error_id, _s(msg), session_id, level, max_subs)


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
class SubRsp:
    source: str          # 回显：无源订阅时是网关实际选中的源
    exchange_id: str
    instrument_id: str
    error_id: int        # 4=无健康源 5=路由冲突/指定源不可用 6=订阅配额已满
    error_msg: str
    current_subs: int
    max_subs: int


def unpack_sub_rsp(data: bytes) -> SubRsp:
    src, exch, inst, err, msg, cur, mx = struct.unpack(SUB_RSP_FMT, data[:SUB_RSP_SIZE])
    return SubRsp(_s(src), _s(exch), _s(inst), err, _s(msg), cur, mx)


# ── SubAllReq / SubAllRsp（整市场订阅）─────────────────────────────
# 一次订下「市场 × 品种 × 数据类型」命中的全部合约，任一维度取 All 表示不限。
# 网关挑一个申报 whole_market 的健康源承接推送，回执 source 回显它。
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
    error_id: int        # 4=网关无可承接的源 6=账号配额受限（整市场订阅要求无限配额）
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


# ── Quote（tag 401，快照 + 10 档盘口）──────────────────────────────
# 字段顺序严格对齐服务端 struct Quote（#pragma pack(1)，529 字节）。
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
class Quote:
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

    @property
    def order_book_id(self) -> str:
        """rqdata 风格标识，如 600519.XSHG。"""
        return f"{self.instrument_id}.{self.exchange_id}"


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


# ── 帧构造辅助 ───────────────────────────────────────────────────
def make_frame(msg_type: int, seq_no: int, body: bytes = b"") -> bytes:
    return pack_header(msg_type, seq_no, len(body)) + body


def make_heartbeat(seq_no: int) -> bytes:
    return make_frame(MsgType.HEARTBEAT, seq_no)
