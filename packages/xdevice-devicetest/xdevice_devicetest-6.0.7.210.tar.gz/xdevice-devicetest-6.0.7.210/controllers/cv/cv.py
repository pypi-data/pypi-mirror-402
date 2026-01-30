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
import os
import time
try:
    import numpy as np
except ImportError:
    pass
from xdevice import DeviceError
from devicetest.controllers.cv import _cv
from devicetest.error import ErrorMessage
from devicetest.utils.file_util import get_resource_path


def find_image(self, src_img, obj_img, similar, index):
    '''
    @summary: 查询图片
    @param  src_img: 原图片路径
            obj_img: 目标图片路径
            similar: 相似度
            index：个数
    @return: 布尔类型,比对结果
    '''

    return True


def match_image(self, src_img, dst_img, similar):
    '''
    @summary: 匹配图片
    @param  src_img: 原图片路径
            dst_img： 目地图片路径
            similar: 相似度
    @return: 布尔类型,比对结果
    '''

    return True


def get_area_by_point(self, img, point_x, point_y):
    '''
    @summary: 获取图片区域
    @param  img: 图片路径
            x: x坐标
            y: y坐标
    @return: 布尔类型,比对结果
    '''

    return True


def get_image_hots(self, img):
    '''
    @summary: 获取图片热点
    @param  img: 图片路径
    @return: 布尔类型,比对结果
    '''
    return True


def match_image_location(src_img, img_path):
    return _cv.match_image_location(src_img, img_path)


def touch_image(device, src_path, duration=0.1,
                similar=0.95, timeout=1, loc=5,
                offset_x=0, offset_y=0, debug=False):
    '''
    @summary: 点击图片
    @param  src_path: 原图片路径
            similar: 相似度
    @return: 布尔类型,比对结果
    '''
    count = 0
    while count < timeout:
        std_path = get_resource_path(src_path)
        device.log.debug("Touch Image: {}".format(std_path))
        path = ""
        if hasattr(device, "is_oh"):
            path = device.take_picture("devicetest.png")
            if not path:
                path = device.take_picture("devicetest.jpeg")
        else:
            path = device.take_picture("devicetest.png")
        if std_path is None:
            raise DeviceError(ErrorMessage.Common.Code_0201006.format(src_path))
        if not os.path.exists(path) or not os.path.isfile(path):
            raise DeviceError(ErrorMessage.Common.Code_0201007.format(path))
        count += 1
        max_val, max_loc = match_image_location(path, std_path)
        device.log.debug("max_val: {}, pos: {}".format(max_val, max_loc))
        if max_val >= similar:
            if duration <= 0.1:
                if hasattr(device, "is_oh"):
                    cmd = "uinput -T -c {} {} 10".format(max_loc[0] + offset_x, max_loc[1] + offset_y)
                else:
                    cmd = "input tap {} {}".format(max_loc[0] + offset_x, max_loc[1] + offset_y)
            else:
                if hasattr(device, "is_oh"):
                    cmd = "uinput -T -m {} {} {} {} 50".format(
                        max_loc[0] + offset_x, max_loc[1] + offset_y,
                        max_loc[0] + offset_x, max_loc[1] + offset_y)
                else:
                    cmd = "input swipe {} {} {} {} {}".format(
                        max_loc[0] + offset_x, max_loc[1] + offset_y,
                        max_loc[0] + offset_x, max_loc[1] + offset_y,
                        int(1000 * duration))
            device.execute_shell_command(cmd)
            return True
        time.sleep(1)
    device.log.error("Get image match rate is too lower.")
    return False


def check_image_exist(device, src_path, similar=0.95,
                      timeout=3, loc=5,
                      debug=False):
    '''
    @summary: 点击图片
    @param  src_path: 原图片路径
            similar: 相似度
    @return: 布尔类型,比对结果
    '''
    count = 0
    while count < timeout:
        std_path = get_resource_path(src_path)
        path = ""
        if hasattr(device, "is_oh"):
            path = device.take_picture("devicetest.png")
            if not path:
                path = device.take_picture("devicetest.jpeg")
        else:
            path = device.take_picture("devicetest.png")
        device.log.debug("Touch Image: {}".format(std_path))
        if std_path is None:
            raise DeviceError(ErrorMessage.Common.Code_0201006.format(src_path))
        if not os.path.exists(path) or not os.path.isfile(path):
            raise DeviceError(ErrorMessage.Common.Code_0201007.format(path))
        count += 1
        max_val, max_loc = match_image_location(path, std_path)
        device.log.debug("max_loc: {}".format(max_loc))
        if max_val >= similar:
            return True
        time.sleep(1)
    return False


def compare_image_similarity(device, src_image_path, target_image_path,
                             similar=0.95):
    '''
    @summary: 点击图片
    @param  src_image_path: 原图片路径
    @param  target_image_path: 目标图片路径
            similar: 相似度
    @return: 布尔类型,比对结果
    '''
    count = 0
    target_path = ""
    src_path = get_resource_path(src_image_path)
    if target_image_path is None:
        if hasattr(device, "is_oh"):
            target_path = device.take_picture("devicetest.png")
            if not target_path:
                target_path = device.take_picture("devicetest.jpeg")
        else:
            target_path = device.take_picture("devicetest.png")
    else:
        target_path = get_resource_path(target_image_path)
    if not os.path.exists(src_path) or not os.path.isfile(src_path):
        raise DeviceError(ErrorMessage.Common.Code_0201006.format(src_image_path))
    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        raise DeviceError(ErrorMessage.Common.Code_0201007.format(target_path))
    count += 1
    max_val = _cv.classify_phash(src_path, target_path)
    device.log.debug("max_val: {}".format(max_val))
    if max_val >= similar:
        return True
    else:
        return False


def match_template(ad, src_img, img_path, threshold, boundary):
    """
    @summary: 检测图片是否在当前页面
    @param  src_img: 检测图片
    @param  img_path: 当前页面
            threshold: 阈值
    @return: 布尔类型,比对结果
    """
    ori_image_path = src_img
    test_image_path = img_path
    import cv2
    img1 = cv2.imread(ori_image_path, 0)
    img2 = cv2.imread(test_image_path, 0)
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)
    bf = cv2.BFMatcher()
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    matches = matches[:int(len(matches) / 2)]
    # 获取匹配结果中源对象(目标本身)的关键点和检测对象(待识别的图片)关键点数组，并进行调整
    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
    # 找到上述两组关键点的空间映射矩阵M
    try:
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, threshold)
    except Exception as ex:
        raise ex
    len_mask = len(mask)
    mark_one = np.sum(mask == 1)
    if len_mask != 0:
        max_val = mark_one / len_mask
    else:
        max_val = 0
    ad.log.info("max_val: {}".format(max_val))
    if max_val > boundary:
        return True
    else:
        return False
