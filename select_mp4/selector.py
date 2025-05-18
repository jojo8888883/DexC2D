import cv2
import numpy as np
import os
import shutil
from pathlib import Path

# 全局配置
CONFIG = {
    "download_dir": str(Path.home() / "Downloads"),  # 使用用户下载文件夹
    "input_dir": "select_mp4/input_video",
    "output_dir": r"F:\24-25spring\DexC2D\static_videos",  # 使用绝对路径
    "threshold": 4.0,  # 光流阈值
    "sample_frames": 10  # 采样帧数
}

def import_latest_videos(count=4):
    """
    从下载文件夹导入最新的视频到input_video文件夹
    
    参数:
        count: 导入的最新视频数量
    """
    # 源文件夹和目标文件夹路径
    source_dir = CONFIG["download_dir"]
    target_dir = CONFIG["input_dir"]
    
    print(f"从 {source_dir} 导入最新的 {count} 个视频")
    
    # 确保目标文件夹存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # 获取下载文件夹中的所有视频文件
    video_files = []
    for file in os.listdir(source_dir):
        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            file_path = os.path.join(source_dir, file)
            video_files.append((file_path, os.path.getmtime(file_path)))
    
    if not video_files:
        print(f"在 {source_dir} 中没有找到视频文件")
        return 0
    
    # 按修改时间排序并获取最新的视频
    video_files.sort(key=lambda x: x[1], reverse=True)
    latest_videos = video_files[:count]
    
    # 复制视频文件到input_video文件夹
    copied_count = 0
    for video_path, _ in latest_videos:
        file_name = os.path.basename(video_path)
        target_path = os.path.join(target_dir, file_name)
        shutil.copy2(video_path, target_path)
        print(f"已复制: {file_name}")
        copied_count += 1
    
    print(f"共导入 {copied_count} 个视频文件")
    return copied_count

def clear_input_folder():
    """
    清空input_video文件夹
    返回: 删除的文件数量
    """
    input_dir = CONFIG["input_dir"]
    deleted_count = 0
    
    if os.path.exists(input_dir):
        for file in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                    deleted_count += 1
            except Exception as e:
                print(f"删除文件时出错: {e}")
        print(f"已清空 {input_dir} 文件夹，删除了 {deleted_count} 个文件")
    
    return deleted_count

def is_static_camera(video_path, threshold=None, sample_frames=None):
    """
    使用光流分析判断视频是否为固定镜头
    
    参数:
        video_path: 视频文件路径
        threshold: 光流幅度的阈值，低于此值视为固定镜头
        sample_frames: 采样的帧数
    
    返回:
        布尔值: True表示固定镜头，False表示非固定镜头
    """
    # 使用全局配置或参数
    threshold = threshold if threshold is not None else CONFIG["threshold"]
    sample_frames = sample_frames if sample_frames is not None else CONFIG["sample_frames"]
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"无法打开视频: {video_path}")
        return False
    
    # 获取视频信息
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"视频信息: {width}x{height}, {fps}fps, {frame_count}帧")
    
    # 如果帧数太少，无法进行光流分析
    if frame_count < 2:
        print("视频帧数太少，无法进行光流分析")
        cap.release()
        return False
    
    # 计算采样间隔
    step = max(1, frame_count // sample_frames)
    
    # 读取第一帧
    ret, prev_frame = cap.read()
    if not ret:
        print("无法读取第一帧")
        cap.release()
        return False
    
    # 转换为灰度图
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    
    total_flow = 0
    samples = 0
    
    # 计算光流
    for i in range(step, frame_count, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if not ret:
            break
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 计算光流
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        # 计算光流幅度
        magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        mean_magnitude = np.mean(magnitude)
        total_flow += mean_magnitude
        samples += 1
        
        prev_gray = gray
    
    cap.release()
    
    # 计算平均光流幅度
    if samples > 0:
        avg_flow = total_flow / samples
        print(f"平均光流幅度: {avg_flow}, 阈值: {threshold}")
        
        # 判断是否为固定镜头
        is_static = avg_flow < threshold
        print(f"判断结果: {'固定镜头' if is_static else '非固定镜头'}")
        return is_static
    else:
        print("无法计算光流")
        return False

def process_video(video_path, save_dir=None, delete_if_not_static=True):
    """
    处理视频：判断是否为固定镜头，然后保存或删除
    
    参数:
        video_path: 视频文件路径
        save_dir: 保存固定镜头视频的目录
        delete_if_not_static: 如果不是固定镜头是否删除
    """
    # 使用全局配置或参数
    save_dir = save_dir if save_dir is not None else CONFIG["output_dir"]
    
    # 确保保存目录存在
    os.makedirs(save_dir, exist_ok=True)
    
    # 判断是否为固定镜头
    is_static = is_static_camera(video_path)
    
    if is_static:
        # 是固定镜头，保存到指定目录
        filename = os.path.basename(video_path)
        save_path = os.path.join(save_dir, filename)
        
        # 如果目标文件与源文件不同，则复制
        if os.path.abspath(save_path) != os.path.abspath(video_path):
            print(f"固定镜头视频，保存到: {save_path}")
            shutil.copy2(video_path, save_path)
        else:
            print(f"视频已在目标位置: {save_path}")
        
        return True
    else:
        # 不是固定镜头
        if delete_if_not_static:
            print(f"非固定镜头视频，删除: {video_path}")
            try:
                os.remove(video_path)
            except Exception as e:
                print(f"删除文件时出错: {e}")
        else:
            print(f"非固定镜头视频: {video_path}")
        
        return False

def cleanup_input_folder(delete_folder=True):
    """
    清理输入文件夹
    
    参数:
        delete_folder: 如果为True，删除整个文件夹；如果为False，只删除文件
    """
    input_dir = CONFIG["input_dir"]
    
    if not os.path.exists(input_dir):
        return
    
    if delete_folder:
        try:
            shutil.rmtree(input_dir)
            print(f"已删除输入文件夹: {input_dir}")
        except Exception as e:
            print(f"删除输入文件夹时出错: {e}")
            # 如果删除文件夹失败，尝试删除文件
            clear_input_folder()
    else:
        clear_input_folder()

def main(clear_first=True, import_videos=True, video_count=4):
    """
    主函数
    
    参数:
        clear_first: 是否先清空输入文件夹
        import_videos: 是否从下载文件夹导入视频
        video_count: 导入的视频数量
    """
    print("=== 启动固定镜头视频分析器 ===")
    print(f"配置信息:")
    print(f"- 输入目录: {CONFIG['input_dir']}")
    print(f"- 输出目录: {CONFIG['output_dir']}")
    print(f"- 光流阈值: {CONFIG['threshold']}")
    print(f"- 下载目录: {CONFIG['download_dir']}")
    
    # 确保输入目录存在
    if not os.path.exists(CONFIG["input_dir"]):
        print(f"创建输入目录: {CONFIG['input_dir']}")
        os.makedirs(CONFIG["input_dir"])
    
    # 是否清空输入文件夹
    if clear_first:
        clear_input_folder()
    
    # 是否导入最新视频
    if import_videos:
        import_latest_videos(count=video_count)

    # 获取输入目录中所有mp4文件
    input_dir = CONFIG["input_dir"]
    mp4_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.mp4')]
    
    if not mp4_files:
        print(f"在 {input_dir} 目录中没有找到mp4文件")
        # 清理输入文件夹
        cleanup_input_folder(True)
        return
    
    print(f"找到 {len(mp4_files)} 个mp4文件")
    
    # 处理每个mp4文件
    processed_count = 0
    static_count = 0
    
    for mp4_file in mp4_files:
        video_path = os.path.join(input_dir, mp4_file)
        print(f"\n处理视频: {mp4_file}")
        
        if process_video(video_path, CONFIG["output_dir"], delete_if_not_static=True):
            static_count += 1
        
        processed_count += 1
    
    print(f"\n=== 处理完成 ===")
    print(f"总共处理: {processed_count} 个视频")
    print(f"固定镜头: {static_count} 个")
    print(f"非固定镜头: {processed_count - static_count} 个")
    
    # 清理输入文件夹
    print("\n清理临时文件...")
    cleanup_input_folder(True)

if __name__ == "__main__":
    main(clear_first=True, import_videos=True, video_count=4)
