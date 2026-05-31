import socket
import struct
import threading
import sys
from concurrent.futures import Future
import time

import msgpack
import lz4.frame
import pandas as pd
from io import StringIO


# 全局客户端实例（单例模式）
_CLIENT = None

def deserialize_dataframe(json_str):
    return pd.read_json(StringIO(json_str), orient='table', convert_dates=True)


# ==========================================
# RPC 错误码 & 异常
# ==========================================

class RpcErrorCode:
    OK                      = 0
    # 协议层 (10xx)
    INVALID_FRAME_SIZE      = 1001
    DECODE_FAILED           = 1002
    INVALID_RPC_FORMAT      = 1003
    UNKNOWN_FRAME_TYPE      = 1004
    # 路由层 (11xx)
    FUNCTION_NOT_FOUND      = 1101
    # 鉴权层 (12xx)
    INSUFFICIENT_AUTH_LEVEL = 1201
    MISSING_REQUIRED_ROLE   = 1202
    # 执行层 (13xx)
    HANDLER_EXCEPTION       = 1301
    UNSUPPORTED_RETURN_TYPE = 1302
    HANDLER_EXECUTION_ERROR = 1303
    # 业务层 (2xxx) — 用户自定义


class RpcError(Exception):
    """RPC 调用错误，包含错误码和消息"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"RpcError(code={code}): {message}")


# ==========================================
# 帧协议常量 (与 C++ 服务端一致)
# ==========================================
# 帧格式: [4B body_len][1B type][4B request_id][1B flags][payload...]
# body_len = 6 + len(payload)

FRAME_LEN_SIZE = 4
FRAME_META_SIZE = 6   # type(1) + request_id(4) + flags(1)
FRAME_HEADER_SIZE = FRAME_LEN_SIZE + FRAME_META_SIZE  # 10


class FrameType:
    RPC_REQUEST = 0x01
    RPC_RESPONSE = 0x02
    PING = 0x03
    PONG = 0x04


class FrameFlags:
    NONE = 0x00
    LZ4_COMPRESSED = 0x01


# ==========================================
# 帧编解码
# ==========================================

def encode_frame(frame_type, request_id, flags, payload=b''):
    body_len = FRAME_META_SIZE + len(payload)
    header = struct.pack('!IBI B', body_len, frame_type, request_id, flags)
    return header + payload


def encode_rpc_request(request_id, function_name, args, compress=True):
    request_data = {"function": function_name, "args": args}
    raw_payload = msgpack.packb(request_data, use_bin_type=True)

    if compress:
        payload = lz4.frame.compress(raw_payload)
        flags = FrameFlags.LZ4_COMPRESSED
    else:
        payload = raw_payload
        flags = FrameFlags.NONE

    return encode_frame(FrameType.RPC_REQUEST, request_id, flags, payload)


def encode_control_frame(frame_type, request_id=0):
    return encode_frame(frame_type, request_id, FrameFlags.NONE)


def decode_payload(flags, payload):
    if flags & FrameFlags.LZ4_COMPRESSED:
        decompressed = lz4.frame.decompress(payload)
    else:
        decompressed = payload
    return msgpack.unpackb(decompressed, raw=False)


# ==========================================
# RPC Client
# ==========================================

class RpcClient:
    """
    Thread-safe RPC client for ContextRPC servers.

    Supports synchronous (call) and asynchronous (call_async) invocation,
    automatic PING/PONG heartbeat handling, and concurrent requests over
    a single TCP connection.
    """
    request_timeout = 300
    request_attempt_count = 3

    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False

        self._next_id = 0
        self._id_lock = threading.Lock()

        self._pending = {}
        self._pending_lock = threading.Lock()

        self._reader_thread = None

        self._last_recv_time = None
        self._last_recv_lock = threading.Lock()

    def connect(self):
        if self.sock:
            self.close()

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect((self.host, self.port))
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        self.running = True
        self._last_recv_time = self._now()

        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    def close(self):
        self.running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.sock.close()
            self.sock = None

        with self._pending_lock:
            for fut in self._pending.values():
                fut.set_exception(ConnectionError("Connection closed"))
            self._pending.clear()

        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2)

    def call_raw(self, function_name, args=None, timeout=10.0):
        """Send an RPC request and wait synchronously for the raw envelope."""
        if args is None:
            args = {}
        if not self.running:
            raise ConnectionError("Not connected to server.")

        req_id = self._alloc_id()
        future = Future()

        with self._pending_lock:
            self._pending[req_id] = future

        frame = encode_rpc_request(req_id, function_name, args)
        try:
            self.sock.sendall(frame)
        except socket.error as e:
            with self._pending_lock:
                self._pending.pop(req_id, None)
            raise IOError(f"Failed to send request: {e}")

        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            with self._pending_lock:
                self._pending.pop(req_id, None)
            raise TimeoutError(
                f"RPC '{function_name}' timeout after {timeout}s (req_id={req_id})"
            )

    def call(self, function_name, args=None, timeout=10.0):
        """Send an RPC request, auto-unwrap envelope, return result or raise RpcError."""
        resp = self.call_raw(function_name, args, timeout)
        return self._unwrap_envelope(resp)

    def call_async(self, function_name, args=None):
        """Send an RPC request and return a Future (non-blocking)."""
        if args is None:
            args = {}
        if not self.running:
            raise ConnectionError("Not connected to server.")

        req_id = self._alloc_id()
        future = Future()

        with self._pending_lock:
            self._pending[req_id] = future

        frame = encode_rpc_request(req_id, function_name, args)
        try:
            self.sock.sendall(frame)
        except socket.error as e:
            with self._pending_lock:
                self._pending.pop(req_id, None)
            future.set_exception(IOError(f"Failed to send request: {e}"))

        return future

    def send_ping(self):
        if not self.running:
            return
        frame = encode_control_frame(FrameType.PING)
        try:
            self.sock.sendall(frame)
        except socket.error:
            pass

    @property
    def seconds_since_last_recv(self):
        with self._last_recv_lock:
            if self._last_recv_time is None:
                return float('inf')
            return (self._now() - self._last_recv_time).total_seconds()

    # --- internal ---

    @staticmethod
    def _unwrap_envelope(resp):
        """Unwrap the unified envelope. Return result on success, raise RpcError on error."""
        if not isinstance(resp, dict):
            return resp
        status = resp.get("status")
        if status == "error":
            code = resp.get("code", -1)
            message = resp.get("message", "Unknown error")
            raise RpcError(code, message)
        if "result" in resp:
            raw_output = resp["result"]
            if isinstance(raw_output, dict) and raw_output.get("type") == "pandas":
                return deserialize_dataframe(raw_output.get("data")) 
            else:
                return raw_output
        return resp

    def _alloc_id(self):
        with self._id_lock:
            self._next_id += 1
            return self._next_id

    @staticmethod
    def _now():
        import datetime
        return datetime.datetime.now()

    def _recv_exact(self, n):
        data = b''
        while len(data) < n and self.running:
            try:
                chunk = self.sock.recv(n - len(data))
            except socket.timeout:
                continue
            except socket.error as e:
                if self.running:
                    print(f"Socket error in reader: {e}", file=sys.stderr)
                return b''
            if not chunk:
                if self.running:
                    print("Server closed connection.", file=sys.stderr)
                self.running = False
                return b''
            data += chunk
        return data

    def _read_one_frame(self):
        len_data = self._recv_exact(FRAME_LEN_SIZE)
        if not len_data or len(len_data) < FRAME_LEN_SIZE:
            return None

        body_len = struct.unpack('!I', len_data)[0]

        if body_len < FRAME_META_SIZE or body_len > 15 * 1024 * 1024:
            print(f"Invalid frame body_len: {body_len}", file=sys.stderr)
            self.running = False
            return None

        body_data = self._recv_exact(body_len)
        if not body_data or len(body_data) < body_len:
            return None

        frame_type = body_data[0]
        request_id = struct.unpack('!I', body_data[1:5])[0]
        flags = body_data[5]
        payload = body_data[FRAME_META_SIZE:]

        return frame_type, request_id, flags, payload

    def _reader_loop(self):
        while self.running:
            try:
                result = self._read_one_frame()
                if result is None:
                    continue

                frame_type, request_id, flags, payload = result

                with self._last_recv_lock:
                    self._last_recv_time = self._now()

                if frame_type == FrameType.PING:
                    pong = encode_control_frame(FrameType.PONG, request_id)
                    try:
                        self.sock.sendall(pong)
                    except socket.error:
                        pass

                elif frame_type == FrameType.PONG:
                    pass

                elif frame_type == FrameType.RPC_RESPONSE:
                    try:
                        response_data = decode_payload(flags, payload)
                    except Exception as e:
                        print(f"Failed to decode response payload: {e}", file=sys.stderr)
                        response_data = {"status": "error", "error": f"decode failed: {e}"}

                    with self._pending_lock:
                        future = self._pending.pop(request_id, None)

                    if future:
                        future.set_result(response_data)
                    else:
                        print(
                            f"Received response for unknown request_id={request_id}",
                            file=sys.stderr,
                        )
                else:
                    print(f"Unknown frame type: 0x{frame_type:02x}", file=sys.stderr)

            except Exception as e:
                if self.running:
                    print(f"Reader loop error: {e}", file=sys.stderr)
                self.running = False
                break

        with self._pending_lock:
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(ConnectionError("Connection lost"))
            self._pending.clear()

    def __getattr__(self, api_name):
        return lambda **kwargs: self(api_name, **kwargs)
    
    def __call__(self, api_name, **kwargs):
        err, response = None, None
        for attempt_index in range(self.request_attempt_count):
            try:
                response = self.call(api_name, kwargs)
                break
            except Exception as ex:
                err = ex
                if attempt_index < self.request_attempt_count - 1:
                    time.sleep(0.6)
            except ResponseError as ex:
                err = ex

        if response is None and isinstance(err, Exception):
            if "TSocket read 0 bytes" in str(err):
                raise Exception("连接被关闭，请减少数据查询量或检查网络后重试")
            raise err

        return response


# 默认懒连接参数；可在 import libfinance 之后、第一次调 api 之前显式 init_client(...) 覆盖
_DEFAULT_HOST = "0.0.0.0"
_DEFAULT_PORT = 8080

# 初始化函数
def init_client(host: str = "127.0.0.1", port: int = 8080):
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = RpcClient(host, port)
        _CLIENT.connect()

def get_client():
    global _CLIENT
    if _CLIENT is None:
        try:
            init_client(host=_DEFAULT_HOST, port=_DEFAULT_PORT)
        except Exception as e:
            _CLIENT = None
            raise RuntimeError(
                f"Client auto-connect to {_DEFAULT_HOST}:{_DEFAULT_PORT} failed: {e}. "
                "Call init_client(host=..., port=...) explicitly before using libfinance.api.*"
            ) from e
    return _CLIENT