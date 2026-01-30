#!/usr/bin/python3.4
# coding=utf-8
#

# Copyright (C) 2016 Huawei Technologies Co., HUTAF xDevice
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import copy
import sys
import os
import traceback
import threading

from xdevice import ConfigConst
from xdevice import calculate_elapsed_time
from xdevice import get_cst_time
from xdevice import get_file_absolute_path
from xdevice import FilePermission
from xdevice import CaseEnd
from xdevice import Binder
from xdevice import Variables
from xdevice import ReportConstant
from xdevice import ResultCode
from xdevice import LifeCycle
from xdevice import redirect_driver_log_begin
from xdevice import redirect_driver_log_end
from xdevice import get_driver_log_path

from devicetest.core.constants import RunResult
from devicetest.core.constants import FileAttribute
from devicetest.core.test_case import UpdateStep
from devicetest.core.variables import DeccVariable
from devicetest.core.variables import ProjectVariables
from devicetest.error import ErrorMessage
from devicetest.report.generation import cache_case_log_begin
from devicetest.report.generation import cache_case_log_end
from devicetest.report.generation import generate_case_report
from devicetest.utils.util import get_base_name
from devicetest.utils.util import get_dir_path
from devicetest.utils.util import import_from_file
from devicetest.utils.util import save_steps_info


class TestSuite:
    """Base class for all test classes to inherit from.

    This class gets all the controller objects from test_runner and executes
    the test cases requested within itself.

    """

    def __init__(self, configs, path):
        self.configs = configs
        self.devices = []
        self.device1 = None
        self.device2 = None
        # 透传的参数
        self.pass_through = Variables.config.pass_through
        self.set_devices(self.configs["devices"])
        self.path = path
        self.log = self.configs["log"]
        self.error_msg = ''
        self.trace_info = ''
        self.case_result = dict()
        self.suite_name = self.configs.get("suite_name")
        self._request = self.configs.get("request")
        # 以“#”分割，是为了适配sub_case的执行场景
        # 白名单用例
        self.white_case_list = [l.split("#")[0] for l in self._request.get_ta_class()]
        # 黑名单用例
        self.black_case_list = [l.split("#")[0] for l in self._request.get_ta_not_class()]
        # 初始化透传参数的列表
        self.arg_list = dict()
        self.app_result_info = dict()
        self._test_args_para_parse(self.configs["testargs"])
        # 往DeviceTest的用例中注入logger并防止重复初始化测试套级别的变量
        self.inject_logger = None
        self.cur_case = None
        # device log
        self.device_log = dict()
        self.hilog = dict()
        self.log_proc = dict()
        self.hilog_proc = dict()

        self.suite_case_results = []
        self.suite_log_hdl = None

        # device录屏截图属性
        self.devices_media = dict()

        self._repeat = self._request.config.repeat
        self._repeat_round = self._request.get_repeat_round()
        self._round_folder = f"round{self._repeat_round}" if self._repeat > 1 else ""

        self.state_machine = None
        self.listeners = self.configs["listeners"]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _device_close(self):
        self.log.debug("Start device close")
        for device in self.devices:
            device.close()
        self.log.debug("Finish device close.")

    def run(self):
        report_path = os.path.join("details", self._round_folder, self.suite_name, self.suite_name + ".html")
        # 记录录屏和截图属性
        self._get_screenrecorder_and_screenshot()
        try:
            self.cur_case.set_suite_instance(self)
            # 1.先判断是否在json中指定，否则先收集当前文件夹下所有testcase得到run_list
            subcase_names, subcase_items = [], []
            for case_path in self._get_case_list(self.path):
                case_name = get_base_name(case_path)
                if (self.black_case_list and case_name in self.black_case_list) \
                        or (self.white_case_list and case_name not in self.white_case_list):
                    self.log.warning(f"case name {case_name} is in '-ta notClass' or not in '-ta class', ignored")
                    continue
                subcase_names.append(case_name)
                subcase_items.append((case_name, case_path))
            # 通过-ta class筛选运行子用例，当子用例不存在时，它的运行结果设为UN
            for case_name in set(self.white_case_list) - set(subcase_names):
                error_msg = ErrorMessage.TestCase.Code_0203022.format(self.suite_name, case_name)
                self.log.warning(error_msg)
                cur_time_str = get_cst_time().strftime(ReportConstant.time_format)
                self.case_result[case_name] = {
                    "result": RunResult.UNAVAILABLE,
                    "error": error_msg,
                    "start_time": cur_time_str,
                    "run_time": 0,
                    "report": report_path
                }
                self.suite_case_results.append({
                    "name": case_name,
                    "result": RunResult.UNAVAILABLE,
                    "begin": cur_time_str,
                    "end": cur_time_str,
                    "elapsed": "0s",
                    "error": error_msg
                })
            start_time = get_cst_time()
            self.log.debug("Execute test case list: {}".format(subcase_items))
            # 2.先执行self.setup
            if self.run_setup():
                # 3.依次执行所有的run_list
                for index, case in enumerate(subcase_items, 1):
                    case_path = case[1]
                    self._reset_screenrecorder_and_screenshot()
                    self.log.info("[{} / {}] Executing suite case: {}".format(index, len(subcase_items), case_path))
                    self.run_one_test_case(case_path)
            else:
                self.error_msg = ErrorMessage.TestCase.Code_0203017.format(self.error_msg)
                for case_name in subcase_names:
                    self.case_result[case_name] = {
                        "result": RunResult.BLOCKED,
                        "error": self.error_msg,
                        "start_time": start_time.strftime(ReportConstant.time_format),
                        "run_time": 0,
                        "report": report_path
                    }
        finally:
            # 4.执行self.teardown
            self.run_teardown()
            self.cur_case.set_suite_instance(None)

    def setup(self):
        """Setup function that will be called before executing any test suite.
        Implementation is optional.
        """
        pass

    def setup_start(self):
        """
        setup_start function that will be called after setup function.
        Implementation is optional.
        """
        pass

    def setup_end(self):
        """
        setup_end function that will be called after setup function.
        Implementation is optional.
        """
        pass

    def teardown(self):
        """Teardown function that will be called after all the selected test
        suite.
        Implementation is optional.
        """
        pass

    def teardown_start(self):
        """
        teardown_start function that will be called before Teardown function.
        Implementation is optional.
        """
        pass

    def teardown_end(self):
        """
        teardown_end function that will be called after Teardown function.
        Implementation is optional.
        """
        pass

    def get_params(self):
        return self.arg_list

    def set_devices(self, devices):
        self.devices = devices
        if not devices:
            return

        try:
            for num, _ad in enumerate(self.devices, 1):
                if not hasattr(_ad, "device_id") or not getattr(_ad, "device_id"):
                    setattr(_ad, "device_id", "device{}".format(num))
                # 兼容release2 增加id、serial
                setattr(_ad, "id", _ad.device_id)
                setattr(_ad, "serial", _ad.device_sn)
                setattr(self, _ad.device_id, _ad)
                setattr(self, "device{}".format(num), _ad)
        except Exception as error:
            self.log.error("Failed to initialize the device object in the "
                           "TestCase.", error_no="01218")
            raise error

    def _get_case_list(self, path):
        result = []
        if len(self.configs["suitecases"]) > 0:
            for _, case in enumerate(self.configs["suitecases"]):
                if os.path.exists(case):
                    case_path = case
                else:
                    case_path = get_file_absolute_path(case, [path,
                                                              self.configs["resource_path"],
                                                              self.configs["testcases_path"]])
                result.append(case_path)
        else:
            all_file_list = os.listdir(path)
            # 遍历该文件夹下的所有目录或者文件
            for file in all_file_list:
                filepath = os.path.join(path, file)
                # 如果是文件夹，递归调用函数
                if os.path.isdir(filepath):
                    result.extend(self._get_case_list(filepath))
                # 如果不是文件夹，保存文件路径及文件名
                elif os.path.isfile(filepath) and \
                        "__pycache__" not in filepath:
                    if file.startswith(FileAttribute.TESTCASE_PREFIX) and \
                            (file.endswith(FileAttribute.TESTCASE_POSFIX_PY) or
                             file.endswith(FileAttribute.TESTCASE_POSFIX_PYC) or
                             file.endswith(FileAttribute.TESTCASE_POSFIX_PYD)):
                        result.append(filepath)
        return result

    def _exec_func(self, func, *args):
        result = False
        try:
            func(*args)
        except Exception as exception:
            self.error_msg = str(exception)
            self.trace_info = traceback.format_exc()

            index = self.cur_case.get_step_index()
            if index == -1:
                self.log.error(self.error_msg)
                self.log.error(self.trace_info)
            else:
                step_error_id = f'step_error_{index}'
                self.log.error(f'<span id="{step_error_id}">{self.error_msg}</span>')
                self.log.error(self.trace_info)
                _error = f'<a href="javascript:" onclick="gotoStep(\'{step_error_id}\')">{self.error_msg}</a>'
                UpdateStep(index, error=_error)
        else:
            result = True
        return result

    def run_setup(self):
        ret = False

        try:
            self.setup_start()
            self.log.info("**********SetUp Starts!")
            ret = self._exec_func(self.setup)
            self.log.info("**********SetUp Ends!")
            if ret:
                self.setup_end()
                return True
            self.log.info("SetUp Failed!")
            return False

        finally:
            if ret:
                result = RunResult.PASSED
            else:
                result = RunResult.FAILED

    def run_one_test_case(self, case_path: str):
        # 在运行测试套子用例前，停止收集测试套的运行日志
        cache_case_log_end(self.suite_log_hdl)
        # 开始收集日志
        case_log_hdl = cache_case_log_begin()
        case_name = get_base_name(case_path)
        # 获取当前用例module_run.log路径
        log_path = get_driver_log_path(threading.current_thread().name)
        # 生成拆分日志路径
        base_name = os.path.basename(log_path)
        case_log_path = log_path.replace(base_name, case_name + ".log")
        # 停止写入module_run.log
        redirect_driver_log_end(threading.current_thread().name)
        # 写入新的日志路径
        redirect_driver_log_begin(threading.current_thread().name, case_log_path)

        self.log.info("Executing test case {}".format(case_path))
        start_time = get_cst_time()
        case_result = RunResult.FAILED
        sub_case_results = []
        tests_result = []
        test_cls_instance = None
        result_content = None  # 用例测试结果的拓展内容
        try:
            test_cls = import_from_file(get_dir_path(case_path), case_name)
            self.log.info("Success to import {}.".format(case_name))
            self._compatible_testcase(case_path, case_name)
            self._start_catch_logs(self.configs["test_name"], case_name)
            with test_cls(self.configs) as test_cls_instance:
                self.cur_case.set_case_instance(test_cls_instance)
                test_cls_instance.case_log_hdl = case_log_hdl
                test_cls_instance.run()
            start_time = test_cls_instance.start_time
            sub_case_results = test_cls_instance.sub_case_results
            case_result = test_cls_instance.result
            error_msg = test_cls_instance.error_msg
            result_content = test_cls_instance.result_content
            tests_result = test_cls_instance.tests_result
            if sub_case_results:
                self._handle_suite_case_result(case_name, test_cls_instance)
        except Exception as e:
            error_msg = str(e)
            self.log.error("run case error! Exception: {}".format(e))
            self.log.error(traceback.format_exc())

        if test_cls_instance is None:
            case_result = RunResult.BLOCKED
        if test_cls_instance:
            try:
                del test_cls_instance
                self.log.debug("del test case instance success")
            except Exception as e:
                self.log.debug(traceback.format_exc())
                self.log.warning("del test case instance exception. Exception: {}".format(e))
        Binder.notify_stage(CaseEnd(case_name, case_result))

        end_time = get_cst_time()
        cost = int(round((end_time - start_time).total_seconds() * 1000))
        self.log.info("Executed case: {}, result: {}, cost time: {}ms".format(case_name, case_result, cost))

        try:
            self._stop_catch_logs()
            self._device_close()
        except Exception as e:
            self.log.error("stop catch device log error! {}".format(e))
            self.log.error(traceback.format_exc())

        steps = self.cur_case.get_steps_info()
        # 停止收集日志
        cache_case_log_end(case_log_hdl)
        if sub_case_results:
            # 不生成testcase用例
            self.suite_case_results.extend(sub_case_results)
        else:
            # 生成正常testcase用例的报告
            base_info = {
                "name": case_name,
                "result": case_result,
                "begin": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                "end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                "elapsed": calculate_elapsed_time(start_time, end_time),
                "error": error_msg
            }
            case_info = copy.copy(base_info)

            case_html_name = case_name + ".html"
            temp_path = os.path.join("details", self._round_folder, self.suite_name)
            case_html_path = os.path.join(temp_path, case_html_name)
            to_file = os.path.join(self.get_case_report_path(), case_html_path)
            relpath = os.path.relpath(case_log_path, os.path.dirname(to_file))
            environment = self._request.config.environment

            case_info.update({
                "logs": '<a href={} target="_blank">{}'.format(relpath, os.path.basename(case_log_path)),
                "devices": [] if environment is None else environment.get_description(),
                "steps": steps,
                "tests_result": tests_result,
            })
            generate_case_report(to_file, case_info, case_log_hdl)
            # 将step信息写入文件
            steps_data_path = os.path.join(self.get_case_report_path(), temp_path, f"{case_name}_step.json")
            save_steps_info(steps, steps_data_path, temp_path)

            base_info["report"] = case_html_name
            self.suite_case_results.append(base_info)
            self.case_result[case_name] = {
                "result": case_result, "error": error_msg,
                "start_time": start_time.strftime(ReportConstant.time_format),
                "run_time": cost, "report": case_html_path, "result_content": result_content,
                "tests_result": tests_result}

        steps.clear()
        # 将用例实例对象和用例名置为空
        self.cur_case.set_case_instance(None)
        self.cur_case.set_name("")

        # 在运行测试套子用例后，重新收集测试套的运行日志
        cache_case_log_begin(case_log_hdl=self.suite_log_hdl)
        # 停止写入子用例日志
        redirect_driver_log_end(threading.current_thread().name)
        # 恢复写入module_run.log
        redirect_driver_log_begin(threading.current_thread().name, log_path)

    def run_teardown(self):
        ret = False
        try:
            self.log.info("**********TearDown Starts!")
            self.teardown_start()
            ret = self._exec_func(self.teardown)
            self.teardown_end()
            self.log.info("**********TearDown Ends!")
        finally:
            if ret:
                result = RunResult.PASSED
            else:
                result = RunResult.FAILED

    def _test_args_para_parse(self, paras):
        paras = dict(paras)
        for para_name in paras.keys():
            para_name = para_name.strip()
            para_values = paras.get(para_name, [])
            if para_name == "para":
                for arg in para_values:
                    key, value = arg.split("#")
                    self.arg_list[key] = value
            elif para_name == "deveco_planet_info":
                for app_info in para_values:
                    key, value = app_info.split("#")
                    if key == "task_type":
                        setattr(sys, "category", value)
                    else:
                        self.app_result_info[key] = value
                        setattr(sys, "app_result_info", self.app_result_info)
            else:
                continue

        self.configs["pass_through"] = self.pass_through
        self.configs["arg_list"] = self.arg_list

    def get_case_report_path(self):
        return self.configs["report_path"]

    def _compatible_testcase(self, case_path, case_name):
        DeccVariable.cur_case().set_name(case_name)
        project_var = ProjectVariables(self.inject_logger)
        project_var.execute_case_name = case_name
        project_var.cur_case_full_path = case_path
        project_var.task_report_dir = self.get_case_report_path()
        self.configs["project"] = project_var

    def _start_catch_logs(self, suite_name, test_name):
        if self.configs[ConfigConst.device_log].get(ConfigConst.tag_suite_case_log) == ConfigConst.device_log_on:
            # 在log文件夹下创建suite的文件夹
            suite_folder = os.path.join(self.get_case_report_path(), "log", self._round_folder, suite_name)
            if not os.path.exists(suite_folder):
                os.makedirs(suite_folder)
            for device in self.devices:
                hilog = os.path.join(suite_folder,
                                     "device_hilog_{}_{}.log".format(test_name, device.__get_serial__()))
                hilog_open = os.open(hilog, os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                                     FilePermission.mode_755)
                device_log_open = None
                device_log = None
                if not hasattr(device, "is_oh"):
                    device_log = os.path.join(suite_folder,
                                              "device_log_{}_{}.log".format(test_name, device.__get_serial__()))
                    device_log_open = os.open(device_log, os.O_WRONLY | os.O_CREAT | os.O_APPEND,
                                              FilePermission.mode_755)
                    self.device_log[device.device_sn] = device_log
                self.hilog[device.device_sn] = hilog
                if device_log_open:
                    with os.fdopen(hilog_open, "a") as hilog_file_pipe, \
                            os.fdopen(device_log_open, "a") as device_log_file_pipe:
                        device.device_log_collector.add_log_address(device_log, hilog)
                        log_proc, hilog_proc = device.device_log_collector. \
                            start_catch_device_log(device_log_file_pipe, hilog_file_pipe, clear_crash_log=False)
                        self.log_proc[device.device_sn] = log_proc
                        self.hilog_proc[device.device_sn] = hilog_proc
                else:
                    with os.fdopen(hilog_open, "a") as hilog_file_pipe:
                        device.device_log_collector.add_log_address(device_log, hilog)
                        _, hilog_proc = device.device_log_collector. \
                            start_catch_device_log(None, hilog_file_pipe, clear_crash_log=False)
                        self.hilog_proc[device.device_sn] = hilog_proc

    def _stop_catch_logs(self):
        try:
            if self.configs[ConfigConst.device_log].get(ConfigConst.tag_suite_case_log) == ConfigConst.device_log_on:
                for device in self.devices:
                    device.device_log_collector.remove_log_address(self.device_log.get(device.device_sn, None),
                                                                   self.hilog.get(device.device_sn, None))
                    device.device_log_collector.stop_catch_device_log(self.log_proc.get(device.device_sn, None))
                    device.device_log_collector.stop_catch_device_log(self.hilog_proc.get(device.device_sn, None))
        except Exception as e:
            self.log.debug("_stop_catch_logs error: {}".format(e))

    def set_screenrecorder_and_screenshot(self, screenrecorder: bool, screenshot: bool = True):
        """
        Set whether to enable screen recording or screenshot for the device in the test case.
        """
        for device in self.devices:
            setattr(device, "screenshot", screenshot)
            if hasattr(device, "is_oh"):
                setattr(device, "screenrecorder", screenrecorder)
                data = {
                    "screenshot": screenshot,
                    "screenrecorder": screenrecorder
                }
            else:
                data = {
                    "screenshot": screenshot,
                    "screenrecorder": getattr(device, "screenrecorder")
                }
            self.devices_media.update({device.device_sn: data})

    def _get_screenrecorder_and_screenshot(self):
        for device in self.devices:
            data = {
                "screenshot": getattr(device, "screenshot"),
                "screenrecorder": getattr(device, "screenrecorder")
            }
            self.devices_media.update({device.device_sn: data})

    def _reset_screenrecorder_and_screenshot(self):
        for device in self.devices:
            setattr(device, "screenshot", self.devices_media.get(device.device_sn, {}).get("screenshot", False))
            if hasattr(device, "is_oh"):
                setattr(device, "screenrecorder",
                        self.devices_media.get(device.device_sn, {}).get("screenrecorder", False))

    def _handle_suite_case_result(self, testcase_name, testcase_instance):
        status_dict = {RunResult.PASSED: ResultCode.PASSED,
                       RunResult.FAILED: ResultCode.FAILED,
                       RunResult.BLOCKED: ResultCode.BLOCKED,
                       "ignore": ResultCode.SKIPPED}
        for case_name, case_result in testcase_instance.case_result.items():
            result = case_result.get("result")
            error = case_result.get("error")
            run_time = case_result.get("run_time")
            report = case_result.get("report")
            result_content = case_result.get("result_content")
            tests_result = case_result.get("tests_result", [])

            test_result = self.state_machine.test(reset=True)
            test_suite = self.state_machine.suite()
            test_result.test_class = test_suite.suite_name
            test_result.test_name = testcase_name + "#" + case_name
            test_result.code = status_dict.get(result).value
            test_result.stacktrace = error
            test_result.run_time = run_time
            test_result.report = report
            if result_content:
                test_result.result_content = result_content
            if tests_result:
                test_result.tests_result = tests_result
            test_result.current = self.state_machine.running_test_index + 1

            self.state_machine.suite().run_time += run_time
            for listener in self.listeners:
                listener.__started__(
                    LifeCycle.TestCase, copy.copy(test_result))
            test_suites = self.state_machine.get_suites()
            test_suites.test_num += 1
            for listener in self.listeners:
                listener.__ended__(
                    LifeCycle.TestCase, copy.copy(test_result))
            self.state_machine.running_test_index += 1
