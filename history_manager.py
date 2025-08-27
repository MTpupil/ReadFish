#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史记录管理模块 - 处理阅读历史记录的存储和管理
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class HistoryManager:
    """历史记录管理器类"""
    
    def __init__(self, history_file='reading_history.json'):
        """初始化历史记录管理器
        
        Args:
            history_file: 历史记录文件名，默认为 reading_history.json
        """
        # 获取AppData目录下的ReadFish文件夹
        appdata_dir = os.path.expanduser('~\\AppData\\Roaming\\ReadFish')
        # 确保目录存在
        os.makedirs(appdata_dir, exist_ok=True)
        self.history_file = os.path.join(appdata_dir, history_file)
        
        # 历史记录数据结构
        # {
        #     "last_read_book": "book_id",  # 最后阅读的书籍ID
        #     "books": {
        #         "book_id": {
        #             "file_path": "/path/to/book.txt",
        #             "title": "书籍标题",
        #             "current_line_index": 0,  # 当前行索引
        #             "current_char_offset": 0,  # 当前字符偏移
        #             "total_lines": 100,  # 总行数
        #             "last_read_time": "2024-01-01 12:00:00",  # 最后阅读时间
        #             "reading_progress": 0.5  # 阅读进度 (0.0-1.0)
        #         }
        #     }
        # }
        
        # 加载历史记录
        self.history_data = self.load_history()
        
    def load_history(self) -> Dict[str, Any]:
        """从文件加载历史记录
        
        Returns:
            历史记录字典
        """
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果历史记录文件不存在，返回空的历史记录结构
                return {
                    "last_read_book": None,
                    "books": {}
                }
                
        except (json.JSONDecodeError, IOError) as e:
            # 加载历史记录文件失败，使用默认数据
            return {
                "last_read_book": None,
                "books": {}
            }
            
    def save_history(self) -> bool:
        """保存历史记录到文件
        
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
            
            # 保存历史记录
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, indent=4, ensure_ascii=False)
                
            return True
            
        except (IOError, TypeError) as e:
            # 保存历史记录文件失败
            return False
            
    def get_book_id(self, file_path: str) -> str:
        """根据文件路径生成书籍ID
        
        Args:
            file_path: 书籍文件路径
            
        Returns:
            书籍ID
        """
        # 使用文件路径的哈希值作为书籍ID
        import hashlib
        return hashlib.md5(file_path.encode('utf-8')).hexdigest()
        
    def update_reading_position(self, file_path: str, title: str, 
                              current_line_index: int, current_char_offset: int, 
                              total_lines: int) -> bool:
        """更新书籍的阅读位置
        
        Args:
            file_path: 书籍文件路径
            title: 书籍标题
            current_line_index: 当前行索引
            current_char_offset: 当前字符偏移
            total_lines: 总行数
            
        Returns:
            更新是否成功
        """
        try:
            book_id = self.get_book_id(file_path)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 计算阅读进度
            reading_progress = 0.0
            if total_lines > 0:
                reading_progress = current_line_index / total_lines
                reading_progress = min(1.0, max(0.0, reading_progress))  # 限制在0-1之间
            
            # 更新书籍信息
            self.history_data["books"][book_id] = {
                "file_path": file_path,
                "title": title,
                "current_line_index": current_line_index,
                "current_char_offset": current_char_offset,
                "total_lines": total_lines,
                "last_read_time": current_time,
                "reading_progress": reading_progress
            }
            
            # 更新最后阅读的书籍
            self.history_data["last_read_book"] = book_id
            
            # 保存到文件
            return self.save_history()
            
        except Exception as e:
            # 更新阅读位置失败
            return False
            
    def get_reading_position(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取书籍的阅读位置
        
        Args:
            file_path: 书籍文件路径
            
        Returns:
            阅读位置信息，如果没有记录则返回None
        """
        book_id = self.get_book_id(file_path)
        return self.history_data["books"].get(book_id)
        
    def get_last_read_book(self) -> Optional[Dict[str, Any]]:
        """获取最后阅读的书籍信息
        
        Returns:
            最后阅读的书籍信息，如果没有记录则返回None
        """
        last_book_id = self.history_data.get("last_read_book")
        if last_book_id and last_book_id in self.history_data["books"]:
            return self.history_data["books"][last_book_id]
        return None
        
    def get_all_books(self) -> Dict[str, Dict[str, Any]]:
        """获取所有书籍的历史记录
        
        Returns:
            所有书籍的历史记录字典
        """
        return self.history_data["books"].copy()
        
    def remove_book(self, file_path: str) -> bool:
        """移除书籍的历史记录
        
        Args:
            file_path: 书籍文件路径
            
        Returns:
            移除是否成功
        """
        try:
            book_id = self.get_book_id(file_path)
            
            if book_id in self.history_data["books"]:
                del self.history_data["books"][book_id]
                
                # 如果删除的是最后阅读的书籍，清空最后阅读记录
                if self.history_data["last_read_book"] == book_id:
                    self.history_data["last_read_book"] = None
                    
                return self.save_history()
                
            return True
            
        except Exception as e:
            # 移除书籍历史记录失败
            return False
            
    def clear_history(self) -> bool:
        """清空所有历史记录
        
        Returns:
            清空是否成功
        """
        try:
            self.history_data = {
                "last_read_book": None,
                "books": {}
            }
            return self.save_history()
            
        except Exception as e:
            # 清空历史记录失败
            return False
            
    def has_history(self) -> bool:
        """检查是否有历史记录
        
        Returns:
            是否有历史记录
        """
        return self.history_data.get('last_read_book') is not None
        
    def get_last_file(self) -> Optional[str]:
        """获取最后阅读的文件路径
        
        Returns:
            最后阅读的文件路径，如果没有记录则返回None
        """
        last_book = self.get_last_read_book()
        if last_book:
            return last_book.get('file_path')
        return None