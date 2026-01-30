#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2022 Huawei Device Co., Ltd.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import json
import socket
import threading
import traceback

from devicetest.core.constants import DeviceConstants
from devicetest.error import ErrorMessage
from devicetest.utils.time_util import TimeHandler
from devicetest.utils.util import get_local_ip_address
from devicetest.core.exception import RPCException


class RPCProtocolError(RPCException):
    """
    Raised when there is some error in exchanging data with server on device.
    """
    NO_RESPONSE_FROM_HANDSHAKE = "No response from handshake."
    NO_RESPONSE_FROM_SERVER = "No response from server."
    MISMATCHED_API_ID = "Mismatched API id."


class OSBase(object):
    def __init__(self, port=DeviceConstants.PORT, addr=DeviceConstants.HOST,
                 timeout=300, device=None):
        self.lock = threading.RLock()
        self.host = None
        self.port = None
        self.timeout = None
        self.device = None
        self.log = None
        self.socket_log = None
        self.socket_in_use = None
        self.sock = None
        self.init(port, addr, timeout, device)

    def __del__(self):
        self.close()

    def init(self, port=DeviceConstants.PORT, addr=DeviceConstants.HOST,
             timeout=300, device=None):
        self.host = addr
        self.port = int(port)
        self.timeout = device.rpc_timeout if device.rpc_timeout != 300 else timeout

        self.device = device
        self.log = self.device.log

        try:
            self.socket_log = None  # 日志采集socket
            self.socket_in_use = []  # 记录使用中的socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.log.debug("set rpc timeout: " + str(self.timeout))
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.port))
        except (TimeoutError, socket.timeout):
            self.log.error("[OSBase] Failed to create socket connection!")
            self.close()
            raise
        except Exception:
            self.log.debug(traceback.format_exc())
            self.log.error("[OSBase] init error")
            self.close()
            raise

    def set_timeout(self, timeout):
        self.log.debug("set the temporary timeout with {}".format(timeout))
        self.sock.settimeout(timeout)

    def reset_timeout(self):
        self.log.debug("restore timeout {}".format(self.timeout))
        self.sock.settimeout(self.timeout)

    def close(self):
        if self.sock is not None:
            try:
                self.log.debug("close socket for device")
                self.sock.close()
            except Exception as exception:
                self.log.debug(exception)
                pass

            self.sock = None

        if self.socket_log is not None:
            try:
                self.log.debug("close socket for log collector")
                self.socket_log.close()
            except Exception as exception:
                self.log.debug(exception)
                pass

            self.socket_log = None

    def create_request(self, module, method, *args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            args = "context", None
        elif len(args) == 1:
            if isinstance(args[0], dict):
                args = json.dumps(args[0],
                                  ensure_ascii=False, separators=(',', ':'))
            args = "context", args
        elif len(kwargs) != 0:
            args = "context", json.dumps(kwargs,
                                         ensure_ascii=False,
                                         separators=(',', ':'))

        self.log.debug("%s.%s(%s)" % (module, method, str(args[1])))
        module = DeviceConstants.MODULE_PACKAGE + module
        ret = self._rpc(module, method, *args)
        self.log.debug("Recv: {}".format(ret))
        return ret

    def _rpc(self, module, method, *args):
        data = {'module': module,
                'method': method,
                'params': args,
                'request_id': TimeHandler.get_now_datetime()}

        request = json.dumps(data,
                             ensure_ascii=False,
                             separators=(',', ':'))
        return self._safe_send(request, is_bin=False)

    def generate_param(self, generate_param_type, value, index):
        # @ReservedAssignment
        param = {"type": generate_param_type,
                 "value": value,
                 "index": index}
        return json.dumps(param, ensure_ascii=False, separators=(',', ':'))

    def _safe_send(self, request, sock=None, isbyte=False, is_bin=False):
        # 增加本地ip输入到设备侧
        local_host = get_local_ip_address()
        if local_host is None:
            local_host = self.device.host
        send_request = json.loads(request)
        send_request["client"] = \
            local_host if local_host is not None else "127.0.0.1"
        send_request = json.dumps(send_request, ensure_ascii=False,
                                  separators=(',', ':'))
        ret = None
        try:
            self.log.debug("sendRequest: {}".format(send_request))
            ret = self._send(send_request, sock=sock, isbyte=isbyte, is_bin=is_bin)
            self.log.debug("@recv rpc msg: {}".format(ret))
            if b'' == ret:
                return b''
        except Exception as e:
            self.log.debug(traceback.format_exc())
            self.log.error("[OSBase] Exception on request to device")
            if self.device is not None:
                if self.device.reconnecttimes == DeviceConstants.RECONNECT_TIMES:
                    self.device.reconnecttimes = 0
                    error_msg = ErrorMessage.Device.Code_0202001.format("OSBase", DeviceConstants.RECONNECT_TIMES)
                    self.log.error(error_msg)
                    raise Exception(error_msg) from e
                self.log.debug(
                    "[OSBase] %d times to reconnect rpc socket "
                    "device: %s" % (self.device.reconnecttimes + 1,
                                    self.device.device_id))
                self.device.reconnecttimes += 1
                self.device.reconnect()
                self.log.debug(
                    "[OSBase] Send request {} again".format(request))
                ret = self._safe_send(request, sock=sock, isbyte=isbyte, is_bin=is_bin)
                self.log.debug("@recv rpc msg: {}".format(ret))
                if b'' == ret:
                    return b''
                self.device.reconnecttimes = 0
        if ret == "false":
            return False
        if ret == "true":
            return True
        return ret

    def _send(self, request, sock=None, isbyte=False, is_bin=False):
        if sock is None:
            sock = self.sock

        if sock is not None:
            if is_bin:
                sock.sendall(request.encode("utf-8") + b'\n')
            else:
                sock.sendall(("1" + request).encode("utf-8") + b'\n')

            response = b''
            while True:
                data = sock.recv(1024 * 1024)
                response += data
                if len(data) == 0 or data[-1:] == b'\n':
                    break

            if len(response) == 0:
                # Windows上,当客户端在接收消息的时候,服务端被杀,
                # 客户端不会抛异常
                # ,会收到0字节;正常服务器响应空字符串时,客户端接收的是"\n"
                raise RPCException(ErrorMessage.Device.Code_0202004)

            if isbyte:
                return response

            response = str(response, encoding="utf-8").strip()

            if response == "false":
                return False
            elif response == "true" or response == b'':
                return True
            return response
        return False

    def _rpc_for_log(self, module, method, *args):
        """
        @summary: 日志采集专用通道
        """
        data = {'module': module,
                'method': method,
                'params': args,
                'request_id': TimeHandler.get_now_datetime()}
        request = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        self._init_log_socket()
        return self._safe_send(request, sock=self.socket_log)

    def _init_log_socket(self):
        if self.socket_log is None:
            self.log.debug("create parallel socket for collect log")
            self.socket_log = self.__socket(is_log=True)

    def __socket(self, is_log=False):
        if not is_log:
            self.log.debug("self.sock in use, create a new parallel socket")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.port))
        return sock
