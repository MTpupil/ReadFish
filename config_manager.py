#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块 - 处理配置文件的读写和默认配置
"""

import json
import os
from typing import Dict, Any


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file='config.json'):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件名，默认为 config.json
        """
        # 获取AppData目录下的ReadFish文件夹
        appdata_dir = os.path.expanduser('~\\AppData\\Roaming\\ReadFish')
        # 确保目录存在
        os.makedirs(appdata_dir, exist_ok=True)
        self.config_file = os.path.join(appdata_dir, config_file)
        
        # 默认配置
        self.default_config = {
            # 窗口设置
            'window_width': 400,
            'window_height': 300,
            'window_x': 100,
            'window_y': 100,
            'window_opacity': 0.9,  # 窗口透明度 (0.0 - 1.0)
            
            # 显示设置
            'single_line_mode': False,  # 单行显示模式
        'show_resize_handles': False,  # 显示四角调节大小标记
            
            # 文字设置
            'font_family': 'Microsoft YaHei',
            'font_size': 12,
            'font_color': '#000000',  # 文字颜色
            'text_opacity': 1.0,  # 文字透明度 (0.0 - 1.0)
            
            # 其他设置
            'stay_on_top': True,  # 是否保持置顶
            'auto_save_position': True,  # 是否自动保存窗口位置
            
            # 显示控制设置
            'hover_to_show': False,  # 鼠标悬停才显示窗口
            'key_to_show': False,  # 需要按住自定义键才显示窗口
            'custom_key': 'ctrl',  # 自定义按键（ctrl, alt, shift, space等）

            # 翻页按键（新增）
            # 说明：保留默认的方向键和PageUp/PageDown翻页功能，
            # 此处允许用户额外自定义最多两个上一页和两个下一页的按键（字母键），通过设置页面按键录入。
            'page_up_keys': [],    # 例如 ["q", "a"]
            'page_down_keys': []   # 例如 ["w", "s"]
            ,
            # 光标设置（新增）
            'dot_cursor_size': 2,           # 圆点直径（像素）
            'dot_cursor_color': '#000000',  # 圆点颜色（十六进制）
            'dot_cursor_opacity': 1.0       # 圆点透明度 (0.1 - 1.0)
        }
        
        # 当前配置
        self.current_config = self.load_config()
        
    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置
        
        Returns:
            默认配置字典
        """
        return self.default_config.copy()
        
    def load_config(self) -> Dict[str, Any]:
        """从文件加载配置
        
        Returns:
            配置字典
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                # 合并默认配置，确保所有必要的键都存在
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                # 验证配置值的有效性
                validated_config = self.validate_config(merged_config)
                
                return validated_config
            else:
                # 如果配置文件不存在，返回默认配置并创建文件
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except (json.JSONDecodeError, IOError) as e:
            # 加载配置文件失败，使用默认配置
            return self.default_config.copy()
            
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件
        
        Args:
            config: 要保存的配置字典
            
        Returns:
            保存是否成功
        """
        try:
            # 验证配置
            validated_config = self.validate_config(config)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(validated_config, f, indent=4, ensure_ascii=False)
                
            # 更新当前配置
            self.current_config = validated_config.copy()
            
            return True
            
        except (IOError, TypeError) as e:
            # 保存配置文件失败
            return False
            
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            当前配置字典的副本
        """
        return self.current_config.copy()
        
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """更新配置
        
        Args:
            updates: 要更新的配置项字典
            
        Returns:
            更新是否成功
        """
        try:
            # 更新当前配置
            new_config = self.current_config.copy()
            new_config.update(updates)
            
            # 保存更新后的配置
            return self.save_config(new_config)
            
        except Exception as e:
            # 更新配置失败
            return False
            
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证和修正配置值
        
        Args:
            config: 要验证的配置字典
            
        Returns:
            验证后的配置字典
        """
        validated = config.copy()
        
        # 验证窗口大小（完全移除最小限制）
        validated['window_width'] = min(1920, validated.get('window_width', 400))
        validated['window_height'] = min(1080, validated.get('window_height', 300))
        
        # 验证窗口位置（确保不会超出屏幕范围）
        validated['window_x'] = max(0, min(1920, validated.get('window_x', 100)))
        validated['window_y'] = max(0, min(1080, validated.get('window_y', 100)))
        
        # 验证透明度值
        validated['window_opacity'] = max(0.1, min(1.0, validated.get('window_opacity', 0.9)))
        validated['text_opacity'] = max(0.1, min(1.0, validated.get('text_opacity', 1.0)))
        # 验证圆点透明度
        validated['dot_cursor_opacity'] = max(0.1, min(1.0, validated.get('dot_cursor_opacity', 1.0)))
        
        # 验证字体大小
        validated['font_size'] = max(1, min(72, validated.get('font_size', 12)))  # 允许更小的字体大小
        
        # 验证字体类型
        valid_fonts = [
            'Microsoft YaHei', 'SimSun', 'SimHei', 'KaiTi', 'FangSong',
            'Arial', 'Times New Roman', 'Courier New'
        ]
        if validated.get('font_family') not in valid_fonts:
            validated['font_family'] = 'Microsoft YaHei'
            
        # 验证颜色格式
        font_color = validated.get('font_color', '#000000')
        if not self.is_valid_color(font_color):
            validated['font_color'] = '#000000'
        # 验证圆点颜色
        dot_color = validated.get('dot_cursor_color', '#000000')
        if not self.is_valid_color(dot_color):
            validated['dot_cursor_color'] = '#000000'
            
        # 验证布尔值
        validated['stay_on_top'] = bool(validated.get('stay_on_top', True))
        validated['auto_save_position'] = bool(validated.get('auto_save_position', True))
        validated['hover_to_show'] = bool(validated.get('hover_to_show', False))
        validated['key_to_show'] = bool(validated.get('key_to_show', False))
        
        # 验证自定义按键
        valid_keys = ['ctrl', 'alt', 'shift', 'space', 'tab', 'enter', 'esc']
        if validated.get('custom_key') not in valid_keys:
            validated['custom_key'] = 'ctrl'

        # 验证圆点大小（像素范围约束）
        size = int(validated.get('dot_cursor_size', 2))
        validated['dot_cursor_size'] = max(1, min(16, size))

        # 验证翻页按键（最多两个，允许字母键 a-z、数字 0-9，以及特定单键：space、enter、tab；禁止 ctrl/alt/shift/win 等全局/功能键及组合键）
        def normalize_page_keys(keys):
            """规范化并限制翻页按键列表
            - 允许：单字符字母/数字，或特定关键词：space、enter、tab
            - 禁止：ctrl/alt/shift/win/meta/command 以及 f1-f12 等功能键（不在可选列表中）
            - 转为小写，去重，最多保留2个
            """
            allowed_specials = {'space', 'enter', 'tab'}
            forbidden = {'ctrl', 'alt', 'shift', 'win', 'meta', 'command', 'super'}
            result = []
            if isinstance(keys, list):
                for k in keys:
                    if not isinstance(k, str):
                        continue
                    kk = k.strip().lower()
                    # 跳过禁止键和空字符串
                    if not kk or kk in forbidden:
                        continue
                    # 允许的特殊键
                    if kk in allowed_specials:
                        if kk not in result:
                            result.append(kk)
                    # 单字符字母或数字
                    elif len(kk) == 1 and (kk.isalpha() or kk.isdigit()):
                        if kk not in result:
                            result.append(kk)
                    # 其他值忽略
                    if len(result) >= 2:
                        break
            return result[:2]

        validated['page_up_keys'] = normalize_page_keys(validated.get('page_up_keys', []))
        validated['page_down_keys'] = normalize_page_keys(validated.get('page_down_keys', []))

        return validated
        
    def is_valid_color(self, color_str: str) -> bool:
        """验证颜色字符串是否有效
        
        Args:
            color_str: 颜色字符串（如 #FF0000）
            
        Returns:
            是否为有效的颜色格式
        """
        if not isinstance(color_str, str):
            return False
            
        # 检查十六进制颜色格式
        if color_str.startswith('#') and len(color_str) == 7:
            try:
                int(color_str[1:], 16)
                return True
            except ValueError:
                return False
                
        return False
        
    def reset_to_default(self) -> bool:
        """重置为默认配置
        
        Returns:
            重置是否成功
        """
        return self.save_config(self.default_config)
        
    def backup_config(self, backup_file: str = None) -> bool:
        """备份当前配置
        
        Args:
            backup_file: 备份文件路径，如果为None则使用默认名称
            
        Returns:
            备份是否成功
        """
        try:
            if backup_file is None:
                backup_file = self.config_file + '.backup'
                
            if os.path.exists(self.config_file):
                import shutil
                shutil.copy2(self.config_file, backup_file)
                return True
            else:
                # 配置文件不存在，无法备份
                return False
                
        except Exception as e:
            # 备份配置文件失败
            return False
            
    def restore_config(self, backup_file: str) -> bool:
        """从备份恢复配置
        
        Args:
            backup_file: 备份文件路径
            
        Returns:
            恢复是否成功
        """
        try:
            if os.path.exists(backup_file):
                import shutil
                shutil.copy2(backup_file, self.config_file)
                self.current_config = self.load_config()
                return True
            else:
                # 备份文件不存在
                return False
                
        except Exception as e:
            # 恢复配置文件失败
            return False
            
    def get_config_file_path(self) -> str:
        """获取配置文件路径
        
        Returns:
            配置文件的完整路径
        """
        return self.config_file
        
    def config_exists(self) -> bool:
        """检查配置文件是否存在
        
        Returns:
            配置文件是否存在
        """
        return os.path.exists(self.config_file)
