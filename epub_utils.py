# -*- coding: utf-8 -*-
"""
EPUB文件工具模块
提供EPUB文件解析功能，提取文本内容
"""

import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from ebooklib import epub


def read_epub_file(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    读取EPUB文件并提取文本内容
    
    Args:
        file_path: EPUB文件路径
        
    Returns:
        (content, error_message): 文件内容和错误信息，如果成功则error_message为None
    """
    if not os.path.exists(file_path):
        return None, "文件不存在"
    
    if not file_path.lower().endswith('.epub'):
        return None, "文件不是EPUB格式"
    
    try:
        # 使用ebooklib库读取EPUB文件
        book = epub.read_epub(file_path)
        
        # 提取所有文本内容
        text_content = []
        
        # 遍历所有项目（章节、内容等）
        for item in book.get_items():
            # 只处理文本类型的内容（HTML/XHTML）
            if isinstance(item, epub.EpubHtml):
                # 获取HTML内容
                html_content = item.get_content().decode('utf-8')
                
                # 简单提取文本内容（去除HTML标签）
                # 这里使用简单的文本提取，可以根据需要改进
                text = extract_text_from_html(html_content)
                if text.strip():
                    text_content.append(text)
        
        # 如果没有提取到内容，尝试其他方法
        if not text_content:
            # 尝试直接读取所有文本内容
            text_content = extract_all_text_from_epub(book)
        
        # 合并所有文本内容
        full_text = '\n\n'.join(text_content)
        
        if not full_text.strip():
            return None, "EPUB文件中没有找到可读的文本内容"
        
        return full_text, None
        
    except Exception as e:
        return None, f"读取EPUB文件失败：{str(e)}"


def extract_text_from_html(html_content: str) -> str:
    """
    从HTML内容中提取纯文本
    
    Args:
        html_content: HTML内容字符串
        
    Returns:
        提取的纯文本
    """
    try:
        # 简单的HTML标签去除
        import re
        
        # 移除脚本和样式标签
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', html_content)
        
        # 处理HTML实体
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&apos;', "'")
        
        # 合并多个空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 去除首尾空白
        text = text.strip()
        
        return text
        
    except Exception:
        # 如果解析失败，返回原始内容
        return html_content


def extract_all_text_from_epub(book) -> list:
    """
    从EPUB书籍对象中提取所有文本内容
    
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
                html_content = item.get_content().decode('utf-8')
                text = extract_text_from_html(html_content)
                if text.strip():
                    text_content.append(text)
        
    except Exception:
        # 如果按照spine顺序提取失败，尝试遍历所有项目
        for item in book.get_items():
            if isinstance(item, epub.EpubHtml):
                try:
                    html_content = item.get_content().decode('utf-8')
                    text = extract_text_from_html(html_content)
                    if text.strip():
                        text_content.append(text)
                except Exception:
                    continue
    
    return text_content


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
    获取EPUB文件的标题
    
    Args:
        file_path: EPUB文件路径
        
    Returns:
        书籍标题，如果获取失败返回None
    """
    try:
        book = epub.read_epub(file_path)
        
        # 获取元数据中的标题
        if book.get_metadata('DC', 'title'):
            title = book.get_metadata('DC', 'title')[0][0]
            if title:
                return title
        
        # 如果元数据中没有标题，使用文件名（不含扩展名）
        filename = os.path.basename(file_path)
        title = os.path.splitext(filename)[0]
        return title
        
    except Exception:
        # 如果获取失败，返回文件名（不含扩展名）
        filename = os.path.basename(file_path)
        return os.path.splitext(filename)[0]