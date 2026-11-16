"""Corporate-action amounts: fixed-point decimals on the wire, float64 in the client."""
import decimal

import pandas as pd
import pyarrow as pa
import pytest

from libfinance.api import corporate_actions
from libfinance.client import deserialize_arrow

FUNCTIONS = ["get_dividends", "get_splits", "get_allotments", "get_spinoffs"]


def _arrow(rows, schema):
    table = pa.Table.from_pylist(rows, schema=schema)
    sink = pa.BufferOutputStream()
    with pa.ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return sink.getvalue().to_pybytes()


SCHEMA = pa.schema([("order_book_id", pa.string()), ("ex_date", pa.string()),
                    ("cash_per_share", pa.decimal128(18, 6)), ("bonus_per_share", pa.decimal128(18, 6))])
ROWS = [{"order_book_id": "000001.XSHE", "ex_date": "2023-06-14",
         "cash_per_share": decimal.Decimal("0.285000"), "bonus_per_share": None}]


class _Server(list):
    rows = ROWS


@pytest.fixture
def server(monkeypatch):
    calls = _Server()

    class Client:
        def __getattr__(self, name):
            def call(**kwargs):
                calls.append((name, kwargs))
                return deserialize_arrow(_arrow(calls.rows, SCHEMA))
            return call

    monkeypatch.setattr(corporate_actions, "get_client", lambda: Client())
    return calls


@pytest.mark.parametrize("name", FUNCTIONS)
def test_amounts_are_float64_by_default(server, name):
    frame = getattr(corporate_actions, name)("000001.XSHE")
    assert frame["cash_per_share"].dtype == "float64"
    assert frame["bonus_per_share"].dtype == "float64" and frame["bonus_per_share"].isna().all()
    assert frame["cash_per_share"].iloc[0] == pytest.approx(0.285)
    assert (frame["cash_per_share"] * 1.5).iloc[0] == pytest.approx(0.4275)     # mixes with get_price's floats
    assert not pd.api.types.is_numeric_dtype(frame["order_book_id"])          # only the decimals are converted


def test_an_empty_answer_has_float64_amount_columns(server):
    server.rows = []                         # no values to recognise them by: the Arrow schema names them
    frame = corporate_actions.get_dividends("000001.XSHE", "2023-08-01", "2023-08-31")
    assert frame.empty and frame["cash_per_share"].dtype == "float64"


def test_a_frame_without_the_schema_note_is_converted_by_its_values():
    """An answer that did not come through deserialize_arrow (pandas JSON, a cached copy without attrs)."""
    frame = pd.DataFrame({"ratio": [decimal.Decimal("1.3"), None], "currency": ["CNY", "CNY"]})
    out = corporate_actions._amounts(frame)
    assert out["ratio"].dtype == "float64" and not pd.api.types.is_numeric_dtype(out["currency"])
