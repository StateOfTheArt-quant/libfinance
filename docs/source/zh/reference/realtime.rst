6 实时行情
========================================

.. currentmodule:: libfinance

快照查询返回一次请求的最新报价，订阅接口持续接收推送。
两者不能替代历史日线或分钟线。行情字段见 :doc:`../data/realtime`。

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
      - 连接、登录、发现行情源并订阅或退订
    * - :class:`~libfinance.subscribe.quote_api.QuoteSpi`
      - 通过回调处理连接状态、订阅回执与报价
    * - :class:`~libfinance.subscribe.md_protocol.Quote`
      - 读取推送中的证券代码、价格和盘口字段

get_last_quotes — 一次查询单只或多只证券的最新快照
--------------------------------------------------------------------

.. autofunction:: get_last_quotes

**示例**

以下按顺序执行，代码后的打印内容为**输出示意**：展示返回结构与参数差异，
并非本次服务实测；数值、编号和事件不作为真实数据使用，省略号表示未展示部分。

.. literalinclude:: ../../../../example/last_quote.py
    :language: python
    :start-after: # [get_last_quotes.1]
    :end-before: # [/get_last_quotes.1]
    :prepend: from libfinance import get_last_quotes

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_last_quotes.1.txt
    :language: text

.. literalinclude:: ../../../../example/last_quote.py
    :language: python
    :start-after: # [get_last_quotes.2]
    :end-before: # [/get_last_quotes.2]

打印结果（示意）：

.. literalinclude:: ../../../_shared/example_outputs/get_last_quotes.2.txt
    :language: text

结果解读：第一段展示代码到 Quote 的字典；第二段读取具体属性，并处理 None（暂无快照）。

:download:`下载完整示例 <../../../../example/last_quote.py>`

QuoteApi / QuoteSpi — 持续订阅
----------------------------------------------------

登录成功后发起订阅，在 ``on_depth_market_data`` 中接收报价。
``subscribe(["600519"], "XSHG")`` 将代码与交易所分开传递；
省略 ``source`` 自动选源，指定 ``source`` 则定向订阅。
完整示例包含登录回调、行情源发现和退出清理，见 :doc:`../howto/subscribe`。

.. list-table::
    :header-rows: 1

    * - 方法
      - 解决的问题
    * - ``connect`` / ``login`` / ``register_spi``
      - 建立连接、登录并注册回调处理器
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

:download:`下载完整订阅示例 <../../../../example/subscription/python/live_subscribe_example.py>`
