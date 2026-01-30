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

import sys
import traceback
from xdevice import platform_logger


DeviceTestLog = platform_logger("DeviceTest")


def print_image(link, path, title, width_height, desc='Screenshot'):
    link = link.replace('\\', '/')
    content = '<a href="{}" target="_blank">{}: {}' + \
        '<img style="display: block;" {} title="{}" src="{}"/></a>'
    DeviceTestLog.info(content.format(link, desc, path, width_height, title, link))


def print_video(link, path, width_height, desc='Screenshot'):
    link = link.replace('\\', '/')
    content = '<a href="{}" target="_blank">{}: {}' + \
              '<video style="display: block;" {} controls> <source src="{}"></video></a>'
    DeviceTestLog.info(content.format(link, desc, path, width_height, link))


"""
兼容release2脚本需要
"""


def print_info(msg):
    DeviceTestLog.info(msg)


def print_error(msg):
    DeviceTestLog.error(msg)


def print_debug(msg):
    DeviceTestLog.debug(msg)


def print_warn(msg):
    DeviceTestLog.warning(msg)


def print_trace():
    DeviceTestLog.error("".join(
        traceback.format_exception(*sys.exc_info())))
