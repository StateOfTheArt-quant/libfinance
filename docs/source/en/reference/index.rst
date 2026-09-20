=============
API reference
=============

Every public interface, grouped by topic.

.. note::

    The Chinese documentation generates this section directly from the source
    docstrings. The English pages are written by hand, so a test
    (``test/test_docs_contract.py``) checks that every public function appears
    here and that the parameter lists match the code. Prose can still drift; the
    signatures cannot.

To understand the semantics before looking up a signature, start at
:doc:`../data/index`.

.. list-table::
    :header-rows: 1
    :widths: 26 74

    *   - Page
        - Contents
    *   - :doc:`client`
        - Connecting and exceptions
    *   - :doc:`calendar`
        - Trading calendar
    *   - :doc:`instrument`
        - Security codes and master data
    *   - :doc:`price`
        - Daily bars and coverage
    *   - :doc:`corporate_actions`
        - Dividends, splits, allotments, spin-offs
    *   - :doc:`financials`
        - PIT statements and factors
    *   - :doc:`shares`
        - Share capital
    *   - :doc:`industry`
        - Industry classification
    *   - :doc:`weights`
        - Index and concept constituents
    *   - :doc:`realtime`
        - Snapshots and subscriptions
    *   - :doc:`fields`
        - Field dictionary
    *   - :doc:`index_meta`
        - Index code table

.. toctree::
    :maxdepth: 1
    :hidden:

    client
    calendar
    instrument
    price
    corporate_actions
    financials
    shares
    industry
    weights
    realtime
    fields
    index_meta
