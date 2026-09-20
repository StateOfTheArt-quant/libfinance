========
实时行情
========

实时行情有两条路径，用途不同：

..  list-table::
    :header-rows: 1
    :widths: 22 26 52

    *   - 方式
        - 入口
        - 什么时候用
    *   - 快照查询
        - :func:`~libfinance.get_last_quotes`
        - 偶尔问一次"现在什么价"。一次请求一个回答
    *   - 订阅推送
        - :class:`~libfinance.subscribe.quote_api.QuoteApi`
        - 持续接收行情。有变化就推给你

两条路径是\ **独立的**\ ：订阅走行情网关，用的是另一个地址和端口，和
:func:`~libfinance.init_client` 连的那个服务不是一回事。它们只是共用同一个
:class:`~libfinance.subscribe.md_protocol.Quote` 数据类型。

快照查询
========

..  code-block:: python

    >>> from libfinance import get_last_quotes
    >>> get_last_quotes(["600000.XSHG"])
    {'600000.XSHG': Quote(...)}

返回一个字典，键是代码。

..  note::

    某个代码\ **当前没有可用快照**\ 时，它的值是 ``None``\ （比如非交易时段，或者这个部署
    没有接实时源）：

    ..  code-block:: python

        >>> get_last_quotes(["600000.XSHG"])
        {'600000.XSHG': None}

    所以用之前先判空，不要直接 ``.last_price``\ 。

订阅推送
========

订阅是\ **回调式**\ 的：你实现一个回调类，注册进去，行情到了会调用你的方法。

..  code-block:: python

    from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi

    class MySpi(QuoteSpi):
        def on_rsp_login(self, rsp, request_id):
            if rsp.error_id == 0:
                # 订阅写在这里，不要写在 main 里 —— 见下面的说明
                api.subscribe(["600519"], "XSHG")

        def on_depth_market_data(self, quote):
            print(quote.order_book_id, quote.last_price)

    api = QuoteApi()
    api.register_spi(MySpi())
    api.connect("行情网关地址", 9001)
    api.login("user", "password")

..  important::

    **订阅要写在 ``on_rsp_login`` 里。**

    网关断线后客户端会自动重连并重新登录，登录成功会再次触发 ``on_rsp_login``——
    订阅写在这里，重连后会自动重放。写在主流程里的话，断线重连之后订阅就悄悄没了，
    程序还在跑，只是再也收不到数据。

    这是这套订阅接口约定的用法，不是可选的风格问题。

订阅的两种模式
--------------

..  list-table::
    :header-rows: 1
    :widths: 24 76

    *   - 模式
        - 行为
    *   - 不指定 ``source``
        - 网关按健康状况和优先级自动选源，源掉线自动切换到备用源
    *   - 指定 ``source``
        - 只接收该源的数据，不自动切换；该源不可用时明确失败

同一个合约在网关侧只有一条路由，\ **不能同时混用两种模式**\ ，冲突的请求会在
``on_rsp_subscribe`` 里明确失败。

行情帧本身不带来源信息。要知道数据来自哪个源，看订阅回执的 ``rsp.source``\ ，或者用
``query_sources()`` 查源目录。

``Quote`` 有哪些字段
====================

..  list-table::
    :header-rows: 1
    :widths: 34 66

    *   - 字段
        - 含义
    *   - ``order_book_id``
        - 代码（只读属性，由 ``instrument_id`` 和 ``exchange_id`` 拼成）
    *   - ``data_time``
        - 行情时间戳
    *   - ``last_price``
        - 最新价
    *   - ``open_price`` / ``high_price`` / ``low_price`` / ``close_price``
        - 今开、最高、最低、收盘
    *   - ``pre_close_price``
        - 昨收
    *   - ``volume`` / ``turnover``
        - 成交量、成交额
    *   - ``upper_limit_price`` / ``lower_limit_price``
        - 涨停价、跌停价
    *   - ``bid_price`` / ``ask_price``
        - 买十档、卖十档价格，均为长度 10 的列表
    *   - ``bid_volume`` / ``ask_volume``
        - 对应档位的量
    *   - ``total_bid_volume`` / ``total_ask_volume``
        - 委买、委卖总量
    *   - ``total_trade_num``
        - 成交笔数
    *   - ``trading_phase_code``
        - 交易阶段
    *   - ``open_interest`` / ``pre_open_interest`` / ``settlement_price`` / ``iopv``
        - 期货与基金相关字段，股票上通常为 0

..  warning::

    回调是在后台的接收线程里执行的。\ **不要在回调里做耗时操作**——那会阻塞整条行情流。
    重活扔进队列，交给另一个线程处理。

可直接运行的完整示例见 :doc:`../howto/subscribe`\ 。
