"""
live_subscribe_example.py — libfinance 流式订阅 demo（按行情源订阅）

用法:
    python live_subscribe_example.py [host] [port] [source]
    - 给定 source：只订该源的 600519.SSE
    - 不给 source：一条连接同时混订 webquote 与 sim 的 600519.SSE，
      on_depth_market_data 里靠 quote.source 区分来源（webquote 为真实行情）。
"""

import sys
import signal
import time
import threading

from libfinance.subscribe.md_protocol import LoginRsp, SubRsp, Quote
from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

g_stop = threading.Event()  # 初始 unset，收到信号后 set 表示该停了


def sig_handler(_sig, _frame):
    g_stop.set()

signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGTERM, sig_handler)


class MyQuoteSpi(QuoteSpi):
    def __init__(self):
        self.count = 0

    def on_connected(self):
        print("[SPI] connected")

    def on_disconnected(self, reason: int):
        print(f"[SPI] disconnected reason={reason}")
        g_stop.set()

    def on_rsp_login(self, rsp: LoginRsp, request_id: int):
        if rsp.error_id == 0:
            max_str = "unlimited" if rsp.max_subscriptions < 0 else str(rsp.max_subscriptions)
            print(f"[SPI] login OK  session_id={rsp.session_id}"
                  f"  user_level={rsp.user_level}  max_subs={max_str}")
        else:
            print(f"[SPI] login FAIL: {rsp.error_msg}")
            g_stop.set()

    def on_rsp_subscribe(self, rsp: SubRsp, request_id: int):
        if rsp.error_id == 0:
            max_str = "unlimited" if rsp.max_subs < 0 else str(rsp.max_subs)
            print(f"[SPI] subscribed {rsp.source}:{rsp.exchange_id}.{rsp.instrument_id}"
                  f"  [{rsp.current_subs}/{max_str}]")
        elif rsp.error_id == 3:
            print(f"[SPI] subscribe QUOTA EXCEEDED: {rsp.error_msg}"
                  f"  [{rsp.current_subs}/{rsp.max_subs}]")
        else:
            print(f"[SPI] subscribe fail: {rsp.error_msg}")

    def on_rsp_unsubscribe(self, rsp: SubRsp, request_id: int):
        print(f"[SPI] unsubscribed {rsp.source}:{rsp.exchange_id}.{rsp.instrument_id}")

    def on_depth_market_data(self, q: Quote):
        self.count += 1
        print(
            f"[QUOTE #{self.count:5d}] "
            f"src={q.source:<10s} "
            f"{q.exchange_id}.{q.instrument_id}"
            f"  last={q.last_price:10.3f}"
            f"  bid1={q.bid_price[0]:10.3f}"
            f"  ask1={q.ask_price[0]:10.3f}"
            f"  vol={q.bid_volume[0]}"
        )

    def on_heartbeat(self):
        pass


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9001
    source = sys.argv[3] if len(sys.argv) > 3 else ""

    spi = MyQuoteSpi()
    api = QuoteApi()
    api.register_spi(spi)

    if api.connect(host, port) != 0:
        print("[Client] connect failed")
        return 1

    #time.sleep(0.2)
    #api.login("trader1", "pass1234")
    #time.sleep(0.3)

    if source:
        print(f"[Client] subscribing source={source} 600519.SSE")
        api.subscribe(["600519"], "SSE", source=source)
    else:
        # 一条连接混订两源同一合约，回调里靠 quote.source 区分
        print("[Client] multiplexing webquote + sim on 600519.SSE")
        api.subscribe(["600519"], "SSE", source="webquote")
        api.subscribe(["600519"], "SSE", source="sim")

    time.sleep(5)
    if not g_stop.is_set() and source:
        print("\n[Client] unsubscribing 600519...")
        api.unsubscribe(["600519"], "SSE", source=source)

    g_stop.wait()  # blocks until set by signal or disconnect

    print(f"\n[Client] total quotes: {spi.count}")
    api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())