=======================
Industry classification
=======================

.. currentmodule:: libfinance

Semantics are covered in :doc:`../data/universe`. Only Shenwan (``source="sw"``) is
currently supported.

.. py:function:: get_industry_mapping(source='sw', date=None, market=None)

    The whole classification tree — codes, names, levels.

    :param source: Classification source; defaults to ``"sw"`` (Shenwan)
    :param date: Use the classification as of this day; omit for the latest
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` with one row per third-level industry

    .. code-block:: python

        >>> get_industry_mapping().shape
        (346, 6)

    Columns: ``first_industry_code`` / ``first_industry_name`` and the same for
    ``second_`` and ``third_``.

.. py:function:: get_instrument_industry(order_book_ids, date=None, source='sw', level=1, market=None)

    Which industry each security belongs to.

    :param order_book_ids: List of stock codes
    :param date: Use the classification as of this day; omit for the latest.
        **Pass this for historical work** — memberships change.
    :param source: Classification source; only ``"sw"`` is supported
    :param level: Depth, 1/2/3; default 1
    :param market: Market; omit for the server default
    :returns: ``DataFrame`` indexed by ``order_book_id``

    .. code-block:: python

        >>> get_instrument_industry(["000001.XSHE", "600000.XSHG"], date="2024-03-08")
                      first_industry_code first_industry_name
        order_book_id
        000001.XSHE                480000                  银行
        600000.XSHG                480000                  银行

    The default ``source`` was ``"010303"`` before 0.0.6, which the server never
    accepted — calls with default arguments always failed.

.. py:function:: get_industry(industry, source='sw', date=None, market=None)

    Every security in an industry.

    :param industry: Industry code or name
    :param source: Classification source; defaults to ``"sw"``
    :param date: Use the classification as of this day; omit for the latest
    :param market: Market; omit for the server default
    :returns: List of codes

    .. code-block:: python

        >>> get_industry("480000")[:4]
        ['000001.XSHE', '001227.XSHE', '002142.XSHE', '002807.XSHE']
