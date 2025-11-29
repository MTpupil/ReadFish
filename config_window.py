#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置窗口模块 - 用于设置阅读器的各种参数
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QSlider, QSpinBox, QPushButton, QColorDialog,
    QComboBox, QGroupBox, QMessageBox, QFrame, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette


class ConfigWindow(QDialog):
    """配置窗口类"""
    
    # 定义信号
    config_changed = pyqtSignal()  # 配置改变信号
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.config = self.config_manager.get_config().copy()  # 获取配置副本
        
        self.init_ui()
        self.load_current_config()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('ReadFish - 设置')
        self.setFixedSize(480, 720)
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
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 窗口设置组
        window_group = self.create_window_group()
        main_layout.addWidget(window_group)
        
        # 文字设置组
        text_group = self.create_text_group()
        main_layout.addWidget(text_group)

        # 光标设置组（新增）
        cursor_group = self.create_cursor_group()
        main_layout.addWidget(cursor_group)

        # 翻页按键设置组（新增）
        nav_group = self.create_navigation_key_group()
        main_layout.addWidget(nav_group)
        
        # 按钮区域
        button_layout = self.create_button_layout()
        main_layout.addLayout(button_layout)
        
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
        - 允许用户通过“按键录入”的方式添加最多两个上一页和两个下一页的按键
        - 保留默认方向键和PageUp/PageDown翻页功能
        """
        group = QGroupBox('翻页按键设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)

        # 上一页按键显示与操作
        up_layout = QHBoxLayout()
        self.page_up_keys_label = QLabel('未设置')
        self.page_up_record_btn = QPushButton('录入上一页按键')
        self.page_up_clear_btn = QPushButton('清除')
        self.page_up_record_btn.setToolTip('点击后，按下要设置的按键进行录入（支持字母/数字、Space、Enter、Tab；最多两个；不支持组合键和 Ctrl/Alt/Shift/Win）。')
        self.page_up_clear_btn.setToolTip('清除已设置的上一页按键')
        self.page_up_record_btn.clicked.connect(self.start_record_up_keys)
        self.page_up_clear_btn.clicked.connect(self.clear_up_keys)
        up_layout.addWidget(self.page_up_keys_label)
        up_layout.addStretch()
        up_layout.addWidget(self.page_up_record_btn)
        up_layout.addWidget(self.page_up_clear_btn)
        layout.addRow('上一页按键:', up_layout)

        # 下一页按键显示与操作
        down_layout = QHBoxLayout()
        self.page_down_keys_label = QLabel('未设置')
        self.page_down_record_btn = QPushButton('录入下一页按键')
        self.page_down_clear_btn = QPushButton('清除')
        self.page_down_record_btn.setToolTip('点击后，按下要设置的按键进行录入（支持字母/数字、Space、Enter、Tab；最多两个；不支持组合键和 Ctrl/Alt/Shift/Win）。')
        self.page_down_clear_btn.setToolTip('清除已设置的下一页按键')
        self.page_down_record_btn.clicked.connect(self.start_record_down_keys)
        self.page_down_clear_btn.clicked.connect(self.clear_down_keys)
        down_layout.addWidget(self.page_down_keys_label)
        down_layout.addStretch()
        down_layout.addWidget(self.page_down_record_btn)
        down_layout.addWidget(self.page_down_clear_btn)
        layout.addRow('下一页按键:', down_layout)

        # 录入状态标志
        self.recording_up = False
        self.recording_down = False

        # 提示信息
        tip = QLabel('提示：最多设置两个按键（字母/数字或 Space、Enter、Tab）。默认方向键和 PageUp/PageDown 始终可用。')
        tip.setStyleSheet('color: #7f8c8d;')
        layout.addRow(tip)

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
            up_keys = self.config.get('page_up_keys', [])
            down_keys = self.config.get('page_down_keys', [])
            self.page_up_keys_label.setText(', '.join(up_keys) if up_keys else '未设置')
            self.page_down_keys_label.setText(', '.join(down_keys) if down_keys else '未设置')
            
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
        # 如果正在录入翻页按键，捕获字母键并写入配置
        if self.recording_up or self.recording_down:
            # 禁止组合键：仅在无修饰键时才允许录入
            if event.modifiers() != Qt.NoModifier:
                event.accept()
                return

            # 将按键映射为可保存的token
            key_token = None
            if event.key() == Qt.Key_Space:
                key_token = 'space'
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                key_token = 'enter'
            elif event.key() == Qt.Key_Tab:
                key_token = 'tab'
            else:
                # 使用event.text()获取字母或数字
                text = event.text().strip().lower()
                if len(text) == 1 and (text.isalpha() or text.isdigit()):
                    key_token = text

            # 过滤禁止的特殊键
            if key_token in ('ctrl', 'alt', 'shift', 'win', 'meta', 'command', 'super'):
                event.accept()
                return

            # 录入逻辑
            if key_token:
                if self.recording_up:
                    up_keys = self.config.get('page_up_keys', [])
                    if key_token not in up_keys and len(up_keys) < 2:
                        up_keys.append(key_token)
                        self.config['page_up_keys'] = up_keys
                        self.page_up_keys_label.setText(', '.join(up_keys))
                        self.config_manager.save_config(self.config)
                        self.config_changed.emit()
                    # 成功录入一个按键后，自动结束录入，避免持续显示“正在录入”
                    self.recording_up = False
                    self.page_up_record_btn.setText('录入上一页按键')
                elif self.recording_down:
                    down_keys = self.config.get('page_down_keys', [])
                    if key_token not in down_keys and len(down_keys) < 2:
                        down_keys.append(key_token)
                        self.config['page_down_keys'] = down_keys
                        self.page_down_keys_label.setText(', '.join(down_keys))
                        self.config_manager.save_config(self.config)
                        self.config_changed.emit()
                    # 成功录入一个按键后，自动结束录入，避免持续显示“正在录入”
                    self.recording_down = False
                    self.page_down_record_btn.setText('录入下一页按键')

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
        self.page_down_record_btn.setText('录入下一页按键')
        # 切换录入状态
        self.recording_up = not self.recording_up
        self.page_up_record_btn.setText('正在录入...(按一个键后自动完成，可再次点击录入第二个)' if self.recording_up else '录入上一页按键')
        # 焦点确保按键能被接收
        self.activateWindow()
        self.setFocus(Qt.OtherFocusReason)

    def start_record_down_keys(self):
        """开始录入下一页按键"""
        self.recording_up = False
        self.page_up_record_btn.setText('录入上一页按键')
        # 切换录入状态
        self.recording_down = not self.recording_down
        self.page_down_record_btn.setText('正在录入...(按一个键后自动完成，可再次点击录入第二个)' if self.recording_down else '录入下一页按键')
        # 焦点确保按键能被接收
        self.activateWindow()
        self.setFocus(Qt.OtherFocusReason)

    def clear_up_keys(self):
        """清除上一页按键设置"""
        self.recording_up = False
        self.page_up_record_btn.setText('录入上一页按键')
        self.config['page_up_keys'] = []
        self.page_up_keys_label.setText('未设置')
        # 保存配置并通知变更
        self.config_manager.save_config(self.config)
        self.config_changed.emit()

    def clear_down_keys(self):
        """清除下一页按键设置"""
        self.recording_down = False
        self.page_down_record_btn.setText('录入下一页按键')
        self.config['page_down_keys'] = []
        self.page_down_keys_label.setText('未设置')
        # 保存配置并通知变更
        self.config_manager.save_config(self.config)
        self.config_changed.emit()
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 结束任何录入状态，避免下次打开仍显示“正在录入”
        try:
            self.recording_up = False
            self.recording_down = False
            # 恢复按钮文本
            if hasattr(self, 'page_up_record_btn'):
                self.page_up_record_btn.setText('录入上一页按键')
            if hasattr(self, 'page_down_record_btn'):
                self.page_down_record_btn.setText('录入下一页按键')
        except Exception:
            pass
        # 配置已自动保存，直接关闭窗口
        event.accept()
