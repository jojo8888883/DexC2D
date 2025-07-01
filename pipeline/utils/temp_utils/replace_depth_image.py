#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

def replace_depth_image(source_file, target_dir, pattern, target_filename):
    """
    用源文件替换目标目录下所有匹配特定模式的子文件夹中的特定文件
    
    Args:
        source_file: 源文件路径
        target_dir: 目标基础目录
        pattern: 子文件夹名称需包含的模式
        target_filename: 目标文件名
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
    
    replaced_count = 0
    error_count = 0
    skipped_count = 0
    
    # 遍历所有子目录
    for subdir in target_path.iterdir():
        if subdir.is_dir() and pattern in subdir.name:
            target_file = subdir / target_filename
            try:
                # 复制源文件到目标位置
                shutil.copy2(source_path, target_file)
                replaced_count += 1
                print(f"已替换: {target_file}")
            except Exception as e:
                error_count += 1
                print(f"替换失败: {target_file}, 错误: {e}")
        else:
            skipped_count += 1
    
    print(f"\n处理完成: 成功替换 {replaced_count} 个文件, 失败 {error_count} 个, 跳过 {skipped_count} 个目录")

if __name__ == "__main__":
    # 将路径和文件名设置为变量，方便修改
    source_file = "/home/airs/Project/embodied_ai/DexC2D/capture_oneshot/035_power_drill/depth_20250611T034940634.png"
    target_dir = "/home/airs/Project/embodied_ai/DexC2D/gen_dataset/gen_datas"
    pattern = "035_power_drill_above"
    target_filename = "depth_000000.png"
    
    replace_depth_image(source_file, target_dir, pattern, target_filename) 