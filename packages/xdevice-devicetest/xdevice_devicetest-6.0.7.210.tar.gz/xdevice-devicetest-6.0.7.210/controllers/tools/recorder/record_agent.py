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
import os
import re
import time
import traceback

from xdevice import DeviceConnectorType
from xdevice import TestDeviceState
from xdevice import check_uitest_version
from xdevice import AgentMode
from xdevice import platform_logger

from devicetest import RESOURCE_PATH
from devicetest.core.variables import DeccVariable
from devicetest.log.logger import print_video, DeviceTestLog as log
from devicetest.controllers.tools.screen_agent import ScreenAgent
from devicetest.utils.util import get_forward_port
from devicetest.utils.util import check_device_file_md5
from devicetest.utils.util import compare_version
from devicetest.controllers.tools.recorder.rpc_manager import RpcManager

MIN_FRAME_COUNT = 10
UNIX_RECORD_SOCKET_NAME = "screen_record_grpc_socket"
LOG = platform_logger("ScreenRecord")


class RecordAgent:
    instance = {}

    def __new__(cls, device):
        """
        Singleton instance
        """
        if device.device_sn not in cls.instance:
            # 创建新的实例并存储
            cls.instance[device.device_sn] = super(RecordAgent, cls).__new__(cls)
        return cls.instance[device.device_sn]

    def __init__(self, device):
        if not hasattr(self, '_device'):
            self._device = device
            self.scrcpy_server_port = 5001
            self.scrcpy_port = None
            self.running_status = None
            self.server = None
            self.display_id = 0
            self.use_unix_socket = False
            self.uitest_version = ""
            clean_proxy_function = getattr(self._device, 'clean_proxy_function', None)
            if clean_proxy_function is not None:
                clean_proxy_function.append(self.terminate)

    def _init_rpc_server(self):
        LOG.debug("Init rpc server.")
        self.server = RpcManager(self._device, self._device.host, self.scrcpy_port)

    def start_and_check_rpc_server(self, display_id: int = 0):
        if self.display_id != display_id:
            self._stop_screen_process()
            self.display_id = display_id
        if self.running_status is None:
            self.running_status = self._start_scrcpy_server(display_id)
            self._init_rpc_server()
        return self.running_status

    @classmethod
    def _compare_software_version(cls, version, base_version: tuple, rex: str):
        """比较两个版本号的大小,若version版本大于base_version,返回True
        Args:
            version: str, version
            rex: version style rex
            base_version: list, base_version
        Example:
            version: "ALN-AL00 5.0.0.22(SP33DEVC00E22R4P1log)" base_version:[5.0.0.22]
            if version bigger than base_version or equal to base_version, return True, else return False
        """
        result = re.findall(rex, version)
        if result:
            version = tuple(result[0].split("."))
            if version > base_version:
                return True
        else:
            return True
        return False

    def _get_scrcpy_uitest_process(self) -> str:
        result = self._device.execute_shell_command('\"ps -ef | grep singleness\"')
        proc_running = result.split("\n")
        for data in proc_running:
            if ("singleness" in data and "grep" not in data
                    and "extension-name" in data and "libscreen_recorder" in data):
                data = data.split()
                result = self._device.execute_shell_command(
                    f'\"cat /proc/net/unix | grep {UNIX_RECORD_SOCKET_NAME}\"')
                if result:
                    result = result.split("\n")
                    for res in result:
                        if self.use_unix_socket and UNIX_RECORD_SOCKET_NAME in res:
                            return data[1]
                        # 如果当前版本是非UNIX版本，意外推了UNIX版本进行需要更新
                        elif not self.use_unix_socket and UNIX_RECORD_SOCKET_NAME in res:
                            # 退出不符合的录屏程序
                            self._device.execute_shell_command("kill -9 {}".format(data[1]), output_flag=False)
                            return None
                if not self.use_unix_socket:
                    return data[1]
                else:
                    # 若使用unix 但以老的so启动了，避免残留需要kill掉
                    self._device.execute_shell_command("kill -9 {}".format(data[1]), output_flag=False)
        return None

    def _push_scrcpy_server(self, server_name):
        # 判断是否存在或是否更新
        pc_path = os.path.join(RESOURCE_PATH, "res", "recorder", server_name)
        device_path = "/data/local/tmp/libscreen_recorder.z.so"
        if not check_device_file_md5(self._device, pc_path, device_path):
            # kill old process
            pid = self._get_scrcpy_uitest_process()
            if pid:
                self._device.execute_shell_command('\"kill -9 {}\"'.format(pid))
            LOG.debug("start update {}".format(device_path))
            self._device.execute_shell_command(f'\"rm -f {device_path}\"')
            self._device.push_file(pc_path, device_path)
            LOG.debug("Finish update server.")
        else:
            LOG.debug("Record server does not need to update.")

    def _start_scrcpy_serevr(self, display_id: int = 0):
        # 之前名字写错了，用于兼容hypium调用此方法，下个版本删除
        return self._start_scrcpy_server(display_id)

    def _start_scrcpy_server(self, display_id: int = 0):
        self.uitest_version = self._device.uitest_version
        self.use_unix_socket = self._device.ui_socket_mode

        base_version = tuple("4.1.4.6".split("."))
        if not check_uitest_version(self.uitest_version, base_version):
            LOG.error("Finish update server.")
            return False
        device_path = "/data/local/tmp/libscreen_recorder.z.so"
        device_file_md5 = self._device.execute_shell_command("md5sum {}".format(device_path))
        # 先判断设备中是否已有录屏so,如果有则优先尝试使用设备中的so进行录制
        if "No such file or directory" not in device_file_md5:
            if self._start_scrcpy_server_by_name(so_name="", display_id=display_id):
                LOG.debug("Using device recorder so start success")
                return True
            LOG.warning("Using device recorder so start failed, start update so.")
        # 遍历recorder文件夹下的so资源进行尝试
        recorder_folder = os.path.join(RESOURCE_PATH, "res", "recorder")
        for _, _, files in os.walk(recorder_folder):
            # 倒序尝试
            for file in list(reversed(files)):
                if not file.startswith("libscrcpy_server"):
                    continue
                # unix模式下只使用unix版本so
                if self.use_unix_socket and "unix" not in file:
                    continue
                # 非unix模式下只尝试非unix的so
                elif not self.use_unix_socket and "unix" in file:
                    continue
                # 分别尝试框架内的so的资源,看哪个能启动
                result = self._start_scrcpy_server_by_name(so_name=file,
                                                           display_id=display_id)
                # 如果能启动成功则直接返回即可
                if result:
                    LOG.debug("Using {} success".format(file))
                    return result
                else:
                    LOG.debug("Using {} fail".format(file))
        return False

    def _start_scrcpy_server_by_name(self, so_name: str, display_id: int = 0):
        # 1、推送资源
        if so_name != "":
            self._push_scrcpy_server(server_name=so_name)
        # 2、设置转发端口
        self.scrcpy_port = get_forward_port(self._device, self._device.host)
        if self.use_unix_socket:
            self._device.connector_command(
                "fport tcp:{} localabstract:{}".format(self.scrcpy_port, UNIX_RECORD_SOCKET_NAME))
        else:
            self._device.connector_command("fport tcp:{} tcp:{}".format(self.scrcpy_port, self.scrcpy_server_port))
        # 3、判断scrcpy是否已经启动
        pid = self._get_scrcpy_uitest_process()
        if pid:
            LOG.debug("record server is running. pid is {}".format(pid))
            return True
        # 4、启动scrcpy -m 1表示仅启动录屏模式
        self._device.execute_shell_command("/system/bin/uitest start-daemon singleness "
                                           "--extension-name libscreen_recorder.z.so -p {} -m 1 -screenId {}"
                                           .format(self.scrcpy_server_port, display_id))
        # 检测scrcpy是否正常启动
        pid = self._get_scrcpy_uitest_process()
        if pid is None:
            if self.use_unix_socket:
                self._device.connector_command(
                    "fport rm tcp:{} localabstract:{}".format(self.scrcpy_port, UNIX_RECORD_SOCKET_NAME))
            else:
                self._device.connector_command("fport rm tcp:{} tcp:{}".format(self.scrcpy_port,
                                                                               self.scrcpy_server_port))
            LOG.error("Start record server failed.")
            return False
        LOG.debug("Record server pid: {}".format(pid))
        time.sleep(1)
        return True

    def _check_software_version(self, base_version):
        software_version = self._device.execute_shell_command("param get const.product.software.version")
        LOG.debug("software version is {}".format(software_version))
        if (software_version and
                self._compare_software_version(software_version, base_version, r'\b\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}\b')):
            return True
        if software_version and "NOH" not in software_version:
            return False
        # mate40用的还是linux内核,所以还需要下面的判断
        openharmony_version = self._device.execute_shell_command("param get const.ohos.fullname")
        LOG.debug("openharmony version is {}".format(openharmony_version))
        if (openharmony_version and
                self._compare_software_version(openharmony_version, base_version,
                                               r'\b\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}\b')):
            return True
        return False

    @classmethod
    def get_device(cls, args):
        if len(args) == 0:
            return None
        _device = args[0]
        try:
            if not hasattr(_device, "screenrecorder"):
                _device = None
                # 适配Hypium的AW接口
                for arg in args:
                    _device = getattr(arg, "_device", None)
                    if _device is not None:
                        break
                if _device is None:
                    log.info("check device object failed.")
                    return None
        except ImportError:
            log.warning("failed in start_screen_recorder function.")
        return _device

    @classmethod
    def start_screen_recorder(cls, args):
        try:
            _device = cls.get_device(args)
            if _device is None:
                return
            if not hasattr(_device, "_agent_mode") or getattr(_device, "_agent_mode") != AgentMode.bin:
                return
            if not hasattr(_device, "screenrecorder") or _device.screenrecorder is False:
                return
            # 设备处于断开状态，不执行录屏
            if hasattr(_device, 'test_device_state') and _device.test_device_state != TestDeviceState.ONLINE:
                _device.log.warning("device state is not online")
                return
            display_id = 0
            hypium_config = getattr(_device, "_hypium_config", None)
            if hypium_config:
                display_id = getattr(hypium_config, "default_display_id", 0)
            agent = RecordAgent(_device)
            agent.start_and_check_rpc_server(display_id)
            # 已经开始录制就不在执行下面
            if hasattr(_device, "recorder_start_time") and getattr(_device, "recorder_start_time") is not None:
                return
            if hasattr(_device, "is_oh") and agent.start_and_check_rpc_server(display_id):
                agent.server.start_scrcpy()
                setattr(_device, "recorder_start_time", time.time())
            else:
                return
        except Exception as e:
            log.error(f"start screen recorder error, {e}")
            log.debug(traceback.format_exc())

    @classmethod
    def stop_screen_recorder(cls, file_name, file_desc, args, index: int):
        """stop recording screen
        file_name: str, 录屏视频文件名
        file_desc: str，录屏视频文件描述
        args: list, the list of devices
        """
        file_name = file_name or "stepepr"
        try:
            _device = cls.get_device(args)
            if _device is None:
                return

            if not hasattr(_device, "screenrecorder") or _device.screenrecorder is False:
                return
            # 设备处于断开状态，不执行录屏
            if hasattr(_device, 'test_device_state') and _device.test_device_state != TestDeviceState.ONLINE:
                _device.log.warning("device state is not online")
                return
            agent = RecordAgent(_device)
            cur_case = DeccVariable.cur_case()
            # 非bin模式就只做截图
            if not hasattr(_device, "_agent_mode") or getattr(_device, "_agent_mode") != AgentMode.bin:
                _device.log.warning("Record step only support in bin mode, using screenshot instead.")
                return

            path, link = ScreenAgent.get_image_dir_path(_device, file_name, ext=".mp4", exe_type="videoRecord")
            if hasattr(_device, "is_oh"):
                if not hasattr(_device, "recorder_start_time"):
                    return
                frame_count = agent.server.stop_scrcpy()
                if hasattr(_device, "recorder_start_time") and getattr(_device, "recorder_start_time") is not None:
                    setattr(_device, "recorder_start_time", None)
                if int(frame_count) < MIN_FRAME_COUNT:
                    _device.log.debug("video frame is too short, use screenshot instead.")
                    return
                _device.pull_file("/data/local/tmp/mytest.mp4", path)
            else:
                return
            print_video(link, path, ScreenAgent.resize_image(path, file_type="video"))
            cur_case.update_step_info(index, screenshot={"link": link.replace("\\", "/"), "name": file_desc})
        except Exception as e:
            log.error(f"stop screen recorder error, {e}")
            log.debug(traceback.format_exc())

    def _stop_screen_process(self):
        pid = self._get_scrcpy_uitest_process()
        if pid:
            self._device.execute_shell_command("kill -9 {}".format(pid))
        self.scrcpy_port = None
        self.running_status = None
        self.server = None

    def terminate(self):
        if self.scrcpy_port is not None and isinstance(self.scrcpy_port, int):
            if hasattr(self._device, "is_oh") or \
                    self._device.usb_type == DeviceConnectorType.hdc:
                log.debug("RecordAgent terminate")
                if self.use_unix_socket:
                    self._device.connector_command(
                        "fport rm tcp:{} localabstract:{}".format(self.scrcpy_port, UNIX_RECORD_SOCKET_NAME))
                else:
                    self._device.connector_command("fport rm tcp:{} tcp:{}".format(self.scrcpy_port,
                                                                                   self.scrcpy_server_port))
                pid = self._get_scrcpy_uitest_process()
                if pid:
                    self._device.execute_shell_command("kill -9 {}".format(pid))
                RecordAgent.instance.pop(self._device.device_sn)
                self.scrcpy_port = None
