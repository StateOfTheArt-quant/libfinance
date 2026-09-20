========
连接服务
========

``libfinance`` 本身不带数据——它把查询发给一个数据服务。所以 ``import`` 之后的第一件
事是告诉它服务在哪里。

连上
====

在\ **第一次调用任何取数函数之前**\ 调用一次 :func:`~libfinance.init_client`\ ：

..  code-block:: python

    import libfinance

    libfinance.init_client(host="libfinance.tech", port=8080)

..  warning::

    ``init_client`` 只在还没有连接时才真正建立连接。如果你已经调用过取数函数（那会触发
    一次自动连接），之后再调 ``init_client`` 换地址是\ **没有效果的**\ ，也不会报错。
    所以把它放在脚本最前面。

自建服务的话，把 ``host`` / ``port`` 换成你自己的地址：

..  code-block:: python

    libfinance.init_client(host="127.0.0.1", port=8080)

怎么算连上了
============

不要靠"下一句取数没报错"来判断——那会把连接问题和数据问题混在一起。直接问一句：

..  code-block:: python

    >>> from libfinance import get_calendar_coverage
    >>> get_calendar_coverage()
    {'history_start': Timestamp('1990-12-19 00:00:00'),
     'confirmed_through': Timestamp('2026-12-31 00:00:00')}

拿到两个日期就说明：连接通了、服务在正常回话、数据也挂上了。

连不上怎么查
============

报错形如 ``Client auto-connect to <host>:<port> failed`` 或 ``ConnectionError``
时，按这个顺序查，每一步都有明确的判断标准：

..  list-table::
    :header-rows: 1
    :widths: 8 30 62

    *   - 步
        - 查什么
        - 怎么判断
    *   - 1
        - 端口通不通

          ``telnet <host> 8080``
        - 连不上 → 地址写错，或服务没起，或被防火墙挡了。到此为止，后面几步不用查。
    *   - 2
        - 服务在不在回话
        - 端口通但调用卡住或立刻断开，说明那个端口上\ **不是**\ 这个服务（比如是个负载
          均衡器，后面没有东西）。
    *   - 3
        - 是不是被拒绝
        - 能收到回应但报 ``RpcError``\ ，那连接是好的，问题在请求本身——看
          :doc:`../howto/troubleshooting`\ 。

可查区间的限制
==============

服务端可能对可查的历史区间设有限制：起始日期会被夹到最近两年多，
比这更早的 ``start_date`` 会被悄悄上拉。这时你可能拿到一张空表，而空表看不出是
"没有数据"还是"超出了可查范围"——所以客户端在这种情况下会先给一句警告，把边界日期
直接说出来。

下一步：\ :doc:`quickstart`\ 。
