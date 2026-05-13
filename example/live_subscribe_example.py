"""
demo.py — Python 客户端 demo（对齐 C++ client_main.cpp）
"""

import sys
import signal
import time
import threading

from libfinance.subscribe.md_protocol import LoginRsp, SubRsp, WireQuote
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
            print(f"[SPI] subscribed {rsp.exchange_id}.{rsp.instrument_id}"
                  f"  [{rsp.current_subs}/{max_str}]")
        elif rsp.error_id == 3:
            print(f"[SPI] subscribe QUOTA EXCEEDED: {rsp.error_msg}"
                  f"  [{rsp.current_subs}/{rsp.max_subs}]")
        else:
            print(f"[SPI] subscribe fail: {rsp.error_msg}")

    def on_rsp_unsubscribe(self, rsp: SubRsp, request_id: int):
        print(f"[SPI] unsubscribed {rsp.exchange_id}.{rsp.instrument_id}")

    def on_depth_market_data(self, q: WireQuote):
        self.count += 1
        print(
            f"[QUOTE #{self.count:5d}] "
            f"{q.exchange_id}.{q.instrument_id}"
            f"  last={q.last_price:8.1f}"
            f"  bid1={q.bid_price[0]:8.1f}"
            f"  ask1={q.ask_price[0]:8.1f}"
            f"  vol={q.volume}"
        )

    def on_heartbeat(self):
        pass


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9001

    spi = MyQuoteSpi()
    api = QuoteApi()
    api.register_spi(spi)

    if api.connect(host, port) != 0:
        print("[Client] connect failed")
        return 1

    #time.sleep(0.2)
    #api.login("trader1", "pass1234")
    #time.sleep(0.3)

    api.subscribe(["rb2501", "hc2501"], "SHFE")
    api.subscribe(["i2501", "j2501"], "DCE")
    api.subscribe(["600000", "600001"], "SSE")

    time.sleep(5)
    if not g_stop.is_set():
        print("\n[Client] unsubscribing rb2501...")
        api.unsubscribe(["rb2501"], "SHFE")

    g_stop.wait()  # blocks until set by signal or disconnect

    print(f"\n[Client] total quotes: {spi.count}")
    api.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())