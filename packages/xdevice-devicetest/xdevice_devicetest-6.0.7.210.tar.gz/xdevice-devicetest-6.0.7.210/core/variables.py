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
import shutil
import threading
import time
from typing import List, Union

from devicetest.core.constants import RunResult
from devicetest.core.constants import RunSection
from devicetest.core.record import ProjectRecord
from devicetest.log.logger import print_image, DeviceTestLog as log
from devicetest.utils.time_util import TimeHandler
from devicetest.utils.util import get_base_name
from xdevice import is_env_pool_run_mode
from xdevice import AgentMode
from xdevice import IDevice
from xdevice import UserConfigManager
from xdevice import Variables


def set_devices_test_args(devices: List[IDevice], config: Union[dict, UserConfigManager]):
    task_args = config.taskargs if isinstance(config, UserConfigManager) else config
    for device in devices:
        # 先恢复为默认的运行参数
        setattr(device, "screenshot", False)
        setattr(device, "screenrecorder", False)

        # 控制agent_mode的运行模式，仅支持鸿蒙设备
        if hasattr(device, "set_agent_mode"):
            if task_args.get("agent_mode", "").lower() == AgentMode.hap:
                device.set_agent_mode(AgentMode.hap)
            else:
                # 默认在bin模式下运行
                device.set_agent_mode(AgentMode.bin)
        # 控制aw接口截图
        if str(task_args.get("screenshot", "")).lower() == "true":
            setattr(device, "screenshot", True)
        # 控制aw接口截图转录屏，当前仅支持鸿蒙设备
        if str(task_args.get("screenrecorder", "")).lower() == "true" and hasattr(device, "is_oh"):
            setattr(device, "screenrecorder", True)



def get_decrypt_resource_path():
    return Variables.res_dir


def set_resource_path(resource_path):
    DeccVariable.project.resource_path = resource_path


def get_testsuit_path():
    return DeccVariable.project.test_suite_path


def get_project_path():
    """
    get project path
    :return: prcject_path
    """
    try:
        if DeccVariable.project.project_path:
            return DeccVariable.project.project_path

        project_path = os.path.dirname(Variables.top_dir)
        if project_path is None:
            log.info("project path is None.")
            raise Exception("")
        if not os.path.exists(project_path):
            log.info("project path not exists.")
            log.debug("project path:{}".format(project_path))
            raise Exception("")
        return project_path

    except Exception as error:
        raise error


class CurCase:

    def __init__(self, _log):
        # 用例级别参数
        self.log = _log
        self.step_total = 0  # tests 数
        self.run_section = ""  # RunSection.SETUP
        self.case_result = RunResult.PASSED  # 当前用例执行结果
        self.name = ''  # 类方法名，即：用例名case_id
        self.suite_name = ""  # 用例对应哪个测试套
        self.sub_name = ""  # 用例的子用例
        self.error_msg = ''  # 用例失败信息
        self.case_screenshot_dir = None  # 当前用例失败截图的图片保存路径
        self.case_flash_error_msg = False  # 记录当前y用例是否更新了errorMsg
        self.is_upload_method_result = False  # 记录当前用例是否上报过第一个失败步骤

        self.step_section = RunSection.SETUP  # 用例方法setup/test/teardown
        self.step_error_msg = ''  # 当前步骤的失败信息
        self.step_fail_msg = ''  # 用户指定的失败信息
        self.step_result = RunResult.PASSED  # 当前步骤执行结果
        self.sub_steps_info = []  # 记录测试用例的子用例的步骤信息，如步骤名称、执行结果、耗时、截图等
        self.steps_info = []  # 记录测试用例（含测试套子用例）的步骤信息，如步骤名称、执行结果、耗时、截图等
        self.suite_steps_info = []  # 记录测试套的的步骤信息，如步骤名称、执行结果、耗时、截图等

        self.test_method = TestMethod(self.log)
        self.cur_check_cmd = CurCheckCmd()

        # 失败截图相关
        self.checkepr = False  # 啥含义？
        self.image_num = 0
        self.video_num = 0
        self.dump_xml_num = 0

        # prepare相关
        self.status = 0
        self.description = ''  # VAR.CurCase.Description  memoryLeakReport.py用到
        self.log_details_path = "./log/test_run_details.log"
        self.log_path = "./log/test_run_summary.log"
        self.report_path = ''
        self.iperf_path = None  # wifi相关

        # windows
        self.win_capture_path = ''  # WinCapturePath
        self.exact_start_time = ''  # memoryLeakReport.py用到VAR.CurCase.ExactStartTime
        self.start_time = ''  # memoryLeakReport.py用到VAR.CurCase.StartTime

        self.case_name_file_path = ''  # VAR.CurCase.CaseName.FilePath
        self.device_log = DeviceLog()

        self.sub_case_instance = None
        self.case_instance = None
        self.suite_instance = None

        self.devices = list()

        self.is_capture_step_screen = False
        self.is_record_step_screen = False
        self.set_step_screen()

        self.record_step_name = None
        self.record_step_index = None

    def set_step_screen(self):
        if Variables.config.taskargs.get("screenrecorder", "").lower() == "true":
            self.is_record_step_screen = True
        else:
            self.is_capture_step_screen = True

    @property
    def subcase(self):
        return self.sub_case_instance

    @property
    def testcase(self):
        return self.case_instance

    @property
    def testsuite(self):
        return self.suite_instance

    def set_sub_case_instance(self, instance):
        self.sub_case_instance = instance
        if instance:
            self.devices = instance.devices

    def set_case_instance(self, instance):
        self.case_instance = instance
        if instance:
            self.devices = instance.devices

    def set_suite_instance(self, instance):
        self.suite_instance = instance
        if instance:
            self.devices = instance.devices

    def set_error_msg(self, error_msg):
        self.log.debug("set CurCase error msg as: {}".format(error_msg))
        self.error_msg = error_msg

    def set_run_section(self, run_section):
        self.log.debug("set CurCase run section as: {}".format(run_section))
        self.run_section = run_section

    def set_case_result(self, case_result):
        self.case_result = case_result
        self.log.debug(
            "set CurCase case result as: {}".format(self.case_result))

    def set_step_total(self, step_total):
        self.step_total = step_total
        self.log.debug(
            "set CurCase step total as: {}".format(self.step_total))

    def set_sub_name(self, name):
        self.sub_name = name
        self.log.debug("set CurCase sub name as: {}".format(self.sub_name))

    def set_name(self, name):
        self.name = name
        self.log.debug("set CurCase name as: {}".format(self.name))

    def set_suite_name(self, name):
        self.suite_name = name
        self.log.debug("set CurCase suite name as: {}".format(self.suite_name))

    def set_step_section(self, step_section):
        self.step_section = step_section
        self.log.debug(
            "set CurCase step section as: {}".format(self.step_section))

    def get_current_case_name(self):
        if self.sub_name:
            return self.sub_name
        else:
            return self.name

    def set_case_screenshot_dir(self, test_suite_path, task_report_dir, cur_case_full_path,
                                repeat=1, repeat_round=1):
        round_folder = f"round{repeat_round}" if repeat > 1 else ""
        case_screenshot_dir = os.path.join(task_report_dir, "details", round_folder)
        if is_env_pool_run_mode():
            case_screenshot_dir = task_report_dir
        case_abs_path_base_name = get_base_name(cur_case_full_path, is_abs_name=True)
        if case_abs_path_base_name and test_suite_path:
            self.log.debug("case_abs_path_base_name:{}, test_suite_path:{}"
                           .format(case_abs_path_base_name, test_suite_path))
            _list = case_abs_path_base_name.split(test_suite_path)
            if len(_list) == 2:
                case_screenshot_dir = os.path.abspath(
                    os.path.join(task_report_dir, _list[1].strip(os.sep)))
        self.case_screenshot_dir = case_screenshot_dir
        self.log.debug("set case screenshot dir path as: {}".format(
            self.case_screenshot_dir))

    def get_screenshot_dir(self):
        pth = os.path.join(self.case_screenshot_dir, self.suite_name, self.get_current_case_name())
        os.makedirs(pth, exist_ok=True)
        return pth

    def init_stage_var(self, test_method_name,
                       run_section=None, is_error_msg=False):
        if run_section:
            self.set_run_section(run_section)
        self.test_method.init_test_method(test_method_name,
                                          is_error_msg=is_error_msg)

    def set_checkepr(self, checkepr):
        self.checkepr = checkepr
        self.log.debug("set project checkepr as: {}".format(self.checkepr))

    def flash_error_msg_and_result(self, error_msg):
        if not self.error_msg:
            self.set_error_msg(error_msg)
        if not self.test_method.error_msg:
            self.test_method.set_error_msg(error_msg)
        if self.case_result == RunResult.PASSED:
            self.set_case_result(RunResult.FAILED)
        if self.test_method.result == RunResult.PASSED:
            self.test_method.set_result(RunResult.FAILED)

    def get_steps_info(self):
        return self.end_previous_step()

    def get_step_index(self):
        steps_info = self._get_steps_info_obj()
        return len(steps_info) - 1

    def set_step_info(self, name, **kwargs):
        name = str(name)
        steps_info = self.end_previous_step()
        index = len(steps_info)
        log.info(f'<div class="step" id="{index}">{name}</div>')
        step = {
            "name": name, "error": "", "cost": 0, "screenshot": [], "extras": {},
            # 下划线开头的字段是内部属性
            "_timestamp": time.time()
        }
        self._update_step_info(step, **kwargs)
        steps_info.append(step)
        self._capture_step_screen(name, index)
        return index

    def set_ui_step_info(self, name, shot_paths, device, **kwargs):
        """记录ui自适应图片"""
        steps_info = self._get_steps_info_obj()
        index = len(steps_info)
        self._show_ui_step_screen(name, shot_paths, device)
        return index

    def _show_ui_step_screen(self, api_name, shot_paths, device):
        """
        展示ui自适应图片
        """
        new_shots = []
        from devicetest.controllers.tools.screen_agent import ScreenAgent
        for shot in shot_paths:
            if os.path.exists(shot):
                try:
                    file_extension = os.path.splitext(shot)[1]
                    name = "ui_adaptive_" + str(os.path.basename(shot).replace(file_extension, "")) + "_" + api_name
                    path, link = ScreenAgent.get_ui_step_picture(TimeHandler.get_now_datetime(), device,
                                                                 ext=file_extension)
                    shutil.move(shot, path)
                    link = link.replace("\\", "/")
                    desc = "[自适应历史基线]"
                    if "original_step" not in name:
                        desc = "[自适应查找结果]"
                        self.update_step_shots(link, name)
                    print_image(link, path, name, ScreenAgent.resize_image(path), desc=desc)
                    time.sleep(0.01)
                except Exception as e:
                    self.log.error(e)
        return new_shots

    def end_previous_step(self):
        """结束上一个step"""
        steps_info = self._get_steps_info_obj()
        if len(steps_info) > 0:
            last_step = steps_info[-1]
            # 结束录屏
            self._stop_record_step_screen()
            # 计算前后step记录的时间差
            cost = round(time.time() - last_step.get("_timestamp"), 3)
            self._update_step_info(last_step, cost=cost)
        return steps_info

    def update_step_info(self, index, **kwargs):
        steps_info = self._get_steps_info_obj()
        max_index = len(steps_info) - 1
        if not 0 <= index <= max_index:
            log.warning(f"update step info failed, index must be in [0, {max_index}]")
            return
        step = steps_info[index]
        self._update_step_info(step, **kwargs)

    def update_step_shots(self, link, name):
        if not link or not name:
            return
        steps_info = self._get_steps_info_obj()
        if len(steps_info) == 0:
            return
        step = steps_info[-1]
        self._update_step_info(step, screenshot={"link": link.replace("\\", "/"), "name": name})

    @staticmethod
    def _update_step_info(step, **kwargs):
        """更新步骤的信息"""
        # builtin_keys，步骤基本信息
        builtin_keys = ["name", "error", "cost", "screenshot", "_timestamp"]
        for k, v in kwargs.items():
            if k not in builtin_keys:
                # extras，步骤额外信息
                step.get("extras").update({k: str(v)})
                continue
            # 更新step记录
            if k == "error":
                step.update({k: str(v)})
            elif k == "screenshot":
                step.get("screenshot").append(v)
            else:
                step.update({k: v})

    def _get_steps_info_obj(self):
        """返回测试套或测试用例的记录表"""
        if self.sub_case_instance:
            return self.sub_steps_info
        elif self.case_instance:
            return self.steps_info
        else:
            return self.suite_steps_info

    def _capture_step_screen(self, step_name, index: int):
        """
        take a screenshot of each device after each step is performed
        """
        from devicetest.controllers.tools.screen_agent import ScreenAgent
        if self.is_capture_step_screen:
            for device in self.devices:
                ScreenAgent.screenshot(device, step_name)
        else:
            self._start_record_step_screen(step_name, index)

    def _start_record_step_screen(self, step_name: str, index: int):
        if not self.is_record_step_screen:
            return
        from devicetest.controllers.tools.recorder.record_agent import RecordAgent
        self.record_step_name = step_name
        self.record_step_index = index
        for device in self.devices:
            RecordAgent.start_screen_recorder([device])

    def _stop_record_step_screen(self):
        if not self.is_record_step_screen:
            return
        # 等待1S保证能录制到后面的响应
        time.sleep(0.5)
        from devicetest.controllers.tools.recorder.record_agent import RecordAgent
        for device in self.devices:
            RecordAgent.stop_screen_recorder(TimeHandler.get_now_datetime(), self.record_step_name, [device],
                                             self.record_step_index)


class TestMethod:
    def __init__(self, _log):
        # 步骤级别参数
        self.log = _log
        self.name = 'setup'
        self.result = RunResult.PASSED
        self.level = ''
        self.error_msg = ''
        self.method_return = ''
        self.func_ret = []
        self.step_flash_fail_msg = False

    def set_result(self, result=None):
        self.result = result or RunResult.PASSED
        self.log.debug(
            "set TestMethod result as: {}".format(self.result))

    def set_error_msg(self, error_msg):
        self.error_msg = error_msg
        self.log.debug(
            "set TestMethod error msg as: {}".format(self.error_msg))

    def init_test_method(self, name, is_error_msg=False):
        self.level = '',
        self.name = name,
        self.result = RunResult.PASSED
        if is_error_msg:
            self.error_msg = ''
        self.func_ret.clear()

    def init_aw_method(self):
        self.error_msg = ''
        self.result = RunResult.PASSED
        self.step_flash_fail_msg = False  # 记录当前步骤是否更新了failMsg
        self.func_ret.clear()
        self.log.debug("init aw method.")


class CurStep:
    pass


class Prepare:
    def __init__(self):
        self.path = ''
        self.config = {}

    def set_prepare_path(self, path):
        if path:
            self.path = path
        log.debug("prepare path:{}".format(path))


class Settings:
    language = ''
    product = ''  # VAR.Settings.Product


class Event:
    configs = {}  # VAR.Event.Configs


class RedirectLog:
    task_name = ""  # VAR.Project.RedirectLog.TaskName


class DeviceLog:
    ftp_path = []  # VAR.CurCase.DeviceLog.FthPath


class ProjectVariables:
    def __init__(self, _log):
        # 工程级别参数
        self.log = _log
        self.record = ProjectRecord(_log)
        self.project_path = ''  # xdevice工程路径
        self.aw_path = ''  # 测试套aw路径
        self.testcase_path = ''
        self.settings = None
        self.resource_path = ''  # 测试套工程resource路径
        self.test_suite_path = ''  # 测试套工程路径
        self.task_report_dir = ''  # 测试用例的框架日志路径
        self.prepare = Prepare()  # prepare 相关
        self.cur_case_full_path = ''  # 记录当前正执行用例全路径
        self.execute_case_name = None  # 记录当前正执行用例id
        self.config_json = {}  # 用户自定义的公共的参数
        self.property_config = []  # 用户自定义的设备相关的参数
        self.retry_test_list = []
        self.devicename = {}
        self.step_debug = ''

        self.monkey = False  # extension/monkey/monkey.py VAR.Project.Monkey
        self.task_id = ""  # VAR.Project.TaskID memoryLeakReport.py中用到，先记录该字段 VAR。Projec.TaskId
        self.settings = Settings()  # target中用到：VAR。Settings.Language
        self.total = 0  # VAR.Project.Total
        self.start_time = ''  # memoryLeakReport.py用到VAR.Project.StartTime
        self.exact_start_time = ''  # memoryLeakReport.py用到VAR.Project.ExactStartTime
        self.finish = 0  # VAR.Project.Finish

        self.config = {
        }

        self.event = Event()
        self.test_file = ''  # VAR.Project.TestFile
        self.is_ticc_server = False  # GlobalParam.IS_TICC_SERVER
        self.redirect_log = RedirectLog()

    def set_project_path(self, project_path=None):
        self.project_path = project_path or get_project_path()
        self.log.debug("project path is: {}".format(self.project_path))

    def set_aw_path(self, aw_path):
        if aw_path:
            self.aw_path = aw_path
            self.log.debug("aw path is: {}".format(self.aw_path))

    def set_testcase_path(self, testcase_path):
        self.testcase_path = testcase_path
        self.log.debug("testcase path is: {}".format(self.testcase_path))

    def set_settings(self, settings):
        if settings:
            self.settings = settings
        self.log.debug("settings is: {}".format(self.settings))

    def set_test_suite_path(self, test_suite_path):
        if test_suite_path:
            self.test_suite_path = test_suite_path
        self.log.debug("test suite path is: {}".format(self.test_suite_path))

    def set_task_report_dir(self, task_report_dir):
        if task_report_dir:
            self.task_report_dir = task_report_dir
        self.log.debug("task report dir: {}".format(self.task_report_dir))

    def set_resource_path(self, resource_path):
        if resource_path:
            self.resource_path = resource_path
        self.log.debug("resource path is: {}".format(self.resource_path))

    def set_config_json(self, config_json):
        self.config_json = config_json
        self.log.debug("config json is: {}".format(self.config_json))

    def set_property_config(self, property_config):
        self.property_config = property_config
        self.log.debug("property config is: {}".format(self.property_config))

    def set_devicename(self, devicename):
        if devicename:
            self.devicename = devicename
        self.log.debug("devicename is: {}".format(self.devicename))


class CurCheckCmd:
    def __init__(self):
        # 用例校验参数？
        self.through = ""
        self.expect = ""
        self.actual = ""

    def get_cur_check_status(self):
        if all([self.through, self.expect, self.actual]):
            return True
        return False

    def get_cur_check_msg(self):
        return "{}, expect:{}, actual:{}".format(self.through, self.expect,
                                                 self.actual)


class DeccVariable:
    __cur_case = {}
    __thread_lock = threading.Lock()
    project = ProjectVariables(log)

    @classmethod
    def set_project_obj(cls, project_obj):
        log.info("init DeccVariable project object")
        cls.project = project_obj

    @classmethod
    def set_cur_case_obj(cls, cur_case_obj: CurCase):
        log.info("init DeccVariable cur case object")
        with cls.__thread_lock:
            cls.__cur_case[cls.__cur_case_key()] = cur_case_obj

    @classmethod
    def cur_case(cls) -> Union[CurCase, None]:
        with cls.__thread_lock:
            return cls.__cur_case.get(cls.__cur_case_key(), None)

    @classmethod
    def __cur_case_key(cls):
        return threading.current_thread().ident

    @classmethod
    def reset(cls):
        log.info("reset DeccVariable")
        with cls.__thread_lock:
            key = cls.__cur_case_key()
            if key in cls.__cur_case:
                cls.__cur_case.pop(key)
