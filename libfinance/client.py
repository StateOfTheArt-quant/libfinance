#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import socket
import threading
import warnings

import pdb

import thriftpy2 as thriftpy
from thriftpy2.rpc import make_client
from thriftpy2.transport import TTransportException
try:
    from thriftpy2.protocol.cybin import ProtocolError
except ImportError:
    ProtocolError = type('FakeProtocolError', (Exception,), {})

#from libfinance.thriftclient import libfinance_thrift
from libfinance.utils.serialize import serialize_object, deserialize_object
from libfinance.utils.loader import load_thrift_module

socket_error = (TTransportException, socket.error, ProtocolError)

libfinance_thrift = load_thrift_module(__file__, "libfinance.thrift")


class ResponseError(Exception):
    """响应错误"""
    

    
class LibFinanceClient(object):

    _threading_local = threading.local()
    _auth_params = {}
    #_default_host = "0.0.0.0"
    _default_host = "libfinance.tech"#"101.201.30.6"
    _default_port = 9090

    request_timeout = 300
    request_attempt_count = 3

    def __init__(self, host=None, port=None, username="", password="", token=""):
        self.host = host or self._default_host
        self.port = int(port or self._default_port)
        self.username = username
        self.password = password
        self.token = token

        assert self.host, "host is required"
        assert self.port, "port is required"
        #assert self.username or self.token, "username is required"
        #assert self.password or self.token, "password is required"

        self.client = None
        self.inited = False
        self.not_auth = True
        self.compress = True
        self.data_api_url = ""
        self._http_token = ""
        
        self._create_client()

    def _create_client(self):
        self.client = make_client(
            libfinance_thrift.LibfinanceService,
            self.host,
            self.port,
            timeout=(self.request_timeout * 1000)
        )
        return self.client
    
    def __getattr__(self, api_name):
        return lambda **kwargs: self(api_name, **kwargs)
    
    def __call__(self, api_name, **kwargs):
        err, result = None, None
        for attempt_index in range(self.request_attempt_count):
            try:
                result = self.query(api_name, kwargs)
                break
            except socket_error as ex:
                if (
                        isinstance(ex, socket.timeout) or
                        "TSocket read 0 bytes" in str(ex) or
                        not self._ping_server()
                        ):
                    self._reset()
                err = ex
                if attempt_index < self.request_attempt_count - 1:
                    time.sleep(0.6)
            except ResponseError as ex:
                err = ex

        if result is None and isinstance(err, Exception):
            if "TSocket read 0 bytes" in str(err):
                raise Exception("连接被关闭，请减少数据查询量或检查网络后重试")
            raise err

        return result
    
    def query(self, api_name, params):
        
        request = libfinance_thrift.St_Query_Req()
        request.api_name = api_name
        request.params = serialize_object(params)
        
        
        result = None
        try:
            #pdb.set_trace()
            #self.ensure_auth()
            response = self.client.query(request)
            #print(response)
            #pdb.set_trace()
            if response.status is False:
                # error occur
                # raise RuntimeError(response.msg)
                warnings.warn(response.msg)

            # get process result
            result = deserialize_object(response.result)
        except Exception as e:
            print(e)
            raise RuntimeError("error:{}".format(e))
        
        return result


_CLIENT = LibFinanceClient()


def get_client():
    return _CLIENT



            
if __name__ == "__main__":
    client = LibFinanceClient()
    
    
    #output = client.get_trading_dates(start_date="2024-01-01",end_date="2024-02-22")
    #print(output)
    
    output = client.get_trading_dates("2024-01-01","2024-02-22")
    print(output)
    