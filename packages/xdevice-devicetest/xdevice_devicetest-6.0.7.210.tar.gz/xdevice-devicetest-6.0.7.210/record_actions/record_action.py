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
import importlib.util
import inspect
import json
import os.path
import re
import shutil
import time
import uuid
import hashlib
import traceback
from functools import wraps

from xdevice import get_current_time
from xdevice import FilePermission
from xdevice import Variables
from xdevice import platform_logger
from xdevice import get_cst_time
from xdevice import TrackEvent, Tracker

from devicetest.utils.util import is_standard_lib
from devicetest.utils.util import is_third_party_lib
from devicetest.utils.util import extract_file_method_code
from devicetest.utils.util import get_local_ip_address
from devicetest.utils.time_util import TimeHandler
from devicetest.utils.type_utils import T
from ohos.environment.device import Device
from devicetest.utils.file_util import compress_and_remove
from devicetest.utils.file_util import unzip_file
from devicetest.utils.file_util import load_json_file
from devicetest.record_actions.record_log import AdaptiveLOG
from devicetest.record_actions.record_upload import download_native
from devicetest.record_actions.record_upload import upload_native
from devicetest.record_actions.record_upload import save_native_dfx
from devicetest.record_actions.record_tree import get_widget_by_pos
from devicetest.record_actions.suggested_code import get_func_args
from devicetest.record_actions.suggested_code import generate_suggest_code

UI_COMPONENT_ACTION = "_convert_to_uicomponent"
WAIT_FOR_COMPONENT = "waitForComponent"
UI_OPERATOR = "UiOperator"
UI_COMPONENT = "UiComponent"
ARK_UI_DRIVER = "ArkUiDriver"
SCROLL_SEARCH = "scrollSearch"
CHECK_COMPONENT_EXIST = "check_component_exist"
COMPONENT = "Component#"
ACTION = "action#"
GET_IMAGE_POS = "_get_image_pos"
DEFAULT_FALSE = ["UiOperator.find_component", "UiOperator.wait_for_component"]
AI_ACTION = "ai_action"

AI_ACTION_COMPONENT = ["click", "double_click", "long_click", "swipe", "drag", "input_text_to"]

LOG = platform_logger("RecordAction")


class NewComponentResult:

    def __init__(self, component=None, graph=None, suggest_code=None, action=None):
        self.component = component
        self.graph = graph
        self.suggest_code = suggest_code
        self.action = action


def get_action_path():
    stack = traceback.format_stack()
    filtered_info = []
    debug_keywords = ["pydev_", "debugger", "_pydevd_", "pdb.py"]

    for line in stack:
        if 'File "' in line:
            file_path = line.split('File "', 1)[1].split('"', 1)[0]
            # 检查是否为调试相关文件
            is_debug_file = any(keyword in file_path for keyword in debug_keywords)

            if not is_standard_lib(file_path) and not is_third_party_lib(file_path) and not is_debug_file:
                file_name, method_name, code_line = extract_file_method_code(line)
                if file_name and method_name and code_line:
                    filtered_info.append("{}+{}+{}".format(file_name, method_name, code_line))
    return "-".join(filtered_info)


def timer(func):
    def func_wrapper(*args, **kwargs):
        time_start = time.time()
        result = func(*args, **kwargs)
        time_end = time.time()
        time_spend = time_end - time_start
        LOG.debug('%s cost time: %.3f s' % (func.__name__, time_spend))
        return result

    return func_wrapper


def rank_of_x(t_list: list, target_index: int, target: str):
    x_indices = [i for i, x in enumerate(t_list) if x == target]

    if len(x_indices) == 1:
        return -1
    else:
        return x_indices.index(target_index)


def translate_xpath(hierarchy, json_file) -> str:
    json_content = load_json_file(json_file)
    node = json_content
    xpath = ""
    hierarchy = hierarchy.split(",")
    for index, i in enumerate(hierarchy):
        if "ROOT" in i:
            host_win_id = i.replace("ROOT", "")
            xpath += "/"
            windows = node.get("children")
            root_list = list(map(lambda y: y.get("attributes").get("type"), windows))
            root_host_id = list(map(lambda y: y.get("attributes").get("hostWindowId"), windows))
            root_index = root_host_id.index(host_win_id)
            root_type = root_list[root_index]
            ret = rank_of_x(root_list, root_index, root_type)
            if ret == -1:
                xpath += "{}".format(root_type)
            else:
                xpath += "{}[{}]".format(root_type, ret)
            node = windows[root_index]
        else:
            hierarchy_path = ",".join(hierarchy[:index + 1])
            node = node.get("children")
            hierarchy_list = list(map(lambda y: y.get("attributes").get("hierarchy"), node))
            index_node = hierarchy_list.index(hierarchy_path)
            type_list = list(map(lambda y: y.get("attributes").get("type"), node))
            ret = rank_of_x(type_list, index_node, type_list[index_node])
            node = node[index_node]
            if ret == -1:
                xpath += "/{}".format(node.get("attributes").get("type"))
            else:
                xpath += "/{}[{}]".format(node.get("attributes").get("type"), ret)
    return xpath


def get_user():
    try:
        _ui_adaptive_pass_through = {}
        try:
            pass_through = Variables.config.pass_through
            if pass_through:
                try:
                    pass_through_data = json.loads(pass_through)
                except json.JSONDecodeError:
                    pass_through_data = {}

                adaptive_pass_through = pass_through_data.get("user_define", {}).get("adaptive", {})
                if isinstance(adaptive_pass_through, str) and adaptive_pass_through.strip():
                    try:
                        adaptive_pass_through = json.loads(adaptive_pass_through)
                    except json.JSONDecodeError:
                        adaptive_pass_through = {}

                ui_adaptive_args_pass_through = (pass_through_data.get("user_define", {}).
                                                 get("ui_adaptive_args", {}))

                if isinstance(ui_adaptive_args_pass_through, str) and ui_adaptive_args_pass_through.strip():
                    try:
                        ui_adaptive_args_pass_through = json.loads(ui_adaptive_args_pass_through)
                    except json.JSONDecodeError:
                        ui_adaptive_args_pass_through = {}

                _ui_adaptive_pass_through = ui_adaptive_args_pass_through or adaptive_pass_through
        except Exception as e:
            LOG.error(e)

        adaptive_custom = Variables.config.custom.get("adaptive", {})
        ui_adaptive_args_custom = Variables.config.custom.get("ui_adaptive_args", {})
        _ui_adaptive_custom = ui_adaptive_args_custom or adaptive_custom

        upload = False
        if (_ui_adaptive_custom.get("upload", "false").lower() == "true" or
                _ui_adaptive_pass_through.get("upload", "false").lower() == "true"):
            upload = True

        download = False
        if (_ui_adaptive_custom.get("download", "false").lower() == "true" or
                _ui_adaptive_pass_through.get("download", "false").lower() == "true"):
            download = True

        local_path = _ui_adaptive_custom.get("local_path", None) or _ui_adaptive_pass_through.get("local_path", None)

        user_name = _ui_adaptive_custom.get("user", "") or _ui_adaptive_pass_through.get("user", "")
        return user_name, upload, download, local_path
    except Exception as e:
        LOG.error(e)
        return "", False, False, None


class RecordAction:
    _instance: object = None
    testcase_name: str = None
    testcase_path: str = None
    save_dir: str = None
    tmp_dir: str = None
    md5: str = None
    # report_path
    report_path = ""
    # adaptive_engine_path
    adaptive_engine_path = ""
    # 基线数据
    old_data: dict = {}
    # 新数据
    data: dict = {}
    # record_action装饰器使用
    __action_name: str = None
    __action_api: str = None
    __action: dict = {}
    __action_components: list = []
    # 判断是否有record_action触发中
    __recoding: bool = False
    __record_switch = False
    # 是否启用自适应控件查找
    adaptive_find = False
    # 任务报告路径
    task_report_dir = None

    devices = []

    # Component
    __component_number = -1

    # action
    __action_number = -1

    # driver
    ui_driver = None

    # 触发了自适应，并找到控件时为True
    is_adaptive = False

    # pop handle
    is_pop_handle = False

    # 是否触发了自适应查找
    is_adaptive_find = False

    # 防止convert_to_uicomponent与waitForComponent冲突
    convert_to_uicomponent_record = False

    # hashcode记录器记录相同的actino
    hashcode_list = []

    graph_list = []

    index = 0

    _local_ip = None

    all_record = True

    __suggest_dict = None

    adaptive_info = {}

    __ai_action = False

    __tmp_component = []

    __ai_action_params = {}

    _replay_ai_action = False

    ui_record = False

    ai_record = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
        return cls._instance

    @classmethod
    def local_ip(cls):
        if cls._local_ip is None:
            cls._local_ip = get_local_ip_address()
        return cls._local_ip

    @classmethod
    def component_number(cls) -> int:
        cls.__component_number += 1
        return cls.__component_number

    @classmethod
    def get_component_number(cls) -> int:
        return cls.__component_number + 1

    @classmethod
    def action_number(cls) -> int:
        cls.__action_number += 1
        return cls.__action_number

    @classmethod
    def get_action_number(cls) -> int:
        return cls.__action_number + 1

    @classmethod
    def download_and_load(cls) -> bool:
        zip_path = os.path.join(cls.tmp_dir, "file.zip")
        data = {
            "caseName": cls.testcase_name,
            "adaptive": "0",
            "deviceModel": cls.data.get("deviceModel", ""),
            "deviceVersion": cls.data.get("deviceVersion", ""),
            "deviceType": cls.data.get("deviceType", "")
        }
        try:
            user, _, download, local_path = get_user()
            if download:
                LOG.debug("Download by online.")
                if not download_online(data, user, zip_path):
                    return False
            else:
                LOG.debug("Download by native.")
                if not download_native(cls, zip_path, local_path):
                    return False
            unzip_file(zip_path, cls.tmp_dir)
            json_content = load_json_file(os.path.join(cls.tmp_dir, cls.testcase_name + ".json"))
            cls.adaptive_find = True
            cls.old_data = json_content
            LOG.debug("Load record file successfully.")
            zip_name = "{}+{}+{}+{}".format(cls.old_data.get("deviceModel"), cls.old_data.get("deviceVersion"),
                                            cls.old_data.get("case"),
                                            str(TimeHandler.convert_formated_name(cls.old_data.get("updateTime"),
                                                                                  formate="%Y-%m-%d %H:%M:%S")))
            LOG.debug("Download zip name: {}".format(zip_name))
            return True
        except Exception as e:
            LOG.warning("Download failed. Not adaptive find, reason: {}. "
                        "It will not affect the execution of use cases.".format(e))
            return False

    @classmethod
    def upload_zip(cls, save_path) -> bool:
        user, upload, _, local_path = get_user()
        if upload:
            LOG.debug("Need to upload zip!")
            return upload_online(user, save_path)
        else:
            LOG.debug("No need to upload zip. Use native mode!")
            return upload_native(cls, save_path, local_path)

    @classmethod
    def track_adaptive_event(cls, result: str = None, error_track: str = None, api: str = None,
                             event: TrackEvent = TrackEvent.CaseUiAdaptive, event_id=None):
        LOG.info("Tracking adaptive event")
        adaptive_result = None
        try:
            try:
                pass_through = json.loads(Variables.config.pass_through)
            except Exception as e:
                pass_through = {}
            taskid = pass_through.get("task_id", None)
            if not taskid and cls.task_report_dir:
                taskid = os.path.basename(cls.task_report_dir)
            if event == TrackEvent.CaseUiAdaptive:
                if result == "Passed":
                    if cls.is_adaptive or cls.is_pop_handle:
                        # 用例成功，且触发了自适应
                        adaptive_result = "adaptive_success"
                    elif not cls.is_adaptive and cls.adaptive_find:
                        # 用例成功，但没有触发自适应
                        adaptive_result = "not_adaptive_success"
                    else:
                        # 基线记录成功
                        adaptive_result = "record_success"
                else:
                    if "record_action" in error_track:
                        adaptive_result = "adaptive_failed"
                    else:
                        adaptive_result = "not_adaptive_failed"
                data = {"case_name": cls.testcase_name, "result": adaptive_result, "task_id": taskid}
                AdaptiveLOG.debug("Track adaptive event: {}".format(data))
                Tracker.event(event.value, event_name=event.name, extraData=data)
            elif event == TrackEvent.StepUiAdaptive:
                data = {"case_name": cls.testcase_name, "result": result, "task_id": taskid, "api": api}
                AdaptiveLOG.debug("Track adaptive event: {}".format(data))
                Tracker.event(event.value, event_name=event.name, extraData=data)
            elif event_id == TrackEvent.PopHandle.value:
                if cls.__record_switch and result == "success":
                    cls.is_pop_handle = True
                data = {"case_name": cls.testcase_name, "result": result, "task_id": taskid, "api": api}
                AdaptiveLOG.debug("Track adaptive event pop_handle: {}".format(data))
                Tracker.event(event.value, event_name=event.name, extraData=data)
            elif event == TrackEvent.AiAction or TrackEvent.AiActionAdaptive or TrackEvent.AiActionAI:
                data = {"case_name": cls.testcase_name, "result": None, "task_id": taskid, "api": api}
                Tracker.event(event.value, event_name=event.name, extraData=data)
            return adaptive_result
        except Exception as e:
            LOG.error("Tracking adaptive event failed! {}".format(e))
            return adaptive_result

    @classmethod
    def record_end(cls, result: str) -> None:
        try:
            if not cls.__record_switch:
                return None
            for device in cls.devices:
                delattr(device, "AdaptiveEnginePath")
            if not cls.data.get("deviceModel", None):
                AdaptiveLOG.debug("The deviceModel is None, no record action data!")
                return None
            cls.__delete_instance(result)
            if Variables.temp_dir in cls.task_report_dir and os.path.exists(cls.task_report_dir):
                shutil.rmtree(cls.task_report_dir)
            return None
        finally:
            cls.clear_instance()

    @classmethod
    def __delete_instance(cls, result: str):
        LOG.debug("delete record instance")
        update_time = get_current_time()
        cls.data.update({"updateTime": update_time})
        cls.data.update({"adaptive": cls.is_adaptive})
        if cls.is_adaptive:
            details = cls.data.get("details", {})
            adaptive_find_components = 0
            for _, value in details.items():
                if value.get("is_adaptive", False):
                    adaptive_find_components += 1
                for extras_item in value.get("extras", []):
                    if extras_item.get("is_adaptive"):
                        adaptive_find_components += 1
            AdaptiveLOG.info(
                "The case is adaptive find success! Adaptive find component triggered {} times in this case!".
                format(adaptive_find_components))
        json_file_name = "{}.json".format(cls.testcase_name)
        json_file = os.path.join(cls.save_dir, json_file_name)
        LOG.info("save the record actions in {}".format(json_file))
        json_fd = os.open(json_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FilePermission.mode_644)
        with os.fdopen(json_fd, mode="w", encoding="utf-8") as f:
            json.dump(cls.data, f, indent=4, ensure_ascii=False)
        if result != "Passed":
            AdaptiveLOG.debug("The case result is not passed, No record action data")
            return None
        AdaptiveLOG.debug("The result is passed, upload record zip.")
        # 更新dfx结果
        cls.adaptive_info.update({"case_result": True})
        save_native_dfx(cls)
        zip_name = "{}+{}+{}+{}".format(cls.data.get("deviceModel"), cls.data.get("deviceVersion"), cls.data.get(
            "case"), str(TimeHandler.convert_formated_name(update_time, formate="%Y-%m-%d %H:%M:%S")))
        save_path = os.path.join(os.path.dirname(cls.save_dir), zip_name)
        compress_result = compress_and_remove(cls.save_dir, save_path)
        if compress_result:
            if cls.upload_zip(save_path + ".zip"):
                LOG.debug("upload zip successfully.")
            else:
                LOG.error("upload zip failed.")
        else:
            LOG.debug("The compressed error no upload!")
        return None

    @classmethod
    def delete_instance(cls, result: str, error_track: str):
        try:
            if not cls.__record_switch:
                return None, None
            for device in cls.devices:
                delattr(device, "AdaptiveEnginePath")
            if not cls.data.get("deviceModel", None):
                AdaptiveLOG.debug("The deviceModel is None, no record action data!")
                return None, None
            adaptive_result = None
            cls.__delete_instance(result)
            # 上传自适应信息
            if result == "Passed" and cls.is_adaptive:
                return "adaptive_success", cls.adaptive_info
            # 上传并删除文件
            return adaptive_result, None
        except Exception as e:
            LOG.error("Ignore error: {}".format(e))
            return "", None
        finally:
            cls.clear_instance()

    @classmethod
    def clear_instance(cls):
        cls.cleanup()
        cls._instance = None

    @classmethod
    def cleanup(cls):
        cls.testcase_name = None
        cls.testcase_path = None
        cls.save_dir = None
        cls.tmp_dir = None
        cls.md5 = None
        cls.report_path = ""
        cls.adaptive_engine_path = ""
        cls.old_data = {}
        cls.data = {}
        cls.__action_name = None
        cls.__action_api = None
        cls.__action = {}
        cls.__action_components = []
        cls.__recoding = False
        cls.__record_switch = False
        cls.adaptive_find = False
        cls.task_report_dir = None
        cls.devices = []
        cls.__component_number = -1
        cls.__action_number = -1
        cls.ui_driver = None
        cls.is_adaptive = False
        cls.is_pop_handle = False
        cls.is_adaptive_find = False
        cls.convert_to_uicomponent_record = False
        cls.hashcode_list = []
        cls.graph_list = []
        cls.index = 0
        cls._local_ip = None
        cls.all_record = True
        cls.__suggest_dict = None
        cls.adaptive_info = {}
        cls.__ai_action = False
        cls.__ai_action_params = {}
        cls.__tmp_component = []
        cls._replay_ai_action = False
        cls.ui_record = False
        cls.ai_record = False

    @classmethod
    def __set_init_info(cls, devices: list):
        task_args = Variables.config.taskargs
        if task_args.get("ui_adaptive", "").lower() == "false":
            AdaptiveLOG.info("Ui adaptive is disable. Not record any component!")
            cls.__record_switch = False
            return
        elif task_args.get("ui_adaptive", "").lower() == "true":
            cls.__record_switch = True
            cls.ui_record = True
            cls.ai_record = True
            AdaptiveLOG.info("UI adaptive is enable!")
            AdaptiveLOG.info("record ai action and record ui component!")
        else:
            AdaptiveLOG.info("default record ai action!")
            cls.__record_switch = True
            cls.ai_record = True
        spec = importlib.util.find_spec("adaptive_engine")
        if not spec:
            cls.adaptive_find = False
            AdaptiveLOG.info("adaptive_engine is not installed. Only record component. Not adaptive")
        LOG.debug("set record info")

        cls.report_path = os.path.join(cls.task_report_dir, "Record", cls.testcase_name)
        cls.adaptive_engine_path = os.path.join(cls.task_report_dir, "AdaptiveEngine", cls.testcase_name)
        if not os.path.exists(cls.report_path):
            os.makedirs(cls.report_path)
        cls.save_dir = os.path.join(cls.report_path, "record")
        if not os.path.exists(cls.save_dir):
            os.makedirs(cls.save_dir)
        cls.tmp_dir = os.path.join(cls.report_path, "old_record")
        if not os.path.exists(cls.tmp_dir):
            os.makedirs(cls.tmp_dir)

        device_model = ""
        device_version = ""
        device_type = ""
        product_info = ""

        cls.devices = devices
        for device in devices:
            setattr(device, "AdaptiveEnginePath", cls.adaptive_engine_path)
        target_device = None
        if len(devices) == 1 and hasattr(devices[0], "is_oh"):
            target_device = devices[0]
        else:
            for device in devices:
                if hasattr(device, "device_id") and getattr(device, "device_id") == "DUT":
                    target_device = device
                if not target_device:
                    target_device = device

        if target_device:
            product_info = cls.product_name(target_device)
            product_info_list = product_info.split(" ")
            device_model = product_info_list[0]
            device_version = product_info_list[1]
            device_type = cls.product_type(target_device)
        LOG.debug("create record file.")

        cls.adaptive_info.update({
            "case_name": cls.testcase_name,
            "case_result": None,
            "device_info": product_info,
            "device_type": device_type,
            "steps": []
        })

        cls.data.update({
            "case": cls.testcase_name,
            "md5": cls.md5,
            "deviceModel": device_model,
            "deviceVersion": device_version,
            "deviceType": device_type,
            "updateTime": None,
            "adaptive": None,
            "details": {
            }
        })
        # 这里需要判断是否是单设备，还是主测机。如果有属性，按正常流程走，没有属性则等到第一次获取记录控件的设备的时候。再去下载用例文件。
        if device_model:
            # 下载文件
            cls.download_and_load()

    @classmethod
    def set_init_info(cls, project, devices: list, test_suite: str = None) -> None:
        try:
            if not project or not devices:
                return
            if test_suite:
                cls.testcase_name = project["suite_name"] + "_" + test_suite
                cls.task_report_dir = project["report_path"]
                cls.md5 = cls.testcase_name
            else:
                cls.testcase_name = project.execute_case_name
                cls.task_report_dir = project.task_report_dir
                cls.md5 = cls.testcase_name
            cls.__set_init_info(devices)
        except Exception as e:
            LOG.warning(e)

    @classmethod
    def record_start(cls, casename: str, devices: list, report_path: str = None, all_record: bool = True) -> None:
        cls.testcase_name = casename
        if report_path:
            cls.task_report_dir = report_path
        else:
            task_folder = get_cst_time().strftime("%Y-%m-%d-%H-%M-%S")
            cls.task_report_dir = os.path.join(Variables.temp_dir, task_folder)
        cls.md5 = cls.testcase_name
        cls.all_record = all_record
        try:
            from adaptive_engine.engine import AdaptiveEngine
        except ImportError:
            LOG.info("adaptive_engine is not installed.")
            return
        new_devices = []
        for device in devices:
            if hasattr(device, "is_oh"):
                new_devices.append(device)
            elif getattr(device, "_device", None):
                new_devices.append(device._device)
        cls.__set_init_info(new_devices)

    @classmethod
    @timer
    def get_component_attribute(cls, component, save_uuid: str) -> dict:
        # UiComponent 有_device对象，没有driver对象
        device = getattr(component, "_device", None)
        if not device:
            # CVUiWidget, OCRUiWidget, UiWidget, XpathWidget 只有driver对象，没有_device对象
            driver = getattr(component, "driver", None)
            if driver:
                device = getattr(driver, "_device", None)
        if getattr(device, "is_oh", None):
            properties = component.getAllProperties().to_dict()
            component_name = component.__class__.__name__
            if component_name in ["CVUiWidget", "OCRUiWidget"]:
                # CVUiWidget、OCRUiWidget通过图像获取的走上面
                rect = properties.get("bounds")
                attr = cls.get_widget_attribute(rect, save_uuid)
            elif component_name in ["UiComponent", "XpathWidget"]:
                # UiComponent、XpathWidget是通过layout获取的走下面
                bounds = properties.get("bounds")
                window_id = properties.get("hostWindowId", None)
                cls.pull_layout(cls.ui_driver, save_uuid, window_id=window_id)
                attr = {
                    "bounds": "[{},{}][{},{}]".format(bounds.get("left"), bounds.get("top"), bounds.get("right"),
                                                      bounds.get("bottom")),
                    "xpath": translate_xpath(properties.get("hierarchy"),
                                             os.path.join(cls.save_dir, save_uuid + ".json")),
                }
            elif component_name in ["UiWidget"]:
                # UiWidget可能是ai生成
                bounds = properties.get("bounds")
                if properties.get("hierarchy"):
                    window_id = properties.get("hostWindowId", None)
                    cls.pull_layout(cls.ui_driver, save_uuid, window_id=window_id)
                    attr = {
                        "bounds": "[{},{}][{},{}]".format(bounds.get("left"), bounds.get("top"), bounds.get("right"),
                                                          bounds.get("bottom")),
                        "xpath": translate_xpath(properties.get("hierarchy"),
                                                 os.path.join(cls.save_dir, save_uuid + ".json")),
                    }
                else:
                    attr = cls.get_widget_attribute(component.getBounds(), save_uuid)
            elif component_name in ["XComponentWidget"]:
                layout_name = "{}.json".format(save_uuid)
                tmp_json_path = os.path.join(cls.save_dir, layout_name)
                shutil.copyfile(component.layout, tmp_json_path)
                bounds = properties.get("bounds")
                attr = {
                    "bounds": "[{},{}][{},{}]".format(bounds.get("left"), bounds.get("top"), bounds.get("right"),
                                                      bounds.get("bottom")),
                    "xpath": component.xpath,
                }
            else:
                raise NotImplementedError
        else:
            pos = component.getBoundsCenter().to_tuple()
            attr = cls.get_widget_attribute(pos, save_uuid)
        return attr

    @classmethod
    @timer
    def get_widget_attribute(cls, rect, save_uuid: str) -> dict:
        cls.pull_layout(cls.ui_driver, save_uuid)
        if isinstance(rect, tuple):
            widget = get_widget_by_pos(rect, os.path.join(cls.save_dir, save_uuid + ".json"))
            attr = {
                "pos": rect,
                "bounds": widget.bounds,
                "xpath": widget.xpath,
            }
        else:
            widget = get_widget_by_pos(rect.get_center(), os.path.join(cls.save_dir, save_uuid + ".json"))
            attr = {
                "pos": rect.get_center(),
                "original_bounds": "[{},{}][{},{}]".format(rect.left, rect.top, rect.right, rect.bottom),
                "bounds": widget.bounds,
                "xpath": widget.xpath,
            }
        return attr

    @classmethod
    @timer
    def product_name(cls, device: Device) -> str:
        if getattr(device, "is_oh", None):
            return device.execute_shell_command("param get const.product.software.version").strip()
        else:
            return device.execute_shell_command("getprop ro.build.display.id").strip()

    @classmethod
    @timer
    def product_type(cls, device: Device) -> str:
        return device.get_device_type()

    @classmethod
    @timer
    def pull_img(cls, driver, uu_id: str) -> None:
        img_name = "{}.jpeg".format(uu_id)
        tmp_img_path = os.path.join(cls.save_dir, img_name)
        driver.capture_screen(tmp_img_path, in_pc=True)

    @classmethod
    @timer
    def pull_layout(cls, driver, uu_id: str, **kwargs) -> None:
        layout_name = "{}.json".format(uu_id)
        tmp_json_path = os.path.join(cls.save_dir, layout_name)
        try:
            window_id = kwargs.get("window_id", None)
            driver.UiTree.dump_to_file(tmp_json_path, window_id=window_id)

            try:
                from adaptive_engine.screen_to_layout.process.screen_to_layout import create_xcomponent_layout
                from adaptive_engine.utils.utils import write_json_file
                tmp_jpeg_path = tmp_json_path.replace(".json", ".jpeg")
                data = create_xcomponent_layout(tmp_jpeg_path, tmp_json_path)
                write_json_file(tmp_json_path, json.loads(data))
            except Exception as e:
                LOG.warning("translate xcomponent error {}".format(e))

        except Exception:
            LOG.debug("use normal dumplayout")
            device = driver._device
            for i in range(3):
                ret2 = device.execute_shell_command("uitest dumpLayout").strip()
                LOG.debug(ret2)
                pattern = r"DumpLayout saved to:(.*)"
                match = re.search(pattern, ret2)
                if match:
                    layout_path = match.group(1).strip()
                    device.pull_file(layout_path, tmp_json_path)
                    if os.path.exists(tmp_json_path):
                        device.execute_shell_command("rm {}".format(layout_path))
                        try:
                            from adaptive_engine.screen_to_layout.process.screen_to_layout import \
                                create_xcomponent_layout
                            from adaptive_engine.utils.utils import write_json_file
                            tmp_jpeg_path = tmp_json_path.replace(".json", ".jpeg")
                            data = create_xcomponent_layout(tmp_jpeg_path, tmp_json_path)
                            write_json_file(tmp_json_path, json.loads(data))
                        except Exception as e:
                            LOG.warning("translate xcomponent error {}".format(e))
                    break
                else:
                    LOG.debug("Fail to pull dumpLayout. try again. {}/{}".format(i + 1, 3))
            else:
                LOG.debug("dump layout failed")

    @classmethod
    def copy_file_to_save_dir(cls, eid):
        target_layout = os.path.join(cls.save_dir, "{}.json".format(eid))
        target_screenshot = os.path.join(cls.save_dir, "{}.jpeg".format(eid))

        layout = os.path.join(cls.tmp_dir, "{}.json".format(eid))

        if os.path.exists(layout):
            shutil.copyfile(layout, target_layout)
        screenshot1 = os.path.join(cls.tmp_dir, "{}.jpeg".format(eid))

        if os.path.exists(screenshot1):
            shutil.copyfile(screenshot1, target_screenshot)
        screenshot2 = os.path.join(cls.tmp_dir, "{}.png".format(eid))

        if os.path.exists(screenshot2):
            shutil.copyfile(screenshot2, target_screenshot)

    @classmethod
    def record_action(cls, result: NewComponentResult, is_adaptive: bool = False) -> None:
        component = result.component
        graph = result.graph
        suggest_code = result.suggest_code
        ai_action = result.action

        if str(component) in cls.__tmp_component:
            LOG.debug("{} is already recorded. skip!".format(str(component)))
            return

        cls.__tmp_component.append(str(component))
        action_data = None
        actions = cls.old_data.get("details", {})
        next_hashcode = cls.get_hashcode(print_info=True)
        hash_action = hashlib.md5(next_hashcode.encode('utf-8')).hexdigest()
        components = actions.get(hash_action, {})
        if components and not is_adaptive:
            if not components.get("extras", []):
                component = actions.get(hash_action)
            else:
                new_components = copy.deepcopy(components.get("extras", []))
                new_components.append(components)
                try:
                    component = new_components[cls.index]
                except IndexError:
                    component = components

            action_data = component
            action_data.update({"action": "{}{}".format(ACTION, cls.get_action_number())})
            action_data.update({"component": "{}{}".format(COMPONENT, cls.component_number())})
            action_id = component.get("actionId")
            eid = component.get("eid", action_id)
            cls.copy_file_to_save_dir(eid)
            LOG.info("Use baseline info. skip to record component!")
        else:
            try:
                save_uuid = str(uuid.uuid4().hex)
                device = cls.ui_driver._device
                try:
                    if not isinstance(result.component, str):
                        cls.pull_img(cls.ui_driver, save_uuid)
                        if isinstance(result.component, tuple):
                            attr = cls.get_widget_attribute(component, save_uuid)
                        else:
                            attr = cls.get_component_attribute(component, save_uuid)
                    else:
                        attr = {}
                except Exception as e:
                    LOG.exception("get attr error {}".format(e))
                    attr = {}
                try:
                    product_info = cls.product_name(device).split(" ")
                    device_model = product_info[0]
                    device_version = product_info[1]
                except Exception:
                    device_model = ""
                    device_version = ""
                device_type = device.get_device_type()

                # 更新链路为唯一值
                hashcode = cls.get_hashcode()

                hash_action = hashlib.md5(hashcode.encode('utf-8')).hexdigest()
                action_data = {
                    "deviceModel": device_model,
                    "deviceVersion": device_version,
                    "deviceType": device_type,
                    "deviceLabel": device.device_id,
                    "actionStatus": "run",
                    "actionType": hashcode,
                    "actionAPI": cls.__action_api,
                    "updateTime": int(time.time()),
                    "actionId": save_uuid,
                    "eid": save_uuid,
                    "is_adaptive": is_adaptive,
                    "action": "{}{}".format(ACTION, cls.get_action_number()),
                    "component": "{}{}".format(COMPONENT, cls.component_number())
                }
                # ai action中记录
                if cls.__ai_action_params:
                    action_data.update({"ai_action": cls.__ai_action_params})
                # 回放时记录
                if ai_action:
                    action_data.update({"ai_action": ai_action})
                if suggest_code:
                    action_data.update({"suggestCode": suggest_code})
                if graph:
                    action_data.update({"actionStatus": "graph"})
                    action_data.update({"graph": graph})
                elif cls.graph_list:
                    action_data.update({"actionStatus": "graph"})
                    action_data.update({"graph": cls.graph_list})

                action_data.update({"widgetAttributes": attr})
            except Exception as e:
                LOG.exception("record action error {}".format(e))
                LOG.error("Not record action.")
        if action_data:
            cls.__action_components.append(action_data)
            cls.index += 1
            cls.__action.update({hash_action: action_data})

    @classmethod
    def save_action(cls):
        if cls.__action:
            actions_components = cls.__action_components[:-1]
            if actions_components:
                hashcode = cls.get_hashcode()
                hash_action = hashlib.md5(hashcode.encode('utf-8')).hexdigest()
                cls.__action.get(hash_action, {}).update({"extras": actions_components})
            cls.data.get("details", {}).update(cls.__action)
            cls.action_number()
            try:
                if cls.__suggest_dict and any(
                        [True if component.get("suggestCode", None) and component.get("is_adaptive", False)
                         else False for component in cls.__action_components]):
                    step = generate_suggest_code(cls.__suggest_dict, cls.__action_components)
                    cls.adaptive_info.get("steps", []).append(step)
            except Exception as e:
                LOG.debug("This error is captured and has no impact.")
                LOG.exception(e)

    @classmethod
    def check_recording(cls):
        return cls.__recoding

    @classmethod
    def check_recording_switch(cls):
        return cls.__record_switch

    @classmethod
    def check_ai_action_switch(cls):
        return cls.__ai_action

    @classmethod
    def check_if_show_rainbow(cls):
        return cls.check_recording_switch() and not cls.check_recording()

    @classmethod
    def start_record(cls, ui_driver, action_name: str, api_name: str, suggest_dict: dict, ai_action: bool = False):
        cls.index = 0
        cls.ui_driver = ui_driver
        cls.__action_name = action_name
        cls.__action_api = api_name
        cls.__recoding = True
        cls.__action_components = []
        cls.__suggest_dict = suggest_dict
        cls.__ai_action = ai_action
        cls.__tmp_component = []
        cls.hashcode_list.append(cls.__action_name)
        cls.graph_list = []

    @classmethod
    def check_ai_action(cls):
        return cls.__ai_action

    @classmethod
    def end_record(cls):
        cls.save_action()
        cls.__action_name = ""
        cls.__action_api = ""
        cls.__action = {}
        cls.__recoding = False
        cls.__suggest_dict = None
        cls.__ai_action = False
        cls.__tmp_component = []
        cls.ui_driver = None
        cls.graph_list = []
        cls.index = 0
        cls.__action_components = []

    @classmethod
    def start_record_ai_action(cls, params: dict):
        cls.__ai_action_params = params

    @classmethod
    def end_record_ai_action(cls):
        cls.__ai_action_params = {}

    @classmethod
    def start_convert_to_uicomponent_record(cls):
        cls.convert_to_uicomponent_record = True

    @classmethod
    def end_convert_to_uicomponent_record(cls):
        cls.convert_to_uicomponent_record = False

    @classmethod
    def check_convert_to_uicomponent_record(cls):
        return cls.convert_to_uicomponent_record

    @classmethod
    def record_component(cls, result: NewComponentResult, is_adaptive: bool = False):
        if not cls.__action_name and not cls.__recoding:
            return
        cls.record_action(result, is_adaptive)

    @classmethod
    def find_component_function(cls, ui_driver, component: dict, scroll_target=None, strategy: str = None):
        from adaptive_engine.engine import AdaptiveEngine
        from adaptive_engine.exception import TargetComponentError
        # 先在当前页面查找
        LOG.debug("action: {}".format(component))
        action_id = component.get("actionId")
        eid = component.get("eid", action_id)
        action_type = component.get("actionType")
        device_type = component.get("deviceType")
        kwargs = {}
        try:
            api = action_type.split("+")[-1]
            kwargs.update({
                "api": api,
                "old_device_type": device_type,
            })
            if strategy:
                kwargs.update({
                    "extend": {
                        "strategy": strategy,
                    }
                })
        except Exception as e:
            LOG.debug(e)
            LOG.debug("Not find action name. Ignore")
        xpath = component.get("widgetAttributes", {}).get("xpath")
        if not xpath:
            LOG.debug("not find attr info, skip find new component!")
            return None, None
        kwargs.update({"widgetAttributes": component.get("widgetAttributes", {})})
        layout = os.path.join(cls.tmp_dir, "{}.json".format(eid))
        try:
            comp = None
            suggest_code = None
            cls.is_adaptive_find = True
            if scroll_target:
                scroll_target.scrollToTop()
                adaptive = AdaptiveEngine(ui_driver, layout, xpath, is_scroll_search=False, **kwargs)
                comp = adaptive.find_component(mode="old", scroll_target=scroll_target)
                if hasattr(adaptive, "generate_code"):
                    suggest_code = adaptive.generate_code()
            else:
                adaptive = AdaptiveEngine(ui_driver, layout, xpath, is_scroll_search=False, **kwargs)
                comp = adaptive.find_component(mode="old")
                if hasattr(adaptive, "generate_code"):
                    suggest_code = adaptive.generate_code()
            return comp, suggest_code
        except TargetComponentError as e:
            LOG.warning(e)
            return None, None

    @classmethod
    def find_component_in_next_3step(cls, ui_driver, actions: dict, next_index_list: list, need_to_skip: list):
        # 尝试查找下三个控件
        # 参数不对，目前没用到，暂时不用管
        for component_hash_action in next_index_list:
            target_component, _ = cls.find_component_function(ui_driver, actions, component_hash_action, need_to_skip)
            if target_component:
                # 查找到的全部跳过
                for skip_component in need_to_skip:
                    hash_action, component = skip_component
                    component.update({"actionStatus": "skip"})
                    component.update({"is_adaptive": True})
                    cls.data.get("details", {}).update({hash_action: component})
                # 获取到下一步的控件，直接返回点击
                return target_component
        else:
            return None

    @classmethod
    def find_new_component(cls, old_component=None, return_pos=False, scroll_target=None,
                           strategy: str = None) -> NewComponentResult:
        try:
            AdaptiveLOG.debug("Try to find new component")
            if not cls.__action_name or not cls.adaptive_find:
                AdaptiveLOG.debug("No action name found, skip finding new component")
                return NewComponentResult()
            if old_component:
                device = old_component._device
                from hypium import UiDriver
                ui_driver = UiDriver(device)
            else:
                ui_driver = cls.ui_driver
            if not cls.old_data:
                LOG.warning("No record data! skip find new component adaptive!")
                return NewComponentResult()

            actions = cls.old_data.get("details", {})
            # 更新链路为唯一值

            next_hashcode = cls.get_hashcode(print_info=True)
            # 当前操作的控件的hashcode
            hash_action = hashlib.md5(next_hashcode.encode('utf-8')).hexdigest()

            components = actions.get(hash_action, {})
            if not components:
                LOG.warning("No action found! skip find new component adaptive!")
                return NewComponentResult()
            if not components.get("extras", []):
                component = actions.get(hash_action)
            else:
                new_components = copy.deepcopy(components.get("extras", []))
                new_components.append(components)
                try:
                    component = new_components[cls.index]
                except IndexError:
                    component = components

            widget_attributes = component.get("widgetAttributes", {})
            ai_action = component.get("ai_action", {})

            if not widget_attributes:
                return NewComponentResult(action=ai_action)

            target_component = None
            target_component, suggest_code = cls.find_component_function(ui_driver, component,
                                                                         scroll_target=scroll_target, strategy=strategy)
            # 查找成功直接返回
            if target_component:
                if return_pos:
                    return NewComponentResult(target_component.getBoundsCenter().to_tuple(), None, suggest_code,
                                              ai_action)
                else:
                    return NewComponentResult(target_component, None, suggest_code, ai_action)

            return NewComponentResult()
        except Exception as e:
            LOG.exception(e)
            return NewComponentResult()

    @classmethod
    def get_hashcode(cls, print_info: bool = False) -> str:
        if print_info:
            LOG.debug("action name: {}".format(cls.__action_name))
        action_times = cls.hashcode_list.count(cls.__action_name) - 1
        if print_info:
            LOG.debug("{} action name {} time emergence".format(cls.__action_name, action_times + 1))
        if action_times == 0:
            next_hashcode = cls.__action_name
        else:
            next_hashcode = cls.__action_name + str(action_times)
        return next_hashcode

    @classmethod
    def get_extras_len(cls):
        actions = RecordAction.old_data.get("details", {})
        # 更新链路为唯一值
        next_hashcode = RecordAction.get_hashcode()
        # 当前操作的控件的hashcode
        hash_action = hashlib.md5(next_hashcode.encode('utf-8')).hexdigest()
        component_info = actions.get(hash_action, {})
        return len(component_info.get("extras", []))

    @classmethod
    def check_action_status(cls):
        from adaptive_engine.exception import TargetComponentError
        next_hashcode = hashlib.md5(cls.get_hashcode().encode('utf-8')).hexdigest()
        old_details = cls.old_data.get("details", {})
        old_component = old_details.get(next_hashcode, {})
        new_details = cls.data.get("details", {})
        action_status = old_component.get("actionStatus", "run")
        graph_list = old_component.get("graph", [])
        action_type = old_component.get("actionType")
        if action_status == "graph":
            LOG.debug("check graph exist. need to run graph step.")
            new_graph_list = []
            from devicetest.record_actions.graph_search import run_action_list
            try:
                for run_path in graph_list:
                    page_id = run_path["exactSceneId"]
                    action_list = run_path["actionList"]
                    run_action_list(cls.ui_driver, page_id, action_list, cls.tmp_dir, cls.save_dir)
                    new_graph_list.append(run_path)
            except TargetComponentError as e1:
                LOG.debug(e1)
                try:
                    from devicetest.record_actions.graph_search import find_component_in_graph
                    action_id = old_component.get("actionId")
                    eid = old_component.get("eid", action_id)
                    xpath = old_component.get("widgetAttributes", {}).get("xpath")
                    layout = os.path.join(cls.tmp_dir, "{}.json".format(eid))
                    _, graph = find_component_in_graph(cls, cls.ui_driver, layout, xpath)
                    new_graph_list.extend(graph)
                except TargetComponentError as e2:
                    LOG.error(e2)
                    LOG.error("Can not go to the target component page! action is: {}".format(action_type))
            return new_graph_list
        else:
            return []

    @classmethod
    def set_replay_ai_action(cls, state: bool = True):
        cls._replay_ai_action = state

    @classmethod
    def get_replay_ai_action(cls):
        return cls._replay_ai_action

    @classmethod
    def get_is_ai_action(cls):
        return cls.__ai_action and cls.ai_record


def extract_version(version_str):
    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', version_str)
    if match:
        return match.group(1)
    return None


def check_exception_in_action_name(name: str) -> bool:
    api = name.split("+")[-1]
    if "EXCEPTION=False" in api:
        return True
    else:
        return False


def check_enable_ui_adaptive(switch: bool, ui_adaptive_enable: bool):
    if switch:
        return switch
    else:
        return ui_adaptive_enable


def run_ai_action(driver, start: NewComponentResult, end: NewComponentResult = None):
    try:
        RecordAction.set_replay_ai_action(True)
        from hypium_turbo.agents.agents_impl.basic_action_agent import GuiAgent
        gui_agent = GuiAgent(driver)
        if start.action:
            action_type = start.action.get("actionType")
            params = copy.deepcopy(start.action)
            if "drag" in action_type:
                if start.component:
                    params.update({"start": start.component})
                if end.component:
                    params.update({"end": end.component})
            else:
                if start.component:
                    params.update({"target_description": start.component})
            params.pop("actionType", None)
            func = getattr(gui_agent, action_type.split(".")[-1], None)
            if func:
                func(**params)
                return True
        return False
    finally:
        RecordAction.set_replay_ai_action(False)


def ui_adaptive(func: T) -> T:
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_name = func.__qualname__
        if api_name in DEFAULT_FALSE:
            ui_adaptive_enable = kwargs.pop("ui_adaptive_enable", False)
        else:
            ui_adaptive_enable = kwargs.pop("ui_adaptive_enable", RecordAction.all_record)
        action_name = get_action_path()

        rules = [
            not RecordAction.check_recording_switch(),
            check_exception_in_action_name(action_name),
            not check_enable_ui_adaptive(RecordAction.check_recording(), ui_adaptive_enable),
            RecordAction.get_replay_ai_action()
        ]
        if any(rules):
            return func(*args, **kwargs)
        elif api_name == UI_COMPONENT_ACTION:
            try:
                if api_name == UI_COMPONENT_ACTION:
                    RecordAction.start_convert_to_uicomponent_record()

                if (len(args) >= 2 and getattr(args[1], "_target_description", "")
                        and not RecordAction.check_ai_action()):
                    component_result = RecordAction.find_new_component(strategy="AI_ACTION")
                    if component_result.component:
                        if RecordAction.check_recording():
                            LOG.debug("The record action has been triggered. "
                                      "Need record component by action BY.target wraps.")
                            RecordAction.record_component(component_result, is_adaptive=False)
                        return component_result.component

                result = func(*args, **kwargs)
                if RecordAction.check_recording() and (RecordAction.ui_record or RecordAction.get_is_ai_action()):
                    LOG.debug("The record action has been triggered. "
                              "Need record component by action UI_COMPONENT_ACTION wraps.")
                    RecordAction.record_component(NewComponentResult(result))
                return result
            except Exception as e:
                try:
                    from hypium.exception import HY_ComponentNotFoundError
                except ImportError:
                    HY_ComponentNotFoundError = int
                try:
                    from hypium.exception import HypiumComponentNotFoundError
                except ImportError:
                    HypiumComponentNotFoundError = int
                try:
                    from hypium.exception import HY_ParamUiTargetError
                except ImportError:
                    HY_ParamUiTargetError = int
                if (isinstance(e, (HY_ComponentNotFoundError, HypiumComponentNotFoundError, HY_ParamUiTargetError))
                        and RecordAction.adaptive_find and not RecordAction.check_ai_action()):
                    new_result = RecordAction.find_new_component()
                    if new_result.component:
                        if RecordAction.check_recording():
                            LOG.debug("The record action has been triggered. "
                                      "Need record component by action UI_COMPONENT_ACTION wraps.")
                            RecordAction.record_component(new_result,
                                                          is_adaptive=True)
                            RecordAction.is_adaptive = True
                        return new_result.component
                    else:
                        if isinstance(e, HY_ComponentNotFoundError):
                            raise HY_ComponentNotFoundError(args[1]) from e
                        elif isinstance(e, HypiumComponentNotFoundError):
                            raise HypiumComponentNotFoundError(args[1]) from e
                        else:
                            raise HY_ParamUiTargetError(type(args[1]), is_no_pos=True) from e
                else:
                    LOG.error("Execute func error, no need record component by action UI_COMPONENT_ACTION")
                    raise e
            finally:
                if api_name == UI_COMPONENT_ACTION:
                    RecordAction.end_convert_to_uicomponent_record()

        elif UI_COMPONENT in api_name and SCROLL_SEARCH not in api_name:
            component = args[0]
            component_change = False
            new_args = []
            if not RecordAction.check_recording() and RecordAction.ui_record:
                LOG.debug("The record component has been triggered. Need record component UI_COMPONENT wraps.")
                try:
                    RecordAction.record_component(NewComponentResult(component))
                except RuntimeError as e:
                    if RecordAction.adaptive_find:
                        LOG.error("The Component maybe is change! reason: {}".format(e))
                        new_result = RecordAction.find_new_component(component)
                        if new_result.component:
                            RecordAction.record_component(new_result, is_adaptive=True)
                            RecordAction.is_adaptive = True
                            new_args = list(args)
                            new_args[0] = new_result.component
                            component_change = True
                        else:
                            raise e
                    else:
                        raise e

            else:
                LOG.debug("The record action has been triggered. No need record component UI_COMPONENT wraps.")
            try:
                if component_change:
                    result = func(*new_args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                if not RecordAction.check_recording():
                    RecordAction.save_action()
                return result
            except Exception as e:
                LOG.error("Execute func error, no need record component UI_COMPONENT")
                raise e
        elif ARK_UI_DRIVER in api_name:
            if RecordAction.check_convert_to_uicomponent_record():
                return func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            if result and RecordAction.check_recording() and RecordAction.ui_record:
                LOG.debug("The record action has been triggered. "
                          "Need record component by action ARK_UI_DRIVER wraps.")
                RecordAction.record_component(NewComponentResult(result))
            elif not result and RecordAction.adaptive_find:
                new_result = RecordAction.find_new_component()
                if new_result.component:
                    if RecordAction.check_recording():
                        LOG.debug("The record action has been triggered. "
                                  "Need record component by action ARK_UI_DRIVER wraps.")
                        RecordAction.record_component(new_result, is_adaptive=True)
                        RecordAction.is_adaptive = True
                result = new_result.component
            return result
        elif SCROLL_SEARCH in api_name:
            if RecordAction.check_convert_to_uicomponent_record():
                return func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            if result and RecordAction.check_recording() and RecordAction.ui_record:
                LOG.debug("The record action has been triggered. "
                          "Need record component by action SCROLL_SEARCH wraps.")
                RecordAction.record_component(NewComponentResult(result))
            elif not result and RecordAction.adaptive_find:
                scroll_target = args[0]
                new_result = RecordAction.find_new_component(scroll_target=scroll_target)
                if new_result.component:
                    if RecordAction.check_recording():
                        LOG.debug("The record action has been triggered. "
                                  "Need record component by action SCROLL_SEARCH wraps.")
                        RecordAction.record_component(new_result, is_adaptive=True)
                        RecordAction.is_adaptive = True
                result = new_result.component
            return result
        elif GET_IMAGE_POS in api_name:
            if RecordAction.check_convert_to_uicomponent_record():
                return func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            if result and RecordAction.check_recording() and RecordAction.ui_record:
                LOG.debug("The record action has been triggered. "
                          "Need record component by action GET_IMAGE_POS wraps.")
                RecordAction.record_component(NewComponentResult(result))
            elif not result and RecordAction.adaptive_find:
                new_result = RecordAction.find_new_component(return_pos=True)
                if new_result.component:
                    if RecordAction.check_recording():
                        LOG.debug("The record action has been triggered. "
                                  "Need record component by action GET_IMAGE_POS wraps.")
                        RecordAction.record_component(new_result, is_adaptive=True)
                        RecordAction.is_adaptive = True
                result = new_result.component
            return result
        else:
            try:
                if RecordAction.check_recording():
                    return func(*args, **kwargs)
                # 获取touch等方法里的driver
                driver = args[0]

                suggest_dict = get_func_args(func, args, kwargs)

                RecordAction.start_record(driver, action_name, api_name, suggest_dict)
                LOG.debug("start record action!")
                try:
                    result = func(*args, **kwargs)
                finally:
                    LOG.debug("end record action!")
                    RecordAction.end_record()
                return result
            except Exception as e:
                LOG.error("Execute func error, no need record action")
                raise e

    wrapper._ui_adaptive = True
    return wrapper


def record_action(func: T) -> T:
    return ui_adaptive(func)


def _get_params(func: T, api_name, *args, **kwargs) -> dict:
    sig = inspect.signature(func)
    # 将位置参数和关键字参数绑定到对应的参数名
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()  # 使用默认值填充未在调用中提供的参数
    params = dict(bound_args.arguments)
    ai_action = {
        "actionType": api_name
    }
    ai_action.update(params)
    ai_action.pop("self", None)
    ai_action.pop("target_description", None)
    ai_action.pop("start", None)
    ai_action.pop("end", None)
    ai_action.pop("driver", None)
    LOG.debug(ai_action)
    return ai_action


def ai_adaptive(func: T) -> T:
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_name = func.__qualname__
        if AI_ACTION in api_name:
            # 仅记录ai_action的触发数
            RecordAction.track_adaptive_event(api=f"{api_name}.{args[1]}", event=TrackEvent.AiAction)
        LOG.debug(api_name)
        if api_name in DEFAULT_FALSE:
            ui_adaptive_enable = kwargs.pop("ui_adaptive_enable", False)
        else:
            ui_adaptive_enable = kwargs.pop("ui_adaptive_enable", RecordAction.all_record)
        action_name = get_action_path()

        rules = [
            not RecordAction.check_recording_switch(),
            check_exception_in_action_name(action_name),
            not check_enable_ui_adaptive(RecordAction.check_recording(), ui_adaptive_enable),
            RecordAction.get_replay_ai_action()
        ]
        if any(rules):
            return func(*args, **kwargs)
        elif AI_ACTION in api_name:
            try:
                if RecordAction.check_recording():
                    return func(*args, **kwargs)
                # 获取touch等方法里的driver
                driver = args[0]

                RecordAction.start_record(driver, action_name, api_name, {}, True)
                LOG.debug("start record action!")
                try:
                    all_result = []
                    i = 0
                    max_times = RecordAction.get_extras_len() + 1
                    while i < max_times:
                        start_result = RecordAction.find_new_component(strategy="AI_ACTION")
                        _result = False

                        if not start_result.component and not start_result.action:
                            break

                        try:
                            if start_result.component:
                                if RecordAction.check_recording():
                                    LOG.debug("The record action has been triggered. "
                                              "Need record component by action AI_ACTION wraps.")
                                    RecordAction.record_component(start_result, is_adaptive=False)

                                # 处理拖拽操作
                                if start_result.action and "drag" in start_result.action.get("actionType", ""):
                                    end_result = RecordAction.find_new_component(strategy="AI_ACTION")
                                    if end_result.component:
                                        if RecordAction.check_recording():
                                            LOG.debug("The record action has been triggered. "
                                                      "Need record component by action AI_ACTION wraps.")
                                            RecordAction.record_component(end_result, is_adaptive=False)
                                        _result = run_ai_action(driver, start_result, end_result)
                                        all_result.append(_result)
                                        # 拖拽操作消耗两个组件，所以增加一次计数
                                        i += 2
                                        continue

                                _result = run_ai_action(driver, start_result)
                            elif start_result.action:
                                component = api_name
                                for key, value in start_result.action.items():
                                    component += "#{}#{}".format(key, value)
                                RecordAction.record_component(
                                    NewComponentResult(component=component, action=start_result.action),
                                    is_adaptive=False)
                                _result = run_ai_action(driver, start_result)

                            all_result.append(_result)
                            i += 1
                        except Exception as e:
                            LOG.error(f"Error executing action: {e}")
                            all_result.append(False)
                            break

                    if not all(all_result) or not all_result:
                        # ai_action 传统逻辑代码自适应自适应失败，走AI的逻辑兜底
                        result = func(*args, **kwargs)
                        if AI_ACTION in api_name and result and getattr(result, "finished", False):
                            RecordAction.track_adaptive_event(api=f"{api_name}.{args[1]}",
                                                              event=TrackEvent.AiActionAI)
                    else:
                        # ai_action 传统逻辑代码自适应成功
                        if AI_ACTION in api_name:
                            RecordAction.track_adaptive_event(api=f"{api_name}.{args[1]}",
                                                              event=TrackEvent.AiActionAdaptive)
                        return True
                finally:
                    LOG.debug("end record action!")
                    RecordAction.end_record()
                return result
            except Exception as e:
                LOG.error("Execute func error, no need record action")
                raise e
        elif api_name.split(".")[-1] in AI_ACTION_COMPONENT:
            ai_action = _get_params(func, api_name, *args, **kwargs)
            try:
                RecordAction.start_record_ai_action(ai_action)
                return func(*args, **kwargs)
            finally:
                RecordAction.end_record_ai_action()
        else:
            ai_action = _get_params(func, api_name, *args, **kwargs)
            try:
                RecordAction.start_record_ai_action(ai_action)
                component = api_name
                for key, value in ai_action.items():
                    component += "#{}#{}".format(key, value)
                RecordAction.record_component(NewComponentResult(component=component, action=ai_action),
                                              is_adaptive=False)
                return func(*args, **kwargs)
            finally:
                RecordAction.end_record_ai_action()

    return wrapper


class UiAdaptiveRecord:

    @classmethod
    def start_record(cls, casename: str, devices: list, report_path: str = None, all_record: bool = True):
        """
        启动ui自适应记录器
        :param casename: 用例名字
        :param devices: 设备对象列表，可以传driver，或者device
        :param report_path: 报告路径，不填默认在临时目录
        :param all_record: 是否全程默认开启记录，如果为True默认操作都记录控件信息，
                        如果为False,只有操作中传入ui_adaptive_enable=True才会记录
        """
        RecordAction.record_start(casename, devices, report_path, all_record)

    @classmethod
    def end_record(cls, result: str):
        """
        结束ui自适应记录器
        :param result: 用例结果，填入Passed才会记录基线。
        """
        RecordAction.record_end(result)
