#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import argparse
import logging
import time
from pathlib import Path

# 添加pipeline目录到Python路径
sys.path.append(str(Path(__file__).parent / "pipeline"))

from pipeline.sora_web_client import SoraWebClient
from pipeline.utils import setup_logging

def find_prompt_and_image(base_dir=None):
    """
    查找prompt.txt和color_000000.png文件
    
    Args:
        base_dir: 基础目录，如果为None则使用当前目录
        
    Returns:
        (prompt_path, image_path)元组，如果找不到则返回(None, None)
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)
    
    # 首先检查是否存在prompt_and_image目录
    prompt_and_image_dir = base_dir / "prompt_and_image"
    if prompt_and_image_dir.exists() and prompt_and_image_dir.is_dir():
        # 查找prompt.txt
        prompt_path = prompt_and_image_dir / "prompt.txt"
        if not prompt_path.exists():
            logging.error(f"在 {prompt_and_image_dir} 中找不到prompt.txt文件")
            prompt_path = None
        
        # 查找color_000000.png
        image_path = prompt_and_image_dir / "color_000000.png"
        if not image_path.exists():
            logging.error(f"在 {prompt_and_image_dir} 中找不到color_000000.png文件")
            image_path = None
        
        return prompt_path, image_path
    
    # 如果没有专门的目录，则在当前目录下查找
    prompt_path = base_dir / "prompt.txt"
    if not prompt_path.exists():
        logging.error(f"在 {base_dir} 中找不到prompt.txt文件")
        prompt_path = None
    
    image_path = base_dir / "color_000000.png"
    if not image_path.exists():
        logging.error(f"在 {base_dir} 中找不到color_000000.png文件")
        image_path = None
    
    return prompt_path, image_path

def run_automation(prompt_path, image_path, output_dir="./output", config_path="pipeline/config.yaml", retry_count=1):
    """
    运行Sora自动化流程
    
    Args:
        prompt_path: 提示文件路径
        image_path: 图像文件路径
        output_dir: 输出目录
        config_path: 配置文件路径
        retry_count: 失败后的重试次数
        
    Returns:
        成功生成的视频数量，如果失败则返回0
    """
    logger = logging.getLogger('sora_automation')
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 尝试执行自动化流程，最多重试指定次数
    success = False
    for attempt in range(retry_count + 1):
        try:
            if attempt > 0:
                logger.warning(f"第 {attempt} 次重试...")
                time.sleep(5)  # 等待5秒后重试
            
            # 创建临时目录
            temp_dir = Path("./temp")
            temp_dir.mkdir(exist_ok=True)
            
            # 运行自动化流程
            with SoraWebClient(config_path=config_path, output_root=output_dir, temp_dir=temp_dir) as client:
                # 访问Sora网站
                if not client.login_to_sora():
                    logger.error("无法访问Sora网站")
                    continue
                
                # 处理生成流程
                success = client.process_pipeline(prompt_path, image_path, output_dir)
                if success:
                    logger.info("成功完成视频生成")
                    break
                else:
                    logger.error("视频生成失败")
        except Exception as e:
            logger.error(f"执行过程中发生错误: {str(e)}")
    
    if not success:
        logger.error(f"在 {retry_count} 次尝试后仍然失败，终止处理")
        return 0
    
    # 返回生成的视频数量
    video_dirs = list(output_dir.glob("video_*"))
    return len(video_dirs)

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="Sora自动化视频生成工具")
    parser.add_argument("--prompt", help="提示文件路径")
    parser.add_argument("--image", help="图像文件路径")
    parser.add_argument("--output", default="./output", help="输出目录")
    parser.add_argument("--config", default="pipeline/config.yaml", help="配置文件路径")
    parser.add_argument("--retry", type=int, default=3, help="失败后的重试次数")
    parser.add_argument("--mock", action="store_true", help="使用模拟模式，不实际启动浏览器")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 查找prompt和图像文件
    if args.prompt and args.image:
        prompt_path = Path(args.prompt)
        image_path = Path(args.image)
    else:
        prompt_path, image_path = find_prompt_and_image()
    
    if not prompt_path or not image_path:
        logger.error("无法找到提示文件或图像文件，请确保文件存在")
        sys.exit(1)
    
    # 显示即将处理的文件
    logger.info(f"开始处理，提示文件: {prompt_path}，图像文件: {image_path}")
    
    # 运行自动化流程
    video_count = run_automation(
        prompt_path, 
        image_path, 
        output_dir=args.output, 
        config_path=args.config, 
        retry_count=args.retry
    )
    
    if video_count > 0:
        logger.info(f"成功生成 {video_count} 个视频")
        sys.exit(0)
    else:
        logger.error("未能成功生成视频")
        sys.exit(1)

if __name__ == "__main__":
    main() 