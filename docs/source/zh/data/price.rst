==============
行情与复权
==============

:func:`~libfinance.get_price` 取日频行情。这一章要讲清楚一件事：**你拿到的价格，
多数情况下不是当天的真实成交价。**

..  code-block:: python

    >>> from libfinance import get_price
    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")

..  code-block:: text

                              open      high       low     close        volume      turnover
    order_book_id datetime
    000001.XSHE   2024-03-01  8.897049  8.905450  8.762627  8.813035  2.175959e+08  1.917689e+09
                  2024-03-04  8.779430  8.821436  8.670212  8.678613  1.971024e+08  1.719563e+09
                  2024-03-05  8.653409  8.796232  8.619804  8.762627  2.163123e+08  1.889144e+09
                  2024-03-06  8.737423  8.779430  8.678613  8.678613  1.601692e+08  1.396940e+09

返回值的索引是 ``(order_book_id, datetime)`` 两层。

字段
====

..  list-table::
    :header-rows: 1
    :widths: 20 80

    *   - 字段
        - 含义
    *   - ``open`` / ``high`` / ``low`` / ``close``
        - 开盘、最高、最低、收盘价
    *   - ``volume``
        - 成交量（股）
    *   - ``turnover``
        - 成交额（元）
    *   - ``limit_up`` / ``limit_down``
        - 当日涨停价、跌停价（A 股有，美股为 ``NaN``\ ）

不传 ``fields`` 就返回全部；传了就只返回指定的几列：

..  code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", fields=["close", "volume"])

复权：这一节决定你的数字对不对
==============================

一只股票分红、送股之后，价格会在除权当天出现一个\ **跳空**——那不是跌，是每股对应的
权益变少了。直接拿未复权价算收益率，会把这个跳空算成一次下跌。

复权就是用一个因子把历史价格拉到同一个尺度上，让收益率连续。

三种取值
--------

..  list-table::
    :header-rows: 1
    :widths: 14 20 66

    *   - 取值
        - 叫法
        - 什么时候用
    *   - ``"pre"``
        - 前复权（\ **默认**\ ）
        - 算收益率、画连续的价格曲线、做因子研究。以最近的价格为基准，历史价格被调整。
    *   - ``"none"``
        - 不复权
        - 要历史上\ **真实的成交价**\ ：复盘当时的盘面、核对涨跌停、按当时价格计算手续费。
    *   - ``"post"``
        - 后复权
        - 以最早的价格为基准往后累乘。做长期净值曲线时用。

看一眼差别有多大
----------------

同一只股票、同一天，两种口径：

..  code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")["close"]              # 默认 pre
    8.813035
    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06",
    ...           adjust_type="none")["close"]                                        # 不复权
    10.49

差 16%。\ **不会有任何报错或警告**——所以如果你以为自己拿到的是当时的成交价，从这里开始
后面每一个数字都是错的。

..  danger::

    ``adjust_type`` 的默认值在 **0.0.2** 从 ``"none"`` 改成了 ``"pre"``\ 。

    这是一次\ **静默的数值变化**\ ：升级后同一段代码不会报错，但拿到的价格从不复权变成了
    前复权。依赖旧行为的代码请显式写 ``adjust_type="none"``\ 。

成交量也被复权，成交额不被
--------------------------

这一条最容易漏。前复权把价格调\ **低\ **\ ，那么同一笔成交对应的股数就要相应调\ **高**\ ，
否则 ``价 × 量`` 就不等于当时真实的成交金额了。

用上面那组数据验证：

..  code-block:: python

    >>> pre  = get_price(["000001.XSHE"], "2024-03-01", "2024-03-06")
    >>> none = get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", adjust_type="none")

    >>> (pre["close"] * pre["volume"] - none["close"] * none["volume"]).abs().max()
    0.005468130111694336          # 价 x 量 守恒（差的是浮点误差）

    >>> (pre["turnover"] == none["turnover"]).all()
    True                          # 成交额本来就是金额，不参与复权

所以：

* 要算\ **成交金额**\ ，直接用 ``turnover``\ ，不要用 ``close * volume``\ ；
* 要比较\ **不同日期的成交量**\ ，注意复权口径下的 ``volume`` 已经被缩放过。

后复权可能被拒绝
----------------

后复权需要从最早的基准日开始累乘因子。如果历史上有某次公司行动\ **没有对应的因子**\ ，
那么跨过它的累乘结果会整体差一个常数——这时服务端宁可拒绝，也不给一个偏掉的数：

..  code-block:: python

    >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-06", adjust_type="post")
    RpcError: ... has 11 corporate action(s) with no factor in this release at
    1991-05-02, 1991-08-17, 1992-03-23, ...; a cumulative factor spanning them
    would be wrong by a constant. Ask from base_date=1999-10-18 onward, ...

报错信息里会给出\ **从哪一天起是安全的**\ 。换一只没有这个问题的票则正常：

..  code-block:: python

    >>> get_price(["600000.XSHG"], "2024-03-01", "2024-03-06", adjust_type="post")["close"]
    110.531242

停牌
====

停牌日在原始数据里成交量为 0。\ ``skip_suspended=True`` 会把这些日子从结果里去掉：

..  code-block:: python

    >>> get_price(ids, start, end, skip_suspended=True)

默认是 ``False``\ ，即保留停牌日。做面板对齐时保留更方便（每只票的日期轴一致）；
算换手率之类的指标时要注意把 0 成交量的日子排除掉。

已知边界
========

..  warning::

    **只有日频。** ``frequency`` 目前只有 ``"1d"`` 可用。其余取值会被明确拒绝，
    不会静默降级：

    ..  code-block:: python

        >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-29", frequency="5d")
        RpcError: frequency='5d' 不支持；上游目前只有日频 artifact，可选 ['1d']

        >>> get_price(["000001.XSHE"], "2024-03-01", "2024-03-29", frequency="1m")
        ValueError: frequency: 目前只支持日频 '1d'，收到 '1m'

..  warning::

    **指数不能用这个接口取行情。\ ** 传一个指数代码进去会返回一张\ **\ 空表**，而且没有任何
    警告：

    ..  code-block:: python

        >>> get_price(["000300.XSHG"], "2024-03-01", "2024-03-08").shape
        (0, 0)

    拿到空表时先确认传的是不是股票代码。指数成分与权重用
    :func:`~libfinance.get_index_weights`\ ，见 :doc:`universe`\ 。

..  note::

    ``include_now`` 这个参数在日频下\ **不起作用**\ ，保留它只是为了签名兼容。

美股
====

同一个函数，代码换成 ``.US`` 后缀即可，不需要额外参数：

..  code-block:: python

    >>> get_price(["AAPL.US"], "2026-03-02", "2026-03-06")[["close", "volume"]]

美股没有涨跌停，\ ``limit_up`` / ``limit_down`` 与 ``turnover`` 返回 ``NaN``\ 。
更多差异见 :doc:`../howto/us_market`\ 。

下一步
======

知道了怎么取，还要知道\ **能取到哪一天**——见 :doc:`freshness`\ 。
