#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReadFish 资源路径处理模块
用于处理PyInstaller打包后的资源文件路径问题
"""

import os
import sys
from pathlib import Path

def get_resource_path(relative_path):
    """
    获取资源文件的绝对路径
    
    在PyInstaller打包环境中，资源文件会被解压到临时目录
    需要使用sys._MEIPASS来获取正确的路径
    
    Args:
        relative_path (str): 相对路径，如 'logo.ico'
    
    Returns:
        str: 资源文件的绝对路径
    """
    try:
        # PyInstaller打包后的临时目录
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境中使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def find_icon_file(icon_name='logo'):
    """
    查找图标文件，按优先级返回第一个找到的文件路径
    
    优先级：.ico > .png > .svg
    
    Args:
        icon_name (str): 图标文件名（不含扩展名），默认为'logo'
    
    Returns:
        str or None: 找到的图标文件路径，如果都不存在则返回None
    """
    # 按优先级定义扩展名
    extensions = ['.ico', '.png', '.svg']
    
    for ext in extensions:
        icon_file = f"{icon_name}{ext}"
        icon_path = get_resource_path(icon_file)
        
        if os.path.exists(icon_path):
            return icon_path
    
    # 如果都不存在，返回None
    return None

def get_icon_paths():
    """
    获取所有可能的图标文件路径
    
    Returns:
        dict: 包含各种格式图标路径的字典
    """
    return {
        'ico': get_resource_path('logo.ico'),
        'png': get_resource_path('logo.png'),
        'svg': get_resource_path('logo.svg')
    }

def debug_resource_paths():
    """
    调试资源路径信息
    """
    print("=" * 50)
    print("[资源路径调试]")
    print("=" * 50)
    
    # 显示环境信息
    if hasattr(sys, '_MEIPASS'):
        print(f"运行环境: PyInstaller打包环境")
        print(f"临时目录: {sys._MEIPASS}")
    else:
        print(f"运行环境: Python开发环境")
        print(f"脚本目录: {os.path.dirname(os.path.abspath(__file__))}")
    
    print(f"当前工作目录: {os.getcwd()}")
    
    # 检查图标文件
    print("\n[图标文件检查]")
    icon_paths = get_icon_paths()
    
    for format_name, path in icon_paths.items():
        exists = os.path.exists(path)
        if exists:
            size = os.path.getsize(path)
            print(f"  ✓ {format_name.upper()}: {path} ({size:,} bytes)")
        else:
            print(f"  ✗ {format_name.upper()}: {path} (不存在)")
    
    # 显示推荐的图标路径
    recommended_path = find_icon_file()
    if recommended_path:
        print(f"\n[推荐使用]: {recommended_path}")
    else:
        print(f"\n[警告]: 未找到任何图标文件")
    
    return icon_paths

if __name__ == '__main__':
    debug_resource_paths()