#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_subscribe_example.py — libfinance 实时行情订阅示例（按行情源）

用法:
    python live_subscribe_example.py [host] [port] [source]
      - 指定 source：订该源的 600519.SSE
      - 不指定 source：一条连接同时混订 webquote + sim 的 600519.SSE，
        回调里靠 quote.source 区分来源（同一合约多源并行、互不串扰）。

要点：
    subscribe(instruments, exchange, source=...)  按源订阅
    on_depth_market_data(quote)                   quote.source 标明来源
    全市场订阅另见 fullmarket_health_check.py 的 subscribe_all。
"""
import signal
import sys
import threading

from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

stop = threading.Event()
for _sig in (signal.SIGINT, signal.SIGTERM):
    signal.signal(_sig, lambda *_: stop.set())


class DemoSpi(QuoteSpi):
    def __init__(self):
        self.count = 0

    def on_connected(self):
        print("[client] connected")

    def on_disconnected(self, reason):
        print(f"[client] disconnected reason={reason}")
        stop.set()

    def on_rsp_login(self, rsp, _):
        if rsp.error_id != 0:
            print(f"[client] login FAIL: {rsp.error_msg}")
            stop.set()
        else:
            mx = "unlimited" if rsp.max_subscriptions < 0 else rsp.max_subscriptions
            print(f"[client] login OK  level={rsp.user_level}  max_subs={mx}")

    def on_rsp_subscribe(self, rsp, _):
        if rsp.error_id == 0:
            print(f"[client] subscribed {rsp.source}:{rsp.exchange_id}.{rsp.instrument_id}")
        elif rsp.error_id == 3:
            print(f"[client] QUOTA EXCEEDED: {rsp.error_msg}")
        else:
            print(f"[client] subscribe fail: {rsp.error_msg}")

    def on_depth_market_data(self, q):
        self.count += 1
        print(f"[{self.count:5d}] src={q.source:<9s} {q.exchange_id}.{q.instrument_id}"
              f"  last={q.last_price:9.3f}  bid1={q.bid_price[0]:9.3f}"
              f"  ask1={q.ask_price[0]:9.3f}  vol={q.volume}")


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9001
    source = sys.argv[3] if len(sys.argv) > 3 else ""

    spi = DemoSpi()
    api = QuoteApi()
    api.register_spi(spi)
    if api.connect(host, port) != 0:
        print("[client] connect failed")
        return 1

    if source:
        print(f"[client] subscribe {source}:SSE.600519")
        api.subscribe(["600519"], "SSE", source=source)
    else:
        print("[client] multiplex webquote + sim on SSE.600519（回调按 quote.source 区分）")
        api.subscribe(["600519"], "SSE", source="webquote")
        api.subscribe(["600519"], "SSE", source="sim")

    stop.wait()          # Ctrl+C 或断线后退出
    print(f"\n[client] total quotes: {spi.count}")
    api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
