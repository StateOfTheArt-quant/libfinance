One function design for Python and C++
======================================

Research usually happens in Python; backtest engines, factor pipelines and
trading systems often run in C++. If the two data interfaces differ by a
default value or a validation rule, a strategy moved from research to
production changes its numbers quietly, and the cause is hard to find.
libfinance's Python and C++ clients implement one contract: the same function
has the same name, parameter order and defaults, validation and errors, and
returned columns.

One contract, two implementations
---------------------------------

``contract/contract.json`` in the repository is what both clients follow. It
lists all 33 public functions, each with:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Item
     - What it fixes
   * - Name and module
     - ``get_price``, ``all_instruments`` ... the same in both languages
   * - Parameters
     - Order, type and default, e.g. ``adjust_type`` defaults to ``"pre"``
   * - Returns
     - A table's columns and index, or a list of dates, or an object
   * - Wire functions
     - The server functions a client calls; both clients send the same requests

Each client implements the wire protocol itself (frames, msgpack, LZ4) and
depends on no server library. Both share the repository version (``VERSION``):
one version number means one contract.

One query, two languages
------------------------

.. code-block:: python

   import libfinance as lf

   bars = lf.get_price(["600000.XSHG", "AAPL.US"], "2024-03-01", "2024-03-05", adjust_type="none")
   factors = lf.get_factor_exposure(["600000.XSHG", "000001.XSHE"], "system/alpha158",
                                    "2026-09-07", "2026-09-10")

.. code-block:: cpp

   #include <libfinance/libfinance.hpp>
   namespace lf = libfinance;

   lf::Table bars = lf::get_price({"600000.XSHG", "AAPL.US"}, "2024-03-01", "2024-03-05",
                                  "1d", {}, false, true, "none");
   lf::Table factors = lf::get_factor_exposure({"600000.XSHG", "000001.XSHE"}, "system/alpha158",
                                               "2026-09-07", "2026-09-10");

C++ has no keyword arguments: pass them in the contract's order; omitted ones
take the same defaults.

How the types map
-----------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Python
     - C++
   * - Dates: ``str``, ``date``, ``int``
     - ``DateLike``: ``"2024-03-01"``, ``"20240301"``, ``20240301``, ``lf::Date``
   * - One code or a list of codes
     - ``Codes``: ``"600000.XSHG"`` or ``{"600000.XSHG", "AAPL.US"}``
   * - ``None``
     - ``std::nullopt``, or omitted
   * - ``pandas.DataFrame``
     - ``arrow::Table`` (``lf::Table``); Python's index columns are ordinary columns with the same names
   * - ``ValueError``
     - ``std::invalid_argument``
   * - An error returned by the server
     - ``lf::RpcError``: ``code()``, ``message()``, ``kind()``

Two differences of form are deliberate: for a single code, Python's
``instruments`` returns one object or ``None`` while C++ always returns a list;
Python warns through ``warnings``, C++ through ``lf::set_warning_handler``.

How consistency is checked
--------------------------

A written contract does not make two implementations agree, so the repository
checks them: ``contract/conformance/`` sends the same calls through the Python
client and the C++ client to one server and compares the answers item by item
-- tables by column names and rows, dates as ISO days, numbers to a relative
1e-9, errors by kind and message, warnings as lists. The cases include normal
queries as well as bad arguments, out-of-range dates and unknown codes: errors
must agree as much as results. A further check confirms that the C++ function
list equals the contract's.

For installing and using the C++ client, see
`cpp/readme_en.md <https://github.com/StateOfTheArt-quant/libfinance/blob/main/cpp/readme_en.md>`_.
