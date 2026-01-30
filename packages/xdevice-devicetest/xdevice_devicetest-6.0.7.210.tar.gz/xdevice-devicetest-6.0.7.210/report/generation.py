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

import collections
import threading
import logging
import os
from jinja2 import Environment, FileSystemLoader

from xdevice import FilePermission
from xdevice import Plugin
from xdevice import Variables
from xdevice import get_plugin
from xdevice import platform_logger

log = platform_logger(name="ReporterHelper")


class BufferHandler(logging.Handler):

    def __init__(self):
        super().__init__()
        self.buffer = collections.deque(maxlen=Variables.config.get_max_log_line_in_html())

    def emit(self, record):
        log_level = record.levelno
        for msg in self.format(record).split('\n'):
            lines = msg.split('\r') if os.name == 'nt' and '\r' in msg else [msg]
            for line in lines:
                if not line:
                    line = '<br>'
                if log_level == logging.ERROR:
                    line = '<div class="error">{}</div>'.format(line)
                elif log_level == logging.WARNING:
                    line = '<div class="warning">{}</div>'.format(line)
                self.buffer.append(line)


def cache_case_log_begin(case_log_hdl: BufferHandler = None):
    if case_log_hdl is None:
        case_log_hdl = BufferHandler()
        case_log_hdl.setFormatter(logging.Formatter(Variables.report_vars.log_format))
    log_plugin = get_log_plugin()
    log_plugin.add_log_handler(threading.current_thread().name, case_log_hdl)
    return case_log_hdl


def cache_case_log_end(case_log_hdl: BufferHandler):
    if case_log_hdl is None:
        return
    case_log_hdl.close()
    log_plugin = get_log_plugin()
    log_plugin.del_log_handler(case_log_hdl)


def get_log_plugin():
    return get_plugin(plugin_type=Plugin.LOG, plugin_id='Tool')[0]


def generate_case_report(to_file, case_info, case_log_hdl, template="case.html", **kwargs):
    """生成用例html报告
    Args:
        to_file: str, generate report in this file
        case_info: dict, test case info
        case_log_hdl: BufferHandler, test case execution log handler
        template: str, render with this template
    Example:
        generate_report(to_file, case_info, case_log_hdl)
    """
    case_logs = case_log_hdl.buffer
    kwargs.update({"case": case_info, "logs": case_logs})
    try:
        os.makedirs(os.path.dirname(to_file), exist_ok=True)
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/template")
        env = Environment(
            loader=FileSystemLoader(template_path),
            lstrip_blocks=True,
            trim_blocks=True)
        template = env.get_template(template)

        html_fd = os.open(to_file, os.O_CREAT | os.O_WRONLY, FilePermission.mode_644)
        with os.fdopen(html_fd, mode="w", encoding="utf-8") as html_f:
            for line in template.generate(kwargs):
                html_f.write(line)
        log.info(f"report is generated in path: {to_file}")
    except Exception as e:
        log.error(f"report generating failed! {e}")
    case_logs.clear()
    del case_log_hdl
