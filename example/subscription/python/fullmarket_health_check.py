#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fullmarket_health_check.py —— 实时行情源「全市场」体检

对某个行情源做【全市场订阅】(subscribe_all)，统计覆盖（出数标的数）、吞吐、
延迟/新鲜度，判断该源是否健康。

走 subscribe_all：网关让源端走全量推送（如 webquote→yunhq 全沪深 ~5289 只），
**客户端不枚举任何代码** —— 因此覆盖即真实全市场、不含空号（旧版按代码段位生成
11000 含大量空号的问题不复存在）。

用法:
    python fullmarket_health_check.py --source webquote \\
        --user admin --password 'AdminPass123!' --duration 20

退出码: 0=健康, 1=不健康(0行情 / 出数标的<--min-instruments / p95滞后超阈值), 2=连接或登录失败
"""
import argparse
import signal
import statistics
import sys
import threading
import time

from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi


class HealthSpi(QuoteSpi):
    def __init__(self):
        self.lock = threading.Lock()
        self.logged_in = threading.Event()
        self.login_ok = False
        self.sub_ok = False
        self.sub_err = ""
        self.first = {}       # "exch.inst" -> 首条到达 wall 时间
        self.first_dt = {}    # "exch.inst" -> 首条 data_time（算新鲜度）
        self.total = 0

    def on_rsp_login(self, rsp, _):
        self.login_ok = (rsp.error_id == 0)
        mx = "unlimited" if rsp.max_subscriptions < 0 else rsp.max_subscriptions
        print(f"[health] login {'OK' if self.login_ok else 'FAIL'} "
              f"level={rsp.user_level} max_subs={mx} "
              f"{'' if self.login_ok else rsp.error_msg}")
        self.logged_in.set()

    def on_rsp_subscribe(self, rsp, _):   # subscribe_all 的应答也走这里
        self.sub_ok = (rsp.error_id == 0)
        self.sub_err = rsp.error_msg

    def on_depth_market_data(self, q):
        now = time.time()
        key = f"{q.exchange_id}.{q.instrument_id}"
        with self.lock:
            self.total += 1
            if key not in self.first:
                self.first[key] = now
                self.first_dt[key] = q.data_time


def lag_ms(data_time, wall):
    """kungfu data_time 多为 ns epoch；解析为 now-data_time(ms)，无法判定返回 None。"""
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
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9001)
    ap.add_argument("--source", required=True, help="行情源名 sim/webquote/...")
    ap.add_argument("--user", default="", help="登录账户（subscribe_all 需登录的高配额账户）")
    ap.add_argument("--password", default="")
    ap.add_argument("--duration", type=int, default=20, help="采集时长(秒)")
    ap.add_argument("--min-instruments", type=int, default=0,
                    help="出数标的少于此值判不健康，0=不判")
    ap.add_argument("--fail-lag-ms", type=float, default=0.0,
                    help="p95 数据滞后超此(ms)判不健康，0=不判")
    args = ap.parse_args()

    spi = HealthSpi()
    api = QuoteApi()
    api.register_spi(spi)
    if api.connect(args.host, args.port) != 0:
        print("[health] connect failed", file=sys.stderr)
        return 2
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())

    if args.user:
        api.login(args.user, args.password)
        spi.logged_in.wait(timeout=5)
        if not spi.login_ok:
            api.disconnect()
            return 2
    else:
        print("[health][warn] 未登录(guest)：subscribe_all 需登录账户，可能被拒")

    # 全市场订阅：一条 subscribe_all，网关让源端走全量推送（不枚举代码、无空号）
    print(f"[health] subscribe_all(source={args.source})，采集 {args.duration}s ...")
    t_sub = time.time()
    api.subscribe_all(args.source)

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
        print(f"[health] subscribe_all 应答: {spi.sub_err or '(未收到)'}", file=sys.stderr)

    print("\n" + "=" * 60)
    print(f"实时源体检  source={args.source}  {args.host}:{args.port}")
    print("=" * 60)
    print(f"覆盖      出数标的={covered}（subscribe_all 全市场，无空号）")
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
                        else "✓ 健康：该源全市场持续出数"))
    print("=" * 60)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
