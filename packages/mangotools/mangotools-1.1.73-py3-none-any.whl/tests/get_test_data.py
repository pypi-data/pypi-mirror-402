# -*- coding: utf-8 -*-
# @Project: 芒果测试平台
# @Description: 
# @Time   : 2025-11-21 14:17
# @Author : 毛鹏
import inspect
import json
import sys
from typing import List, Dict, Any
from mangotools.data_processor import DataProcessor

# 确保标准输出使用 UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def safe_string_conversion(text):
    """安全处理字符串编码"""
    if text is None:
        return None

    if isinstance(text, bytes):
        try:
            return text.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return text.decode('gbk')
            except:
                return "编码错误"

    # 确保是有效的 Unicode 字符串
    try:
        return str(text)
    except:
        return "字符串转换错误"


def get_function_info(func) -> Dict[str, Any]:
    """获取函数的详细信息"""
    docstring = func.__doc__
    if docstring:
        # 清理文档字符串
        docstring = docstring.strip()

    info = {
        'name': func.__name__,
        'docstring': safe_string_conversion(docstring),
        'signature': str(inspect.signature(func)),
        'qualname': getattr(func, '__qualname__', func.__name__),
    }
    return info


def get_class_methods_info(cls) -> List[Dict[str, Any]]:
    """获取类的所有方法信息"""
    methods_list = []

    for name in dir(cls):
        if name.startswith('__') and name.endswith('__'):
            continue

        obj = getattr(cls, name)

        if callable(obj) and not isinstance(obj, type):
            try:
                func_info = get_function_info(obj)
                methods_list.append(func_info)
            except Exception as e:
                print(f"跳过 {name}: {e}")

    return methods_list


if __name__ == "__main__":
    class_methods = get_class_methods_info(DataProcessor)

    # 确保使用 UTF-8 编码写入文件
    with open('test_data.json', 'w', encoding='utf-8') as f:
        json.dump(class_methods, f, ensure_ascii=False, indent=4)

    # 控制台输出也确保编码正确
    for method in class_methods:
        print(f"\n方法: {method['name']}")
        docstring = method['docstring'] or "无文档"
        print(f"  文档: {docstring}")
        print(f"  签名: {method['signature']}")