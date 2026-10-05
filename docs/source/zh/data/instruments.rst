================
证券代码与主数据
================

所有取数函数都要你先说清楚\ **查哪只证券**\ 。这一章讲代码怎么写、名称从哪来，以及一个
很容易踩的坑：查历史区间时，已退市的证券能不能被认出来。

代码怎么写
==========

代码的形式是 ``<交易所代码>.<市场后缀>``\ ：

..  list-table::
    :header-rows: 1
    :widths: 40 22 38

    *   - 市场
        - 后缀
        - 例子
    *   - 上海证券交易所
        - ``.XSHG``
        - ``600000.XSHG``
    *   - 深圳证券交易所
        - ``.XSHE``
        - ``000001.XSHE``
    *   - 美股
        - ``.US``
        - ``AAPL.US``

后缀不能省。同一串数字在两个交易所可能都存在——``000001.XSHG`` 是上证指数，
``000001.XSHE`` 是平安银行，靠后缀区分。

..  warning::

    代码写得不完整时，\ :func:`~libfinance.instruments` 返回 ``None``\ ，\ **不报错**\ ：

    ..  code-block:: python

        >>> instruments("600000")      # 少了后缀
        None

    所以拿到 ``None`` 先检查代码拼写，而不是以为这只证券不存在。

``order_book_id`` 是代码，\ ``symbol`` 是名称
=============================================

这两个词容易记反，记住这一条就行：

..  code-block:: python

    >>> from libfinance import instruments
    >>> ins = instruments("600000.XSHG")
    >>> ins.order_book_id
    '600000.XSHG'
    >>> ins.symbol
    '浦发银行'

单个代码返回一个 :class:`~libfinance.api.instrument.Instrument` 对象，代码列表返回
对象列表：

..  code-block:: python

    >>> instruments(["000001.XSHE", "000300.XSHG"])
    [Instrument(order_book_id='000001.XSHE', symbol='平安银行', type='CS',
                market='cn', listed_date='1991-04-03T00:00:00.000'),
     Instrument(order_book_id='000300.XSHG', symbol='沪深300', type='INDX',
                market='cn')]

查不到的代码会被\ **跳过**\ ，不会在列表里留一个占位——所以返回列表的长度可能比你传进去的
少。需要一一对应的话，自己按 ``order_book_id`` 建字典。

全市场列表
==========

:func:`~libfinance.all_instruments` 给出全部证券：

..  code-block:: python

    >>> from libfinance import all_instruments
    >>> df = all_instruments(type="CS")
    >>> df.shape
    (10616, 6)
    >>> df.head(3)
      order_book_id symbol type market              listed_date  de_listed_date
    0   000001.XSHE   平安银行   CS     cn  1991-04-03T00:00:00.000             NaN
    1   000002.XSHE  万  科Ａ   CS     cn  1991-01-29T00:00:00.000             NaN
    2   000006.XSHE   深振业Ａ   CS     cn  1992-04-27T00:00:00.000             NaN

``type`` 的取值：

..  list-table::
    :header-rows: 1
    :widths: 24 24 52

    *   - ``type``
        - 别名
        - 含义
    *   - ``CS``
        - ``STOCK``
        - 股票
    *   - ``INDX``
        - ``INDEX``
        - 指数

美股传 ``market="us"``\ ：

..  code-block:: python

    >>> us = all_instruments(market="us")
    >>> us[us["type"] == "CS"].head()

..  note::

    这张表有一万多行、体积不小，所以客户端会缓存它，并在服务端数据更新时自动失效。
    你不需要自己缓存，反复调用是廉价的。

已退市的证券
============

这是最容易栽的一处。

**现象**\ ：查一只已经退市的股票在它还在交易时的行情，返回的却是"无效代码"。

**原因\ **\ ：代码要先被解析成一只证券，才能去查它的行情。如果按\ **今天**\ 的证券表来解析，
那些今天已经不存在的代码自然查不到。

以海通证券（\ ``600837.XSHG``\ ，2025-03-04 退市）为例：

..  code-block:: python

    >>> instruments("600837.XSHG")            # 按今天问
    None

    >>> instruments("600837.XSHG", as_of="2022-09-20")   # 按 2022 年问
    Instrument(order_book_id='600837.XSHG', symbol='海通证券', type='CS', market='cn',
               listed_date='1994-02-24T00:00:00.000',
               de_listed_date='2025-03-04T00:00:00.000')

**怎么处理**\ ：\ :func:`~libfinance.get_price` 会按你给的 ``end_date``\ （而不是今天）去
解析代码，所以查历史区间时退市股能正常返回，不需要你做任何额外的事：

..  code-block:: python

    >>> get_price(["600837.XSHG"], "2022-09-01", "2022-09-20").shape
    (13, 8)

要自己先校验代码时，才需要把日期显式传给 :func:`~libfinance.instruments`\ 。

**判断方法**\ ：查历史区间时，凡是需要"这个代码在那时存不存在"的判断，都要显式给日期。
不给日期就是按今天问，而今天和你要查的那段时间未必是同一个世界。
