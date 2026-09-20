==========
连接与异常
==========

..  currentmodule:: libfinance

连接
====

..  autofunction:: init_client

异常
====

..  autoexception:: libfinance.client.RpcError

    服务端拒绝了这次调用。\ ``code`` 是错误码，\ ``message`` 是原因。

..  autoexception:: libfinance.api.calendar.CalendarCoverageError

缓存
====

参考数据（证券主数据、交易日历、行业分类等）会在客户端缓存，并在服务端数据更新时
自动失效，所以反复调用是廉价的，你不需要自己包一层缓存。

需要强制重新拉取时（一般只在排查问题时用到）：

..  code-block:: python

    >>> from libfinance.utils.cache import clear_all
    >>> clear_all()
