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
        self.setFixedSize(450, 600)
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
        
        # 按钮区域
        button_layout = self.create_button_layout()
        main_layout.addLayout(button_layout)
        
    def create_window_group(self):
        """创建窗口设置组"""
        group = QGroupBox('窗口设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 窗口宽度（只读显示）
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(35, 1920)  # 设置最小宽度为35像素
        self.width_spinbox.setSuffix(' px')
        self.width_spinbox.setToolTip('当前窗口宽度（只读，请使用四角标记调节大小）')
        self.width_spinbox.setReadOnly(True)  # 设置为只读
        self.width_spinbox.setEnabled(False)  # 禁用输入
        layout.addRow('窗口宽度:', self.width_spinbox)
        
        # 窗口高度设置（只读显示）
        self.height_spinbox = QSpinBox()
        self.height_spinbox.setRange(35, 1080)  # 设置最小高度为35像素
        self.height_spinbox.setSuffix(' px')
        self.height_spinbox.setToolTip('当前窗口高度（只读，请使用四角标记调节大小）')
        self.height_spinbox.setReadOnly(True)  # 设置为只读
        self.height_spinbox.setEnabled(False)  # 禁用输入
        layout.addRow('窗口高度:', self.height_spinbox)
        
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
        
        # 按键显示控制
        self.key_to_show_checkbox = QCheckBox()
        self.key_to_show_checkbox.setText('需要按键')
        self.key_to_show_checkbox.setToolTip('启用后，需要按住指定按键并且鼠标悬停才显示窗口')
        self.key_to_show_checkbox.stateChanged.connect(self.on_config_changed)
        layout.addRow('按键隐藏:', self.key_to_show_checkbox)
        
        # 自定义按键选择
        self.custom_key_combo = QComboBox()
        self.custom_key_combo.addItems(['ctrl', 'alt', 'shift'])
        self.custom_key_combo.setToolTip('选择需要按住的自定义按键')
        self.custom_key_combo.currentTextChanged.connect(self.on_config_changed)
        layout.addRow('自定义按键:', self.custom_key_combo)
        
        # 移除窗口透明度设置，因为已固定为极低透明度以避免鼠标穿透
        
        return group
        
    def create_text_group(self):
        """创建文字设置组"""
        group = QGroupBox('文字设置')
        layout = QFormLayout(group)
        layout.setSpacing(10)
        
        # 字体大小
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(1, 72)  # 允许更小的字体大小
        self.font_size_spinbox.setSuffix(' pt')
        self.font_size_spinbox.valueChanged.connect(self.on_config_changed)
        layout.addRow('字体大小:', self.font_size_spinbox)
        
        # 字体类型
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            'Microsoft YaHei',
            'SimSun',
            'SimHei',
            'KaiTi',
            'FangSong',
            'Arial',
            'Times New Roman',
            'Courier New'
        ])
        self.font_family_combo.currentTextChanged.connect(self.on_config_changed)
        layout.addRow('字体类型:', self.font_family_combo)
        
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
        # 阻止Ctrl+Q快捷键传递到父窗口，避免意外退出程序
        if event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            # 在配置窗口中忽略Ctrl+Q，不传递给父窗口
            event.accept()
            return
        
        # 其他按键事件正常处理
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 配置已自动保存，直接关闭窗口
        event.accept()