#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fullmarket_health_check.py —— 实时行情「全市场」体检

用【整市场订阅】(subscribe_all) 统计覆盖（出数标的数）、吞吐、延迟/新鲜度，
判断当前承接源是否健康。

subscribe_all 按「市场 × 品种 × 数据类型」下单，**客户端不枚举任何代码** ——
网关自己挑一个申报 whole_market 的健康源承接推送，回执里回显是哪个源。
因此覆盖即真实全市场、不含空号。

前提：票据授予整市场订阅（grant.sub_all）。不登录按 IP 拿到的最小额度不含它（会被拒，error_id=8），
需要用 --ticket 提供一张有整市场授权的票据（例如 libfinance-service 为高等级账号签发的）。

用法:
    python fullmarket_health_check.py --duration 20
    python fullmarket_health_check.py --market SSE --instrument-type Stock

退出码: 0=健康, 1=不健康(0行情 / 出数标的<--min-instruments / p95滞后超阈值), 2=连接或登录失败
"""
import argparse
import signal
import statistics
import sys
import threading
import time

from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi
from libfinance.subscribe.md_protocol import (
    MarketType, SubscribeInstrumentType, SubscribeDataType,
)


class HealthSpi(QuoteSpi):
    def __init__(self):
        self.lock = threading.Lock()
        self.logged_in = threading.Event()
        self.login_ok = False
        self.sub_ok = False
        self.sub_err = ""
        self.sub_errno = -1
        self.feed_source = ""      # 网关实际挑中的承接源
        self.first = {}       # "exch.inst" -> 首条到达 wall 时间
        self.first_dt = {}    # "exch.inst" -> 首条 data_time（算新鲜度）
        self.total = 0

    def on_rsp_login(self, rsp, _):
        self.login_ok = (rsp.error_id == 0)
        mx = "unlimited" if rsp.max_subscriptions < 0 else rsp.max_subscriptions
        print(f"[health] login {'OK' if self.login_ok else 'FAIL'} "
              f"whole_market={rsp.sub_all} max_subs={mx} "
              f"{'' if self.login_ok else rsp.error_msg}")
        self.logged_in.set()

    def on_rsp_subscribe_all(self, rsp, _):
        self.sub_ok = (rsp.error_id == 0)
        self.sub_err = rsp.error_msg
        self.sub_errno = rsp.error_id
        self.feed_source = rsp.source

    def on_depth_market_data(self, q, envelope):
        now = time.time()
        key = f"{q.exchange_id}.{q.instrument_id}"
        with self.lock:
            self.total += 1
            if key not in self.first:
                self.first[key] = now
                self.first_dt[key] = q.data_time


def lag_ms(data_time, wall):
    """data_time 为 ns epoch；解析为 now-data_time(ms)，无法判定返回 None。"""
    if not data_time or data_time <= 0:
        return None
    for scale in (1e9, 1e6, 1e3, 1.0):
        secs = data_time / scale
        if 9.46e8 < secs < 4.1e9:        # 2000~2100 的合理 epoch 秒
            return (wall - secs) * 1000.0
    return None


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p / 100.0 * (len(xs) - 1))))]


def main():
    ap = argparse.ArgumentParser(description="实时行情源全市场体检（subscribe_all）")
    ap.add_argument("--gateways", default=None,
                    help="网关地址 host:port[,host:port]；不给则用 libfinance-service 返回的")
    ap.add_argument("--market", default="All",
                    choices=[m.name for m in MarketType],
                    help="市场维度，All=不限（默认）")
    ap.add_argument("--instrument-type", default="All",
                    choices=[t.name for t in SubscribeInstrumentType],
                    help="品种维度，All=不限（默认）")
    ap.add_argument("--data-type", default="All",
                    choices=[t.name for t in SubscribeDataType],
                    help="数据类型维度，All=不限（默认）")
    ap.add_argument("--ticket", default="", help="有整市场授权的票据；不给则自动向 libfinance-service 取（按 IP 额度）")
    ap.add_argument("--duration", type=int, default=20, help="采集时长(秒)")
    ap.add_argument("--min-instruments", type=int, default=0,
                    help="出数标的少于此值判不健康，0=不判")
    ap.add_argument("--fail-lag-ms", type=float, default=0.0,
                    help="p95 数据滞后超此(ms)判不健康，0=不判")
    args = ap.parse_args()

    spi = HealthSpi()
    api = QuoteApi()
    api.register_spi(spi)
    if args.ticket:
        api.login(args.ticket)
    if api.connect(args.gateways) != 0:
        print("[health] connect failed", file=sys.stderr)
        return 2
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    spi.logged_in.wait(timeout=5)
    if not spi.login_ok:
        api.disconnect()
        return 2

    # 整市场订阅：一条 subscribe_all，网关挑承接源并让它走全量推送（不枚举代码、无空号）
    market = MarketType[args.market]
    itype = SubscribeInstrumentType[args.instrument_type]
    dtype = SubscribeDataType[args.data_type]
    print(f"[health] subscribe_all(market={market.name}, instrument={itype.name}, "
          f"data={dtype.name})，采集 {args.duration}s ...")
    t_sub = time.time()
    api.subscribe_all(market, itype, dtype)

    deadline = t_sub + args.duration
    while time.time() < deadline and not stop.is_set():
        time.sleep(min(5.0, max(0.0, deadline - time.time())))
        with spi.lock:
            covered, tq = len(spi.first), spi.total
        dt = max(1e-9, time.time() - t_sub)
        print(f"[health]  +{int(time.time()-t_sub):>3}s  出数标的={covered}  行情={tq}  qps≈{tq/dt:.0f}")
    api.disconnect()

    # ───────── 汇总 ─────────
    with spi.lock:
        covered = len(spi.first)
        total = spi.total
        first_lat = sorted((t - t_sub) * 1000.0 for t in spi.first.values())
        lags = [v for v in (lag_ms(spi.first_dt[k], spi.first[k])
                            for k in list(spi.first)[:2000]) if v is not None]
    elapsed = max(1e-9, time.time() - t_sub)
    if not spi.sub_ok:
        hint = {4: "网关侧没有可承接整市场的源（源须申报 whole_market、健康且覆盖该条件）",
                6: "账号订阅配额受限——整市场订阅要求配额无限制"}.get(spi.sub_errno, "")
        print(f"[health] subscribe_all 应答({spi.sub_errno}): {spi.sub_err or '(未收到)'}"
              f"{chr(10) + '         ' + hint if hint else ''}", file=sys.stderr)

    print("\n" + "=" * 60)
    print(f"实时源体检  承接源={spi.feed_source or '(未知)'}  "
          f"条件={market.name}/{itype.name}/{dtype.name}  {args.gateways or '(libfinance-service)'}")
    print("=" * 60)
    print(f"覆盖      出数标的={covered}（整市场订阅，无空号）")
    print(f"吞吐      总行情={total}  采集={elapsed:.1f}s  qps≈{total/elapsed:.0f}")
    if first_lat:
        print(f"首条延迟  中位={statistics.median(first_lat):.0f}ms  "
              f"p95={pct(first_lat,95):.0f}ms  (订阅→该标的首条)")
    if lags:
        print(f"数据滞后  中位={statistics.median(lags):.0f}ms  "
              f"p95={pct(lags,95):.0f}ms  (now−data_time，抽样{len(lags)})")
    if covered:
        avg = total / covered
        print(f"更新频率  每标的均 {avg:.1f} 条/{elapsed:.0f}s ≈ 每 {elapsed/max(1e-9,avg):.1f}s 一跳")

    bad = []
    if total == 0:
        bad.append("采集窗口内 0 行情")
    if args.min_instruments and covered < args.min_instruments:
        bad.append(f"出数标的 {covered} < {args.min_instruments}")
    if args.fail_lag_ms and lags and pct(lags, 95) > args.fail_lag_ms:
        bad.append(f"p95 滞后 {pct(lags,95):.0f}ms > {args.fail_lag_ms:.0f}ms")
    print("\n[结论] " + ("✗ 不健康：" + "；".join(bad) if bad
                        else f"✓ 健康：'{spi.feed_source}' 全市场持续出数"))
    print("=" * 60)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
