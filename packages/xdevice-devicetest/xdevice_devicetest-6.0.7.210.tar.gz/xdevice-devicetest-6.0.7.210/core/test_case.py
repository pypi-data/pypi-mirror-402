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

import inspect
import json
import random
import re
import sys
import threading
import time
import traceback
import warnings
from functools import wraps
from typing import Callable
from typing import List
from typing import Tuple
from typing import Union

from xdevice import calculate_elapsed_time
from xdevice import convert_serial
from xdevice import get_decode
from xdevice import get_cst_time
from xdevice import ConfigConst
from xdevice import IDevice
from xdevice import EnvPool
from xdevice import is_env_pool_run_mode
from xdevice import ReportConstant
from xdevice import Request
from xdevice import TrackEvent, Tracker
from xdevice import Variables


from devicetest.record_actions.record_action import RecordAction
from devicetest.core.exception import BaseTestError
from devicetest.core.exception import HdcCommandRejectedException
from devicetest.core.exception import ShellCommandUnresponsiveException
from devicetest.core.exception import DeviceNotFound
from devicetest.core.exception import AppInstallError
from devicetest.core.exception import RpcNotRunningError
from devicetest.core.exception import TestFailure
from devicetest.core.exception import TestError
from devicetest.core.exception import TestSkip
from devicetest.core.exception import TestTerminated
from devicetest.core.exception import TestAbortManual
from devicetest.core.exception import DeviceTestError
from devicetest.core.exception import TestAssertionError
from devicetest.core.constants import RunResult
from devicetest.core.constants import RunSection
from devicetest.core.constants import RunStatus
from devicetest.core.variables import DeccVariable
from devicetest.core.variables import CurCase
from devicetest.core.variables import set_devices_test_args
from devicetest.error import ErrorMessage
from devicetest.utils.time_util import TS
from devicetest.utils.type_utils import T
from devicetest.utils.util import get_current_action_name
from devicetest.log.logger import DeviceTestLog as log
from devicetest.controllers.tools.screen_agent import ScreenAgent

RESULT_LINE_TEMPLATE = "[Test Step] %s %s"


class DeviceRoot:
    is_root_device = False

    def __init__(self):
        pass

    @staticmethod
    def set_device_root(is_root):
        DeviceRoot.is_root_device = is_root

    @staticmethod
    def get_device_root():
        return DeviceRoot.is_root_device


class BaseCase:
    """Base class for all test classes to inherit from.
    This class gets all the controller objects from test_runner and executes
    the test cases requested within itself.
    """

    def __init__(self, tag, configs):
        self.TAG = tag
        self.cur_case = None
        self.devices = []
        self.device1 = None
        self.device2 = None
        self.project = None
        self.configs = {}
        self.__case_error = ''  # the test case's error message
        self.__case_result = RunResult.PASSED  # the test case's result
        self.__case_start_time = get_cst_time()  # the test case's start time
        self.__test_method_error = ''  # the test method's error message
        self.__test_method_result = RunResult.PASSED  # the test method's result
        self.__tests_result = []  # the tests result
        self.__result_content = {}  # the test case's result content
        self.trace_info = ''
        self.log = log
        self.step_flash_fail_msg = False
        # proxy function
        self.execption_callback = None
        # case end function
        self.case_end_callback = None
        # 子用例
        self.sub_case_results = []

        self.testLoop = 0
        self.fail_times = 0
        self.con_fail_times = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._exec_func(self.clean_up)

    def _print_error(self, error: str, result: RunResult = RunResult.FAILED):
        """打印异常信息
        error : str, error message
        result: RunResult, RunResult class variables
        """
        trace_info = traceback.format_exc()
        if not _is_in_teardown_section():
            # 刷新测试方法的运行结果
            self.set_test_method_error(str(error))
            self.set_test_method_result(result)
            # 非Passed时，刷新测试用例的运行结果
            if result != RunResult.PASSED:
                self.set_case_error(str(error))
                self.set_case_result(result)
        # 将报错的代码行，作为新Step展示在报告里
        Step(get_current_action_name(self.TAG))
        # 打印异常信息
        index = self.cur_case.get_step_index()
        step_error_id = f'step_error_{index}'
        self.log.error(f'<span id="{step_error_id}">{error}</span>')
        if not trace_info.startswith('NoneType: None'):
            self.log.error(trace_info)
        _error = f'<a href="javascript:" onclick="gotoStep(\'{step_error_id}\')">{error}</a>'
        # 更新报错的代码行Step对应的错误信息
        UpdateStep(index, error=_error)

    def setup(self):
        """Setup function that will be called before executing any test case
        in the test class. Implementation is optional.
        """
        return True

    def process(self):
        """process function that will be called before setup function and after
        teardown function in the test class. Implementation is optional.
        """
        pass

    def teardown(self):
        """Teardown function that will be called after all the selected test
        cases in the test class have been executed.
        Implementation is optional.
        """
        pass

    def exec_one_testcase(self, test_name, test_func, *args):
        """Executes one test case and update test results.
        Args:
            test_name: Name of the test.
            test_func: The test function.
        Returns:
            True if the test passes, False otherwise.
        """
        warnings.warn("function is deprecated, 'self.run_test()' instead", DeprecationWarning)
        self.run_test(test_name, test_func, *args)

    def _exec_func(self, func, *args):
        """Executes a function with exception safeguard.
        Args:
            func: Function to be executed.
            args: Arguments to be passed to the function.
        Returns:
            Whatever the function returns, or False if unhandled exception occurred.
        """
        ret = False
        error = None
        try:
            func_ret = func(*args)
            if func_ret is None or func_ret is True:
                ret = True
            else:
                error = ErrorMessage.TestCase.Code_0203002.format(f"test func '{func.__name__}' return false")
                self._print_error(error)
        except TestSkip:
            self.log.debug("Test skipped")
            ret = True
        except (AppInstallError, BaseTestError, DeviceNotFound, DeviceTestError,
                TestAssertionError, TestError, TestAbortManual, TestTerminated) as exception:
            # 上述异常，已设置错误码，无需再次设置
            error = str(exception)
            self._print_error(error)
        except HdcCommandRejectedException as exception:
            error = ErrorMessage.Device.Code_0202302.format(exception)
            self._print_error(error)
        except ShellCommandUnresponsiveException as exception:
            error = ErrorMessage.Device.Code_0202304.format(exception)
            self._print_error(error)
        except RpcNotRunningError as exception:
            error = ErrorMessage.Device.Code_0202305.format(exception)
            self._print_error(error)
        except ConnectionRefusedError as exception:
            error = ErrorMessage.Device.Code_0202306.format(exception)
            self._print_error(error)
        except ImportError as exception:
            error = ErrorMessage.TestCase.Code_0203006.format(exception)
            self._print_error(error)
        except Exception as exception:
            error = ErrorMessage.TestCase.Code_0203002.format(exception)
            self._print_error(error)
        if self.execption_callback is not None and error is not None:
            self.execption_callback(error)
        return ret

    def run(self, test_names=None):
        """Runs test cases within a test class by the order they
        appear in the test list.
        Being in the test_names list makes the test case "requested". If its
        name passes validation, then it'll be executed, otherwise the name will
        be skipped.
        Args:
            test_names: A list of names of the requested test cases. If None,
                all test cases in the class are considered requested.
        Returns:
            A tuple of: The number of requested test cases, the number of test
            cases executed, and the number of test cases passed.
        """
        # 若未在self.tests中设置测试方法，则process是默认的测试方法
        tests = getattr(self, "tests", None)
        if not isinstance(tests, list) or not tests:
            setattr(self, "tests", ["process"])

        if not is_env_pool_run_mode():
            RecordAction.set_init_info(self.project, self.devices)

        if RunStatus.FINISHED == self.run_setup():

            if not is_env_pool_run_mode():
                RecordAction.delete_instance(self.result, self.trace_info)
            return
        self.run_tests(test_names)
        self.run_teardown()
        if self.case_end_callback is not None:
            self.case_end_callback()

        if not is_env_pool_run_mode():
            result, adaptive_info = RecordAction.delete_instance(self.result, self.trace_info)
            self.log.debug(f"Case adaptive result: {result}")

    def run_setup(self):
        self.set_case_run_section(RunSection.SETUP)
        self.run_setup_start()
        self.log.info("**********SetUp Starts!")
        ret = self._exec_func(self.setup)
        self.log.info("**********SetUp Ends!")
        if not ret:
            self.log.error("setup step fails")
            self.set_case_run_section(RunSection.TEARDOWN)
            self.log.info("**********TearDown Starts!")
            self._exec_func(self.teardown)
            self.log.info('**********TearDown Ends!')
            self.set_case_result(RunResult.FAILED)
            self.print_case_result(self.TAG, self.result)
            return RunStatus.FINISHED
        self.run_setup_end()
        return RunStatus.RUNNING

    def run_tests(self, test_names):
        self.set_case_run_section(RunSection.TEST)
        test_funcs = []
        for test_name in getattr(self, "tests"):
            test_func = getattr(self, test_name, None)
            if test_func is None or not inspect.ismethod(test_func):
                self._print_error(ErrorMessage.TestCase.Code_0203004.format(self.TAG, test_name))
                return
            test_funcs.append((test_name, test_func))
        loop_tests_cfg = {}
        request = self.configs.get("request")
        if request is not None and isinstance(request, Request):
            loop_tests_cfg = request.get_tf_loop_tests()
        if loop_tests_cfg and loop_tests_cfg.get("sequence") is not None:
            event = TrackEvent.LoopTest
            Tracker.event(event.value, event_name=event.name)
            self._exec_loop_tests(loop_tests_cfg, test_funcs)
        else:
            for test_name, test_func in test_funcs:
                self.run_test(test_name, test_func)
        self.log.info("**********All test methods Ends!**********")

    def run_test(self, test_name, test_func, *args):
        self.log.info("[Test Step] {}".format(test_name))
        start_time = time.time()
        self.set_test_method_result(RunResult.PASSED)
        self.set_test_method_error("")
        if not self._exec_func(self.setup_test):
            self.log.error("Setup for {} failed, skipping.".format(test_name))
        func_ret = self._exec_func(test_func, *args)
        self.print_case_result(test_name, self.test_method_result)
        # 记录test的运行结果
        self.add_tests_result(test_name, self.test_method_result, start_time, self.test_method_error)
        self._exec_func(self.teardown_test)
        self.test_method_end(test_name)
        return func_ret

    def run_teardown(self):
        event = TrackEvent.TestCase
        extras = {}
        Tracker.event(event.value, event_name=event.name, extraData=extras)
        self.set_case_run_section(RunSection.TEARDOWN)
        self.run_teardown_start()
        self.log.info("**********TearDown Starts!")
        self._exec_func(self.teardown)
        self.log.info("**********TearDown Ends!")
        self.run_teardown_end()
        self._exec_func(self.clean_up)


    def run_perf_models(self, models, fail_break=False):
        """
        models: list, list of model object
        fail_break: bool, if this is set to True, break down the loop of model execution when it fails
        """
        warnings.warn("function is deprecated", DeprecationWarning)
        fail_models, pass_models, total = [], [], len(models)
        for model in models:
            model_name = model.__class__.__name__
            self.log.info("Executing test model {}".format(model_name))
            # 执行jump_to_start_anchor成功后，再执行execute
            self.run_test("{}.jump_to_start_anchor".format(model_name), model.jump_to_start_anchor)
            if self.test_method_result == RunResult.PASSED:
                self.run_test("{}.execute".format(model_name), model.execute)
            if self.test_method_result == RunResult.PASSED:
                pass_models.append(model_name)
                continue
            fail_models.append(model_name)
            if fail_break:
                break
        fail_cnt, pass_cnt = len(fail_models), len(pass_models)
        self.log.info("Test models executed result with "
                      "{} fail({}), {} pass({})".format(fail_cnt, fail_models, pass_cnt, pass_models))
        # 所有model执行通过，用例pass
        if pass_cnt == total:
            self.set_case_error("")
            self.set_case_result(RunResult.PASSED)
            return
        self.set_case_result(RunResult.FAILED)

    def test_method_end(self, test_name):
        """
        case test method end event
        """
        self.log.info("TestMethod: {} result is {}".format(test_name, self.test_method_result))
        self.log.info("TestMethod: {} End".format(test_name))

    def clean_up(self):
        """A function that is executed upon completion of all tests cases
        selected in the test class.
        This function should clean up objects initialized in the constructor
        by user.
        """
        pass

    def run_setup_start(self):
        """A function that is before all tests cases and before setup cases
        selected in the test class.
        This function can be customized to create different base classes or use cases.
        """
        self.setup_start()

    def setup_start(self):
        """A function that is before all tests cases
        selected in the test class.
        This function can be used to execute before running.
        """
        pass

    def run_setup_end(self):
        """A function that is before all tests cases and after setup cases
        selected in the test class.
        This function can be customized to create different base classes or use cases.
        """
        self.setup_end()

    def setup_end(self):
        """A function that is after setup cases
        selected in the test class.
        This function can be used to execute after setup.
        """
        pass

    @classmethod
    def setup_test(cls):
        """Setup function that will be called every time before executing each
        test case in the test class.

        Implementation is optional.
        """
        return True

    def teardown_test(self):
        """Teardown function that will be called every time a test case has
        been executed.
        Implementation is optional.
        """
        pass

    def run_teardown_start(self):
        """A function that is after all tests cases and before teardown cases
        selected in the test class.
        This function can be customized to create different base classes or use cases.
        """
        self.teardown_start()

    def teardown_start(self):
        """A function that is before teardown cases
        selected in the test class.
        This function can be used to execute before running.
        """
        pass

    def run_teardown_end(self):
        """A function that is after all tests cases and teardown cases
        selected in the test class.
        This function can be customized to create different base classes or use cases.
        """
        self.teardown_end()

    def teardown_end(self):
        """A function that is after teardown cases
        selected in the test class.
        This function can be used to execute before running.
        """
        pass

    def loop_start(self):
        pass

    def loop_end(self, result):
        pass

    def loop(self, test_name: Union[str, Callable], looptimes: int = 0, fail_break: bool = False,
             fail_times: int = 0, continues_fail: bool = False, **kwargs):
        """
        test_name: test function to be executed
        fail_break: exit loop when test fail
        fail_times: exit loop when test fail N times
        continues_fail: exit loop when test continuously fail N times
        """
        loop_times = int(looptimes)
        if loop_times <= 0:
            self.log.warning("")
            return
        _test_name = test_name if isinstance(test_name, str) else test_name.__name__
        test_items = []
        for i in range(loop_times):
            loop_name = f"{_test_name}_loop{i + 1}"
            test_items.append((test_name, loop_name))
        self._exec_loop(
            test_items,
            fail_break=fail_break,
            fail_times=fail_times,
            continues_fail=continues_fail,
            **kwargs
        )

    def _exec_loop_tests(self, loop_tests_cfg: dict, test_funcs: List[Tuple[str, Callable]]):
        """执行testfile.json里定义的tests循环执行方案"""
        fail_break = loop_tests_cfg.get("fail_break", False)
        fail_times = loop_tests_cfg.get("fail_times", 0)
        continues_fail = loop_tests_cfg.get("continues_fail", False)
        run_setup_on_fail = loop_tests_cfg.get("run_setup_on_fail", False)
        run_shuffle = loop_tests_cfg.get("run_shuffle", False)
        exclude = loop_tests_cfg.get("exclude")
        if not isinstance(exclude, list):
            exclude = []
        sequence = loop_tests_cfg.get("sequence")

        tests = [name for name, _ in test_funcs]
        set_tests = set(tests)
        # 生成test执行序列
        test_items = []
        if isinstance(sequence, dict):
            loop_times = int(sequence.get("loop"))
            if loop_times < 1:
                self._print_error(ErrorMessage.TestCase.Code_0203018)
                return
            loop_tests = sequence.get("tests")
            if not loop_tests:
                for i in range(1, loop_times + 1):
                    for name in tests:
                        test_items.append((name, f"{name}_loop{i}"))
            else:
                if not set(loop_tests).issubset(set_tests):
                    self._print_error(ErrorMessage.TestCase.Code_0203020)
                    return
                for name in tests:
                    if name in exclude:
                        continue
                    if name not in loop_tests:
                        test_items.append((name, name))
                        continue
                    for i in range(1, loop_times + 1):
                        test_items.append((name, f"{name}_loop{i}"))
        elif isinstance(sequence, list):
            for item in sequence:
                loop_times = int(item.get("loop"))
                if loop_times < 1:
                    self._print_error(ErrorMessage.TestCase.Code_0203018)
                    return
                loop_tests = item.get("tests")
                if not loop_tests:
                    self._print_error(ErrorMessage.TestCase.Code_0203019)
                    return
                if not set(loop_tests).issubset(set_tests):
                    self._print_error(ErrorMessage.TestCase.Code_0203020)
                    return
                for i in range(1, loop_times + 1):
                    for name in loop_tests:
                        if name in exclude:
                            continue
                        test_items.append((name, f"{name}_loop{i}"))
        if not test_items:
            self._print_error(ErrorMessage.TestCase.Code_0203021)
            return
        # 乱序执行
        if run_shuffle:
            random.shuffle(test_items)
        self._exec_loop(
            test_items,
            fail_break=fail_break,
            fail_times=fail_times,
            continues_fail=continues_fail,
            run_setup_on_fail=run_setup_on_fail
        )

    def _exec_loop(self, test_items: List[Tuple[Union[Callable, str], str]],
                   fail_break: bool = False, fail_times: int = 0, continues_fail: bool = False, **kwargs):
        """
        test_items: test function to be executed
        fail_break: exit loop when test fail
        fail_times: exit loop when test fail N times
        continues_fail: exit loop when test continuously fail N times
        """
        _fail_times = 0
        _continues_fail_times = 0
        _last_result = RunResult.PASSED
        run_setup_on_fail = kwargs.get("run_setup_on_fail", False)

        for i, test_item in enumerate(test_items, 1):
            test_name, loop_name = test_item
            if isinstance(test_name, str):
                # 调用方式1：self.loop('test_step', 3)
                _args = []
                _test_func = getattr(self, test_name)
                _test_name = test_name
            else:
                # 调用方式2：self.loop(self.test_step, 3)，此方式的方法绑定了调用对象（对象描述包含bound method），无需在_args中添加调用对象
                # 调用方式3：装饰器
                _args = [] if "bound method" in str(test_name) else [self]
                _test_func = test_name
                _test_name = test_name.__name__
            if self.project.record.is_shutdown():
                self.set_case_error("Testcase is stopped by manual!")
                self.set_case_result(RunResult.FAILED)
                self.log.error(self.error_msg)
                break

            # 判断是否需要在用例失败之后运行setup步骤
            if _last_result != RunResult.PASSED \
                    and isinstance(run_setup_on_fail, bool) and run_setup_on_fail:
                self.log.info("run setup when loop tests failed")
                self.run_setup_start()
                self.log.info("**********SetUp Starts!")
                ret = self._exec_func(self.setup)
                self.log.info("**********SetUp Ends!")
                if not ret:
                    self.log.info("break loop cause run setup failed")
                    break

            # 将当前循环次数同步给self.testLoop
            self.testLoop = i
            self.log.info("run test func: {}".format(loop_name))
            self.loop_start()
            self.run_test(loop_name, _test_func, *_args)
            self.loop_end(self.result)
            self.log.info("run test func: {}, result: {}".format(loop_name, self.test_method_result))

            if DeccVariable.cur_case().test_method.func_ret:
                self.log.warning("FUNCRET has error, clear FUNCRET")
                DeccVariable.cur_case().test_method.func_ret.clear()

            _cur_result = self.test_method_result
            if _cur_result != RunResult.PASSED:
                _fail_times += 1
                self.fail_times = _fail_times
                if continues_fail:
                    if _last_result != RunResult.PASSED:
                        _continues_fail_times += 1
                    else:
                        _continues_fail_times = 1
                    self.con_fail_times = _continues_fail_times
                cat_log_step = kwargs.get("cat_log_step")
                if cat_log_step is not None:
                    self._exec_func(getattr(self, cat_log_step))
                reset_test = kwargs.get("reset_test")
                if reset_test is not None:
                    self._exec_func(getattr(self, reset_test))
            _last_result = _cur_result

            if not fail_break:
                continue
            # 失败立即退出
            if _cur_result != RunResult.PASSED and fail_times == 0:
                break
            # 连续失败多少次退出
            if continues_fail and 0 < fail_times <= _continues_fail_times:
                error_msg = "test func '{}' continues fail {} times in loop".format(
                    _test_name, _continues_fail_times)
                self.log.error(error_msg)
                self.set_case_error(error_msg)
                self.set_case_result(RunResult.FAILED)
                break
            # 失败多少次退出
            elif not continues_fail and 0 < fail_times <= _fail_times:
                error_msg = "test func '{}' fail {} times in loop".format(_test_name, _fail_times)
                self.log.error(error_msg)
                self.set_case_error(error_msg)
                self.set_case_result(RunResult.FAILED)
                break
            else:
                self.set_case_error("")
                self.set_case_result(RunResult.PASSED)

    def print_case_result(self, case, result):
        self.log.info(f"****************************Test {case} result is: {result}")

    def get_case_report_path(self):
        warnings.warn("function is deprecated, use 'self.report_path' instead", DeprecationWarning)
        return self.configs.get("report_path")

    def set_case_error(self, error: str):
        """set case error message"""
        self.__case_error = str(error)

    def get_case_result(self):
        warnings.warn("function is deprecated, use 'self.result' instead", DeprecationWarning)
        return self.result

    def set_case_result(self, result: Union[RunResult, str]):
        """set case result"""
        expect_results = [RunResult.PASSED, RunResult.FAILED, RunResult.BLOCKED, RunResult.UNAVAILABLE]
        if isinstance(result, RunResult) or result in expect_results:
            self.__case_result = result
            return
        self.log.warning(f"the value of result must be an attribute of RunResult, or one of {expect_results}")

    def set_case_result_content(self, content: dict):
        """set result content for testcase（供用例拓展结果内容）
        content: dict, result content
        """
        if not isinstance(content, dict) or not content:
            log.warning("the value of result_content must be a dict and cannot be empty")
            return
        self.log.info(f"set result content: {content}")
        if self.__result_content is None:
            self.__result_content = content
        else:
            self.__result_content.update(content)

    def set_case_run_section(self, section):
        self.cur_case.set_run_section(section)

    def set_test_method_error(self, error: str):
        """set test error message"""
        self.__test_method_error = str(error)

    def set_test_method_result(self, result):
        """set test result"""
        expect_results = [RunResult.PASSED, RunResult.FAILED, RunResult.BLOCKED]
        if isinstance(result, RunResult) or result in expect_results:
            self.__test_method_result = result
            return
        self.log.warning(f"the value of test_method_result must be an attribute of RunResult, "
                         f"or one of {expect_results}")


    def add_tests_result(self, name: str, result: str, start_time: float, error: str):
        """设置tests的运行结果"""
        # 不添加process方法的运行结果
        if name == "process":
            return
        end_time = time.time()
        cost_time = round(end_time - start_time, 2)
        self.__tests_result.append({
            "name": name, "result": result, "time": cost_time, "error": error,
            "begin": time.strftime(ReportConstant.time_format, time.localtime(start_time)),
            "end": time.strftime(ReportConstant.time_format, time.localtime(end_time)),
            "elapsed": calculate_elapsed_time(start_time, end_time),
        })

    # 提示！为避免内部变量被重新赋值，以下property属性不添加setter。如需修改变量，请用对应的set方法
    @property
    def error_msg(self):
        """get case error message"""
        return self.__case_error

    @property
    def report_path(self):
        """get report path"""
        return self.configs.get("report_path")

    @property
    def result(self):
        """get case result"""
        return self.__case_result

    @property
    def screenshot_dir(self):
        """get case screenshot/screenrecorder path"""
        return self.cur_case.get_screenshot_dir()

    @property
    def start_time(self):
        """get case start time"""
        return self.__case_start_time

    @property
    def test_method_error(self):
        """get test error message"""
        return self.__test_method_error

    @property
    def test_method_result(self):
        """get test result"""
        return self.__test_method_result

    @property
    def result_content(self):
        """get case result content"""
        return self.__result_content

    @property
    def tests_result(self):
        """get case tests result"""
        return self.__tests_result


class TestCase(BaseCase):
    """Base class for all test classes to inherit from.
    This class gets all the controller objects from test_runner and executes
    the test cases requested within itself.
    """

    def __init__(self, tag, configs):
        super().__init__(tag, configs)
        self.pass_through = ""

        self._set_configs(configs)
        self._set_pass_through()
        self._set_project(configs)
        self.set_devices(self.configs.get("devices", []))

    def _set_configs(self, controllers):
        if not is_env_pool_run_mode():
            self.configs = controllers
            return
        configs = {
            "report_path": controllers.get("report_path", EnvPool.report_path),
            "request": None,
            ConfigConst.testargs: controllers.get(ConfigConst.testargs, {})
        }
        devices = controllers.get("devices", None)
        if devices:
            if isinstance(devices, list):
                self.devices.extend(devices)
            else:
                self.devices.append(devices)
            configs.update({"devices": self.devices})
        set_devices_test_args(self.devices, controllers)
        self.configs = configs

    def _set_pass_through(self):
        """设置透传参数"""
        test_args = self.configs.get(ConfigConst.testargs, {})
        if is_env_pool_run_mode():
            # 运行在资源池模式
            pass_args = test_args.get(ConfigConst.pass_through, {})
            self.pass_through = json.dumps(pass_args) if isinstance(pass_args, dict) else str(pass_args)
            return
        pass_args = test_args.get(ConfigConst.pass_through, "")
        if pass_args:
            # 运行在命令行模式
            self.pass_through = str(pass_args)
        else:
            # 运行在配置文件模式
            self.pass_through = Variables.config.pass_through

    def _set_project(self, configs):
        project = configs.get("project", None)
        if not project:
            return
        self.project = project
        DeccVariable.set_project_obj(project)
        self.cur_case = DeccVariable.cur_case()
        self._init_case_var(self.TAG)
        self.log.info("init case variables success.")

    def _init_case_var(self, tag):
        if tag:
            self.cur_case.set_name(tag)
        else:
            self.cur_case.set_name(self.project.execute_case_name)

        request = self.configs.get("request", None)
        repeat, repeat_round = 1, 1
        if request is not None and isinstance(request, Request):
            repeat, repeat_round = request.config.repeat, request.get_repeat_round()
        self.cur_case.set_step_total(1)
        self.cur_case.set_case_screenshot_dir(
            self.project.test_suite_path,
            self.project.task_report_dir,
            self.project.cur_case_full_path,
            repeat=repeat, repeat_round=repeat_round)

    def set_devices(self, devices):
        if not devices:
            return
        self.devices = devices
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
            err_msg = ErrorMessage.TestCase.Code_0203007
            log.error(err_msg, is_traceback=True)
            raise DeviceTestError(err_msg) from error

    def set_property(self, index):
        if isinstance(self.project.property_config, dict):
            get_devices = self.project.property_config.get("devices")
            if isinstance(get_devices, list) and len(get_devices) > index:
                propertys = get_devices[index]
                if isinstance(propertys, dict):
                    self.log.debug("set propertys: {}".format(propertys))
                    return propertys
                self.log.debug("get propertys: {}".format(propertys))
                self.log.warning("propertys not a dict!")
        return {}

    def get_property(self, property):
        if hasattr(self, "propertys"):
            get_value = self.propertys.get(property)
            log.debug("get property {}:{}".format(property, get_value))
            return get_value
        else:
            log.warning("'Device' object has no attribute 'propertys'")
            return None

    def get_rpc_timeout(self, device: IDevice) -> Union[int, float, None]:
        """get device rpc timeout
        device: IDevice, device instance
        """
        device_sn = getattr(device, "device_sn", None)
        timeout = getattr(device, "rpc_timeout", None)
        if timeout is None:
            self.log.warning("device '{}' has no attribute 'rpc_timeout'".format(device_sn))
        else:
            self.log.info("device '{}' rpc timeout is {}s".format(device_sn, timeout))
        return timeout

    def set_rpc_timeout(self, device: IDevice, timeout: Union[int, float]):
        """set device rpc timeout
        device: IDevice, device instance
        timeout: int/float, timeout in seconds
        """
        device_sn = getattr(device, "device_sn", None)
        if not hasattr(device, "rpc_timeout"):
            self.log.warning("device '{}' has no attribute 'rpc_timeout'".format(device_sn))
            return
        if isinstance(timeout, (int, float)):
            self.log.info("device '{}' set rpc timeout {}s".format(device_sn, timeout))
            setattr(device, "rpc_timeout", timeout)
        self.log.warning("invalid timeout value '{}'".format(timeout))

    def set_screenrecorder_and_screenshot(self, screenrecorder: bool, screenshot: bool = True):
        """此方法提供给用例调用
        Set whether to enable screen recording or screenshot for the device in the test case
        """
        cur_case = DeccVariable.cur_case()
        if screenrecorder:
            cur_case.is_record_step_screen = True
            cur_case.is_capture_step_screen = False
        else:
            cur_case.is_record_step_screen = False
            cur_case.is_capture_step_screen = True
        for device in self.devices:
            setattr(device, "screenshot", screenshot)
            if hasattr(device, "is_oh"):
                setattr(device, "screenrecorder", screenrecorder)


class WindowsTestCase(TestCase):
    """Base class for all windows test classes to inherit from.
    This class gets all the controller objects from test_runner and executes
    the test cases requested within itself.
    """
    pass


def _log_info_aw_information(func, args, kwargs, is_checkepr=False):
    cur_case = DeccVariable.cur_case()
    if len(cur_case.test_method.func_ret) == 0:
        if is_checkepr:
            cur_case.set_checkepr(True)
            cur_case.cur_check_cmd.__init__()
        else:
            cur_case.set_checkepr(False)
        aw_level = "aw"
    elif len(cur_case.test_method.func_ret) == 1:
        aw_level = "aw1"
    else:
        aw_level = "aw2"
    aw_info = _gen_aw_invoke_info_no_div(func, args, kwargs)
    print_rules = [
        getattr(func, "_ui_adaptive", False),
        kwargs.get('EXCEPTION', True),
    ]
    if all(print_rules):
        log.info("<div class='aw3-container'>"
                 "<div class='aw3' id='rainbowText'>{} ui_adaptive</div>"
                 "</div>".format(aw_info))
    else:
        log.info("<div class='{}'>{}</div>".format(aw_level, aw_info))


def _get_is_raise_exception(kwargs):
    if "EXCEPTION" not in kwargs:
        is_raise_exception = True
    else:
        is_raise_exception = kwargs.pop("EXCEPTION")
    return is_raise_exception, kwargs


def _get_screenshot(kwargs):
    if "SCREENSHOT" not in kwargs:
        screenshot = True
    else:
        screenshot = kwargs.pop("SCREENSHOT")
    return screenshot, kwargs


def _get_msg_args(kwargs):
    msg_args = None
    if "failMsg" in kwargs:
        msg_args = kwargs.pop("failMsg")
        msg_args = '' if msg_args is None else ErrorMessage.TestCase.Code_0203002.format(msg_args)

    return msg_args, kwargs


def _screenshot_and_flash_error_msg(ignore_fail, is_raise_exception, msg_args,
                                    func_name, args, error_msg, screenshot: bool = True):
    if not ignore_fail:
        # 非teardown阶段
        if is_raise_exception:
            _flash_error_msg(msg_args, error_msg)
            raise DeviceTestError(error_msg)
        else:
            # 忽略异常
            log.info("Ignore current exception because parameter EXCEPTION is False.")
    else:
        # teardown阶段
        _flash_error_msg(msg_args, error_msg)
    ScreenAgent.screen_take_picture(args, False, func_name, is_raise_exception=is_raise_exception,
                                    screenshot=screenshot)


def _is_in_teardown_section():
    # 忽略定义在teardown里的接口的运行报错，使得teardown里的每个接口都能被执行
    return DeccVariable.cur_case().run_section == RunSection.TEARDOWN


def _is_in_top_aw():
    starts_num = DeccVariable.cur_case().test_method.func_ret.count("Starts")
    ends_num = DeccVariable.cur_case().test_method.func_ret.count("Ends")
    log.debug("Starts: {}, Ends: {}".format(starts_num, ends_num))
    return starts_num == ends_num


def _check_ret_in_run_keyword(func, args, kwargs, _ret, cost_time,
                              ignore_fail, is_raise_exception, msg_args, screenshot: bool = True):
    aw_info = _gen_aw_invoke_info_no_div(func, args, kwargs)
    result = False if isinstance(_ret, bool) and not _ret else True
    cur_case = DeccVariable.cur_case()
    if _is_in_top_aw():
        cost = 0 if cost_time is None else round(cost_time / 1000, 3)
        log.info("<div class='aw'>{} cost: {}s</div>".format(aw_info, cost))
        cur_case.test_method.func_ret.clear()
        ScreenAgent.screen_take_picture(args, result, func.__name__, is_raise_exception=is_raise_exception,
                                        screenshot=screenshot)

    if not cur_case.checkepr and not result:
        if is_raise_exception and not ignore_fail:
            _flash_error_msg(msg_args, "测试用例执行失败")
            if msg_args:
                raise DeviceTestError(msg_args)
            raise TestFailure(ErrorMessage.TestCase.Code_0203003.format(aw_info))


def _check_ret_in_run_checkepr(func, args, kwargs, _ret, ignore_fail,
                               is_raise_exception, msg_args, screenshot: bool = True):
    cur_case = DeccVariable.cur_case()
    if _is_in_top_aw():
        cur_case.test_method.func_ret.clear()
        result = False if isinstance(_ret, bool) and not _ret else True
        ScreenAgent.screen_take_picture(args, result, func.__name__, is_raise_exception=is_raise_exception,
                                        screenshot=screenshot)
        if not _ret:
            aw_info = _gen_aw_invoke_info_no_div(func, args, kwargs)
            if cur_case.cur_check_cmd.get_cur_check_status():
                msg = cur_case.cur_check_cmd.get_cur_check_msg()
            else:
                msg = "Check Result: {} = {}!".format(_ret, aw_info)
                log.info("Return: {}".format(_ret))

            if is_raise_exception and not ignore_fail:
                _flash_error_msg(msg_args, "测试用例执行失败")
                if msg_args:
                    raise DeviceTestError(msg_args)
                raise TestFailure(ErrorMessage.TestCase.Code_0203003.format(aw_info))
            else:
                log.info(msg)
            time.sleep(0.01)  # 避免日志顺序混乱

        else:
            log.info("Return: {}".format(_ret))


def _check_exception(exception, in_method=False):
    # 测试设备断连找不见, 直接抛出异常
    find_result = re.search(r'device \w* not found|offline', str(exception))
    if find_result is not None:
        err_msg = ErrorMessage.Device.Code_0202306
        log.error(err_msg)
        if in_method:
            return True
        raise DeviceNotFound(err_msg)
    return False


def checkepr(func: T) -> T:
    @wraps(func)
    def wrapper(*args, **kwargs):
        # set default case obj
        if DeccVariable.cur_case() is None:
            cur_case = CurCase(log)
            DeccVariable.set_cur_case_obj(cur_case)
        DeccVariable.project.record.is_shutdown()
        _res = run_checkepr(func, *args, **kwargs)
        return _res

    return wrapper


def keyword(func: T) -> T:
    @wraps(func)
    def wrapper(*args, **kwargs):
        # set default case obj
        if DeccVariable.cur_case() is None:
            cur_case = CurCase(log)
            DeccVariable.set_cur_case_obj(cur_case)
        DeccVariable.project.record.is_shutdown()
        run_k = run_keyword(func, *args, **kwargs)
        return run_k

    return wrapper


def loop(times: int, fail_break: bool = False, fail_times: int = 0, continues_fail: bool = False):
    """循环运行测试方法。当前仅支持在测试用例里面使用
    times: int, loop times
    fail_break: bool, exit loop when test fail
    fail_times: int,  exit loop when test fail N times
    continues_fail: bool, exit loop when test continuously fail N times

    Example1:
        @loop(3, fail_break=True)
        def test_func(self): pass

    Example2:
        @loop(3, fail_break=True, fail_times=2)
        def test_func(self): pass

    Example3:
        @loop(3, fail_break=True, fail_times=2, continues_fail=True)
        def test_func(self): pass
    """

    def loop_decorator(func):
        @wraps(func)
        def wrapper(*args):
            if not args or not hasattr(args[0], 'loop'):
                raise Exception(ErrorMessage.TestCase.Code_0203015)
            self = args[0]
            self.loop(func, looptimes=int(times), fail_break=fail_break,
                      fail_times=fail_times, continues_fail=continues_fail)

        return wrapper

    return loop_decorator


def new_thread(func, *args, **kwargs) -> threading.Thread:
    """创建线程的便捷方法。我们使用线程名称对日志内容进行分流，请勿修改线程名称的命名规则，同时不允许在此线程下开启新线程"""
    t = threading.Thread(target=func, args=args, kwargs=kwargs)
    t.name = threading.current_thread().name + "-" + str(time.time()).replace('.', '')[-5:]
    return t


def handle_pop_and_ui_adaptive(func: T) -> T:
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            if not kwargs.get("EXCEPTION", True):
                function = args[0]
                _ui_adaptive = getattr(function, "_ui_adaptive", False)
                if _ui_adaptive:
                    kwargs.update({"ui_adaptive_enable": False})
                from hypium.uidriver.interface.uitree import ISelector
                for arg in args[1:]:
                    if isinstance(arg, ISelector):
                        arg.set_config("pop_window_dismiss", False)
                for value in kwargs.values():
                    if isinstance(value, ISelector):
                        value.set_config("pop_window_dismiss", False)
        except Exception as e:
            log.warning(e)
            kwargs.pop("ui_adaptive_enable", None)

        return func(*args, **kwargs)

    return wrapper


@handle_pop_and_ui_adaptive
def run_keyword(func, *args, **kwargs):
    _log_info_aw_information(func, args, kwargs)
    DeccVariable.cur_case().test_method.func_ret.append("Starts")
    is_raise_exception, kwargs = _get_is_raise_exception(kwargs)
    screenshot, kwargs = _get_screenshot(kwargs)
    msg_args, kwargs = _get_msg_args(kwargs)
    ignore_fail = _is_in_teardown_section()
    is_exception = True
    _ret = None
    cost_time = 0
    func_name = func.__name__
    try:
        TS.start()
        _ret = func(*args, **kwargs)
        ret_str = str(_ret).replace("<", "&lt").replace(">", "&gt")
        log.debug("func {} ret: {}".format(func_name, ret_str))
        cost_time = TS.stop()
        is_exception = False

        if is_raise_exception and (not ignore_fail) and func_name == 'get_info_from_decc_svr':
            if isinstance(_ret, dict):
                if _ret['code'] != 200 and (_ret['success'] == 'false'
                                            or _ret['success'] is False):
                    raise TestAssertionError('result error.')
    except (DeviceNotFound, DeviceTestError) as e:
        # 设备异常或DeviceTestError，直接将异常抛出，可解决错误码重复添加的问题
        raise e
    except TestAssertionError as exception:
        error_msg = str(exception)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, error_msg, func_name, args, error_msg, screenshot)
    except TypeError as exception:
        error_msg = ErrorMessage.TestCase.Code_0203008.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except HdcCommandRejectedException as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202302.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except ShellCommandUnresponsiveException as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202304.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except AppInstallError as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202307.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except RpcNotRunningError as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202305.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except ConnectionRefusedError as exception:
        # 设备掉线connector client连接拒绝
        error_msg = ErrorMessage.Device.Code_0202306.format(exception)
        log.error(error_msg)
        raise DeviceNotFound(error_msg) from exception
    except Exception as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.TestCase.Code_0203002.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    finally:
        DeccVariable.cur_case().test_method.func_ret.append("Ends")
        # 1.若执行接口出现异常，会进入_screenshot_and_flash_error_msg方法
        # 2.当接口不是定义在teardown里，且没有接口参数没有设置EXCEPTION=False，
        # 那么_screenshot_and_flash_error_msg方法会重新抛出DeviceTestError异常
        # 3.若接口不是定义在teardown里，执行出现异常，且回到了顶层aw，将Starts/Ends计数器清零
        if is_exception and not ignore_fail and _is_in_top_aw():
            log.debug('----------finally clear Starts/Ends--------')
            DeccVariable.cur_case().test_method.func_ret.clear()

    if is_exception:
        if _is_in_top_aw():
            DeccVariable.cur_case().test_method.func_ret.clear()
        return False
    _check_ret_in_run_keyword(func, args, kwargs, _ret, cost_time,
                              ignore_fail, is_raise_exception, msg_args, screenshot)
    return _ret


@handle_pop_and_ui_adaptive
def run_checkepr(func, *args, **kwargs):
    _log_info_aw_information(func, args, kwargs, is_checkepr=True)
    DeccVariable.cur_case().test_method.func_ret.append("Starts")
    is_raise_exception, kwargs = _get_is_raise_exception(kwargs)
    screenshot, kwargs = _get_screenshot(kwargs)
    msg_args, kwargs = _get_msg_args(kwargs)
    ignore_fail = _is_in_teardown_section()
    is_exception = True
    _ret = None
    func_name = func.__name__
    try:
        TS.start()
        # 执行当前函数
        _ret = func(*args, **kwargs)
        ret_str = str(_ret).replace("<", "&lt").replace(">", "&gt")
        log.debug("step {} execute result: {}".format(func_name, ret_str))
        TS.stop()
        is_exception = False
    except (DeviceNotFound, DeviceTestError) as e:
        # 设备异常或DeviceTestError，直接将异常抛出，可解决错误码重复添加的问题
        raise e
    except TestAssertionError as exception:
        error_msg = str(exception)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, error_msg, func_name, args, error_msg, screenshot)
    except TypeError as exception:
        error_msg = ErrorMessage.TestCase.Code_0203008.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except HdcCommandRejectedException as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202302.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except ShellCommandUnresponsiveException as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202304.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except AppInstallError as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202307.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except RpcNotRunningError as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.Device.Code_0202305.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    except ConnectionRefusedError as exception:
        # 设备掉线connector client连接拒绝
        error_msg = ErrorMessage.Device.Code_0202306.format(exception)
        log.error(error_msg, is_traceback=True)
        raise DeviceNotFound(error_msg) from exception
    except Exception as exception:
        _check_exception(exception)
        error_msg = ErrorMessage.TestCase.Code_0203002.format(exception)
        log.error(error_msg, is_traceback=True)
        _screenshot_and_flash_error_msg(
            ignore_fail, is_raise_exception, msg_args, func_name, args, error_msg, screenshot)
    finally:
        DeccVariable.cur_case().test_method.func_ret.append("Ends")
        # 1.若执行接口出现异常，会进入_screenshot_and_flash_error_msg方法
        # 2.当被执行的接口不在teardown阶段里运行，且没有接口参数没有设置EXCEPTION=False，
        # _screenshot_and_flash_error_msg方法会重新抛出DeviceTestError异常
        # 3.若执行非teardown的接口出现异常，且回到了顶层aw，将Starts/Ends计数器清零
        if is_exception and not ignore_fail and _is_in_top_aw():
            log.debug('----------finally clear Starts/Ends--------')
            DeccVariable.cur_case().test_method.func_ret.clear()

    if is_exception:
        if _is_in_top_aw():
            DeccVariable.cur_case().test_method.func_ret.clear()
        return False

    _check_ret_in_run_checkepr(func, args, kwargs, _ret, ignore_fail,
                               is_raise_exception, msg_args, screenshot)
    return _ret


def _flash_error_msg(msg_args, error_msg):
    log.info("flash error msg.")
    # 优先使用断言的自定义异常，然后再是failMsg，最后是捕获的异常
    if msg_args:
        if not DeccVariable.cur_case().test_method.error_msg or \
                not DeccVariable.cur_case().test_method.step_flash_fail_msg:
            DeccVariable.cur_case().test_method.set_error_msg(msg_args)
            DeccVariable.cur_case().test_method.step_flash_fail_msg = True
            if not DeccVariable.cur_case().is_upload_method_result:
                DeccVariable.cur_case().set_error_msg(msg_args)
    else:
        if not DeccVariable.cur_case().test_method.error_msg:
            # 更新当前步骤error_msg
            DeccVariable.cur_case().test_method.set_error_msg(error_msg)
            if not DeccVariable.cur_case().is_upload_method_result \
                    and DeccVariable.cur_case().error_msg:
                DeccVariable.cur_case().set_error_msg(msg_args)

    DeccVariable.cur_case().test_method.set_result(RunResult.FAILED)
    if DeccVariable.cur_case().case_result == RunResult.PASSED:
        DeccVariable.cur_case().set_case_result(RunResult.FAILED)


def _gen_aw_invoke_info_no_div(func, args, kwargs):
    all_args = []
    name_id = None
    if args and getattr(args[0], "__module__", None):
        try:
            _ad = args[0]
            id_strings = []
            _device = getattr(_ad, "_device", None)
            if _device:
                dev_alias = getattr(_device, "device_id", "")
                if dev_alias:
                    id_strings.append(dev_alias)
            dev_sn = getattr(_ad, "device_sn", "")
            if dev_sn:
                id_strings.append(convert_serial(dev_sn))
            name_id = ".".join(id_strings).replace(" ", ".")
        except Exception as exception:
            log.error(exception)
        args = args[1:]
    if name_id is not None:
        all_args.append(name_id)
    if args:
        for arg in args:
            all_args.append(str(arg))
    if kwargs:
        for key, value in kwargs.items():
            all_args.append("{}={}".format(key, value))
    info_items = [
        func.__module__.split(".")[-1:][0], ".", func.__name__,
        "(", ", ".join(all_args), ")"
    ]
    return "".join(info_items)




def GET_TRACEBACK(_trac=""):
    if _trac == "AW":
        return "".join(traceback.format_exception(*sys.exc_info())), \
            traceback.format_exception(*sys.exc_info())[-1].strip()
    return "".join(traceback.format_exception(*sys.exc_info()))


def ASSERT(expect, actual):
    if expect != actual:
        raise TestFailure(ErrorMessage.Assertion.Code_0204026.format(expect, actual))


def CHECK(message, expect, actual):
    if DeccVariable.cur_case() is None:
        cur_case = CurCase(log)
        DeccVariable.set_cur_case_obj(cur_case)
        return
    MESSAGE(message)
    EXPECT(expect)
    ACTUAL(actual)


def MESSAGE(arg):
    if DeccVariable.cur_case() is None:
        cur_case = CurCase(log)
        DeccVariable.set_cur_case_obj(cur_case)
        return
    DeccVariable.cur_case().cur_check_cmd.through = get_decode(arg)
    log.debug("Description: {}".format(
        DeccVariable.cur_case().cur_check_cmd.through))


def EXPECT(arg):
    if DeccVariable.cur_case() is None:
        cur_case = CurCase(log)
        DeccVariable.set_cur_case_obj(cur_case)
        return
    DeccVariable.cur_case().cur_check_cmd.expect = get_decode(arg)
    log.debug("Expected: {}".format(
        DeccVariable.cur_case().cur_check_cmd.expect))


def ACTUAL(arg):
    if DeccVariable.cur_case() is None:
        cur_case = CurCase(log)
        DeccVariable.set_cur_case_obj(cur_case)
        return
    DeccVariable.cur_case().cur_check_cmd.actual = get_decode(arg)
    log.debug("Actual: {}".format(
        DeccVariable.cur_case().cur_check_cmd.actual))


def Step(name, **kwargs):
    """记录用例操作步骤，并展示在用例报告里
    Args:
        name: str, step name
    Example:
        Step("11")
        Step("11", video="a video address")
    """
    cur_case = DeccVariable.cur_case()
    if cur_case is None:
        log.warning("current case object is none, recording step failed")
        return -1
    return cur_case.set_step_info(name, **kwargs)


class step:

    def __init__(self, name: str, enter_func: Callable = None, exit_func: Callable = None, **kwargs):
        """记录用例操作步骤，并展示在用例报告里（with用法）
        Args:
            name: step name
            enter_func: execute function before step
            exit_func : execute function after step
        Example:
            with step("11"): pass
        """
        self.name = name
        self.kwargs = kwargs
        self.__enter_func = enter_func
        self.__exit_func = exit_func
        self.__cur_case = DeccVariable.cur_case()
        self.__index = -1

    def __enter__(self):
        if self.__cur_case:
            self.__index = self.__cur_case.set_step_info(self.name, **self.kwargs)
        else:
            log.warning("current case object is none")
        if self.__enter_func and callable(self.__enter_func):
            self.__enter_func()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__exit_func and callable(self.__exit_func):
            self.__exit_func()
        if self.__cur_case:
            self.__cur_case.end_previous_step()
        else:
            log.warning("current case object is none")
        return False

    @property
    def index(self):
        return self.__index


def ui_adaptive_step(name: str, shot_paths: list, device, **kwargs):
    """记录用例ui自适应操作步骤，并展示在用例报告里
    Args:
        name: str, api名字
        shot_paths: list, 图片位置
        device: 设备
    """
    cur_case = DeccVariable.cur_case()
    if cur_case is None:
        log.warning("current case object is none, recording step failed")
        return -1
    return cur_case.set_ui_step_info(name, shot_paths, device, **kwargs)


def UpdateStep(index, **kwargs):
    """更新步骤记录信息
    Args:
        index: int, step index
    Example:
        index = Step("11")
        UpdateStep(index, video="a video address")
    """
    cur_case = DeccVariable.cur_case()
    if cur_case is None:
        log.warning("current case object is none, updating step failed")
        return
    cur_case.update_step_info(index, **kwargs)


def CheckPoint(checkpoint):
    Step(checkpoint)


def CONFIG():
    return DeccVariable.project.config_json


def get_report_dir(self=None):
    """
    get Path to the framework execution case log folder
    Returns: log_dir_path
    """
    warnings.warn("function is deprecated, use 'self.get_case_report_path()' instead", DeprecationWarning)
    if isinstance(self, TestCase):
        return self.project.task_report_dir
    return DeccVariable.project.task_report_dir


class Property:

    def __init__(self):
        pass

    def add_attributes(self, key, value):
        setattr(self, key, value)
        log.debug("Property setattr {}={}".format(key, value))
