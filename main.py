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
    QInputDialog, QTabWidget, QFrame, QSplitter, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QGridLayout, QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QFontDatabase, QColor

from reader_window import ReaderWindow
from config_manager import ConfigManager
from history_manager import HistoryManager
from book_item_widget import BookItemWidget, BookCardWidget
from file_utils import detect_encoding_and_read_file, read_file_content
from resource_path import get_resource_path, find_icon_file

# 现代UI：无边框窗口（可选）
try:
    from qframelesswindow import FramelessMainWindow as _BaseMainWindow
except Exception:
    _BaseMainWindow = QMainWindow

# Fluent 组件
try:
    from qfluentwidgets import PrimaryPushButton, setTheme, Theme
except Exception:
    PrimaryPushButton = QPushButton
    def setTheme(x):
        pass
    class Theme:
        AUTO = None



class MainWindow(_BaseMainWindow):
    """主窗口类 - 用于选择文件和启动阅读器"""
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()  # 历史记录管理器
        self.reader_window = None
        self.selected_file = None
        self.tray_icon = None
        # 应用退出标志：用于避免退出时短暂显示主窗口
        self.exiting = False
        
        # 书架相关属性 - 使用AppData目录
        appdata_dir = os.path.expanduser('~\\AppData\\Roaming\\ReadFish')
        # 确保目录存在
        os.makedirs(appdata_dir, exist_ok=True)
        self.book_folder = os.path.join(appdata_dir, 'book')
        self.bookshelf_data_file = os.path.join(appdata_dir, 'bookshelf.json')
        self.books_data = {}
        self.groups_data = None  # 书籍分组（嵌套虚拟分组）
        
        # 初始化书架系统
        self.init_bookshelf()
        self.init_ui()
        self.init_tray_icon()
        
        # 初始化完成后刷新书架显示
        self.refresh_bookshelf()
        self.update_continue_button_state()  # 更新继续阅读按钮状态
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('ReadFish')
        self.setFixedSize(1000, 680)
        try:
            setTheme(Theme.AUTO)
        except Exception:
            pass
        
        # 设置应用程序图标
        # 使用资源路径处理模块来正确获取图标文件路径
        icon_path = find_icon_file()
        if icon_path:
            # 找到图标文件，创建图标对象
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.setWindowIcon(icon)
                print(f"[DEBUG] 窗口图标设置成功: {icon_path}")
            else:
                print(f"[WARNING] 图标文件加载失败: {icon_path}")
        else:
            print(f"[ERROR] 未找到任何图标文件")
        
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
        
        modern_root = self.create_modern_bookshelf_tab()
        main_layout.addWidget(title_label)
        main_layout.addWidget(modern_root)

        # 无边框标题栏置顶以支持拖动
        try:
            self.titleBar.raise_()
        except Exception:
            pass
        
        # 公众号区域不再加载，保持简洁现代
        
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
    
    def create_wechat_info_widget(self):
        """创建公众号信息区域"""
        # 创建主容器
        wechat_widget = QFrame()
        wechat_widget.setFrameStyle(QFrame.NoFrame)
        wechat_widget.setStyleSheet(
            'QFrame {'
            '    background-color: #f8f9fa;'
            '    margin: 5px;'
            '}'
        )
        wechat_widget.setFixedHeight(180)
        
        # 创建水平布局
        layout = QHBoxLayout(wechat_widget)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        # 左侧：公众号信息
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        # 公众号标题
        title_label = QLabel('关注我的公众号')
        title_label.setFont(QFont('Microsoft YaHei', 12, QFont.Bold))
        title_label.setStyleSheet('color: #2c3e50;')
        
        # 公众号名称
        name_label = QLabel('木瞳科技Pro')
        name_label.setFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        name_label.setStyleSheet('color: #e74c3c; margin: 2px 0;')
        
        # 公众号描述
        desc_label = QLabel('有趣的灵魂互相吸引')
        desc_label.setFont(QFont('Microsoft YaHei', 10))
        desc_label.setStyleSheet('color: #7f8c8d;')
        desc_label.setWordWrap(True)
        
        # 扫码提示
        scan_label = QLabel('扫描右侧二维码关注 →')
        scan_label.setFont(QFont('Microsoft YaHei', 9))
        scan_label.setStyleSheet('color: #95a5a6; margin-top: 5px;')
        
        info_layout.addWidget(title_label)
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        info_layout.addWidget(scan_label)
        info_layout.addStretch()
        
        # 右侧：二维码
        qr_layout = QVBoxLayout()
        qr_layout.setAlignment(Qt.AlignCenter)
        
        # 二维码标签
        qr_label = QLabel()
        qr_label.setFixedSize(150, 150)
        qr_label.setAlignment(Qt.AlignCenter)
        qr_label.setStyleSheet(
            'QLabel {'
            '    border: 1px solid #bdc3c7;'
            '    border-radius: 4px;'
            '    background-color: white;'
            '}'
        )
        
        # 加载二维码图片（使用资源路径处理模块）
        try:
            # 使用资源路径处理模块获取正确的二维码图片路径
            qr_path = get_resource_path('qrcode.png')
            print(f"[DEBUG] 尝试加载二维码图片: {qr_path}")
            
            # 检查文件是否存在
            if os.path.exists(qr_path):
                qr_pixmap = QPixmap(qr_path)
                if not qr_pixmap.isNull():
                    # 缩放图片以适应标签大小
                    scaled_pixmap = qr_pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    qr_label.setPixmap(scaled_pixmap)
                    print(f"[DEBUG] 二维码图片加载成功: {qr_path}")
                else:
                    print(f"[WARNING] 二维码图片加载失败(null pixmap): {qr_path}")
                    # 如果图片加载失败，显示文字
                    qr_label.setText('二维码')
                    qr_label.setStyleSheet(
                        qr_label.styleSheet() + 
                        'color: #95a5a6; font-size: 12px;'
                    )
            else:
                print(f"[ERROR] 二维码图片文件不存在: {qr_path}")
                # 如果文件不存在，显示文字
                qr_label.setText('二维码')
                qr_label.setStyleSheet(
                    qr_label.styleSheet() + 
                    'color: #95a5a6; font-size: 12px;'
                )
        except Exception as e:
            print(f"[ERROR] 二维码图片加载异常: {e}")
            # 异常处理：显示文字替代
            qr_label.setText('二维码')
            qr_label.setStyleSheet(
                qr_label.styleSheet() + 
                'color: #95a5a6; font-size: 12px;'
            )
        
        qr_layout.addWidget(qr_label)
        
        # 添加到主布局
        layout.addLayout(info_layout, 3)  # 信息区域占3份
        layout.addLayout(qr_layout, 1)    # 二维码区域占1份
        
        return wechat_widget
        
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
        
        # 打开书架目录按钮（Windows上打开 %APPDATA%\ReadFish\book）
        self.open_folder_button = QPushButton('打开书架目录')
        self.open_folder_button.setFixedHeight(35)
        self.open_folder_button.setStyleSheet(
            'QPushButton {'
            '    background-color: #2ecc71; '
            '    color: white; '
            '    border: none; '
            '    border-radius: 6px; '
            '    font-size: 13px; '
            '    font-weight: bold; '
            '    padding: 0 15px;'
            '}'
            'QPushButton:hover {'
            '    background-color: #27ae60;'
            '}'
            'QPushButton:pressed {'
            '    background-color: #1e8449;'
            '}'
        )
        self.open_folder_button.clicked.connect(self.open_bookshelf_folder)

        button_layout.addWidget(self.import_book_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.open_folder_button)
        button_layout.addStretch()
        
        # 书架树（支持分组嵌套）
        self.book_tree = QTreeWidget()
        self.book_tree.setHeaderHidden(True)
        self.book_tree.setStyleSheet(
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
        # 树右键菜单与双击阅读
        self.book_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.book_tree.customContextMenuRequested.connect(self.show_book_context_menu_tree)
        self.book_tree.itemDoubleClicked.connect(self.read_book_from_tree)
        # 启用拖拽导入
        self.book_tree.setAcceptDrops(True)
        self.book_tree.installEventFilter(self)
        
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
        layout.addWidget(self.book_tree)
        layout.addWidget(self.bookshelf_status_label)
        
        return tab

    def create_modern_bookshelf_tab(self):
        tab = QWidget()
        from PyQt5.QtWidgets import QHBoxLayout
        layout = QHBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        sidebar = QFrame()
        sidebar.setFixedWidth(160)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(12,12,12,12)
        s_layout.setSpacing(10)
        # 拟物风格包裹 + 阴影
        sidebar.setStyleSheet('QFrame{background:#f7f9fb; border-radius:12px; border:1px solid #e1e8ed;}')
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0,0,0,60))
        sidebar.setGraphicsEffect(shadow)

        # 上区：书架
        shelf_label = QLabel('书架')
        shelf_label.setStyleSheet('color:#7f8c8d; font-weight:bold;')
        self.shelf_list = QListWidget()
        self.shelf_list.itemSelectionChanged.connect(self.on_shelf_changed)
        self.shelf_list.setStyleSheet('QListWidget{border:none; background:transparent;}')
        s_layout.addWidget(shelf_label)
        s_layout.addWidget(self.shelf_list)
        # 下区：设置 / 帮助
        other_label = QLabel('其他')
        other_label.setStyleSheet('color:#7f8c8d; font-weight:bold;')
        self.tools_list = QListWidget()
        self.tools_list.itemSelectionChanged.connect(self.on_tools_changed)
        self.tools_list.setStyleSheet('QListWidget{border:none; background:transparent;}')
        s_layout.addWidget(other_label)
        s_layout.addWidget(self.tools_list)

        right = QFrame()
        r_layout = QVBoxLayout(right)
        r_layout.setContentsMargins(0,0,0,0)
        r_layout.setSpacing(8)
        tb = QHBoxLayout()
        self.import_book_button2 = PrimaryPushButton('导入书籍')
        self.import_book_button2.clicked.connect(self.import_book)
        self.refresh_button2 = PrimaryPushButton('刷新书架')
        self.refresh_button2.clicked.connect(self.refresh_bookshelf)
        self.open_folder_button2 = PrimaryPushButton('打开书架目录')
        self.open_folder_button2.clicked.connect(self.open_bookshelf_folder)
        for b in [self.import_book_button2, self.refresh_button2, self.open_folder_button2]:
            b.setFixedHeight(32)
        tb.addWidget(self.import_book_button2)
        tb.addWidget(self.refresh_button2)
        tb.addWidget(self.open_folder_button2)
        tb.addStretch()
        r_layout.addLayout(tb)
        self.card_scroll = QScrollArea()
        self.card_scroll.setWidgetResizable(True)
        self.card_host = QWidget()
        self.card_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.card_grid = QGridLayout(self.card_host)
        self.card_grid.setContentsMargins(10,10,10,10)
        self.card_grid.setHorizontalSpacing(20)
        self.card_grid.setVerticalSpacing(20)
        try:
            self.card_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        except Exception:
            pass
        self.card_scroll.setWidget(self.card_host)
        r_layout.addWidget(self.card_scroll)
        self.bookshelf_status_label2 = QLabel('书架为空，请导入书籍')
        self.bookshelf_status_label2.setAlignment(Qt.AlignCenter)
        r_layout.addWidget(self.bookshelf_status_label2)

        layout.addWidget(sidebar)
        layout.addWidget(right, stretch=1)

        self.card_scroll.setAcceptDrops(True)
        self.card_scroll.installEventFilter(self)
        self.ensure_groups_structure()
        self.build_sidebar_sections()
        self.populate_cards_for_current_category()

        return tab
        
    def init_bookshelf(self):
        """初始化书架系统"""
        # 创建book文件夹（如果不存在）
        if not os.path.exists(self.book_folder):
            os.makedirs(self.book_folder)
            
        # 加载书架数据
        self.load_bookshelf_data()
        # 确保分组结构存在
        self.ensure_groups_structure()

    def open_bookshelf_folder(self):
        """打开书架所在的文件夹"""
        try:
            if os.path.exists(self.book_folder):
                os.startfile(self.book_folder)
            else:
                QMessageBox.warning(self, '提示', '书架目录不存在！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'无法打开书架目录：{str(e)}')
        
    def load_bookshelf_data(self):
        """加载书架数据"""
        if os.path.exists(self.bookshelf_data_file):
            try:
                with open(self.bookshelf_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # 兼容老格式（仅书籍映射）或新格式（包含分组）
                if isinstance(data, dict) and 'books' in data and 'groups' in data:
                    self.books_data = data.get('books', {})
                    self.groups_data = data.get('groups', None)
                else:
                    self.books_data = data if isinstance(data, dict) else {}
                    self.groups_data = None
            except Exception as e:
                self.books_data = {}
                QMessageBox.warning(self, '警告', f'加载书架数据失败：{str(e)}')
        else:
            self.books_data = {}
            self.groups_data = None
            
    def save_bookshelf_data(self):
        """保存书架数据"""
        try:
            payload = {
                'books': self.books_data,
                'groups': self.groups_data if self.groups_data else self.build_default_groups()
            }
            with open(self.bookshelf_data_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存书架数据失败：{str(e)}')
            
    def import_book(self):
        """导入书籍到书架（支持TXT和EPUB格式）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择要导入的书籍文件（支持TXT和EPUB格式）',
            '',
            'Text files (*.txt);;EPUB files (*.epub);;All files (*)'
        )
        
        if not file_path:
            return
            
        self.import_book_file(file_path)

    def import_book_file(self, file_path):
        """从指定路径导入书籍文件（支持TXT/EPUB），复用现有导入逻辑"""
        if not file_path:
            return
        try:
            file_name = os.path.basename(file_path)
            book_name = os.path.splitext(file_name)[0]
            # 询问用户是否要自定义书名
            custom_name, ok = QInputDialog.getText(
                self,
                '设置书名',
                f'请输入书名（默认：{book_name}）：',
                text=book_name
            )
            if ok and custom_name.strip():
                book_name = custom_name.strip()
            # 冲突处理
            if book_name in self.books_data:
                reply = QMessageBox.question(
                    self,
                    '书名冲突',
                    f'书架中已存在名为"{book_name}"的书籍，是否覆盖？',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            # 生成唯一目标文件
            import time
            timestamp = str(int(time.time()))
            target_filename = f"{timestamp}_{file_name}"
            target_path = os.path.join(self.book_folder, target_filename)
            shutil.copy2(file_path, target_path)
            # 保存书籍信息
            self.books_data[book_name] = {
                'file_path': target_path,
                'original_name': file_name,
                'import_time': timestamp,
                'display_name': book_name
            }
            self.save_bookshelf_data()
            self.refresh_bookshelf()
            QMessageBox.information(self, '成功', f'书籍"{book_name}"已成功导入书架！')
        except Exception as e:
            QMessageBox.critical(self, '错误', f'导入书籍失败：{str(e)}')

    def eventFilter(self, obj, event):
        """事件过滤：支持拖拽导入到书架列表"""
        if obj is getattr(self, 'book_list', None) or obj is getattr(self, 'book_tree', None) or obj is getattr(self, 'card_scroll', None):
            from PyQt5.QtCore import QEvent
            from PyQt5.QtGui import QDropEvent
            if event.type() == QEvent.DragEnter or event.type() == QEvent.DragMove:
                mime = event.mimeData()
                if mime.hasUrls():
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.Drop:
                mime = event.mimeData()
                if mime.hasUrls():
                    for url in mime.urls():
                        path = url.toLocalFile()
                        if path and os.path.isfile(path):
                            ext = os.path.splitext(path)[1].lower()
                            if ext in ['.txt', '.epub']:
                                self.import_book_file(path)
                    event.acceptProposedAction()
                    return True
            elif event.type() == QEvent.Resize and obj is getattr(self, 'card_scroll', None):
                self.populate_cards_for_current_category()
        return super().eventFilter(obj, event)
            
    def refresh_bookshelf(self):
        """刷新书架显示（树形分组）"""
        self.book_tree.clear() if hasattr(self, 'book_tree') else None
        self.clear_card_grid() if hasattr(self, 'card_grid') else None
        
        # 检查并清理不存在的文件记录
        books_to_remove = []
        for book_name, book_info in self.books_data.items():
            file_path = book_info.get('file_path', '')
            if file_path and not os.path.exists(file_path):
                books_to_remove.append(book_name)
        
        # 移除不存在的文件记录
        for book_name in books_to_remove:
            del self.books_data[book_name]
        
        # 如果有记录被移除，保存数据
        if books_to_remove:
            self.save_bookshelf_data()
        
        if not self.books_data:
            if hasattr(self, 'bookshelf_status_label'):
                self.bookshelf_status_label.setText('书架为空，请导入书籍')
                self.bookshelf_status_label.show()
            if hasattr(self, 'bookshelf_status_label2'):
                self.bookshelf_status_label2.setText('书架为空，请导入书籍')
                self.bookshelf_status_label2.show()
            return
            
        if hasattr(self, 'bookshelf_status_label'):
            self.bookshelf_status_label.hide()
        if hasattr(self, 'bookshelf_status_label2'):
            self.bookshelf_status_label2.hide()
        
        # 分组树构建
        self.ensure_groups_structure()
        if hasattr(self, 'book_tree'):
            self.build_tree_view()
        if hasattr(self, 'shelf_list'):
            self.build_sidebar_sections()
            self.populate_cards_for_current_category()

    def build_default_groups(self):
        """根据当前书籍构建默认分组结构"""
        return {
            'name': 'root',
            'children': [
                {
                    'name': '未分组',
                    'children': [],
                    'books': list(self.books_data.keys())
                }
            ]
        }

    def ensure_groups_structure(self):
        """确保分组结构存在（兼容旧数据）"""
        if not self.groups_data:
            self.groups_data = self.build_default_groups()

    def build_tree_view(self):
        """根据分组数据构建树形视图"""
        self.book_tree.clear()
        def add_group(parent_item, group_node, path):
            group_item = QTreeWidgetItem(parent_item, [group_node['name']])
            group_item.setData(0, Qt.UserRole, {'type': 'group', 'path': path})
            # 添加书籍子项
            for book_name in group_node.get('books', []):
                info = self.books_data.get(book_name)
                if not info:
                    continue
                leaf = QTreeWidgetItem(group_item)
                book_info_with_name = info.copy()
                book_info_with_name['name'] = book_name
                leaf.setData(0, Qt.UserRole, book_info_with_name)
                widget = BookItemWidget(book_name, book_info_with_name)
                widget.continue_reading.connect(self.continue_reading_from_shelf)
                widget.start_reading.connect(self.start_reading_from_shelf)
                widget.rename_book.connect(self.rename_book_from_widget)
                widget.delete_book.connect(self.delete_book_from_widget)
                widget.show_contents.connect(self.show_book_contents)
                self.book_tree.setItemWidget(leaf, 0, widget)
            # 递归子分组
            for idx, child in enumerate(group_node.get('children', [])):
                add_group(group_item, child, path + [idx])
        # 根
        root = QTreeWidgetItem(self.book_tree, ['书架'])
        root.setData(0, Qt.UserRole, {'type': 'root'})
        for i, child in enumerate(self.groups_data.get('children', [])):
            add_group(root, child, [i])
        self.book_tree.expandAll()

    def build_sidebar_sections(self):
        # 上区
        self.shelf_list.clear()
        all_item = QListWidgetItem('全部')
        all_item.setData(Qt.UserRole, {'type': 'all'})
        self.shelf_list.addItem(all_item)
        for idx, group in enumerate(self.groups_data.get('children', [])):
            # 不显示“未分组”
            if group.get('name') == '未分组':
                continue
            it = QListWidgetItem(group.get('name', f'分组{idx+1}'))
            it.setData(Qt.UserRole, {'type': 'group', 'index': idx})
            self.shelf_list.addItem(it)
        self.shelf_list.setCurrentRow(0)
        # 下区
        self.tools_list.clear()
        settings_item = QListWidgetItem('设置')
        settings_item.setData(Qt.UserRole, {'type': 'settings'})
        help_item = QListWidgetItem('帮助')
        help_item.setData(Qt.UserRole, {'type': 'help'})
        self.tools_list.addItem(settings_item)
        self.tools_list.addItem(help_item)

    def clear_card_grid(self):
        if not hasattr(self, 'card_grid'):
            return
        while self.card_grid.count():
            item = self.card_grid.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)

    def populate_cards_for_current_category(self):
        if not hasattr(self, 'card_grid'):
            return
        self.clear_card_grid()
        if self.shelf_list.currentItem() is None:
            return
        data = self.shelf_list.currentItem().data(Qt.UserRole)
        names = []
        if data.get('type') == 'all':
            names = list(self.books_data.keys())
        elif data.get('type') == 'group':
            idx = data.get('index', 0)
            names = self.groups_data.get('children', [])[idx].get('books', [])
        vw =  self.card_scroll.viewport().width() if hasattr(self.card_scroll, 'viewport') else 600
        card_w = 150
        gap = self.card_grid.horizontalSpacing() or 20
        cols = max(1, min(8, vw // (card_w + gap)))
        # 设置列拉伸，留出右侧空白以保证左对齐
        for i in range(cols):
            self.card_grid.setColumnStretch(i, 0)
        self.card_grid.setColumnStretch(cols, 1)
        row = 0
        col = 0
        for name in names:
            info = self.books_data.get(name)
            if not info:
                continue
            info_with_name = info.copy()
            info_with_name['name'] = name
            card = BookCardWidget(name, info_with_name)
            card.continue_reading.connect(self.continue_reading_from_shelf)
            card.start_reading.connect(self.start_reading_from_shelf)
            card.rename_book.connect(self.rename_book_from_widget)
            card.delete_book.connect(self.delete_book_from_widget)
            card.show_contents.connect(self.show_book_contents)
            self.card_grid.addWidget(card, row, col)
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def on_shelf_changed(self):
        self.populate_cards_for_current_category()

    def on_tools_changed(self):
        item = self.tools_list.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole)
        t = data.get('type')
        if t == 'settings':
            self.open_settings()
        elif t == 'help':
            self.show_help()

    def open_settings(self):
        try:
            from config_window import ConfigWindow
            self._config_window = getattr(self, '_config_window', None)
            if self._config_window is None:
                self._config_window = ConfigWindow(self.config_manager, self)
                self._config_window.config_changed.connect(lambda: self.refresh_bookshelf())
            self._config_window.show()
            self._config_window.raise_()
            self._config_window.activateWindow()
        except Exception as e:
            QMessageBox.critical(self, '错误', f'打开设置失败：{str(e)}')

    def show_help(self):
        msg = (
            'ReadFish 书架重构版：\n'
            ' - 左侧选择分组或功能\n'
            ' - 右侧双击书籍继续阅读；右键菜单提供所有操作\n'
            ' - 顶部可导入/刷新/打开书架目录'
        )
        QMessageBox.information(self, '帮助', msg)

    def read_book_from_tree(self, item, column):
        """树节点双击阅读（叶子节点）"""
        data = item.data(0, Qt.UserRole)
        if isinstance(data, dict) and 'file_path' in data:
            file_path = data['file_path']
            if not os.path.exists(file_path):
                QMessageBox.warning(self, '警告', '书籍文件不存在，可能已被删除！')
                return
            self.selected_file = file_path
            self.start_reading()

    def show_book_context_menu_tree(self, position):
        """树形书架右键菜单：支持分组与书籍"""
        item = self.book_tree.itemAt(position)
        if not item:
            return
        data = item.data(0, Qt.UserRole)
        menu = QMenu(self)
        if isinstance(data, dict) and data.get('type') == 'group':
            # 分组操作
            add_group_action = QAction('新建子分组', self)
            add_group_action.triggered.connect(lambda: self.create_subgroup_at(data.get('path', [])))
            menu.addAction(add_group_action)
            rename_group_action = QAction('重命名分组', self)
            rename_group_action.triggered.connect(lambda: self.rename_group_at(data.get('path', [])))
            menu.addAction(rename_group_action)
            delete_group_action = QAction('删除分组', self)
            delete_group_action.triggered.connect(lambda: self.delete_group_at(data.get('path', [])))
            menu.addAction(delete_group_action)
        else:
            # 书籍操作
            read_action = QAction('阅读', self)
            read_action.triggered.connect(lambda: self.read_book_from_tree(item, 0))
            menu.addAction(read_action)
            menu.addSeparator()
            rename_action = QAction('重命名', self)
            rename_action.triggered.connect(lambda: self.rename_book_tree(item))
            menu.addAction(rename_action)
            delete_action = QAction('删除', self)
            delete_action.triggered.connect(lambda: self.delete_book_tree(item))
            menu.addAction(delete_action)
        menu.exec_(self.book_tree.mapToGlobal(position))

    def get_group_node(self, path):
        """根据路径获取分组节点"""
        node = self.groups_data
        for idx in path:
            node = node['children'][idx]
        return node

    def create_subgroup_at(self, path):
        name, ok = QInputDialog.getText(self, '新建子分组', '请输入分组名称：')
        if ok and name.strip():
            node = self.get_group_node(path)
            node.setdefault('children', []).append({'name': name.strip(), 'children': [], 'books': []})
            self.save_bookshelf_data()
            self.refresh_bookshelf()

    def rename_group_at(self, path):
        node = self.get_group_node(path)
        name, ok = QInputDialog.getText(self, '重命名分组', '请输入新的分组名称：', text=node.get('name', ''))
        if ok and name.strip():
            node['name'] = name.strip()
            self.save_bookshelf_data()
            self.refresh_bookshelf()

    def delete_group_at(self, path):
        if not path:
            QMessageBox.warning(self, '警告', '根分组不可删除！')
            return
        parent = self.get_group_node(path[:-1])
        idx = path[-1]
        # 删除分组前，将书籍移动到“未分组”
        moving = parent['children'][idx].get('books', [])
        ungroup = self.groups_data['children'][0]  # 默认“未分组”
        ungroup['books'].extend(moving)
        del parent['children'][idx]
        self.save_bookshelf_data()
        self.refresh_bookshelf()

    def rename_book_tree(self, item):
        info = item.data(0, Qt.UserRole)
        old_name = info.get('name', '')
        new_name, ok = QInputDialog.getText(self, '重命名书籍', '请输入新的书籍名称：', text=old_name)
        if ok and new_name.strip() and new_name.strip() != old_name:
            new_name = new_name.strip()
            if new_name in self.books_data:
                QMessageBox.warning(self, '警告', '该书籍名称已存在！')
                return
            book_data = self.books_data.pop(old_name)
            book_data['name'] = new_name
            self.books_data[new_name] = book_data
            # 更新分组中的引用
            def replace_name(node):
                node['books'] = [new_name if n == old_name else n for n in node.get('books', [])]
                for c in node.get('children', []):
                    replace_name(c)
            replace_name(self.groups_data)
            self.save_bookshelf_data()
            self.refresh_bookshelf()

    def delete_book_tree(self, item):
        info = item.data(0, Qt.UserRole)
        book_name = info.get('name', '')
        file_path = info.get('file_path', '')
        reply = QMessageBox.question(
            self, '确认删除', f'确定要删除书籍《{book_name}》吗？\n\n注意：这将同时删除书架记录和文件！',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                if book_name in self.books_data:
                    del self.books_data[book_name]
                # 从分组删除引用
                def remove_name(node):
                    node['books'] = [n for n in node.get('books', []) if n != book_name]
                    for c in node.get('children', []):
                        remove_name(c)
                remove_name(self.groups_data)
                # 历史
                if file_path:
                    self.history_manager.remove_book(file_path)
                self.save_bookshelf_data()
                self.refresh_bookshelf()
                self.update_continue_button_state()
                QMessageBox.information(self, '成功', f'书籍《{book_name}》已删除！')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除书籍失败：{str(e)}')
            
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
        # 从item的UserRole数据中获取书籍信息
        book_info = item.data(Qt.UserRole)
        if not book_info:
            QMessageBox.warning(self, '错误', '无法获取书籍信息！')
            return
            
        # 从书籍信息中获取书名，如果没有name字段则从books_data中查找
        book_name = book_info.get('name', '')
        if not book_name:
            # 通过file_path在books_data中查找对应的书名
            file_path = book_info.get('file_path', '')
            for name, info in self.books_data.items():
                if info.get('file_path') == file_path:
                    book_name = name
                    break
        
        if not book_name:
            book_name = '未知书籍'
            
        reply = QMessageBox.question(
            self, 
            '确认删除', 
            f'确定要删除书籍《{book_name}》吗？\n\n注意：这将同时删除书架记录和文件！',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 获取文件路径并删除文件
                file_path = book_info.get('file_path', '')
                
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                    
                # 从书架数据中删除记录（确保删除正确的记录）
                if book_name in self.books_data:
                    del self.books_data[book_name]
                else:
                    # 如果按书名找不到，尝试按文件路径删除
                    books_to_remove = []
                    for name, info in self.books_data.items():
                        if info.get('file_path') == file_path:
                            books_to_remove.append(name)
                    
                    for name in books_to_remove:
                        del self.books_data[name]
                
                # 从历史记录中移除
                if file_path:
                    self.history_manager.remove_book(file_path)
                
                # 保存数据并刷新显示
                self.save_bookshelf_data()
                self.refresh_bookshelf()
                self.update_continue_button_state()
                
                QMessageBox.information(self, '成功', f'书籍《{book_name}》已删除！')
                
            except Exception as e:
                QMessageBox.critical(self, '错误', f'删除书籍失败：{str(e)}')
                
    def update_continue_button_state(self):
        """更新继续阅读按钮状态"""
        # 检查是否有历史记录
        has_history = self.history_manager.has_history()
        if hasattr(self, 'continue_button'):
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
                    if hasattr(self, 'current_book_label'):
                        self.current_book_label.setText(f'当前阅读：《{display_name}》')
                        self.current_book_label.setVisible(True)
                else:
                    if hasattr(self, 'current_book_label'):
                        self.current_book_label.setVisible(False)
            else:
                if hasattr(self, 'current_book_label'):
                    self.current_book_label.setVisible(False)
        else:
            if hasattr(self, 'current_book_label'):
                self.current_book_label.setVisible(False)
            
        # 继续阅读按钮始终显示固定文本
        if hasattr(self, 'continue_button'):
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
        # 获取书名，优先从book_info中获取，如果没有则通过file_path查找
        book_name = book_info.get('name', '')
        file_path = book_info.get('file_path', '')
        
        # 如果book_info中没有name字段，通过file_path在books_data中查找
        if not book_name and file_path:
            for name, info in self.books_data.items():
                if info.get('file_path') == file_path:
                    book_name = name
                    break
        
        # 如果还是没有找到书名，使用默认值
        if not book_name:
            book_name = '未知书籍'
        
        reply = QMessageBox.question(
            self, '确认删除', 
            f'确定要删除书籍《{book_name}》吗？\n\n注意：这将同时删除书架记录和原文件！',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 删除原文件
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
                
                # 从书架数据中移除（确保删除正确的记录）
                if book_name in self.books_data:
                    del self.books_data[book_name]
                else:
                    # 如果按书名找不到，尝试按文件路径删除
                    books_to_remove = []
                    for name, info in self.books_data.items():
                        if info.get('file_path') == file_path:
                            books_to_remove.append(name)
                    
                    for name in books_to_remove:
                        del self.books_data[name]
                    
                # 从历史记录中移除
                if file_path:
                    self.history_manager.remove_book(file_path)
                    
                # 保存数据并刷新显示
                self.save_bookshelf_data()
                self.refresh_bookshelf()
                self.update_continue_button_state()
                
                QMessageBox.information(self, '成功', f'书籍《{book_name}》已删除！')
                
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
            
        # 使用智能文件读取函数（支持TXT和EPUB）
        content, error_message = read_file_content(file_path)
        
        if content is None:
            QMessageBox.critical(self, '错误', f'无法读取文件：{error_message}')
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
        # 传递历史管理器给阅读器窗口
        reader.history_manager = self.history_manager
        
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
        """选择阅读文件（支持TXT和EPUB格式）"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            '选择阅读文件（支持TXT和EPUB格式）',
            '',
            'Text files (*.txt);;EPUB files (*.epub);;All files (*)'
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
            QMessageBox.warning(self, '警告', '请先选择一个文件！')
            return
            
        # 使用智能文件读取函数（支持TXT和EPUB）
        content, error_message = read_file_content(self.selected_file)
        
        if content is None:
            QMessageBox.critical(self, '错误', f'无法读取文件：{error_message}')
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
        # 传递历史管理器给阅读器窗口
        self.reader_window.history_manager = self.history_manager
        self.reader_window.show()
        
    def start_reading_without_history(self, file_path):
        """从头开始阅读，不恢复历史位置"""
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, '警告', '文件不存在！')
            return
            
        # 使用智能文件读取函数（支持TXT和EPUB）
        content, error_message = read_file_content(file_path)
        
        if content is None:
            QMessageBox.critical(self, '错误', f'无法读取文件：{error_message}')
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
        # 传递历史管理器给阅读器窗口
        self.reader_window.history_manager = self.history_manager
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
        
    def create_fallback_icon(self):
        """
        创建备选图标（绿色圆点）
        当无法加载正常图标时使用
        """
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.green)
        painter.setPen(Qt.darkGreen)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        return QIcon(pixmap)
    
    def init_tray_icon(self):
        """初始化系统托盘图标"""
        # 检查系统是否支持托盘图标
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "系统托盘", "系统不支持托盘图标功能")
            return
            
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置托盘图标
        # 使用资源路径处理模块来正确获取图标文件路径
        icon_path = find_icon_file()
        if icon_path:
            # 找到图标文件，创建图标对象
            icon = QIcon(icon_path)
            if icon.isNull():
                print(f"[WARNING] 托盘图标加载失败: {icon_path}")
                # 创建备选图标（绿色圆点）
                icon = self.create_fallback_icon()
            else:
                print(f"[DEBUG] 托盘图标设置成功: {icon_path}")
        else:
            print(f"[ERROR] 未找到图标文件，使用备选图标")
            # 创建备选图标（绿色圆点）
            icon = self.create_fallback_icon()
        
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("ReadFish - 摸个鱼吧")
        
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
        # 设置退出标志，通知子窗口不要唤起主窗口
        self.exiting = True
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
    
    # 在Windows上设置应用程序用户模型ID，确保任务栏图标正确显示
    try:
        import ctypes
        # 设置应用程序用户模型ID，这有助于Windows正确识别应用程序
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('ReadFish.ReadFish.1.0')
    except:
        pass  # 如果设置失败，继续执行
    
    # 设置应用程序图标（用于任务栏和进程）
    # 使用资源路径处理模块来正确获取图标文件路径
    from resource_path import find_icon_file
    
    icon_path = find_icon_file()
    if icon_path:
        # 找到图标文件，创建图标对象
        app_icon = QIcon(icon_path)
        if not app_icon.isNull():
            # 设置应用程序图标
            app.setWindowIcon(app_icon)
            # 在Windows上，还需要设置应用程序图标属性
            try:
                app.setProperty('windowIcon', app_icon)
            except:
                pass
            print(f"[DEBUG] 应用程序图标设置成功: {icon_path}")
        else:
            print(f"[WARNING] 应用程序图标加载失败: {icon_path}")
    else:
        print(f"[ERROR] 未找到任何图标文件，应用程序将使用默认图标")
    
    # 设置应用程序在最后一个窗口关闭时不自动退出
    # 这样即使所有窗口都隐藏了，程序也会继续运行（通过托盘图标维持）
    app.setQuitOnLastWindowClosed(False)

    # 统一使用 Fluent 主题，避免 qt_material 资源路径兼容问题
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
