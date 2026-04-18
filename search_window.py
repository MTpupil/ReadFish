#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全文搜索窗口 - 支持关键词搜索和结果显示 - 性能优化版
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

from file_utils import detect_encoding_and_read_file, read_file_content
from table_of_contents import TableOfContents


class SearchThread(QThread):
    """搜索线程 - 在后台执行搜索操作 - 性能优化版"""
    
    # 定义信号
    search_progress = pyqtSignal(int)  # 搜索进度信号
    search_result = pyqtSignal(dict)   # 单个搜索结果信号
    search_finished = pyqtSignal(int)  # 搜索完成信号，参数为总结果数
    search_error = pyqtSignal(str)     # 搜索错误信号
    
    def __init__(self, file_path, keyword, case_sensitive=False, whole_word=False, use_regex=False, start_line=1):
        super().__init__()
        self.file_path = file_path
        self.keyword = keyword
        self.case_sensitive = case_sensitive
        self.whole_word = whole_word
        self.use_regex = use_regex
        self.start_line = start_line  # 搜索起始行号
        self.is_cancelled = False
        self.chapters = []  # 存储章节信息
        
    def run(self):
        """执行搜索 - 性能优化版"""
        try:
            # 读取文件内容（支持TXT和EPUB）
            content, error_message = read_file_content(self.file_path)
            if content is None:
                self.search_error.emit(f'无法读取文件内容：{error_message}')
                return
                
            lines = content.split('\n')
            total_lines = len(lines)
            results_count = 0
            
            # 快速检查：如果关键词不存在于文本中，直接返回
            has_keyword = False
            if not self.use_regex:
                search_text = self.keyword if self.case_sensitive else self.keyword.lower()
                content_check = content if self.case_sensitive else content.lower()
                if search_text not in content_check:
                    self.search_progress.emit(100)
                    self.search_finished.emit(0)
                    return
            
            # 准备搜索模式
            search_pattern = self.prepare_search_pattern()
            if not search_pattern:
                self.search_error.emit('搜索模式无效')
                return
                
            # 逐行搜索，从start_line开始
            start_index = max(0, self.start_line - 1)  # 转换为0基索引
            
            # 性能优化：只在需要时解析章节信息
            need_chapters = self._need_chapter_info()
            
            if need_chapters:
                toc_parser = TableOfContents()
                self.chapters = toc_parser.parse_contents(content)
            
            # 性能优化：批量处理和减少进度更新
            progress_update_interval = max(100, total_lines // 100)  # 至少100行或1%
            
            for line_num in range(self.start_line, total_lines + 1):
                if self.is_cancelled:
                    break
                    
                # 更新进度 - 减少更新频率
                if line_num % progress_update_interval == 0:
                    progress = int(((line_num - self.start_line + 1) / (total_lines - self.start_line + 1)) * 100) if (total_lines - self.start_line + 1) > 0 else 100
                    self.search_progress.emit(progress)
                    
                line_index = line_num - 1
                line = lines[line_index]
                
                # 快速检查：先做简单的字符串包含检查，避免不必要的正则匹配
                if not self.use_regex:
                    search_text = self.keyword if self.case_sensitive else self.keyword.lower()
                    line_check = line if self.case_sensitive else line.lower()
                    if search_text not in line_check:
                        continue
                
                # 搜索匹配
                matches = self.find_matches_in_line(line, search_pattern)
                
                for match in matches:
                    if self.is_cancelled:
                        break
                        
                    # 获取当前行所在的章节
                    chapter_info = self.get_chapter_info(line_num) if need_chapters else {'chapter': 0, 'title': '未找到章节'}
                    
                    # 创建搜索结果
                    result = {
                        'line_number': line_num,
                        'chapter': chapter_info['chapter'],
                        'chapter_title': chapter_info['title'],
                        'line_content': line.strip(),
                        'match_start': match['start'],
                        'match_end': match['end'],
                        'match_text': match['text'],
                        'context_before': self.get_context_before_fast(lines, line_index, 50) if need_chapters else '',
                        'context_after': self.get_context_after_fast(lines, line_index, 50) if need_chapters else ''
                    }
                    
                    self.search_result.emit(result)
                    results_count += 1
                    
                    # 限制结果数量，避免内存溢出
                    if results_count >= 5000:  # 最多显示5000个结果（减少一半）
                        break
                        
                if results_count >= 5000:
                    break
                    
            # 搜索完成
            self.search_progress.emit(100)
            self.search_finished.emit(results_count)
            
        except Exception as e:
            self.search_error.emit(f'搜索过程中发生错误：{str(e)}')
            
    def _need_chapter_info(self):
        """判断是否需要获取章节信息 - 性能优化"""
        # 暂时不需要章节信息，避免每次都解析
        return False
            
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
        """在行中查找匹配项 - 性能优化版"""
        matches = []
        for match in pattern.finditer(line):
            matches.append({
                'start': match.start(),
                'end': match.end(),
                'text': match.group()
            })
        return matches
        
    def get_context_before_fast(self, lines, line_index, max_chars):
        """获取前文上下文 - 简化版"""
        if line_index <= 0:
            return ''
        return lines[max(0, line_index - 3):line_index][-1] if line_index > 0 else ''
        
    def get_context_after_fast(self, lines, line_index, max_chars):
        """获取后文上下文 - 简化版"""
        if line_index >= len(lines) - 1:
            return ''
        return lines[line_index + 1:min(len(lines), line_index + 4)][0] if line_index < len(lines) - 1 else ''
        
    def get_chapter_info(self, line_num):
        """获取指定行号所在的章节信息 - 性能优化版"""
        if not self.chapters:
            return {'chapter': 0, 'title': '未找到章节'}
            
        # 使用二分查找快速定位章节
        left, right = 0, len(self.chapters) - 1
        current_chapter = 0
        chapter_title = '未找到章节'
        
        while left <= right:
            mid = (left + right) // 2
            if self.chapters[mid]['line_number'] <= line_num:
                current_chapter = mid + 1
                chapter_title = self.chapters[mid]['title']
                left = mid + 1
            else:
                right = mid - 1
        
        return {'chapter': current_chapter, 'title': chapter_title}
        
    def cancel(self):
        """取消搜索"""
        self.is_cancelled = True


class SearchWindow(QDialog):
    """全文搜索窗口"""
    
    # 定义信号
    search_result_selected = pyqtSignal(int)  # 搜索结果选择信号，参数为行号
    
    def __init__(self, file_path, title, current_line=0, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.book_title = title
        self.current_line = current_line  # 当前阅读位置的行号
        self.search_thread = None
        self.search_results = []  # 存储搜索结果
        self.current_page = 0     # 当前页码
        self.page_size = 50       # 每页显示数量
        self.auto_close_after_jump = True  # 跳转后自动关闭配置
        
        self.init_ui()
    
    def format_book_title(self, title):
        """格式化书籍标题，去掉时间戳和扩展名，并加上书名号"""
        if not title:
            return "未知书籍"
        
        if '_' in title:
            book_name = '_'.join(title.split('_')[1:])
        else:
            book_name = title
        
        if '.' in book_name:
            book_name = '.'.join(book_name.split('.')[:-1])
        
        return f'《{book_name}》'
        
    def init_ui(self):
        """初始化用户界面"""
        formatted_title = self.format_book_title(self.book_title)
        self.setWindowTitle(f'全文搜索 - {formatted_title}')
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        if os.path.exists('logo.ico'):
            self.setWindowIcon(QIcon('logo.ico'))
        elif os.path.exists('logo.png'):
            self.setWindowIcon(QIcon('logo.png'))
        elif os.path.exists('logo.svg'):
            self.setWindowIcon(QIcon('logo.svg'))
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        self.create_search_area(main_layout)
        
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        self.create_results_area(splitter)
        
        self.create_preview_area(splitter)
        
        splitter.setSizes([400, 200])
        
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
            "    padding: 5px;"
            "}"
        )
        
        search_layout = QVBoxLayout(search_frame)
        search_layout.setSpacing(5)
        
        input_layout = QHBoxLayout()
        
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
        
        options_layout = QHBoxLayout()
        
        self.case_sensitive_cb = QCheckBox('区分大小写')
        self.case_sensitive_cb.setFont(QFont('Microsoft YaHei', 9))
        
        self.whole_word_cb = QCheckBox('全词匹配')
        self.whole_word_cb.setFont(QFont('Microsoft YaHei', 9))
        
        self.regex_cb = QCheckBox('正则表达式')
        self.regex_cb.setFont(QFont('Microsoft YaHei', 9))
        
        self.search_after_current_cb = QCheckBox('只搜索当前位置之后')
        self.search_after_current_cb.setFont(QFont('Microsoft YaHei', 9))
        if self.current_line > 0:
            self.search_after_current_cb.setEnabled(True)
            self.search_after_current_cb.setChecked(True)
        else:
            self.search_after_current_cb.setEnabled(False)
        
        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        options_layout.addWidget(self.regex_cb)
        options_layout.addWidget(self.search_after_current_cb)
        options_layout.addStretch()
        
        search_layout.addLayout(options_layout)
        
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
        
        self.results_list.itemClicked.connect(self.on_result_clicked)
        self.results_list.itemDoubleClicked.connect(self.on_result_double_clicked)
        
        results_layout.addWidget(self.results_list)
        
        self.create_pagination_controls(results_layout)
        
        parent.addWidget(results_frame)
        
    def create_pagination_controls(self, layout):
        """创建分页控制"""
        pagination_layout = QHBoxLayout()
        
        self.prev_button = QPushButton('上一页')
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.prev_page)
        
        self.page_info = QLabel('第 0 页，共 0 页')
        self.page_info.setFont(QFont('Microsoft YaHei', 9))
        self.page_info.setAlignment(Qt.AlignCenter)
        
        self.next_button = QPushButton('下一页')
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.next_page)
        
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
        
        preview_title = QLabel('内容预览')
        preview_title.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        preview_title.setStyleSheet('color: #495057; padding: 5px;')
        preview_layout.addWidget(preview_title)
        
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
            "}"
        )
        self.auto_close_checkbox.toggled.connect(self.on_auto_close_toggled)
        
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
            
        self.search_results.clear()
        self.results_list.clear()
        self.current_page = 0
        self.update_pagination()
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.search_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.results_stats.setText('正在搜索...')
        
        start_line = 1
        if self.search_after_current_cb.isChecked() and self.search_after_current_cb.isEnabled():
            start_line = self.current_line
        
        self.search_thread = SearchThread(
            self.file_path,
            keyword,
            self.case_sensitive_cb.isChecked(),
            self.whole_word_cb.isChecked(),
            self.regex_cb.isChecked(),
            start_line
        )
        
        self.search_thread.search_progress.connect(self.update_progress)
        self.search_thread.search_result.connect(self.add_search_result)
        self.search_thread.search_finished.connect(self.search_completed)
        self.search_thread.search_error.connect(self.search_failed)
        
        self.search_thread.start()
        
    def cancel_search(self):
        """取消搜索"""
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.search_thread.wait(3000)
            
        self.search_completed(len(self.search_results))
        
    def update_progress(self, value):
        """更新搜索进度"""
        self.progress_bar.setValue(value)
        
    def add_search_result(self, result):
        """添加搜索结果"""
        self.search_results.append(result)
        
        if len(self.search_results) <= self.page_size:
            self.update_results_display()
            
    def search_completed(self, total_results):
        """搜索完成"""
        self.progress_bar.setVisible(False)
        self.search_button.setVisible(True)
        self.cancel_button.setVisible(False)
        
        if total_results == 0:
            self.results_stats.setText('未找到匹配结果')
        else:
            self.results_stats.setText(f'找到 {total_results} 个匹配结果')
            
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
            
        start_index = self.current_page * self.page_size
        end_index = min(start_index + self.page_size, len(self.search_results))
        
        for i in range(start_index, end_index):
            result = self.search_results[i]
            
            if result['chapter'] > 0:
                display_text = f"第 {result['chapter']} 章 - 第 {result['line_number']} 行：{result['line_content'][:100]}"
            else:
                display_text = f"第 {result['line_number']} 行：{result['line_content'][:100]}"
            if len(result['line_content']) > 100:
                display_text += '...'
                
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, result)
            
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
                self.current_page = 0
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
        if result['chapter'] > 0:
            preview_text = f"""章节：第 {result['chapter']} 章 - {result['chapter_title']}
位置：第 {result['line_number']} 行
匹配文本：{result['match_text']}

--- 匹配行 ---
{result['line_content']}"""
        else:
            preview_text = f"""位置：第 {result['line_number']} 行
匹配文本：{result['match_text']}

--- 匹配行 ---
{result['line_content']}"""
        
        self.preview_text.setPlainText(preview_text)
        
        cursor = self.preview_text.textCursor()
        format = QTextCharFormat()
        format.setBackground(QColor(255, 255, 0))
        
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
            self.search_result_selected.emit(result['line_number'])
            if self.auto_close_after_jump:
                self.close()
    
    def on_auto_close_toggled(self, checked):
        """自动关闭配置选项切换回调"""
        self.auto_close_after_jump = checked
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.cancel()
            self.search_thread.wait(3000)
            
        event.accept()
