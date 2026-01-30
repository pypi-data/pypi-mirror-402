import base64
import json
import os
import re
from typing import List

from xdevice import FilePermission


def get_bounds(data: str) -> List:
    """
    get bounds from str: [0,2431][630,2616]
    :param data: str
    :return: bound list
    """
    point_list = re.findall("[0-9]+", data)
    point_list = [int(i) for i in point_list]
    return point_list


def get_bounds_area(data: str) -> int:
    """
    get bounds area from str: [0,2431][630,2616]
    :param data: bound str
    :return: float
    """
    point_list = get_bounds(data)
    area = (point_list[2] - point_list[0]) * (point_list[3] - point_list[1])
    return area


class WidgetAttribute:
    def __init__(self, node: dict):
        self.xpath = ""
        self.node = node
        self.id = node.get("attributes").get("id") if node.get("attributes").get("id") else ""
        self.type = node.get("attributes").get("type") if node.get("attributes").get("type") else ""
        self.text = node.get("attributes").get("text") if node.get("attributes").get("text") else ""
        self.bounds = node.get("attributes").get("bounds") if node.get("attributes").get("bounds") else ""
        # 用于识别属于哪个窗口
        self.bundleName = node.get("attributes").get("bundleName") if node.get("attributes").get("bundleName") else ""
        # 事件属性
        self.clickable = node.get("attributes").get("clickable") if node.get("attributes").get("clickable") else ""
        self.scrollable = node.get("attributes").get("scrollable") if node.get("attributes").get("scrollable") else ""
        self.checkable = node.get("attributes").get("checkable") if node.get("attributes").get("checkable") else ""
        self.checked = node.get("attributes").get("checked") if node.get("attributes").get("checked") else ""
        self.enabled = node.get("attributes").get("enabled") if node.get("attributes").get("enabled") else ""
        self.focused = node.get("attributes").get("focused") if node.get("attributes").get("focused") else ""
        self.longClickable = node.get("attributes").get("longClickable") if node.get("attributes").get(
            "longClickable") else ""

        self.parent_type = ""
        self.child_index = 0
        self.children_type = ""


def get_widget_by_pos(pos: (int, int), layout: str) -> WidgetAttribute:
    smallest_area = float('inf')
    smallest_target = None
    widget_tree = WidgetTree(layout)
    for widget in widget_tree.widgets_list:
        rect = get_bounds(widget.bounds)
        x1, y1, x2, y2 = rect
        # 检查点 (x, y) 是否在矩形内
        if x1 <= pos[0] <= x2 and y1 <= pos[1] <= y2:
            # 计算矩形面积
            area = (x2 - x1) * (y2 - y1)
            # 如果当前矩形面积更小，则更新最小矩形和最小面积
            if area <= smallest_area:
                smallest_area = area
                smallest_target = widget
    return smallest_target


class WidgetTree:

    def __init__(self, layout_path: str):
        self.widgets_list: List[WidgetAttribute] = list()
        self.root = None
        self.layout_path = layout_path
        with open(layout_path, "r", encoding='utf-8') as file:
            self.root = json.load(file)
        self._init_tree()

    def _init_tree(self):
        if len(self.widgets_list) > 0:
            return
        self.widgets_list.clear()
        self._dfs_create_widget(self.root, "", -1, 0, None)

    def _dfs_create_widget(self, node: dict, xpath: str, type_index: int, child_index: int,
                           parent: WidgetAttribute):
        # 初始化控件属性
        widget = WidgetAttribute(node)
        widget.child_index = child_index
        widget.parent_type = "" if len(xpath.split("/")) == 0 else xpath.split("/")[-1]
        if "[" in widget.parent_type:
            widget.parent_type = widget.parent_type.split("[")[0]

        if widget.type == "" or not parent:
            widget.xpath = "/"
        elif xpath == "/":
            window_name = "{}".format(widget.type) if type_index == -1 \
                else "{}[{}]".format(widget.type, type_index)
            widget.xpath = "{}{}".format(xpath, window_name)
        else:
            widget.xpath = "{}/{}".format(xpath, widget.type) if type_index == -1 \
                else "{}/{}[{}]".format(xpath, widget.type, type_index)

        # 回溯前面的控件看是否唯一，以及其父节点的孩子节点信息
        for pre_widget in reversed(self.widgets_list):

            if pre_widget.xpath == xpath:
                pre_widget.children_type = "{}/{}".format(pre_widget.children_type, widget.type)
            # 获取到孩子节点第几层的信息
            level = 2
            for i in range(level):
                child_level = i + 1
                grand_parent_xpath = "/".join(xpath.split("/")[:-child_level])
                if pre_widget.xpath == grand_parent_xpath:
                    pre_widget.children_type = "{}/{}{}".format(pre_widget.children_type, child_level, widget.type)

        self.widgets_list.append(widget)

        # 先获取孩子节点下同类型的节点的索引信息
        child_type_index = dict()
        for _, child in enumerate(node.get("children", list())):
            key = child.get("attributes").get("type")
            if key in child_type_index.keys():
                child_type_index[key] += 1
            else:
                child_type_index.update({key: 1})

        type_index_dict = child_type_index.copy()
        for _, child in enumerate(node.get("children", list())):
            # 适配新的xpath的计算方式
            key = child.get("attributes").get("type")
            # 该类型控件只有一个，因此xpath不需要索引
            if type_index_dict.get(key) == 1:
                current_type_index = -1
            else:
                child_type_index.update({key: child_type_index.get(key) - 1})
                current_type_index = (type_index_dict.get(key) - 1) - child_type_index.get(key)

            self._dfs_create_widget(child, widget.xpath, current_type_index, child_index, widget)

    def get_widget_index(self, xpath: str):
        """
        根据xpath返回控件属性索引
        """
        for index, widget in enumerate(self.widgets_list):
            if widget.xpath == xpath:
                return index
        return None

    def get_widget(self, xpath: str) -> WidgetAttribute:
        """
        根据xpath返回控件属性
        """
        index = self.get_widget_index(xpath)
        if index and self.widgets_list:
            return self.widgets_list[index]
        return None


def get_base64(path: str) -> str:
    # 读取图像文件并转换为二进制数据
    image_fd = os.open(path, os.O_RDONLY, FilePermission.mode_755)
    with os.fdopen(image_fd, mode="rb") as file:
        img_data = file.read()
    # 对图像数据进行Base64编码
    encoded_data = base64.b64encode(img_data)
    # 将编码后的数据转换为字符串
    encoded_string = encoded_data.decode('utf-8')
    return encoded_string


def get_layout(path):
    layout_fd = os.open(path, os.O_RDONLY, FilePermission.mode_755)
    with os.fdopen(layout_fd, mode="r", encoding="utf-8") as file:
        layout_data = file.read()
    return layout_data
