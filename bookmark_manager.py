#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
书签管理模块 - 处理书签的存储和管理
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class BookmarkManager:
    """书签管理器类"""
    
    def __init__(self, bookmark_file='bookmarks.json'):
        """初始化书签管理器
        
        Args:
            bookmark_file: 书签文件名，默认为 bookmarks.json
        """
        # 获取AppData目录下的ReadFish文件夹
        appdata_dir = os.path.expanduser('~\\AppData\\Roaming\\ReadFish')
        # 确保目录存在
        os.makedirs(appdata_dir, exist_ok=True)
        self.bookmark_file = os.path.join(appdata_dir, bookmark_file)
        
        # 书签数据结构
        # {
        #     "books": {
        #         "book_id": {
        #             "file_path": "/path/to/book.txt",
        #             "title": "书籍标题",
        #             "bookmarks": [
        #                 {
        #                     "id": "bookmark_id",
        #                     "name": "书签名称",
        #                     "line_number": 100,
        #                     "char_position": 1500,
        #                     "content_preview": "书签位置的文本预览",
        #                     "created_time": "2024-01-01 12:00:00",
        #                     "note": "用户备注"
        #                 }
        #             ]
        #         }
        #     }
        # }
        
        # 加载书签数据
        self.bookmark_data = self.load_bookmarks()
        
    def load_bookmarks(self) -> Dict[str, Any]:
        """加载书签数据
        
        Returns:
            书签数据字典
        """
        try:
            if os.path.exists(self.bookmark_file):
                with open(self.bookmark_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保数据结构正确
                    if 'books' not in data:
                        data['books'] = {}
                    return data
        except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
            print(f"加载书签数据失败: {e}")
        
        # 返回默认结构
        return {'books': {}}
    
    def save_bookmarks(self) -> bool:
        """保存书签数据到文件
        
        Returns:
            是否保存成功
        """
        try:
            with open(self.bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmark_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存书签数据失败: {e}")
            return False
    
    def get_book_id(self, file_path: str) -> str:
        """根据文件路径生成书籍ID
        
        Args:
            file_path: 文件路径
            
        Returns:
            书籍ID
        """
        # 使用文件路径的绝对路径作为ID
        return os.path.abspath(file_path)
    
    def add_bookmark(self, file_path: str, title: str, line_number: int, 
                    char_position: int, content_preview: str, 
                    name: str = None, note: str = "") -> str:
        """添加书签
        
        Args:
            file_path: 文件路径
            title: 书籍标题
            line_number: 行号
            char_position: 字符位置
            content_preview: 内容预览
            name: 书签名称（可选，默认使用时间）
            note: 用户备注
            
        Returns:
            书签ID
        """
        book_id = self.get_book_id(file_path)
        
        # 确保书籍记录存在
        if book_id not in self.bookmark_data['books']:
            self.bookmark_data['books'][book_id] = {
                'file_path': file_path,
                'title': title,
                'bookmarks': []
            }
        
        # 生成书签ID和名称
        bookmark_id = f"bookmark_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        if not name:
            name = f"书签 {datetime.now().strftime('%m-%d %H:%M')}"
        
        # 创建书签数据
        bookmark = {
            'id': bookmark_id,
            'name': name,
            'line_number': line_number,
            'char_position': char_position,
            'content_preview': content_preview[:100],  # 限制预览长度
            'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': note
        }
        
        # 添加书签
        self.bookmark_data['books'][book_id]['bookmarks'].append(bookmark)
        
        # 按行号排序书签
        self.bookmark_data['books'][book_id]['bookmarks'].sort(
            key=lambda x: x['line_number']
        )
        
        # 保存数据
        self.save_bookmarks()
        
        return bookmark_id
    
    def get_bookmarks(self, file_path: str) -> List[Dict[str, Any]]:
        """获取指定书籍的所有书签
        
        Args:
            file_path: 文件路径
            
        Returns:
            书签列表
        """
        book_id = self.get_book_id(file_path)
        
        if book_id in self.bookmark_data['books']:
            return self.bookmark_data['books'][book_id]['bookmarks']
        
        return []
    
    def delete_bookmark(self, file_path: str, bookmark_id: str) -> bool:
        """删除指定书签
        
        Args:
            file_path: 文件路径
            bookmark_id: 书签ID
            
        Returns:
            是否删除成功
        """
        book_id = self.get_book_id(file_path)
        
        if book_id in self.bookmark_data['books']:
            bookmarks = self.bookmark_data['books'][book_id]['bookmarks']
            
            # 查找并删除书签
            for i, bookmark in enumerate(bookmarks):
                if bookmark['id'] == bookmark_id:
                    del bookmarks[i]
                    self.save_bookmarks()
                    return True
        
        return False
    
    def update_bookmark(self, file_path: str, bookmark_id: str, 
                       name: str = None, note: str = None) -> bool:
        """更新书签信息
        
        Args:
            file_path: 文件路径
            bookmark_id: 书签ID
            name: 新的书签名称
            note: 新的备注
            
        Returns:
            是否更新成功
        """
        book_id = self.get_book_id(file_path)
        
        if book_id in self.bookmark_data['books']:
            bookmarks = self.bookmark_data['books'][book_id]['bookmarks']
            
            # 查找并更新书签
            for bookmark in bookmarks:
                if bookmark['id'] == bookmark_id:
                    if name is not None:
                        bookmark['name'] = name
                    if note is not None:
                        bookmark['note'] = note
                    
                    self.save_bookmarks()
                    return True
        
        return False
    
    def get_bookmark_by_id(self, file_path: str, bookmark_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取书签
        
        Args:
            file_path: 文件路径
            bookmark_id: 书签ID
            
        Returns:
            书签数据，如果不存在返回None
        """
        book_id = self.get_book_id(file_path)
        
        if book_id in self.bookmark_data['books']:
            bookmarks = self.bookmark_data['books'][book_id]['bookmarks']
            
            for bookmark in bookmarks:
                if bookmark['id'] == bookmark_id:
                    return bookmark
        
        return None
    
    def clear_bookmarks(self, file_path: str) -> bool:
        """清空指定书籍的所有书签
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否清空成功
        """
        book_id = self.get_book_id(file_path)
        
        if book_id in self.bookmark_data['books']:
            self.bookmark_data['books'][book_id]['bookmarks'] = []
            self.save_bookmarks()
            return True
        
        return False
    
    def get_bookmark_count(self, file_path: str) -> int:
        """获取指定书籍的书签数量
        
        Args:
            file_path: 文件路径
            
        Returns:
            书签数量
        """
        return len(self.get_bookmarks(file_path))
    
    def export_bookmarks(self, file_path: str, export_file: str) -> bool:
        """导出书签到文件
        
        Args:
            file_path: 书籍文件路径
            export_file: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            bookmarks = self.get_bookmarks(file_path)
            
            export_data = {
                'book_title': self.bookmark_data['books'].get(
                    self.get_book_id(file_path), {}
                ).get('title', '未知书籍'),
                'file_path': file_path,
                'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'bookmarks': bookmarks
            }
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"导出书签失败: {e}")
            return False