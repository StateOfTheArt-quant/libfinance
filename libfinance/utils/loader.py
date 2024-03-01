#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import thriftpy2

from typing import Any
from pathlib import Path


def load_thrift_module(dir_or_file: str, thrift_file: str = "") -> Any:
    """加载thrift模块

    Args:
        dir_or_file (str): .thrift所在的文件或文件夹路径，若是文件则取当前文件所在目录为默认根目录
        thrift_file (str, optional): thrift文件名全称，如果未提供，则默认按传入的文件名进行解析

    Returns:
        Any: thrifty配置文件加载后的实例

    Examples:
        >>> load_thrift_module(__file__, "pingpong.thrift")
        <module 'pingpong_thrift'>
        >>> load_thrift_module("/home/user/pingpong.thrift")
        <module 'pingpong_thrift'>
    """
    # current file absolute working directory
    working_dir = Path(dir_or_file).absolute()
    # if file get file directory
    if working_dir.is_file():
        working_dir = working_dir.parent
        thrift_file = thrift_file or working_dir.name
    # is file name valid
    if len(thrift_file) == 0:
        raise ValueError(
            "thrift file name is empty, please check path '{}' contains ".format(dir_or_file) +
            "file name or given 'thrift_file' parameter when called 'load_thrift_module' function."
        )
    # convert file name from 'demo.thrifty' to module name 'demo_thrifty'
    thrift_module_name = thrift_file.replace(".", "_")
    # thriftpy2 do not support pathlib
    thrift_module = thriftpy2.load(path=str(working_dir.joinpath(thrift_file)),
                                   module_name=thrift_module_name)

    return thrift_module
