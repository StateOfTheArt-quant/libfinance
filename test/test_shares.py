import datetime

import pandas as pd
import pytest

import libfinance
import libfinance.api.shares as shares_api
from libfinance.client import RpcClient


class FakeClient:
    def __init__(self, result=None):
        self.result = result
        self.calls = []

    def get_shares(self, **kwargs):
        self.calls.append(kwargs)
        return self.result


def test_get_shares_is_exported_and_forwards_normalized_arguments(monkeypatch):
    expected = pd.DataFrame(
        {"total": [1_000_000.0]},
        index=pd.MultiIndex.from_tuples(
            [("600000.XSHG", pd.Timestamp("2024-01-02"))],
            names=["order_book_id", "date"],
        ),
    )
    client = FakeClient(expected)
    monkeypatch.setattr(shares_api, "get_client", lambda: client)

    result = libfinance.get_shares(
        "600000.XSHG",
        datetime.date(2024, 1, 2),
        pd.Timestamp("2024-01-03"),
        "total",
    )

    assert result is expected
    assert client.calls == [{
        "order_book_ids": ["600000.XSHG"],
        "start_date": "2024-01-02",
        "end_date": "2024-01-03",
        "fields": ["total"],
    }]


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"order_book_ids": []}, "at least one"),
        ({"order_book_ids": "600000.XSHG", "fields": ["unknown"]}, "invalided value"),
        (
            {
                "order_book_ids": "600000.XSHG",
                "start_date": "2024-01-03",
                "end_date": "2024-01-02",
            },
            "invalid date range",
        ),
    ],
)
def test_get_shares_rejects_invalid_arguments(monkeypatch, kwargs, message):
    monkeypatch.setattr(shares_api, "get_client", lambda: FakeClient())
    with pytest.raises(ValueError, match=message):
        libfinance.get_shares(**kwargs)


def test_rpc_dataframe_response_is_deserialized():
    expected = pd.DataFrame(
        {"total": [1_000_000.0], "circulation_a": [800_000.0]},
        index=pd.MultiIndex.from_tuples(
            [("600000.XSHG", pd.Timestamp("2024-01-02"))],
            names=["order_book_id", "date"],
        ),
    )
    envelope = {
        "status": "ok",
        "result": {"type": "pandas", "data": expected.to_json(orient="table")},
    }

    actual = RpcClient._unwrap_envelope(envelope)

    pd.testing.assert_frame_equal(actual, expected)
