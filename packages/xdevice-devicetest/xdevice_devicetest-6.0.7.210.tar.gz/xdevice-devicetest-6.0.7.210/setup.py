#!/usr/bin/env python3
# coding=utf-8

#
# Copyright (c) 2020-2022 Huawei Device Co., Ltd.
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
import stat
from setuptools import setup


def get_info(file_path):
    ver = "0.0.0"
    try:
        ver_file_open = os.open(file_path,
                                os.O_RDWR, stat.S_IWUSR | stat.S_IRUSR)
        with os.fdopen(ver_file_open, "r", encoding="utf-8") as file_desc:
            lines = file_desc.readlines()
            for line in lines:
                if line.strip().startswith("VERSION"):
                    ver = line.split("=")[1].strip()
                    ver = ver.replace("'", "").replace('"', "")
    except Exception as e:
        ver = "0.0.0"
    return ver


INSTALL_REQUIRES = [
    "jinja2",
    "xdevice"
]
version = get_info("__init__.py")

setup(
    name='xdevice-devicetest',
    version=version,
    description='device test runner',
    url='',
    package_dir={'devicetest': ''},
    packages=[
        'devicetest',
        'devicetest.controllers',
        'devicetest.controllers.tools',
        'devicetest.controllers.cv',
        'devicetest.core',
        'devicetest.core.suite',
        'devicetest.log',
        'devicetest.report',
        'devicetest.runner',
        'devicetest.utils',
        'devicetest.driver',
        'devicetest.controllers.tools.recorder',
        'devicetest.controllers.tools.recorder.proto',
        'devicetest.record_actions',
    ],
    package_data={
        'devicetest': [
            'res/prototype/native/*.so',
            'res/prototype/native/uitest_agent_v1.1.9.x86_64_so',
            'res/recorder/*',
            'res/template/*',
        ]
    },
    entry_points={
        'driver': [
            'device_test=devicetest.driver.device_test',
        ],
    },
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    extras_require={
        "full": ["numpy", "pillow", "opencv-python", "grpcio", "protobuf"]
    },
)
