# -*- coding: utf-8 -*-
"""
书籍列表项组件
实现带有操作图标的书籍列表项
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QBrush


class BookItemWidget(QWidget):
    """书籍列表项组件"""
    
    # 定义信号
    continue_reading = pyqtSignal(dict)  # 继续阅读信号
    start_reading = pyqtSignal(dict)     # 从头阅读信号
    rename_book = pyqtSignal(dict)       # 重命名信号
    delete_book = pyqtSignal(dict)       # 删除信号
    show_contents = pyqtSignal(dict)     # 显示目录信号
    
    def __init__(self, book_name, book_info, parent=None):
        super().__init__(parent)
        self.book_name = book_name
        self.book_info = book_info
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置组件的固定高度
        self.setFixedHeight(50)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)
        
        # 书名标签
        self.name_label = QLabel(self.book_name)
        self.name_label.setFont(QFont("微软雅黑", 11))
        self.name_label.setStyleSheet(
            "QLabel {"
            "    color: #2c3e50;"
            "    padding: 6px;"
            "    background-color: transparent;"
            "}"
        )
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.name_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # 垂直居中对齐
        
        # 操作按钮区域
        self.create_action_buttons()
        
        # 添加到布局
        layout.addWidget(self.name_label)
        layout.addWidget(self.continue_btn)
        layout.addWidget(self.start_btn)
        layout.addWidget(self.contents_btn)
        layout.addWidget(self.rename_btn)
        layout.addWidget(self.delete_btn)
        
        # 设置布局对齐方式
        layout.setAlignment(Qt.AlignVCenter)
        
    def create_action_buttons(self):
        """创建操作按钮"""
        button_style = (
            "QPushButton {"
            "    border: none;"
            "    background-color: transparent;"
            "    color: #7f8c8d;"
            "    font-size: 18px;"
            "    padding: 6px;"
            "    border-radius: 4px;"
            "    min-width: 32px;"
            "    max-width: 32px;"
            "    min-height: 32px;"
            "    max-height: 32px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #ecf0f1;"
            "    color: #2c3e50;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #bdc3c7;"
            "}"
        )
        
        # 继续阅读按钮（三角形图标）
        self.continue_btn = QPushButton("▶")
        self.continue_btn.setStyleSheet(button_style + 
            "QPushButton:hover { color: #27ae60; }")
        self.continue_btn.setToolTip("继续阅读")
        self.continue_btn.clicked.connect(lambda: self.continue_reading.emit(self.book_info))
        
        # 从头阅读按钮（带回转的三角形）
        self.start_btn = QPushButton("⟲")
        self.start_btn.setStyleSheet(button_style + 
            "QPushButton:hover { color: #3498db; }")
        self.start_btn.setToolTip("从头阅读")
        self.start_btn.clicked.connect(lambda: self.start_reading.emit(self.book_info))
        
        # 目录按钮
        self.contents_btn = QPushButton("📋")
        self.contents_btn.setStyleSheet(button_style + 
            "QPushButton:hover { color: #9b59b6; }")
        self.contents_btn.setToolTip("显示目录")
        self.contents_btn.clicked.connect(lambda: self.show_contents.emit(self.book_info))
        
        # 重命名按钮
        self.rename_btn = QPushButton("✏")
        self.rename_btn.setStyleSheet(button_style + 
            "QPushButton:hover { color: #f39c12; }")
        self.rename_btn.setToolTip("重命名")
        self.rename_btn.clicked.connect(lambda: self.rename_book.emit(self.book_info))
        
        # 删除按钮
        self.delete_btn = QPushButton("🗑")
        self.delete_btn.setStyleSheet(button_style + 
            "QPushButton:hover { color: #e74c3c; }")
        self.delete_btn.setToolTip("删除")
        self.delete_btn.clicked.connect(lambda: self.delete_book.emit(self.book_info))
        
    def update_book_info(self, book_name, book_info):
        """更新书籍信息"""
        self.book_name = book_name
        self.book_info = book_info
        self.name_label.setText(book_name)


class BookCardWidget(QWidget):
    continue_reading = pyqtSignal(dict)
    start_reading = pyqtSignal(dict)
    rename_book = pyqtSignal(dict)
    delete_book = pyqtSignal(dict)
    show_contents = pyqtSignal(dict)

    def __init__(self, book_name, book_info, parent=None):
        super().__init__(parent)
        self.book_name = book_name
        self.book_info = book_info
        self.setFixedSize(150, 190)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.title = QLabel(self.elide_text(book_name))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setStyleSheet('color:#2c3e50;')
        layout.addWidget(self.title)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def elide_text(self, text, max_len=20):
        return text if len(text) <= max_len else text[:max_len] + '...'

    def mouseDoubleClickEvent(self, event):
        self.continue_reading.emit(self.book_info)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect()
        shadow = QColor(0, 0, 0, 40)
        p.setPen(Qt.NoPen)
        p.setBrush(shadow)
        p.drawRoundedRect(r.adjusted(4, 4, -4, -4), 10, 10)
        cover_rect = r.adjusted(18, 18, -18, -60)
        p.setBrush(QColor(46, 134, 193))
        p.setPen(QPen(QColor(33, 97, 140), 2))
        p.drawRoundedRect(cover_rect, 6, 6)
        p.end()

    def show_menu(self, pos):
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu(self)
        a1 = QAction('继续阅读', self)
        a1.triggered.connect(lambda: self.continue_reading.emit(self.book_info))
        menu.addAction(a1)
        a2 = QAction('从头阅读', self)
        a2.triggered.connect(lambda: self.start_reading.emit(self.book_info))
        menu.addAction(a2)
        menu.addSeparator()
        a3 = QAction('重命名', self)
        a3.triggered.connect(lambda: self.rename_book.emit(self.book_info))
        menu.addAction(a3)
        a4 = QAction('删除', self)
        a4.triggered.connect(lambda: self.delete_book.emit(self.book_info))
        menu.addAction(a4)
        a5 = QAction('显示目录', self)
        a5.triggered.connect(lambda: self.show_contents.emit(self.book_info))
        menu.addAction(a5)
        menu.exec_(self.mapToGlobal(pos))

    def update_book_info(self, book_name, book_info):
        self.book_name = book_name
        self.book_info = book_info
        self.title.setText(self.elide_text(book_name))
