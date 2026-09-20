========
变更记录
========

只记录会\ **改变已有代码行为**\ 的变更。

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
    *   - :func:`~libfinance.get_concept_weights` 的参数改名
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
