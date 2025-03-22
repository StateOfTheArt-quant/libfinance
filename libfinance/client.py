#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import json
import lz4.frame
import pandas as pd
import numpy as np
import hashlib
import msgpack
from typing import Union, Dict, Any
from functools import wraps
import inspect  # 用于解析函数签名
from io import StringIO
import time

def deserialize_dataframe(json_str):
    return pd.read_json(StringIO(json_str), orient='table', convert_dates=True)


# 全局客户端实例（单例模式）
_CLIENT = None

class APIClientCore:
    
    _default_host = "0.0.0.0"
    _default_port = 8080

    request_timeout = 300
    request_attempt_count = 3

    def __init__(self, host: str, port: int, use_binary: bool = True):
        self.sock = self._create_connection(host, port)
        self.use_binary = use_binary
        self.auth_token = None  # 存储认证令牌
        
    def _create_connection(self, host, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock

    def _encode_request(self, func_name: str, args: Dict[str, Any]) -> bytes:
        #the key and value in args, must be the types that json.dumps supports
        request = {"function": func_name, "args": args or {}}
        if self.auth_token:
            request["auth_token"] = self.auth_token
        return json.dumps(request).encode() + b'\n'

    def _decode_response(self, raw: bytes) -> Union[Dict, pd.DataFrame]:
        #print(raw)
        try:
            if self.use_binary:
                decompressed = lz4.frame.decompress(raw)
                response = msgpack.unpackb(decompressed, raw=False)
            else:
                response = json.loads(raw.decode().strip())
            
            # DataFrame 重建逻辑
            if isinstance(response, dict) and 'data_type' in response:
                if response.get('data_type') == 'pandas':
                    #print(response['data'])
                    return deserialize_dataframe(response['data'])
            return response
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute(self, func_name: str, kwargs) -> Union[Dict, pd.DataFrame]:
        try:
            # 编码请求
            request_data = self._encode_request(func_name, kwargs)
            self.sock.sendall(request_data)
    
            # 接收响应
            if self.use_binary:
                # 读取协议头（5字节：4字节长度 + 1字节协议类型）
                header = b''
                while len(header) < 5:
                    chunk = self.sock.recv(5 - len(header))
                    if not chunk:
                        raise ConnectionError("连接中断，未能接收完整头部")
                    header += chunk
                
                data_size = int.from_bytes(header[:4], byteorder='big')
                proto_type = header[4]
                
                # 读取数据体（根据长度循环读取）
                data = b''
                remaining = data_size
                while remaining > 0:
                    chunk = self.sock.recv(min(remaining, 4096))  # 分片读取
                    if not chunk:
                        raise ConnectionError("连接中断，数据接收不完整")
                    data += chunk
                    remaining -= len(chunk)
            else:
                # 文本模式持续读取直到换行符
                data = b""
                while True:
                    chunk = self.sock.recv(4096)
                    if not chunk:  # 连接关闭
                        break
                    data += chunk
                    if data.endswith(b'\n'):
                        break
    
            response = self._decode_response(data)
            if isinstance(response, dict) and response.get("status") == "error":
                raise APIError(response["message"])
            return response
    
        except socket.timeout:
            self.reconnect()
            raise ConnectionError("请求超时，请检查网络或服务状态")
        except socket.error as e:
            self.reconnect()
            raise ConnectionError(f"连接错误: {str(e)}")

    def set_token(self, token: str):
        self.auth_token = token

    def reconnect(self):
        """重连逻辑"""
        self.sock.close()
        self.sock = self._create_connection()

    def close(self):
        self.sock.close()

    def __getattr__(self, api_name):
        return lambda **kwargs: self(api_name, **kwargs)
    
    def __call__(self, api_name, **kwargs):
        err, response = None, None
        for attempt_index in range(self.request_attempt_count):
            try:
                response = self.execute(api_name, kwargs)
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

class APIError(Exception):
    pass

class ResponseError(Exception):
    """响应错误"""
    
# 初始化函数
def init_client(host: str = "localhost", port: int = 8080, use_binary: bool = True):
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = APIClientCore(host, port, use_binary)

def get_client():
    if _CLIENT is None:
        raise RuntimeError("Client not initialized. Call init_client() first")
    return _CLIENT