# -*- coding: utf-8 -*-
"""
书籍列表项组件
实现带有操作图标的书籍列表项
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QByteArray, QRectF, QSize
import time
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QPixmap, QPainterPath, QImage
import random
import math
_COVER_CACHE = {}


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
    move_book = pyqtSignal(dict)
    drop_group_create = pyqtSignal(str, str)
    selection_changed = pyqtSignal(str, bool)
    move_book = pyqtSignal(dict)
    drop_group_create = pyqtSignal(str, str)
    selection_changed = pyqtSignal(str, bool)

    def __init__(self, book_name, book_info, parent=None):
        super().__init__(parent)
        self.book_name = book_name
        self.book_info = book_info
        self.setFixedSize(130, 210)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.cover_space = QWidget()
        self.cover_space.setFixedHeight(140)
        layout.addWidget(self.cover_space)
        self.title = QLabel(self.elide_text(book_name))
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setWordWrap(True)
        self.title.setStyleSheet('color:#2c3e50;')
        layout.addWidget(self.title)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._spine_color = QColor('#cfd9d6')
        self._cover_cache_size = None
        self._cover_cache_pixmap = None
        self._selection_mode = False
        self._selected = False
        self._selection_mode = False
        self._selected = False

    def elide_text(self, text, max_len=20):
        return text if len(text) <= max_len else text[:max_len] + '...'

    def mouseDoubleClickEvent(self, event):
        self.continue_reading.emit(self.book_info)

    def set_selection_mode(self, enabled: bool):
        self._selection_mode = bool(enabled)
        if not enabled and self._selected:
            self._selected = False
            self.selection_changed.emit(self.book_name, False)
        try:
            self.setAcceptDrops(not enabled)
        except Exception:
            pass
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_pos = event.pos()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selection_mode:
            self._selected = not self._selected
            self.selection_changed.emit(self.book_name, self._selected)
            self.update()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._selection_mode:
            return super().mouseMoveEvent(event)
        if event.buttons() & Qt.LeftButton and hasattr(self, '_press_pos'):
            if (event.pos() - self._press_pos).manhattanLength() > 6:
                from PyQt5.QtGui import QDrag
                from PyQt5.QtCore import QMimeData
                drag = QDrag(self)
                mime = QMimeData()
                mime.setText(f"book:{self.book_name}")
                drag.setMimeData(mime)
                # 拖拽预览跟随鼠标（80%缩放）
                pm = self.grab()
                sw = int(pm.width() * 0.8)
                sh = int(pm.height() * 0.8)
                spm = pm.scaled(sw, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                drag.setPixmap(spm)
                from PyQt5.QtCore import QPoint
                hs = QPoint(int(event.pos().x() * 0.8), int(event.pos().y() * 0.8))
                drag.setHotSpot(hs)
                try:
                    mw = self.window()
                    mw._drag_src_name = self.book_name
                    mw._dragging = True
                except Exception:
                    pass
                self.hide()
                res = drag.exec_(Qt.MoveAction)
                try:
                    mw = self.window()
                    mw._drag_src_name = None
                    mw._dragging = False
                    if hasattr(mw, 'clear_drop_indicator'):
                        mw.clear_drop_indicator()
                except Exception:
                    pass
                self.show()
        super().mouseMoveEvent(event)

    def dragEnterEvent(self, event):
        if self._selection_mode:
            event.ignore()
            return
        if event.mimeData().hasText() and event.mimeData().text().startswith('book:'):
            event.setDropAction(Qt.MoveAction)
            self._drag_hover_start = time.time()
            try:
                from PyQt5.QtCore import QTimer
                if not hasattr(self, '_group_hint_timer'):
                    self._group_hint_timer = QTimer(self)
                    self._group_hint_timer.setSingleShot(True)
                self._group_hint_timer.stop()
                def show_hint():
                    try:
                        mw = self.window()
                        if hasattr(mw, 'show_global_group_hint'):
                            mw.show_global_group_hint(True)
                    except Exception:
                        pass
                self._group_hint_timer.timeout.connect(show_hint)
                self._group_hint_timer.start(500)
                try:
                    mw = self.window()
                    vp = getattr(mw, 'card_scroll').viewport() if hasattr(mw, 'card_scroll') else None
                    if vp and hasattr(mw, 'update_drop_indicator'):
                        gp = self.mapTo(vp, event.pos())
                        mw.update_drop_indicator(vp, gp)
                except Exception:
                    pass
            except Exception:
                pass
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if self._selection_mode:
            event.ignore()
            return
        if event.mimeData().hasText() and event.mimeData().text().startswith('book:'):
            try:
                mw = self.window()
                vp = getattr(mw, 'card_scroll').viewport() if hasattr(mw, 'card_scroll') else None
                if vp and hasattr(mw, 'update_drop_indicator'):
                    gp = self.mapTo(vp, event.pos())
                    mw.update_drop_indicator(vp, gp)
            except Exception:
                pass
            event.setDropAction(Qt.MoveAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self._selection_mode:
            event.ignore()
            return
        if event.mimeData().hasText() and event.mimeData().text().startswith('book:'):
            src = event.mimeData().text()[5:]
            if src and src != self.book_name:
                hold_ms = int((time.time() - getattr(self, '_drag_hover_start', time.time())) * 1000)
                self.drop_group_create.emit(f"{src}|{hold_ms}", self.book_name)
            event.setDropAction(Qt.MoveAction)
            event.accept()
            try:
                mw = self.window()
                if hasattr(mw, 'show_global_group_hint'):
                    mw.show_global_group_hint(False)
                mw._drag_src_name = None
            except Exception:
                pass
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        try:
            if hasattr(self, '_group_hint_timer') and self._group_hint_timer:
                self._group_hint_timer.stop()
            mw = self.window()
            if hasattr(mw, 'show_global_group_hint'):
                mw.show_global_group_hint(False)
        except Exception:
            pass
        super().dragLeaveEvent(event)

    # 删除重复的旧事件处理，避免按下即选择与拖拽逻辑冲突

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.cover_space.geometry()
        cover_rect = QRectF(r.adjusted(6, 2, -6, -2))
        size = QSize(int(cover_rect.width()), int(cover_rect.height()))
        if size != self._cover_cache_size:
            self._cover_cache_pixmap = self._build_cover_pixmap(size)
            self._cover_cache_size = size
        if self._cover_cache_pixmap:
            p.drawPixmap(cover_rect.topLeft(), self._cover_cache_pixmap)
        p.setPen(Qt.NoPen)
        p.setBrush(self._spine_color)
        p.drawRoundedRect(QRectF(cover_rect.left() - 8, cover_rect.top(), 8, cover_rect.height()), 4, 4)
        p.setBrush(QColor(255, 255, 255, 90))
        p.drawRect(QRectF(cover_rect.right() - 3, cover_rect.top() + 2, 3, cover_rect.height() - 4))
        outer = QRectF(self.rect().adjusted(2, 2, -2, -2))
        if self._selection_mode:
            if getattr(self, '_selected', False):
                p.setPen(QPen(QColor(52, 152, 219), 2))
            else:
                p.setPen(QPen(QColor(189, 195, 199), 1))
            p.drawRoundedRect(outer, 10, 10)
        p.end()

    def _build_cover_pixmap(self, size: QSize) -> QPixmap:
        key = (self.book_name, size.width(), size.height())
        if key in _COVER_CACHE:
            return _COVER_CACHE[key]
        img = QImage(size.width(), size.height(), QImage.Format_ARGB32)
        img.fill(QColor(255, 255, 255))  # 先填充白色背景
        pr = random.Random(abs(hash(self.book_name)) % (2**32))
        
        # 目标粉紫蓝配色（和图二一致）
        colors = [
            QColor('#f8cdd5'),  # 浅粉
            QColor('#e9d2ff'),  # 淡紫
            QColor('#cfe7ff'),  # 浅蓝
            QColor('#f0e6ff')   # 粉紫过渡
        ]
        
        blobs = []
        n_blobs = pr.randint(5, 7)
        for i in range(n_blobs):
            cx = pr.uniform(0.08, 0.92) * size.width()
            cy = pr.uniform(0.08, 0.92) * size.height()
            sigma = pr.uniform(0.18, 0.35) * min(size.width(), size.height())
            col = pr.choice(colors).lighter(pr.randint(98, 102))
            blobs.append((cx, cy, sigma, col))

        # 细节层（更明显的随机晕染变化）
        micro_blobs = []
        m_count = pr.randint(6, 10)
        for _ in range(m_count):
            mcx = pr.uniform(0.05, 0.95) * size.width()
            mcy = pr.uniform(0.05, 0.95) * size.height()
            msigma = pr.uniform(0.08, 0.18) * min(size.width(), size.height())
            mcol = pr.choice(colors).lighter(pr.randint(96, 100))
            micro_blobs.append((mcx, mcy, msigma, mcol))

        # 角点渐变（保证可见的粉紫蓝过渡）
        corners = random.sample(colors, 4)
        tl, tr, bl, br = corners

        for y in range(size.height()):
            dy = y / (size.height() - 1)
            for x in range(size.width()):
                dx = x / (size.width() - 1)
                r = int(tl.red()   * (1 - dx) * (1 - dy) + tr.red()   * dx * (1 - dy) + bl.red()   * (1 - dx) * dy + br.red()   * dx * dy)
                g = int(tl.green() * (1 - dx) * (1 - dy) + tr.green() * dx * (1 - dy) + bl.green() * (1 - dx) * dy + br.green() * dx * dy)
                b = int(tl.blue()  * (1 - dx) * (1 - dy) + tr.blue()  * dx * (1 - dy) + bl.blue()  * (1 - dx) * dy + br.blue()  * dx * dy)
                # 叠加水彩色团
                for (cx, cy, sigma, col) in blobs:
                    dx2 = x - cx
                    dy2 = y - cy
                    w = math.exp(-(dx2*dx2 + dy2*dy2) / (2.0 * sigma * sigma))
                    r = int(r * (1 - w) + col.red()   * w)
                    g = int(g * (1 - w) + col.green() * w)
                    b = int(b * (1 - w) + col.blue()  * w)
                # 叠加细节层，增强随机变化与水彩边缘
                for (mcx, mcy, msigma, mcol) in micro_blobs:
                    ddx = x - mcx
                    ddy = y - mcy
                    mw = math.exp(-(ddx*ddx + ddy*ddy) / (2.0 * msigma * msigma)) * 0.6
                    r = int(r * (1 - mw) + mcol.red()   * mw)
                    g = int(g * (1 - mw) + mcol.green() * mw)
                    b = int(b * (1 - mw) + mcol.blue()  * mw)
                # 与白色轻混（进一步降低比例）
                mix = 0.03
                r = int(r * (1 - mix) + 255 * mix)
                g = int(g * (1 - mix) + 255 * mix)
                b = int(b * (1 - mix) + 255 * mix)
                grain = pr.randint(-1, 1)
                img.setPixel(x, y, QColor(min(255, max(0, r + grain)), min(255, max(0, g + grain)), min(255, max(0, b + grain)), 255).rgba())
        
        # 添加细微噪点（模拟纸张纹理）
        qp = QPainter(img)
        for y in range(size.height()):
            for x in range(size.width()):
                if pr.random() < 0.02:  # 2%的像素添加噪点
                    c = img.pixelColor(x, y)
                    c.setRed(min(255, max(0, c.red() + pr.randint(-10, 10))))
                    c.setGreen(min(255, max(0, c.green() + pr.randint(-10, 10))))
                    c.setBlue(min(255, max(0, c.blue() + pr.randint(-10, 10))))
                    img.setPixelColor(x, y, c)
        qp.end()
        
        pm = QPixmap.fromImage(img)
        _COVER_CACHE[key] = pm
        return pm

    def show_menu(self, pos):
        from PyQt5.QtWidgets import QMenu, QAction
        mw = self.window()
        if getattr(mw, 'selection_mode', False):
            menu = QMenu(self)
            mv_all = QAction('移动到分组', self)
            mv_all.triggered.connect(lambda: getattr(mw, 'bulk_move_selected')())
            menu.addAction(mv_all)
            del_all = QAction('删除', self)
            del_all.triggered.connect(lambda: getattr(mw, 'bulk_delete_selected')())
            menu.addAction(del_all)
            menu.exec_(self.mapToGlobal(pos))
            return
        menu = QMenu(self)
        a1 = QAction('继续阅读', self)
        a1.triggered.connect(lambda: self.continue_reading.emit(self.book_info))
        menu.addAction(a1)
        a2 = QAction('从头阅读', self)
        a2.triggered.connect(lambda: self.start_reading.emit(self.book_info))
        menu.addAction(a2)
        menu.addSeparator()
        mv = QAction('移动到分组', self)
        mv.triggered.connect(lambda: self.move_book.emit(self.book_info))
        menu.addAction(mv)
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


class FolderCardWidget(QWidget):
    open_group = pyqtSignal(int)           # index
    rename_group = pyqtSignal(int)
    delete_group = pyqtSignal(int)
    drop_book_to_group = pyqtSignal(str, int)  # book_name, group_index

    def __init__(self, group_index, group_name, parent=None, preview_books=None):
        super().__init__(parent)
        self.group_index = group_index
        self.group_name = group_name
        self.preview_books = preview_books or []
        self.setFixedSize(130, 160)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        self.icon_space = QWidget()
        self.icon_space.setFixedHeight(100)
        layout.addWidget(self.icon_space)
        self.title = QLabel(group_name)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet('color:#2c3e50;')
        layout.addWidget(self.title)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.setAcceptDrops(True)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.open_group.emit(self.group_index)
        super().mousePressEvent(e)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith('book:'):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith('book:'):
            name = event.mimeData().text()[5:]
            self.drop_book_to_group.emit(name, self.group_index)
            event.acceptProposedAction()
        else:
            event.ignore()

    def show_menu(self, pos):
        from PyQt5.QtWidgets import QMenu, QAction
        menu = QMenu(self)
        a1 = QAction('打开分组', self)
        a1.triggered.connect(lambda: self.open_group.emit(self.group_index))
        menu.addAction(a1)
        a2 = QAction('重命名分组', self)
        a2.triggered.connect(lambda: self.rename_group.emit(self.group_index))
        menu.addAction(a2)
        a3 = QAction('删除分组', self)
        a3.triggered.connect(lambda: self.delete_group.emit(self.group_index))
        menu.addAction(a3)
        menu.exec_(self.mapToGlobal(pos))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.icon_space.geometry()
        body_rect = QRectF(r.adjusted(8, 8, -8, -8))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(245, 245, 245))
        p.drawRoundedRect(body_rect, 10, 10)
        grid_w = int(body_rect.width())
        grid_h = int(body_rect.height())
        cell_w = grid_w // 2
        cell_h = grid_h // 2
        for i, name in enumerate(self.preview_books[:4]):
            cx = int(i % 2)
            cy = int(i // 2)
            cell = QRectF(body_rect.left() + cx * cell_w + 6, body_rect.top() + cy * cell_h + 6, cell_w - 12, cell_h - 12)
            pm = _COVER_CACHE.get((name, int(cell.width()), int(cell.height())))
            if pm is None:
                pm = QPixmap(int(cell.width()), int(cell.height()))
                pm.fill(QColor(230,230,230))
            p.drawPixmap(cell.topLeft(), pm)
        p.end()

    def update_book_info(self, book_name, book_info):
        self.book_name = book_name
        self.book_info = book_info
        self.title.setText(self.elide_text(book_name))
