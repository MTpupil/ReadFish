#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本 - 将现有的配置和书籍数据迁移到AppData目录

使用方法：
1. 在升级到新版本前运行此脚本
2. 脚本会自动将现有数据迁移到AppData目录
3. 迁移完成后可以安全删除项目目录下的数据文件
"""

import os
import shutil
import json
from pathlib import Path


def get_appdata_dir():
    """获取AppData目录下的ReadFish文件夹"""
    appdata_dir = os.path.expanduser('~\\AppData\\Roaming\\ReadFish')
    os.makedirs(appdata_dir, exist_ok=True)
    return appdata_dir


def get_project_dir():
    """获取项目目录"""
    return os.path.dirname(os.path.abspath(__file__))


def migrate_file(source_path, target_path, file_description):
    """迁移单个文件
    
    Args:
        source_path: 源文件路径
        target_path: 目标文件路径
        file_description: 文件描述
    
    Returns:
        bool: 迁移是否成功
    """
    try:
        if os.path.exists(source_path):
            # 确保目标目录存在
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # 如果目标文件已存在，创建备份
            if os.path.exists(target_path):
                backup_path = target_path + '.backup'
                shutil.copy2(target_path, backup_path)
                print(f"已备份现有的{file_description}到: {backup_path}")
            
            # 复制文件
            shutil.copy2(source_path, target_path)
            print(f"✓ 已迁移{file_description}: {source_path} -> {target_path}")
            return True
        else:
            print(f"- {file_description}不存在，跳过迁移")
            return False
    except Exception as e:
        print(f"✗ 迁移{file_description}失败: {str(e)}")
        return False


def migrate_directory(source_dir, target_dir, dir_description):
    """迁移整个目录
    
    Args:
        source_dir: 源目录路径
        target_dir: 目标目录路径
        dir_description: 目录描述
    
    Returns:
        bool: 迁移是否成功
    """
    try:
        if os.path.exists(source_dir) and os.path.isdir(source_dir):
            # 确保目标目录存在
            os.makedirs(target_dir, exist_ok=True)
            
            # 复制目录内容
            for item in os.listdir(source_dir):
                source_item = os.path.join(source_dir, item)
                target_item = os.path.join(target_dir, item)
                
                if os.path.isfile(source_item):
                    shutil.copy2(source_item, target_item)
                elif os.path.isdir(source_item):
                    shutil.copytree(source_item, target_item, dirs_exist_ok=True)
            
            print(f"✓ 已迁移{dir_description}: {source_dir} -> {target_dir}")
            return True
        else:
            print(f"- {dir_description}不存在，跳过迁移")
            return False
    except Exception as e:
        print(f"✗ 迁移{dir_description}失败: {str(e)}")
        return False


def update_bookshelf_paths(bookshelf_file, old_book_dir, new_book_dir):
    """更新书架文件中的书籍路径
    
    Args:
        bookshelf_file: 书架文件路径
        old_book_dir: 旧的书籍目录
        new_book_dir: 新的书籍目录
    """
    try:
        if not os.path.exists(bookshelf_file):
            return
            
        with open(bookshelf_file, 'r', encoding='utf-8') as f:
            bookshelf_data = json.load(f)
        
        updated = False
        for book_name, book_info in bookshelf_data.items():
            old_path = book_info.get('file_path', '')
            if old_path and old_book_dir in old_path:
                # 更新路径
                filename = os.path.basename(old_path)
                new_path = os.path.join(new_book_dir, filename)
                book_info['file_path'] = new_path
                updated = True
                print(f"  更新书籍路径: {book_name} -> {new_path}")
        
        if updated:
            with open(bookshelf_file, 'w', encoding='utf-8') as f:
                json.dump(bookshelf_data, f, ensure_ascii=False, indent=2)
            print("✓ 已更新书架文件中的路径")
        
    except Exception as e:
        print(f"✗ 更新书架路径失败: {str(e)}")


def update_history_paths(history_file, old_book_dir, new_book_dir):
    """更新历史记录文件中的书籍路径
    
    Args:
        history_file: 历史记录文件路径
        old_book_dir: 旧的书籍目录
        new_book_dir: 新的书籍目录
    """
    try:
        if not os.path.exists(history_file):
            return
            
        with open(history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
        
        updated = False
        books = history_data.get('books', {})
        for book_id, book_info in books.items():
            old_path = book_info.get('file_path', '')
            if old_path and old_book_dir in old_path:
                # 更新路径
                filename = os.path.basename(old_path)
                new_path = os.path.join(new_book_dir, filename)
                book_info['file_path'] = new_path
                updated = True
                print(f"  更新历史记录路径: {book_info.get('title', 'Unknown')} -> {new_path}")
        
        if updated:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
            print("✓ 已更新历史记录文件中的路径")
        
    except Exception as e:
        print(f"✗ 更新历史记录路径失败: {str(e)}")


def main():
    """主函数 - 执行数据迁移"""
    print("ReadFish 数据迁移工具")
    print("=" * 50)
    
    # 获取路径
    project_dir = get_project_dir()
    appdata_dir = get_appdata_dir()
    
    print(f"项目目录: {project_dir}")
    print(f"AppData目录: {appdata_dir}")
    print()
    
    # 定义要迁移的文件和目录
    migrations = [
        {
            'type': 'file',
            'source': os.path.join(project_dir, 'config.json'),
            'target': os.path.join(appdata_dir, 'config.json'),
            'description': '配置文件'
        },
        {
            'type': 'file',
            'source': os.path.join(project_dir, 'bookshelf.json'),
            'target': os.path.join(appdata_dir, 'bookshelf.json'),
            'description': '书架数据文件'
        },
        {
            'type': 'file',
            'source': os.path.join(project_dir, 'reading_history.json'),
            'target': os.path.join(appdata_dir, 'reading_history.json'),
            'description': '阅读历史文件'
        },
        {
            'type': 'directory',
            'source': os.path.join(project_dir, 'book'),
            'target': os.path.join(appdata_dir, 'book'),
            'description': '书籍文件夹'
        }
    ]
    
    # 执行迁移
    print("开始迁移数据...")
    print()
    
    success_count = 0
    total_count = len(migrations)
    
    for migration in migrations:
        if migration['type'] == 'file':
            if migrate_file(migration['source'], migration['target'], migration['description']):
                success_count += 1
        elif migration['type'] == 'directory':
            if migrate_directory(migration['source'], migration['target'], migration['description']):
                success_count += 1
    
    print()
    
    # 更新文件中的路径引用
    print("更新文件中的路径引用...")
    old_book_dir = os.path.join(project_dir, 'book')
    new_book_dir = os.path.join(appdata_dir, 'book')
    
    update_bookshelf_paths(
        os.path.join(appdata_dir, 'bookshelf.json'),
        old_book_dir,
        new_book_dir
    )
    
    update_history_paths(
        os.path.join(appdata_dir, 'reading_history.json'),
        old_book_dir,
        new_book_dir
    )
    
    print()
    print("=" * 50)
    print(f"迁移完成！成功迁移 {success_count}/{total_count} 项")
    
    if success_count > 0:
        print()
        print("迁移成功！现在可以安全地删除项目目录下的以下文件：")
        print("- config.json")
        print("- bookshelf.json")
        print("- reading_history.json")
        print("- book/ 文件夹")
        print()
        print("注意：删除前请确认迁移的数据在AppData目录中正常工作。")
    
    input("\n按回车键退出...")


if __name__ == '__main__':
    main()