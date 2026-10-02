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


def test_protocol_version_and_hash_are_v3():
    assert mp.VERSION == 3
    assert mp.instrument_hash("XSHG", "600000") != mp.instrument_hash("XSHE", "600000")


def _sent(monkeypatch):
    api, frames = QuoteApi(), []
    monkeypatch.setattr(api, "_send", lambda msg_type, body=b"": frames.append((msg_type, body)) or len(frames))
    return api, frames


def test_subscribe_takes_order_book_ids_across_exchanges(monkeypatch):
    api, frames = _sent(monkeypatch)
    assert api.subscribe(["600519.XSHG", "000001.XSHE", "600519.XSHG"], source="sim") == 2   # duplicates once
    assert frames == [(mp.MsgType.REQ_SUBSCRIBE, mp.pack_sub_req("XSHG", "600519", "sim")),
                      (mp.MsgType.REQ_SUBSCRIBE, mp.pack_sub_req("XSHE", "000001", "sim"))]
    api.unsubscribe("000001.XSHE")
    assert frames[-1] == (mp.MsgType.REQ_UNSUBSCRIBE, mp.pack_sub_req("XSHE", "000001"))


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
    rsp = mp.unpack_sub_rsp(mp.struct.pack(mp.SUB_RSP_FMT, b"sim", b"XSHE", b"000001", 0, b"", 1, 10))
    assert rsp.order_book_id == "000001.XSHE"
    tick = mp.unpack_tick(mp.struct.pack(mp.TICK_FMT, 1, b"600519", b"XSHG", 1, 1.0, 2.0, 3.0, 4.0))
    assert tick.order_book_id == "600519.XSHG"
    gap = qa.SequenceGap(1, mp.RecordTag.QUOTE, "XSHG", "600519", 3, 5)
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
    assert env.instrument_key == mp.instrument_hash("XSHG", "600000")   # 与服务端 FNV 一致
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
    assert api.connect() == 0           # 不 login、不给地址：全部来自 libfinance-service
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
