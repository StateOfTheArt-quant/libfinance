6 实时行情
========================================

.. currentmodule:: libfinance

快照查询返回一次请求的最新报价，订阅接口持续接收推送。
两者不能替代历史日线或分钟线。行情字段见 :doc:`../data/realtime`\ 。

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :func:`~libfinance.get_last_quotes`
      - 一次查询单只或多只证券的最新快照

.. list-table::
    :header-rows: 1
    :widths: 40 60

    * - 函数 / 类
      - 解决的问题
    * - :class:`~libfinance.subscribe.quote_api.QuoteApi`
      - 连接、发现行情源并订阅或退订（无需登录）
    * - :class:`~libfinance.subscribe.quote_api.QuoteSpi`
      - 通过回调处理连接状态、订阅回执与报价
    * - :class:`~libfinance.subscribe.md_protocol.Quote`
      - 读取推送中的证券代码、价格和盘口字段

行情源
------

订阅推送有两个行情源：

.. list-table::
    :header-rows: 1
    :widths: 16 54 30

    * - 源
      - 内容
      - 怎样使用
    * - ``webquote``
      - A 股实时行情（上交所、深交所），交易时段推送
      - 订阅时不指定 ``source``\ ，自动使用
    * - ``sim``
      - 模拟行情，7×24 小时推送，便于在非交易时段开发、联调与测试；报价为模拟生成，不代表真实市场
      - 订阅时指定 ``source="sim"``

``query_sources()`` 列出当前可用的源及其状态。

.. note::

    如果你有免费、质量更好的实时行情源可以提供给社区，欢迎联系我们（\ `GitHub Issue
    <https://github.com/StateOfTheArt-quant/libfinance/issues>`_\ ）。

最小示例
--------

订阅一只股票，在回调里计算订阅以来的涨跌幅和买卖价差：

.. code-block:: python

    from libfinance.subscribe.quote_api import QuoteApi, QuoteSpi


    class Monitor(QuoteSpi):
        def __init__(self, api):
            self.api = api
            self.first = {}                                    # 每只证券收到的第一个价格

        def on_rsp_login(self, rsp, _):                        # 登录成功后订阅；断线重连后会再次触发
            if rsp.error_id == 0:
                self.api.subscribe(["600519.XSHG"], source="sim")   # 交易时段去掉 source，用实时行情

        def on_depth_market_data(self, q, _):                  # 每条报价到达时调用
            first = self.first.setdefault(q.order_book_id, q.last_price)
            change = q.last_price / first - 1
            spread = q.ask_price[0] - q.bid_price[0]
            print(f"{q.order_book_id}  last={q.last_price:.2f}  订阅以来={change:+.2%}  价差={spread:.2f}")


    api = QuoteApi()
    api.register_spi(Monitor(api))
    api.connect()                                              # 无需登录：自动取票据，到期自动续期
    input("回车退出\n")
    api.disconnect()

.. code-block:: text

    600519.XSHG  last=113.37  订阅以来=+0.00%  价差=0.02
    600519.XSHG  last=113.59  订阅以来=+0.20%  价差=0.02
    600519.XSHG  last=113.42  订阅以来=+0.04%  价差=0.02
    600519.XSHG  last=113.02  订阅以来=-0.31%  价差=0.02

回调在 SDK 的接收线程里执行，应当很快返回；耗时的计算放到自己的线程或队列里。

get_last_quotes — 一次查询单只或多只证券的最新快照
--------------------------------------------------------------------

.. autofunction:: get_last_quotes

QuoteApi / QuoteSpi — 持续订阅
----------------------------------------------------

``connect()`` 即可：不必登录，SDK 自动向服务取行情票据（不登录按 IP 额度）、到期前自动续期。
登录成功（``on_rsp_login``）后发起订阅，在 ``on_depth_market_data(quote, envelope)`` 中接收报价。
``subscribe(["600519.XSHG", "000001.XSHE"])`` 传统一的 order_book_id，可混合交易所；
省略 ``source`` 自动选源，指定 ``source`` 则定向订阅。
完整示例包含登录回调、行情源发现和退出清理，见 :doc:`../howto/subscribe`\ ；C++ 客户端有同样的
``libfinance::QuoteApi`` / ``QuoteSpi``\ （\ ``example/cpp/12_live_subscription.cpp``\ ）。

.. list-table::
    :header-rows: 1

    * - 方法
      - 解决的问题
    * - ``connect`` / ``register_spi``
      - 建立连接（自动取票据登录）并注册回调处理器
    * - ``login``
      - 可选：自己提供票据（字符串或返回票据的函数）
    * - ``query_sources``
      - 查询可用行情源及其状态
    * - ``subscribe`` / ``unsubscribe``
      - 订阅或取消指定证券
    * - ``subscribe_all`` / ``unsubscribe_all``
      - 订阅整市场或取消全部订阅
    * - ``disconnect``
      - 结束连接并释放资源

.. autoclass:: libfinance.subscribe.quote_api.QuoteApi
    :members: connect, login, subscribe, unsubscribe, subscribe_all,
              unsubscribe_all, query_sources, disconnect, register_spi

.. autoclass:: libfinance.subscribe.quote_api.QuoteSpi
    :members:

.. autoclass:: libfinance.subscribe.md_protocol.Quote

