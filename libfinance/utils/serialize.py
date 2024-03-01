#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dill
import pickle

from typing import Any


def serialize_object(obj: Any, protocol: int = pickle.DEFAULT_PROTOCOL) -> bytes:
    """serialize obj to bytes

    protocol v5 only available in python3.8,it`s a new feature that can accelerate memory process efficiency.
    We highly recommend use v5,but to adapt more other python version choose protocol v4 as default,consider
    adding a new api in 'Handle' class to sync client and server protocol.

    Args:
        obj (object): almost support all python standard types,exclude frame, generator, traceback
        protocol (int, optional): protocol can be 0-5,refer to https://docs.python.org/zh-cn/3/library/pickle.html#pickle-protocols

    Returns:
        bytes: serialize value
    """
    return dill.dumps(obj, protocol=protocol)


def deserialize_object(stream: bytes) -> Any:
    """deserialize bytes to object

    Args:
        stream (bytes): serialize bytes

    Returns:
        Any: deserialize object
    """
    if stream is None:
        return

    return dill.loads(stream)