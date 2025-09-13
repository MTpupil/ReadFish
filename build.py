#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReadFish 简化打包脚本 - 避免编码问题

功能:
- 检查打包依赖
- 清理构建目录
- 构建可执行文件
- 验证构建结果
- 创建发布包
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

def print_step(message):
    """打印步骤信息 - 使用ASCII字符"""
    print("\n" + "=" * 50)
    print(f"[PACK] {message}")
    print("=" * 50)

def print_info(message):
    """打印信息"""
    print(f"[INFO] {message}")

def print_success(message):
    """打印成功信息"""
    print(f"[OK] {message}")

def print_error(message):
    """打印错误信息"""
    print(f"[ERROR] {message}")

def print_warning(message):
    """打印警告信息"""
    print(f"[WARN] {message}")

def check_dependencies():
    """检查打包依赖"""
    print_step("检查打包依赖")
    
    # 检查PyInstaller
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'show', 'pyinstaller'], 
                              capture_output=True, text=True, encoding='utf-8')
        if result.returncode == 0:
            # 提取版本信息
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':')[1].strip()
                    print_success(f"PyInstaller 已安装 (版本: {version})")
                    break
        else:
            print_warning("PyInstaller 未安装，正在安装...")
            install_result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], 
                                          capture_output=True, text=True)
            if install_result.returncode == 0:
                print_success("PyInstaller 安装成功")
            else:
                print_error("PyInstaller 安装失败")
                return False
    except Exception as e:
        print_error(f"检查PyInstaller时出错: {str(e)}")
        return False
    
    # 检查PyQt5
    try:
        import PyQt5
        print_success("PyQt5 已安装")
    except ImportError:
        print_warning("PyQt5 未安装，但不影响打包")
    
    # 检查Pillow（用于图标转换）
    try:
        from PIL import Image
        print_success("Pillow 已安装 (支持图标转换)")
    except ImportError:
        print_warning("Pillow 未安装，将跳过ICO图标创建")
        print_info("建议安装: pip install Pillow")
    
    return True

def clean_build_dirs():
    """清理构建目录"""
    print_step("清理构建目录")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                # 强制删除目录
                if os.path.isdir(dir_name):
                    # 先尝试修改权限
                    for root, dirs, files in os.walk(dir_name):
                        for d in dirs:
                            os.chmod(os.path.join(root, d), 0o777)
                        for f in files:
                            os.chmod(os.path.join(root, f), 0o777)
                    
                    # 删除目录
                    shutil.rmtree(dir_name, ignore_errors=True)
                    
                    # 等待一下确保删除完成
                    time.sleep(0.5)
                    
                    if not os.path.exists(dir_name):
                        print_success(f"已清理目录: {dir_name}")
                    else:
                        print_warning(f"目录可能未完全清理: {dir_name}")
                        
            except Exception as e:
                print_warning(f"清理目录 {dir_name} 时出错: {str(e)}")
    
    # 清理.pyc文件
    print_info("清理.pyc文件...")
    pyc_count = 0
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    pyc_count += 1
                except:
                    pass
    
    if pyc_count > 0:
        print_success(f"已清理 {pyc_count} 个.pyc文件")
    else:
        print_info("没有找到.pyc文件")

def build_executable():
    """构建可执行文件"""
    print_step("构建可执行文件")
    
    # 检查并创建ICO图标文件
    if os.path.exists('logo.png') and not os.path.exists('logo.ico'):
        print_info("检测到PNG图标，正在创建ICO格式...")
        try:
            # 尝试导入PIL库
            from PIL import Image
            
            # 打开PNG图片并转换为ICO
            img = Image.open('logo.png')
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 创建多个尺寸的图标
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128)]
            img.save('logo.ico', format='ICO', sizes=sizes)
            
            print_success("ICO图标创建成功")
            
        except ImportError:
            print_warning("未安装PIL库，跳过ICO图标创建")
            print_info("可运行: pip install Pillow")
        except Exception as e:
            print_warning(f"ICO图标创建失败: {str(e)}")
    
    # 检查spec文件
    spec_file = 'ReadFish.spec'
    if os.path.exists(spec_file):
        print_info(f"使用配置文件: {spec_file}")
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', spec_file]
    else:
        print_info("使用默认配置构建")
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--name=ReadFish',
            '--add-data=logo.png;.',
            '--add-data=logo.svg;.',
            'main.py'
        ]
    
    print_info(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 执行构建命令
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print_success("可执行文件构建完成")
            return True
        else:
            print_error("构建失败")
            if result.stderr:
                print_error(f"错误信息: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"构建过程中出现异常: {str(e)}")
        return False

def verify_build():
    """验证构建结果"""
    print_step("验证构建结果")
    
    exe_path = os.path.join('dist', 'ReadFish.exe')
    
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print_success(f"可执行文件已生成: {exe_path}")
        print_info(f"文件大小: {file_size:.2f} MB")
        
        # 检查资源文件
        resource_files = ['logo.png', 'logo.svg']
        for resource in resource_files:
            if not os.path.exists(resource):
                print_warning(f"资源文件缺失: {resource}")
        
        return True
    else:
        print_error(f"可执行文件未生成: {exe_path}")
        return False

def create_release_package():
    """创建发布包"""
    print_step("创建发布包")
    
    release_dir = 'release'
    
    # 创建发布目录
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir, ignore_errors=True)
    
    os.makedirs(release_dir, exist_ok=True)
    print_success(f"创建发布目录: {release_dir}")
    
    # 复制可执行文件
    exe_src = os.path.join('dist', 'ReadFish.exe')
    exe_dst = os.path.join(release_dir, 'ReadFish.exe')
    
    if os.path.exists(exe_src):
        shutil.copy2(exe_src, exe_dst)
        print_success("复制可执行文件")
    
    # 复制其他文件
    files_to_copy = ['README.md', 'LICENSE.txt']
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy2(file_name, os.path.join(release_dir, file_name))
            print_success(f"复制文件: {file_name}")
    
    # 创建使用说明
    usage_text = """ReadFish 使用说明
==================

1. 双击 ReadFish.exe 启动程序
2. 首次使用时会要求选择电子书目录
3. 支持的格式: TXT, EPUB, PDF 等
4. 使用 Ctrl+O 打开文件，Ctrl+B 管理书签

更多信息请查看 README.md 文件。
"""
    
    usage_file = os.path.join(release_dir, '使用说明.txt')
    with open(usage_file, 'w', encoding='utf-8') as f:
        f.write(usage_text)
    print_success("创建使用说明文件")
    
    print_success(f"发布包已创建在: {release_dir}")
    return True

def main():
    """主函数"""
    try:
        print_step("ReadFish 自动打包脚本")
        print_info("开始打包流程...")
        
        # 检查依赖
        if not check_dependencies():
            print_error("依赖检查失败")
            return False
        
        # 清理目录
        clean_build_dirs()
        
        # 构建可执行文件
        if not build_executable():
            print_error("构建失败")
            return False
        
        # 验证构建结果
        if not verify_build():
            print_error("验证失败")
            return False
        
        # 创建发布包
        if not create_release_package():
            print_error("创建发布包失败")
            return False
        
        print_step("打包完成")
        print_success("ReadFish 打包成功！")
        print_info("输出文件:")
        print_info("  - 可执行文件: dist/ReadFish.exe")
        print_info("  - 发布包: release/")
        print_info("")
        print_info("下一步可以运行 NSIS 创建安装程序:")
        print_info("  makensis installer.nsi")
        
        return True
        
    except KeyboardInterrupt:
        print_error("用户中断操作")
        return False
    except Exception as e:
        print_error(f"发生未预期的错误: {str(e)}")
        return False

if __name__ == '__main__':
    success = main()
    
    if success:
        print_success("打包成功完成")
    else:
        print_error("打包失败")
    
    # 等待用户按键
    input("按回车键退出...")
    sys.exit(0 if success else 1)