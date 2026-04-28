#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置窗口模块 - 用于设置阅读器的各种参数
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSlider, QSpinBox, QPushButton, QColorDialog,
    QComboBox, QGroupBox, QMessageBox, QFrame, QCheckBox, QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


class ConfigWindow(QDialog):
    """配置窗口类"""
    
    # 定义信号
    config_changed = pyqtSignal()  # 配置改变信号
    
    # Qt 键值到显示名的映射（用于 UI 显示）
    KEY_VALUE_TO_DISPLAY_NAME = {
        Qt.Key_Space: 'Space',
        Qt.Key_Return: 'Enter',
        Qt.Key_Enter: 'Enter',
        Qt.Key_Tab: 'Tab',
        Qt.Key_Comma: ',',
        Qt.Key_Period: '.',
        Qt.Key_Semicolon: ';',
        Qt.Key_Colon: ':',
        Qt.Key_Question: '?',
        Qt.Key_Exclam: '!',
        Qt.Key_QuoteDbl: '"',
        Qt.Key_Apostrophe: "'",
        Qt.Key_ParenLeft: '(',
        Qt.Key_ParenRight: ')',
        Qt.Key_BracketLeft: '[',
        Qt.Key_BracketRight: ']',
        Qt.Key_BraceLeft: '{',
        Qt.Key_BraceRight: '}',
        Qt.Key_Minus: '-',
        Qt.Key_Underscore: '_',
        Qt.Key_Plus: '+',
        Qt.Key_Equal: '=',
        Qt.Key_Asterisk: '*',
        Qt.Key_Slash: '/',
        Qt.Key_Backslash: '\\',
        Qt.Key_Bar: '|',
        Qt.Key_Ampersand: '&',
        Qt.Key_Percent: '%',
        Qt.Key_Dollar: '$',
        Qt.Key_NumberSign: '#',
        Qt.Key_At: '@',
        Qt.Key_AsciiCircum: '^',
        Qt.Key_QuoteLeft: '`',
        Qt.Key_AsciiTilde: '~',
    }
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = self.config_manager.get_config().copy()  # 获取配置副本
        
        self.init_ui()
        self.load_current_config()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('ReadFish - 设置')
        self.setFixedSize(500, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 设置窗口图标
        import os
        from PyQt5.QtGui import QIcon
        # 优先使用ICO格式，因为Windows exe需要ICO格式图标
        if os.path.exists('logo.ico'):
            self.setWindowIcon(QIcon('logo.ico'))
        elif os.path.exists('logo.png'):
            self.setWindowIcon(QIcon('logo.png'))
        elif os.path.exists('logo.svg'):
            self.setWindowIcon(QIcon('logo.svg'))
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 添加标签页
        self.create_window_tab()
        self.create_text_tab()
        self.create_cursor_tab()
        self.create_navigation_tab()
        self.create_auto_read_tab()
        self.create_shortcuts_tab()
        
        # 按钮区域
        button_layout = self.create_button_layout()
        main_layout.addLayout(button_layout)
    
    def create_window_tab(self):
        """创建窗口设置标签页"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 窗口设置组
        window_group = self.create_window_group()
        layout.addWidget(window_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, '窗口')
    
    def create_text_tab(self):
        """创建文字设置标签页"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 文字设置组
        text_group = self.create_text_group()
        layout.addWidget(text_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, '文字')
    
    def create_cursor_tab(self):
        """创建光标设置标签页"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 光标设置组
        cursor_group = self.create_cursor_group()
        layout.addWidget(cursor_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, '光标')
    
    def create_navigation_tab(self):
        """创建翻页按键设置标签页"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 翻页按键设置组
        nav_group = self.create_navigation_key_group()
        layout.addWidget(nav_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, '翻页')
    
    def create_auto_read_tab(self):
        """创建自动阅读设置标签页"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 自动阅读设置组
        auto_read_group = self.create_auto_read_group()
        layout.addWidget(auto_read_group)
        layout.addStretch()
        
        self.tab_widget.addTab(widget, '自动阅读')
    
    def create_shortcuts_tab(self):
        """创建快捷键说明标签页"""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 快捷键说明
        shortcuts_group = self.create_shortcuts_group()
        layout.addWidget(shortcuts_group)
        
        self.tab_widget.addTab(widget, '快捷键')
    
    def create_window_group(self):
        """创建窗口设置组"""
        group = QGroupBox('窗口设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 窗口宽度/高度（只读显示）- 同一行
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(35, 1920)
        self.width_spinbox.setSuffix(' px')
        self.width_spinbox.setToolTip('当前窗口宽度（只读，请使用四角标记调节大小）')
        self.width_spinbox.setReadOnly(True)
        self.width_spinbox.setEnabled(False)

        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(35, 1080)
        self.height_spinbox.setSuffix(' px')
        self.height_spinbox.setToolTip('当前窗口高度（只读，请使用四角标记调节大小）')
        self.height_spinbox.setReadOnly(True)
        self.height_spinbox.setEnabled(False)

        size_row_widget = QFrame()
        size_row_layout = QHBoxLayout(size_row_widget)
        size_row_layout.setContentsMargins(0, 0, 0, 0)
        size_row_layout.addWidget(QLabel('宽度:'))
        size_row_layout.addWidget(self.width_spinbox)
        size_row_layout.addSpacing(12)
        size_row_layout.addWidget(QLabel('高度:'))
        size_row_layout.addWidget(self.height_spinbox)
        size_row_layout.addStretch()
        layout.addRow('窗口尺寸:', size_row_widget)
        
        # 单行模式
        self.single_line_checkbox = QCheckBox()
        self.single_line_checkbox.setText('单行模式')
        self.single_line_checkbox.setToolTip('启用后，阅读窗口只显示一行文本，便于逐行阅读')
        self.single_line_checkbox.stateChanged.connect(self.on_config_changed)
        layout.addRow('显示模式:', self.single_line_checkbox)
        
        # 显示调节大小标记
        self.show_resize_handles_checkbox = QCheckBox()
        self.show_resize_handles_checkbox.setText('四角标记')
        self.show_resize_handles_checkbox.setToolTip('启用后，在窗口四角显示小标记，可拖拽调节窗口大小')
        self.show_resize_handles_checkbox.stateChanged.connect(self.on_config_changed)
        layout.addRow('窗口调节:', self.show_resize_handles_checkbox)
        
        # 鼠标悬停显示
        self.hover_to_show_checkbox = QCheckBox()
        self.hover_to_show_checkbox.setText('自动隐藏')
        self.hover_to_show_checkbox.setToolTip('启用后，只有鼠标移动到窗口位置时才显示窗口内容')
        self.hover_to_show_checkbox.stateChanged.connect(self.on_config_changed)
        layout.addRow('自动隐藏:', self.hover_to_show_checkbox)
        
        # 按键显示控制（与自定义按键下拉框同一行，且仅在开启时可操作）
        self.key_to_show_checkbox = QCheckBox()
        self.key_to_show_checkbox.setText('需要按键')
        self.key_to_show_checkbox.setToolTip('启用后，需要按住指定按键并且鼠标悬停才显示窗口')
        self.key_to_show_checkbox.stateChanged.connect(self.on_config_changed)

        self.custom_key_combo = QComboBox()
        self.custom_key_combo.addItems(['ctrl', 'alt', 'shift'])
        self.custom_key_combo.setToolTip('选择需要按住的自定义按键')
        self.custom_key_combo.currentTextChanged.connect(self.on_config_changed)

        key_row_widget = QFrame()
        key_row_layout = QHBoxLayout(key_row_widget)
        key_row_layout.setContentsMargins(0, 0, 0, 0)
        key_row_layout.addWidget(self.key_to_show_checkbox)
        key_row_layout.addSpacing(12)
        key_row_layout.addWidget(self.custom_key_combo)
        key_row_layout.addStretch()
        layout.addRow('按键隐藏:', key_row_widget)
        
        # 移除窗口透明度设置，因为已固定为极低透明度以避免鼠标穿透
        
        return group
        
    def create_text_group(self):
        """创建文字设置组"""
        group = QGroupBox('文字设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 字体大小与类型（同一行）
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(1, 72)
        self.font_size_spinbox.setSuffix(' pt')
        self.font_size_spinbox.valueChanged.connect(self.on_config_changed)

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            'Microsoft YaHei', 'SimSun', 'SimHei', 'KaiTi', 'FangSong',
            'Arial', 'Times New Roman', 'Courier New'
        ])
        self.font_family_combo.currentTextChanged.connect(self.on_config_changed)

        font_row_widget = QFrame()
        font_row_layout = QHBoxLayout(font_row_widget)
        font_row_layout.setContentsMargins(0, 0, 0, 0)
        font_row_layout.addWidget(QLabel('大小:'))
        font_row_layout.addWidget(self.font_size_spinbox)
        font_row_layout.addSpacing(12)
        font_row_layout.addWidget(QLabel('类型:'))
        font_row_layout.addWidget(self.font_family_combo)
        font_row_layout.addStretch()
        layout.addRow('字体:', font_row_widget)
        
        # 文字颜色
        color_layout = QHBoxLayout()
        self.color_button = QPushButton()
        self.color_button.setFixedSize(60, 30)
        self.color_button.clicked.connect(self.choose_color)
        
        self.color_label = QLabel('#000000')
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_label)
        color_layout.addStretch()
        layout.addRow('文字颜色:', color_layout)
        
        # 文字透明度
        text_opacity_layout = QHBoxLayout()
        self.text_opacity_slider = QSlider(Qt.Horizontal)
        self.text_opacity_slider.setRange(10, 100)  # 10% 到 100%
        self.text_opacity_slider.valueChanged.connect(self.on_text_opacity_changed)
        
        self.text_opacity_label = QLabel('100%')
        self.text_opacity_label.setMinimumWidth(40)
        
        text_opacity_layout.addWidget(self.text_opacity_slider)
        text_opacity_layout.addWidget(self.text_opacity_label)
        layout.addRow('文字透明度:', text_opacity_layout)
        
        return group

    def create_cursor_group(self):
        group = QGroupBox('光标设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)

        # 圆点大小（滑块，1-16px）
        dot_size_row = QFrame()
        dot_size_layout = QHBoxLayout(dot_size_row)
        dot_size_layout.setContentsMargins(0, 0, 0, 0)
        self.dot_size_slider = QSlider(Qt.Horizontal)
        self.dot_size_slider.setRange(1, 16)
        self.dot_size_slider.valueChanged.connect(self.on_dot_size_changed)
        self.dot_size_value_label = QLabel('2 px')
        self.dot_size_value_label.setMinimumWidth(40)
        dot_size_layout.addWidget(self.dot_size_slider)
        dot_size_layout.addWidget(self.dot_size_value_label)
        layout.addRow('圆点大小:', dot_size_row)

        # 圆点颜色
        dot_color_layout = QHBoxLayout()
        self.dot_color_button = QPushButton()
        self.dot_color_button.setFixedSize(60, 30)
        self.dot_color_button.clicked.connect(self.choose_dot_color)
        self.dot_color_label = QLabel('#000000')
        dot_color_layout.addWidget(self.dot_color_button)
        dot_color_layout.addWidget(self.dot_color_label)
        dot_color_layout.addStretch()
        layout.addRow('圆点颜色:', dot_color_layout)

        # 圆点透明度
        dot_opacity_layout = QHBoxLayout()
        self.dot_opacity_slider = QSlider(Qt.Horizontal)
        self.dot_opacity_slider.setRange(10, 100)
        self.dot_opacity_slider.valueChanged.connect(self.on_dot_opacity_changed)
        self.dot_opacity_label = QLabel('100%')
        self.dot_opacity_label.setMinimumWidth(40)
        dot_opacity_layout.addWidget(self.dot_opacity_slider)
        dot_opacity_layout.addWidget(self.dot_opacity_label)
        layout.addRow('圆点透明度:', dot_opacity_layout)

        return group

    def create_navigation_key_group(self):
        """创建翻页按键设置组
        - 允许用户通过"按键录入"的方式添加最多五个上一页和五个下一页的按键
        - 保留默认方向键和PageUp/PageDown翻页功能
        - 每个按键都有单独的删除按钮
        - 支持字母、数字、符号键
        """
        group = QGroupBox('翻页按键设置')
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(8)

        # ===== 上一页按键 =====
        up_label = QLabel('上一页按键:')
        up_label.setStyleSheet('font-weight: bold;')
        group_layout.addWidget(up_label)

        # 上一页按键容器
        self.page_up_keys_container = QFrame()
        self.page_up_keys_layout = QHBoxLayout(self.page_up_keys_container)
        self.page_up_keys_layout.setContentsMargins(0, 0, 0, 0)
        self.page_up_keys_layout.setSpacing(6)
        self.page_up_keys_container.setStyleSheet('background-color: #f8f9fa; border-radius: 4px; padding: 6px;')
        group_layout.addWidget(self.page_up_keys_container)

        # 上一页操作按钮
        up_btn_layout = QHBoxLayout()
        self.page_up_record_btn = QPushButton('+ 添加按键')
        self.page_up_record_btn.setToolTip('点击后按下要添加的按键（支持字母、数字、符号键）')
        self.page_up_record_btn.setFixedSize(90, 28)
        self.page_up_record_btn.clicked.connect(self.start_record_up_keys)
        up_btn_layout.addWidget(self.page_up_record_btn)
        up_btn_layout.addStretch()
        up_count_label = QLabel('最多可添加 5 个')
        up_count_label.setStyleSheet('color: #7f8c8d; font-size: 10pt;')
        up_btn_layout.addWidget(up_count_label)
        group_layout.addLayout(up_btn_layout)

        # ===== 下一页按键 =====
        down_label = QLabel('下一页按键:')
        down_label.setStyleSheet('font-weight: bold;')
        group_layout.addWidget(down_label)

        # 下一页按键容器
        self.page_down_keys_container = QFrame()
        self.page_down_keys_layout = QHBoxLayout(self.page_down_keys_container)
        self.page_down_keys_layout.setContentsMargins(0, 0, 0, 0)
        self.page_down_keys_layout.setSpacing(6)
        self.page_down_keys_container.setStyleSheet('background-color: #f8f9fa; border-radius: 4px; padding: 6px;')
        group_layout.addWidget(self.page_down_keys_container)

        # 下一页操作按钮
        down_btn_layout = QHBoxLayout()
        self.page_down_record_btn = QPushButton('+ 添加按键')
        self.page_down_record_btn.setToolTip('点击后按下要添加的按键（支持字母、数字、符号键）')
        self.page_down_record_btn.setFixedSize(90, 28)
        self.page_down_record_btn.clicked.connect(self.start_record_down_keys)
        down_btn_layout.addWidget(self.page_down_record_btn)
        down_btn_layout.addStretch()
        down_count_label = QLabel('最多可添加 5 个')
        down_count_label.setStyleSheet('color: #7f8c8d; font-size: 10pt;')
        down_btn_layout.addWidget(down_count_label)
        group_layout.addLayout(down_btn_layout)

        # 提示信息
        tip = QLabel('提示：默认方向键和 PageUp/PageDown 始终可用。添加自定义按键可配合使用。')
        tip.setStyleSheet('color: #7f8c8d; font-size: 10pt;')
        group_layout.addWidget(tip)

        # 录入状态标志
        self.recording_up = False
        self.recording_down = False

        return group

    def refresh_key_tags(self):
        """刷新按键标签显示（上一页和下一页）"""
        self._refresh_key_tags_for('page_up_keys', self.page_up_keys_layout, self.page_up_record_btn)
        self._refresh_key_tags_for('page_down_keys', self.page_down_keys_layout, self.page_down_record_btn)

    def _get_key_display_name(self, key_token):
        """
        将键值 token 转换为显示名
        
        Args:
            key_token: 键值 token（可能是 'space'、'enter'、'tab' 或字符串形式的键值数字）
            
        Returns:
            友好的显示名称
        """
        if key_token == 'space':
            return 'Space'
        elif key_token == 'enter':
            return 'Enter'
        elif key_token == 'tab':
            return 'Tab'
        
        # 尝试解析为数字键值
        try:
            key_value = int(key_token)
            # 检查是否在预定义映射中
            if key_value in self.KEY_VALUE_TO_DISPLAY_NAME:
                return self.KEY_VALUE_TO_DISPLAY_NAME[key_value]
            
            # 检查是否是字母或数字（范围 0-9, A-Z）
            if key_value >= 48 and key_value <= 57:  # 0-9
                return chr(key_value)
            if key_value >= 65 and key_value <= 90:  # A-Z
                return chr(key_value).lower()
            
            # 其他情况直接返回键值数字
            return f'Key({key_value})'
        except (ValueError, TypeError):
            return key_token
            
    def _refresh_key_tags_for(self, config_key, layout, record_btn):
        """为指定方向刷新按键标签"""
        # 清除旧标签
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        keys = self.config.get(config_key, [])
        max_keys = 5

        # 更新按钮状态
        if len(keys) >= max_keys:
            record_btn.setEnabled(False)
            record_btn.setText('已达上限')
        else:
            record_btn.setEnabled(True)
            record_btn.setText('+ 添加按键')

        if not keys:
            empty_label = QLabel('未设置')
            empty_label.setStyleSheet('color: #999; font-style: italic;')
            layout.addWidget(empty_label)
            return

        # 为每个按键创建标签+删除按钮
        for idx, key_token in enumerate(keys):
            row_frame = QFrame()
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)

            # 获取显示名称
            display_name = self._get_key_display_name(key_token)
            
            # 按键标签
            key_label = QLabel(f'  {display_name}  ')
            key_label.setStyleSheet(
                'background-color: #e8f4fd; color: #2c3e50; border: 1px solid #b0d4f1; '
                'border-radius: 3px; font-family: monospace; font-size: 11pt;'
            )
            row_layout.addWidget(key_label)

            # 删除按钮
            del_btn = QPushButton('×')
            del_btn.setFixedSize(20, 20)
            del_btn.setStyleSheet(
                'QPushButton { background-color: #e74c3c; color: white; border: none; '
                'border-radius: 10px; font-size: 12pt; font-weight: bold; }'
                'QPushButton:hover { background-color: #c0392b; }'
            )
            del_btn.setToolTip(f'删除按键 "{display_name}"')
            del_btn.clicked.connect(lambda checked, k=config_key, t=key_token: self.remove_key(k, t))
            row_layout.addWidget(del_btn)
            row_layout.addStretch()

            layout.addWidget(row_frame)

    def create_auto_read_group(self):
        """创建自动阅读设置组"""
        group = QGroupBox('自动阅读设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)

        # 速度设置
        speed_row = QFrame()
        speed_layout = QHBoxLayout(speed_row)
        speed_layout.setContentsMargins(0, 0, 0, 0)
        
        self.auto_read_speed_slider = QSlider(Qt.Horizontal)
        # 为了支持0.5的步长，我们使用整数滑块（0-19，对应0.5-10秒）
        self.auto_read_speed_slider.setRange(0, 19)
        self.auto_read_speed_slider.valueChanged.connect(self.on_auto_read_speed_changed)
        
        self.auto_read_speed_label = QLabel('2.0 秒/页')
        self.auto_read_speed_label.setMinimumWidth(80)
        
        speed_layout.addWidget(self.auto_read_speed_slider)
        speed_layout.addWidget(self.auto_read_speed_label)
        layout.addRow('翻页速度:', speed_row)
        
        # 去除空行设置
        self.remove_empty_lines_checkbox = QCheckBox()
        self.remove_empty_lines_checkbox.setText('去除完全空行')
        self.remove_empty_lines_checkbox.setToolTip('启用后，阅读时会自动过滤掉完全空白的行')
        self.remove_empty_lines_checkbox.stateChanged.connect(self.on_config_changed)
        layout.addRow('显示设置:', self.remove_empty_lines_checkbox)

        return group

    def create_shortcuts_group(self):
        """创建快捷键说明组"""
        group = QGroupBox('快捷键说明')
        layout = QVBoxLayout(group)
        layout.setSpacing(10)

        # 快捷键文本
        shortcuts_text = """
阅读器快捷键：
  Ctrl + E    显示章节进度
  Ctrl + F    打开搜索窗口
  Ctrl + I    打开设置窗口
  Ctrl + A    开始/关闭自动阅读
  Ctrl + Q    退出应用
  Ctrl + `    临时固定显示阅读器
  ESC         关闭阅读器窗口
  ↑ / PageUp  上一页
  ↓ / PageDown 下一页
  ←（左键）   减慢自动阅读速度（仅在自动阅读时有效）
  →（右键）   加快自动阅读速度（仅在自动阅读时有效）
  空格        暂停/恢复自动阅读（仅在自动阅读时有效）

说明：
- 所有快捷键需要阅读器有焦点才能生效
- 自定义翻页按键可在上方配置中设置
        """

        self.shortcuts_text = QTextEdit()
        self.shortcuts_text.setReadOnly(True)
        self.shortcuts_text.setPlainText(shortcuts_text.strip())
        self.shortcuts_text.setStyleSheet(
            "QTextEdit {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: #f8f9fa;"
            "    color: #495057;"
            "    font-family: 'Consolas', 'Courier New', monospace;"
            "    font-size: 9pt;"
            "    padding: 10px;"
            "}"
        )

        layout.addWidget(self.shortcuts_text)

        return group
        
    def create_button_layout(self):
        """创建按钮布局"""
        layout = QHBoxLayout()
        
        # 重置按钮
        self.reset_button = QPushButton('重置默认')
        self.reset_button.clicked.connect(self.reset_to_default)
        
        # 确定按钮（关闭窗口）
        self.ok_button = QPushButton('确定')
        self.ok_button.clicked.connect(self.accept_config)
        
        # 取消按钮
        self.cancel_button = QPushButton('取消')
        self.cancel_button.clicked.connect(self.reject)
        
        # 设置按钮样式
        button_style = """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """
        
        for button in [self.reset_button, self.ok_button, self.cancel_button]:
            button.setStyleSheet(button_style)
            
        # 设置确定按钮的特殊样式
        primary_style = """
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #3498db;
                border-radius: 4px;
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        
        self.ok_button.setStyleSheet(primary_style)
        
        layout.addWidget(self.reset_button)
        layout.addStretch()
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)
        
        return layout
        
    def load_current_config(self):
        """加载当前配置到界面"""
        # 临时断开信号连接，避免在设置值时触发配置改变
        # 注意：宽高输入框现在是只读的，不需要断开信号
        self.single_line_checkbox.stateChanged.disconnect()
        self.show_resize_handles_checkbox.stateChanged.disconnect()
        self.hover_to_show_checkbox.stateChanged.disconnect()
        self.key_to_show_checkbox.stateChanged.disconnect()
        self.custom_key_combo.currentTextChanged.disconnect()
        self.font_size_spinbox.valueChanged.disconnect()
        self.font_family_combo.currentTextChanged.disconnect()
        self.text_opacity_slider.valueChanged.disconnect()
        # 新增：光标组控件断开信号
        try:
            self.dot_size_slider.valueChanged.disconnect()
            self.dot_opacity_slider.valueChanged.disconnect()
            self.auto_read_speed_slider.valueChanged.disconnect()
            self.remove_empty_lines_checkbox.stateChanged.disconnect()
        except Exception:
            pass
        
        try:
            # 窗口设置
            self.width_spinbox.setValue(self.config.get('window_width', 400))
            self.height_spinbox.setValue(self.config.get('window_height', 300))
            
            # 单行模式设置
            self.single_line_checkbox.setChecked(self.config.get('single_line_mode', False))
            
            # 调节大小标记设置
            self.show_resize_handles_checkbox.setChecked(self.config.get('show_resize_handles', False))
            
            # 显示控制设置
            self.hover_to_show_checkbox.setChecked(self.config.get('hover_to_show', False))
            self.key_to_show_checkbox.setChecked(self.config.get('key_to_show', False))
            
            # 自定义按键设置
            custom_key = self.config.get('custom_key', 'ctrl')
            key_index = self.custom_key_combo.findText(custom_key)
            if key_index >= 0:
                self.custom_key_combo.setCurrentIndex(key_index)
            
            # 移除窗口透明度加载，因为已固定为极低透明度
            
            # 文字设置
            self.font_size_spinbox.setValue(self.config.get('font_size', 12))
            
            font_family = self.config.get('font_family', 'Microsoft YaHei')
            index = self.font_family_combo.findText(font_family)
            if index >= 0:
                self.font_family_combo.setCurrentIndex(index)
                
            # 文字颜色
            font_color = self.config.get('font_color', '#000000')
            self.update_color_button(font_color)
            self.color_label.setText(font_color)
            
            # 文字透明度
            text_opacity = int(self.config.get('text_opacity', 1.0) * 100)
            self.text_opacity_slider.setValue(text_opacity)
            self.text_opacity_label.setText(f'{text_opacity}%')

            # 自定义按键使能状态由“按键隐藏”控制
            self.custom_key_combo.setEnabled(self.key_to_show_checkbox.isChecked())

            # 光标设置
            self.dot_size_slider.setValue(self.config.get('dot_cursor_size', 2))
            self.dot_size_value_label.setText(f"{self.config.get('dot_cursor_size', 2)} px")
            dot_color = self.config.get('dot_cursor_color', '#000000')
            self.update_dot_color_button(dot_color)
            self.dot_color_label.setText(dot_color)
            dot_opacity = int(self.config.get('dot_cursor_opacity', 1.0) * 100)
            self.dot_opacity_slider.setValue(dot_opacity)
            self.dot_opacity_label.setText(f'{dot_opacity}%')

            # 翻页按键设置显示
            self.refresh_key_tags()

            # 自动阅读速度设置
            auto_read_speed = self.config.get('auto_read_speed', 2.0)
            # 转换为滑块值（0.5-10秒 -> 0-19）
            slider_value = int((auto_read_speed - 0.5) / 0.5)
            self.auto_read_speed_slider.setValue(slider_value)
            self.auto_read_speed_label.setText(f'{auto_read_speed:.1f} 秒/页')
            
            # 去除空行设置
            self.remove_empty_lines_checkbox.setChecked(self.config.get('remove_empty_lines', False))
            
        finally:
            # 重新连接信号（宽高输入框现在是只读的，不需要重连信号）
            self.single_line_checkbox.stateChanged.connect(self.on_config_changed)
            self.show_resize_handles_checkbox.stateChanged.connect(self.on_config_changed)
            self.hover_to_show_checkbox.stateChanged.connect(self.on_config_changed)
            self.key_to_show_checkbox.stateChanged.connect(self.on_config_changed)
            self.custom_key_combo.currentTextChanged.connect(self.on_config_changed)
            self.font_size_spinbox.valueChanged.connect(self.on_config_changed)
            self.font_family_combo.currentTextChanged.connect(self.on_config_changed)
            self.text_opacity_slider.valueChanged.connect(self.on_text_opacity_changed)
            # 新增：光标组控件重连信号
            if hasattr(self, 'dot_size_slider'):
                self.dot_size_slider.valueChanged.connect(self.on_dot_size_changed)
            if hasattr(self, 'dot_opacity_slider'):
                self.dot_opacity_slider.valueChanged.connect(self.on_dot_opacity_changed)
            # 新增：自动阅读速度滑块重连信号
            if hasattr(self, 'auto_read_speed_slider'):
                self.auto_read_speed_slider.valueChanged.connect(self.on_auto_read_speed_changed)
            # 新增：去除空行复选框重连信号
            if hasattr(self, 'remove_empty_lines_checkbox'):
                self.remove_empty_lines_checkbox.stateChanged.connect(self.on_config_changed)
        
    def on_config_changed(self):
        """配置改变时更新内部配置并立即应用"""
        # 注意：窗口宽高现在通过四角标记调节，不从输入框获取
        self.config['single_line_mode'] = self.single_line_checkbox.isChecked()
        self.config['show_resize_handles'] = self.show_resize_handles_checkbox.isChecked()
        self.config['hover_to_show'] = self.hover_to_show_checkbox.isChecked()
        self.config['key_to_show'] = self.key_to_show_checkbox.isChecked()
        self.config['custom_key'] = self.custom_key_combo.currentText()
        self.config['font_size'] = self.font_size_spinbox.value()
        self.config['font_family'] = self.font_family_combo.currentText()
        self.config['remove_empty_lines'] = self.remove_empty_lines_checkbox.isChecked()

        # 控制自定义按键下拉框使能状态：仅在“按键隐藏”开启时可操作
        self.custom_key_combo.setEnabled(self.key_to_show_checkbox.isChecked())
        # 光标设置（大小由滑块处理）

        # 翻页按键配置由录入逻辑直接更新，这里不重复处理
        
        # 立即保存并应用配置
        self.config_manager.save_config(self.config)
        self.config_changed.emit()
        
    # 移除窗口透明度处理方法，因为已固定为极低透明度
    
    def on_text_opacity_changed(self, value):
        """文字透明度改变"""
        self.config['text_opacity'] = value / 100.0
        self.text_opacity_label.setText(f'{value}%')
        
        # 立即保存并应用配置
        self.config_manager.save_config(self.config)
        self.config_changed.emit()

    def on_dot_opacity_changed(self, value):
        self.config['dot_cursor_opacity'] = value / 100.0
        self.dot_opacity_label.setText(f'{value}%')
        self.config_manager.save_config(self.config)
        self.config_changed.emit()

    def on_dot_size_changed(self, value):
        self.config['dot_cursor_size'] = value
        self.dot_size_value_label.setText(f'{value} px')
        self.config_manager.save_config(self.config)
        self.config_changed.emit()

    def choose_dot_color(self):
        current_color = QColor(self.config.get('dot_cursor_color', '#000000'))
        color = QColorDialog.getColor(current_color, self, '选择圆点颜色')
        if color.isValid():
            color_hex = color.name()
            self.config['dot_cursor_color'] = color_hex
            self.update_dot_color_button(color_hex)
            self.dot_color_label.setText(color_hex)
            self.config_manager.save_config(self.config)
            self.config_changed.emit()

    def update_dot_color_button(self, color_hex):
        self.dot_color_button.setStyleSheet(
            f'QPushButton {{'
            f'    background-color: {color_hex};'
            f'    border: 1px solid #bdc3c7;'
            f'    border-radius: 4px;'
            f'}}'
        )

    # 删除旧的 on_cursor_config_changed（改为滑块专用处理）
        
    def choose_color(self):
        """选择文字颜色"""
        current_color = QColor(self.config.get('font_color', '#000000'))
        color = QColorDialog.getColor(current_color, self, '选择文字颜色')
        
        if color.isValid():
            color_hex = color.name()
            self.config['font_color'] = color_hex
            self.update_color_button(color_hex)
            self.color_label.setText(color_hex)
            
            # 立即保存并应用配置
            self.config_manager.save_config(self.config)
            self.config_changed.emit()
            
    def update_color_button(self, color_hex):
        """更新颜色按钮的显示"""
        self.color_button.setStyleSheet(
            f'QPushButton {{'
            f'    background-color: {color_hex};'
            f'    border: 1px solid #bdc3c7;'
            f'    border-radius: 4px;'
            f'}}'
        )
        
    def reset_to_default(self):
        """重置为默认配置"""
        # 直接重置为默认配置，无需确认提示
        self.config = self.config_manager.get_default_config().copy()
        self.load_current_config()
        # 立即保存并应用配置
        self.config_manager.save_config(self.config)
        self.config_changed.emit()
            
    def apply_config(self):
        """应用配置"""
        self.config_manager.save_config(self.config)
        self.config_changed.emit()
        
    def accept_config(self):
        """确定并关闭窗口"""
        self.apply_config()
        self.close()  # 使用close()而不是accept()，避免可能的快捷键冲突
        
    def keyPressEvent(self, event):
        """键盘按键事件处理"""
        # 如果正在录入翻页按键，捕获按键并写入配置
        if self.recording_up or self.recording_down:
            # 禁止组合键：仅在无修饰键时才允许录入
            if event.modifiers() != Qt.NoModifier:
                event.accept()
                return

            # 将按键映射为可保存的token（使用Qt键值作为token，确保一致性）
            key_token = None
            key_value = event.key()
            # 对于特殊键，用特殊名称；对于其他键，用字符串形式的键值
            if key_value == Qt.Key_Space:
                key_token = 'space'
            elif key_value in (Qt.Key_Return, Qt.Key_Enter):
                key_token = 'enter'
            elif key_value == Qt.Key_Tab:
                key_token = 'tab'
            else:
                # 对于字母、数字、符号键，直接用键值作为token（字符串形式存储）
                key_token = str(key_value)

            # 过滤禁止的特殊键
            if key_token in ('ctrl', 'alt', 'shift', 'win', 'meta', 'command', 'super'):
                event.accept()
                return

            # 录入逻辑（添加按键，支持最多5个）
            if key_token:
                if self.recording_up:
                    success = self.add_key('page_up_keys', key_token)
                    if success:
                        # 成功添加后自动结束录入
                        self.recording_up = False
                        self.page_up_record_btn.setText('+ 添加按键')
                elif self.recording_down:
                    success = self.add_key('page_down_keys', key_token)
                    if success:
                        self.recording_down = False
                        self.page_down_record_btn.setText('+ 添加按键')

            # 正在录入时不向父窗口传递按键事件
            event.accept()
            return

        # 阻止Ctrl+Q快捷键传递到父窗口，避免意外退出程序
        if event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            # 在配置窗口中忽略Ctrl+Q，不传递给父窗口
            event.accept()
            return
        
        # 其他按键事件正常处理
        super().keyPressEvent(event)

    def start_record_up_keys(self):
        """开始录入上一页按键"""
        self.recording_down = False
        self.page_down_record_btn.setText('+ 添加按键')
        self.recording_up = True
        self.page_up_record_btn.setText('⏺ 请按键...')
        self.activateWindow()
        self.setFocus(Qt.OtherFocusReason)

    def start_record_down_keys(self):
        """开始录入下一页按键"""
        self.recording_up = False
        self.page_up_record_btn.setText('+ 添加按键')
        self.recording_down = True
        self.page_down_record_btn.setText('⏺ 请按键...')
        self.activateWindow()
        self.setFocus(Qt.OtherFocusReason)

    def remove_key(self, config_key, key_token):
        """删除指定按键"""
        keys = self.config.get(config_key, [])
        if key_token in keys:
            keys.remove(key_token)
            self.config[config_key] = keys
            self.config_manager.save_config(self.config)
            self.config_changed.emit()
            self.refresh_key_tags()

    def add_key(self, config_key, key_token):
        """添加按键"""
        keys = self.config.get(config_key, [])
        if key_token not in keys and len(keys) < 5:
            keys.append(key_token)
            self.config[config_key] = keys
            self.config_manager.save_config(self.config)
            self.config_changed.emit()
            self.refresh_key_tags()
            return True
        return False

    def on_auto_read_speed_changed(self, value):
        """自动阅读速度改变"""
        # 转换为实际速度值（0-19 -> 0.5-10秒，步长0.5）
        speed = 0.5 + value * 0.5
        self.config['auto_read_speed'] = speed
        self.auto_read_speed_label.setText(f'{speed:.1f} 秒/页')
        # 立即保存并应用配置
        self.config_manager.save_config(self.config)
        self.config_changed.emit()

    def refresh_config(self):
        """刷新配置显示（供外部调用）"""
        self.config = self.config_manager.get_config().copy()
        self.load_current_config()

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 结束任何录入状态，避免下次打开仍显示“正在录入”
        try:
            self.recording_up = False
            self.recording_down = False
            # 恢复按钮文本
            if hasattr(self, 'page_up_record_btn'):
                self.page_up_record_btn.setText('+ 添加按键')
            if hasattr(self, 'page_down_record_btn'):
                self.page_down_record_btn.setText('+ 添加按键')
        except Exception:
            pass
        # 配置已自动保存，直接关闭窗口
        event.accept()
