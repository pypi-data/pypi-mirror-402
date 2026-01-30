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
import os
import ast

try:
    import cv2
except ImportError:
    pass
try:
    import numpy as np
except ImportError:
    pass


def find_image(self, src_img_path, obj_img_path, similar, index):
    '''
    @summary: 查询图片
    @param  src_img_path: 原图片路径
            obj_img_path: 目标图片路径
            similar: 相似度
            index：个数
    @return: 布尔类型,比对结果
    '''
    return True


def match_image(self, src_img, dst_img_path, similar):
    '''
    @summary: 匹配图片
    @param  src_img: 原图片路径
            dst_img_path： 目地图片路径
            similar: 相似度
    @return: 布尔类型,比对结果
    '''
    return True


def get_area_by_point(self, img, x_point, y_point):
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


def preprocess_text(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 1. Sobel算子，x方向求梯度
    sobel = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)
    # 2. 二值化
    ret, binary = cv2.threshold(sobel, 0, 255,
                                cv2.THRESH_OTSU + cv2.THRESH_BINARY)
    # 3. 膨胀和腐蚀操作的核函数
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (8, 5))
    element2 = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 10))
    # 4. 膨胀一次，让轮廓突出
    dilation = cv2.dilate(binary, element2, iterations=1)
    # 5. 腐蚀一次，去掉细节，如表格线等。注意这里去掉的是竖直的线
    erosion = cv2.erode(dilation, element1, iterations=1)
    # 6. 再次膨胀，让轮廓明显一些
    dilation2 = cv2.dilate(erosion, element2, iterations=3)
    cv2.imwrite("dilation2.png", dilation2)
    region = []
    img_height, img_width = dilation2.shape[:2]  # 获取图像的高和宽
    # 1. 查找轮廓
    temp, contours, hierarchy = cv2.findContours(dilation2,
                                                 cv2.RETR_EXTERNAL,
                                                 cv2.CHAIN_APPROX_SIMPLE)
    # 2. 筛选那些面积小的
    for cnt in contours:
        # 计算该轮廓的面积
        area = cv2.contourArea(cnt)
        # 面积小的都筛选掉
        if (area < 1000):
            continue
        # 轮廓近似，作用很小
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        # 找到最小的矩形，该矩形可能有方向
        rect = cv2.minAreaRect(cnt)
        # box是四个坐标点
        box_points = cv2.boxPoints(rect)
        box_points = np.int0(box_points)
        # 计算box的高和宽
        height = abs(box_points[0][1] - box_points[2][1])
        width = abs(box_points[0][0] - box_points[2][0])
        if (height > width * 3 or height < 30 or width > 0.8 * img_width):
            continue
        region.append(box_points)

    return region


def preprocess_icon(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 25))
    gradient = cv2.morphologyEx(blurred, cv2.MORPH_GRADIENT, kernel)
    ret, thresh = cv2.threshold(gradient, 70, 255, cv2.THRESH_BINARY)
    # 2. 二值化
    region = []
    img_height, img_width = img.shape[:2]  # 获取图像的高和宽
    # 1. 查找轮廓
    temp, contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                                 cv2.CHAIN_APPROX_SIMPLE)
    # 2. 筛选那些面积小的
    for cnt in contours:
        # 计算该轮廓的面积
        area = cv2.contourArea(cnt)
        # 面积小的都筛选掉
        if (area < 1000):
            continue
        # 轮廓近似，作用很小
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        # 找到最小的矩形，该矩形可能有方向
        rect = cv2.minAreaRect(cnt)
        # box是四个点的坐标
        box_points = cv2.boxPoints(rect)
        box_points = np.int0(box_points)
        # 计算高和宽
        height = abs(box_points[0][1] - box_points[2][1])
        width = abs(box_points[0][0] - box_points[2][0])
        region.append(box_points)
    return region


def preprocess_grid_layout(img):
    region = []
    # 1.  转化成灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY_INV)[1]
    element1 = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    erosion = cv2.erode(thresh, element1, iterations=1)
    # 1. 查找轮廓
    temp, contours, hierarchy = cv2.findContours(erosion, cv2.RETR_EXTERNAL,
                                                 cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        # 计算该轮廓的面积
        area = cv2.contourArea(cnt)
        # 面积小的都筛选掉
        if (area < 500):
            continue
        # 轮廓近似，作用很小
        epsilon = 0.01 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        # 找到最小的矩形，该矩形可能有方向
        rect = cv2.minAreaRect(cnt)
        # box是四个点的坐标
        box_points = cv2.boxPoints(rect)
        box_points = np.int0(box_points)
        # 计算高和宽
        height = abs(box_points[0][1] - box_points[2][1])
        width = abs(box_points[0][0] - box_points[2][0])
        # 筛选那些太细的矩形，留下扁的
        if (height < 20):
            continue
        cv2.drawContours(img, [box_points], 0, (0, 255, 0), 2)
        region.append(box_points)
    return region


def find_point_contour(region, x_point, y_point):
    for text_box in region:
        xs_point = [i[0] for i in text_box]
        ys_point = [i[1] for i in text_box]
        x_one = int(max(min(xs_point), 0))
        x_two = int(max(xs_point))
        y_one = int(max(min(ys_point), 0))
        y_two = int(max(ys_point))
        if (x_point >= x_one
                and x_point <= x_two
                and y_point >= y_one
                and y_point <= y_two):
            return ((x_one, y_one), (x_two, y_two))
    return 0


def match_image_location(src_img, img_path):
    tpl = cv2.imread(src_img)
    target = cv2.imread(img_path)
    target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)
    tpl_gray = cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(target_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    start_x, start_y = max_loc
    end_x = start_x + target.shape[1]
    end_y = start_y + target.shape[0]
    print("max_val: {}".format(max_val))
    return max_val, (start_x + (end_x - start_x) // 2, start_y + (end_y - start_y) // 2)


def classify_phash(src_img, img_target):
    '''
    感知哈希算法(pHash)
    '''
    image1 = cv2.imread(src_img)
    image2 = cv2.imread(img_target)
    image1 = cv2.resize(image1, (32, 32))
    image2 = cv2.resize(image2, (32, 32))
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    # 将灰度图转为浮点型，再进行dct变换
    dct1 = cv2.dct(np.float32(gray1))
    dct2 = cv2.dct(np.float32(gray2))
    # 取左上角的8*8，这些代表图片的最低频率
    # 这个操作等价于c++中利用opencv实现的掩码操作
    # 在python中进行掩码操作，可以直接这样取出图像矩阵的某一部分
    dct1_roi = dct1[0:8, 0:8]
    dct2_roi = dct2[0:8, 0:8]
    hash1 = get_hash(dct1_roi)
    hash2 = get_hash(dct2_roi)
    distance = hamming_distance(hash1, hash2)
    if hash1 != 0:
        return (len(hash1) - distance) * 1.0 / len(hash1)
    else:
        return 0


# 输入灰度图，返回hash
def get_hash(image):
    avreage = np.mean(image)
    hash = []
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            if image[i, j] > avreage:
                hash.append(1)
            else:
                hash.append(0)
    return hash


# 计算汉明距离
def hamming_distance(hash1, hash2):
    num = 0
    for index, _ in enumerate(hash1):
        if hash1[index] != hash2[index]:
            num += 1
    return num


if __name__ == '__main__':
    # 读取文件
    pass
