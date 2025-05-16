#!/usr/bin/env python
import os
import sys
import argparse
import logging
from pathlib import Path
import time
import shutil
import yaml

from utils import setup_logging
from sora_web_client import SoraWebClient

logger = logging.getLogger('pipeline')

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
            logger.error(f"在 {prompt_and_image_dir} 中找不到prompt.txt文件")
            prompt_path = None
        
        # 查找color_000000.png
        image_path = prompt_and_image_dir / "color_000000.png"
        if not image_path.exists():
            logger.error(f"在 {prompt_and_image_dir} 中找不到color_000000.png文件")
            image_path = None
        
        return prompt_path, image_path
    
    # 如果没有专门的目录，则在当前目录下查找
    prompt_path = base_dir / "prompt.txt"
    if not prompt_path.exists():
        logger.error(f"在 {base_dir} 中找不到prompt.txt文件")
        prompt_path = None
    
    image_path = base_dir / "color_000000.png"
    if not image_path.exists():
        logger.error(f"在 {base_dir} 中找不到color_000000.png文件")
        image_path = None
    
    return prompt_path, image_path

def create_prompt_and_image_dir(base_dir=None):
    """
    创建prompt_and_image目录结构
    
    Args:
        base_dir: 基础目录，如果为None则使用当前目录
        
    Returns:
        创建的目录路径
    """
    if base_dir is None:
        base_dir = Path.cwd()
    else:
        base_dir = Path(base_dir)
    
    prompt_and_image_dir = base_dir / "prompt_and_image"
    prompt_and_image_dir.mkdir(exist_ok=True)
    
    # 创建示例提示文件
    prompt_path = prompt_and_image_dir / "prompt.txt"
    if not prompt_path.exists():
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write("一只手握住一个饼干盒，将其旋转180度。背景是纯白色的。摄像机保持静止。")
    
    logger.info(f"创建了示例提示文件: {prompt_path}")
    
    # 提示用户需要添加图像文件
    print(f"请将color_000000.png图像文件放置在 {prompt_and_image_dir} 目录中")
    
    return prompt_and_image_dir

def process_videos(prompt_path, image_path, output_dir, config_path=None):
    """
    处理视频生成流水线
    
    Args:
        prompt_path: 提示文件路径
        image_path: 图像文件路径
        output_dir: 输出目录
        config_path: 配置文件路径
        
    Returns:
        如果成功处理则返回True，否则返回False
    """
    # 创建客户端
    with SoraWebClient(config_path=config_path, output_root=output_dir) as client:
        logger.info("初始化Sora Web客户端")
        # 确保不使用模拟模式
        client.use_mock = False
        logger.info(f"模拟模式已禁用: use_mock={client.use_mock}")
        
        # 访问Sora网站
        try:
            logger.info("尝试访问Sora网站...")
            sora_url = "https://sora.chatgpt.com/explore"
            login_success = client.login_to_sora(url=sora_url)
            if not login_success:
                logger.error("访问Sora失败，终止处理")
                return False
            logger.info("成功访问Sora网站")
        except Exception as e:
            logger.error(f"访问Sora网站过程中发生异常: {str(e)}")
            return False
        
        # 处理流水线
        try:
            logger.info("开始处理生成流水线...")
            pipeline_success = client.process_pipeline(prompt_path, image_path)
            if pipeline_success:
                logger.info("流水线处理成功")
            else:
                logger.error("流水线处理失败")
            return pipeline_success
        except Exception as e:
            logger.error(f"流水线处理过程中发生异常: {str(e)}")
            return False

def extract_frames_from_videos(video_dirs, output_rgb_dir):
    """
    从视频目录中提取帧并合并到一个rgb目录中
    
    Args:
        video_dirs: 视频目录列表
        output_rgb_dir: 输出rgb目录
        
    Returns:
        提取的帧数
    """
    output_rgb_dir = Path(output_rgb_dir)
    output_rgb_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理输出目录
    for f in output_rgb_dir.glob("frame_*.png"):
        f.unlink()
    
    # 确保帧数不超过150帧（5秒 x 30帧/秒）
    max_frames = 150
    frame_count = 0
    
    for video_dir in video_dirs:
        rgb_dir = Path(video_dir) / "rgb"
        if not rgb_dir.exists() or not rgb_dir.is_dir():
            logger.warning(f"视频目录中找不到rgb文件夹: {video_dir}")
            continue
        
        # 获取所有PNG帧
        frames = sorted(rgb_dir.glob("frame_*.png"))
        if not frames:
            # 尝试其他命名格式
            frames = sorted(rgb_dir.glob("*.png"))
        
        if not frames:
            logger.warning(f"rgb目录中找不到帧: {rgb_dir}")
            continue
        
        # 如果有多个视频通过过滤，只使用第一个视频的帧
        if frame_count == 0:  # 只处理第一个有效视频
            # 如果帧数超过150，只取前150帧
            frames_to_use = frames[:min(len(frames), max_frames)]
            
            # 复制帧到输出目录，确保命名格式是frame_000000.png到frame_000149.png
            for i, frame in enumerate(frames_to_use):
                target_frame = output_rgb_dir / f"frame_{i:06d}.png"
                shutil.copy2(frame, target_frame)
            
            frame_count = len(frames_to_use)
            logger.info(f"从 {rgb_dir} 提取了 {frame_count} 帧")
            
            # 如果帧数不足150，用最后一帧填充
            if frame_count < max_frames and frames_to_use:
                last_frame = frames_to_use[-1]
                for i in range(frame_count, max_frames):
                    target_frame = output_rgb_dir / f"frame_{i:06d}.png"
                    shutil.copy2(last_frame, target_frame)
                
                logger.info(f"用最后一帧填充至 {max_frames} 帧")
                frame_count = max_frames
            
            # 验证帧序列
            final_frames = sorted(output_rgb_dir.glob("frame_*.png"))
            if len(final_frames) != max_frames:
                logger.error(f"帧数不正确: {len(final_frames)} != {max_frames}")
                # 删除所有帧
                for f in final_frames:
                    f.unlink()
                return 0
            
            # 验证帧命名
            for i, frame in enumerate(final_frames):
                expected_name = f"frame_{i:06d}.png"
                if frame.name != expected_name:
                    logger.error(f"帧命名不正确: {frame.name} != {expected_name}")
                    # 删除所有帧
                    for f in final_frames:
                        f.unlink()
                    return 0
            
            # 只处理第一个视频就够了
            break
    
    logger.info(f"总共提取了 {frame_count} 帧到 {output_rgb_dir}")
    return frame_count

def main():
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="Sora Web自动化流水线")
    parser.add_argument("--prompt", help="提示文件路径")
    parser.add_argument("--image", help="图像文件路径")
    parser.add_argument("--output", help="输出目录", default="./output")
    parser.add_argument("--config", help="配置文件路径", default="pipeline/config.yaml")
    parser.add_argument("--init", action="store_true", help="初始化prompt_and_image目录")
    parser.add_argument("--retry", type=int, default=3, help="重试次数")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 初始化目录
    if args.init:
        create_prompt_and_image_dir()
        return
    
    # 确定输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 查找提示和图像文件
    if args.prompt and args.image:
        prompt_path = Path(args.prompt)
        image_path = Path(args.image)
    else:
        prompt_path, image_path = find_prompt_and_image()
    
    if prompt_path is None or image_path is None:
        logger.error("找不到提示文件或图像文件，使用--init参数创建必要的目录结构")
        return
    
    # 创建时间戳目录
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = output_dir / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理视频
    max_retries = args.retry
    retry_count = 0
    success = False
    
    while not success and retry_count < max_retries:
        if retry_count > 0:
            logger.warning(f"处理失败，正在重试... ({retry_count}/{max_retries})")
            # 在重试前清理temp目录的临时文件
            try:
                temp_dir = Path("./temp")
                for ext in ["*.png", "*.mp4", "*.html"]:
                    for file in temp_dir.glob(ext):
                        file.unlink()
                logger.info("已清理临时文件")
            except Exception as e:
                logger.warning(f"清理临时文件时出错: {str(e)}")
            time.sleep(5)  # 等待5秒后重试
        
        retry_count += 1
        logger.info(f"开始处理，提示文件: {prompt_path}，图像文件: {image_path}")
        
        try:
            success = process_videos(prompt_path, image_path, run_dir, args.config)
        except Exception as e:
            logger.error(f"处理过程中发生异常: {str(e)}")
            import traceback
            logger.error(f"异常堆栈: {traceback.format_exc()}")
            success = False
    
    if not success:
        logger.error(f"在 {max_retries} 次尝试后仍然失败，终止处理")
        return
    
    # 查找所有成功的视频目录
    video_dirs = []
    for item in run_dir.iterdir():
        if item.is_dir() and item.name.startswith("video_"):
            video_dirs.append(item)
    
    if not video_dirs:
        logger.error("未找到处理成功的视频目录")
        return
    
    logger.info(f"找到 {len(video_dirs)} 个处理成功的视频目录")
    
    # 创建最终输出目录
    final_output_dir = output_dir / f"output_{timestamp}"
    final_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 提取帧到最终输出目录
    rgb_dir = final_output_dir / "rgb"
    frame_count = extract_frames_from_videos(video_dirs, rgb_dir)
    
    if frame_count > 0:
        # 创建成功标记
        with open(final_output_dir / "success.txt", 'w') as f:
            f.write(f"处理成功: 提取了 {frame_count} 帧\n")
            f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            with open(prompt_path, 'r', encoding='utf-8') as p:
                prompt = p.read().strip()
                f.write(f"提示: {prompt}\n")
        
        logger.info(f"处理成功，结果保存在: {final_output_dir}")
    else:
        logger.error("未提取到任何帧")

if __name__ == "__main__":
    main() 