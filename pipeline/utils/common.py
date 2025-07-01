"""
通用工具模块，实现通用的工具函数
"""

import os
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

def ensure_directory(directory_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory_path: 目录路径
        
    Returns:
        bool: 操作是否成功
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {directory_path}, 错误: {e}")
        return False

def copy_file(src_path: str, dst_path: str, create_dst_dir: bool = True) -> bool:
    """
    复制文件
    
    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径
        create_dst_dir: 是否创建目标目录
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if not os.path.exists(src_path):
            print(f"源文件不存在: {src_path}")
            return False
            
        if create_dst_dir:
            dst_dir = os.path.dirname(dst_path)
            ensure_directory(dst_dir)
            
        shutil.copy2(src_path, dst_path)
        return True
    except Exception as e:
        print(f"复制文件失败: {src_path} -> {dst_path}, 错误: {e}")
        return False

def move_file(src_path: str, dst_path: str, create_dst_dir: bool = True) -> bool:
    """
    移动文件
    
    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径
        create_dst_dir: 是否创建目标目录
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if not os.path.exists(src_path):
            print(f"源文件不存在: {src_path}")
            return False
            
        if create_dst_dir:
            dst_dir = os.path.dirname(dst_path)
            ensure_directory(dst_dir)
            
        shutil.move(src_path, dst_path)
        return True
    except Exception as e:
        print(f"移动文件失败: {src_path} -> {dst_path}, 错误: {e}")
        return False

def delete_file(file_path: str, missing_ok: bool = True) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件路径
        missing_ok: 如果文件不存在，是否正常返回
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if not os.path.exists(file_path):
            if missing_ok:
                return True
            else:
                print(f"文件不存在: {file_path}")
                return False
                
        os.remove(file_path)
        return True
    except Exception as e:
        print(f"删除文件失败: {file_path}, 错误: {e}")
        return False

def get_next_index(directory: str, prefix: str, digits: int = 3) -> int:
    """
    根据已有目录前缀，返回下一个可用索引
    
    Args:
        directory: 目录路径
        prefix: 目录前缀
        digits: 索引位数
        
    Returns:
        int: 下一个可用索引
    """
    if not os.path.exists(directory):
        return 1
        
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d{{{digits}}})$")
    max_idx = 0
    
    for item in os.listdir(directory):
        if os.path.isdir(os.path.join(directory, item)):
            match = pattern.match(item)
            if match:
                max_idx = max(max_idx, int(match.group(1)))
                
    return max_idx + 1

def read_text_file(file_path: str, encoding: str = "utf-8") -> Optional[str]:
    """
    读取文本文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
        
    Returns:
        Optional[str]: 文件内容，失败则返回None
    """
    try:
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return None
            
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败: {file_path}, 错误: {e}")
        return None

def write_text_file(file_path: str, content: str, encoding: str = "utf-8", create_dir: bool = True) -> bool:
    """
    写入文本文件
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        create_dir: 是否创建目录
        
    Returns:
        bool: 操作是否成功
    """
    try:
        if create_dir:
            directory = os.path.dirname(file_path)
            ensure_directory(directory)
            
        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入文件失败: {file_path}, 错误: {e}")
        return False 