#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全文搜索窗口 - 支持关键词搜索和结果显示
"""

import os
import re
import time
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QTextEdit, QFrame, QSplitter, QProgressBar, QComboBox, QCheckBox,
    QSpinBox, QGroupBox
)
from toast_notification import ToastManager
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont, QIcon, QTextCharFormat, QColor

from file_utils import detect_encoding_and_read_file


class SearchThread(QThread):
    """搜索线程 - 在后台执行搜索操作"""
    
    # 定义信号
    search_progress = pyqtSignal(int)  # 搜索进度信号
    search_result = pyqtSignal(dict)   # 单个搜索结果信号
    search_finished = pyqtSignal(int)  # 搜索完成信号，参数为总结果数
    search_error = pyqtSignal(str)     # 搜索错误信号
    
    def __init__(self, file_path, keyword, case_sensitive=False, whole_word=False, use_regex=False):
        super().__init__()
        self.file_path = file_path
        self.keyword = keyword
        self.case_sensitive = case_sensitive
        self.whole_word = whole_word
        self.use_regex = use_regex
        self.is_cancelled = False
        
    def run(self):
        """执行搜索"""
        try:
            # 读取文件内容
            result = detect_encoding_and_read_file(self.file_path)
            if not result or not result[0]:
                self.search_error.emit('无法读取文件内容')
                return
            
            content = result[0]  # 获取文件内容
                
            lines = content.split('\n')
            total_lines = len(lines)
            results_count = 0
            
            # 准备搜索模式
            search_pattern = self.prepare_search_pattern()
            if not search_pattern:
                self.search_error.emit('搜索模式无效')
                return
                
            # 逐行搜索
            for line_num, line in enumerate(lines, 1):
                if self.is_cancelled:
                    break
                    
                # 更新进度
                if line_num % 100 == 0:  # 每100行更新一次进度
                    progress = int((line_num / total_lines) * 100)
                    self.search_progress.emit(progress)
                    
                # 搜索匹配
                matches = self.find_matches_in_line(line, search_pattern)
                
                for match in matches:
                    if self.is_cancelled:
                        break
                        
                    # 创建搜索结果
                    result = {
                        'line_number': line_num,
                        'line_content': line.strip(),
                        'match_start': match['start'],
                        'match_end': match['end'],
                        'match_text': match['text'],
                        'context_before': self.get_context_before(lines, line_num - 1, 50),
                        'context_after': self.get_context_after(lines, line_num - 1, 50)
                    }
                    
                    self.search_result.emit(result)
                    results_count += 1
                    
                    # 限制结果数量，避免内存溢出
                    if results_count >= 10000:  # 最多显示10000个结果
                        break
                        
                if results_count >= 10000:
                    break
                    
            # 搜索完成
            self.search_progress.emit(100)
            self.search_finished.emit(results_count)
            
        except Exception as e:
            self.search_error.emit(f'搜索过程中发生错误：{str(e)}')
            
    def prepare_search_pattern(self):
        """准备搜索模式"""
        try:
            if self.use_regex:
                # 使用正则表达式
                flags = 0 if self.case_sensitive else re.IGNORECASE
                return re.compile(self.keyword, flags)
            else:
                # 普通文本搜索
                keyword = self.keyword
                if self.whole_word:
                    keyword = r'\b' + re.escape(keyword) + r'\b'
                else:
                    keyword = re.escape(keyword)
                    
                flags = 0 if self.case_sensitive else re.IGNORECASE
                return re.compile(keyword, flags)
        except re.error:
            return None
            
    def find_matches_in_line(self, line, pattern):
        """在行中查找匹配项"""
        matches = []
        for match in pattern.finditer(line):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group()
            })
        return matches
        
    def get_context_before(self, lines, line_index, max_chars):
        """获取前文上下文"""
        if line_index <= 0:
            return ''
            
        context = ''
        chars_count = 0
        
        for i in range(line_index - 1, -1, -1):
            line = lines[i].strip()
            if chars_count + len(line) > max_chars:
                # 截取部分内容
                remaining = max_chars - chars_count
                context = '...' + line[-remaining:] + '\n' + context
                break
            else:
                context = line + '\n' + context
                chars_count += len(line)
                
        return context.rstrip()
        
    def get_context_after(self, lines, line_index, max_chars):
        """获取后文上下文"""
        if line_index >= len(lines) - 1:
            return ''
            
        context = ''
        chars_count = 0
        
        for i in range(line_index + 1, len(lines)):
            line = lines[i].strip()
            if chars_count + len(line) > max_chars:
                # 截取部分内容
                remaining = max_chars - chars_count
                context = context + '\n' + line[:remaining] + '...'
                break
            else:
                context = context + '\n' + line
                chars_count += len(line)
                
        return context.lstrip()
        
    def cancel(self):
        """取消搜索"""
        self.is_cancelled = True


class SearchWindow(QDialog):
    """全文搜索窗口"""
    
    # 定义信号
    search_result_selected = pyqtSignal(int)  # 搜索结果选择信号，参数为行号
    
    def __init__(self, file_path, title, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.book_title = title
        self.search_thread = None
        self.search_results = []  # 存储搜索结果
        self.current_page = 0     # 当前页码
        self.page_size = 50       # 每页显示数量
        self.auto_close_after_jump = True  # 跳转后自动关闭配置
        
        self.init_ui()
    
    def format_book_title(self, title):
        """格式化书籍标题，去掉时间戳和扩展名，并加上书名号
        
        Args:
            title: 原始标题
            
        Returns:
            格式化后的标题
        """
        if not title:
            return "未知书籍"
        
        # 移除时间戳前缀（格式：数字_文件名.扩展名）
        if '_' in title:
            book_name = '_'.join(title.split('_')[1:])  # 去掉时间戳部分
        else:
            book_name = title
        
        # 移除扩展名
        if '.' in book_name:
            book_name = '.'.join(book_name.split('.')[:-1])
        
        # 添加书名号
        return f'《{book_name}》'
        
    def init_ui(self):
        """初始化用户界面"""
        formatted_title = self.format_book_title(self.book_title)
        self.setWindowTitle(f'全文搜索 - {formatted_title}')
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
        
        # 搜索区域
        self.create_search_area(main_layout)
        
        # 分割器 - 上方结果列表，下方预览
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # 上方：搜索结果列表
        self.create_results_area(splitter)
        
        # 下方：结果预览
        self.create_preview_area(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 200])
        
        # 状态和按钮区域
        self.create_status_area(main_layout)
        
    def create_search_area(self, layout):
        """创建搜索区域"""
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.StyledPanel)
        search_frame.setStyleSheet(
            "QFrame {"
            "    background-color: #f8f9fa;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 5px;"
            "    padding: 10px;"
            "}"
        )
        
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(10)
        
        # 标题
        formatted_title = self.format_book_title(self.book_title)
        title_label = QLabel(f'在 {formatted_title} 中搜索')
        title_label.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        title_label.setStyleSheet('color: #2c3e50; background: transparent; border: none;')
        search_layout.addWidget(title_label)
        
        # 搜索输入区域
        input_layout = QHBoxLayout()
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('请输入搜索关键词...')
        self.search_input.setFont(QFont('Microsoft YaHei', 10))
        self.search_input.setStyleSheet(
            "QLineEdit {"
            "    border: 2px solid #ced4da;"
            "    border-radius: 4px;"
            "    padding: 8px;"
            "    background-color: white;"
            "}"
            "QLineEdit:focus {"
            "    border-color: #007bff;"
            "}"
        )
        self.search_input.returnPressed.connect(self.start_search)
        
        # 搜索按钮
        self.search_button = QPushButton('搜索')
        self.search_button.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        self.search_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #007bff;"
            "    color: white;"
            "    border: none;"
            "    padding: 8px 20px;"
            "    border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #0056b3;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #004085;"
            "}"
            "QPushButton:disabled {"
            "    background-color: #6c757d;"
            "}"
        )
        self.search_button.clicked.connect(self.start_search)
        
        # 取消按钮
        self.cancel_button = QPushButton('取消')
        self.cancel_button.setFont(QFont('Microsoft YaHei', 10))
        self.cancel_button.setStyleSheet(
            "QPushButton {"
            "    background-color: #dc3545;"
            "    color: white;"
            "    border: none;"
            "    padding: 8px 20px;"
            "    border-radius: 4px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #c82333;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #bd2130;"
            "}"
        )
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_search)
        
        input_layout.addWidget(self.search_input)
        input_layout.addWidget(self.search_button)
        input_layout.addWidget(self.cancel_button)
        
        search_layout.addLayout(input_layout)
        
        # 搜索选项
        options_layout = QHBoxLayout()
        
        self.case_sensitive_cb = QCheckBox('区分大小写')
        self.case_sensitive_cb.setFont(QFont('Microsoft YaHei', 9))
        
        self.whole_word_cb = QCheckBox('全词匹配')
        self.whole_word_cb.setFont(QFont('Microsoft YaHei', 9))
        
        self.regex_cb = QCheckBox('正则表达式')
        self.regex_cb.setFont(QFont('Microsoft YaHei', 9))
        
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        options_layout.addWidget(self.regex_cb)
        options_layout.addStretch()
        
        search_layout.addLayout(options_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    text-align: center;"
            "}"
            "QProgressBar::chunk {"
            "    background-color: #007bff;"
            "    border-radius: 3px;"
            "}"
        )
        search_layout.addWidget(self.progress_bar)
        
        layout.addWidget(search_frame)
        
    def create_results_area(self, parent):
        """创建搜索结果区域"""
        results_frame = QFrame()
        results_frame.setFrameStyle(QFrame.StyledPanel)
        
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(5, 5, 5, 5)
        
        # 结果标题和统计
        header_layout = QHBoxLayout()
        
        results_title = QLabel('搜索结果')
        results_title.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        results_title.setStyleSheet('color: #495057;')
        
        self.results_stats = QLabel('请输入关键词开始搜索')
        self.results_stats.setFont(QFont('Microsoft YaHei', 9))
        self.results_stats.setStyleSheet('color: #6c757d;')
        
        header_layout.addWidget(results_title)
        header_layout.addStretch()
        header_layout.addWidget(self.results_stats)
        
        results_layout.addLayout(header_layout)
        
        # 搜索结果列表
        self.results_list = QListWidget()
        self.results_list.setStyleSheet(
            "QListWidget {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: white;"
            "    selection-background-color: #007bff;"
            "    selection-color: white;"
            "}"
            "QListWidget::item {"
            "    padding: 10px;"
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
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        
        results_layout.addWidget(self.results_list)
        
        # 分页控制
        self.create_pagination_controls(results_layout)
        
        parent.addWidget(results_frame)
        
    def create_pagination_controls(self, layout):
        """创建分页控制"""
        pagination_layout = QHBoxLayout()
        
        # 上一页按钮
        self.prev_button = QPushButton('上一页')
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.prev_page)
        
        # 页码信息
        self.page_info = QLabel('第 0 页，共 0 页')
        self.page_info.setFont(QFont('Microsoft YaHei', 9))
        self.page_info.setAlignment(Qt.AlignCenter)
        
        # 下一页按钮
        self.next_button = QPushButton('下一页')
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_page)
        
        # 每页显示数量
        page_size_label = QLabel('每页显示：')
        page_size_label.setFont(QFont('Microsoft YaHei', 9))
        
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(['25', '50', '100', '200'])
        self.page_size_combo.setCurrentText('50')
        self.page_size_combo.currentTextChanged.connect(self.change_page_size)
        
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.page_info)
        pagination_layout.addStretch()
        pagination_layout.addWidget(page_size_label)
        pagination_layout.addWidget(self.page_size_combo)
        pagination_layout.addWidget(self.next_button)
        
        layout.addLayout(pagination_layout)
        
    def create_preview_area(self, parent):
        """创建预览区域"""
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.StyledPanel)
        
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        # 预览标题
        preview_title = QLabel('内容预览')
        preview_title.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        preview_title.setStyleSheet('color: #495057; padding: 5px;')
        preview_layout.addWidget(preview_title)
        
        # 预览内容
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(
            "QTextEdit {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: #f8f9fa;"
            "    color: #495057;"
            "    font-family: 'Microsoft YaHei';"
            "    font-size: 10pt;"
            "    padding: 10px;"
            "}"
        )
        self.preview_text.setPlainText('请选择一个搜索结果查看内容预览')
        preview_layout.addWidget(self.preview_text)
        
        parent.addWidget(preview_frame)
        
    def create_status_area(self, layout):
        """创建状态和按钮区域"""
        status_layout = QHBoxLayout()
        
        # 跳转按钮
        self.goto_button = QPushButton('跳转到位置')
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
        self.goto_button.clicked.connect(self.goto_result)
        
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
        
        status_layout.addWidget(self.goto_button)
        status_layout.addStretch()
        status_layout.addWidget(self.auto_close_checkbox)
        status_layout.addWidget(close_button)
        
        layout.addLayout(status_layout)
        
    def start_search(self):
        """开始搜索"""
        keyword = self.search_input.text().strip()
        if not keyword:
            ToastManager.show_warning('请输入搜索关键词！', self)
            return
            
        # 清空之前的结果
        self.search_results.clear()
        self.results_list.clear()
        self.current_page = 0
        self.update_pagination()
        
        # 显示进度条和取消按钮
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.results_stats.setText('正在搜索...')
        
        # 创建搜索线程
        self.search_thread = SearchThread(
            self.file_path,
            keyword,
            self.case_sensitive_cb.isChecked(),
            self.whole_word_cb.isChecked(),
            self.regex_cb.isChecked()
        )
        
        # 连接信号
        self.search_thread.search_progress.connect(self.update_progress)
        self.search_thread.search_result.connect(self.add_search_result)
        self.search_thread.search_finished.connect(self.search_completed)
        self.search_thread.search_error.connect(self.search_failed)
        
        # 启动搜索
        self.search_thread.start()
        
    def cancel_search(self):
        """取消搜索"""
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.search_thread.wait(3000)  # 等待最多3秒
            
        self.search_completed(len(self.search_results))
        
    def update_progress(self, value):
        """更新搜索进度"""
        self.progress_bar.setValue(value)
        
    def add_search_result(self, result):
        """添加搜索结果"""
        self.search_results.append(result)
        
        # 如果是第一页的结果，立即显示
        if len(self.search_results) <= self.page_size:
            self.update_results_display()
            
    def search_completed(self, total_results):
        """搜索完成"""
        # 隐藏进度条和取消按钮
        self.progress_bar.setVisible(False)
        self.search_button.setVisible(True)
        self.cancel_button.setVisible(False)
        
        # 更新统计信息
        if total_results == 0:
            self.results_stats.setText('未找到匹配结果')
        else:
            self.results_stats.setText(f'找到 {total_results} 个匹配结果')
            
        # 更新显示
        self.update_results_display()
        self.update_pagination()
        
    def search_failed(self, error_msg):
        """搜索失败"""
        self.search_completed(0)
        ToastManager.show_error(f'搜索错误：{error_msg}', self)
        
    def update_results_display(self):
        """更新结果显示"""
        self.results_list.clear()
        
        if not self.search_results:
            return
            
        # 计算当前页的结果范围
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.search_results))
        
        # 显示当前页的结果
        for i in range(start_index, end_index):
            result = self.search_results[i]
            
            # 创建显示文本
            display_text = f"第 {result['line_number']} 行：{result['line_content'][:100]}"
            if len(result['line_content']) > 100:
                display_text += '...'
                
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, result)  # 存储完整结果数据
            item.setToolTip(f"匹配文本：{result['match_text']}")
            
            self.results_list.addItem(item)
            
    def update_pagination(self):
        """更新分页控制"""
        total_results = len(self.search_results)
        total_pages = (total_results + self.page_size - 1) // self.page_size if total_results > 0 else 0
        current_page_display = self.current_page + 1 if total_pages > 0 else 0
        
        self.page_info.setText(f'第 {current_page_display} 页，共 {total_pages} 页')
        
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)
        
    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_results_display()
            self.update_pagination()
            
    def next_page(self):
        """下一页"""
        total_pages = (len(self.search_results) + self.page_size - 1) // self.page_size
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_results_display()
            self.update_pagination()
            
    def change_page_size(self, size_text):
        """改变每页显示数量"""
        try:
            new_size = int(size_text)
            if new_size != self.page_size:
                self.page_size = new_size
                self.current_page = 0  # 重置到第一页
                self.update_results_display()
                self.update_pagination()
        except ValueError:
            pass
            
    def on_result_clicked(self, item):
        """搜索结果点击事件"""
        result = item.data(Qt.UserRole)
        if result:
            self.show_result_preview(result)
            self.goto_button.setEnabled(True)
            
    def on_result_double_clicked(self, item):
        """搜索结果双击事件 - 直接跳转"""
        result = item.data(Qt.UserRole)
        if result:
            self.goto_result()
            
    def show_result_preview(self, result):
        """显示搜索结果预览"""
        # 构建预览文本
        preview_text = f"""位置：第 {result['line_number']} 行
匹配文本：{result['match_text']}

--- 前文 ---
{result['context_before']}

--- 匹配行 ---
{result['line_content']}

--- 后文 ---
{result['context_after']}"""
        
        self.preview_text.setPlainText(preview_text)
        
        # 高亮匹配文本（简单实现）
        cursor = self.preview_text.textCursor()
        format = QTextCharFormat()
        format.setBackground(QColor(255, 255, 0))  # 黄色背景
        
        # 查找并高亮匹配文本
        text = self.preview_text.toPlainText()
        match_text = result['match_text']
        start = text.find(match_text)
        
        while start != -1:
            cursor.setPosition(start)
            cursor.setPosition(start + len(match_text), cursor.KeepAnchor)
            cursor.setCharFormat(format)
            start = text.find(match_text, start + 1)
            
    def goto_result(self):
        """跳转到选中的搜索结果"""
        current_item = self.results_list.currentItem()
        if not current_item:
            return
            
        result = current_item.data(Qt.UserRole)
        if result:
            # 发送跳转信号
            self.search_result_selected.emit(result['line_number'])
            # 根据配置决定是否自动关闭窗口
            if self.auto_close_after_jump:
                self.close()
    
    def on_auto_close_toggled(self, checked):
        """自动关闭配置选项切换回调"""
        self.auto_close_after_jump = checked
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 取消正在进行的搜索
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.search_thread.wait(3000)
            
        event.accept()