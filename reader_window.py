#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阅读窗口模块 - 无边框可拖动的文本显示窗口
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QMenu, QAction,
    QApplication, QMessageBox, QCheckBox, QLabel
)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QEvent, QRect, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette, QPainter, QPen, QCursor, QPixmap
import ctypes
from ctypes import wintypes


class NoZoomTextEdit(QTextEdit):
    """禁用缩放功能的QTextEdit子类"""
    
    def zoomIn(self, range=1):
        """禁用放大功能"""
        pass
    
    def zoomOut(self, range=1):
        """禁用缩小功能"""
        pass
    
    def wheelEvent(self, event):
        """重写滚轮事件，完全禁用缩放"""
        # 不调用父类的wheelEvent，完全忽略滚轮事件
        event.ignore()

class ProgressTooltip(QWidget):
    """进度提示悬浮窗 - 显示章节信息和阅读进度"""
    
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # 设置窗口属性
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 窗口全透明
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)  # 显示时不激活窗口
        self.setAttribute(Qt.WA_NoSystemBackground, True)     # 无系统背景
        
        # 初始化UI
        self.init_ui()
        
        # 初始隐藏
        self.hide()
        
        # 记录上次更新的位置和内容，避免频繁更新导致闪动
        self._last_pos = None
        self._last_chapter = None
        self._last_book_progress = None
        self._last_chapter_progress = None
    
    def init_ui(self):
        """初始化UI组件"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 章节名称
        self.chapter_label = QLabel()
        self.chapter_label.setFont(QFont('Microsoft YaHei', 10, QFont.Bold))
        self.chapter_label.setStyleSheet('color: rgba(255, 255, 255, 0.9); background: transparent;')
        layout.addWidget(self.chapter_label)
        
        # 全书进度
        self.book_progress_label = QLabel()
        self.book_progress_label.setFont(QFont('Microsoft YaHei', 9))
        self.book_progress_label.setStyleSheet('color: rgba(255, 255, 255, 0.8); background: transparent;')
        layout.addWidget(self.book_progress_label)
        
        # 本章进度
        self.chapter_progress_label = QLabel()
        self.chapter_progress_label.setFont(QFont('Microsoft YaHei', 9))
        self.chapter_progress_label.setStyleSheet('color: rgba(255, 255, 255, 0.8); background: transparent;')
        layout.addWidget(self.chapter_progress_label)
        
        # 调整窗口大小以适应内容
        self.adjustSize()
        
        # 设置半透明背景效果（移除backdrop-filter以避免警告）
        self.setStyleSheet(
            """QWidget {
            background-color: rgba(0, 0, 0, 0.6);  /* 半透明黑色背景，增强可读性 */
            border-radius: 8px;  /* 圆角边框 */
            }"""
        )
    
    def update_progress(self, chapter_name, book_progress, chapter_progress):
        """更新进度信息
        
        Args:
            chapter_name (str): 当前章节名称
            book_progress (float): 全书进度 (0-100)
            chapter_progress (float): 本章进度 (0-100)
        """
        # 防抖逻辑：只有内容变化时才更新，避免频繁更新导致闪动
        if (self._last_chapter == chapter_name and 
            abs(self._last_book_progress - book_progress) < 0.1 and 
            abs(self._last_chapter_progress - chapter_progress) < 0.1):
            return  # 内容没有明显变化，不更新
        
        # 更新显示内容
        self.chapter_label.setText(chapter_name)
        self.book_progress_label.setText(f'全书进度: {book_progress:.1f}%')
        self.chapter_progress_label.setText(f'本章进度: {chapter_progress:.1f}%')
        
        # 调整窗口大小以适应新内容
        self.adjustSize()
        
        # 保存当前状态
        self._last_chapter = chapter_name
        self._last_book_progress = book_progress
        self._last_chapter_progress = chapter_progress
    
    def show_at_position(self, pos, reader_rect):
        """在指定位置显示悬浮窗，避免边缘重叠
        
        Args:
            pos (QPoint): 鼠标位置
            reader_rect (QRect): 阅读器窗口矩形
        """
        # 位置防抖逻辑：只有位置变化明显时才更新位置
        if self._last_pos is not None:
            # 计算鼠标位置变化距离
            dx = abs(pos.x() - self._last_pos.x())
            dy = abs(pos.y() - self._last_pos.y())
            # 如果位置变化小于5像素，不更新位置
            if dx < 5 and dy < 5:
                # 只需要显示，不需要更新位置
                self.show()
                return
        
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        
        # 获取悬浮窗尺寸
        tooltip_rect = self.geometry()
        tooltip_width = tooltip_rect.width()
        tooltip_height = tooltip_rect.height()
        
        # 计算初始位置（鼠标右上角）
        x = pos.x() + 10
        y = pos.y() - tooltip_height - 10
        
        # 边缘回避处理
        # 右边没空间，显示在左边
        if x + tooltip_width > screen_rect.right():
            x = pos.x() - tooltip_width - 10
        
        # 上边没空间，显示在下方
        if y < screen_rect.top():
            y = pos.y() + 10
        
        # 下边没空间，显示在上方
        if y + tooltip_height > screen_rect.bottom():
            y = pos.y() - tooltip_height - 10
        
        # 移除不允许覆盖阅读器窗口的逻辑，允许悬浮窗覆盖阅读器
        
        # 确保悬浮窗完全在屏幕内
        x = max(screen_rect.left(), min(x, screen_rect.right() - tooltip_width))
        y = max(screen_rect.top(), min(y, screen_rect.bottom() - tooltip_height))
        
        # 设置位置并显示
        self.setGeometry(x, y, tooltip_width, tooltip_height)
        self.show()
        
        # 保存当前位置
        self._last_pos = pos
import os

from config_window import ConfigWindow
from history_manager import HistoryManager
from bookmark_manager import BookmarkManager
from bookmark_window import BookmarkWindow
from search_window import SearchWindow
from toast_notification import ToastManager


class ReaderWindow(QWidget):
    """无边框阅读窗口类"""
    
    # 定义信号
    closed = pyqtSignal()  # 窗口关闭信号
    
    def __init__(self, content, config_manager, main_window, file_path=None, title=None, restore_position=True):
        super().__init__()
        self.content = content
        self.config_manager = config_manager
        self.main_window = main_window
        self.config_window = None
        
        # 历史记录相关属性
        self.history_manager = HistoryManager()
        self.file_path = file_path  # 当前阅读的文件路径
        self.title = title or "未知文档"  # 文档标题
        
        # 书签和搜索相关属性
        self.bookmark_manager = BookmarkManager()
        self.bookmark_window = None
        self.search_window = None
        
        # 用于窗口拖动的变量
        self.drag_position = QPoint()
        self.is_dragging = False
        
        # 用于翻页功能的变量
        self.text_lines = []  # 文本行列表
        self.current_line_index = 0  # 当前显示的行索引
        self.lines_per_page = 1  # 每页显示的行数（单行模式为1，多行模式根据窗口高度计算）
        
        # 用于四角拖拽调节大小的变量
        self.show_resize_handles = False  # 是否显示调节大小的标记
        self.resize_handle_size = 20  # 调节大小标记的尺寸（增大以便更容易触发）
        self.resizing = False  # 是否正在调节大小
        self.resize_direction = None  # 调节大小的方向
        
        # 用于显示控制的变量
        self.hover_to_show = False  # 鼠标悬停才显示
        self.key_to_show = False  # 需要按住自定义键才显示
        self.custom_key = 'ctrl'  # 自定义按键
        self.is_key_pressed = False  # 当前是否按住了自定义键
        self.is_mouse_over = False  # 鼠标是否在窗口上方
        self.content_visible = True  # 内容是否可见（用于控制显示/隐藏）
        self.context_menu_showing = False  # 右键菜单是否正在显示
        self.window_activated = False  # 窗口是否已经被激活过（用于优化显示逻辑）
        
        # 用于调试输出控制的变量
        # 移除调试相关变量
        
        # 是否恢复阅读位置的标志
        self.should_restore_position = restore_position
        
        # 临时固定显示标志
        self.is_temporarily_fixed = False
        
        # 章节信息悬浮窗
        self.progress_tooltip = None
        
        # 自动阅读相关
        self.auto_reading = False  # 是否正在自动阅读
        self.auto_read_paused = False  # 是否暂停
        self.auto_read_timer = None  # 自动阅读定时器
        self.auto_read_was_paused_by_hide = False  # 标记是否因窗口隐藏而暂停
        self.contents_window = None  # 目录窗口引用
        
        # 初始化自动阅读定时器
        self.auto_read_timer = QTimer(self)
        self.auto_read_timer.timeout.connect(self.auto_read_step)
        
        # 安装全局事件过滤器，用于监听Ctrl+`组合键，无论是否有焦点
        self.install_global_event_filter()
        
        self.init_ui()
        self.prepare_text_content()  # 准备文本内容
        self.load_config()
        
        # 创建悬浮窗实例
        self.progress_tooltip = ProgressTooltip(self)
        
        # 预解析章节信息并缓存，避免第一次按Ctrl+E时的延迟
        self.get_current_chapter_info()
        
        # 恢复阅读位置（必须在文本内容准备完成后调用）
        if self.should_restore_position:
            self.restore_reading_position()
        
    def init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性 - 添加Tool标志隐藏任务栏图标和多任务切换视图
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.Tool  # 隐藏任务栏图标，不显示在Alt+Tab和Win+Tab中
        )
        
        # 设置窗口标题（虽然不显示，但用于调试）
        self.setWindowTitle('ReadFish Reader')
        
        # 设置对象名称以便样式表识别
        self.setObjectName('ReaderWindow')
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # 无边距
        layout.setSizeConstraint(QVBoxLayout.SetNoConstraint)  # 移除布局尺寸约束
        
        # 创建一个透明的背景控件来捕获鼠标事件
        from PyQt5.QtWidgets import QFrame
        self.background_frame = QFrame()
        # 初始样式将在apply_window_background_opacity中设置
        self.background_frame.installEventFilter(self)
        self.background_frame.setMinimumSize(0, 0)  # 移除背景框架的最小尺寸限制
        
        # 为背景框架创建布局
        frame_layout = QVBoxLayout(self.background_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSizeConstraint(QVBoxLayout.SetNoConstraint)  # 移除布局尺寸约束
        
        # 创建文本显示区域
        self.text_edit = NoZoomTextEdit()
        self.text_edit.setPlainText(self.content)
        self.text_edit.setReadOnly(True)  # 只读模式

        # 禁用文本选择
        self.text_edit.setTextInteractionFlags(Qt.NoTextInteraction)

        # 禁止文本编辑器获取键盘焦点，确保方向键事件由ReaderWindow接收
        # 说明：之前方向键不生效的原因是焦点可能在其他窗口或被子控件抢占，
        # 将文本编辑器的焦点策略设为NoFocus可以避免其拦截键盘事件。
        self.text_edit.setFocusPolicy(Qt.NoFocus)
        
        # 禁用字体缩放功能
        self.text_edit.setProperty('zoomInFactor', 1.0)
        self.text_edit.setProperty('zoomOutFactor', 1.0)
        
        # 设置鼠标光标为箭头形状，避免显示文本光标
        self.text_edit.setCursor(Qt.ArrowCursor)    
        
        # 禁用滚动条
        self.text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 移除文本编辑器的最小尺寸限制
        self.text_edit.setMinimumSize(0, 0)
        
        # 设置文本编辑器样式 - 完全透明背景
        self.text_edit.setStyleSheet(
            'QTextEdit {'
            '    border: none;'
            '    background-color: transparent;'
            '}'
        )
        
        # 为主窗口也设置箭头光标
        self.setCursor(Qt.ArrowCursor)

        # 创建“小圆点”鼠标光标（用于自动隐藏显示时）
        cfg = self.config_manager.get_config()
        self.dot_cursor = self.create_dot_cursor(
            diameter=cfg.get('dot_cursor_size', 2),
            color_hex=cfg.get('dot_cursor_color', '#000000'),
            opacity=cfg.get('dot_cursor_opacity', 1.0)
        )
        self.use_dot_cursor = False
        
        # 设置窗口焦点策略，确保能够接收键盘输入
        self.setFocusPolicy(Qt.StrongFocus)
        
        # 安装事件过滤器，让文本编辑器的鼠标事件传递给父窗口
        self.text_edit.installEventFilter(self)
        self.text_edit.viewport().installEventFilter(self)
        self.text_edit.viewport().setCursor(Qt.ArrowCursor)
        
        frame_layout.addWidget(self.text_edit)
        layout.addWidget(self.background_frame)
        
        # 设置默认大小和位置
        self.resize(400, 300)
        self.move(100, 100)
        
        # 设置窗口最小尺寸限制：宽度100px，高度35px
        self.setMinimumSize(100, 35)  # 设置合理的最小尺寸限制
        self.setMaximumSize(16777215, 16777215)  # 设置最大尺寸为Qt允许的最大值
        
        # 设置窗口在所有虚拟桌面显示
        self.set_window_on_all_desktops()
        
        # 启用鼠标跟踪以检测鼠标进入和离开事件
        self.setMouseTracking(True)
        self.text_edit.setMouseTracking(True)
        self.background_frame.setMouseTracking(True)
        
        # 创建定时器来定期检查鼠标位置（用于窗口隐藏时的鼠标检测）
        self.mouse_check_timer = QTimer()
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)  # 每100毫秒检查一次
        
    def prepare_text_content(self):
        """准备文本内容，分析源文件格式"""
        # 保持原文件格式，不去除换行符
        self.full_text = self.content
        
        # 确保至少有一些内容
        if not self.full_text.strip():
            self.full_text = '（无内容）'
            
        # 初始化显示相关变量
        self.text_lines = []  # 将根据显示模式动态生成
        self.current_line_index = 0
        self.current_char_index = 0  # 当前显示的字符位置（用于单行模式）
        
    def update_display_mode(self, preserve_position=True):
        """根据单行模式配置更新显示模式
        
        Args:
            preserve_position: 是否保持当前阅读位置，默认为True
        """
        config = self.config_manager.get_config()
        single_line_mode = config.get('single_line_mode', False)
        
        # 保存当前阅读位置
        saved_line_index = getattr(self, 'current_line_index', 0) if preserve_position else 0
        saved_char_offset = getattr(self, 'current_char_offset', 0) if preserve_position else 0
        
        if single_line_mode:
            # 单行模式：只显示一行，仅受宽度限制
            self.prepare_single_line_mode()
            # 恢复阅读位置
            if preserve_position:
                self.current_line_index = min(saved_line_index, len(self.text_lines) - 1)
                self.current_char_offset = saved_char_offset
        else:
            # 多行模式：显示原内容，窗口显示不全时只显示完整行数
            self.prepare_multi_line_mode()
            # 恢复阅读位置
            if preserve_position:
                self.current_line_index = min(saved_line_index, len(self.text_lines) - 1)
            # 多行模式下重置字符偏移（多行模式不使用字符偏移）
            if hasattr(self, 'current_char_offset'):
                self.current_char_offset = 0
            
        self.update_text_display()
         
    def prepare_single_line_mode(self):
        """准备单行模式：按原文换行符分割，支持长行分页显示"""
        # 单行模式下，按原文的换行符分割成行
        self.text_lines = self.full_text.split('\n')
        
        # 确保至少有一行
        if not self.text_lines:
            self.text_lines = ['（无内容）']
            
        self.lines_per_page = 1  # 单行模式每页显示一行
        self.current_line_index = 0
        self.current_char_offset = 0  # 当前行内的字符偏移量，用于长行分页
        
        
    def prepare_multi_line_mode(self):
        """准备多行模式：保持原内容格式，按行分割"""
        # 多行模式下，按原文本的换行符分割成行
        self.text_lines = self.full_text.split('\n')
        
        # 确保至少有一行
        if not self.text_lines:
            self.text_lines = ['（无内容）']
        self.current_line_index = 0
        self.calculate_lines_per_page()
             
    def calculate_lines_per_page(self):
        """计算多行模式下每页显示的行数"""
        if not hasattr(self, 'text_edit') or not self.text_edit:
            self.lines_per_page = 1
            return
            
        # 获取字体信息
        font_metrics = self.text_edit.fontMetrics()
        line_height = font_metrics.lineSpacing()
        
        # 获取文本编辑器的可用高度
        available_height = self.text_edit.height() - 20  # 减去边距
        
        # 计算能显示的完整行数
        self.lines_per_page = max(1, int(available_height / line_height))
        
    def calculate_visible_chars(self, current_line=None):
        """计算单行模式下窗口可以显示的字符数"""
        if not hasattr(self, 'text_edit') or not self.text_edit:
            return 10  # 默认值
            
        # 获取字体信息
        font_metrics = self.text_edit.fontMetrics()
        
        # 获取文本编辑器的实际可用宽度
        text_edit_width = self.text_edit.width()
        
        # 获取QTextEdit的内容边距
        margins = self.text_edit.contentsMargins()
        left_margin = margins.left()
        right_margin = margins.right()
        
        # 获取文档边距
        document = self.text_edit.document()
        doc_margin = document.documentMargin()
        
        # 获取滚动条宽度（即使隐藏也可能占用空间）
        scrollbar_width = self.text_edit.verticalScrollBar().sizeHint().width() if self.text_edit.verticalScrollBar().isVisible() else 0
        
        # 计算实际可用宽度，使用更保守的安全边距
        # 增加安全边距到20px，并考虑可能的滚动条宽度和字体渲染误差
        safety_margin = 20
        available_width = text_edit_width - left_margin - right_margin - (doc_margin * 2) - scrollbar_width - safety_margin
        
        # 确保可用宽度为正数
        available_width = max(50, available_width)  # 至少保证50px宽度
        
        # 如果有当前行文本，使用实际文本测量
        if current_line:
            # 使用二分查找找到最大可显示字符数
            left, right = 1, len(current_line)
            max_chars = 1
            
            while left <= right:
                mid = (left + right) // 2
                test_text = current_line[:mid]
                text_width = font_metrics.width(test_text)
                
                # 为了更保险，在二分查找中也留一些余量
                if text_width <= available_width - 5:  # 额外留5px余量
                    max_chars = mid
                    left = mid + 1
                else:
                    right = mid - 1
            
            # 最终再次验证，确保选择的字符数不会导致截断
            if max_chars > 1:
                final_text = current_line[:max_chars]
                final_width = font_metrics.width(final_text)
                # 如果最终宽度太接近边界，减少一个字符作为安全措施
                if final_width > available_width - 10:
                    max_chars = max(1, max_chars - 1)
                    
            return max(1, max_chars)
        else:
            # 没有具体文本时，使用平均字符宽度估算
            # 使用更保守的安全系数
            avg_char_width = font_metrics.averageCharWidth()
            
            if avg_char_width > 0:
                # 使用更保守的计算，留出更多余量
                visible_chars = max(1, int((available_width - 10) / avg_char_width))
            else:
                visible_chars = 10  # 默认值
                
            return visible_chars
        
    def update_text_display(self):
        """更新文本显示内容"""
        if not self.text_lines:
            return
            
        config = self.config_manager.get_config()
        single_line_mode = config.get('single_line_mode', False)
        
        if single_line_mode:
            # 单行模式：支持长行分页显示
            self.current_line_index = max(0, min(self.current_line_index, len(self.text_lines) - 1))
            current_line = self.text_lines[self.current_line_index]
            
            # 计算当前窗口可以显示的字符数，传入当前行文本进行精确测量
            visible_chars = self.calculate_visible_chars(current_line)
            
            # 确保字符偏移量在有效范围内
            self.current_char_offset = max(0, min(self.current_char_offset, len(current_line)))
            
            # 获取当前页要显示的文本片段
            end_offset = min(self.current_char_offset + visible_chars, len(current_line))
            display_text = current_line[self.current_char_offset:end_offset]
            
            self.text_edit.setPlainText(display_text)
            self.text_edit.setLineWrapMode(QTextEdit.NoWrap)
        else:
            # 多行模式：显示完整行，避免显示不完整的行
            display_text = self.get_visible_complete_lines()
            # 启用自动换行，让长行能够在窗口内正确显示
            self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
            self.text_edit.setPlainText(display_text)
        
    def page_up(self):
        """向上翻页"""
        config = self.config_manager.get_config()
        single_line_mode = config.get('single_line_mode', False)
        remove_empty_lines = config.get('remove_empty_lines', False)
        
        if single_line_mode:
            # 单行模式：支持长行分页
            if not hasattr(self, 'current_char_offset'):
                self.current_char_offset = 0
                
            current_line = self.text_lines[self.current_line_index]
            visible_chars = self.calculate_visible_chars(current_line)
            
            # 如果当前行有字符偏移，先向前翻页显示该行的前面部分
            if self.current_char_offset > 0:
                self.current_char_offset = max(0, self.current_char_offset - visible_chars)
                self.update_text_display()
            # 如果已经在当前行的开头，则跳到上一行的末尾
            elif self.current_line_index > 0:
                # 跳过空行（如果启用）
                target_index = self.current_line_index - 1
                if remove_empty_lines:
                    while target_index >= 0 and self.text_lines[target_index].strip() == '':
                        target_index -= 1
                
                if target_index >= 0:
                    self.current_line_index = target_index
                    prev_line = self.text_lines[self.current_line_index]
                    # 重新计算上一行的可见字符数
                    visible_chars = self.calculate_visible_chars(prev_line)
                    # 计算上一行需要多少页显示完
                    if len(prev_line) > visible_chars:
                        # 跳到上一行的最后一页
                        pages_needed = (len(prev_line) + visible_chars - 1) // visible_chars
                        self.current_char_offset = (pages_needed - 1) * visible_chars
                    else:
                        self.current_char_offset = 0
                    self.update_text_display()
        else:
            # 多行模式：向上翻页
            if self.current_line_index > 0:
                self.current_line_index -= self.lines_per_page
                self.current_line_index = max(0, self.current_line_index)
                
                # 跳过空行（如果启用）
                if remove_empty_lines:
                    # 向上查找非空行
                    target_index = self.current_line_index
                    while target_index > 0 and self.text_lines[target_index].strip() == '':
                        target_index -= 1
                    self.current_line_index = target_index
                
                self.update_text_display()
        
        # 更新阅读历史记录
        self.update_reading_history()
        
        # 如果在自动阅读状态，重置计时器，避免用户刚翻完页又被自动翻回去
        if self.auto_reading and not self.auto_read_paused:
            self.auto_read_timer.start()
            
    def page_down(self):
        """向下翻页"""
        config = self.config_manager.get_config()
        single_line_mode = config.get('single_line_mode', False)
        remove_empty_lines = config.get('remove_empty_lines', False)
        
        if single_line_mode:
            # 单行模式：支持长行分页
            if not hasattr(self, 'current_char_offset'):
                self.current_char_offset = 0
                
            current_line = self.text_lines[self.current_line_index]
            visible_chars = self.calculate_visible_chars(current_line)
            
            # 检查当前行是否还有更多内容可以显示
            if self.current_char_offset + visible_chars < len(current_line):
                # 当前行还有内容，向后翻页显示该行的后面部分
                self.current_char_offset += visible_chars
                self.update_text_display()
            # 如果当前行已经显示完，跳到下一行的开头
            elif self.current_line_index < len(self.text_lines) - 1:
                # 跳过空行（如果启用）
                target_index = self.current_line_index + 1
                if remove_empty_lines:
                    while target_index < len(self.text_lines) and self.text_lines[target_index].strip() == '':
                        target_index += 1
                
                if target_index < len(self.text_lines):
                    self.current_line_index = target_index
                    self.current_char_offset = 0
                    self.update_text_display()
        else:
            # 多行模式：向下翻页
            max_start_line = max(0, len(self.text_lines) - self.lines_per_page)
            if self.current_line_index < max_start_line:
                self.current_line_index += self.lines_per_page
                self.current_line_index = min(self.current_line_index, max_start_line)
                
                # 跳过空行（如果启用）
                if remove_empty_lines:
                    # 向下查找非空行
                    target_index = self.current_line_index
                    while target_index < max_start_line and self.text_lines[target_index].strip() == '':
                        target_index += 1
                    self.current_line_index = target_index
                
                self.update_text_display()
        
        # 更新阅读历史记录
        self.update_reading_history()
        
        # 如果在自动阅读状态，重置计时器，避免用户刚翻完页又被自动翻回去
        if self.auto_reading and not self.auto_read_paused:
            self.auto_read_timer.start()
        
    def update_reading_history(self):
        """更新阅读历史记录"""
        if self.file_path and hasattr(self, 'text_lines') and self.text_lines:
            # 获取当前字符偏移，如果没有则默认为0
            current_char_offset = getattr(self, 'current_char_offset', 0)
            
            # 更新历史记录
            self.history_manager.update_reading_position(
                file_path=self.file_path,
                title=self.title,
                current_line_index=self.current_line_index,
                current_char_offset=current_char_offset,
                total_lines=len(self.text_lines)
            )
    
    def restore_reading_position(self):
        """从历史记录恢复阅读位置"""
        if self.file_path:
            history = self.history_manager.get_reading_position(self.file_path)
            if history:
                # 恢复阅读位置
                self.current_line_index = min(history.get('current_line_index', 0), len(self.text_lines) - 1)
                self.current_char_offset = history.get('current_char_offset', 0)
                
                # 更新显示
                self.update_text_display()
                
                # 已恢复阅读位置
        
    def load_config(self, apply_window_geometry=True):
        """加载配置并应用到窗口
        
        Args:
            apply_window_geometry: 是否应用窗口大小和位置，默认为True
                                 在配置改变时设为False，避免重置窗口大小
        """
        config = self.config_manager.get_config()
        
        if apply_window_geometry:
            # 应用窗口大小
            width = config.get('window_width', 400)
            height = config.get('window_height', 300)
            self.resize(width, height)
            
            # 应用窗口位置
            x = config.get('window_x', 100)
            y = config.get('window_y', 100)
            self.move(x, y)
        
        # 应用窗口背景透明度（不影响文字）
        window_opacity = config.get('window_opacity', 0.9)
        self.apply_window_background_opacity(window_opacity)
        
        # 应用文字设置
        self.apply_text_config(config)
        
        # 加载显示控制设置
        self.hover_to_show = config.get('hover_to_show', False)
        self.key_to_show = config.get('key_to_show', False)
        self.custom_key = config.get('custom_key', 'ctrl')
        # 读取用户自定义翻页按键（字母键，最多两个）
        self.page_up_keys = config.get('page_up_keys', [])
        self.page_down_keys = config.get('page_down_keys', [])
        
        # 更新显示模式（如果不需要恢复位置，则不保持位置）
        self.update_display_mode(preserve_position=self.should_restore_position)
        # 刷新圆点光标设置，确保后续可见性更新采用最新光标样式
        self.refresh_dot_cursor_from_config()

        # 刷新圆点光标设置
        self.refresh_dot_cursor_from_config()
        
        # 根据配置更新窗口可见性
        # 如果启用了显示控制功能，初始状态应该是隐藏的
        if self.hover_to_show or self.key_to_show:
            self.content_visible = True  # 设置为True以便update_content_visibility能正确切换状态
            self.is_mouse_over = False  # 初始鼠标不在窗口上
            self.is_key_pressed = False  # 初始按键未按下
        # 刷新圆点光标设置并更新窗口可见性
        self.refresh_dot_cursor_from_config()
        self.update_content_visibility()
        
    def apply_text_config(self, config=None):
        """应用文字配置"""
        if config is None:
            config = self.config_manager.get_config()
            
        # 设置字体
        font_family = config.get('font_family', 'Microsoft YaHei')
        font_size = config.get('font_size', 12)
        font = QFont(font_family, font_size)
        self.text_edit.setFont(font)
        
        # 设置文字颜色和透明度
        font_color = config.get('font_color', '#000000')
        text_opacity = config.get('text_opacity', 1.0)
        
        # 解析颜色并应用透明度
        color = QColor(font_color)
        color.setAlphaF(text_opacity)
        
        # 通过样式表设置文字颜色和透明度
        rgba_color = f"rgba({color.red()}, {color.green()}, {color.blue()}, {text_opacity})"
        
        # 设置样式 - 保持背景透明，只设置文字颜色
        self.text_edit.setStyleSheet(
            f'QTextEdit {{'
            f'    border: none;'
            f'    background-color: transparent;'
            f'    color: {rgba_color};'
            f'}}'
        )
        
    def apply_window_background_opacity(self, opacity=None):
        """应用窗口背景透明度（完全透明但不穿透鼠标）"""
        # 使用完全透明的背景，但通过背景框架避免鼠标穿透
        window_style = '''
            QWidget#ReaderWindow {
                background-color: rgba(255, 255, 255, 0);
            }
            QTextEdit {
                background-color: transparent;
                border: none;
                color: rgba(0, 0, 0, 1.0);
            }
        '''
        
        self.setStyleSheet(window_style)
        
        # 设置背景框架为极低透明度但能捕获鼠标事件
        if hasattr(self, 'background_frame'):
            self.background_frame.setStyleSheet(
                'QFrame {'
                '    background-color: rgba(255, 255, 255, 0.004);'  # 极低透明度的白色背景（约1/255）
                '    border: none;'
                '}'
            )
        
        # 确保窗口本身完全不透明
        self.setWindowOpacity(1.0)
        
        # 启用半透明背景支持
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        
        # 设置窗口接受鼠标事件，防止穿透
        self.setAttribute(Qt.WA_NoMousePropagation, False)
        self.setMouseTracking(True)
        
        # 设置对象名称以便样式表识别
        self.setObjectName('ReaderWindow')
        
        # 创建一个不可见的背景层来捕获鼠标事件
        self.setAutoFillBackground(False)
        
        # 重写鼠标事件处理以确保整个窗口区域都能响应
        self.installEventFilter(self)

    def create_dot_cursor(self, diameter=2, color_hex='#000000', opacity=1.0):
        """创建一个小圆点形状的自定义鼠标光标

        作者: MTpupil
        时间: 2025-11-29
        功能: 生成一个透明背景，仅在中心绘制直径为 `diameter` 像素的小圆点的光标。
        适用场景: 自动隐藏（悬停显示/按键显示）模式下，窗口显示时将鼠标替换为不干扰阅读的极简光标。
        依赖条件: PyQt5 已安装，可在 Windows 10/11 专业版上使用。
        风险提示: 自定义光标会覆盖组件原有光标；当需要精确指示（如调整窗口大小）时，圆点光标可能不够直观。
        """
        size = 16
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing, False)
        color = QColor(color_hex)
        color.setAlphaF(max(0.1, min(1.0, opacity)))
        pen = QPen(color)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(color)
        cx = size // 2
        cy = size // 2
        d = max(1, min(16, int(diameter)))
        r = max(1, d // 2)
        painter.drawEllipse(cx - r, cy - r, d, d)
        painter.end()
        # 热点设置为圆心，便于定位
        return QCursor(pm, cx, cy)

    def refresh_dot_cursor_from_config(self):
        cfg = self.config_manager.get_config()
        self.dot_cursor = self.create_dot_cursor(
            diameter=cfg.get('dot_cursor_size', 2),
            color_hex=cfg.get('dot_cursor_color', '#000000'),
            opacity=cfg.get('dot_cursor_opacity', 1.0)
        )
        if self.use_dot_cursor:
            self.apply_cursor_style(use_dot=True)

    def apply_cursor_style(self, use_dot):
        """根据标志应用圆点或箭头光标到相关组件

        作者: MTpupil
        时间: 2025-11-29
        功能: 将光标统一设置到窗口、文本编辑器和背景框架，确保无文本插入光标出现。
        """
        self.use_dot_cursor = bool(use_dot)
        cursor_obj = self.dot_cursor if self.use_dot_cursor else Qt.ArrowCursor
        try:
            self.setCursor(cursor_obj)
            if hasattr(self, 'text_edit') and self.text_edit:
                self.text_edit.setCursor(cursor_obj)
                self.text_edit.viewport().setCursor(cursor_obj)
            if hasattr(self, 'background_frame') and self.background_frame:
                self.background_frame.setCursor(cursor_obj)
        except Exception:
            pass
        
    def update_content_visibility(self):
        """根据配置和当前状态更新窗口可见性"""
        # 如果右键菜单正在显示，不执行隐藏逻辑
        if self.context_menu_showing:
            return
            
        should_show = True
        
        # 根据启用的显示控制功能决定显示条件
        if self.hover_to_show and self.key_to_show:
            # 同时启用鼠标悬停和按键显示的优化逻辑：
            # 1. 如果窗口还未被激活过，需要同时满足鼠标在窗口上AND按键被按下
            # 2. 一旦窗口被激活过，只要鼠标还在窗口内就保持显示，无需按键
            if not self.window_activated:
                # 窗口未激活，需要同时满足鼠标和按键条件
                if self.is_mouse_over and self.is_key_pressed:
                    should_show = True
                    self.window_activated = True  # 标记窗口已被激活
                else:
                    should_show = False
            else:
                # 窗口已激活，只要鼠标在窗口内就显示
                should_show = self.is_mouse_over
                # 如果鼠标离开窗口，重置激活状态，下次需要重新激活
                if not self.is_mouse_over:
                    self.window_activated = False
        elif self.hover_to_show:
            # 只启用鼠标悬停显示：鼠标在窗口上就显示
            should_show = self.is_mouse_over
            # 对于只启用鼠标显示的情况，确保程序启动后鼠标进出就能控制隐藏
            if self.is_mouse_over:
                self.window_activated = True
        elif self.key_to_show:
            # 只启用按键显示：按键被按下就显示
            should_show = self.is_key_pressed
        # 如果都没启用，默认显示
        
        # 如果临时固定显示标志为True，强制显示
        if self.is_temporarily_fixed:
            should_show = True
            
        # 自动阅读与窗口隐藏/显示联动
        if should_show != self.content_visible:
            if not should_show and self.auto_reading and not self.auto_read_paused:
                # 窗口要隐藏，且正在自动阅读且未暂停，则暂停并标记
                self.pause_auto_read()
                self.auto_read_was_paused_by_hide = True
            elif should_show and self.auto_reading and self.auto_read_was_paused_by_hide:
                # 窗口要显示，且之前因隐藏而暂停，则恢复
                self.resume_auto_read()
        
        # 在显示控制模式下，窗口处于显示状态时切换为小圆点光标
        self.apply_cursor_style(use_dot=(should_show and (self.hover_to_show or self.key_to_show)))

        # 更新窗口可见性
        if should_show != self.content_visible:
            self.content_visible = should_show
            if should_show:
                self.show()  # 显示整个窗口
                # 当内容显示时主动请求键盘焦点，确保方向键可用
                # activateWindow可以让窗口成为活动窗口，setFocus确保键盘事件传递到ReaderWindow
                # 注意：我们不将焦点给text_edit，以避免其拦截方向键（已设为NoFocus）
                try:
                    self.activateWindow()
                except Exception:
                    # 某些系统环境下activateWindow可能受限，忽略异常
                    pass
                self.setFocus(Qt.OtherFocusReason)
            else:
                self.hide()  # 隐藏整个窗口
                # 隐藏时恢复箭头光标
                self.apply_cursor_style(use_dot=False)
                
    def check_key_state(self):
        """检查自定义按键是否被按下"""
        try:
            # 统一使用Windows API检测所有按键状态，确保一致性和可靠性
            # Windows虚拟键码映射
            key_codes = {
                'ctrl': 0x11,   # VK_CONTROL
                'alt': 0x12,    # VK_MENU
                'shift': 0x10,  # VK_SHIFT
                'space': 0x20,  # VK_SPACE
                'tab': 0x09,    # VK_TAB
                'enter': 0x0D,  # VK_RETURN
                'esc': 0x1B     # VK_ESCAPE
            }
            
            if self.custom_key in key_codes:
                # 使用GetAsyncKeyState检测按键状态
                # 返回值的最高位表示按键是否被按下
                key_state = ctypes.windll.user32.GetAsyncKeyState(key_codes[self.custom_key])
                return bool(key_state & 0x8000)
            else:
                return False
        except Exception as e:
            # 如果API调用失败，回退到Qt的方法
            from PyQt5.QtWidgets import QApplication
            modifiers = QApplication.keyboardModifiers()
            
            if self.custom_key == 'ctrl':
                return bool(modifiers & Qt.ControlModifier)
            elif self.custom_key == 'alt':
                return bool(modifiers & Qt.AltModifier)
            elif self.custom_key == 'shift':
                return bool(modifiers & Qt.ShiftModifier)
            else:
                return self.is_key_pressed
            
    def check_mouse_position(self):
        """检查鼠标位置是否在窗口区域内"""
        if not (self.hover_to_show or self.key_to_show):
            return  # 如果没有启用相关功能，直接返回
            
        # 获取鼠标全局位置
        from PyQt5.QtGui import QCursor
        mouse_pos = QCursor.pos()
        
        # 获取窗口的全局矩形区域
        # 使用窗口的实际位置和大小，即使窗口隐藏也能正确检测
        if self.isVisible():
            # 窗口可见时，使用当前几何信息
            window_rect = self.geometry()
        else:
            # 窗口隐藏时，使用保存的位置和当前大小
            window_rect = QRect(self.x(), self.y(), self.width(), self.height())
        
        # 检查鼠标是否在窗口区域内
        was_mouse_over = self.is_mouse_over
        self.is_mouse_over = window_rect.contains(mouse_pos)
        
        # 如果启用了按键显示功能，也检查按键状态（特别是修饰键）
        was_key_pressed = self.is_key_pressed
        if self.key_to_show:
            self.is_key_pressed = self.check_key_state()
        
        # 如果状态发生变化，更新窗口可见性
        if was_mouse_over != self.is_mouse_over or was_key_pressed != self.is_key_pressed:
            self.update_content_visibility()
            
    def mousePressEvent(self, event):
        """鼠标按下事件 - 开始拖动"""
        if event.button() == Qt.LeftButton:
            config = self.config_manager.get_config()
            if config.get('show_resize_handles', False):
                # 检查是否点击在调节大小的区域
                resize_direction = self.get_resize_direction(event.pos())
                if resize_direction:
                    self.resizing = True
                    self.resize_direction = resize_direction
                    self.resize_start_pos = event.globalPos()
                    self.resize_start_geometry = self.geometry()
                    event.accept()
                    return
            
            # 普通拖拽窗口
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.RightButton:
            # 右键点击显示菜单
            self.show_context_menu(event.globalPos())
        # 确保事件不会传递给子控件
        event.accept()
            
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖动窗口或调节大小"""
        if event.buttons() == Qt.LeftButton:
            if self.resizing and self.resize_direction:
                # 调节窗口大小
                self.handle_resize(event.globalPos())
                event.accept()
            elif self.is_dragging:
                # 拖动窗口
                new_pos = event.globalPos() - self.drag_position
                self.move(new_pos)
                event.accept()
        else:
            # 更新鼠标光标
            if not self.use_dot_cursor:
                config = self.config_manager.get_config()
                if config.get('show_resize_handles', False):
                    resize_direction = self.get_resize_direction(event.pos())
                    if resize_direction:
                        if resize_direction in ['top_left', 'bottom_right']:
                            self.setCursor(Qt.SizeFDiagCursor)
                        elif resize_direction in ['top_right', 'bottom_left']:
                            self.setCursor(Qt.SizeBDiagCursor)
                    else:
                        self.apply_cursor_style(use_dot=False)
                else:
                    self.apply_cursor_style(use_dot=False)
        # 确保事件不会传递给子控件
        event.accept()
            
    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 结束拖动或调节大小"""
        if event.button() == Qt.LeftButton:
            if self.resizing:
                self.resizing = False
                self.resize_direction = None
                # 保存新的窗口大小
                self.save_window_size()
            else:
                self.is_dragging = False
                # 保存窗口位置
                self.save_window_position()
        # 确保事件不会传递给子控件
        event.accept()
        
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理文本编辑器和背景框架的鼠标事件"""
        # 检查属性是否存在，避免初始化过程中的 AttributeError
        text_edit = getattr(self, 'text_edit', None)
        background_frame = getattr(self, 'background_frame', None)
        
        if obj == text_edit or obj == background_frame or (text_edit and obj == text_edit.viewport()):
            if event.type() == QEvent.MouseButtonPress:
                # 将鼠标按下事件传递给父窗口
                self.mousePressEvent(event)
                return True
            elif event.type() == QEvent.MouseMove:
                # 将鼠标移动事件传递给父窗口
                self.mouseMoveEvent(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                # 将鼠标释放事件传递给父窗口
                self.mouseReleaseEvent(event)
                return True
            elif event.type() == QEvent.Enter:
                # 鼠标进入事件
                self.is_mouse_over = True
                self.update_content_visibility()
                return True
            elif event.type() == QEvent.Leave:
                # 鼠标离开事件
                self.is_mouse_over = False
                self.update_content_visibility()
                return True
            elif event.type() == QEvent.Wheel and (obj == text_edit or (text_edit and obj == text_edit.viewport())):
                # 完全拦截文本编辑器的所有滚轮事件，防止任何字体调节
                # 无论是否按下修饰键，都将滚轮事件传递给父窗口处理翻页功能
                self.wheelEvent(event)
                return True  # 阻止事件传递给QTextEdit，完全禁用其滚轮响应
        return super().eventFilter(obj, event)
        
    def enterEvent(self, event):
        """鼠标进入窗口事件"""
        self.is_mouse_over = True
        self.update_content_visibility()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开窗口事件"""
        self.is_mouse_over = False
        self.update_content_visibility()
        super().leaveEvent(event)
            
    def show_context_menu(self, position):
        """显示右键菜单"""
        # 设置右键菜单显示标志，防止窗口被隐藏
        self.context_menu_showing = True
        
        menu = QMenu(self)
        
        # 书签功能区域（仅在有文件路径时显示）
        if self.file_path:
            # 添加书签
            add_bookmark_action = QAction('添加书签', self)
            add_bookmark_action.triggered.connect(self.add_bookmark)
            menu.addAction(add_bookmark_action)
            
            # 书签管理
            bookmark_action = QAction('书签', self)
            bookmark_action.triggered.connect(self.show_bookmark_window)
            menu.addAction(bookmark_action)
            
            # 全文搜索
            search_action = QAction('搜索', self)
            search_action.triggered.connect(self.show_search_window)
            menu.addAction(search_action)
            
            # 查看目录
            contents_action = QAction('查看目录', self)
            contents_action.triggered.connect(self.show_contents_window)
            menu.addAction(contents_action)
            
            # 分隔线
            menu.addSeparator()
            
            # 自动阅读
            auto_read_text = '停止自动阅读' if self.auto_reading else '开始自动阅读'
            auto_read_action = QAction(auto_read_text, self)
            auto_read_action.triggered.connect(self.toggle_auto_read)
            menu.addAction(auto_read_action)
            
            # 分隔线
            menu.addSeparator()
        
        # 配置选项
        config_action = QAction('配置设置', self)
        config_action.triggered.connect(self.show_config_window)
        menu.addAction(config_action)
        
        # 分隔线
        menu.addSeparator()
        
        # 置顶选项
        stay_on_top_action = QAction('保持置顶', self)
        stay_on_top_action.setCheckable(True)
        stay_on_top_action.setChecked(self.windowFlags() & Qt.WindowStaysOnTopHint)
        stay_on_top_action.triggered.connect(self.toggle_stay_on_top)
        menu.addAction(stay_on_top_action)
        
        # 分隔线
        menu.addSeparator()
        
        # 返回主窗口
        back_action = QAction('返回主窗口', self)
        back_action.triggered.connect(self.back_to_main)
        menu.addAction(back_action)
        
        # 退出选项
        exit_action = QAction('退出', self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)
        
        # 显示菜单
        menu.exec_(position)
        
        # 菜单关闭后清除标志，恢复显示控制逻辑
        self.context_menu_showing = False
        self.update_content_visibility()
        
    def show_config_window(self):
        """显示配置窗口"""
        if self.config_window is None:
            self.config_window = ConfigWindow(self.config_manager, self)
            self.config_window.config_changed.connect(self.on_config_changed)
        else:
            # 每次打开前确保录入状态复位，避免残留“正在录入”提示
            try:
                self.config_window.recording_up = False
                self.config_window.recording_down = False
                if hasattr(self.config_window, 'page_up_record_btn'):
                    self.config_window.page_up_record_btn.setText('录入上一页按键')
                if hasattr(self.config_window, 'page_down_record_btn'):
                    self.config_window.page_down_record_btn.setText('录入下一页按键')
            except Exception:
                pass
        
        self.config_window.show()
        self.config_window.raise_()
        self.config_window.activateWindow()
        
    def add_bookmark(self):
        """添加书签到当前位置"""
        if not self.file_path:
            ToastManager.show_warning('无法为当前内容添加书签！', self)
            return
            
        try:
            # 获取当前阅读位置
            current_line = self.current_line_index + 1  # 转换为1基索引
            current_char_pos = self.get_current_char_position()
            
            # 获取当前行内容作为预览
            if self.text_lines and 0 <= self.current_line_index < len(self.text_lines):
                content_preview = self.text_lines[self.current_line_index].strip()
                if len(content_preview) > 100:
                    content_preview = content_preview[:100] + '...'
            else:
                content_preview = '无内容预览'
                
            # 生成书签名称
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            bookmark_name = f'书签 - {timestamp}'
            
            # 添加书签
            bookmark_id = self.bookmark_manager.add_bookmark(
                file_path=self.file_path,
                title=self.title or os.path.basename(self.file_path),
                name=bookmark_name,
                line_number=current_line,
                char_position=current_char_pos,
                content_preview=content_preview
            )
            
            if bookmark_id:
                # 如果书签窗口已经打开，刷新书签列表显示
                if hasattr(self, 'bookmark_window') and self.bookmark_window is not None:
                    self.bookmark_window.load_bookmarks()
            else:
                ToastManager.show_error('添加书签失败！', self)
        except Exception as e:
            ToastManager.show_error(f'添加书签时发生错误：{str(e)}', self)
            
    def get_current_char_position(self):
        """获取当前字符位置"""
        try:
            # 计算当前行之前的所有字符数
            char_position = 0
            for i in range(self.current_line_index):
                if i < len(self.text_lines):
                    char_position += len(self.text_lines[i]) + 1  # +1 for newline
            return char_position
        except:
            return 0
            
    def show_bookmark_window(self):
        """显示书签管理窗口"""
        if not self.file_path:
            ToastManager.show_warning('无法为当前内容显示书签！', self)
            return
            
        try:
            # 创建或显示书签窗口
            if self.bookmark_window is None or not self.bookmark_window.isVisible():
                # 如果窗口不存在或已关闭，创建新的窗口实例
                self.bookmark_window = BookmarkWindow(self.file_path, self.title, self.bookmark_manager, self)
                self.bookmark_window.bookmark_selected.connect(self.goto_bookmark)
                # 连接窗口关闭信号，确保窗口关闭时清理引用
                self.bookmark_window.finished.connect(lambda: setattr(self, 'bookmark_window', None))
            else:
                # 如果窗口已存在且可见，刷新书签数据
                self.bookmark_window.load_bookmarks()
                
            self.bookmark_window.show()
            self.bookmark_window.raise_()
            self.bookmark_window.activateWindow()
            
        except Exception as e:
            ToastManager.show_error(f'打开书签窗口时发生错误：{str(e)}', self)
            
    def goto_bookmark(self, bookmark):
        """跳转到指定书签位置"""
        try:
            line_number = bookmark.get('line_number', 1)
            char_position = bookmark.get('char_position', 0)
            
            # 跳转到指定行
            self.jump_to_line(line_number)
            
            # 保存阅读位置
            self.save_reading_position()
            
            ToastManager.show_success(f'已跳转到书签：{bookmark.get("name", "未知书签")}', self)
            
        except Exception as e:
            ToastManager.show_error(f'跳转到书签时发生错误：{str(e)}', self)
            
    def show_search_window(self):
        """显示全文搜索窗口"""
        if not self.file_path:
            ToastManager.show_warning('无法为当前内容进行搜索！', self)
            return
            
        try:
            # 获取当前阅读位置（行号）
            current_line = self.current_line_index + 1  # 转换为1基索引
            
            # 创建或显示搜索窗口，传递当前阅读位置
            if self.search_window is None:
                self.search_window = SearchWindow(self.file_path, self.title, current_line, self)
                self.search_window.search_result_selected.connect(self.goto_search_result)
            else:
                # 更新搜索窗口的当前位置
                self.search_window.current_line = current_line
                self.search_window.search_after_current_cb.setEnabled(current_line > 0)
                
            self.search_window.show()
            self.search_window.raise_()
            self.search_window.activateWindow()
            
        except Exception as e:
            ToastManager.show_error(f'打开搜索窗口时发生错误：{str(e)}', self)
    def goto_search_result(self, line_number):
        """跳转到搜索结果位置"""
        try:
            # 跳转到指定行
            self.jump_to_line(line_number)
            
            # 保存阅读位置
            self.save_reading_position()
            
            ToastManager.show_success(f'已跳转到第 {line_number} 行', self)
            
        except Exception as e:
            ToastManager.show_error(f'跳转到搜索结果时发生错误：{str(e)}', self)
            
    def save_reading_position(self):
        """保存当前阅读位置到历史记录"""
        if not self.file_path or not hasattr(self, 'history_manager'):
            return
            
        try:
            # 使用当前的行索引和字符偏移
            current_line_index = getattr(self, 'current_line_index', 0)
            current_char_offset = getattr(self, 'current_char_offset', 0)
            
            # 获取总行数
            total_lines = len(self.text_lines) if hasattr(self, 'text_lines') and self.text_lines else 0
            
            # 更新阅读位置
            self.history_manager.update_reading_position(
                file_path=self.file_path,
                title=self.title or os.path.basename(self.file_path),
                current_line_index=current_line_index,
                current_char_offset=current_char_offset,
                total_lines=total_lines
            )
            
        except Exception as e:
            # 保存阅读位置失败，不影响正常使用
            pass
        
    def on_config_changed(self):
        """配置改变时的处理"""
        # 配置变更信号处理
        config = self.config_manager.get_config()
        
        # 不在配置改变时重置窗口尺寸，避免用户手动调整的尺寸被覆盖
        # 窗口尺寸只在load_config时应用，或者用户在配置界面明确修改时才生效
        
        # 更新文字设置
        self.apply_text_config(config)
        
        # 更新显示模式
        self.update_display_mode()
        
        # 重新加载显示控制设置
        self.hover_to_show = config.get('hover_to_show', False)
        self.key_to_show = config.get('key_to_show', False)
        self.custom_key = config.get('custom_key', 'ctrl')
        # 自定义翻页按键更新
        self.page_up_keys = config.get('page_up_keys', [])
        self.page_down_keys = config.get('page_down_keys', [])
        # 调试信息
        print(f"[调试-on_config_changed] 配置更新! 上一页按键: {self.page_up_keys}, 下一页按键: {self.page_down_keys}")
        
        # 根据新配置更新窗口可见性
        # 如果启用了显示控制功能，需要重新评估窗口状态
        if self.hover_to_show or self.key_to_show:
            # 重新检查鼠标位置和按键状态
            self.check_mouse_position()
            # 检查按键状态（如果启用了按键显示功能）
            if self.key_to_show:
                self.is_key_pressed = self.check_key_state()
        # 刷新圆点光标设置并立即应用（可见时更新样式）
        self.refresh_dot_cursor_from_config()
        self.update_content_visibility()
        
        # 更新四角标记显示
        self.update()  # 触发重绘
        
    def toggle_stay_on_top(self, checked):
        """切换置顶状态"""
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()  # 重新显示窗口以应用标志更改
    
    def get_current_chapter_info(self):
        """获取当前章节信息和进度"""
        # 获取当前行号
        current_line = self.current_line_index + 1
        total_lines = len(self.text_lines)
        
        # 计算全书进度
        book_progress = (current_line / total_lines) * 100 if total_lines > 0 else 0
        
        # 默认章节信息
        chapter_name = "未识别章节"
        chapter_progress = 0.0
        
        try:
            # 检查是否已缓存章节信息，避免重复解析
            if not hasattr(self, '_cached_chapters') or not self._cached_chapters:
                # 导入目录解析器
                from table_of_contents import TableOfContents
                
                # 创建目录解析器实例
                toc_parser = TableOfContents()
                
                # 解析当前文本的章节
                chapters = toc_parser.parse_contents(self.full_text)
                
                # 缓存章节信息
                self._cached_chapters = chapters
            else:
                # 使用缓存的章节信息
                chapters = self._cached_chapters
            
            if chapters:
                # 查找当前行所在的章节
                current_chapter_index = -1
                for i, chapter in enumerate(chapters):
                    if current_line >= chapter['line_number']:
                        current_chapter_index = i
                    else:
                        break
                
                if current_chapter_index >= 0:
                    # 获取当前章节信息
                    current_chapter = chapters[current_chapter_index]
                    chapter_name = current_chapter['title']
                    
                    # 计算本章进度
                    # 本章起始行号
                    chapter_start = current_chapter['line_number']
                    
                    # 本章结束行号（下一章的起始行号减1，或文件末尾）
                    if current_chapter_index < len(chapters) - 1:
                        chapter_end = chapters[current_chapter_index + 1]['line_number'] - 1
                    else:
                        chapter_end = total_lines
                    
                    # 计算本章进度
                    chapter_length = chapter_end - chapter_start + 1
                    if chapter_length > 0:
                        chapter_progress = ((current_line - chapter_start + 1) / chapter_length) * 100
        
        except Exception as e:
            # 如果获取章节信息失败，使用默认值
            pass
        
        return chapter_name, book_progress, chapter_progress
    
    def show_progress_tooltip(self):
        """显示进度悬浮窗"""
        if not self.progress_tooltip:
            return
        
        # 获取鼠标位置
        mouse_pos = QCursor.pos()
        
        # 获取阅读器窗口矩形
        reader_rect = self.geometry()
        
        # 检查鼠标是否在阅读器窗口内
        if not reader_rect.contains(mouse_pos):
            # 鼠标不在阅读器内，隐藏悬浮窗
            self.hide_progress_tooltip()
            return
        
        # 添加标志位，确保按住Ctrl+E期间只更新一次悬浮窗内容
        if not hasattr(self, '_tooltip_updated') or not self._tooltip_updated:
            # 获取当前章节信息和进度
            chapter_name, book_progress, chapter_progress = self.get_current_chapter_info()
            
            # 更新悬浮窗内容
            self.progress_tooltip.update_progress(chapter_name, book_progress, chapter_progress)
            
            # 标记已经更新过内容
            self._tooltip_updated = True
        
        # 在鼠标位置显示悬浮窗
        self.progress_tooltip.show_at_position(mouse_pos, reader_rect)
        
        # 启动定时器持续检查鼠标位置，确保鼠标移出时隐藏悬浮窗
        if not hasattr(self, '_tooltip_mouse_timer'):
            self._tooltip_mouse_timer = QTimer(self)
            self._tooltip_mouse_timer.timeout.connect(self.check_tooltip_mouse_position)
        self._tooltip_mouse_timer.start(100)  # 每100毫秒检查一次
        
    def check_tooltip_mouse_position(self):
        """持续检查鼠标位置，确保悬浮窗只在鼠标位于阅读器内时显示"""
        if not self.progress_tooltip or not self.progress_tooltip.isVisible():
            # 如果悬浮窗不可见，停止检查
            if hasattr(self, '_tooltip_mouse_timer'):
                self._tooltip_mouse_timer.stop()
            return
        
        # 获取鼠标位置
        mouse_pos = QCursor.pos()
        
        # 获取阅读器窗口矩形
        reader_rect = self.geometry()
        
        # 检查鼠标是否在阅读器窗口内
        if not reader_rect.contains(mouse_pos):
            # 鼠标不在阅读器内，隐藏悬浮窗
            self.hide_progress_tooltip()
            # 停止定时器
            if hasattr(self, '_tooltip_mouse_timer'):
                self._tooltip_mouse_timer.stop()
    
    def hide_progress_tooltip(self):
        """隐藏进度悬浮窗"""
        if self.progress_tooltip:
            self.progress_tooltip.hide()
        
        # 重置标志位，允许下次显示时重新更新内容
        self._tooltip_updated = False
        
        # 停止定时器，避免资源浪费
        if hasattr(self, '_tooltip_mouse_timer'):
            self._tooltip_mouse_timer.stop()
        
    def back_to_main(self):
        """返回主窗口"""
        self.save_window_position()
        self.close()
        if self.main_window:
            self.main_window.show_main_window()
            
    def save_window_position(self):
        """保存窗口位置和大小"""
        config = self.config_manager.get_config()
        config['window_x'] = self.x()
        config['window_y'] = self.y()
        config['window_width'] = self.width()
        config['window_height'] = self.height()
        self.config_manager.save_config(config)
        
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 保存窗口大小
        self.save_window_position()
        
        # 重新计算显示模式（主要是多行模式下的每页行数），保持当前阅读位置
        if hasattr(self, 'text_lines') and self.text_lines:
            self.update_display_mode(preserve_position=True)
            
    def get_visible_complete_lines(self):
        """获取当前窗口能显示的完整行文本"""
        if not self.text_lines:
            return ''
            
        start_line = self.current_line_index
        end_line = min(start_line + self.lines_per_page, len(self.text_lines))
        
        visible_lines = self.text_lines[start_line:end_line]
        return '\n'.join(visible_lines)
        
    def install_global_event_filter(self):
        """安装全局事件过滤器，用于监听Ctrl+`组合键"""
        # 全局事件过滤器已经在当前类中实现，不需要单独创建
        # 我们将使用定时器定期检查键盘状态，确保无论窗口是否有焦点都能捕获Ctrl+`组合键
        if not hasattr(self, '_global_hotkey_timer'):
            self._global_hotkey_timer = QTimer(self)
            self._global_hotkey_timer.timeout.connect(self.check_global_hotkey)
            self._global_hotkey_timer.start(100)  # 每100毫秒检查一次
        
    def remove_global_event_filter(self):
        """移除全局事件过滤器"""
        # 停止全局热键定时器
        if hasattr(self, '_global_hotkey_timer'):
            self._global_hotkey_timer.stop()
            delattr(self, '_global_hotkey_timer')
        
    def check_global_hotkey(self):
        """定期检查全局热键状态，不依赖于窗口焦点"""
        try:
            import ctypes
            # VK_BACKQUOTE = 0xC0，VK_CONTROL = 0x11
            # 使用GetAsyncKeyState检测按键状态，确保全局生效
            backquote_state = ctypes.windll.user32.GetAsyncKeyState(0xC0) & 0x8000
            ctrl_state = ctypes.windll.user32.GetAsyncKeyState(0x11) & 0x8000
            
            # 检查是否同时按下了Ctrl+`组合键
            if backquote_state and ctrl_state:
                # 只在按键按下的瞬间处理，避免重复触发
                if not getattr(self, '_hotkey_was_pressed', False):
                    # 按照要求的逻辑执行：
                    # 1. 如果flag是true，直接取消固定并隐藏
                    if self.is_temporarily_fixed:
                        self.is_temporarily_fixed = False
                        self.content_visible = False
                        self.hide()
                    else:
                        # 2. 如果flag是false，检查是否有焦点，有焦点就固定
                        if self.hasFocus():
                            self.is_temporarily_fixed = True
                            self.content_visible = True
                            self.show()
                    
                    # 标记按键已按下，避免重复触发
                    self._hotkey_was_pressed = True
            else:
                # 按键已释放，重置标记
                self._hotkey_was_pressed = False
        except:
            # 忽略异常，避免影响程序运行
            pass
    
    def eventFilter(self, obj, event):
        """事件过滤器 - 处理窗口内的事件"""
        # 调用原有的事件过滤器逻辑
        text_edit = getattr(self, 'text_edit', None)
        background_frame = getattr(self, 'background_frame', None)
        
        if obj == text_edit or obj == background_frame or (text_edit and obj == text_edit.viewport()):
            if event.type() == QEvent.MouseButtonPress:
                # 将鼠标按下事件传递给父窗口
                self.mousePressEvent(event)
                return True
            elif event.type() == QEvent.MouseMove:
                # 将鼠标移动事件传递给父窗口
                self.mouseMoveEvent(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                # 将鼠标释放事件传递给父窗口
                self.mouseReleaseEvent(event)
                return True
            elif event.type() == QEvent.Enter:
                # 鼠标进入事件
                self.is_mouse_over = True
                self.update_content_visibility()
                return True
            elif event.type() == QEvent.Leave:
                # 鼠标离开事件
                self.is_mouse_over = False
                self.update_content_visibility()
                return True
            elif event.type() == QEvent.Wheel and (obj == text_edit or (text_edit and obj == text_edit.viewport())):
                # 完全拦截文本编辑器的所有滚轮事件，防止任何字体调节
                # 无论是否按下修饰键，都将滚轮事件传递给父窗口处理翻页功能
                self.wheelEvent(event)
                return True  # 阻止事件传递给QTextEdit，完全禁用其滚轮响应
        
        return super().eventFilter(obj, event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止自动阅读定时器
        self.stop_auto_read()
        
        # 停止定时器
        if hasattr(self, 'mouse_check_timer'):
            self.mouse_check_timer.stop()
        
        # 停止悬浮窗相关定时器
        if hasattr(self, '_tooltip_mouse_timer'):
            self._tooltip_mouse_timer.stop()
        
        # 移除全局事件过滤器
        self.remove_global_event_filter()
        
        self.save_window_position()
        
        # 关闭配置窗口
        if self.config_window:
            self.config_window.close()
            
        # 发出关闭信号
        self.closed.emit()
        
        # 显示主窗口（仅当不是应用整体退出时）
        if self.main_window and not getattr(self.main_window, 'exiting', False):
            self.main_window.show_main_window()
            
        event.accept()
        
    def keyPressEvent(self, event):
        """键盘按键事件"""
        # 如果内容未显示，不处理方向键翻页，避免误触
        # 只有当文字显示时，才允许方向键翻页（符合用户期望的交互）
        content_visible_now = getattr(self, 'content_visible', True)
        
        # 检查是否是自定义按键
        key_pressed = False
        if self.custom_key == 'ctrl' and event.key() == Qt.Key_Control:
            key_pressed = True
        elif self.custom_key == 'alt' and event.key() == Qt.Key_Alt:
            key_pressed = True
        elif self.custom_key == 'shift' and event.key() == Qt.Key_Shift:
            key_pressed = True
        elif self.custom_key == 'space' and event.key() == Qt.Key_Space:
            key_pressed = True
        elif self.custom_key == 'tab' and event.key() == Qt.Key_Tab:
            key_pressed = True
        elif self.custom_key == 'enter' and event.key() == Qt.Key_Return:
            key_pressed = True
        elif self.custom_key == 'esc' and event.key() == Qt.Key_Escape:
            key_pressed = True
            
        # 更新按键状态
        if key_pressed:
            self.is_key_pressed = True
            self.update_content_visibility()
            
        # ESC键关闭窗口（如果不是自定义按键）
        if event.key() == Qt.Key_Escape and self.custom_key != 'esc':
            # ESC键关闭窗口
            self.close()
        # Ctrl+Q 退出应用 - 添加调试信息并检查是否来自配置窗口
        elif event.key() == Qt.Key_Q and event.modifiers() == Qt.ControlModifier:
            # Ctrl+Q 快捷键处理
            if self.config_window and self.config_window.isVisible():
                # 如果配置窗口正在显示，不退出程序，而是关闭配置窗口
                self.config_window.close()
            else:
                # 执行程序退出
                QApplication.quit()
        # Ctrl+F 打开搜索窗口
        elif event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            # 快捷键打开搜索窗口
            self.show_search_window()
        # Ctrl+I 打开设置窗口
        elif event.key() == Qt.Key_I and event.modifiers() == Qt.ControlModifier:
            # 快捷键打开设置窗口
            self.show_config_window()
        # Ctrl+` 临时固定显示阅读器 - 已移至全局热键检测，此处不再处理
        elif event.key() == Qt.Key_QuoteLeft and event.modifiers() == Qt.ControlModifier:
            # 直接返回，不做处理，避免与全局热键冲突
            return
        # Ctrl+A 开始/关闭自动阅读
        elif event.key() == Qt.Key_A and event.modifiers() == Qt.ControlModifier:
            self.toggle_auto_read()
        # Ctrl+E 显示章节信息和进度悬浮窗
        elif event.key() == Qt.Key_E and event.modifiers() == Qt.ControlModifier:
            # 显示悬浮窗
            self.show_progress_tooltip()
        # 空格 - 暂停/恢复自动阅读（仅在自动阅读时有效）
        elif event.key() == Qt.Key_Space and event.modifiers() == Qt.NoModifier:
            if self.auto_reading:
                if self.auto_read_paused:
                    self.resume_auto_read()
                else:
                    self.pause_auto_read()
            else:
                # 不是自动阅读状态，按原逻辑处理
                super().keyPressEvent(event)
        # 上键 - 翻页
        elif event.key() == Qt.Key_Up:
            if content_visible_now:
                self.page_up()
        # 下键 - 翻页
        elif event.key() == Qt.Key_Down:
            if content_visible_now:
                self.page_down()
        # 左键 - 减慢自动阅读速度（仅在自动阅读时有效）
        elif event.key() == Qt.Key_Left:
            if self.auto_reading:
                self.decrease_auto_read_speed()
        # 右键 - 加快自动阅读速度（仅在自动阅读时有效）
        elif event.key() == Qt.Key_Right:
            if self.auto_reading:
                self.increase_auto_read_speed()
        # PageUp/PageDown 支持 - 常见期望的翻页键
        elif event.key() == Qt.Key_PageUp:
            if content_visible_now:
                self.page_up()
        elif event.key() == Qt.Key_PageDown:
            if content_visible_now:
                self.page_down()
        # 自定义翻页按键：使用 Qt 键值作为 token，支持所有按键（不受输入法影响）
        else:
            # 禁止组合键：仅在无修饰键时才响应自定义翻页按键
            if event.modifiers() == Qt.NoModifier and content_visible_now:
                # 识别按键 token（使用 Qt 键值）
                key_token = None
                key_value = event.key()
                
                # 对于特殊键，用特殊名称
                if key_value == Qt.Key_Space:
                    key_token = 'space'
                elif key_value in (Qt.Key_Return, Qt.Key_Enter):
                    key_token = 'enter'
                elif key_value == Qt.Key_Tab:
                    key_token = 'tab'
                else:
                    # 对于其他键，用字符串形式的键值作为 token
                    key_token = str(key_value)
                
                # 根据用户设置触发翻页
                if key_token:
                    # 调试：打印按键信息
                    print(f"[调试] 按键识别: key={key_value}, text={repr(event.text())}, token={repr(key_token)}")
                    print(f"[调试] 上一页按键列表: {self.page_up_keys}")
                    print(f"[调试] 下一页按键列表: {self.page_down_keys}")
                    
                    if key_token in (self.page_up_keys or []):
                        self.page_up()
                        event.accept()
                        return
                    if key_token in (self.page_down_keys or []):
                        self.page_down()
                        event.accept()
                        return
            # 其他按键按原逻辑处理
            super().keyPressEvent(event)
            
    def keyReleaseEvent(self, event):
        """键盘按键释放事件"""
        # 检查是否是自定义按键被释放
        key_released = False
        if self.custom_key == 'ctrl' and event.key() == Qt.Key_Control:
            key_released = True
        elif self.custom_key == 'alt' and event.key() == Qt.Key_Alt:
            key_released = True
        elif self.custom_key == 'shift' and event.key() == Qt.Key_Shift:
            key_released = True
        elif self.custom_key == 'space' and event.key() == Qt.Key_Space:
            key_released = True
        elif self.custom_key == 'tab' and event.key() == Qt.Key_Tab:
            key_released = True
        elif self.custom_key == 'enter' and event.key() == Qt.Key_Return:
            key_released = True
        elif self.custom_key == 'esc' and event.key() == Qt.Key_Escape:
            key_released = True
            
        # 更新按键状态
        if key_released:
            self.is_key_pressed = False
            self.update_content_visibility()
        
        # 修复Ctrl+E窗口不消失问题：只要释放了Ctrl或E键，就隐藏悬浮窗
        if event.key() in [Qt.Key_Control, Qt.Key_E]:
            # 检查是否还同时按住了Ctrl+E，使用event.modifiers()代替keyboardModifiers()
            if not (event.modifiers() & Qt.ControlModifier and event.key() != Qt.Key_Control):
                self.hide_progress_tooltip()
        
        super().keyReleaseEvent(event)
            
    def wheelEvent(self, event):
        """鼠标滚轮事件 - 实现翻页功能"""
        # 获取滚轮滚动的角度
        angle_delta = event.angleDelta().y()
        
        # 向上滚动（正值）- 向上翻页
        if angle_delta > 0:
            self.page_up()
        # 向下滚动（负值）- 向下翻页
        elif angle_delta < 0:
            self.page_down()
            
        # 接受事件，防止传递给父控件
        event.accept()
        
    def paintEvent(self, event):
        """绘制事件 - 绘制四角调节大小标记"""
        super().paintEvent(event)
        
        config = self.config_manager.get_config()
        if config.get('show_resize_handles', False):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 设置画笔
            pen = QPen(QColor(100, 100, 100), 2)
            painter.setPen(pen)
            
            # 获取窗口尺寸
            width = self.width()
            height = self.height()
            handle_size = self.resize_handle_size
            
            # 绘制四个角的标记
            # 左上角
            painter.drawLine(0, 0, handle_size, 0)
            painter.drawLine(0, 0, 0, handle_size)
            
            # 右上角
            painter.drawLine(width - handle_size, 0, width, 0)
            painter.drawLine(width, 0, width, handle_size)
            
            # 左下角
            painter.drawLine(0, height - handle_size, 0, height)
            painter.drawLine(0, height, handle_size, height)
            
            # 右下角
            painter.drawLine(width - handle_size, height, width, height)
            painter.drawLine(width, height - handle_size, width, height)
            
    def get_resize_direction(self, pos):
        """根据鼠标位置判断调节大小的方向"""
        width = self.width()
        height = self.height()
        handle_size = self.resize_handle_size
        
        x, y = pos.x(), pos.y()
        
        # 检查是否在四个角的范围内
        if x <= handle_size and y <= handle_size:
            return 'top_left'
        elif x >= width - handle_size and y <= handle_size:
            return 'top_right'
        elif x <= handle_size and y >= height - handle_size:
            return 'bottom_left'
        elif x >= width - handle_size and y >= height - handle_size:
            return 'bottom_right'
        
        return None
         
    def handle_resize(self, global_pos):
        """处理窗口大小调节"""
        if not self.resizing or not self.resize_direction:
            return
            
        # 计算鼠标移动的距离
        delta = global_pos - self.resize_start_pos
        dx, dy = delta.x(), delta.y()
        
        # 获取原始窗口几何信息
        start_rect = self.resize_start_geometry
        x, y, w, h = start_rect.x(), start_rect.y(), start_rect.width(), start_rect.height()
        
        # 设置最小窗口大小限制：宽度100px，高度35px
        min_width, min_height =100, 35
        
        # 根据调节方向计算新的窗口位置和大小
        if self.resize_direction == 'top_left':
            new_x = x + dx
            new_y = y + dy
            new_w = max(min_width, w - dx)
            new_h = max(min_height, h - dy)
            # 如果达到最小尺寸，不移动窗口位置
            if new_w == min_width:
                new_x = x + w - min_width
            if new_h == min_height:
                new_y = y + h - min_height
                
        elif self.resize_direction == 'top_right':
            new_x = x
            new_y = y + dy
            new_w = max(min_width, w + dx)
            new_h = max(min_height, h - dy)
            # 如果达到最小高度，不移动窗口位置
            if new_h == min_height:
                new_y = y + h - min_height
                
        elif self.resize_direction == 'bottom_left':
            new_x = x + dx
            new_y = y
            new_w = max(min_width, w - dx)
            new_h = max(min_height, h + dy)
            # 如果达到最小宽度，不移动窗口位置
            if new_w == min_width:
                new_x = x + w - min_width
                
        elif self.resize_direction == 'bottom_right':
            new_x = x
            new_y = y
            new_w = max(min_width, w + dx)
            new_h = max(min_height, h + dy)
            
        # 应用新的窗口几何信息
        self.setGeometry(new_x, new_y, new_w, new_h)
        
    def save_window_size(self):
        """保存窗口大小到配置，并同步更新配置窗口"""
        config = self.config_manager.get_config()
        config['window_width'] = self.width()
        config['window_height'] = self.height()
        self.config_manager.save_config(config)
        
        # 如果配置窗口已打开，同步更新其显示值
        if hasattr(self, 'config_window') and self.config_window and self.config_window.isVisible():
            self.config_window.width_spinbox.setValue(self.width())
            self.config_window.height_spinbox.setValue(self.height())
    
    def set_window_on_all_desktops(self):
        """设置窗口在所有虚拟桌面显示"""
        try:
            # 获取窗口句柄
            hwnd = int(self.winId())
            
            # 定义Windows API常量
            GWLP_EXSTYLE = -20
            WS_EX_TOOLWINDOW = 0x00000080
            
            # 获取当前扩展样式
            user32 = ctypes.windll.user32
            current_style = user32.GetWindowLongPtrW(hwnd, GWLP_EXSTYLE)
            
            # 添加WS_EX_TOOLWINDOW样式（进一步确保不显示在任务栏）
            new_style = current_style | WS_EX_TOOLWINDOW
            user32.SetWindowLongPtrW(hwnd, GWLP_EXSTYLE, new_style)
            
            # 尝试设置窗口在所有虚拟桌面显示（Windows 10+）
            # 这个API可能不是所有Windows版本都支持，所以用try-except包装
            try:
                # 定义GUID for IVirtualDesktopManager
                from ctypes import POINTER, Structure, c_void_p, c_ulong
                import uuid
                
                # 创建COM对象来管理虚拟桌面
                ole32 = ctypes.windll.ole32
                ole32.CoInitialize(None)
                
                # 虚拟桌面管理器的CLSID
                CLSID_VirtualDesktopManager = uuid.UUID('{aa509086-5ca9-4c25-8f95-589d3c07b48a}')
                IID_IVirtualDesktopManager = uuid.UUID('{a5cd92ff-29be-454c-8d04-d82879fb3f1b}')
                
                # 尝试创建虚拟桌面管理器（仅Windows 10+支持）
                # 如果失败，窗口仍然会因为Qt.Tool标志而不显示在任务栏
                pass  # 简化实现，主要依赖Qt.Tool标志
                
            except Exception:
                # 虚拟桌面API不可用，忽略错误
                # 窗口仍然会因为Qt.Tool标志而不显示在任务栏和Alt+Tab中
                pass
                
        except Exception as e:
            # 如果Windows API调用失败，记录错误但不影响程序运行
            # print(f"设置窗口属性时出错: {e}")  # 移除调试输出
            # 程序仍然可以正常运行，只是可能在某些情况下会显示在任务栏
            pass
            
    def jump_to_position(self, char_position):
        """跳转到指定字符位置"""
        print(f"[调试] jump_to_position 被调用，目标字符位置: {char_position}")
        try:
            # 确保文本行已经初始化
            if not hasattr(self, 'text_lines') or not self.text_lines:
                print(f"[调试] 跳转失败: 文本行数据不存在")
                return
                
            # 在原始内容中查找目标位置对应的行和字符偏移
            current_pos = 0
            target_line_index = 0
            target_char_offset = 0
            
            for i, line in enumerate(self.text_lines):
                line_end_pos = current_pos + len(line)
                if char_position <= line_end_pos:
                    # 找到目标行
                    target_line_index = i
                    target_char_offset = char_position - current_pos
                    break
                current_pos = line_end_pos + 1  # +1 for newline character
            else:
                # 如果没有找到对应行，跳转到最后一行
                target_line_index = len(self.text_lines) - 1
                target_char_offset = 0
            
            print(f"[调试] 计算得到目标行: {target_line_index}, 字符偏移: {target_char_offset}")
            
            # 参考 restore_reading_position 方法的实现，直接设置位置并更新显示
            # 确保目标行索引在有效范围内
            self.current_line_index = min(target_line_index, len(self.text_lines) - 1)
            
            # 检查当前显示模式
            config = self.config_manager.get_config()
            single_line_mode = config.get('single_line_mode', False)
            
            if single_line_mode:
                # 单行模式：设置字符偏移
                self.current_char_offset = target_char_offset
                print(f"[调试] 单行模式 - 设置行索引: {self.current_line_index}, 字符偏移: {self.current_char_offset}")
            else:
                # 多行模式：重置字符偏移（多行模式不使用字符偏移）
                if hasattr(self, 'current_char_offset'):
                    self.current_char_offset = 0
                print(f"[调试] 多行模式 - 设置行索引: {self.current_line_index}")
            
            # 直接更新文本显示，这与 restore_reading_position 方法的做法一致
            self.update_text_display()
            
            print(f"[调试] 跳转完成，当前显示起始行: {self.current_line_index}")
                    
        except Exception as e:
            print(f"[调试] 跳转到位置时出错: {e}")
            pass
            
    def jump_to_line(self, line_number):
        """跳转到指定行号（从1开始计数）"""
        print(f"[调试] jump_to_line 被调用，目标行号: {line_number}")
        try:
            # 转换为从0开始的索引
            line_index = max(0, line_number - 1)
            print(f"[调试] 转换为索引: {line_index}")
            
            # 确保行索引在有效范围内
            if hasattr(self, 'text_lines') and self.text_lines:
                line_index = min(line_index, len(self.text_lines) - 1)
                
                # 参考 restore_reading_position 方法的实现，直接设置位置并更新显示
                # 确保目标行索引在有效范围内
                self.current_line_index = min(line_index, len(self.text_lines) - 1)
                
                print(f"[调试] 设置当前行索引为: {self.current_line_index}")
                
                # 检查当前显示模式
                config = self.config_manager.get_config()
                single_line_mode = config.get('single_line_mode', False)
                print(f"[调试] 当前显示模式 - 单行模式: {single_line_mode}")
                
                if single_line_mode:
                    # 单行模式：设置字符偏移为0（行首）
                    self.current_char_offset = 0
                    print(f"[调试] 单行模式 - 设置行索引: {self.current_line_index}, 字符偏移: 0")
                else:
                    # 多行模式：重置字符偏移（多行模式不使用字符偏移）
                    if hasattr(self, 'current_char_offset'):
                        self.current_char_offset = 0
                    print(f"[调试] 多行模式 - 设置行索引: {self.current_line_index}")
                
                # 直接更新文本显示，这与 restore_reading_position 方法的做法一致
                self.update_text_display()
                
                print(f"[调试] 跳转到行号完成，当前显示起始行: {self.current_line_index}")
                
        except Exception as e:
            print(f"[调试] 跳转到行号时出错: {e}")
            pass

    def toggle_auto_read(self):
        """切换自动阅读状态（开始/停止）"""
        if self.auto_reading:
            self.stop_auto_read()
        else:
            self.start_auto_read()

    def start_auto_read(self):
        """开始自动阅读"""
        config = self.config_manager.get_config()
        speed = config.get('auto_read_speed', 2.0)
        
        self.auto_reading = True
        self.auto_read_paused = False
        self.auto_read_was_paused_by_hide = False
        
        # 启动定时器
        self.update_auto_read_timer()

    def stop_auto_read(self):
        """停止自动阅读"""
        if self.auto_read_timer:
            self.auto_read_timer.stop()
        
        self.auto_reading = False
        self.auto_read_paused = False
        self.auto_read_was_paused_by_hide = False

    def pause_auto_read(self):
        """暂停自动阅读"""
        if self.auto_reading and not self.auto_read_paused:
            if self.auto_read_timer:
                self.auto_read_timer.stop()
            self.auto_read_paused = True

    def resume_auto_read(self):
        """恢复自动阅读"""
        if self.auto_reading and self.auto_read_paused:
            self.auto_read_paused = False
            self.auto_read_was_paused_by_hide = False
            self.update_auto_read_timer()

    def auto_read_step(self):
        """自动翻页执行方法"""
        if not self.auto_reading or self.auto_read_paused:
            return
        
        # 保存当前位置，用于判断是否到达末尾
        old_line_index = self.current_line_index
        old_char_offset = getattr(self, 'current_char_offset', 0)
        
        # 执行翻页
        self.page_down()
        
        # 检查是否到达末尾（位置没有变化）
        if (self.current_line_index == old_line_index and 
            getattr(self, 'current_char_offset', 0) == old_char_offset):
            # 到达末尾，停止自动阅读
            self.stop_auto_read()

    def increase_auto_read_speed(self):
        """加快自动阅读速度"""
        config = self.config_manager.get_config()
        current_speed = config.get('auto_read_speed', 2.0)
        min_speed = config.get('auto_read_speed_min', 0.5)
        step = config.get('auto_read_speed_step', 0.5)
        
        new_speed = max(min_speed, current_speed - step)
        config['auto_read_speed'] = new_speed
        self.config_manager.save_config(config)
        
        # 如果正在自动阅读，更新定时器
        if self.auto_reading and not self.auto_read_paused:
            self.update_auto_read_timer()
        
        # 如果配置窗口打开，刷新配置显示
        if self.config_window and hasattr(self.config_window, 'refresh_config'):
            self.config_window.refresh_config()

    def decrease_auto_read_speed(self):
        """减慢自动阅读速度"""
        config = self.config_manager.get_config()
        current_speed = config.get('auto_read_speed', 2.0)
        max_speed = config.get('auto_read_speed_max', 10.0)
        step = config.get('auto_read_speed_step', 0.5)
        
        new_speed = min(max_speed, current_speed + step)
        config['auto_read_speed'] = new_speed
        self.config_manager.save_config(config)
        
        # 如果正在自动阅读，更新定时器
        if self.auto_reading and not self.auto_read_paused:
            self.update_auto_read_timer()
        
        # 如果配置窗口打开，刷新配置显示
        if self.config_window and hasattr(self.config_window, 'refresh_config'):
            self.config_window.refresh_config()

    def update_auto_read_timer(self):
        """更新自动阅读定时器"""
        if not self.auto_reading or self.auto_read_paused:
            return
        
        config = self.config_manager.get_config()
        speed = config.get('auto_read_speed', 2.0)
        interval = int(speed * 1000)
        
        if self.auto_read_timer:
            self.auto_read_timer.stop()
            self.auto_read_timer.start(interval)

    def show_contents_window(self):
        """显示目录页面并自动定位到当前章节"""
        if not self.file_path:
            return
        
        try:
            from contents_window import ContentsWindow
            
            # 构造书籍信息
            book_info = {
                'file_path': self.file_path,
                'name': self.title,
                'display_name': self.title
            }
            
            # 获取当前阅读的行号（转换为1基）
            current_line_number = self.current_line_index + 1
            
            # 创建目录窗口
            if self.contents_window is None or not self.contents_window.isVisible():
                self.contents_window = ContentsWindow(
                    book_info, 
                    current_line_number=current_line_number,
                    parent=self
                )
                self.contents_window.chapter_selected.connect(self.goto_chapter_from_contents)
                self.contents_window.finished.connect(lambda: setattr(self, 'contents_window', None))
            else:
                # 窗口已存在，更新当前行号
                self.contents_window.current_line_number = current_line_number
                # 如果目录已解析，重新高亮
                if hasattr(self.contents_window, 'chapters') and self.contents_window.chapters:
                    self.contents_window.highlight_current_chapter()
            
            self.contents_window.show()
            self.contents_window.raise_()
            self.contents_window.activateWindow()
            
        except Exception as e:
            print(f"[调试] 打开目录窗口时出错: {e}")
            pass

    def goto_chapter_from_contents(self, chapter):
        """从目录跳转到指定章节"""
        try:
            line_number = chapter.get('line_number', 1)
            self.jump_to_line(line_number)
            self.save_reading_position()
        except Exception as e:
            print(f"[调试] 跳转到章节时出错: {e}")
            pass
