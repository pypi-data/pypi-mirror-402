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

import copy
import os
import sys
import traceback
import threading
from typing import Union

from xdevice import calculate_elapsed_time
from xdevice import StateRecorder
from xdevice import LifeCycle
from xdevice import ResultCode
from xdevice import get_cst_time
from xdevice import EnvPool
from xdevice import CaseEnd
from xdevice import Binder
from xdevice import get_driver_log_path

from devicetest.runner.prepare import PrepareHandler
from devicetest.core.constants import RunResult
from devicetest.utils.util import clean_sys_resource
from devicetest.utils.util import get_base_name
from devicetest.utils.util import get_dir_path
from devicetest.utils.util import import_from_file
from devicetest.utils.util import save_steps_info
from devicetest.core.variables import DeccVariable
from devicetest.core.variables import ProjectVariables
from devicetest.core.variables import CurCase
from devicetest.core.exception import DeviceTestError
from devicetest.core.test_case import DeviceRoot
from devicetest.core.test_case import BaseCase
from devicetest.error import ErrorMessage
from devicetest.log.logger import DeviceTestLog as Log
from devicetest.report.generation import cache_case_log_begin
from devicetest.report.generation import cache_case_log_end
from devicetest.report.generation import generate_case_report


class TmpTestCase:

    def __init__(self, case_result: dict):
        self.case_result = case_result


class RunnerMode:
    PIPELINE = "pipeline"
    DEBUG = "debug"


class BaseRunner:

    def __init__(self):
        self.state_machine = StateRecorder()
        self.listeners = None
        self.suite_name = ""
        self._repeat = 1
        self._repeat_round = 1

    def handle_suites_started(self):
        self.state_machine.get_suites(reset=True)
        test_suites = self.state_machine.get_suites()
        test_suites.suites_name = self.suite_name
        test_suites.test_num = 0
        for listener in self.listeners:
            suite_report = copy.copy(test_suites)
            listener.__started__(LifeCycle.TestSuites, suite_report)

    def handle_suites_ended(self, error_msg):
        suites = self.state_machine.get_suites()
        suites.is_completed = True
        suites.stacktrace = error_msg
        for listener in self.listeners:
            listener.__ended__(LifeCycle.TestSuites, suites, repeat=self._repeat, repeat_round=self._repeat_round)

    def handle_suite_started(self):
        self.state_machine.suite(reset=True)
        self.state_machine.running_test_index = 0
        test_suite = self.state_machine.suite()
        test_suite.suite_name = self.suite_name
        test_suite.test_num = 0
        for listener in self.listeners:
            suite_report = copy.copy(test_suite)
            listener.__started__(LifeCycle.TestSuite, suite_report)

    def handle_suite_ended(self, suite_report_path):
        suite = self.state_machine.suite()
        suites = self.state_machine.get_suites()
        suite.is_completed = True
        # 设置测试套的报告路径
        suite.report = suite_report_path
        for listener in self.listeners:
            listener.__ended__(LifeCycle.TestSuite, copy.copy(suite), is_clear=True)
        suites.run_time += suite.run_time

    def handle_suite_case_result(self, testsuite_cls):
        status_dict = {
            RunResult.PASSED: ResultCode.PASSED,
            RunResult.FAILED: ResultCode.FAILED,
            RunResult.BLOCKED: ResultCode.BLOCKED,
            "ignore": ResultCode.SKIPPED,
            RunResult.UNAVAILABLE: ResultCode.UNAVAILABLE
        }
        for case_name, case_result in testsuite_cls.case_result.items():
            result = case_result.get("result")
            error = case_result.get("error")
            run_time = case_result.get("run_time")
            report = case_result.get("report")
            result_content = case_result.get("result_content")
            tests_result = case_result.get("tests_result", [])
            start_time = case_result.get("start_time", "")

            test_result = self.state_machine.test(reset=True)
            test_suite = self.state_machine.suite()
            test_result.test_class = test_suite.suite_name
            test_result.test_name = case_name
            test_result.code = status_dict.get(result).value
            test_result.stacktrace = error
            test_result.starttime = start_time
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


class TestRunner(BaseRunner):
    """executes test cases and
    """

    def __init__(self):
        super().__init__()
        self.run_mode = RunnerMode.PIPELINE
        self.run_list = None
        self.no_run_list = None
        self.running = None
        self.configs = None
        self.devices = None
        self.log = Log
        self.start_time = None
        self.test_results = None
        self.project = None
        self.prepare = None
        self.cur_case = None

    def init_pipeline_runner(self, run_list, configs, devices):
        self.run_list = run_list
        self.no_run_list = copy.copy(self.run_list)
        self.running = False
        self.configs = configs
        self.devices = devices
        self.start_time = get_cst_time()
        self.test_results = []
        self.project = ProjectVariables(self.log)
        self.prepare = None
        self.__init_project_variables()
        self.run_mode = RunnerMode.PIPELINE
        self._repeat = self.configs.get("request").config.repeat
        self._repeat_round = self.configs.get("request").get_repeat_round()
        self.listeners = self.configs["listeners"]

    def init_case_runner(self, run_list: Union[BaseCase, list]):
        # simple case runner
        self.run_list = run_list
        self.run_mode = RunnerMode.DEBUG

    def __init_project_variables(self):
        """
        testargs：为xDevice透传过来的数据,用户调用CONFIG可获取
        :return:
        """
        self.log.debug("configs:{}".format(self.configs))
        testcases_path = self.configs.get('testcases_path', "")
        testargs = self.configs.get("testargs", {})
        self.__flash_run_list(testargs)

        self.cur_case = CurCase(self.log)
        self.project.set_project_path()
        self.project.set_testcase_path(testcases_path)
        self.project.set_task_report_dir(self.configs.get("report_path"))
        self.project.set_resource_path(self.get_local_resource_path())

    def get_local_resource_path(self):
        local_resource_path = os.path.join(
            self.project.project_path, "testcases", "DeviceTest", "resource")
        return local_resource_path

    def get_local_aw_path(self):
        local_aw_path = os.path.join(
            self.project.project_path, "testcases", "DeviceTest", "aw")
        return local_aw_path

    def __flash_run_list(self, testargs):
        """
        retry 场景更新run list
        :param testargs:
        :return:
        """
        get_test = testargs.get("test")
        self.log.info("get test:{}".format(get_test))
        retry_test_list = self.parse_retry_test_list(get_test)
        if retry_test_list is not None:
            self.run_list = retry_test_list
            self.no_run_list = copy.copy(self.run_list)
            self.log.info("retry test list:{}".format(retry_test_list))

    def parse_retry_test_list(self, retry_test_list):
        if retry_test_list is None:
            return None
        elif not isinstance(retry_test_list, list):
            err_msg = ErrorMessage.TestCase.Code_0203005
            self.log.error(err_msg)
            raise DeviceTestError(err_msg)

        elif len(retry_test_list) == 1 and "#" not in str(retry_test_list[0]):
            return None
        else:
            history_case_list = []
            history_case_dict = dict()
            retry_case_list = []
            for abd_file_path in self.run_list:
                base_file_name = get_base_name(abd_file_path)
                if base_file_name not in history_case_dict.keys():
                    history_case_dict.update({base_file_name: []})
                history_case_dict.get(base_file_name).append(abd_file_path)
                history_case_list.append(base_file_name)
            self.log.debug("history case list:{}".format(history_case_list))

            for _value in retry_test_list:
                case_id = str(_value).split("#")[0]
                case_id_file = history_case_dict.get(case_id)[0]
                if case_id in history_case_dict.keys() and case_id_file not in retry_case_list:
                    retry_case_list.append(case_id_file)
            return retry_case_list

    def parse_config(self, test_configs):
        pass

    def add_value_to_configs(self):
        self.configs["log"] = Log
        self.configs["devices"] = self.devices
        self.configs["project"] = self.project

    def run(self):
        if self.run_mode == RunnerMode.PIPELINE:
            self._pipeline_run()
        else:
            self._debug_run()

    def _pipeline_run(self):
        self.running = True
        aw_path = self.add_aw_path_to_sys(self.project.aw_path)
        self.log.info("Executing run list {}.".format(self.run_list))

        self.add_value_to_configs()

        self.prepare = PrepareHandler(self.log, self.cur_case,
                                      self.project, self.configs,
                                      self.devices, self.run_list)
        # **********混合root和非root**************
        try:
            for device in self.devices:
                if hasattr(device, "is_root"):
                    DeviceRoot.is_root_device = device.is_root
                    self.log.debug(DeviceRoot.is_root_device)
                    setattr(device, "is_device_root", DeviceRoot.is_root_device)
        except Exception as e:
            self.log.error(f'set branch api error. {e}')
        # **************混合root和非root end**********************
        self.prepare.run_prepare()

        for case_path in self.run_list:
            case_name = get_base_name(case_path)
            if self.project.record.is_shutdown(raise_exception=False):
                break
            self.project.execute_case_name = case_name
            self.run_test_class(case_path, case_name)

        self.prepare.run_prepare(is_teardown=True)
        clean_sys_resource(file_path=aw_path)
        DeccVariable.reset()

    def _debug_run(self):
        # 获取环境池报告路径
        report_path = EnvPool.report_path
        if not isinstance(self.run_list, list):
            run_list = list()
            run_list.append(self.run_list)
            self.run_list = run_list
        total_case_num = len(self.run_list)
        case_num = 1
        passed_num = 0
        failed_num = 0
        try:
            for test_cls_instance in self.run_list:
                # 开始收集日志
                case_log_hdl = cache_case_log_begin()

                start_time = get_cst_time()
                case_name = test_cls_instance.TAG if test_cls_instance.TAG else "Case{}".format(case_num)
                self.log.info("[{} / {}] Executing case: {}".format(case_num, total_case_num, case_name))

                self.cur_case = CurCase(self.log)
                self.cur_case.set_case_instance(test_cls_instance)
                # 设置curcase对象
                setattr(test_cls_instance, "cur_case", self.cur_case)
                DeccVariable.set_cur_case_obj(self.cur_case)

                # 设置截图保存路径
                self.cur_case.set_name(case_name)
                if EnvPool.generate_report:
                    DeccVariable.cur_case().set_case_screenshot_dir(None, report_path, None)

                test_cls_instance.run()
                Binder.notify_stage(CaseEnd(case_name, test_cls_instance.result))

                end_time = get_cst_time()
                if test_cls_instance.result == RunResult.PASSED:
                    passed_num = passed_num + 1
                elif test_cls_instance.result == RunResult.FAILED:
                    failed_num = failed_num + 1
                self.log.info("Executed case: {}, result: {}, cost time: {}".format(
                    case_name, test_cls_instance.result, calculate_elapsed_time(start_time, end_time)))

                steps = self.cur_case.get_steps_info()
                # 停止收集日志
                cache_case_log_end(case_log_hdl)
                case_info = {
                    "name": case_name,
                    "result": test_cls_instance.result,
                    "begin": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "elapsed": calculate_elapsed_time(start_time, end_time),
                    "error": test_cls_instance.error_msg,
                    "logs": "",
                    "devices": [],
                    "steps": steps
                }
                # 生成测试报告
                if EnvPool.generate_report:
                    to_file = os.path.join(report_path, case_name + ".html")
                    generate_case_report(to_file, case_info, case_log_hdl)
                else:
                    # 清除缓存的日志
                    case_log_hdl.buffer.clear()
                    del case_log_hdl
                steps.clear()
                case_num += 1
        except Exception as exception:
            error_msg = ErrorMessage.TestCase.Code_0203002.format(exception)
            self.log.error(error_msg)
            self.log.error(traceback.format_exc())
        finally:
            DeccVariable.reset()
            self.log.info("Summary result: total cases: {}, passed: {}, failed: {}, unavailable: {}".format(
                total_case_num, passed_num, failed_num, total_case_num - passed_num - failed_num))

    def add_aw_path_to_sys(self, aw_path):
        sys_aw_path = os.path.dirname(aw_path)
        if os.path.exists(sys_aw_path):
            sys.path.insert(1, sys_aw_path)
            self.log.info("add {} to sys path.".format(sys_aw_path))
            return sys_aw_path
        return None

    def run_test_class(self, case_path, case_name):
        """Instantiates and executes a test class.
        If the test cases list is not None, all the test cases in the test
        class should be executed.
        Args:
            case_path: case path
            case_name: case name
        Returns:
            A tuple, with the number of cases passed at index 0, and the total
            number of test cases at index 1.
        """
        # 开始收集日志
        case_log_hdl = cache_case_log_begin()

        self.log.info("Executing test case {}".format(case_path))
        tests_result = []
        sub_case_results = []
        start_time = get_cst_time()
        case_dir_path = get_dir_path(case_path)
        test_cls_instance = None
        self.suite_name = self.configs.get("test_name", case_name)

        self.handle_suites_started()
        self.handle_suite_started()

        # 用例测试结果的拓展内容
        result_content = None
        try:
            self.project.cur_case_full_path = case_path
            DeccVariable.set_cur_case_obj(self.cur_case)
            test_cls = import_from_file(case_dir_path, case_name)
            self.log.info("Success to import {}.".format(case_name))
            with test_cls(self.configs) as test_cls_instance:
                self.cur_case.set_case_instance(test_cls_instance)
                test_cls_instance.case_log_hdl = case_log_hdl
                test_cls_instance.run()

            start_time = test_cls_instance.start_time
            sub_case_results = getattr(test_cls_instance, "sub_case_results", [])
            case_result = test_cls_instance.result
            error_msg = test_cls_instance.error_msg
            result_content = test_cls_instance.result_content
            tests_result = test_cls_instance.tests_result
        except Exception as exception:
            case_result = RunResult.FAILED
            error_msg = ErrorMessage.TestCase.Code_0203002.format(exception)
            self.log.error(error_msg)
            self.log.error(traceback.format_exc())

        Binder.notify_stage(CaseEnd(case_name, case_result, error_msg))

        end_time = get_cst_time()
        environment = self.configs.get("request").config.environment
        steps = self.cur_case.get_steps_info()
        log_path = get_driver_log_path(threading.current_thread().name)
        round_folder = f"round{self._repeat_round}" if self._repeat > 1 else ""
        temp_path = os.path.join("details", round_folder)
        case_html_path = os.path.join(temp_path, f"{case_name}.html")
        to_file = os.path.join(self.project.task_report_dir, case_html_path)
        relpath = os.path.relpath(log_path, os.path.dirname(to_file))
        # 生成报告
        case_info = {
            "name": case_name,
            "result": case_result,
            "begin": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed": calculate_elapsed_time(start_time, end_time),
            "error": error_msg,
            "subcases": sub_case_results,
            "logs": '<a href={} target="_blank">{}'.format(relpath, os.path.basename(log_path)),
            "devices": [] if environment is None else environment.get_description(),
            "steps": steps,
            "tests_result": tests_result,
        }

        if not test_cls_instance or not sub_case_results:
            tmp_result = {
                self.suite_name: {
                    "result": case_result,
                    "error": error_msg,
                    "run_time": int(round((end_time - start_time).total_seconds() * 1000)),
                    "report": case_html_path,
                    "result_content": result_content,
                    "tests_result": tests_result,
                }
            }
            result_instance = TmpTestCase(tmp_result)
        else:
            result_instance = test_cls_instance
        self.handle_suite_case_result(result_instance)

        if isinstance(result_instance, TmpTestCase):
            del result_instance

        if test_cls_instance:
            try:
                del test_cls_instance
                self.log.debug("del test_cls_instance success.")
            except Exception as exception:
                self.log.warning("del test_cls_instance exception. {}".format(exception))

        # 停止收集日志
        cache_case_log_end(case_log_hdl)
        generate_case_report(to_file, case_info, case_log_hdl)
        # 将step信息写入文件
        steps_data_path = os.path.join(self.project.task_report_dir, temp_path, f"{case_name}_step.json")
        save_steps_info(steps, steps_data_path, temp_path)

        self.handle_suite_ended(case_html_path)
        self.handle_suites_ended(error_msg)

        steps.clear()
        self.cur_case.set_case_instance(None)
        return case_result, error_msg

    def stop(self):
        """
        Releases resources from test run. Should be called right after run()
        finishes.
        """
        if self.running:
            self.running = False


class TestSuiteRunner(BaseRunner):
    """
    executes test suite cases
    """

    def __init__(self, suite, configs, devices):
        super().__init__()
        self.suite = suite
        self.running = False
        self.configs = configs
        self.cur_case = None
        self.devices = devices
        self.log = Log
        self.listeners = self.configs["listeners"]

        self._repeat = self.configs.get("request").config.repeat
        self._repeat_round = self.configs.get("request").get_repeat_round()
        self._round_folder = f"round{self._repeat_round}" if self._repeat > 1 else ""

    def _init_devicetest(self):
        self.cur_case = CurCase(self.log)
        self.cur_case.suite_name = self.suite_name
        self.cur_case.set_case_screenshot_dir(
            None, self.get_report_path(), None,
            repeat=self._repeat, repeat_round=self._repeat_round)
        DeccVariable.set_cur_case_obj(self.cur_case)

    def get_report_path(self):
        return self.configs["report_path"]

    def add_value_to_configs(self):
        self.configs["log"] = self.log
        self.configs["devices"] = self.devices
        self.configs["suite_name"] = self.suite_name

        # 获取--retry场景里要执行的用例列表
        test_args = self.configs.get("testargs", {})
        test_list = test_args.get("test", [])
        self.log.info("test list: {}".format(test_list))
        if isinstance(test_list, list) and test_list:
            test_args["class"] = [l.split("#")[1] for l in test_list if "#" in l]

    def run(self):
        self.running = True
        self.suite_name = get_base_name(self.suite)
        self.add_value_to_configs()
        self.run_test_suite(self.suite)

    def run_test_suite(self, test_cls_name):
        """Instantiates and executes a test class.
        If the test cases list is not None, all the test cases in the test
        class should be executed.
        Args:
            test_cls_name: Name of the test class to execute.
        Returns:
            A tuple, with the number of cases passed at index 0, and the total
            number of test cases at index 1.
        """
        # 开始收集日志
        suite_log_hdl = cache_case_log_begin()

        self.log.info("Executing test suite {}".format(self.suite))
        start_time = get_cst_time()
        suite_case_results = []
        test_cls_instance = None
        self.handle_suites_started()
        self.handle_suite_started()
        self._init_devicetest()
        try:
            suite_dir_path = get_dir_path(test_cls_name)
            test_cls = import_from_file(suite_dir_path, self.suite_name)
            self.log.info("Success to import {}.".format(self.suite_name))
            self.configs["cur_suite"] = test_cls
            with test_cls(self.configs, suite_dir_path) as test_cls_instance:
                test_cls_instance.cur_case = self.cur_case
                test_cls_instance.suite_log_hdl = suite_log_hdl
                test_cls_instance.state_machine = self.state_machine
                test_cls_instance.run()

            error_msg = test_cls_instance.error_msg
            suite_case_results = test_cls_instance.suite_case_results
            self.handle_suite_case_result(test_cls_instance)
        except Exception as e:
            error_msg = ErrorMessage.TestCase.Code_0203017.format(e)
            self.log.error(error_msg)
            self.log.error(traceback.format_exc())
        if test_cls_instance:
            try:
                del test_cls_instance
                self.log.debug("del test suite instance success.")
            except Exception as e:
                self.log.warning("del test suite instance exception. {}".format(e))

        steps = self.cur_case.get_steps_info()
        # 停止收集日志
        cache_case_log_end(suite_log_hdl)
        # 生成测试套的报告
        self.log.info("generate suite report")
        end_time = get_cst_time()
        environment = self.configs.get("request").config.environment

        report_path = self.get_report_path()
        round_folder = f"round{self._repeat_round}" if self._repeat > 1 else ""
        temp_path = os.path.join("details", round_folder, self.suite_name)
        suite_html_path = os.path.join(temp_path, f"{self.suite_name}.html")
        to_file = os.path.join(report_path, suite_html_path)
        suite_log_path = get_driver_log_path(threading.current_thread().name)
        relpath = os.path.relpath(suite_log_path, os.path.dirname(to_file))
        suite_info = {
            "name": self.suite_name,
            "result": "",
            "begin": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed": calculate_elapsed_time(start_time, end_time),
            "error": error_msg,
            "logs": '<a href={} target="_blank">{}'.format(relpath, os.path.basename(suite_log_path)),
            "subcases": suite_case_results,
            "devices": [] if environment is None else environment.get_description(),
            "steps": steps,
            "is_testsuite": "true",
        }
        generate_case_report(to_file, suite_info, suite_log_hdl)
        # 将step信息写入文件
        steps_data_path = os.path.join(report_path, temp_path, f"{self.suite_name}_step.json")
        save_steps_info(steps, steps_data_path, temp_path)
        steps.clear()

        self.handle_suite_ended(suite_html_path)
        self.handle_suites_ended(error_msg)
        DeccVariable.reset()

    def stop(self):
        """
        Releases resources from test run. Should be called right after run()
        finishes.
        """
        if self.running:
            self.running = False
