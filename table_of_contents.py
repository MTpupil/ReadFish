# -*- coding: utf-8 -*-
"""
目录解析器
智能解析各种格式的章节目录 - 性能优化版
"""

import re
import logging
from typing import List, Dict, Tuple, Optional

# 配置日志 - 生产环境中设置为WARNING级别，减少日志输出
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')


class TableOfContents:
    """目录解析器类 - 性能优化版"""
    
    def __init__(self):
        # 快速检查：先检查是否包含常见的章节关键词，避免不必要的正则匹配
        self.fast_check_keywords = [
            '第', '章', '回', '节', '篇', '卷', '部', '集',
            '序章', '楔子', '尾声', '后记', '番外', '终章',
            'Chapter', 'chapter', 'CHAPTER'
        ]
        
        # 核心正则表达式（精简版，只保留最常用的模式）
        number_pattern = r'[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+'
        chapter_unit_pattern = r'[章回节篇卷部集]'
        
        # 只保留最核心、最常用的章节模式（按优先级排序）
        self.chapter_patterns = [
            # 第X章、第X回、第X节等（最常见，优先级最高）
            rf'^\s*第{number_pattern}{chapter_unit_pattern}(?:[：:\s]+.*)?$',
            # Chapter X
            r'^\s*[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*[\d]+(?:[：:\s]+.*)?$',
            # 书名号格式：《第X章》
            rf'^\s*《第{number_pattern}{chapter_unit_pattern}[^》]*》.*$',
            # 特殊格式：序章、楔子等
            r'^\s*(序章|楔子|尾声|后记|番外|终章)[：:：\s].*$',
        ]
        
        # 编译正则表达式
        self.compiled_patterns = [re.compile(pattern) for pattern in self.chapter_patterns]
        
    def parse_contents(self, text: str, min_chapter_length: int = 3, max_chapters: int = 10000) -> List[Dict]:
        """
        解析文本中的目录 - 性能优化版
        
        优化策略：
        1. 快速检查：先检查是否包含章节关键词，避免不必要的处理
        2. 增量处理：逐行处理，不存储中间结果
        3. 模式精简：只使用最核心的正则表达式
        4. 提前返回：达到最大章节数后立即返回
        
        Args:
            text: 要解析的文本内容
            min_chapter_length: 章节标题的最小长度
            max_chapters: 最大章节数量限制
            
        Returns:
            章节列表
        """
        logging.info(f"开始解析目录，文本长度: {len(text)} 字符")
        
        # 快速检查：如果文本不包含任何章节关键词，直接返回空列表
        has_chapters = False
        for keyword in self.fast_check_keywords:
            if keyword in text:
                has_chapters = True
                break
        if not has_chapters:
            logging.info("文本中未发现章节关键词，跳过解析")
            return []
        
        chapters = []
        char_position = 0
        
        # 逐行处理（使用splitlines避免分割整个文本）
        lines = text.splitlines()
        logging.info(f"文本总行数: {len(lines)}")
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 快速跳过：空行或过短的行
            if not line_stripped or len(line_stripped) < min_chapter_length:
                char_position += len(line) + 1
                continue
            
            # 快速跳过：过长的行（可能不是章节标题）
            if len(line_stripped) > 100:
                char_position += len(line) + 1
                continue
            
            # 快速检查：是否包含章节关键词
            has_keyword = False
            for keyword in self.fast_check_keywords:
                if keyword in line_stripped:
                    has_keyword = True
                    break
            if not has_keyword:
                char_position += len(line) + 1
                continue
            
            # 正则匹配（只检查核心模式）
            matched = False
            for pattern in self.compiled_patterns:
                if pattern.match(line_stripped):
                    # 确定章节级别（简化版）
                    level = self._determine_chapter_level_fast(line_stripped)
                    
                    chapter_info = {
                        'title': line_stripped,
                        'line_number': line_num,
                        'char_position': char_position,
                        'level': level
                    }
                    chapters.append(chapter_info)
                    matched = True
                    break
            
            char_position += len(line) + 1
            
            # 达到最大章节数后立即返回
            if len(chapters) >= max_chapters:
                logging.warning(f"达到最大章节数量限制 {max_chapters}，停止解析")
                break
        
        logging.info(f"解析完成，找到 {len(chapters)} 个章节")
        return chapters
    
    def _determine_chapter_level_fast(self, title: str) -> int:
        """
        快速确定章节级别 - 简化版
        """
        # 卷级别
        if '卷' in title or '部' in title or '篇' in title:
            if re.search(r'第.*[卷部篇]', title) or re.search(r'^[卷部篇]', title):
                return 1
        # 子章节级别
        if '节' in title or '段' in title:
            return 3
        # 默认章节级别
        return 2
        
    def get_chapter_summary(self, chapters):
        """获取章节统计信息 - 简化版"""
        if not chapters:
            return {
                'total_chapters': 0,
                'main_chapters': 0,
                'sub_chapters': 0,
                'first_chapter': None,
                'last_chapter': None
            }
            
        main_chapters = [ch for ch in chapters if ch['level'] == 1]
        sub_chapters = [ch for ch in chapters if ch['level'] == 2]
        
        return {
            'total_chapters': len(chapters),
            'main_chapters': len(main_chapters),
            'sub_chapters': len(sub_chapters),
            'first_chapter': chapters[0]['title'] if chapters else None,
            'last_chapter': chapters[-1]['title'] if chapters else None
        }
