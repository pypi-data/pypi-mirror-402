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
from xdevice import DeviceError
from devicetest.controllers.cv import cv
from devicetest.error import ErrorMessage
from devicetest.utils.file_util import get_resource_path
from devicetest.utils.img_util import ImgUtils


class Image:
    def __init__(self, device):
        self.device = device
        self._sn = device.device_sn
        self.log = device.log

    def check_image(self, src_path, similar=0.95, loc=5, debug=False):
        '''
        @summary: 图片比对
        @param  src_path: 原图片路径
                similar: 相似度
        @return: 布尔类型,比对结果
        '''
        path = self.device.take_picture("test.png")
        temp = src_path
        src_path = get_resource_path(temp)
        self.log.debug("SRC_PATH: %s" % src_path)
        if src_path is None:
            raise DeviceError(ErrorMessage.Common.Code_0201006.format(temp))
        if not os.path.exists(path) or not os.path.isfile(path):
            raise DeviceError(ErrorMessage.Common.Code_0201007.format(path))

        vaule_r, vaule_g = ImgUtils.quick_find(path,
                                               src_path,
                                               similar=similar,
                                               loc=loc,
                                               debug=debug)
        self.log.debug("%s %s" % (str(vaule_r), str(vaule_g)))
        result = vaule_r is not None and vaule_g is not None
        self.log.debug("Recv: %s" % result)
        return result

    def touch_image(self, src_path, similar=0.95, loc=5, debug=False):
        '''
        @summary: 点击图片
        @param  src_path: 原图片路径
                similar: 相似度
        @return: 布尔类型,比对结果
        '''
        path = self.device.take_picture("test.png")
        std_path = get_resource_path(src_path)
        self.log.debug("Touch Image: %s" % std_path)
        if std_path is None:
            raise DeviceError(ErrorMessage.Common.Code_0201006.format(src_path))
        if not os.path.exists(path) or not os.path.isfile(path):
            raise DeviceError(ErrorMessage.Common.Code_0201007.format(path))

        get_r, get_g = ImgUtils.quick_find(path, std_path, similar=similar,
                                           loc=loc,
                                           debug=debug)
        self.log.debug("%s %s" % (str(get_r), str(get_g)))
        if get_g is None:
            self.log.error("Get image location is None, image not "
                           "exits in current page!")
            return
        self.device.uiautomator.click((get_g[0] + get_g[2]) / 2,
                                      (get_g[1] + get_g[3]) / 2)

    def check_widget_exist(self, view_node, std_path, threshold=5.0, boundary=0.45, refresh=True):
        """
        @summary: 检测viewNode是否存在当前手机截图中
        @Param: view_node: viewNode的截图
                std_path: 手机截屏
                threshold: 算法阈值，默认即可
                boundary: 存在边界，一般在0.0~0.5，默认0.45,需要根据不同场景自行适配
        """
        path = self.device.hierarchyviewer.captureViewNode(view_node, "compare", refresh=refresh)
        temp = std_path
        std_path = get_resource_path(temp)
        self.log.info("STD_PATH: {}".format(std_path))
        if std_path is None:
            raise DeviceError(ErrorMessage.Common.Code_0201006.format(temp))
        if not os.path.exists(path) or not os.path.isfile(path):
            raise DeviceError(ErrorMessage.Common.Code_0201007.format(path))
        return cv.match_template(self, path, std_path, threshold=threshold, boundary=boundary)
