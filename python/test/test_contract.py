"""The Python client matches contract/contract.json: every function, parameter and default.

The contract is what every client language implements; this test is the Python side of that
promise (cpp/test checks the C++ side against the same file).
"""
import inspect
import json
import pathlib

import pytest

import libfinance

_CONTRACT = json.loads((pathlib.Path(__file__).resolve().parents[2] / "contract" / "contract.json").read_text())
_FUNCTIONS = {entry["name"]: entry for entry in _CONTRACT["functions"]}


@pytest.mark.parametrize("name", sorted(_FUNCTIONS))
def test_function_matches_the_contract(name):
    function = getattr(libfinance, name, None)
    assert function is not None, "{} is in the contract but not exported by libfinance".format(name)
    params = [p for p in inspect.signature(inspect.unwrap(function)).parameters.values()
              if p.kind is not p.VAR_KEYWORD]
    declared = _FUNCTIONS[name]["params"]
    assert [p.name for p in params] == [p["name"] for p in declared]
    for param, entry in zip(params, declared):
        if "default" in entry:
            assert param.default == entry["default"], "{}({}) default".format(name, param.name)
        else:
            assert param.default is inspect.Parameter.empty, "{}({}) must be required".format(name, param.name)


def test_every_exported_function_is_in_the_contract():
    exported = {name for name in libfinance.__all__ if callable(getattr(libfinance, name))} - {"init_client"}
    assert exported - set(_FUNCTIONS) == set()


def test_every_wire_function_a_function_uses_is_declared():
    for entry in _CONTRACT["functions"]:
        assert set(entry["wire"]) <= set(_CONTRACT["wire"]), entry["name"]
