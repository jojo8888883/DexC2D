import cv2
import subprocess
import shlex
import logging
import os
from pathlib import Path
import time
import shutil

logger = logging.getLogger('pipeline')

def extract_frames_opencv(video_path, output_dir, start_frame=0, end_frame=None, step=1, quality=95, target_fps=30):
    """
    使用OpenCV从视频中提取帧
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        start_frame: 起始帧索引
        end_frame: 结束帧索引，如果为None则提取到最后
        step: 帧采样步长
        quality: 输出图像质量（1-100）
        target_fps: 目标帧率，如果视频帧率不同，会进行调整
        
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
    duration = total_frames / fps if fps > 0 else 0
    
    logger.info(f"视频信息 - 帧数: {total_frames}, 帧率: {fps}, 时长: {duration:.2f}秒")
    
    # 确保视频有5秒长（30fps x 5秒 = 150帧）
    target_frames = int(target_fps * 5)
    
    # 如果视频帧率不是30fps，需要调整采样步长
    if abs(fps - target_fps) > 1.0 and fps > 0:
        step = fps / target_fps
        logger.info(f"视频帧率不是{target_fps}fps，调整采样步长为: {step:.2f}")
    
    # 确定结束帧
    if end_frame is None or end_frame > total_frames:
        end_frame = total_frames
    
    logger.info(f"开始提取帧，视频: {video_path}, 总帧数: {total_frames}, FPS: {fps}")
    logger.info(f"提取范围: {start_frame} 到 {end_frame}, 步长: {step}")
    
    # 设置起始位置
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    count = 0
    frame_idx = start_frame
    extracted_frames = []
    
    # 估计需要提取的帧数
    expected_frames = min(int((end_frame - start_frame) / step) + 1, target_frames)
    logger.info(f"预计提取 {expected_frames} 帧")
    
    while frame_idx < end_frame and count < target_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        if step > 1:
            # 如果步长大于1，需要跳过一些帧
            if frame_idx % step < 1.0:
            # 保存帧
                output_path = output_dir / f"{count:05d}.png"
                cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                extracted_frames.append(output_path)
                count += 1
        else:
            # 正常提取每一帧
            output_path = output_dir / f"{count:05d}.png"
            cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            extracted_frames.append(output_path)
            count += 1
        
        # 更新帧索引
        if step > 1:
            # 如果步长大于1，直接跳过一些帧
            next_frame = frame_idx + 1
            if next_frame < end_frame:
                cap.set(cv2.CAP_PROP_POS_FRAMES, next_frame)
            frame_idx = next_frame
        else:
            frame_idx += 1
    
    # 释放视频
    cap.release()
    
    logger.info(f"已提取 {count} 帧到 {output_dir}")
    
    # 如果提取的帧数不足150帧（5秒×30fps），使用最后一帧补足
    if count < target_frames and extracted_frames:
        last_frame_path = extracted_frames[-1]
        last_frame = cv2.imread(str(last_frame_path))
        
        for i in range(count, target_frames):
            output_path = output_dir / f"{i:05d}.png"
            cv2.imwrite(str(output_path), last_frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
            count += 1
        
        logger.info(f"用最后一帧补充到总计 {count} 帧")
    
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

def video_to_frames(video_path, output_dir, use_ffmpeg=True, quality=2, target_fps=30):
    """
    将视频转换为帧序列
    
    Args:
        video_path: 视频文件路径
        output_dir: 输出目录
        use_ffmpeg: 是否使用FFmpeg（否则使用OpenCV）
        quality: 输出质量
        target_fps: 目标帧率，确保输出是30Hz
        
    Returns:
        是否成功转换
    """
    start_time = time.time()
    success = False
    
    # 创建输出目录
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 清理输出目录中的现有文件
    for f in output_dir.glob("frame_*.png"):
        f.unlink()
    
    # 目标帧数：5秒 × 30fps = 150帧
    target_frames = 150
    
    # 先尝试使用指定的方法
    if use_ffmpeg:
        try:
            # 使用FFmpeg提取帧
            cmd = f'ffmpeg -i "{video_path}" -vf "fps={target_fps}" -qscale:v {quality} "{output_dir}/temp_%06d.png" -y'
            
            logger.info(f"使用FFmpeg提取帧，命令: {cmd}")
            
            process = subprocess.run(
                shlex.split(cmd),
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                check=True,
                text=True
            )
            
            if process.returncode == 0:
                # 重命名帧为正确的格式
                temp_frames = sorted(output_dir.glob("temp_*.png"))
                frame_count = len(temp_frames)
                
                if frame_count > 0:
                    # 如果帧数不足150，复制最后一帧
                    if frame_count < target_frames:
                        last_frame = temp_frames[-1]
                        for i in range(frame_count, target_frames):
                            new_frame = output_dir / f"temp_{i+1:06d}.png"
                            shutil.copy2(last_frame, new_frame)
                            temp_frames.append(new_frame)
                    
                    # 重命名前150帧
                    for i, frame in enumerate(temp_frames[:target_frames]):
                        new_name = output_dir / f"frame_{i:06d}.png"
                        frame.rename(new_name)
                    
                    # 删除多余的帧
                    for frame in temp_frames[target_frames:]:
                        if frame.exists():
                            frame.unlink()
                    
                    success = True
                    logger.info(f"FFmpeg成功提取并重命名了 {target_frames} 帧")
            
        except Exception as e:
            logger.error(f"使用FFmpeg提取帧时出错: {str(e)}，将尝试使用OpenCV")
            # 清理可能存在的临时文件
            for f in output_dir.glob("temp_*.png"):
                f.unlink()
    
    # 如果FFmpeg失败或未使用FFmpeg，使用OpenCV
    if not success:
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                return False
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 计算采样步长
            if abs(fps - target_fps) > 1.0 and fps > 0:
                step = fps / target_fps
                logger.info(f"调整采样步长: {step:.2f} (原始fps: {fps}, 目标fps: {target_fps})")
            else:
                step = 1.0
            
            frame_idx = 0.0
            count = 0
            last_frame = None
            
            while count < target_frames:
                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_idx))
                ret, frame = cap.read()
                
                if ret:
                    last_frame = frame.copy()
                    output_path = output_dir / f"frame_{count:06d}.png"
                    cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                    count += 1
                elif last_frame is not None:
                    # 使用最后一帧填充
                    output_path = output_dir / f"frame_{count:06d}.png"
                    cv2.imwrite(str(output_path), last_frame, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                    count += 1
                else:
                    break
                
                frame_idx += step
            
            cap.release()
            success = count == target_frames
            
            if success:
                logger.info(f"OpenCV成功提取了 {count} 帧")
            else:
                logger.error(f"OpenCV只提取到 {count} 帧，期望 {target_frames} 帧")
        
        except Exception as e:
            logger.error(f"使用OpenCV提取帧时出错: {str(e)}")
            return False
    
    # 最终检查
    frames = list(output_dir.glob("frame_*.png"))
    frame_count = len(frames)
    
    if frame_count != target_frames:
        logger.error(f"最终帧数 ({frame_count}) 不等于目标帧数 ({target_frames})")
        return False
    
    elapsed = time.time() - start_time
    logger.info(f"帧提取完成，耗时: {elapsed:.2f}秒")
    
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