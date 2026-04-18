# -*- coding: utf-8 -*-
"""
EPUB文件工具模块 - 性能优化版
提供EPUB文件解析功能，提取文本内容，并添加缓存机制
"""

import os
import re
import zipfile
import hashlib
import json
from typing import Optional, Tuple
from html import unescape
from html.parser import HTMLParser
from ebooklib import epub


class EpubCache:
    """EPUB 缓存管理器"""
    
    def __init__(self, cache_dir='.epub_cache'):
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
            try:
                os.makedirs(cache_dir, exist_ok=True)
            except Exception:
                self.cache_dir = None
    
    def _get_file_hash(self, file_path: str) -> str:
        """计算文件的哈希值（用于缓存键）"""
        try:
            # 获取文件修改时间和大小，避免计算大文件的完整哈希
            stat = os.stat(file_path)
            file_info = f"{file_path}_{stat.st_mtime}_{stat.st_size}"
            return hashlib.md5(file_info.encode('utf-8')).hexdigest()
        except Exception:
            # 如果失败，使用路径作为后备
            return hashlib.md5(file_path.encode('utf-8')).hexdigest()
    
    def _get_cache_path(self, file_path: str) -> Optional[str]:
        """获取缓存文件路径"""
        if not self.cache_dir:
            return None
        file_hash = self._get_file_hash(file_path)
        return os.path.join(self.cache_dir, f"{file_hash}.cache")
    
    def get(self, file_path: str) -> Optional[dict]:
        """从缓存获取内容"""
        cache_path = self._get_cache_path(file_path)
        if not cache_path or not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception:
            return None
    
    def set(self, file_path: str, content: str, title: Optional[str] = None):
        """保存内容到缓存"""
        cache_path = self._get_cache_path(file_path)
        if not cache_path:
            return
        
        try:
            cache_data = {
                'content': content,
                'title': title,
                'version': 1
            }
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False)
        except Exception:
            pass


# 全局缓存实例
_epub_cache = EpubCache()


class EpubHtmlTextExtractor(HTMLParser):
    """
    EPUB HTML 文本提取器 - 性能优化版
    保留段落/标题等块级标签换行，避免正文全部挤成一行。
    """

    BLOCK_TAGS = {
        'address', 'article', 'aside', 'blockquote', 'body', 'caption', 'dd',
        'div', 'dl', 'dt', 'figcaption', 'figure', 'footer', 'form',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'header', 'hr', 'li', 'main',
        'nav', 'ol', 'p', 'pre', 'section', 'table', 'tbody', 'td', 'tfoot',
        'th', 'thead', 'tr', 'ul'
    }
    LINE_BREAK_TAGS = {'br'}
    SKIP_TAGS = {'script', 'style', 'svg', 'noscript'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
            return

        if self.skip_depth > 0:
            return

        if tag in self.BLOCK_TAGS or tag in self.LINE_BREAK_TAGS:
            self._append_newline()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return

        if self.skip_depth > 0:
            return

        if tag in self.BLOCK_TAGS:
            self._append_newline()

    def handle_data(self, data):
        if self.skip_depth > 0 or not data:
            return

        normalized = self._normalize_fragment(data)
        if normalized:
            self.parts.append(normalized)

    def _append_newline(self):
        if not self.parts:
            return

        if not self.parts[-1].endswith('\n'):
            self.parts.append('\n')

    @staticmethod
    def _normalize_fragment(text: str) -> str:
        text = text.replace('\xa0', ' ')
        text = text.replace('\u00ad', '')
        text = text.replace('\ufeff', '')
        text = text.replace('\u200b', '')
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = re.sub(r'[ \t\f\v]+', ' ', text)
        return text


def read_epub_file(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    读取EPUB文件并提取文本内容 - 性能优化版
    
    Args:
        file_path: EPUB文件路径
        
    Returns:
        (content, error_message): 文件内容和错误信息，如果成功则error_message为None
    """
    if not os.path.exists(file_path):
        return None, "文件不存在"
    
    if not file_path.lower().endswith('.epub'):
        return None, "文件不是EPUB格式"
    
    # 优先从缓存获取
    cached_data = _epub_cache.get(file_path)
    if cached_data and 'content' in cached_data:
        return cached_data['content'], None
    
    try:
        # 使用ebooklib库读取EPUB文件
        book = epub.read_epub(file_path)
        
        # 优先按照阅读顺序提取正文，目录定位会更稳定。
        text_content = extract_all_text_from_epub(book)
        
        # 如果没有提取到内容，尝试其他方法
        if not text_content:
            text_content = extract_text_from_all_items(book)
        
        # 合并所有文本内容
        full_text = '\n\n'.join(text_content)
        
        if not full_text.strip():
            return None, "EPUB文件中没有找到可读的文本内容"
        
        # 获取书籍标题
        title = None
        if book.get_metadata('DC', 'title'):
            title = book.get_metadata('DC', 'title')[0][0]
        
        # 保存到缓存
        _epub_cache.set(file_path, full_text, title)
        
        return full_text, None
        
    except Exception as e:
        return None, f"读取EPUB文件失败：{str(e)}"


def extract_text_from_html(html_content: str) -> str:
    """
    从HTML内容中提取纯文本 - 性能优化版
    
    Args:
        html_content: HTML内容字符串
        
    Returns:
        提取的纯文本
    """
    try:
        extractor = EpubHtmlTextExtractor()
        extractor.feed(_decode_html_entities(html_content))
        extractor.close()

        return _clean_extracted_text(''.join(extractor.parts))
        
    except Exception:
        # 回退到正则方案，避免个别异常HTML导致完全无法读取。
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<br\s*/?>', '\n', html_content, flags=re.IGNORECASE)
        html_content = re.sub(
            r'</?(p|div|section|article|h[1-6]|li|tr|blockquote|pre)[^>]*>',
            '\n',
            html_content,
            flags=re.IGNORECASE
        )
        text = re.sub(r'<[^>]+>', ' ', html_content)
        return _clean_extracted_text(_decode_html_entities(text))


def extract_all_text_from_epub(book) -> list:
    """
    从EPUB书籍对象中提取所有文本内容 - 性能优化版
    
    Args:
        book: ebooklib.epub.EpubBook对象
        
    Returns:
        文本内容列表
    """
    text_content = []
    
    try:
        # 获取书籍的spine（阅读顺序）
        spine_items = book.spine
        
        # 按照spine顺序提取内容
        for spine_id, linear in spine_items:
            # 获取对应的项目
            item = book.get_item_with_id(spine_id)
            if item and isinstance(item, epub.EpubHtml):
                html_content = _decode_item_content(item)
                text = extract_text_from_html(html_content)
                if text.strip():
                    text_content.append(text)
        
    except Exception:
        return extract_text_from_all_items(book)
    
    return text_content


def extract_text_from_all_items(book) -> list:
    """遍历所有正文项目提取文本，作为spine解析失败时的兜底方案。"""
    text_content = []

    for item in book.get_items():
        if isinstance(item, epub.EpubHtml):
            try:
                html_content = _decode_item_content(item)
                text = extract_text_from_html(html_content)
                if text.strip():
                    text_content.append(text)
            except Exception:
                continue

    return text_content


def _decode_item_content(item) -> str:
    """安全解码 EPUB 文本项目，兼容少量非标准编码声明。"""
    raw_content = item.get_content()

    if isinstance(raw_content, bytes):
        for encoding in ('utf-8', 'utf-8-sig', 'gbk'):
            try:
                return raw_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw_content.decode('utf-8', errors='ignore')

    return str(raw_content)


def _decode_html_entities(text: str) -> str:
    """
    多轮解码 HTML 实体。
    兼容 `&#13;` 和 `&amp;#13;` 这类被重复转义的内容。
    """
    decoded = text
    for _ in range(3):
        new_value = unescape(decoded)
        if new_value == decoded:
            break
        decoded = new_value
    return decoded


def _clean_extracted_text(text: str) -> str:
    """清洗提取后的文本，保留自然段并去掉控制字符。"""
    text = _decode_html_entities(text)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = text.replace('\xa0', ' ')
    text = text.replace('\ufeff', '')
    text = text.replace('\u200b', '')
    text = text.replace('\u00ad', '')

    # 保留换行，压缩每行内部的空白，避免章节标题和正文被挤成一团。
    lines = [re.sub(r'\s+', ' ', line).strip() for line in text.split('\n')]

    cleaned_lines = []
    last_blank = True
    for line in lines:
        if line:
            cleaned_lines.append(line)
            last_blank = False
        elif not last_blank:
            cleaned_lines.append('')
            last_blank = True

    cleaned_text = '\n'.join(cleaned_lines).strip()
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    return cleaned_text


def is_epub_file(file_path: str) -> bool:
    """
    检查文件是否为EPUB格式
    
    Args:
        file_path: 文件路径
        
    Returns:
        是否为EPUB文件
    """
    if not os.path.exists(file_path):
        return False
    
    # 检查文件扩展名
    if file_path.lower().endswith('.epub'):
        return True
    
    # 检查文件签名（可选）
    try:
        with open(file_path, 'rb') as f:
            header = f.read(58)  # EPUB文件头长度
            # EPUB文件以PK开头（ZIP格式）
            if header.startswith(b'PK'):
                # 检查是否包含mimetype文件
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    if 'mimetype' in zip_ref.namelist():
                        with zip_ref.open('mimetype') as mime_file:
                            mime_content = mime_file.read().decode('utf-8').strip()
                            if mime_content == 'application/epub+zip':
                                return True
    except Exception:
        pass
    
    return False


def get_epub_title(file_path: str) -> Optional[str]:
    """
    获取EPUB文件的标题 - 性能优化版
    
    Args:
        file_path: EPUB文件路径
        
    Returns:
        书籍标题，如果获取失败返回None
    """
    # 优先从缓存获取
    cached_data = _epub_cache.get(file_path)
    if cached_data and cached_data.get('title'):
        return cached_data['title']
    
    try:
        book = epub.read_epub(file_path)
        
        # 获取元数据中的标题
        if book.get_metadata('DC', 'title'):
            title = book.get_metadata('DC', 'title')[0][0]
            if title:
                # 如果缓存有内容，更新标题
                if cached_data and 'content' in cached_data:
                    _epub_cache.set(file_path, cached_data['content'], title)
                return title
        
        # 如果元数据中没有标题，使用文件名（不含扩展名）
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        return title
        
    except Exception:
        # 如果获取失败，返回文件名（不含扩展名）
        filename = os.path.basename(file_path)
        return os.path.splitext(filename)[0]
