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

