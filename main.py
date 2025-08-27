#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReadFish - 主程序
用于上班摸鱼时看小说的工具
"""

import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QFileDialog, QMessageBox,
    QSystemTrayIcon, QMenu, QAction, QListWidget, QListWidgetItem,
    QInputDialog, QTabWidget, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter

from reader_window import ReaderWindow
from config_manager import ConfigManager
from history_manager import HistoryManager
from book_item_widget import BookItemWidget
from file_utils import detect_encoding_and_read_file


class MainWindow(QMainWindow):
    """主窗口类 - 用于选择文件和启动阅读器"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()  # 历史记录管理器
        self.reader_window = None
        self.selected_file = None
        self.tray_icon = None
        
        # 书架相关属性 - 使用AppData目录
        appdata_dir = os.path.expanduser('~\\AppData\\Roaming\\ReadFish')
        # 确保目录存在
        os.makedirs(appdata_dir, exist_ok=True)
        self.book_folder = os.path.join(appdata_dir, 'book')
        self.bookshelf_data_file = os.path.join(appdata_dir, 'bookshelf.json')
        self.books_data = {}
        
        # 初始化书架系统
        self.init_bookshelf()
        self.init_ui()
        self.init_tray_icon()
        
        # 初始化完成后刷新书架显示
        self.refresh_bookshelf()
        self.update_continue_button_state()  # 更新继续阅读按钮状态
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('ReadFish - 摸个鱼吧')
        self.setFixedSize(600, 500)  # 增大窗口尺寸以容纳书架功能
        
        # 设置窗口居中
        self.center_window()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题标签
        title_label = QLabel('ReadFish by.木瞳')
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont('Microsoft YaHei', 16, QFont.Bold))
        title_label.setStyleSheet('color: #2c3e50; margin-bottom: 10px;')
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(
            'QTabWidget::pane {'
            '    border: 1px solid #bdc3c7;'
            '    border-radius: 6px;'
            '}'
            'QTabBar::tab {'
            '    background-color: #ecf0f1;'
            '    padding: 8px 16px;'
            '    margin-right: 2px;'
            '    border-top-left-radius: 6px;'
            '    border-top-right-radius: 6px;'
            '}'
            'QTabBar::tab:selected {'
            '    background-color: #3498db;'
            '    color: white;'
            '}'
        )
        
        # 创建快速阅读标签页
        self.quick_read_tab = self.create_quick_read_tab()
        self.tab_widget.addTab(self.quick_read_tab, '快速阅读')
        
        # 创建书架标签页
        self.bookshelf_tab = self.create_bookshelf_tab()
        self.tab_widget.addTab(self.bookshelf_tab, '我的书架')
        
        # 添加组件到主布局
        main_layout.addWidget(title_label)
        main_layout.addWidget(self.tab_widget)
        
    def create_quick_read_tab(self):
        """创建快速阅读标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 文件选择区域
        file_layout = QVBoxLayout()
        
        # 文件路径显示标签
        self.file_label = QLabel('请选择要阅读的txt文件')
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet(
            'border: 2px dashed #bdc3c7; '
            'padding: 20px; '
            'border-radius: 8px; '
            'background-color: #ecf0f1; '
            'color: #7f8c8d;'
        )
        self.file_label.setWordWrap(True)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 选择文件按钮
        self.select_button = QPushButton('选择文件')
        self.select_button.setFixedHeight(40)
        self.select_button.setStyleSheet(
            'QPushButton {'
            '    background-color: #3498db; '
            '    color: white; '
            '    border: none; '
            '    border-radius: 6px; '
            '    font-size: 14px; '
            '    font-weight: bold;'
            '}'
            'QPushButton:hover {'
            '    background-color: #2980b9;'
            '}'
            'QPushButton:pressed {'
            '    background-color: #21618c;'
            '}'
        )
        self.select_button.clicked.connect(self.select_file)
        
        # 当前阅读书籍显示标签
        self.current_book_label = QLabel('')
        self.current_book_label.setAlignment(Qt.AlignCenter)
        self.current_book_label.setStyleSheet(
            'QLabel {'
            '    color: #2c3e50; '
            '    font-size: 12px; '
            '    padding: 5px; '
            '    background-color: #f8f9fa; '
            '    border: 1px solid #dee2e6; '
            '    border-radius: 4px; '
            '    margin: 5px 0;'
            '}'
        )
        self.current_book_label.setVisible(False)
        
        # 继续阅读按钮
        self.continue_button = QPushButton('继续阅读')
        self.continue_button.setFixedHeight(40)
        self.continue_button.setStyleSheet(
            'QPushButton {'
            '    background-color: #e67e22; '
            '    color: white; '
            '    border: none; '
            '    border-radius: 6px; '
            '    font-size: 14px; '
            '    font-weight: bold;'
            '}'
            'QPushButton:hover:enabled {'
            '    background-color: #d35400;'
            '}'
            'QPushButton:pressed:enabled {'
            '    background-color: #ba4a00;'
            '}'
            'QPushButton:disabled {'
            '    background-color: #95a5a6; '
            '    color: #7f8c8d;'
            '}'
        )
        self.continue_button.clicked.connect(self.continue_reading)
        
        # 开始阅读按钮
        self.read_button = QPushButton('开始阅读')
        self.read_button.setFixedHeight(40)
        self.read_button.setEnabled(False)  # 初始状态禁用
        self.read_button.setStyleSheet(
            'QPushButton {'
            '    background-color: #27ae60; '
            '    color: white; '
            '    border: none; '
            '    border-radius: 6px; '
            '    font-size: 14px; '
            '    font-weight: bold;'
            '}'
            'QPushButton:hover:enabled {'
            '    background-color: #229954;'
            '}'
            'QPushButton:pressed:enabled {'
            '    background-color: #1e8449;'
            '}'
            'QPushButton:disabled {'
            '    background-color: #95a5a6; '
            '    color: #7f8c8d;'
            '}'
        )
        self.read_button.clicked.connect(self.start_reading)
        
        # 添加组件到布局
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.current_book_label)  # 添加当前阅读书籍标签
        
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.continue_button)
        button_layout.addWidget(self.read_button)
        
        layout.addLayout(file_layout)
        layout.addLayout(button_layout)
        layout.addStretch()  # 添加弹性空间
        
        return tab
        
    def create_bookshelf_tab(self):
        """创建书架标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 书架操作按钮区域
        button_layout = QHBoxLayout()
        
        # 导入书籍按钮
        self.import_book_button = QPushButton('导入书籍')
        self.import_book_button.setFixedHeight(35)
        self.import_book_button.setStyleSheet(
            'QPushButton {'
            '    background-color: #e74c3c; '
            '    color: white; '
            '    border: none; '
            '    border-radius: 6px; '
            '    font-size: 13px; '
            '    font-weight: bold; '
            '    padding: 0 15px;'
            '}'
            'QPushButton:hover {'
            '    background-color: #c0392b;'
            '}'
            'QPushButton:pressed {'
            '    background-color: #a93226;'
            '}'
        )
        self.import_book_button.clicked.connect(self.import_book)
        
        # 刷新书架按钮
        self.refresh_button = QPushButton('刷新书架')
        self.refresh_button.setFixedHeight(35)
        self.refresh_button.setStyleSheet(
            'QPushButton {'
            '    background-color: #9b59b6; '
            '    color: white; '
            '    border: none; '
            '    border-radius: 6px; '
            '    font-size: 13px; '
            '    font-weight: bold; '
            '    padding: 0 15px;'
            '}'
            'QPushButton:hover {'
            '    background-color: #8e44ad;'
            '}'
            'QPushButton:pressed {'
            '    background-color: #7d3c98;'
            '}'
        )
        self.refresh_button.clicked.connect(self.refresh_bookshelf)
        
        button_layout.addWidget(self.import_book_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        
        # 书籍列表
        self.book_list = QListWidget()
        self.book_list.setStyleSheet(
            'QListWidget {'
            '    border: 1px solid #bdc3c7;'
            '    border-radius: 6px;'
            '    background-color: #ffffff;'
            '    selection-background-color: #3498db;'
            '    selection-color: white;'
            '}'
            'QListWidget::item {'
            '    padding: 8px;'
            '    border-bottom: 1px solid #ecf0f1;'
            '    color: #2c3e50;'
            '}'
            'QListWidget::item:hover {'
            '    background-color: #f8f9fa;'
            '}'
            'QListWidget::item:selected {'
            '    background-color: #3498db;'
            '    color: white;'
            '}'
            'QListWidget::item:selected:hover {'
            '    background-color: #2980b9;'
            '    color: white;'
            '}'
        )
        self.book_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.book_list.customContextMenuRequested.connect(self.show_book_context_menu)
        self.book_list.itemDoubleClicked.connect(self.read_book_from_shelf)
        
        # 书架状态标签
        self.bookshelf_status_label = QLabel('书架为空，请导入书籍')
        self.bookshelf_status_label.setAlignment(Qt.AlignCenter)
        self.bookshelf_status_label.setStyleSheet(
            'color: #7f8c8d; '
            'font-style: italic; '
            'padding: 20px;'
        )
        
        # 添加组件到布局
        layout.addLayout(button_layout)
        layout.addWidget(self.book_list)
        layout.addWidget(self.bookshelf_status_label)
        
        return tab
        
    def init_bookshelf(self):
        """初始化书架系统"""
        # 创建book文件夹（如果不存在）
        if not os.path.exists(self.book_folder):
            os.makedirs(self.book_folder)
            
        # 加载书架数据
        self.load_bookshelf_data()
        
    def load_bookshelf_data(self):
        """加载书架数据"""
        if os.path.exists(self.bookshelf_data_file):
            try:
                with open(self.bookshelf_data_file, 'r', encoding='utf-8') as f:
                    self.books_data = json.load(f)
            except Exception as e:
                self.books_data = {}
                QMessageBox.warning(self, '警告', f'加载书架数据失败：{str(e)}')
        else:
            self.books_data = {}
            
    def save_bookshelf_data(self):
        """保存书架数据"""
        try:
            with open(self.bookshelf_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.books_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存书架数据失败：{str(e)}')
            
    def import_book(self):
        """导入书籍到书架"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择要导入的txt文件',
            '',
            'Text files (*.txt);;All files (*)'
        )
        
        if not file_path:
            return
            
        try:
            # 获取文件名（不含路径）
            file_name = os.path.basename(file_path)
            book_name = os.path.splitext(file_name)[0]  # 去掉扩展名作为默认书名
            
            # 询问用户是否要自定义书名
            custom_name, ok = QInputDialog.getText(
                self, 
                '设置书名', 
                f'请输入书名（默认：{book_name}）：',
                text=book_name
            )
            
            if ok and custom_name.strip():
                book_name = custom_name.strip()
                
            # 检查书名是否已存在
            if book_name in self.books_data:
                reply = QMessageBox.question(
                    self, 
                    '书名冲突', 
                    f'书架中已存在名为"{book_name}"的书籍，是否覆盖？',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
                    
            # 生成唯一的文件名（使用时间戳避免冲突）
            import time
            timestamp = str(int(time.time()))
            target_filename = f"{timestamp}_{file_name}"
            target_path = os.path.join(self.book_folder, target_filename)
            
            # 复制文件到book文件夹
            shutil.copy2(file_path, target_path)
            
            # 保存书籍信息
            self.books_data[book_name] = {
                'file_path': target_path,
                'original_name': file_name,
                'import_time': timestamp,
                'display_name': book_name
            }
            
            # 保存数据并刷新显示
            self.save_bookshelf_data()
            self.refresh_bookshelf()
            
            QMessageBox.information(self, '成功', f'书籍"{book_name}"已成功导入书架！')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导入书籍失败：{str(e)}')
            
    def refresh_bookshelf(self):
        """刷新书架显示"""
        self.book_list.clear()
        
        if not self.books_data:
            self.bookshelf_status_label.setText('书架为空，请导入书籍')
            self.bookshelf_status_label.show()
            return
            
        self.bookshelf_status_label.hide()
        
        # 添加书籍到列表
        for book_name, book_info in self.books_data.items():
            # 创建列表项
            item = QListWidgetItem()
            item.setData(Qt.UserRole, book_info)  # 存储书籍信息
            
            # 创建自定义组件
            book_widget = BookItemWidget(book_name, book_info)
            
            # 连接信号
            book_widget.continue_reading.connect(self.continue_reading_from_shelf)
            book_widget.start_reading.connect(self.start_reading_from_shelf)
            book_widget.rename_book.connect(self.rename_book_from_widget)
            book_widget.delete_book.connect(self.delete_book_from_widget)
            book_widget.show_contents.connect(self.show_book_contents)
            
            # 添加到列表
            self.book_list.addItem(item)
            item.setSizeHint(book_widget.sizeHint())
            self.book_list.setItemWidget(item, book_widget)
            
    def show_book_context_menu(self, position):
        """显示书籍右键菜单"""
        item = self.book_list.itemAt(position)
        if not item:
            return
            
        menu = QMenu(self)
        
        # 阅读书籍
        read_action = QAction('阅读', self)
        read_action.triggered.connect(lambda: self.read_book_from_shelf(item))
        menu.addAction(read_action)
        
        menu.addSeparator()
        
        # 重命名书籍
        rename_action = QAction('重命名', self)
        rename_action.triggered.connect(lambda: self.rename_book(item))
        menu.addAction(rename_action)
        
        # 删除书籍
        delete_action = QAction('删除', self)
        delete_action.triggered.connect(lambda: self.delete_book(item))
        menu.addAction(delete_action)
        
        menu.exec_(self.book_list.mapToGlobal(position))
        
    def read_book_from_shelf(self, item):
        """从书架阅读书籍"""
        if isinstance(item, QListWidgetItem):
            book_info = item.data(Qt.UserRole)
            file_path = book_info['file_path']
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                QMessageBox.warning(self, '警告', '书籍文件不存在，可能已被删除！')
                return
                
            # 设置选中的文件并开始阅读
            self.selected_file = file_path
            self.start_reading()
            
    def rename_book(self, item):
        """重命名书籍"""
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self, 
            '重命名书籍', 
            '请输入新的书名：',
            text=old_name
        )
        
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            # 检查新名称是否已存在
            if new_name in self.books_data:
                QMessageBox.warning(self, '警告', '该书名已存在，请选择其他名称！')
                return
                
            # 更新书籍数据
            book_info = self.books_data.pop(old_name)
            book_info['display_name'] = new_name
            self.books_data[new_name] = book_info
            
            # 保存数据并刷新显示
            self.save_bookshelf_data()
            self.refresh_bookshelf()
            
    def delete_book(self, item):
        """删除书籍"""
        book_name = item.text()
        reply = QMessageBox.question(
            self, 
            '确认删除', 
            f'确定要删除书籍"{book_name}"吗？\n\n注意：这将同时删除书架记录和文件！',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 获取文件路径并删除文件
                book_info = self.books_data[book_name]
                file_path = book_info['file_path']
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
                # 从数据中删除记录
                del self.books_data[book_name]
                
                # 保存数据并刷新显示
                self.save_bookshelf_data()
                self.refresh_bookshelf()
                
                QMessageBox.information(self, '成功', f'书籍"{book_name}"已删除！')
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除书籍失败：{str(e)}')
                
    def update_continue_button_state(self):
        """更新继续阅读按钮状态"""
        # 检查是否有历史记录
        has_history = self.history_manager.has_history()
        self.continue_button.setEnabled(has_history)
        
        if has_history:
            # 获取最后阅读的书籍信息
            last_book = self.history_manager.get_last_read_book()
            if last_book and last_book.get('file_path'):
                file_path = last_book['file_path']
                
                # 尝试从书架数据中获取书名
                book_name = None
                for name, info in self.books_data.items():
                    if info.get('file_path') == file_path:
                        book_name = name
                        break
                
                # 如果在书架中找不到，使用文件名（去掉时间戳和扩展名）
                if not book_name:
                    filename = os.path.basename(file_path)
                    # 移除时间戳前缀（格式：数字_文件名.扩展名）
                    if '_' in filename:
                        book_name = '_'.join(filename.split('_')[1:])  # 去掉时间戳部分
                    else:
                        book_name = filename
                    # 移除扩展名
                    if '.' in book_name:
                        book_name = '.'.join(book_name.split('.')[:-1])
                
                # 显示当前阅读的书籍
                if book_name:
                    # 如果书名太长，截断显示
                    display_name = book_name if len(book_name) <= 20 else book_name[:20] + '...'
                    self.current_book_label.setText(f'当前阅读：《{display_name}》')
                    self.current_book_label.setVisible(True)
                else:
                    self.current_book_label.setVisible(False)
            else:
                self.current_book_label.setVisible(False)
        else:
            self.current_book_label.setVisible(False)
            
        # 继续阅读按钮始终显示固定文本
        self.continue_button.setText('继续阅读')
        
    def continue_reading(self):
        """继续阅读上次的文件"""
        last_file = self.history_manager.get_last_file()
        if not last_file:
            QMessageBox.information(self, '提示', '没有找到阅读历史记录！')
            return
            
        if not os.path.exists(last_file):
            QMessageBox.warning(self, '警告', '上次阅读的文件不存在，可能已被删除或移动！')
            return
            
        # 设置选中的文件并开始阅读
        self.selected_file = last_file
        self.start_reading()
        
    def continue_reading_from_shelf(self, book_info):
        """从书架继续阅读"""
        file_path = book_info.get('file_path')
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, '警告', '文件不存在，可能已被删除或移动！')
            return
            
        self.selected_file = file_path
        self.start_reading()
        
    def start_reading_from_shelf(self, book_info):
        """从书架从头开始阅读"""
        file_path = book_info.get('file_path')
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, '警告', '文件不存在，可能已被删除或移动！')
            return
            
        # 清除该书籍的历史记录
        self.history_manager.remove_book(file_path)
        
        # 直接启动阅读，不恢复历史位置
        self.start_reading_without_history(file_path)
        
    def rename_book_from_widget(self, book_info):
        """从组件重命名书籍"""
        old_name = book_info.get('name', '')
        new_name, ok = QInputDialog.getText(
            self, '重命名书籍', '请输入新的书籍名称：', text=old_name
        )
        
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            
            # 检查名称是否已存在
            if new_name in self.books_data:
                QMessageBox.warning(self, '警告', '该书籍名称已存在！')
                return
                
            try:
                # 更新书籍数据
                book_data = self.books_data.pop(old_name)
                book_data['name'] = new_name
                self.books_data[new_name] = book_data
                
                # 保存数据并刷新显示
                self.save_bookshelf_data()
                self.refresh_bookshelf()
                
                QMessageBox.information(self, '成功', f'书籍已重命名为：{new_name}')
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'重命名失败：{str(e)}')
                
    def delete_book_from_widget(self, book_info):
        """从组件删除书籍"""
        book_name = book_info.get('name', '')
        file_path = book_info.get('file_path', '')
        
        reply = QMessageBox.question(
            self, '确认删除', 
            f'确定要删除书籍《{book_name}》吗？\n\n注意：这只会从书架中移除，不会删除原文件。',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 从书架数据中移除
                if book_name in self.books_data:
                    del self.books_data[book_name]
                    
                # 从历史记录中移除
                if file_path:
                    self.history_manager.remove_book(file_path)
                    
                # 保存数据并刷新显示
                self.save_bookshelf_data()
                self.refresh_bookshelf()
                self.update_continue_button_state()
                
                QMessageBox.information(self, '成功', '书籍已从书架中移除！')
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除书籍失败：{str(e)}')
                
    def show_book_contents(self, book_info):
        """显示书籍目录"""
        from contents_window import ContentsWindow
        
        # 创建目录窗口
        contents_window = ContentsWindow(book_info, self)
        
        # 连接章节选择信号，使用 lambda 传递书籍信息
        contents_window.chapter_selected.connect(
            lambda chapter_info: self.open_book_at_chapter(chapter_info, book_info)
        )
        
        # 显示目录窗口
        contents_window.exec_()
        
    def open_book_at_chapter(self, chapter_info, book_info=None):
        """从指定章节开始阅读"""
        print(f"[调试] 开始处理章节跳转请求")
        print(f"[调试] 接收到的章节信息: {chapter_info}")
        
        # 如果没有传入书籍信息，尝试从当前选中项获取
        if book_info is None:
            current_item = self.book_list.currentItem()
            if not current_item:
                print("[调试] 跳转失败: 没有选中的书籍")
                return
                
            book_info = current_item.data(Qt.UserRole)
            if not book_info:
                print("[调试] 跳转失败: 书籍信息为空")
                return
            
        file_path = book_info['file_path']
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            QMessageBox.warning(self, '文件不存在', f'文件不存在：{file_path}')
            return
            
        # 使用智能编码检测读取文件
        content, encoding = detect_encoding_and_read_file(file_path)
        
        if content is None:
            QMessageBox.critical(self, '错误', '无法读取文件，可能是编码问题或文件损坏！')
            return
            
        if not content.strip():
            QMessageBox.warning(self, '警告', '文件内容为空！')
            return
            
        # 隐藏主窗口
        self.hide()
        
        # 创建阅读器窗口，禁用历史位置恢复以便跳转到指定章节
        file_title = book_info.get('display_name', os.path.basename(file_path))
        reader = ReaderWindow(content, self.config_manager, self, 
                            file_path=file_path, title=file_title, restore_position=False)
        
        # 显示阅读器窗口
        reader.show()
        
        # 使用 QTimer 延迟跳转到指定章节位置，确保窗口完全初始化后再跳转
        from PyQt5.QtCore import QTimer
        def delayed_jump():
            print(f"[调试] 延迟跳转函数被调用")
            # 确保阅读器窗口已经完全显示和初始化
            if reader.isVisible() and hasattr(reader, 'text_lines') and reader.text_lines:
                print(f"[调试] 阅读器窗口已初始化，开始执行跳转")
                if 'char_position' in chapter_info:
                    print(f"[调试] 使用字符位置跳转: {chapter_info['char_position']}")
                    reader.jump_to_position(chapter_info['char_position'])
                elif 'line_number' in chapter_info:
                    print(f"[调试] 使用行号跳转: {chapter_info['line_number']}")
                    reader.jump_to_line(chapter_info['line_number'])
                else:
                    print(f"[调试] 跳转失败: 章节信息中没有位置数据")
            else:
                print(f"[调试] 阅读器窗口还未完全初始化，再次延迟")
                print(f"[调试] 窗口可见性: {reader.isVisible()}, 有文本行: {hasattr(reader, 'text_lines') and reader.text_lines}")
                # 如果窗口还没有完全初始化，再延迟一点时间
                QTimer.singleShot(200, delayed_jump)
        
        print(f"[调试] 设置延迟跳转定时器，500毫秒后执行")
        QTimer.singleShot(500, delayed_jump)  # 延迟500毫秒执行跳转，确保窗口完全初始化
        
        # 保存阅读器窗口引用，以便后续管理
        self.reader_window = reader
        
    def center_window(self):
        """将窗口居中显示"""
        screen = QApplication.desktop().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
        
    def select_file(self):
        """选择txt文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择txt文件',
            '',
            'Text files (*.txt);;All files (*)'
        )
        
        if file_path:
            self.selected_file = file_path
            # 显示文件名（不显示完整路径）
            file_name = os.path.basename(file_path)
            self.file_label.setText(f'已选择文件：\n{file_name}')
            self.file_label.setStyleSheet(
                'border: 2px solid #27ae60; '
                'padding: 20px; '
                'border-radius: 8px; '
                'background-color: #d5f4e6; '
                'color: #27ae60;'
            )
            self.read_button.setEnabled(True)
            
    def start_reading(self):
        """开始阅读 - 隐藏主窗口并显示阅读窗口"""
        if not self.selected_file:
            QMessageBox.warning(self, '警告', '请先选择一个txt文件！')
            return
            
        # 使用智能编码检测读取文件
        content, encoding = detect_encoding_and_read_file(self.selected_file)
        
        if content is None:
            QMessageBox.critical(self, '错误', '无法读取文件，可能是编码问题或文件损坏！')
            return
            
        if not content.strip():
            QMessageBox.warning(self, '警告', '文件内容为空！')
            return
            
        # 隐藏主窗口
        self.hide()
        
        # 创建并显示阅读窗口
        # 获取文件名作为标题
        file_title = os.path.basename(self.selected_file)
        self.reader_window = ReaderWindow(content, self.config_manager, self, 
                                        file_path=self.selected_file, title=file_title)
        self.reader_window.show()
        
    def start_reading_without_history(self, file_path):
        """从头开始阅读，不恢复历史位置"""
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, '警告', '文件不存在！')
            return
            
        # 使用智能编码检测读取文件
        content, encoding = detect_encoding_and_read_file(file_path)
        
        if content is None:
            QMessageBox.critical(self, '错误', '无法读取文件，可能是编码问题或文件损坏！')
            return
            
        if not content.strip():
            QMessageBox.warning(self, '警告', '文件内容为空！')
            return
            
        # 隐藏主窗口
        self.hide()
        
        # 创建并显示阅读窗口，不恢复历史位置
        file_title = os.path.basename(file_path)
        self.reader_window = ReaderWindow(content, self.config_manager, self, 
                                        file_path=file_path, title=file_title, restore_position=False)
        self.reader_window.show()
        
    def show_main_window(self):
        """显示主窗口（从阅读窗口返回时调用）"""
        self.show()
        # 刷新书架显示（以防在阅读期间有文件变化）
        self.refresh_bookshelf()
        # 更新继续阅读按钮状态
        self.update_continue_button_state()
        self.raise_()
        self.activateWindow()
        
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 检查系统是否支持托盘图标
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "系统托盘", "系统不支持托盘图标功能")
            return
            
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建一个简单的图标（绿色圆点）
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.green)
        painter.setPen(Qt.darkGreen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("ReadFish")
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        # 显示主窗口动作
        show_action = QAction("显示主窗口", self)
        show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(show_action)
        
        # 分隔符
        tray_menu.addSeparator()
        
        # 退出动作
        quit_action = QAction("退出程序", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 双击托盘图标显示主窗口
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        
    def tray_icon_activated(self, reason):
        """托盘图标被激活时的处理"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_main_window()
            
    def quit_application(self):
        """退出应用程序"""
        # 停止阅读窗口的定时器
        if self.reader_window:
            self.reader_window.close()
        
        # 隐藏托盘图标
        if self.tray_icon:
            self.tray_icon.hide()
            
        # 退出应用程序
        QApplication.quit()
        
    def closeEvent(self, event):
        """主窗口关闭事件 - 隐藏到托盘而不是退出"""
        if self.tray_icon and self.tray_icon.isVisible():
            # 如果托盘图标可见，隐藏主窗口到托盘
            self.hide()
            event.ignore()
        else:
            # 如果没有托盘图标，正常退出
            self.quit_application()
            event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName('ReadFish')
    app.setApplicationVersion('1.0')
    app.setOrganizationName('ReadFish')
    
    # 设置应用程序在最后一个窗口关闭时不自动退出
    # 这样即使所有窗口都隐藏了，程序也会继续运行（通过托盘图标维持）
    app.setQuitOnLastWindowClosed(False)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()