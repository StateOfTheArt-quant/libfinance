#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_subscribe_example.py — libfinance 实时行情订阅示例

流程：连网关 → 登录 → 发现可订源（query_sources）→ 订阅 → 收行情回调。

用法:
    python live_subscribe_example.py [host] [port] [source]
      - 不指定 source：无源订阅，网关按健康+优先级自动选源，源掉线自动灾备切换
      - 指定 source  ：定向订阅该源，不自动切源；该源不健康时明确失败

要点：
    订阅写在 on_rsp_login 里 —— 断线自动重连+重登录后会再次触发，订阅随之重放。
    交易所用 rqdata 风格后缀：XSHG(上交所) / XSHE(深交所)。
    行情帧不带来源，要知道数据来自哪个源看订阅回执的 rsp.source。
    整市场订阅另见 fullmarket_health_check.py。
"""
import signal
import sys
import threading

from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

INSTRUMENTS = ["600519"]      # 贵州茅台
EXCHANGE = "XSHG"             # 上交所

stop = threading.Event()
for _sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(_sig, lambda *_: stop.set())


class DemoSpi(QuoteSpi):
    def __init__(self, api, source=""):
        self.api = api
        self.source = source
        self.count = 0

    def on_connected(self):
        print("[client] connected")

    def on_disconnected(self, reason):
        print(f"[client] disconnected reason={reason}，等待自动重连…")

    # 登录成功即发现可订源；断线重连会重新走一遍，订阅自动重放。
    def on_rsp_login(self, rsp, _):
        if rsp.error_id != 0:
            print(f"[client] login FAIL: {rsp.error_msg}")
            stop.set()
            return
        mx = "unlimited" if rsp.max_subscriptions < 0 else rsp.max_subscriptions
        print(f"[client] login OK  level={rsp.user_level}  max_subs={mx}")
        self.api.query_sources()

    def on_rsp_query_sources(self, sources, _):
        print(f"[client] 发现 {len(sources)} 个源：")
        for s in sources:
            cover = "整市场" if s.whole_market else f"mask={s.instrument_mask:#x}"
            state = "ready" if s.health else "down"
            mode = " 仅定向(不自动选/灾备)" if s.directed_only else ""
            print(f"  - {s.source:<12} [{state}] priority={s.priority} 覆盖={cover}{mode}")

        # 仅定向源不参与无源订阅/灾备，不能算作可用于自动路由的健康源。
        if not self.source and not any(s.health and not s.directed_only for s in sources):
            print("[client] 暂无可用于自动路由的健康源，不订阅")
            return
        tag = f"定向 {self.source}" if self.source else "无源(网关自动选源)"
        print(f"[client] 订阅 {EXCHANGE}.{','.join(INSTRUMENTS)}  方式={tag}")
        self.api.subscribe(INSTRUMENTS, EXCHANGE, source=self.source)

    def on_rsp_subscribe(self, rsp, _):
        if rsp.error_id == 0:
            print(f"[client] subscribed {rsp.exchange_id}.{rsp.instrument_id} "
                  f"← 供数源 '{rsp.source}'  ({rsp.current_subs}/{rsp.max_subs})")
        elif rsp.error_id == 6:
            print(f"[client] 订阅配额已满: {rsp.error_msg}")
        elif rsp.error_id == 5:
            print(f"[client] 路由冲突或指定源不可用: {rsp.error_msg}")
        else:
            print(f"[client] subscribe fail({rsp.error_id}): {rsp.error_msg}")

    def on_depth_market_data(self, q):
        self.count += 1
        print(f"[{self.count:5d}] {q.order_book_id:<14s}"
              f"  last={q.last_price:9.3f}  bid1={q.bid_price[0]:9.3f}"
              f"  ask1={q.ask_price[0]:9.3f}  vol={q.volume:.0f}")


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9001
    source = sys.argv[3] if len(sys.argv) > 3 else ""

    api = QuoteApi()
    spi = DemoSpi(api, source)
    api.register_spi(spi)
    if api.connect(host, port) != 0:
        print("[client] connect failed")
        return 1
    api.login("demo", "")     # 凭据被记住，断线重连自动重登录

    stop.wait()               # Ctrl+C 退出
    print(f"\n[client] total quotes: {spi.count}")
    api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
