# -*- coding: utf-8 -*-
"""
目录显示窗口
显示书籍的章节目录，支持跳转到指定章节
"""

import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QListWidget, QListWidgetItem, QMessageBox, QProgressBar,
    QSplitter, QTextEdit, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from table_of_contents import TableOfContents
from file_utils import detect_encoding_and_read_file, read_file_content


class ContentsParseThread(QThread):
    """目录解析线程"""
    
    # 定义信号
    parse_finished = pyqtSignal(list)  # 解析完成信号
    parse_progress = pyqtSignal(int)   # 解析进度信号
    parse_error = pyqtSignal(str)      # 解析错误信号
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.toc_parser = TableOfContents()
        
    def run(self):
        """运行解析任务"""
        try:
            self.parse_progress.emit(10)
            
            # 智能读取文件内容，尝试多种编码
            content, encoding = self._read_file_with_encoding_detection()
            if content is None:
                self.parse_error.emit("无法读取文件，可能是编码问题或文件损坏")
                return
                
            self.parse_progress.emit(30)
            
            # 解析目录
            chapters = self.toc_parser.parse_contents(content)
            
            self.parse_progress.emit(100)
            
            # 发送解析结果
            self.parse_finished.emit(chapters)
            
        except Exception as e:
            self.parse_error.emit(str(e))
            
    def _read_file_with_encoding_detection(self):
        """智能检测文件编码并读取内容（支持TXT和EPUB）"""
        content, error_message = read_file_content(self.file_path)
        if content is None:
            raise Exception(f"无法读取文件：{error_message}")
        return content, None  # 返回内容，编码信息设为None


class ContentsWindow(QDialog):
    """目录显示窗口"""
    
    # 定义信号
    chapter_selected = pyqtSignal(dict)  # 章节选择信号
    
    def __init__(self, book_info, parent=None):
        super().__init__(parent)
        self.book_info = book_info
        self.chapters = []
        self.parse_thread = None
        
        self.init_ui()
        self.start_parsing()
        
    def init_ui(self):
        """初始化用户界面"""
        # 获取书籍名称，优先使用 display_name，然后是 name，最后从文件路径解析
        book_name = self.book_info.get('display_name') or self.book_info.get('name', '')
        if not book_name or book_name == '未知书籍':
            # 从文件路径中提取文件名（不含扩展名）
            file_path = self.book_info.get('file_path', '')
            if file_path:
                filename = os.path.basename(file_path)
                book_name = os.path.splitext(filename)[0]
                
                # 去掉时间戳前缀（格式：数字_文件名.扩展名）
                if '_' in book_name:
                    book_name = '_'.join(book_name.split('_')[1:])  # 去掉时间戳部分
            else:
                book_name = '未知书籍'
        
        self.setWindowTitle(f'目录 - {book_name}')
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 设置窗口图标
        import os
        from PyQt5.QtGui import QIcon
        # 优先使用PNG格式，因为Windows对PNG支持更好
        if os.path.exists('logo.ico'):
            self.setWindowIcon(QIcon('logo.ico'))
        elif os.path.exists('logo.png'):
            self.setWindowIcon(QIcon('logo.png'))
        elif os.path.exists('logo.svg'):
            self.setWindowIcon(QIcon('logo.svg'))
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题区域
        self.create_title_area(layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：章节列表
        self.create_chapter_list(splitter)
        
        # 右侧：章节预览
        self.create_chapter_preview(splitter)
        
        # 设置分割器比例
        splitter.setSizes([400, 400])
        
        # 底部按钮区域
        self.create_button_area(layout)
        
        # 设置样式
        self.setStyleSheet(
            "QDialog {"
            "    background-color: #f8f9fa;"
            "}"
            "QLabel {"
            "    color: #2c3e50;"
            "}"
        )
        
    def create_title_area(self, layout):
        """创建标题区域"""
        title_frame = QFrame()
        title_frame.setStyleSheet(
            "QFrame {"
            "    background-color: #ffffff;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 6px;"
            "    padding: 6px 12px;"
            "    max-height: 40px;"
            "}"
        )
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 书籍名称 - 使用智能解析的书名，如果没有则使用文件名
        book_name = self.book_info.get('name', '')
        if not book_name or book_name == '未知书籍':
            # 从文件路径中提取文件名（不含扩展名）
            file_path = self.book_info.get('file_path', '')
            if file_path:
                filename = os.path.basename(file_path)
                book_name = os.path.splitext(filename)[0]
                
                # 去掉时间戳前缀（格式：数字_文件名.扩展名）
                if '_' in book_name:
                    book_name = '_'.join(book_name.split('_')[1:])  # 去掉时间戳部分
            else:
                book_name = '未知书籍'
        
        book_label = QLabel(book_name)
        book_label.setFont(QFont("微软雅黑", 11, QFont.Bold))
        book_label.setStyleSheet("color: #2c3e50;")
        book_label.setWordWrap(False)  # 不换行，保持单行显示
        book_label.setMaximumHeight(24)  # 限制高度
        
        # 章节统计信息（稍后会更新）
        self.stats_label = QLabel("解析中...")
        self.stats_label.setFont(QFont("微软雅黑", 9))
        self.stats_label.setStyleSheet("color: #6c757d;")
        self.stats_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.stats_label.setMaximumHeight(24)  # 限制高度
        
        title_layout.addWidget(book_label, 1)  # 书名占更多空间
        title_layout.addWidget(self.stats_label, 0)  # 统计信息靠右
        
        layout.addWidget(title_frame)
        
    def create_chapter_list(self, parent):
        """创建章节列表"""
        list_frame = QFrame()
        list_frame.setStyleSheet(
            "QFrame {"
            "    background-color: #ffffff;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 6px;"
            "}"
        )
        
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(10, 10, 10, 10)
        
        # 列表标题
        list_title = QLabel("章节目录")
        list_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        list_title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        
        # 章节列表
        self.chapter_list = QListWidget()
        self.chapter_list.setStyleSheet(
            "QListWidget {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: #ffffff;"
            "    selection-background-color: #007bff;"
            "    selection-color: white;"
            "}"
            "QListWidget::item {"
            "    padding: 8px;"
            "    border-bottom: 1px solid #f1f3f4;"
            "    color: #495057;"
            "}"
            "QListWidget::item:hover {"
            "    background-color: #f8f9fa;"
            "}"
            "QListWidget::item:selected {"
            "    background-color: #007bff;"
            "    color: white;"
            "}"
        )
        self.chapter_list.itemClicked.connect(self.on_chapter_clicked)
        self.chapter_list.itemDoubleClicked.connect(self.on_chapter_double_clicked)
        
        # 状态标签
        self.status_label = QLabel("正在解析目录...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(
            "color: #6c757d; "
            "font-style: italic; "
            "padding: 20px;"
        )
        
        list_layout.addWidget(list_title)
        list_layout.addWidget(self.chapter_list)
        list_layout.addWidget(self.status_label)
        
        parent.addWidget(list_frame)
        
    def create_chapter_preview(self, parent):
        """创建章节预览"""
        preview_frame = QFrame()
        preview_frame.setStyleSheet(
            "QFrame {"
            "    background-color: #ffffff;"
            "    border: 1px solid #dee2e6;"
            "    border-radius: 6px;"
            "}"
        )
        
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        
        # 预览标题
        preview_title = QLabel("章节信息")
        preview_title.setFont(QFont("微软雅黑", 12, QFont.Bold))
        preview_title.setStyleSheet("color: #495057; margin-bottom: 10px;")
        
        # 章节信息显示
        self.chapter_info = QTextEdit()
        self.chapter_info.setReadOnly(True)
        self.chapter_info.setStyleSheet(
            "QTextEdit {"
            "    border: 1px solid #ced4da;"
            "    border-radius: 4px;"
            "    background-color: #f8f9fa;"
            "    color: #495057;"
            "    font-family: '微软雅黑';"
            "    font-size: 10pt;"
            "    padding: 10px;"
            "}"
        )
        self.chapter_info.setText("请选择一个章节查看详细信息")
        
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(self.chapter_info)
        
        parent.addWidget(preview_frame)
        
    def create_button_area(self, layout):
        """创建按钮区域"""
        button_layout = QHBoxLayout()
        
        # 重新解析按钮
        self.reparse_btn = QPushButton("重新解析")
        self.reparse_btn.setFixedHeight(35)
        self.reparse_btn.setStyleSheet(
            "QPushButton {"
            "    background-color: #6c757d;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 4px;"
            "    font-size: 12px;"
            "    padding: 0 15px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #5a6268;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #545b62;"
            "}"
        )
        self.reparse_btn.clicked.connect(self.start_parsing)
        
        # 跳转到章节按钮
        self.goto_btn = QPushButton("跳转到此章节")
        self.goto_btn.setFixedHeight(35)
        self.goto_btn.setEnabled(False)
        self.goto_btn.setStyleSheet(
            "QPushButton {"
            "    background-color: #007bff;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 4px;"
            "    font-size: 12px;"
            "    padding: 0 15px;"
            "}"
            "QPushButton:hover:enabled {"
            "    background-color: #0056b3;"
            "}"
            "QPushButton:pressed:enabled {"
            "    background-color: #004085;"
            "}"
            "QPushButton:disabled {"
            "    background-color: #6c757d;"
            "    color: #adb5bd;"
            "}"
        )
        self.goto_btn.clicked.connect(self.goto_chapter)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(35)
        close_btn.setStyleSheet(
            "QPushButton {"
            "    background-color: #dc3545;"
            "    color: white;"
            "    border: none;"
            "    border-radius: 4px;"
            "    font-size: 12px;"
            "    padding: 0 15px;"
            "}"
            "QPushButton:hover {"
            "    background-color: #c82333;"
            "}"
            "QPushButton:pressed {"
            "    background-color: #bd2130;"
            "}"
        )
        close_btn.clicked.connect(self.close)
        
        button_layout.addWidget(self.reparse_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.goto_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def start_parsing(self):
        """开始解析目录"""
        file_path = self.book_info.get('file_path')
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, '错误', '文件不存在！')
            return
            
        # 清空列表
        self.chapter_list.clear()
        self.chapters = []
        
        # 显示进度条和状态
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在解析目录...")
        self.status_label.setVisible(True)
        self.reparse_btn.setEnabled(False)
        
        # 启动解析线程
        self.parse_thread = ContentsParseThread(file_path)
        self.parse_thread.parse_finished.connect(self.on_parse_finished)
        self.parse_thread.parse_progress.connect(self.on_parse_progress)
        self.parse_thread.parse_error.connect(self.on_parse_error)
        self.parse_thread.start()
        
    @pyqtSlot(list)
    def on_parse_finished(self, chapters):
        """解析完成处理"""
        self.chapters = chapters
        self.progress_bar.setVisible(False)
        self.reparse_btn.setEnabled(True)
        
        if not chapters:
            self.status_label.setText("未找到章节目录")
            self.chapter_info.setText("该书籍可能没有标准的章节格式，或者章节格式不被支持。")
            self.stats_label.setText("无章节")
            return
            
        # 隐藏状态标签
        self.status_label.setVisible(False)
        
        # 填充章节列表
        for i, chapter in enumerate(chapters):
            item = QListWidgetItem()
            
            # 根据章节级别设置缩进
            indent = "  " if chapter['level'] == 2 else ""
            display_text = f"{indent}{chapter['title']}"
            
            item.setText(display_text)
            item.setData(Qt.UserRole, chapter)
            
            # 设置不同级别章节的样式
            if chapter['level'] == 2:
                font = item.font()
                font.setPointSize(9)
                item.setFont(font)
                
            self.chapter_list.addItem(item)
            
        # 显示统计信息
        toc_parser = TableOfContents()
        summary = toc_parser.get_chapter_summary(chapters)
        
        # 更新标题区域的统计信息
        self.stats_label.setText(f"共 {summary['total_chapters']} 章")
        
        info_text = f"""
解析完成！

统计信息：
• 总章节数：{summary['total_chapters']}
• 主章节数：{summary['main_chapters']}
• 子章节数：{summary['sub_chapters']}

提示：
• 点击章节可查看详细信息
• 双击章节可直接跳转阅读
• 支持的格式包括：第X章、第X回、Chapter X、【第X章】等
        """
        
        self.chapter_info.setText(info_text)
        
    @pyqtSlot(int)
    def on_parse_progress(self, value):
        """更新解析进度"""
        self.progress_bar.setValue(value)
        
    @pyqtSlot(str)
    def on_parse_error(self, error_msg):
        """解析错误处理"""
        self.progress_bar.setVisible(False)
        self.reparse_btn.setEnabled(True)
        self.status_label.setText(f"解析失败：{error_msg}")
        QMessageBox.critical(self, '解析错误', f'目录解析失败：{error_msg}')
        
    def on_chapter_clicked(self, item):
        """章节点击处理"""
        chapter = item.data(Qt.UserRole)
        if not chapter:
            return
            
        # 显示章节详细信息
        info_text = f"""
章节信息：

标题：{chapter['title']}
行号：第 {chapter['line_number']} 行
字符位置：{chapter['char_position']}
章节级别：{'主章节' if chapter['level'] == 1 else '子章节'}

操作：
• 点击下方"跳转到此章节"按钮开始阅读
• 或双击此章节直接跳转
        """
        
        self.chapter_info.setText(info_text)
        self.goto_btn.setEnabled(True)
        
    def on_chapter_double_clicked(self, item):
        """章节双击处理 - 直接跳转"""
        chapter = item.data(Qt.UserRole)
        if chapter:
            print(f"[调试] 双击跳转到章节: {chapter['title']}")
            print(f"[调试] 章节信息: 行号={chapter.get('line_number', '未知')}, 字符位置={chapter.get('char_position', '未知')}")
            self.chapter_selected.emit(chapter)
            self.accept()  # 关闭对话框
            
    def goto_chapter(self):
        """跳转到选中的章节"""
        current_item = self.chapter_list.currentItem()
        if not current_item:
            print("[调试] 跳转失败: 没有选中的章节")
            return
            
        chapter = current_item.data(Qt.UserRole)
        if chapter:
            print(f"[调试] 点击按钮跳转到章节: {chapter['title']}")
            print(f"[调试] 章节信息: 行号={chapter.get('line_number', '未知')}, 字符位置={chapter.get('char_position', '未知')}")
            self.chapter_selected.emit(chapter)
            self.accept()  # 关闭对话框
        else:
            print("[调试] 跳转失败: 章节数据为空")