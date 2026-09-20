========
问题排查
========

按\ **症状**\ 编排：你看到什么现象，就从哪一行开始。

拿到空表
========

空表最麻烦，因为它不告诉你原因。按可能性从高到低排查：

..  list-table::
    :header-rows: 1
    :widths: 30 34 36

    *   - 可能原因
        - 怎么确认
        - 怎么修
    *   - 传的是\ **指数**\ 代码
        - ``instruments(代码).type`` 是不是 ``INDX``
        - :func:`~libfinance.get_price` 只出股票行情。指数成分用
          :func:`~libfinance.get_index_weights`
    *   - 概念 id 不存在
        - 看有没有 "未知的 concept_id" 警告
        - 从 :func:`~libfinance.get_concept_meta` 里取 id，别写死
    *   - 区间内该股票没有交易
        - 用 :func:`~libfinance.instruments` 查 ``listed_date`` /
          ``de_listed_date``
        - 换一个区间
    *   - 超出了可查的历史区间
        - 看有没有"可查区间起点是…"的警告
        - 把 ``start_date`` 调到警告给出的边界之内，见
          :doc:`../getting_started/connect`
    *   - 这个市场没有这类数据
        - 换成明确支持的市场试一次
        - 见 :doc:`us_market` 的可用性表

..  tip::

    **空表 vs 报错**\ ：这套接口尽量让"数据没有"报错、让"确实没有事件"返回空表。
    所以拿到空表时，先倾向于认为"查询本身是成功的，只是这段区间真的没有内容"。

数字和预期对不上
================

..  list-table::
    :header-rows: 1
    :widths: 32 68

    *   - 现象
        - 原因
    *   - 收盘价比行情软件低一截
        - 默认是\ **前复权**\ 价。要真实成交价传 ``adjust_type="none"``\ ，
          见 :doc:`../data/price`
    *   - 成交量和行情软件对不上
        - 成交量也参与复权。用 ``adjust_type="none"`` 对照
    *   - ``close * volume`` 不等于成交额
        - 直接用 ``turnover`` 列
    *   - 某天"暴跌"但查不到消息
        - 查一下那天是不是除权日：\ :func:`~libfinance.get_dividends`\ ，
          见 :doc:`../data/corporate_actions`
    *   - 回测收益率高得离谱
        - 先怀疑前视偏差：财务数据有没有传 ``as_of``\ ，股票池有没有传 ``date``\ ，
          见 :doc:`pit_backtest`
    *   - 财务数字和年报原文不一致
        - 可能取到了修订版。看 ``info_date`` 和 ``if_adjusted``

常见报错怎么读
==============

..  list-table::
    :header-rows: 1
    :widths: 42 58

    *   - 报错
        - 含义与处理
    *   - ``Client auto-connect to ... failed``
        - 还没连上服务。在第一次取数\ **之前**\ 调
          :func:`~libfinance.init_client`\ ，见 :doc:`../getting_started/connect`
    *   - ``... is outside coverage ...; a date this release does not reach is
          not a date with no trading``
        - ``end_date`` 超出了行情覆盖。用
          :func:`~libfinance.get_price_coverage` 查上界，见 :doc:`../data/freshness`
    *   - ``CalendarCoverageError: ... 超出 release 确认范围``
        - 问到了日历还没确认的日期。用
          :func:`~libfinance.get_calendar_coverage` 查区间
    *   - ``order_book_ids: at least one valid instrument expected``
        - 传入的代码一个都没解析出来。往上看有没有
          "invalid order_book_id" 警告，多半是代码拼写或后缀问题
    *   - ``frequency='5d' 不支持；上游目前只有日频 artifact``
        - 目前只有日频。用 ``frequency="1d"``
    *   - ``has N corporate action(s) with no factor in this release``
        - 后复权跨过了无法定价的历史事件。报错里给了安全的起始日期，按它重取
    *   - ``命名空间 'xxx' 没有 market='us' 的 provider``
        - 这个接口在该市场没有数据，见 :doc:`us_market`
    *   - ``AmbiguousMarketError: ... 绑定了多个市场``
        - 需要显式传 ``market=``
    *   - ``RpcError(code=1201)`` / ``(code=1202)``
        - 服务端拒绝了这次调用的权限，联系服务管理员
    *   - ``Array type doesn't match type of values set``
        - 服务端内部错误。多数出现在对不支持的市场调财务接口时

返回了 ``None``
===============

..  list-table::
    :header-rows: 1
    :widths: 40 60

    *   - 场景
        - 原因
    *   - ``instruments("600000")`` 返回 ``None``
        - 代码少了后缀。应为 ``"600000.XSHG"``
    *   - ``instruments(已退市代码)`` 返回 ``None``
        - 按今天的证券表查不到。传 ``date=`` 按历史日期查，
          见 :doc:`../data/instruments`
    *   - ``get_last_quotes`` 的值是 ``None``
        - 当前没有可用快照（非交易时段，或未接实时源）

订阅收不到行情
==============

..  list-table::
    :header-rows: 1
    :widths: 36 64

    *   - 检查
        - 说明
    *   - 订阅写在 ``on_rsp_login`` 里了吗
        - 写在别处的话，断线重连后订阅会丢失，且\ **没有任何报错**
    *   - ``on_rsp_subscribe`` 的 ``error_id``
        - 4 无可用源、5 路由冲突、6 配额受限
    *   - 代码带后缀了吗
        - ``subscribe()`` 要不带后缀的代码，交易所单独传
    *   - 回调里有没有阻塞操作
        - 回调在接收线程里跑，重活会卡住整条流

见 :doc:`subscribe`\ 。

还是没解决
==========

把下面这些信息一起带上，比只说"取不到数据"有用得多：

..  code-block:: python

    import libfinance
    from libfinance import get_calendar_coverage, get_price_coverage

    print("版本:", libfinance.__version__)
    print("日历覆盖:", get_calendar_coverage())
    print("行情覆盖:", get_price_coverage())
    # 再贴上你的完整调用与完整报错（含警告）
