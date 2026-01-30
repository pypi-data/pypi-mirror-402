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

from devicetest.core.exception import TestPrepareError
from devicetest.error import ErrorMessage
from devicetest.log.logger import DeviceTestLog as Log
from devicetest.runner.test_runner import TestRunner
from devicetest.runner.test_runner import TestSuiteRunner


class DeviceTest:

    def __init__(self, test_list, configs, devices):
        self.test_list = test_list or []
        self.configs = configs or {}
        self.devices = devices or []

    def run(self):
        try:
            test_runner = TestRunner()
            test_runner.init_pipeline_runner(self.test_list, self.configs, self.devices)
            test_runner.run()
        except TestPrepareError as err:
            Log.error(err)
        except Exception as err:
            Log.error(ErrorMessage.Common.Code_0201017)
            Log.exception(err, exc_info=True)


class DeviceTestSuite:

    def __init__(self, test_list, configs, devices):
        self.test_list = test_list or []
        self.configs = configs or {}
        self.devices = devices or []

    def run(self):
        try:
            test_runner = TestSuiteRunner(self.test_list, self.configs, self.devices)
            test_runner.run()
        except Exception as err:
            Log.error(ErrorMessage.Common.Code_0201017)
            Log.error("Failed to instantiate the test runner.")
            Log.exception(err, exc_info=True)
