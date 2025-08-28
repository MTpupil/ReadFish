#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
书签管理窗口 - 显示和管理书签
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QInputDialog,
    QTextEdit, QFrame, QSplitter, QMenu, QAction, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QCursor

from bookmark_manager import BookmarkManager
from toast_notification import ToastManager


class BookmarkWindow(QDialog):
    """书签管理窗口"""
    
    # 定义信号
    bookmark_selected = pyqtSignal(dict)  # 书签选择信号
    
    def __init__(self, file_path, title, bookmark_manager, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.book_title = title
        self.bookmark_manager = bookmark_manager  # 使用传入的BookmarkManager实例
        self.bookmarks = []
        self.auto_close_after_jump = True  # 跳转后自动关闭配置
        
        self.init_ui()
        self.load_bookmarks()
    
    def format_book_title(self, file_path):
        """
        格式化书籍标题，去除时间戳、扩展名并添加书名号
        """
        filename = os.path.basename(file_path)
        
        # 移除时间戳前缀（格式：数字_文件名.扩展名）
        if '_' in filename:
            book_name = '_'.join(filename.split('_')[1:])  # 去掉时间戳部分
        else:
            book_name = filename
        
        # 移除扩展名
        if '.' in book_name:
            book_name = '.'.join(book_name.split('.')[:-1])
        
        # 添加书名号
        return f'《{book_name}》'
        
    def init_ui(self):
        """初始化用户界面"""
        formatted_title = self.format_book_title(self.file_path)
        self.setWindowTitle(f'书签管理 - {formatted_title}')
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 设置窗口图标
        if os.path.exists('logo.png'):
            self.setWindowIcon(QIcon('logo.png'))
        elif os.path.exists('logo.svg'):
            self.setWindowIcon(QIcon('logo.svg'))
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题区域
        self.create_title_area(main_layout)
        
        # 分割器 - 左侧书签列表，右侧预览
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧：书签列表
        self.create_bookmark_list(splitter)
        
        # 右侧：书签预览
        self.create_bookmark_preview(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 300])
        
        # 按钮区域
        self.create_button_area(main_layout)
        
    def create_title_area(self, layout):
        """创建标题区域"""
        title_frame = QFrame()
        title_frame.setFrameStyle(QFrame.StyledPanel)
        title_frame.setStyleSheet(
            "QFrame {"
            "    background-color: #f8f9fa;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 5px;"
            "    padding: 10px;"
            "}"
        )
        
        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(5)
        
        # 书籍标题
        formatted_title = self.format_book_title(self.file_path)
        book_label = QLabel(f'书籍：{formatted_title}')
        book_label.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        book_label.setStyleSheet('color: #2c3e50; background: transparent; border: none;')
        
        # 书签统计
        self.stats_label = QLabel('正在加载书签...')
        self.stats_label.setFont(QFont('Microsoft YaHei', 9))
        self.stats_label.setStyleSheet('color: #6c757d; background: transparent; border: none;')
        
        title_layout.addWidget(book_label)
        title_layout.addWidget(self.stats_label)
        
        layout.addWidget(title_frame)
        
    def create_bookmark_list(self, parent):
        """创建书签列表"""
        list_frame = QFrame()
        list_frame.setFrameStyle(QFrame.StyledPanel)
        
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(5, 5, 5, 5)
        
        # 列表标题
        list_title = QLabel('书签列表')
        list_title.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        list_title.setStyleSheet('color: #495057; padding: 5px;')
        list_layout.addWidget(list_title)
        
        # 书签列表
        self.bookmark_list = QListWidget()
        self.bookmark_list.setStyleSheet(
            "QListWidget {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: white;"
            "    selection-background-color: #007bff;"
            "    selection-color: white;"
            "}"
            "QListWidget::item {"
            "    padding: 8px;"
            "    border-bottom: 1px solid #e9ecef;"
            "}"
            "QListWidget::item:hover {"
            "    background-color: #f8f9fa;"
            "}"
            "QListWidget::item:selected {"
            "    background-color: #007bff;"
            "    color: white;"
            "}"
        )
        
        # 连接信号
        self.bookmark_list.itemClicked.connect(self.on_bookmark_clicked)
        self.bookmark_list.itemDoubleClicked.connect(self.on_bookmark_double_clicked)
        self.bookmark_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.bookmark_list.customContextMenuRequested.connect(self.show_bookmark_context_menu)
        
        list_layout.addWidget(self.bookmark_list)
        
        parent.addWidget(list_frame)
        
    def create_bookmark_preview(self, parent):
        """创建书签预览区域"""
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.StyledPanel)
        
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        # 预览标题
        preview_title = QLabel('书签详情')
        preview_title.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        preview_title.setStyleSheet('color: #495057; padding: 5px;')
        preview_layout.addWidget(preview_title)
        
        # 书签信息
        self.bookmark_info = QLabel('请选择一个书签查看详情')
        self.bookmark_info.setFont(QFont('Microsoft YaHei', 9))
        self.bookmark_info.setStyleSheet(
            "QLabel {"
            "    color: #6c757d;"
            "    padding: 10px;"
            "    background-color: #f8f9fa;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 4px;"
            "}"
        )
        self.bookmark_info.setWordWrap(True)
        self.bookmark_info.setAlignment(Qt.AlignTop)
        preview_layout.addWidget(self.bookmark_info)
        
        # 内容预览
        preview_content_label = QLabel('内容预览')
        preview_content_label.setFont(QFont('Microsoft YaHei', 9, QFont.Bold))
        preview_content_label.setStyleSheet('color: #495057; padding: 5px 0px;')
        preview_layout.addWidget(preview_content_label)
        
        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        self.content_preview.setMaximumHeight(150)
        self.content_preview.setStyleSheet(
            "QTextEdit {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: #f8f9fa;"
            "    color: #495057;"
            "    font-family: 'Microsoft YaHei';"
            "    font-size: 9pt;"
            "    padding: 8px;"
            "}"
        )
        self.content_preview.setPlainText('请选择一个书签查看内容预览')
        preview_layout.addWidget(self.content_preview)
        
        parent.addWidget(preview_frame)
        
    def create_button_area(self, layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 跳转到书签按钮
        self.goto_button = QPushButton('跳转到书签')
        self.goto_button.setFont(QFont('Microsoft YaHei', 9))
        self.goto_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #007bff;"
            "    color: white;"
            "    border: none;"
            "    padding: 8px 16px;"
            "    border-radius: 4px;"
            "    font-weight: bold;"
            "}"
            "QPushButton:hover {"
            "    background-color: #0056b3;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #004085;"
            "}"
            "QPushButton:disabled {"
            "    background-color: #6c757d;"
            "    color: #adb5bd;"
            "}"
        )
        self.goto_button.setEnabled(False)
        self.goto_button.clicked.connect(self.goto_bookmark)
        
        # 删除书签按钮
        self.delete_button = QPushButton('删除书签')
        self.delete_button.setFont(QFont('Microsoft YaHei', 9))
        self.delete_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #dc3545;"
            "    color: white;"
            "    border: none;"
            "    padding: 8px 16px;"
            "    border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #c82333;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #bd2130;"
            "}"
            "QPushButton:disabled {"
            "    background-color: #6c757d;"
            "    color: #adb5bd;"
            "}"
        )
        self.delete_button.setEnabled(False)
        self.delete_button.clicked.connect(self.delete_bookmark)
        
        # 关闭按钮
        close_button = QPushButton('关闭')
        close_button.setFont(QFont('Microsoft YaHei', 9))
        close_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #6c757d;"
            "    color: white;"
            "    border: none;"
            "    padding: 8px 16px;"
            "    border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #5a6268;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #545b62;"
            "}"
        )
        close_button.clicked.connect(self.close)
        
        # 自动关闭配置选项
        self.auto_close_checkbox = QCheckBox('跳转后自动关闭窗口')
        self.auto_close_checkbox.setFont(QFont('Microsoft YaHei', 9))
        self.auto_close_checkbox.setChecked(self.auto_close_after_jump)
        self.auto_close_checkbox.setStyleSheet(
            "QCheckBox {"
            "    color: #495057;"
            "    spacing: 5px;"
            "}"
            "QCheckBox::indicator {"
            "    width: 16px;"
            "    height: 16px;"
            "}"
            "QCheckBox::indicator:unchecked {"
            "    border: 2px solid #ced4da;"
            "    background-color: white;"
            "    border-radius: 3px;"
            "}"
            "QCheckBox::indicator:checked {"
            "    border: 2px solid #007bff;"
            "    background-color: #007bff;"
            "    border-radius: 3px;"
            "    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPgo=);"
            "}"
        )
        self.auto_close_checkbox.toggled.connect(self.on_auto_close_toggled)
        
        # 添加按钮到布局
        button_layout.addWidget(self.goto_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()  # 添加弹性空间
        button_layout.addWidget(self.auto_close_checkbox)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
    def load_bookmarks(self):
        """加载书签数据"""
        try:
            self.bookmarks = self.bookmark_manager.get_bookmarks(self.file_path)
            self.update_bookmark_list()
            self.update_stats()
        except Exception as e:
            ToastManager.show_error(f'加载书签失败：{str(e)}', self)
            
    def update_bookmark_list(self):
        """更新书签列表显示"""
        self.bookmark_list.clear()
        
        if not self.bookmarks:
            item = QListWidgetItem('暂无书签')
            item.setFlags(Qt.NoItemFlags)  # 禁用选择
            item.setData(Qt.UserRole, None)
            self.bookmark_list.addItem(item)
            return
            
        for bookmark in self.bookmarks:
            # 创建显示文本
            display_text = f"{bookmark['name']}\n第 {bookmark['line_number']} 行 - {bookmark['created_time']}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, bookmark)  # 存储书签数据
            item.setToolTip(f"内容预览：{bookmark['content_preview']}")
            
            self.bookmark_list.addItem(item)
            
    def update_stats(self):
        """更新统计信息"""
        count = len(self.bookmarks)
        if count == 0:
            self.stats_label.setText('暂无书签')
        else:
            self.stats_label.setText(f'共 {count} 个书签')
            
    def on_bookmark_clicked(self, item):
        """书签点击事件"""
        bookmark = item.data(Qt.UserRole)
        if bookmark:
            self.show_bookmark_details(bookmark)
            self.goto_button.setEnabled(True)
            self.delete_button.setEnabled(True)
        else:
            self.goto_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            
    def on_bookmark_double_clicked(self, item):
        """书签双击事件 - 直接跳转"""
        bookmark = item.data(Qt.UserRole)
        if bookmark:
            self.goto_bookmark()
            
    def show_bookmark_details(self, bookmark):
        """显示书签详情"""
        info_text = f"""书签名称：{bookmark['name']}
创建时间：{bookmark['created_time']}
位置信息：第 {bookmark['line_number']} 行，字符位置 {bookmark['char_position']}
备注：{bookmark.get('note', '无')}"""
        
        self.bookmark_info.setText(info_text)
        self.content_preview.setPlainText(bookmark['content_preview'])
        
    def show_bookmark_context_menu(self, position):
        """显示书签右键菜单"""
        item = self.bookmark_list.itemAt(position)
        if not item or not item.data(Qt.UserRole):
            return
            
        menu = QMenu(self)
        
        # 跳转到书签
        goto_action = QAction('跳转到书签', self)
        goto_action.triggered.connect(self.goto_bookmark)
        menu.addAction(goto_action)
        
        menu.addSeparator()
        
        # 重命名书签
        rename_action = QAction('重命名书签', self)
        rename_action.triggered.connect(self.rename_bookmark)
        menu.addAction(rename_action)
        
        # 编辑备注
        edit_note_action = QAction('编辑备注', self)
        edit_note_action.triggered.connect(self.edit_bookmark_note)
        menu.addAction(edit_note_action)
        
        menu.addSeparator()
        
        # 删除书签
        delete_action = QAction('删除书签', self)
        delete_action.triggered.connect(self.delete_bookmark)
        menu.addAction(delete_action)
        
        # 显示菜单
        menu.exec_(self.bookmark_list.mapToGlobal(position))
        
    def goto_bookmark(self):
        """跳转到选中的书签"""
        current_item = self.bookmark_list.currentItem()
        if not current_item:
            return
            
        bookmark = current_item.data(Qt.UserRole)
        if bookmark:
            # 发送跳转信号
            self.bookmark_selected.emit(bookmark)
            # 根据配置决定是否自动关闭窗口
            if self.auto_close_after_jump:
                self.close()
            
    def delete_bookmark(self):
        """删除选中的书签"""
        current_item = self.bookmark_list.currentItem()
        if not current_item:
            return
            
        bookmark = current_item.data(Qt.UserRole)
        if not bookmark:
            return
            
        # 直接删除，不需要确认和成功提示
        if self.bookmark_manager.delete_bookmark(self.file_path, bookmark['id']):
            # 重新加载书签列表
            self.load_bookmarks()
            # 清空详情显示
            self.bookmark_info.setText('请选择一个书签查看详情')
            self.content_preview.setPlainText('请选择一个书签查看内容预览')
            self.goto_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            ToastManager.show_error('删除书签失败！', self)
                
    def rename_bookmark(self):
        """重命名书签"""
        current_item = self.bookmark_list.currentItem()
        if not current_item:
            return
            
        bookmark = current_item.data(Qt.UserRole)
        if not bookmark:
            return
            
        # 输入新名称
        new_name, ok = QInputDialog.getText(
            self, '重命名书签', 
            '请输入新的书签名称：',
            text=bookmark['name']
        )
        
        if ok and new_name.strip():
            if self.bookmark_manager.update_bookmark(
                self.file_path, bookmark['id'], name=new_name.strip()
            ):
                # 重新加载书签列表
                self.load_bookmarks()
            else:
                ToastManager.show_error('重命名书签失败！', self)
                
    def edit_bookmark_note(self):
        """编辑书签备注"""
        current_item = self.bookmark_list.currentItem()
        if not current_item:
            return
            
        bookmark = current_item.data(Qt.UserRole)
        if not bookmark:
            return
            
        # 输入新备注
        new_note, ok = QInputDialog.getMultiLineText(
            self, '编辑备注', 
            '请输入书签备注：',
            text=bookmark.get('note', '')
        )
        
        if ok:
            if self.bookmark_manager.update_bookmark(
                self.file_path, bookmark['id'], note=new_note
            ):
                # 重新加载书签列表
                self.load_bookmarks()
                # 如果当前选中的还是这个书签，更新详情显示
                current_item = self.bookmark_list.currentItem()
                if current_item and current_item.data(Qt.UserRole):
                    updated_bookmark = current_item.data(Qt.UserRole)
                    if updated_bookmark['id'] == bookmark['id']:
                        self.show_bookmark_details(updated_bookmark)
            else:
                ToastManager.show_error('更新书签备注失败！', self)
    
    def on_auto_close_toggled(self, checked):
        """自动关闭配置选项切换回调"""
        self.auto_close_after_jump = checked