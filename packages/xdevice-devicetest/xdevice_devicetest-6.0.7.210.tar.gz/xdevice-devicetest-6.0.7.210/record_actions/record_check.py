import re
import uuid
import os
from functools import wraps
from devicetest.utils.type_utils import T
from devicetest.record_actions.record_action import RecordAction


def check_exception(func: T) -> T:
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_name = func.__qualname__
        ui_driver = args[0]
        result = None
        if not RecordAction.check_recording_switch():
            return func(*args, **kwargs)
        try:
            if len(args) > 0:
                device = getattr(ui_driver, "_device")
                if not hasattr(device, "is_oh"):
                    return func(*args, **kwargs)
            result = func(*args, **kwargs)
            if ("find_component" in api_name or "find_all_components" in api_name) and not result:
                raise CheckException
            elif "wait_for_component" in api_name and not result:
                raise CheckException
            elif "wait_for_component_disappear" in api_name and result:
                raise CheckException
            elif "check_component_exist" in api_name and not result:
                raise CheckException
            elif "check_component" in api_name and not result:
                raise CheckException
            return result
        except CheckException as e:
            ui_driver.log.error("api_name {} failed reason {}".format(api_name, e))
            action_uuid = "{}".format(uuid.uuid4().hex)
            ui_driver.log.info("save picture in {}".format(action_uuid))
            # 拉取截图
            temp_dir = os.path.join(ui_driver._device.get_device_report_path(), "checkfailed",
                                    RecordAction.testcase_name)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            cur_screenshot_path = os.path.join(temp_dir, "{}.jpeg".format(action_uuid))
            ui_driver.capture_screen(cur_screenshot_path, in_pc=True)
            # 拉取layout
            cur_layout_path = os.path.join(temp_dir, "{}.json".format(action_uuid))
            pull_current_layout(ui_driver, cur_layout_path)
            return result
        except Exception as e:
            ui_driver.log.error("api_name {} failed reason {}".format(api_name, e))
            action_uuid = "{}".format(uuid.uuid4().hex)
            ui_driver.log.info("save picture in {}".format(action_uuid))
            # 拉取截图
            temp_dir = os.path.join(ui_driver._device.get_device_report_path(), "checkfailed",
                                    RecordAction.testcase_name)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            cur_screenshot_path = os.path.join(temp_dir, "{}.jpeg".format(action_uuid))
            ui_driver.capture_screen(cur_screenshot_path, in_pc=True)
            # 拉取layout
            cur_layout_path = os.path.join(temp_dir, "{}.json".format(action_uuid))
            pull_current_layout(ui_driver, cur_layout_path)
            raise e

    return wrapper


def pull_current_layout(driver, pc_path: str):
    ret = driver.shell("uitest dumpLayout")
    driver.log.debug(ret)
    pattern = r"DumpLayout saved to:(.*)"
    match = re.search(pattern, ret)
    if match:
        path = match.group(1).strip()
        driver.pull_file(path, pc_path)
        driver.shell("rm {}".format(path))
    else:
        driver.log.debug("dump layout failed")


class CheckException(Exception):
    def __init__(self, msg: str = "check failed"):
        super().__init__(msg)
