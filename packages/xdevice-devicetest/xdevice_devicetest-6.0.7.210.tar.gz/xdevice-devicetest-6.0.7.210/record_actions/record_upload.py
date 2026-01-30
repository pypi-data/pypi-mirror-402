import getpass
import json
import os
import platform
import shutil
import zipfile
import requests

from xdevice import platform_logger
from xdevice import FilePermission
from xdevice import Variables
from xdevice import get_cst_time

from devicetest.record_actions.record_tree import get_bounds
from devicetest.utils.file_util import write_json_file
from devicetest.utils.file_util import load_json_file

LOG = platform_logger("RecordAction")



def upload_native(record_instance, save_path: str, local_path: str) -> bool:
    if not local_path:
        old_res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_data")
        res_path = os.path.join(Variables.config.get_resource_path(), "baseline")
        if os.path.exists(old_res_path):
            try:
                LOG.debug("try to move ui data to resource baseline")
                shutil.move(old_res_path, res_path)
            except Exception as e:
                LOG.warning("move failed {}".format(e))
    else:
        res_path = local_path
    if not os.path.exists(res_path):
        os.makedirs(res_path)
    if record_instance.is_adaptive:
        LOG.debug("Baseline is ui adaptive!")
    else:
        LOG.debug("Baseline is not ui adaptive!")
    file_name = record_instance.testcase_name + ".zip"
    try:
        shutil.copyfile(save_path, os.path.join(res_path, file_name))
        LOG.debug("upload native zip success")
        return True
    except Exception as e:
        LOG.warning("upload native zip failed! reason: {}".format(e))
        return False


def download_native(record_instance, zip_path: str, local_path: str = None) -> bool:
    if not local_path:
        old_res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_data")
        res_path = os.path.join(Variables.config.get_resource_path(), "baseline")
        if os.path.exists(old_res_path):
            try:
                LOG.debug("try to move ui data to resource baseline")
                shutil.move(old_res_path, res_path)
            except Exception as e:
                LOG.warning("move failed {}".format(e))
    else:
        res_path = local_path
    if not os.path.exists(res_path):
        os.makedirs(res_path)
    file_path = os.path.join(res_path, record_instance.testcase_name + ".zip")
    try:
        if os.path.exists(file_path):
            shutil.copyfile(file_path, zip_path)
            return True
        else:
            LOG.warning("Download native failed! Not adaptive find.")
            return False
    except Exception as e:
        LOG.warning("Download native failed! Not adaptive find, reason: {}".format(e))
        return False


def save_native_dfx(record_instance) -> bool:
    try:
        # 在非流水线任务的时候才保存
        from xdevice._core.context.upload import Uploader
        if Uploader.is_enable() and Uploader.get_session().proxy:
            return False
        res_path = os.path.abspath(os.path.join(Variables.exec_dir, "tmp_hypium", "adaptive_suggest_code"))
        if not os.path.exists(res_path):
            os.makedirs(res_path)
        data = {"adaptive_info": record_instance.adaptive_info}
        json_file = record_instance.testcase_name + "_dfx.json"
        json_file_path = os.path.join(res_path, json_file)
        json_fd = os.open(json_file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, FilePermission.mode_644)
        with os.fdopen(json_fd, mode="w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        LOG.debug("save dfx success")
        return True
    except Exception as e:
        LOG.warning("save dfx failed! reason: {}".format(e))
        return False


