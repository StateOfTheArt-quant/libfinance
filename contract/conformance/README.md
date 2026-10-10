# conformance

同一组调用分别经 Python 客户端（`python/`，进程内）与 C++ 客户端（`cpp/` 的 `libfinance-call`）发给
**同一个服务端**，逐项比对：表格按列名与行、日期按 ISO 日、数值 1e-9 相对误差、错误按类别与消息、
告警按列表。另外核对 C++ 实现的函数与 `contract/contract.json` 的清单完全一致。

```bash
LIBFINANCE_HOST=127.0.0.1 LIBFINANCE_PORT=8080 \
    python contract/conformance/run.py --call cpp/build/tools/libfinance-call [--only get_price]
```

最近一次（2026-10-10，libfinance.tech，服务端 v0.1.10）：76 个用例（含参数错误、越界、未知代码等），70 个一致，6 个不同：

| 用例 | 差异 | 性质 |
|---|---|---|
| `get_dividends`、`get_splits`、`get_allotments` | 定点小数列：Python 为 `Decimal`，C++ 的 `libfinance-call` 输出字符串 | 表示不同，数值相同；比对需按数值归一 |
| `get_index_weights` | 列表列 `quality_flags`：C++ 的 `libfinance-call` 输出 `list<element: string>[...]` 字样 | 工具的序列化缺口 |
| `get_last_quotes` | Python 为 `Quote` 对象，C++ 为字典 | 表示不同 |
| `get_financial_metrics` | 行序：Python 按代码排序，C++ 保持请求顺序 | **行为差异**，需在一侧修正 |
