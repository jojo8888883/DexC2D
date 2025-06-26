#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def copy_cam_k_to_subdirs(source_file, target_dir):
    """
    将源文件复制到目标目录下的所有子文件夹中
    
    Args:
        source_file: 源文件路径
        target_dir: 目标目录路径
    """
    source_path = Path(source_file)
    target_path = Path(target_dir)
    
    # 确保源文件存在
    if not source_path.exists() or not source_path.is_file():
        print(f"错误: 源文件 '{source_file}' 不存在或不是一个文件")
        return
    
    # 确保目标目录存在
    if not target_path.exists() or not target_path.is_dir():
        print(f"错误: 目标目录 '{target_dir}' 不存在或不是一个目录")
        return
    
    copied_count = 0
    error_count = 0
    
    # 读取源文件内容
    try:
        with open(source_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"读取源文件失败: {e}")
        return
    
    # 遍历所有子目录
    for subdir in target_path.iterdir():
        if subdir.is_dir():
            target_file = subdir / "cam_K.txt"
            try:
                # 写入内容到目标文件
                with open(target_file, 'w') as f:
                    f.write(content)
                copied_count += 1
                print(f"已复制到: {target_file}")
            except Exception as e:
                error_count += 1
                print(f"复制失败: {target_file}, 错误: {e}")
    
    print(f"\n处理完成: 成功复制到 {copied_count} 个目录, 失败 {error_count} 个")

if __name__ == "__main__":
    source_file = "/home/airs/Project/embodied_ai/DexC2D/capture/cam_K.txt"
    target_dir = "/home/airs/Project/embodied_ai/DexC2D/gen_dataset/gen_datas"
    copy_cam_k_to_subdirs(source_file, target_dir) 