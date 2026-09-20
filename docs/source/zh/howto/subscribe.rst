================
接收实时行情
================

**目标**\ ：连上行情网关，订阅几只股票，持续接收推送。

订阅是回调式的：你写一个回调类，行情到了会调用你的方法。

..  note::

    订阅走的是\ **行情网关**\ ，地址和端口与 :func:`~libfinance.init_client` 连的那个服务
    不同。要先向管理员确认网关地址和账号。

完整可运行示例
==============

..  code-block:: python

    import signal
    import threading

    from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

    INSTRUMENTS = ["600519"]      # 注意：这里不带 .XSHG 后缀
    EXCHANGE = "XSHG"

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())


    class DemoSpi(QuoteSpi):
        def __init__(self, api):
            self.api = api
            self.count = 0

        def on_connected(self):
            print("[client] connected")

        def on_disconnected(self, reason):
            print("[client] disconnected reason=%s，等待自动重连…" % reason)

        def on_rsp_login(self, rsp, request_id):
            if rsp.error_id != 0:
                print("[client] login FAIL:", rsp.error_msg)
                stop.set()
                return
            print("[client] login OK")
            # 订阅必须写在这里 —— 断线重连后会再次触发，订阅随之重放
            self.api.subscribe(INSTRUMENTS, EXCHANGE)

        def on_rsp_subscribe(self, rsp, request_id):
            if rsp.error_id != 0:
                print("[client] subscribe FAIL:", rsp.error_msg)
            else:
                print("[client] subscribed, source=%s" % rsp.source)

        def on_depth_market_data(self, quote):
            self.count += 1
            print("%s  last=%.2f  volume=%s" % (
                quote.order_book_id, quote.last_price, quote.volume))


    api = QuoteApi()
    api.register_spi(DemoSpi(api))
    api.connect("网关地址", 9001)
    api.login("your-name", "your-password")

    stop.wait()
    api.disconnect()

三个必须知道的点
================

订阅写在 ``on_rsp_login`` 里
----------------------------

..  important::

    这不是风格问题。网关断线后客户端会自动重连并重新登录，登录成功再次触发
    ``on_rsp_login``——订阅写在这里才会被重放。

    写在主流程里的话，断线重连之后订阅就没了：**程序还在跑，日志也正常，就是再也收不到
    行情**。这是最难发现的一类故障。

代码不带后缀
------------

``subscribe()`` 的第一个参数是\ **不带后缀**\ 的代码，交易所通过第二个参数给：

..  code-block:: python

    api.subscribe(["600519"], "XSHG")      # 对
    api.subscribe(["600519.XSHG"], ...)    # 错

回调里收到的 ``quote.order_book_id`` 则是拼好的完整代码。

回调里不要做重活
----------------

..  warning::

    回调在后台接收线程里执行。在回调里落库、画图、跑模型会阻塞整条行情流。
    把数据扔进 ``queue.Queue``\ ，交给另一个线程处理。

选源
====

..  list-table::
    :header-rows: 1
    :widths: 30 70

    *   - 写法
        - 行为
    *   - ``api.subscribe(ids, "XSHG")``
        - 网关自动选源，源掉线自动切到备用源
    *   - ``api.subscribe(ids, "XSHG", source="sim")``
        - 只收这个源，不自动切换；该源不可用时明确失败

同一个合约在网关侧只有一条路由，\ **不能两种混用**\ ，冲突请求会在 ``on_rsp_subscribe``
里失败（\ ``error_id=5``\ ）。

想知道有哪些源：

..  code-block:: python

    def on_rsp_query_sources(self, sources, request_id):
        for s in sources:
            print(s.source, "健康" if s.health else "掉线",
                  "整市场" if s.whole_market else "部分")

    api.query_sources()

常见错误码
==========

..  list-table::
    :header-rows: 1
    :widths: 16 84

    *   - ``error_id``
        - 含义
    *   - 4
        - 没有可用的源
    *   - 5
        - 路由冲突，或指定的源不可用
    *   - 6
        - 订阅配额受限

整市场订阅
==========

一次订下"市场 × 品种 × 数据类型"命中的全部合约：

..  code-block:: python

    from libfinance.subscribe.md_protocol import (
        MarketType, SubscribeInstrumentType, SubscribeDataType)

    api.subscribe_all(market=MarketType.SSE,
                      instrument_type=SubscribeInstrumentType.Stock,
                      data_type=SubscribeDataType.Snapshot)

任一维度传 ``All`` 表示不限。这要求账号的订阅配额无限制，否则返回 ``error_id=6``\ 。

只想问一次当前价
================

不需要持续推送的话，用快照查询更简单：

..  code-block:: python

    >>> from libfinance import get_last_quotes
    >>> get_last_quotes(["600000.XSHG"])
    {'600000.XSHG': None}

值为 ``None`` 表示当前没有可用快照（非交易时段，或这个部署没接实时源），
用之前先判空。

字段说明见 :doc:`../data/realtime`\ 。
