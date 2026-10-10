========
变更记录
========

只记录会\ **改变已有代码行为**\ 的变更。

0.1.3（未发布）
===============

..  danger::

    **返回结果不再含服务端内部标识：**\ 证券只以 ``order_book_id`` 标识（契约 3.0.0，服务端 libfinanceserver v0.1.10 起）。

    - ``get_price``\ 、\ ``all_instruments``\ 、\ ``get_ex_factor``\ 、\ ``get_index_weights`` 去掉 ``permanent_id`` 列。
    - ``get_dividends`` / ``get_splits`` / ``get_allotments`` / ``get_spinoffs`` 去掉 ``permanent_id``\ 、\ ``event_id``\ 、
      ``confirmed_by_revision``\ ；\ ``get_spinoffs`` 另去掉 ``child_permanent_id``\ （子公司仍由 ``child_symbol`` 给出）。
    - ``instruments`` 返回的 ``Instrument`` 不再有 ``permanent_id``\ 、\ ``listing_id``\ 、\ ``identity_quality`` 属性；
      C++ 删除 ``Instrument::permanent_id()``\ 。
    - 用这些列做连接或去重的代码，改用 ``order_book_id``\ ；历史上的身份由 ``as_of`` 解析。

..  danger::

    **实时行情的标的只用 order_book_id：**\ 行情网关协议升到 v4，与旧网关不兼容（dynamics 协议 v4 起）。

    - ``Quote`` 与逐笔、盘口、深度记录、订阅回执（\ ``SubRsp``\ ）、缺口通知（\ ``SequenceGap``\ ）只有 ``order_book_id``
      一个标的字段，去掉 ``instrument_id``\ 、\ ``exchange_id``\ 、\ ``instrument_type``\ ；\ ``get_last_quotes`` 的快照同样。
    - C++ 的 ``order_book_id`` 由方法 ``order_book_id()`` 改为字段 ``order_book_id``\ 。
    - 需要品种时，用 :func:`~libfinance.instruments` 查 ``type``\ 。

0.1.2（2026-10-10）
===================

不改变已有代码的行为。新增日频因子接口 ``get_factor_exposure``\ 、``list_factor_libraries``\ 、``list_factors``\ （qlib、alpha158、Barra CNE5 / CNE6），需服务端 libfinanceserver v0.1.9 及以上。

0.1.1（2026-10-05）
===================

首个发布到 PyPI 的 0.1 版本（0.1.0 只打了标签，未发布）。以下是相对 PyPI 上 0.0.6 的变化。

..  danger::

    **实时订阅按统一的 order_book_id 订阅：**\ ``QuoteApi.subscribe(instruments, exchange_id, source="")`` →
    ``subscribe(order_book_ids, *, source="")``\ （\ ``unsubscribe`` 同）。

    - ``api.subscribe(["600519"], "XSHG")`` → ``api.subscribe(["600519.XSHG"])``\ ；一次可混合交易所。
    - ``source`` 只能按关键字传：旧写法第二个位置参数会报 ``TypeError``\ ，而不是被当成源名静默订错。
    - 后缀不是网关承接的交易所、或没有后缀的代码，在发出任何请求前报 ``ValueError``\ 。
    - 订阅回执、逐笔成交 / 委托 / 盘口 / 深度记录与缺口通知都有 ``order_book_id``\ 。
    - C++ 客户端新增同样的 ``libfinance::QuoteApi`` / ``QuoteSpi``\ （\ ``libfinance/quote_api.hpp``\ ）。

..  danger::

    **行业接口按新的行业数据族重写：**\ ``get_industry`` 与 ``get_industry_mapping`` 删除。

    - 行业以 ``order_book_id``\ （\ ``801780.SW``\ 、``10.GICS``\ ）命名；``source`` 是分类体系（\ ``SW``\ 、``GICS``\ ……）。
    - ``get_industry(industry, source, date, market)`` → ``get_industry_constituents(order_book_id, as_of=None)``\ 。
    - ``get_instrument_industry(order_book_ids, date, source="sw", level=1)`` →
      ``get_instrument_industry(order_book_ids, source=None, level=None, as_of=None)``\ ：省略 ``source`` / ``level`` 即全部；
      返回长表 ``order_book_id, related_order_book_id, source, market, level``\ ，不再是 ``first_industry_code`` 宽表。
    - 新增 ``get_industry_weights(order_book_id, as_of=None)``\ ，每行带 ``methodology``\ 。
    - 行业节点列表（原 ``get_industry_mapping``\ ）随跨类型的 ``all_instruments(type=...)`` 提供。

..  danger::

    **实时订阅（``libfinance.subscribe``）改用行情网关协议 v3，与旧网关不兼容。**

    - ``QuoteApi.login(user_id, password)`` 取消：\ **不需要登录**\ ，``connect()`` 自动向服务取行情票据
      （不登录按 IP 给基础额度），到期前自动续期；``login(token)`` 只在需要自己提供票据时使用。
    - ``connect()`` 不传地址时，网关地址由服务随票据给出；也可 ``connect("host:port,host:port")``\ 。
    - 行情回调多一个参数：``on_depth_market_data(quote, envelope)``\ ，``envelope`` 是网关的定序信封
      （序号与时间戳）；旧的单参数写法会报 ``TypeError``\ 。
    - ``LoginRsp`` 去掉 ``user_level``\ ，改为回显额度（``max_subscriptions``\ 、``sub_all``\ 、``expires_at_ms`` 等）。
    - 整市场订阅不再以"配额无限"判定，而看额度里是否含整市场订阅（否则 ``error_id=8``\ ）。
    - 新增：断线后按序号补发、``on_sequence_gap``\ 、``on_stream_status``\ 、``on_rsp_reauth``\ 、``on_session_closed``\ ，
      以及逐笔成交 / 委托 / 盘口 / 深度的回调。

0.0.6
=====

..  danger::

    **``get_price`` 的 ``adjust_type`` 默认值从 ``"none"`` 变为 ``"pre"``\ ，
    ``skip_suspended`` 从 ``True`` 变为 ``False``\ 。**

    这是一次\ **静默的数值变化**\ ：不报错，但不传 ``adjust_type`` 时拿到的价格从不复权
    变成了前复权。依赖旧行为的代码请显式写 ``adjust_type="none"``\ 。

    改动的原因是此前客户端与服务端的默认值相反——同一个语义的调用，走客户端和走服务端
    会得到不同的数字，而这种不一致从文档上看不出来。

其他变更：

..  list-table::
    :header-rows: 1
    :widths: 32 68

    *   - 变更
        - 说明
    *   - :func:`~libfinance.get_price_coverage` 支持 ``market`` 参数
        - 服务端同时绑定 CN 与 US 之后，不传 ``market`` 会报
          ``AmbiguousMarketError``\ 。现在默认 ``"cn"``\ ，并支持 ``"us"``
    *   - :func:`~libfinance.get_price` 的 ``frequency`` 校验
        - 不支持的频率此前\ **返回**\ 一个异常对象而不是抛出，导致调用方在后续操作里
          拿到无关的报错。现在正确抛出 ``ValueError``
    *   - :func:`~libfinance.get_index_weights` 的参数改名
        - ``index_id`` → ``index_code``
    *   - ``get_concept_weights``\ （已移除） 的参数改名
        - ``date`` → ``as_of``\ 。旧名仍可用，但会发 ``DeprecationWarning``——
          服务端把"知识截止时间"与"数据日期"分开了，两者含义不同，
          见 :doc:`../data/point_in_time`
    *   - :func:`~libfinance.get_instrument_industry` 的默认 ``source``
        - 从 ``"010303"`` 改为 ``"sw"``\ 。前者服务端不认，用默认参数调用一直是报错的
    *   - 日历查询越界
        - 超出 release 确认范围时抛 ``CalendarCoverageError``\ ，不再静默返回一个
          变短的结果；前后推 N 个交易日推到边界外时同样报错，不再返回端点

0.0.2
=====

见上面 0.0.6 中关于 ``adjust_type`` 的说明——该变更自 0.0.2 起生效。
