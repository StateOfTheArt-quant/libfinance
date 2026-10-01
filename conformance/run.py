"""Conformance: the Python and C++ clients give the same answers, against the same server.

    LIBFINANCE_HOST=127.0.0.1 LIBFINANCE_PORT=8080 \
        python conformance/run.py --call cpp/build/tools/libfinance-call [--only get_price]

Every case calls one contract function through both clients -- python/ in-process, cpp/ through
libfinance-call -- and compares the answers after putting both in one form: tables as columns +
rows (a DataFrame's index becomes columns; columns matched by name), dates as ISO days, NaN as null,
numbers to 1e-9 relative. Errors compare by kind and message, warnings as lists. The C++ client must
also implement exactly the functions contract/contract.json lists.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
import pathlib
import subprocess
import sys
import warnings

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))

CN = ["600000.XSHG", "000001.XSHE", "300750.XSHE"]
US = ["AAPL.US", "MSFT.US"]

#: (function, keyword arguments). Normal calls, edge cases and the client-side refusals.
CASES = [
    # calendar
    ("get_all_trading_dates", {}),
    ("get_all_trading_dates", {"market": "us"}),
    ("get_calendar_coverage", {}),
    ("get_trading_dates", {"start_date": "2025-06-01", "end_date": "2025-06-30"}),
    ("get_trading_dates", {"start_date": "20250630", "end_date": "20250601"}),
    ("get_trading_dates", {"start_date": "1980-01-01", "end_date": "2025-06-30"}),
    ("get_trading_dates", {"start_date": "2025-06-01", "end_date": "2025-06-30", "market": "us"}),
    ("get_previous_trading_date", {"date": "2025-06-03"}),
    ("get_previous_trading_date", {"date": "2025-06-03", "n": 5}),
    ("get_previous_trading_date", {"date": "1990-12-19"}),
    ("get_next_trading_date", {"date": "2025-06-06", "n": 3}),
    ("get_next_trading_date", {"date": "2026-12-31"}),
    ("is_trading_date", {"date": "2025-06-07"}),
    ("is_trading_date", {"date": "2025-06-09"}),
    ("get_n_trading_dates_until", {"date": "2025-06-09", "n": 4}),
    ("get_n_trading_dates_until", {"date": "1990-12-20", "n": 4}),
    ("count_trading_dates", {"start_date": "2025-01-01", "end_date": "2025-12-31"}),
    # instrument
    ("all_instruments", {"type": "stock"}),
    ("all_instruments", {"type": ["stock", "index"], "as_of": "2020-01-02"}),
    ("all_instruments", {"type": "index", "source": "CSI"}),
    ("all_instruments", {"type": "CS"}),
    ("all_instruments", {"market": "us"}),
    ("instruments", {"order_book_ids": CN + ["000300.XSHG", "NOPE.XSHG"]}),
    ("instruments", {"order_book_ids": "600000.XSHG", "as_of": "2010-01-04"}),
    ("instruments", {"order_book_ids": "600837.XSHG", "last_known": True}),
    ("instruments", {"order_book_ids": []}),
    # price
    ("get_price", {"order_book_ids": CN, "start_date": "2025-06-02", "end_date": "2025-06-30"}),
    ("get_price", {"order_book_ids": CN[:2], "start_date": "2025-06-02", "end_date": "2025-06-06",
                   "fields": ["close", "volume"], "adjust_type": "none"}),
    ("get_price", {"order_book_ids": "600000.XSHG", "start_date": "2025-06-02", "end_date": "2025-06-06",
                   "adjust_type": "post"}),
    ("get_price", {"order_book_ids": ["600000.XSHG", "NOPE.XSHG"], "start_date": "2025-06-02", "end_date": "2025-06-06"}),
    ("get_price", {"order_book_ids": US, "start_date": "2025-06-02", "end_date": "2025-06-06"}),
    ("get_price", {"order_book_ids": CN[:1] + ["000300.XSHG"], "start_date": "2025-06-02", "end_date": "2025-06-06"}),
    ("get_price", {"order_book_ids": CN, "start_date": "2025-06-02", "end_date": "2025-06-06", "frequency": "1m"}),
    ("get_price", {"order_book_ids": CN, "start_date": "2025-06-02", "end_date": "2025-06-06", "adjust_type": "both"}),
    ("get_price", {"order_book_ids": CN, "start_date": "2025-06-02", "end_date": "2025-06-06", "fields": ["vwap"]}),
    ("get_price", {"order_book_ids": ["NOPE.XSHG"], "start_date": "2025-06-02", "end_date": "2025-06-06"}),
    ("get_price_coverage", {}),
    ("get_price_coverage", {"market": "us"}),
    # corporate actions
    ("get_dividends", {"order_book_ids": CN, "start_date": "2020-01-01", "end_date": "2025-12-31"}),
    ("get_dividends", {"order_book_ids": CN, "start_date": "2025-12-31", "end_date": "2020-01-01"}),
    ("get_splits", {"order_book_ids": US, "start_date": "2015-01-01", "end_date": "2025-12-31"}),
    ("get_allotments", {"order_book_ids": CN, "start_date": "1995-01-01", "end_date": "2025-12-31"}),
    ("get_spinoffs", {"order_book_ids": US, "start_date": "2015-01-01", "end_date": "2025-12-31"}),
    ("get_spinoffs", {"order_book_ids": CN}),
    # exfactor
    ("get_ex_factor", {"order_book_ids": CN, "start_date": "2020-01-01", "end_date": "2025-12-31"}),
    ("get_ex_factor", {"order_book_ids": CN, "start_date": "2025-12-31", "end_date": "2020-01-01"}),
    # financials
    ("get_pit_financials_ex", {"order_book_ids": CN[:2], "fields": ["revenue", "net_profit"],
                               "start_quarter": "2024q1", "end_quarter": "2024q4"}),
    ("get_pit_financials_ex", {"order_book_ids": CN[:2], "fields": ["revenue"], "start_quarter": "2024",
                               "end_quarter": "2024q4"}),
    ("get_pit_financials_ex", {"order_book_ids": CN[:2], "fields": ["revenue"], "start_quarter": "2024q1",
                               "end_quarter": "2024q4", "statements": "some"}),
    ("get_factor", {"order_book_ids": CN[:1], "factors": ["roe"], "start_quarter": "2024q1", "end_quarter": "2024q4"}),
    # industry, index, concepts
    ("get_instrument_industry", {"order_book_ids": CN}),
    ("get_instrument_industry", {"order_book_ids": CN, "source": "SW", "level": 2, "as_of": "2024-06-28"}),
    ("get_index_weights", {"index_code": "000300.XSHG", "date": "2025-06-30"}),
    ("get_industry_constituents", {"order_book_id": "801780.SW"}),
    ("get_industry_constituents", {"order_book_id": "801780.SW", "as_of": "2024-06-28"}),
    ("get_industry_weights", {"order_book_id": "801780.SW", "as_of": "2024-06-28"}),
    ("get_concept_meta", {}),
    ("get_concept_weights", {"concept_ids": ["885311", "886074"], "as_of": "2025-06-30"}),
    # shares, quotes
    ("get_shares", {"order_book_ids": CN, "start_date": "2025-01-01", "end_date": "2025-06-30"}),
    ("get_shares", {"order_book_ids": CN, "fields": ["float"]}),
    ("get_last_quotes", {"order_book_ids": CN}),
]


# ---------------------------------------------------------------- one form for both answers

def plain(value):
    """A scalar in the form libfinance-call prints."""
    import numpy as np
    import pandas as pd

    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if value is pd.NaT:
        return None
    if isinstance(value, (pd.Timestamp, datetime.datetime, datetime.date, np.datetime64)):
        return pd.Timestamp(value).strftime("%Y-%m-%d")
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def python_form(value):
    import pandas as pd

    if isinstance(value, pd.DataFrame):
        frame = value.reset_index() if any(name is not None for name in value.index.names) else value
        return {"columns": [str(c) for c in frame.columns],
                "rows": [[plain(v) for v in row] for row in frame.itertuples(index=False, name=None)]}
    if isinstance(value, pd.DatetimeIndex):
        return [plain(v) for v in value]
    if isinstance(value, list) and value and type(value[0]).__name__ == "Instrument":
        return [plain(item.__dict__) for item in value]
    if type(value).__name__ == "Instrument":
        return [plain(value.__dict__)]  # C++ always answers a list
    if value is None:
        return None
    return plain(value)


def by_column(table):
    """{column: [values]} -- column order is not part of the contract, the values are."""
    if not isinstance(table, dict) or "columns" not in table:
        return table
    return {name: [row[i] for row in table["rows"]] for i, name in enumerate(table["columns"])}


def same(a, b):
    if isinstance(a, float) or isinstance(b, float):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
            return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)
        return False
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


# ---------------------------------------------------------------- the two sides

ERROR_KINDS = {"TypeError": "ValueError", "AssertionError": "ValueError"}


def python_side(name, args):
    import libfinance

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            answer = ("ok", by_column(python_form(getattr(libfinance, name)(**args))))
        except Exception as error:  # noqa: BLE001
            kind = type(error).__name__
            message = str(error)
            if kind == "RpcError":
                kind, message = (error.kind or "RpcError"), error.message
            answer = ("error", (ERROR_KINDS.get(kind, kind), message.rstrip()))
    # libfinance's own warnings are UserWarnings; pandas' FutureWarnings and the like are not ours
    return answer, [str(w.message) for w in caught if w.category is UserWarning]


def cpp_side(call, name, args):
    done = subprocess.run([call, name, json.dumps(args)], capture_output=True, text=True)
    lines = done.stderr.strip().splitlines()
    warned = [line[len("warning: "):] for line in lines if line.startswith("warning: ")]
    # the error comes last and may span lines ("<Kind>: <message ...>")
    error = "\n".join(line for line in lines if not line.startswith("warning: "))
    if done.returncode != 0:
        if not error:
            return ("crash", done.returncode), warned
        kind, _, message = error.partition(": ")
        return ("error", (kind, message)), warned
    return ("ok", by_column(json.loads(done.stdout))), warned


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--call", required=True, help="cpp/build/tools/libfinance-call")
    parser.add_argument("--only", help="run the cases of one function")
    opts = parser.parse_args()

    contract = json.loads((ROOT / "contract" / "contract.json").read_text())
    declared = {entry["name"] for entry in contract["functions"]}
    implemented = set(subprocess.run([opts.call, "--list"], capture_output=True, text=True).stdout.split())
    failures = 0
    if implemented != declared:
        failures += 1
        print("DIFF  C++ functions vs contract: missing {}, extra {}".format(
            sorted(declared - implemented), sorted(implemented - declared)))
    uncovered = declared - {name for name, _ in CASES}
    if uncovered:
        print("note: no case for {}".format(sorted(uncovered)))

    for name, args in CASES:
        if opts.only and name != opts.only:
            continue
        (want, want_warned), (got, got_warned) = python_side(name, args), cpp_side(opts.call, name, args)
        agree = same(list(want), list(got)) and sorted(want_warned) == sorted(got_warned)
        failures += not agree
        columns = list(want[1].values()) if want[0] == "ok" and isinstance(want[1], dict) else []
        size = len(columns[0]) if columns and isinstance(columns[0], list) else ""
        label = "{}({}) {}".format(name, json.dumps(args, ensure_ascii=False)[:100], size)
        print("{:<5} {}".format("ok" if agree else "DIFF", label))
        if not agree:
            print("    python: {} warnings={}".format(str(want)[:400], want_warned))
            print("    c++:    {} warnings={}".format(str(got)[:400], got_warned))
    print("\n{} cases, {} differ".format(len(CASES), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
