========
实时行情
========

..  currentmodule:: libfinance

口径说明见 :doc:`../data/realtime`\ 。

快照查询
========

..  autofunction:: get_last_quotes

订阅
====

..  autoclass:: libfinance.subscribe.quote_api.QuoteApi
    :members: connect, login, subscribe, unsubscribe, subscribe_all,
              unsubscribe_all, query_sources, disconnect, register_spi

..  autoclass:: libfinance.subscribe.quote_api.QuoteSpi
    :members:

..  autoclass:: libfinance.subscribe.md_protocol.Quote
