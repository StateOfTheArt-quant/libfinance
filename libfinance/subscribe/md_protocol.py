"""
md_protocol.py — 二进制帧协议 Python 实现

严格对齐 C++ proto/md_protocol.h 中的 #pragma pack(1) 结构体布局。
"""

import struct
from dataclasses import dataclass
from enum import IntEnum

# ── 常量 ──────────────────────────────────────────────────────────
MAGIC = 0x4B463235  # "KF25"
VERSION = 1
HEADER_SIZE = 16

# ── 消息类型 ──────────────────────────────────────────────────────
class MsgType(IntEnum):
    REQ_LOGIN       = 0x0001
    RSP_LOGIN       = 0x0002
    REQ_SUBSCRIBE   = 0x0003
    RSP_SUBSCRIBE   = 0x0004
    REQ_UNSUBSCRIBE = 0x0005
    RSP_UNSUBSCRIBE = 0x0006
    MD_QUOTE        = 0x0010
    HEARTBEAT       = 0x00FF


# ── FrameHeader (16 bytes, packed) ────────────────────────────────
# uint32 magic, uint8 version, uint8 _pad, uint16 msg_type,
# uint32 seq_no, uint16 body_len, uint16 _pad2
HEADER_FMT = "<IBBHIHH"
assert struct.calcsize(HEADER_FMT) == HEADER_SIZE


def pack_header(msg_type: int, seq_no: int, body_len: int) -> bytes:
    return struct.pack(HEADER_FMT, MAGIC, VERSION, 0, msg_type, seq_no, body_len, 0)


def unpack_header(data: bytes):
    magic, ver, _pad, msg_type, seq_no, body_len, _pad2 = struct.unpack(HEADER_FMT, data)
    return magic, ver, msg_type, seq_no, body_len


# ── LoginReq: char[16] + char[32] + char[32] = 80 bytes ──────────
LOGIN_REQ_FMT = "<16s32s32s"
LOGIN_REQ_SIZE = struct.calcsize(LOGIN_REQ_FMT)

def pack_login_req(user_id: str, password: str, client_id: str = "kf_py_client") -> bytes:
    return struct.pack(
        LOGIN_REQ_FMT,
        user_id.encode().ljust(16, b"\x00")[:16],
        password.encode().ljust(32, b"\x00")[:32],
        client_id.encode().ljust(32, b"\x00")[:32],
    )


# ── LoginRsp: int32 + char[64] + uint64 + int8 + pad[3] + int32 = 84 bytes ──
LOGIN_RSP_FMT = "<i64sQb3xi"
LOGIN_RSP_SIZE = struct.calcsize(LOGIN_RSP_FMT)

@dataclass
class LoginRsp:
    error_id: int
    error_msg: str
    session_id: int
    user_level: int          # 用户等级（GUEST=10, PLUS=40, PRO=50, MAX=60）
    max_subscriptions: int   # 最大订阅数，-1 表示无限制

def unpack_login_rsp(data: bytes) -> LoginRsp:
    error_id, error_msg_raw, session_id, user_level, max_subs = struct.unpack(
        LOGIN_RSP_FMT, data[:LOGIN_RSP_SIZE])
    return LoginRsp(
        error_id,
        error_msg_raw.split(b"\x00", 1)[0].decode(),
        session_id,
        user_level,
        max_subs,
    )


# ── SubReq: char[8] + char[32] = 40 bytes ────────────────────────
SUB_REQ_FMT = "<8s32s"
SUB_REQ_SIZE = struct.calcsize(SUB_REQ_FMT)

def pack_sub_req(exchange_id: str, instrument_id: str) -> bytes:
    return struct.pack(
        SUB_REQ_FMT,
        exchange_id.encode().ljust(8, b"\x00")[:8],
        instrument_id.encode().ljust(32, b"\x00")[:32],
    )


# ── SubRsp: char[8] + char[32] + int32 + char[64] + int32 + int32 = 116 bytes
SUB_RSP_FMT = "<8s32si64sii"
SUB_RSP_SIZE = struct.calcsize(SUB_RSP_FMT)

@dataclass
class SubRsp:
    exchange_id: str
    instrument_id: str
    error_id: int
    error_msg: str
    current_subs: int    # 当前订阅数
    max_subs: int        # 最大订阅数，-1 无限制

def unpack_sub_rsp(data: bytes) -> SubRsp:
    exch, inst, error_id, error_msg_raw, current_subs, max_subs = struct.unpack(
        SUB_RSP_FMT, data[:SUB_RSP_SIZE])
    return SubRsp(
        exch.split(b"\x00", 1)[0].decode(),
        inst.split(b"\x00", 1)[0].decode(),
        error_id,
        error_msg_raw.split(b"\x00", 1)[0].decode(),
        current_subs,
        max_subs,
    )


# ── WireQuote ─────────────────────────────────────────────────────
# 字段顺序严格对齐 C++ WireQuote（#pragma pack(1)）
#
# char[9] trading_day, char[32] instrument_id, char[8] exchange_id,
# int32 instrument_type,
# double pre_close_price, pre_settlement_price, last_price,
# int64 volume, double turnover,
# double pre_open_interest, open_interest,
# double open_price, high_price, low_price,
#        upper_limit_price, lower_limit_price,
#        close_price, settlement_price, iopv,
# double bid_price[10], ask_price[10],
# int64 bid_volume[10], ask_volume[10],
# char[8] trading_phase_code, int64 data_time
WIRE_QUOTE_FMT = (
    "<"
    "9s"       # trading_day
    "32s"      # instrument_id
    "8s"       # exchange_id
    "i"        # instrument_type
    "d"        # pre_close_price
    "d"        # pre_settlement_price
    "d"        # last_price
    "q"        # volume
    "d"        # turnover
    "d"        # pre_open_interest
    "d"        # open_interest
    "d"        # open_price
    "d"        # high_price
    "d"        # low_price
    "d"        # upper_limit_price
    "d"        # lower_limit_price
    "d"        # close_price
    "d"        # settlement_price
    "d"        # iopv
    "10d"      # bid_price[10]
    "10d"      # ask_price[10]
    "10q"      # bid_volume[10]
    "10q"      # ask_volume[10]
    "8s"       # trading_phase_code
    "q"        # data_time
)
WIRE_QUOTE_SIZE = struct.calcsize(WIRE_QUOTE_FMT)


@dataclass
class Quote:
    trading_day: str
    instrument_id: str
    exchange_id: str
    instrument_type: int
    pre_close_price: float
    pre_settlement_price: float
    last_price: float
    volume: int
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
    bid_price: list       # [10]
    ask_price: list       # [10]
    bid_volume: list      # [10]
    ask_volume: list      # [10]
    trading_phase_code: str
    data_time: int


def unpack_wire_quote(data: bytes) -> Quote:
    fields = struct.unpack(WIRE_QUOTE_FMT, data[:WIRE_QUOTE_SIZE])
    idx = 0
    def _s():
        nonlocal idx; v = fields[idx]; idx += 1
        return v.split(b"\x00", 1)[0].decode()
    def _i():
        nonlocal idx; v = fields[idx]; idx += 1; return v
    def _f():
        nonlocal idx; v = fields[idx]; idx += 1; return v
    def _fa(n):
        nonlocal idx; v = list(fields[idx:idx+n]); idx += n; return v
    def _ia(n):
        nonlocal idx; v = list(fields[idx:idx+n]); idx += n; return v

    return Quote(
        trading_day=_s(), instrument_id=_s(), exchange_id=_s(),
        instrument_type=_i(),
        pre_close_price=_f(), pre_settlement_price=_f(), last_price=_f(),
        volume=_i(), turnover=_f(),
        pre_open_interest=_f(), open_interest=_f(),
        open_price=_f(), high_price=_f(), low_price=_f(),
        upper_limit_price=_f(), lower_limit_price=_f(),
        close_price=_f(), settlement_price=_f(), iopv=_f(),
        bid_price=_fa(10), ask_price=_fa(10),
        bid_volume=_ia(10), ask_volume=_ia(10),
        trading_phase_code=_s(), data_time=_i(),
    )


# ── 帧构造辅助 ───────────────────────────────────────────────────
def make_frame(msg_type: int, seq_no: int, body: bytes = b"") -> bytes:
    return pack_header(msg_type, seq_no, len(body)) + body


def make_heartbeat(seq_no: int) -> bytes:
    return make_frame(MsgType.HEARTBEAT, seq_no)
