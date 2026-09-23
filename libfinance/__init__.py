from .client import init_client

# 不再 import 时连接 RPC（服务 A）；第一次调用 libfinance.api.* 会按 client.py 的
# _DEFAULT_HOST/_DEFAULT_PORT 懒自动连接。两种方式指到别的服务端：
#
#   1. 环境变量（本地调试推荐，不用改代码）：
#        export LIBFINANCE_HOST=127.0.0.1
#        export LIBFINANCE_PORT=8080
#      必须在 `import libfinance` 之前 export —— 取值发生在 import 时。
#
#   2. 显式调用：
#        from libfinance import init_client
#        init_client(host="127.0.0.1", port=8080)
#
# 两者都不设时连的是内置默认 libfinance.tech:8080，那是**生产环境**。
# 这样 RPC 服务未就绪时，libfinance.subscribe 等子模块也可以独立使用。

__all__ = ["__version__", "init_client"]

__version__ = "0.0.6"
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