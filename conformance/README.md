# conformance

同一组调用分别经 Python 客户端（`python/`，进程内）与 C++ 客户端（`cpp/` 的 `libfinance-call`）发给
**同一个服务端**，逐项比对：表格按列名与行、日期按 ISO 日、数值 1e-9 相对误差、错误按类别与消息、
告警按列表。另外核对 C++ 实现的函数与 `contract/contract.json` 的清单完全一致。

```bash
LIBFINANCE_HOST=127.0.0.1 LIBFINANCE_PORT=8080 \
    python conformance/run.py --call cpp/build/tools/libfinance-call [--only get_price]
```

最近一次：57 个用例（27 个函数，含参数错误、越界、未知代码等）全部一致。
