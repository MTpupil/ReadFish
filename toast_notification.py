# -*- coding: utf-8 -*-
"""
气泡提示组件
提供自动消失的气泡提示功能，替代传统的弹窗提示
"""

import sys
from PyQt5.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPalette


class ToastNotification(QWidget):
    """气泡提示组件
    
    提供自动消失的气泡提示功能，支持成功、警告、错误等不同类型的提示
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 创建标签
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(QFont('Microsoft YaHei', 10))
        
        # 设置透明度效果
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        
        # 创建动画
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)  # 300ms淡入淡出
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 创建定时器
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.fade_out)
        
    def show_success(self, message, duration=2000):
        """显示成功提示
        
        Args:
            message: 提示消息
            duration: 显示时长（毫秒），默认2秒
        """
        self._show_toast(message, 'success', duration)
        
    def show_warning(self, message, duration=3000):
        """显示警告提示
        
        Args:
            message: 提示消息
            duration: 显示时长（毫秒），默认3秒
        """
        self._show_toast(message, 'warning', duration)
        
    def show_error(self, message, duration=3000):
        """显示错误提示
        
        Args:
            message: 提示消息
            duration: 显示时长（毫秒），默认3秒
        """
        self._show_toast(message, 'error', duration)
        
    def show_info(self, message, duration=2000):
        """显示信息提示
        
        Args:
            message: 提示消息
            duration: 显示时长（毫秒），默认2秒
        """
        self._show_toast(message, 'info', duration)
        
    def _show_toast(self, message, toast_type, duration):
        """显示气泡提示
        
        Args:
            message: 提示消息
            toast_type: 提示类型（success, warning, error, info）
            duration: 显示时长（毫秒）
        """
        # 设置消息文本
        self.label.setText(message)
        
        # 根据类型设置样式
        self._set_style(toast_type)
        
        # 调整大小和位置
        self._adjust_size_and_position()
        
        # 显示动画
        self.show()
        self.fade_in()
        
        # 设置自动消失定时器
        self.timer.start(duration)
        
    def _set_style(self, toast_type):
        """设置气泡样式
        
        Args:
            toast_type: 提示类型
        """
        # 基础样式
        base_style = """
            QLabel {
                background-color: %s;
                color: %s;
                border: 1px solid %s;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
            }
        """
        
        # 根据类型设置颜色
        if toast_type == 'success':
            bg_color = '#d4edda'
            text_color = '#155724'
            border_color = '#c3e6cb'
        elif toast_type == 'warning':
            bg_color = '#fff3cd'
            text_color = '#856404'
            border_color = '#ffeaa7'
        elif toast_type == 'error':
            bg_color = '#f8d7da'
            text_color = '#721c24'
            border_color = '#f5c6cb'
        else:  # info
            bg_color = '#d1ecf1'
            text_color = '#0c5460'
            border_color = '#bee5eb'
            
        self.label.setStyleSheet(base_style % (bg_color, text_color, border_color))
        
    def _adjust_size_and_position(self):
        """调整大小和位置"""
        # 调整标签大小
        self.label.adjustSize()
        
        # 设置窗口大小
        self.resize(self.label.size())
        
        # 计算位置（显示在父窗口的顶部中央）
        if self.parent_widget:
            parent_rect = self.parent_widget.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 50  # 距离顶部50像素
        else:
            # 如果没有父窗口，显示在屏幕中央顶部
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.desktop().screenGeometry()
            x = (screen.width() - self.width()) // 2
            y = 50
            
        self.move(x, y)
        
    def fade_in(self):
        """淡入动画"""
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.start()
        
    def fade_out(self):
        """淡出动画"""
        self.fade_animation.finished.connect(self.hide)
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
        
    def hide(self):
        """隐藏气泡"""
        super().hide()
        # 断开信号连接，避免重复连接
        try:
            self.fade_animation.finished.disconnect(self.hide)
        except:
            pass


class ToastManager:
    """气泡提示管理器
    
    管理全局的气泡提示，确保同一时间只显示一个提示
    """
    
    _instance = None
    _current_toast = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    @classmethod
    def show_success(cls, message, parent=None, duration=2000):
        """显示成功提示"""
        cls._show_toast(message, 'success', parent, duration)
        
    @classmethod
    def show_warning(cls, message, parent=None, duration=3000):
        """显示警告提示"""
        cls._show_toast(message, 'warning', parent, duration)
        
    @classmethod
    def show_error(cls, message, parent=None, duration=3000):
        """显示错误提示"""
        cls._show_toast(message, 'error', parent, duration)
        
    @classmethod
    def show_info(cls, message, parent=None, duration=2000):
        """显示信息提示"""
        cls._show_toast(message, 'info', parent, duration)
        
    @classmethod
    def _show_toast(cls, message, toast_type, parent, duration):
        """显示气泡提示"""
        # 如果有正在显示的提示，先隐藏
        if cls._current_toast:
            cls._current_toast.hide()
            
        # 创建新的提示
        cls._current_toast = ToastNotification(parent)
        
        # 显示提示
        if toast_type == 'success':
            cls._current_toast.show_success(message, duration)
        elif toast_type == 'warning':
            cls._current_toast.show_warning(message, duration)
        elif toast_type == 'error':
            cls._current_toast.show_error(message, duration)
        else:
            cls._current_toast.show_info(message, duration)