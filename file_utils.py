# -*- coding: utf-8 -*-
"""
文件工具模块
提供文件编码检测和读取功能
"""

import os
from typing import Optional, Tuple


def detect_encoding_and_read_file(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    智能检测文件编码并读取内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        (content, encoding): 文件内容和使用的编码，如果失败返回(None, None)
    """
    if not os.path.exists(file_path):
        return None, None
        
    # 尝试的编码列表，按优先级排序
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'utf-16', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            # 验证读取的内容是否包含合理的中文字符
            if _validate_content_encoding(content):
                return content, encoding
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue
            
    # 如果所有编码都失败，最后尝试用utf-8读取并替换错误字符
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        return content, 'utf-8-replace'
    except Exception:
        return None, None


def _validate_content_encoding(content: str) -> bool:
    """
    验证内容编码是否正确
    
    Args:
        content: 文件内容
        
    Returns:
        是否为正确编码
    """
    if not content or len(content.strip()) < 10:
        return False
        
    # 检查前1000个字符的编码质量
    sample = content[:1000]
    
    # 检查是否包含合理的中文字符比例
    chinese_chars = sum(1 for char in sample if '\u4e00' <= char <= '\u9fff')
    total_chars = len(sample)
    
    if total_chars == 0:
        return False
        
    # 计算中文字符比例
    chinese_ratio = chinese_chars / total_chars
    
    # 检查是否包含常见的章节标识符
    chapter_indicators = ['第', '章', '卷', '节', '篇', '回', '部', '集']
    has_chapter_indicators = any(indicator in sample for indicator in chapter_indicators)
    
    # 检查是否包含常见的标点符号
    chinese_punctuation = ['，', '。', '！', '？', '；', '：', '、']
    has_chinese_punctuation = any(punct in sample for punct in chinese_punctuation)
    
    # 检查是否包含过多的替换字符（�）
    replacement_chars = sample.count('�')
    replacement_ratio = replacement_chars / total_chars if total_chars > 0 else 0
    
    # 如果替换字符过多，认为编码错误
    if replacement_ratio > 0.1:
        return False
        
    # 综合判断：中文字符比例合理，或包含章节标识符，或包含中文标点
    return (chinese_ratio > 0.1 or 
            has_chapter_indicators or 
            has_chinese_punctuation)


def detect_encoding(file_path: str) -> Optional[str]:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        检测到的编码，如果失败返回None
    """
    content, encoding = detect_encoding_and_read_file(file_path)
    return encoding if content else None