# -*- coding: utf-8 -*-
"""
目录解析器
智能解析各种格式的章节目录
"""

import re
import logging
from typing import List, Dict, Tuple, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class TableOfContents:
    """目录解析器类"""
    
    def __init__(self):
        # 定义各种章节格式的正则表达式（按优先级排序，更精确的模式在前）
        self.chapter_patterns = [
            # 书名号格式：《第X章》、《第X回》等
            r'^\s*《第[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[章回节篇卷部集][^》]*》.*$',
            
            # 书名号格式：《Chapter X》等
            r'^\s*《[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*[\d]+[^》]*》.*$',
            
            # 方括号格式：【第X章】、【第X回】等
            r'^\s*【第[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[章回节篇卷部集][^】]*】.*$',
            
            # 方括号格式：【Chapter X】等
            r'^\s*【[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*[\d]+[^】]*】.*$',
            
            # 第X章、第X回、第X节等（必须有明确的章节标识）
            r'^\s*第[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[章回节篇卷部集][：:：\s].*$',
            
            # 第(X)章、第(X)回等
            r'^\s*第\([\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\)[章回节篇卷部集][：:：\s].*$',
            
            # 第X部分、第X篇等
            r'^\s*第[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+部分[：:：\s].*$',
            
            # Chapter X、CHAPTER X等（必须有冒号或空格分隔）
            r'^\s*[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s*[\d]+[：:：\s].*$',
            
            # 卷X：卷一、卷二等
            r'^\s*卷[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[：:：\s].*$',
            
            # 书X：书一、书二等
            r'^\s*书[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[：:：\s].*$',
            
            # 篇X：篇一、篇二等
            r'^\s*篇[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[：:：\s].*$',
            
            # 数字章节：1、2、3或1.、2.、3.等（限制数字范围，避免误匹配）
            r'^\s*[1-9]\d{0,2}[、．.][：:：\s]*.+$',
            
            # 中文数字章节：一、二、三等（必须有标点分隔）
            r'^\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[、．.][：:：\s]*.+$',
            
            # 括号数字：(1)、(2)、(3)等（限制数字范围）
            r'^\s*\([1-9]\d{0,2}\)[：:：\s]*.+$',
            
            # 括号中文数字：(一)、(二)、(三)等
            r'^\s*\([一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+\)[：:：\s]*.+$',
            
            # 方括号数字：[1]、[2]、[3]等（限制数字范围）
            r'^\s*\[[1-9]\d{0,2}\][：:：\s]*.+$',
            
            # 特殊格式：序章、楔子、尾声、后记、番外等（必须是完整词汇）
            r'^\s*(序章|楔子|尾声|后记|番外|终章|结局|完结)[：:：\s].*$',
            
            # 特殊格式：前言、引言、结语等
            r'^\s*(前言|引言|结语|序言|后语)[：:：\s].*$',
            
            # 特殊格式：上篇、中篇、下篇等
            r'^\s*[上中下前后]篇[：:：\s].*$',
        ]
        
        # 编译正则表达式以提高性能
        self.compiled_patterns = [re.compile(pattern) for pattern in self.chapter_patterns]
        
    def parse_contents(self, text: str, min_chapter_length: int = 3, max_chapters: int = 1000) -> List[Dict]:
        """
        解析文本中的目录
        
        Args:
            text: 要解析的文本内容
            min_chapter_length: 章节标题的最小长度
            max_chapters: 最大章节数量限制
            
        Returns:
            章节列表，每个章节包含：
            {
                'title': '章节标题',
                'line_number': 行号,
                'char_position': 字符位置,
                'level': 章节级别 (1-主章节, 2-子章节)
            }
        """
        logging.info(f"开始解析目录，文本长度: {len(text)} 字符")
        
        lines = text.split('\n')
        chapters = []
        char_position = 0
        matched_patterns = {}  # 记录匹配的模式统计
        
        logging.info(f"文本总行数: {len(lines)}")
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # 跳过空行和过短的行
            if not line_stripped or len(line_stripped) < min_chapter_length:
                char_position += len(line) + 1  # +1 for newline
                continue
                
            # 跳过过长的行（可能不是章节标题）
            if len(line_stripped) > 100:
                char_position += len(line) + 1
                continue
                
            # 检查是否匹配任何章节模式
            for i, pattern in enumerate(self.compiled_patterns):
                if pattern.match(line_stripped):
                    # 确定章节级别
                    level = self._determine_chapter_level(line_stripped)
                    
                    chapter_info = {
                        'title': line_stripped,
                        'line_number': line_num,
                        'char_position': char_position,
                        'level': level
                    }
                    chapters.append(chapter_info)
                    
                    # 记录匹配的模式
                    pattern_name = f"模式{i+1}"
                    matched_patterns[pattern_name] = matched_patterns.get(pattern_name, 0) + 1
                    
                    logging.info(f"找到章节 [{line_num}行]: {line_stripped} (级别: {level}, 模式: {pattern_name})")
                    break
                    
            char_position += len(line) + 1
            
            # 限制章节数量，避免解析过多内容
            if len(chapters) >= max_chapters:
                logging.warning(f"达到最大章节数量限制 {max_chapters}，停止解析")
                break
        
        logging.info(f"初步解析完成，找到 {len(chapters)} 个章节")
        logging.info(f"匹配模式统计: {matched_patterns}")
        
        # 过滤和排序章节
        filtered_chapters = self._filter_and_sort_chapters(chapters)
        
        logging.info(f"过滤后章节数量: {len(filtered_chapters)}")
        logging.info("最终章节列表:")
        for i, chapter in enumerate(filtered_chapters[:20]):  # 只显示前20个章节
            logging.info(f"  {i+1}. [{chapter['line_number']}行] {chapter['title']} (级别: {chapter['level']})")
        
        if len(filtered_chapters) > 20:
            logging.info(f"  ... 还有 {len(filtered_chapters) - 20} 个章节")
        
        return filtered_chapters
        
    def _determine_chapter_level(self, title: str) -> int:
        """
        确定章节级别
        
        Args:
            title: 章节标题
            
        Returns:
            章节级别 (1-卷级别, 2-章节级别, 3-子章节级别)
        """
        # 卷级别标识符（最高级别）
        volume_indicators = ['卷', '部', '篇', '书']
        
        # 章节级别标识符（中级别）
        chapter_indicators = ['第.*章', '第.*回', 'Chapter', 'chapter', 'CHAPTER']
        
        # 子章节标识符（最低级别）
        sub_indicators = ['节', '段', '小节']
        
        # 检查是否为卷级别
        if any(indicator in title for indicator in volume_indicators):
            # 进一步检查是否为真正的卷标题
            if re.search(r'第.*[卷部篇书]', title) or re.search(r'^[卷部篇书]', title):
                return 1
                
        # 检查是否为子章节级别
        if any(indicator in title for indicator in sub_indicators):
            return 3
            
        # 检查是否为章节级别
        for pattern in chapter_indicators:
            if re.search(pattern, title):
                return 2
                
        # 检查数字格式的章节
        if re.search(r'第\d+[章回]', title) or re.search(r'第[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[章回]', title):
            return 2
            
        # 默认为章节级别
        return 2
        
    def _filter_and_sort_chapters(self, chapters: List[Dict]) -> List[Dict]:
        """
        过滤和排序章节列表
        
        Args:
            chapters: 原始章节列表
            
        Returns:
            过滤和排序后的章节列表
        """
        if not chapters:
            return []
            
        # 按行号排序
        chapters.sort(key=lambda x: x['line_number'])
        
        # 过滤重复和相似的章节
        filtered_chapters = []
        last_title = ""
        
        for chapter in chapters:
            title = chapter['title']
            
            # 验证章节标题的合理性
            if not self._is_valid_chapter_title(title):
                logging.info(f"过滤掉无效章节: {title}")
                continue
            
            # 跳过与上一个章节标题相同或非常相似的章节
            if title != last_title and not self._is_similar_title(title, last_title):
                filtered_chapters.append(chapter)
                last_title = title
                
        return filtered_chapters
        
    def _is_valid_chapter_title(self, title: str) -> bool:
        """
        验证章节标题的合理性
        
        Args:
            title: 章节标题
            
        Returns:
            是否为有效的章节标题
        """
        # 去除首尾空白
        title = title.strip()
        
        # 检查长度（章节标题不应该太长）
        if len(title) > 50:
            return False
            
        # 检查是否包含乱码字符
        if self._contains_garbled_text(title):
            logging.info(f"过滤掉包含乱码的章节: {title}")
            return False
            
        # 检查是否包含明显的章节标识符
        chapter_indicators = [
            '第', '章', '回', '节', '篇', '卷', '部', '集',
            'Chapter', 'chapter', 'CHAPTER',
            '序章', '楔子', '尾声', '后记', '番外', '终章', '结局', '完结',
            '前言', '引言', '结语', '序言', '后语',
            '上篇', '中篇', '下篇', '前篇', '后篇'
        ]
        
        # 检查书名号格式
        if title.startswith('《') and '》' in title:
            return True
            
        # 检查方括号格式
        if title.startswith('【') and '】' in title:
            return True
            
        # 检查是否包含章节标识符
        has_indicator = any(indicator in title for indicator in chapter_indicators)
        
        # 如果包含明确的章节标识符，进一步验证
        if has_indicator:
            # 检查是否为真正的章节格式
            if re.search(r'第[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[章回节篇卷部集]', title):
                return True
            # 检查其他章节标识符
            if any(indicator in title for indicator in ['序章', '楔子', '尾声', '后记', '番外', '终章', '结局', '完结', '前言', '引言', '结语', '序言', '后语']):
                return True
            if any(indicator in title for indicator in ['上篇', '中篇', '下篇', '前篇', '后篇']):
                return True
                
        # 对于数字格式，需要更严格的验证
        if not has_indicator:
            # 检查是否为可能的错误识别内容
            if self._is_likely_enumeration_content(title):
                return False
                
            # 数字开头的格式：1、2、3或1.、2.、3.等（限制范围和内容）
            if re.match(r'^\s*[1-9]\d{0,2}[、．.]', title):
                # 进一步检查内容是否像章节标题
                if self._is_likely_chapter_content(title):
                    return True
                return False
                
            # 括号数字格式：(1)、(2)、(3)等
            if re.match(r'^\s*\([1-9]\d{0,2}\)', title):
                if self._is_likely_chapter_content(title):
                    return True
                return False
                
            # 方括号数字格式：[1]、[2]、[3]等
            if re.match(r'^\s*\[[1-9]\d{0,2}\]', title):
                if self._is_likely_chapter_content(title):
                    return True
                return False
                
            # 中文数字格式：一、二、三等
            if re.match(r'^\s*[一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬]+[、．.]', title):
                if self._is_likely_chapter_content(title):
                    return True
                return False
                
            return False
            
        # 检查是否为完整句子（可能是误匹配的正文）
        # 如果包含过多标点符号或者是完整的句子，可能不是章节标题
        punctuation_count = sum(1 for char in title if char in '，。！？；：')
        if punctuation_count > 2:
            return False
            
        return True
        
    def _is_likely_enumeration_content(self, title: str) -> bool:
        """
        检查是否为可能的列举内容（非章节标题）
        
        Args:
            title: 标题文本
            
        Returns:
            是否为列举内容
        """
        # 常见的列举内容特征
        enumeration_patterns = [
            # 包含网址、邮箱等
            r'[a-zA-Z0-9]+\.[a-zA-Z]{2,}',  # 网址
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # 邮箱
            # 包含QQ号、手机号等
            r'QQ\d+',  # QQ号
            r'\d{11}',  # 手机号
            r'\d{3,}[xX]{3,}',  # 部分隐藏的数字
            # 包含技术术语、型号等
            r'\d+\.\d+[Tt]v\d+',  # 发动机型号等
            r'[Cc]os吧|贴吧|回复',  # 贴吧相关
            r'反诈骗|联盟|报告',  # 反诈骗相关
            r'包裹|快递|跟踪',  # 快递相关
            r'已知.*为实常数',  # 数学题目
            r'数列.*通向',  # 数学术语
            r'属于.*使得',  # 数学表达
        ]
        
        for pattern in enumeration_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
                
        return False
        
    def _is_likely_chapter_content(self, title: str) -> bool:
        """
        检查内容是否像章节标题
        
        Args:
            title: 标题文本
            
        Returns:
            是否像章节标题
        """
        # 去除数字前缀，获取实际内容
        content = re.sub(r'^\s*[\d一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬()\[\]、．.：:：\s]+', '', title).strip()
        
        # 如果去除前缀后内容太短，可能不是章节
        if len(content) < 2:
            return False
            
        # 如果内容太长，可能是正文
        if len(content) > 30:
            return False
            
        # 检查是否包含章节相关的词汇
        chapter_related_words = [
            '开始', '结束', '初遇', '相遇', '离别', '回忆', '梦境', '觉醒',
            '战斗', '决战', '胜利', '失败', '成长', '变化', '秘密', '真相',
            '危机', '转机', '希望', '绝望', '重生', '新生', '终结', '开端'
        ]
        
        # 如果包含章节相关词汇，更可能是章节
        if any(word in content for word in chapter_related_words):
            return True
            
        # 检查是否为纯中文内容（更可能是章节标题）
        chinese_chars = sum(1 for char in content if '\u4e00' <= char <= '\u9fff')
        total_chars = len(content)
        
        if total_chars > 0 and chinese_chars / total_chars > 0.7:
            return True
            
        # 检查是否包含特殊符号（可能是列举内容）
        special_symbols = ['@', '.com', '.cn', 'http', 'www', 'QQ', 'qq']
        if any(symbol in content for symbol in special_symbols):
            return False
            
        return True
        
    def _contains_garbled_text(self, text: str) -> bool:
        """
        检查文本是否包含乱码字符
        
        Args:
            text: 要检查的文本
            
        Returns:
            是否包含乱码字符
        """
        # 常见的乱码字符模式
        garbled_patterns = [
            # 连续的特殊字符或符号
            r'[ٵΪ]{2,}',  # 阿拉伯文字符
            r'[ѷû桪йթƭ]{3,}',  # 西里尔文等字符
            r'[ɣظšħcos]{3,}',  # 其他特殊字符
            r'[ǼǴļ]{2,}',  # 拉丁扩展字符
            r'[˫ѹķ]{2,}',  # 更多特殊字符
            r'[ӴͻӦ顢òġܵʹ˿б֮С]{4,}',  # 混合字符
            r'[ϼ쵼񡣡]{3,}',  # 其他乱码字符
            # 检查是否包含过多非中文、非英文、非数字的字符
            r'[^\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\u2ceb0-\u2ebef\u30000-\u3134fa-zA-Z0-9\s\(\)\[\]【】《》第章回节篇卷部集一二三四五六七八九十百千万零壹贰叁肆伍陆柒捌玖拾佰仟萬、．.：:：！？，。；]{5,}'
        ]
        
        # 检查是否匹配乱码模式
        for pattern in garbled_patterns:
            if re.search(pattern, text):
                return True
                
        # 检查字符编码合理性
        try:
            # 尝试编码为UTF-8，如果失败可能是乱码
            text.encode('utf-8')
        except UnicodeEncodeError:
            return True
            
        # 检查是否包含过多不可打印字符
        printable_chars = sum(1 for char in text if char.isprintable() or char in '\u4e00-\u9fff')
        total_chars = len(text)
        if total_chars > 0 and printable_chars / total_chars < 0.7:
            return True
            
        return False
        
    def _is_similar_title(self, title1: str, title2: str) -> bool:
        """
        检查两个标题是否相似
        
        Args:
            title1: 第一个标题
            title2: 第二个标题
            
        Returns:
            是否相似
        """
        if not title1 or not title2:
            return False
            
        # 简单的相似度检查：如果两个标题的前10个字符相同，认为相似
        return title1[:10] == title2[:10]
        
    def get_chapter_summary(self, chapters: List[Dict]) -> Dict:
        """
        获取章节统计信息
        
        Args:
            chapters: 章节列表
            
        Returns:
            统计信息字典
        """
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