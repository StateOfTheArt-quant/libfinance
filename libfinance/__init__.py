#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__all__ = ["__version__"]

__version__ = "0.0.1"
#from libfinance.api import *
def __go():
    import sys
    import importlib
    import pkgutil

    # 3.4 引入 asyncio，3.5 引入 async/await 语法，3.6 引入 async generator
    async_syntax_supported = sys.version_info[:2] >= (3, 6)

    for loader, module_name, is_pkg in pkgutil.walk_packages(__path__, "libfinance."):
        if module_name.startswith("libfinance.api") and not is_pkg:
            importlib.import_module(module_name)

__go()