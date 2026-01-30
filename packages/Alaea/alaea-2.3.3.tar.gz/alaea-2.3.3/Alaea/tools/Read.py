#!/bin/env python3
# -*- coding: utf-8 -*-
#  日期 : 2025/12/23 14:28
#  作者 : Christmas
#  邮箱 : 273519355@qq.com
#  项目 : Project
#  版本 : python 3
#  摘要 :
"""

"""
import json


def read_json(_filepath):
    """
    读取JSON文件
    :param _filepath: JSON文件路径
    :return: 解析后的数据
    """
    with open(_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


# 列表去重
def unique_list(_lst):
    """
    列表去重，保持顺序
    :param _lst: 输入列表
    :return: 去重后的列表
    """
    _set = set()
    result = []
    for item in _lst:
        if item in _set or len(item.strip())==0:  # 去重 空行 注释行
            continue
        _set.add(item)
        result.append(item)
    
    return result