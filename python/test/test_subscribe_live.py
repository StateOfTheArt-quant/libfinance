# -*- coding: utf-8 -*-
"""libfinance.subscribe 对真实 dynamics 网关的端到端测试（需要环境变量，缺省跳过）。

    LIBFINANCE_TEST_GATEWAY=127.0.0.1:9001              票据模式的网关 downstream 地址（有行情源在推）
    LIBFINANCE_TEST_TICKET_CMD="md_ticket issue ..."     打印一张有效票据的命令

离线部分（结构体布局）在 import md_protocol 时即由 assert 校验。
"""
import os
import shlex
import subprocess
import threading
import time

import pytest

from libfinance.subscribe import md_protocol as mp
from libfinance.subscribe import quote_api as qa
from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

GATEWAY = os.environ.get("LIBFINANCE_TEST_GATEWAY")
TICKET_CMD = os.environ.get("LIBFINANCE_TEST_TICKET_CMD")
live = pytest.mark.skipif(not (GATEWAY and TICKET_CMD), reason="no live gateway configured")


def issue_ticket() -> str:
    return subprocess.check_output(shlex.split(TICKET_CMD), text=True).strip()


def wait(pred, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if pred():
            return True
        time.sleep(0.05)
    return pred()


class Recorder(QuoteSpi):
    def __init__(self, api, instruments=("600000.XSHG",)):
        self.api = api
        self.instruments = list(instruments)
        self.logins, self.subs, self.quotes, self.gaps = [], [], [], []
        self.lock = threading.Lock()

    def on_rsp_login(self, rsp, _):
        self.logins.append(rsp)
        if rsp.error_id == 0 and self.instruments:
            self.api.subscribe(self.instruments)

    def on_rsp_subscribe(self, rsp, _):
        self.subs.append(rsp)

    def on_depth_market_data(self, quote, envelope):
        with self.lock:
            self.quotes.append((quote, envelope))

    def on_sequence_gap(self, gap):
        self.gaps.append(gap)


def test_protocol_version_and_hash_are_v4():
    assert mp.VERSION == 4
    assert mp.instrument_hash("600000.XSHG") != mp.instrument_hash("600000.XSHE")
    # FNV-1a 64 over the order_book_id, as dynamics::instrument_hash
    assert mp.instrument_hash("") == 14695981039346656037


def _sent(monkeypatch):
    api, frames = QuoteApi(), []
    monkeypatch.setattr(api, "_send", lambda msg_type, body=b"": frames.append((msg_type, body)) or len(frames))
    return api, frames


def test_subscribe_takes_order_book_ids_across_exchanges(monkeypatch):
    api, frames = _sent(monkeypatch)
    assert api.subscribe(["600519.XSHG", "000001.XSHE", "600519.XSHG"], source="sim") == 2   # duplicates once
    assert frames == [(mp.MsgType.REQ_SUBSCRIBE, mp.pack_sub_req("600519.XSHG", "sim")),
                      (mp.MsgType.REQ_SUBSCRIBE, mp.pack_sub_req("000001.XSHE", "sim"))]
    assert frames[0][1] == b"sim".ljust(16, b"\0") + b"600519.XSHG".ljust(48, b"\0")   # 线上就是这串
    api.unsubscribe("000001.XSHE")
    assert frames[-1] == (mp.MsgType.REQ_UNSUBSCRIBE, mp.pack_sub_req("000001.XSHE"))


def test_a_bad_code_sends_nothing(monkeypatch):
    api, frames = _sent(monkeypatch)
    with pytest.raises(ValueError, match="not <code>.<exchange>"):
        api.subscribe(["600519.XSHG", "600000"])
    with pytest.raises(ValueError, match="serves"):
        api.subscribe("AAPL.US")
    with pytest.raises(ValueError, match="at least one"):
        api.subscribe([])
    with pytest.raises(TypeError):
        api.subscribe(["600519"], "XSHG")          # the old (codes, exchange) form: source is keyword-only
    assert frames == []


def test_records_and_receipts_carry_the_order_book_id():
    rsp = mp.unpack_sub_rsp(mp.struct.pack(mp.SUB_RSP_FMT, b"sim", b"000001.XSHE", 0, b"", 1, 10))
    assert rsp.order_book_id == "000001.XSHE"
    tick = mp.unpack_tick(mp.struct.pack(mp.TICK_FMT, 1, b"600519.XSHG", 1.0, 2.0, 3.0, 4.0))
    assert tick.order_book_id == "600519.XSHG" and tick.ask_volume == 4.0
    quote = mp.unpack_quote(mp.struct.pack(mp.QUOTE_FMT, 1, b"600519.XSHG", *range(17), 7, *range(40), b"T0"))
    assert quote.order_book_id == "600519.XSHG" and quote.pre_close_price == 0 and quote.total_ask_volume == 16
    assert quote.total_trade_num == 7 and quote.bid_price == list(range(10)) and quote.ask_volume == list(range(30, 40))
    assert quote.trading_phase_code == "T0"
    for record in (rsp, tick, quote):
        assert not hasattr(record, "instrument_id") and not hasattr(record, "exchange_id")
        assert not hasattr(record, "instrument_type")
    gap = qa.SequenceGap(1, mp.RecordTag.QUOTE, "600519.XSHG", 3, 5)
    assert gap.order_book_id == "600519.XSHG"
    assert mp.unpack_sub_all_rsp(mp.struct.pack(mp.SUB_ALL_RSP_FMT, b"", 0, b"")).source == ""


@live
def test_ticket_login_envelopes_and_resume_after_reconnect():
    api = QuoteApi()
    spi = Recorder(api)
    api.register_spi(spi)
    api.login(issue_ticket)
    assert api.connect(GATEWAY) == 0
    assert wait(lambda: spi.logins) and spi.logins[0].error_id == 0, spi.logins[0].error_msg
    assert spi.logins[0].expires_at_ms > 0
    assert wait(lambda: spi.subs) and spi.subs[0].error_id == 0
    assert wait(lambda: len(spi.quotes) >= 5, timeout=15)
    quote, env = spi.quotes[-1]
    assert env.instrument_key == mp.instrument_hash("600000.XSHG")   # 与服务端 FNV 一致
    assert env.seq > 0 and quote.order_book_id == "600000.XSHG"

    # 强制断线：SDK 自动重连、重新登录、按 seq 续传，不报缺口
    before = len(spi.quotes)
    api._close_socket()
    assert wait(lambda: len(spi.logins) >= 2)
    assert wait(lambda: len(spi.quotes) >= before + 5, timeout=15)
    assert spi.gaps == []
    live_seqs = [e.seq for _, e in spi.quotes if not e.snapshot]
    assert live_seqs == sorted(live_seqs) and len(set(live_seqs)) == len(live_seqs)   # 不重、按序
    api.disconnect()


@live
def test_invalid_ticket_is_rejected_and_not_retried():
    api = QuoteApi()
    spi = Recorder(api, instruments=())
    api.register_spi(spi)
    api.login("v4.public.not-a-ticket")
    assert api.connect(GATEWAY) == 0
    assert wait(lambda: spi.logins)
    assert spi.logins[0].error_id == mp.ErrorCode.TOKEN_INVALID
    api.disconnect()


@live
def test_default_path_fetches_ticket_and_gateways_from_libfinance(monkeypatch):
    calls = []

    def fake_service():
        calls.append(1)
        return {"token": issue_ticket(), "gateways": GATEWAY, "expires_at": 0, "grant": {}}

    monkeypatch.setattr(qa, "libfinance_ticket", fake_service)
    api = QuoteApi()
    spi = Recorder(api)
    api.register_spi(spi)
    assert api.connect() == 0           # 不 login、不给地址：全部来自 libfinance 服务端
    assert wait(lambda: spi.logins) and spi.logins[0].error_id == 0
    assert calls
    assert wait(lambda: spi.quotes, timeout=15)
    api.disconnect()


@live
def test_ticket_is_renewed_in_place():
    class Renewing(Recorder):
        def __init__(self, api):
            super().__init__(api)
            self.reauths = []

        def on_rsp_reauth(self, rsp):
            self.reauths.append(rsp)

    calls = []

    def short_lived():
        calls.append(1)
        # 有效期短于网关的到期提示提前量（60 s）：登录后立即收到提示并续期
        return subprocess.check_output(shlex.split(TICKET_CMD.replace("--ttl-sec 600", "--ttl-sec 30")),
                                       text=True).strip()

    api = QuoteApi()
    spi = Renewing(api)
    api.register_spi(spi)
    api.login(short_lived)
    assert api.connect(GATEWAY) == 0
    assert wait(lambda: spi.reauths, timeout=5)
    assert spi.reauths[0].error_id == 0 and len(calls) >= 2
    assert len(spi.logins) == 1        # 续期不重连、不重新登录
    api.disconnect()


# ── 票据被吊销后的重连（离线：回环上的假网关）─────────────────────────────
import socket
import struct

from libfinance.client import RpcError


class FakeGateway:
    """按协议应答登录与订阅；revoke() 发 NOTIFY_SESSION_CLOSED(吊销) 并断开，之后该票据登录答 TOKEN_REVOKED。"""

    def __init__(self):
        self.listener = socket.socket()
        self.listener.bind(("127.0.0.1", 0))
        self.listener.listen(4)
        self.address = "127.0.0.1:%d" % self.listener.getsockname()[1]
        self.logins, self.subscribed, self.revoked = [], [], set()
        self.connections = 0
        self.client = None
        threading.Thread(target=self._serve, daemon=True).start()

    def _recv(self, sock, n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError
            buf += chunk
        return buf

    def _send(self, msg_type, body):
        self.client.sendall(mp.make_frame(msg_type, 0, body))

    def _serve(self):
        while True:
            try:
                sock, _ = self.listener.accept()
            except OSError:
                return
            self.client = sock
            self.connections += 1
            try:
                while True:
                    _magic, _ver, msg_type, _seq, body_len = mp.unpack_header(self._recv(sock, mp.HEADER_SIZE))
                    body = self._recv(sock, body_len) if body_len else b""
                    if msg_type == mp.MsgType.REQ_LOGIN:
                        _cid, length, _pad = struct.unpack_from(mp.LOGIN_REQ_FMT, body)
                        token = body[struct.calcsize(mp.LOGIN_REQ_FMT):][:length].decode()
                        self.logins.append(token)
                        error = mp.ErrorCode.TOKEN_REVOKED if token in self.revoked else 0
                        self._send(mp.MsgType.RSP_LOGIN, struct.pack(
                            mp.LOGIN_RSP_FMT, error, b"revoked" if error else b"ok", 1, 4102444800000,
                            5, 2, 200, 0, 0x180, 1))
                    elif msg_type == mp.MsgType.REQ_SUBSCRIBE:
                        _src, order_book_id = struct.unpack(mp.SUB_REQ_FMT, body)
                        self.subscribed.append((self.connections, order_book_id.rstrip(b"\0").decode()))
                        self._send(mp.MsgType.RSP_SUBSCRIBE, struct.pack(
                            mp.SUB_RSP_FMT, b"sim", order_book_id, 0, b"", 1, 5))
            except (ConnectionError, OSError):
                sock.close()

    def revoke(self):
        self.revoked.add(self.logins[-1])
        self._send(mp.MsgType.NOTIFY_SESSION_CLOSED, struct.pack(mp.SESSION_CLOSED_FMT, 2, b"ticket revoked"))
        self.client.shutdown(socket.SHUT_RDWR)

    def close(self):
        self.listener.close()


def _connected(provider_of):
    """provider_of(gateway) -> the ticket provider; it may look at what the gateway has revoked."""
    gateway = FakeGateway()
    api = QuoteApi()
    spi = Recorder(api, instruments=("600519.XSHG",))
    api.register_spi(spi)
    api.login(provider_of(gateway))
    assert api.connect(gateway.address) == 0
    assert wait(lambda: gateway.subscribed)
    return gateway, api, spi


def test_a_revoked_ticket_is_replaced_and_subscriptions_come_back():
    # a new ticket after every revocation (the provider is also asked at login and on connecting)
    gateway, api, spi = _connected(lambda gw: lambda: "t%d" % len(gw.revoked))
    gateway.revoke()
    # 重连、换新票据登录、在 on_rsp_login 里重放订阅
    assert wait(lambda: len(gateway.subscribed) >= 2)
    assert gateway.logins == ["t0", "t1"]
    assert gateway.subscribed == [(1, "600519.XSHG"), (2, "600519.XSHG")]
    assert [rsp.error_id for rsp in spi.logins] == [0, 0]
    api.disconnect()
    gateway.close()


def test_a_caller_refused_tickets_stops_after_revocation():
    refused = []

    def banned_once_revoked(gw):
        def provider():
            if gw.revoked:
                refused.append(1)
                raise RpcError(2001, "real-time quote access is suspended for this caller", "PermissionError")
            return "t0"
        return provider

    gateway, api, spi = _connected(banned_once_revoked)
    gateway.revoke()
    assert wait(lambda: gateway.connections >= 2)
    time.sleep(1.0)
    assert gateway.logins == ["t0"]          # 拿不到新票据：不带空票据 / 旧票据去登录
    assert len(refused) == 1                 # 被拒绝后不再反复去取
    api.disconnect()
    gateway.close()


def test_a_fixed_ticket_revoked_is_not_retried_forever():
    gateway, api, spi = _connected(lambda gw: "fixed")
    gateway.revoke()
    assert wait(lambda: len(gateway.logins) >= 2)
    time.sleep(1.0)
    assert gateway.logins == ["fixed", "fixed"]   # 再试一次，网关答已吊销，到此为止
    assert spi.logins[-1].error_id == mp.ErrorCode.TOKEN_REVOKED
    api.disconnect()
    gateway.close()
