import ast
import copy
import inspect
import os
import re
import traceback

from xdevice import FilePermission
from xdevice import platform_logger
from xdevice import Variables
from devicetest.utils.util import is_standard_lib
from devicetest.utils.util import is_third_party_lib

try:
    import astor

    install_astor = True
except Exception:
    install_astor = False

LOG = platform_logger("RecordAction")

METHOD = {
    "touch": ["scroll_target", "target"],
    "drag": ["area", "start", "end"],
    "click": ["target"],
    "double_click": ["target"],
    "long_click": ["target"],
    "switch_component_status": ["component"],
    "get_component_bound": ["component"],
    "get_component_pos": ["component"],
    "slide": ["area", "start", "end"],
    "swipe": ["area"],
    "get_component_property": ["component"],
    "mouse_double_click": ["pos"],
    "mouse_long_click": ["pos"],
    "mouse_click": ["pos"],
    "mouse_scroll": ["pos"],
    "mouse_move_to": ["pos"],
    "mouse_move": ["pos"],
    "mouse_drag": ["start", "end"],
}


def extract_file_lineno(stack_line):
    match = re.search(r'File "(.*?)", line (\d+), in (.+)', stack_line)
    if match:
        file_name = match.group(1).strip()
        line_number = match.group(2).strip()
        method_name = match.group(3).strip()
        code_line = stack_line.split('\n')[-2].strip()
        return file_name, method_name, code_line, line_number
    return None, None, None, None


def get_last_action_code_line():
    stack = traceback.format_stack()
    last_file_name = None
    last_method_name = None
    last_code_line = None
    last_lineno = None
    for line in stack:
        if 'File "' in line:
            file_path = line.split('File "', 1)[1].split('"', 1)[0]
            if not is_standard_lib(file_path) and not is_third_party_lib(file_path):
                file_name, method_name, code_line, lineno = extract_file_lineno(line)
                if file_name and method_name and code_line and lineno:
                    last_file_name = file_name
                    last_method_name = method_name
                    last_code_line = code_line
                    last_lineno = lineno
    return last_file_name, last_method_name, last_code_line, last_lineno


class MethodCallVisitor(ast.NodeVisitor):
    def __init__(self):
        self.method_name = None
        self.arguments = []
        self.kwargs = {}

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            self.method_name = self.get_full_attr(node.func)

        for arg in node.args:
            if install_astor:
                self.arguments.append(astor.to_source(arg))
            else:
                self.arguments.append(ast.unparse(arg))

        for keyword in node.keywords:
            if install_astor:
                self.kwargs.update({keyword.arg: astor.to_source(keyword.value)})
            else:
                self.kwargs.update({keyword.arg: ast.unparse(keyword.value)})

    def get_full_attr(self, node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        parts.reverse()
        return ".".join(parts)


def get_code_from_line():
    data = {}
    file_path, _, _, line_num = get_last_action_code_line()
    line_num = int(line_num)
    code_line = None
    original_code_line = None
    fd = os.open(file_path, os.O_RDONLY, FilePermission.mode_644)
    with os.fdopen(fd, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    tree = None

    if line_num > len(lines) or line_num < 1:
        return data

    next_code_lines = []
    next_original_code_lines = []
    next_number = line_num
    find = False
    while next_number <= line_num + 5:
        next_code_lines.append(lines[next_number - 1].strip())
        next_original_code_lines.append(lines[next_number - 1])
        try:
            code_line = "\n".join(next_code_lines)
            tree = ast.parse(code_line)
            original_code_line = "".join(next_original_code_lines)
            find = True
            break
        except SyntaxError:
            next_number += 1
            continue
    prev_code_lines = []
    prev_original_code_lines = []
    prev_number = line_num
    while not find and line_num - 5 <= prev_number:
        prev_code_lines.insert(0, lines[prev_number - 1].strip())
        prev_original_code_lines.insert(0, lines[prev_number - 1])
        try:
            code_line = "\n".join(prev_code_lines)
            tree = ast.parse(code_line)
            original_code_line = "".join(prev_original_code_lines)
            find = True
            break
        except SyntaxError:
            prev_number -= 1
            continue

    if tree:
        visitor = MethodCallVisitor()
        visitor.visit(tree)
        data = {
            "file_path": file_path,
            "line_num": line_num,
            "code_line": code_line.replace("\n", " "),
            "original_code_line": original_code_line,
            "method_name": visitor.method_name,
            "visitor_arguments": visitor.arguments,
            "visitor_kwargs": visitor.kwargs,
        }
    return data


def get_func_args(func, args, kwargs) -> dict:
    try:
        from hypium.uidriver.interface.uitree import ISelector
        from hypium.uidriver import UiComponent
        signature = inspect.signature(func)
        bound_arguments = signature.bind(*args, **kwargs)
        arguments = {}
        for name, value in bound_arguments.arguments.items():
            if isinstance(value, (ISelector, UiComponent)):
                arguments[name] = "suggest_target"
            else:
                arguments[name] = value
        suggest_dict = get_code_from_line()
        suggest_dict.update({"arguments": arguments})
    except Exception as e:
        LOG.warning("Ignor error. Test cases are not affected.")
        LOG.warning(e)
        if isinstance(e, AttributeError):
            LOG.warning("Ignor: Only python 3.9 or higher can use suggest code")
        suggest_dict = {}
    return suggest_dict


def replace_value(arr: list, old_value: str, new_value: str) -> list:
    return [new_value if x == old_value else x for x in arr]


def convert_backslash_to_slash(path: str) -> str:
    return path.replace('\\', '/')


def generate_suggest_code(suggest_dict: dict, components: list):
    try:
        project_path = Variables.exec_dir
        file_path = suggest_dict.get("file_path")
        line_num = suggest_dict.get("line_num")
        arguments = suggest_dict.get("arguments")
        code_line = suggest_dict.get("code_line")
        original_code_line = suggest_dict.get("original_code_line")
        method_name = suggest_dict.get("method_name")
        visitor_arguments = suggest_dict.get("visitor_arguments")
        visitor_kwargs = suggest_dict.get("visitor_kwargs")

        if not file_path:
            return None

        if not method_name:
            return None

        if not line_num:
            return None

        if not arguments:
            return None

        if not code_line or not original_code_line:
            return None

        if not visitor_arguments:
            return None

        api = method_name.split(".")[-1]

        suggest_target = METHOD.get(api, None)
        if not suggest_target:
            return None
        need_suggest = []
        for i in suggest_target:
            if arguments.get(i, "") == "suggest_target":
                need_suggest.append(i)
        new_visitor_arguments = {}
        keys = list(arguments.keys())
        for key, value in zip(keys[1:], visitor_arguments):
            new_visitor_arguments[key] = value
        new_visitor_arguments.update(visitor_kwargs)
        index = 0
        additional_conditions = {}
        need_to_replace = {}
        for arg, component in zip(need_suggest, components):
            suggest_code = component.get("suggestCode", None)
            if isinstance(suggest_code, list):
                name = "component{}".format(index)
                additional_conditions.update({name: suggest_code})
                index += 1
                need_to_replace.update({arg: name})
            elif isinstance(suggest_code, str):
                need_to_replace.update({arg: suggest_code})
        replace_args = {}
        for key, value in need_to_replace.items():
            code = new_visitor_arguments.get(key, None)
            if code:
                replace_args.update({code: value})
        replace_args_list = copy.copy(visitor_arguments)
        replace_kwargs_dict = copy.copy(visitor_kwargs)
        for key, value in replace_args.items():
            if key in visitor_arguments:
                replace_args_list = replace_value(replace_args_list, key, value)
            elif key in visitor_kwargs.values():
                new_key = next(k for k, v in visitor_kwargs.items() if v == key)
                replace_kwargs_dict.update({new_key: value})
        for key, value in replace_kwargs_dict.items():
            replace_args_list.append(f"{key}={value}")
        all_args_str = ", ".join(replace_args_list)

        new_codes = []
        driver = method_name.replace(f".{api}", "")
        for key, value in additional_conditions.items():
            condition = f"{key} = {driver}.find_all_components({value[0]}, {value[1]})"
            new_codes.append(condition)
        new_code = f"{code_line.split(method_name)[0]}{method_name}({all_args_str})"
        new_codes.append(new_code)
        if project_path in file_path:
            relative_path = convert_backslash_to_slash(file_path.replace(project_path + os.sep, ""))
        else:
            relative_path = convert_backslash_to_slash(file_path)
        step = {
            "file_name": relative_path,
            "line_num": line_num,
            "code": original_code_line,
            "suggestion": "\n".join(new_codes),
        }
        return step
    except Exception as e:
        LOG.warning(e)
        return None
