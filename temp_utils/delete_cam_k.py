#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def delete_cam_k_files(base_dir):
    """
    删除指定目录下所有子文件夹中的cam_K.txt文件
    
    Args:
        base_dir: 要处理的基础目录
    """
    base_path = Path(base_dir)
    
    # 确保目录存在
    if not base_path.exists() or not base_path.is_dir():
        print(f"错误: 目录 '{base_dir}' 不存在或不是一个目录")
        return
    
    deleted_count = 0
    error_count = 0
    
    # 遍历所有子目录
    for subdir in base_path.iterdir():
        if subdir.is_dir():
            target_file = subdir / "cam_K.txt"
            if target_file.exists():
                try:
                    target_file.unlink()
                    deleted_count += 1
                    print(f"已删除: {target_file}")
                except Exception as e:
                    error_count += 1
                    print(f"删除失败: {target_file}, 错误: {e}")
    
    print(f"\n处理完成: 成功删除 {deleted_count} 个文件, 失败 {error_count} 个文件")

if __name__ == "__main__":
    target_dir = "/home/airs/Project/embodied_ai/DexC2D/gen_dataset/gen_datas"
    delete_cam_k_files(target_dir) 