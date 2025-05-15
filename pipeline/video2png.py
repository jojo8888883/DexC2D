import cv2
import subprocess
import shlex
import logging
import os
from pathlib import Path
import time

logger = logging.getLogger('pipeline')

def extract_frames_opencv(video_path, output_dir, start_frame=0, end_frame=None, step=1, quality=95):
    """
    使用OpenCV从视频中提取帧
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        start_frame: 起始帧索引
        end_frame: 结束帧索引，如果为None则提取到最后
        step: 帧采样步长
        quality: 输出图像质量（1-100）
        
    Returns:
        提取的帧数
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 打开视频
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        logger.error(f"无法打开视频: {video_path}")
        return 0
    
    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # 确定结束帧
    if end_frame is None or end_frame > total_frames:
        end_frame = total_frames
    
    logger.info(f"开始提取帧，视频: {video_path}, 总帧数: {total_frames}, FPS: {fps}")
    logger.info(f"提取范围: {start_frame} 到 {end_frame}, 步长: {step}")
    
    # 设置起始位置
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    count = 0
    frame_idx = start_frame
    
    while frame_idx < end_frame:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_idx % step == 0:
            # 保存帧
            output_path = output_dir / f"{count+1:05d}.png"
            cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            count += 1
        
        frame_idx += 1
    
    # 释放视频
    cap.release()
    
    logger.info(f"已提取 {count} 帧到 {output_dir}")
    return count

def extract_frames_ffmpeg(video_path, output_dir, quality=2):
    """
    使用FFmpeg从视频中提取帧
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        quality: 输出质量（1-31，越小质量越高）
        
    Returns:
        是否成功提取
    """
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 构建FFmpeg命令
    cmd = f'ffmpeg -i "{video_path}" -qscale:v {quality} "{output_dir}/%05d.png" -y'
    
    logger.info(f"开始提取帧，视频: {video_path}")
    logger.info(f"FFmpeg命令: {cmd}")
    
    try:
        # 执行命令
        process = subprocess.run(
            shlex.split(cmd),
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True,
            text=True
        )
        
        # 检查是否成功
        if process.returncode != 0:
            logger.error(f"FFmpeg提取失败: {process.stderr}")
            return False
        
        # 检查是否有输出文件
        frames = list(output_dir.glob("*.png"))
        logger.info(f"已提取 {len(frames)} 帧到 {output_dir}")
        
        return len(frames) > 0
        
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg执行失败: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"提取帧时出错: {str(e)}")
        return False

def video_to_frames(video_path, output_dir, use_ffmpeg=True, quality=2):
    """
    将视频转换为帧序列
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        use_ffmpeg: 是否使用FFmpeg（否则使用OpenCV）
        quality: 输出质量
        
    Returns:
        是否成功转换
    """
    start_time = time.time()
    success = False
    
    # 先尝试使用指定的方法
    if use_ffmpeg:
        try:
            success = extract_frames_ffmpeg(video_path, output_dir, quality)
            if success:
                logger.info(f"使用FFmpeg成功提取帧")
            else:
                logger.warning(f"使用FFmpeg提取帧失败，将尝试使用OpenCV")
                # 使用OpenCV作为备选方案
                success = extract_frames_opencv(video_path, output_dir, quality=quality) > 0
        except Exception as e:
            logger.error(f"使用FFmpeg提取帧时出错: {str(e)}，将尝试使用OpenCV")
            # 使用OpenCV作为备选方案
            success = extract_frames_opencv(video_path, output_dir, quality=quality) > 0
    else:
        # 直接使用OpenCV
        success = extract_frames_opencv(video_path, output_dir, quality=quality) > 0
    
    elapsed = time.time() - start_time
    
    if success:
        # 再次检查输出目录中是否有文件
        output_path = Path(output_dir)
        frames = list(output_path.glob("*.png"))
        if len(frames) == 0:
            logger.error(f"提取帧失败：没有生成任何PNG文件")
            success = False
    
    logger.info(f"帧提取{'成功' if success else '失败'}，耗时: {elapsed:.2f}秒")
    
    return success

if __name__ == "__main__":
    import sys
    from utils import setup_logging
    
    # 设置日志
    logger = setup_logging()
    
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("用法: python video2png.py <video_path> <output_dir> [use_ffmpeg=1] [quality=2]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_dir = sys.argv[2]
    use_ffmpeg = int(sys.argv[3]) == 1 if len(sys.argv) > 3 else True
    quality = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    
    # 转换视频
    success = video_to_frames(video_path, output_dir, use_ffmpeg, quality)
    
    if success:
        print(f"视频已成功转换为帧序列: {output_dir}")
    else:
        print(f"视频转换失败: {video_path}")
        sys.exit(1) 