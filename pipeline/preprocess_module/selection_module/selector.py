"""
视频选择器模块，实现选择静态视频的功能
"""

import os
import cv2
import numpy as np
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any

from pipeline.logger_module.logger import get_logger
from pipeline.config.selection_module_variant import SelectionModuleConfig
from pipeline.utils.common import ensure_directory

# 获取日志记录器
logger = get_logger("VideoSelector")

class VideoAnalyzer:
    """视频分析类"""
    
    def __init__(self, config: Optional[SelectionModuleConfig] = None):
        """
        初始化视频分析器
        
        Args:
            config: 选择模块配置，如果为None则创建默认配置
        """
        self.config = config or SelectionModuleConfig()
        
    def is_static_camera(self, video_path: str) -> bool:
        """
        使用光流分析判断视频是否为固定镜头
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            bool: 是否为固定镜头视频
        """
        threshold = self.config.get("threshold")
        sample_frames = self.config.get("sample_frames")
        
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频文件: {video_path}")
                return False
            
            # 获取视频基本信息
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if frame_count <= 1:
                logger.error(f"视频帧数太少: {video_path}")
                return False
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = frame_count / fps if fps > 0 else 0
            
            logger.info(f"视频信息: {os.path.basename(video_path)}, 帧数: {frame_count}, FPS: {fps:.2f}, 时长: {duration:.2f}秒")
            
            # 确定采样间隔
            if frame_count <= sample_frames:
                skip_frames = 0  # 不跳过任何帧
            else:
                skip_frames = max(1, frame_count // sample_frames - 1)
                
            # 读取第一帧
            ret, prev_frame = cap.read()
            if not ret:
                logger.error(f"无法读取第一帧: {video_path}")
                cap.release()
                return False
                
            # 转换为灰度图
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            
            # 计算光流的累积位移
            total_flow = 0
            processed_frames = 1
            
            frame_idx = 0
            while True:
                # 跳过指定数量的帧
                for _ in range(skip_frames):
                    cap.read()  # 读取但不处理
                    frame_idx += 1
                    if frame_idx >= frame_count - 1:
                        break
                        
                # 读取当前帧
                ret, frame = cap.read()
                if not ret:
                    break
                    
                frame_idx += 1
                processed_frames += 1
                
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
                
                # 更新上一帧
                prev_gray = gray
                
            cap.release()
            
            # 计算平均光流幅度
            avg_flow = total_flow / processed_frames if processed_frames > 0 else 0
            
            # 判断是否为固定镜头
            is_static = avg_flow < threshold
            
            logger.info(f"视频 {os.path.basename(video_path)} 的平均光流幅度: {avg_flow:.4f}, 阈值: {threshold}, 判定为: {'固定镜头' if is_static else '非固定镜头'}")
            
            return is_static
            
        except Exception as e:
            logger.error(f"分析视频时出错: {video_path}, 错误: {e}")
            return False

class FileManager:
    """文件操作管理类"""
    
    def __init__(self, config: Optional[SelectionModuleConfig] = None):
        """
        初始化文件管理器
        
        Args:
            config: 选择模块配置，如果为None则创建默认配置
        """
        self.config = config or SelectionModuleConfig()
        
    def import_latest_videos(self, count: int = 4) -> int:
        """
        从下载文件夹导入最新的视频到输入视频文件夹
        
        Args:
            count: 导入的最新视频数量
            
        Returns:
            int: 导入的视频数量
        """
        source_dir = self.config.get("download_dir")
        target_dir = self.config.get("input_dir")
        
        logger.info(f"从 {source_dir} 导入最新的 {count} 个视频")
        
        # 确保目标文件夹存在
        ensure_directory(target_dir)
        
        # 获取下载文件夹中的所有视频文件
        video_files = []
        if os.path.exists(source_dir):
            for file in os.listdir(source_dir):
                if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    file_path = os.path.join(source_dir, file)
                    video_files.append((file_path, os.path.getmtime(file_path)))
        
        if not video_files:
            logger.info(f"在 {source_dir} 中没有找到视频文件")
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
            logger.info(f"已复制: {file_name}")
            copied_count += 1
        
        logger.info(f"共导入 {copied_count} 个视频文件")
        return copied_count
    
    def clear_directory(self, directory: str) -> int:
        """
        清空指定目录
        
        Args:
            directory: 目录路径
            
        Returns:
            int: 删除的文件数量
        """
        deleted_count = 0
        
        if os.path.exists(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        deleted_count += 1
                except Exception as e:
                    logger.error(f"删除文件时出错: {file_path}, 错误: {e}")
            logger.info(f"已清空 {directory} 文件夹，删除了 {deleted_count} 个文件")
        
        return deleted_count
    
    def get_video_files(self, directory: str) -> List[str]:
        """
        获取指定目录中的所有视频文件
        
        Args:
            directory: 目录路径
            
        Returns:
            List[str]: 视频文件路径列表
        """
        if not os.path.exists(directory):
            return []
        
        return [
            os.path.join(directory, f) 
            for f in os.listdir(directory) 
            if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
        ]
    
    def save_static_video(self, video_path: str, output_dir: str) -> bool:
        """
        保存固定镜头视频到输出目录
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录路径
            
        Returns:
            bool: 是否保存成功
        """
        ensure_directory(output_dir)
        
        filename = os.path.basename(video_path)
        save_path = os.path.join(output_dir, filename)
        
        # 如果目标文件与源文件不同，则复制
        if os.path.abspath(save_path) != os.path.abspath(video_path):
            try:
                shutil.copy2(video_path, save_path)
                logger.info(f"固定镜头视频，保存到: {save_path}")
                return True
            except Exception as e:
                logger.error(f"保存视频失败: {video_path} -> {save_path}, 错误: {e}")
                return False
        else:
            logger.info(f"视频已在目标位置: {save_path}")
            return True
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"已删除文件: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件时出错: {file_path}, 错误: {e}")
            return False

class StaticCameraDetector:
    """静态相机检测器类，组合文件管理和视频分析功能"""
    
    def __init__(self, config: Optional[SelectionModuleConfig] = None):
        """
        初始化静态相机检测器
        
        Args:
            config: 选择模块配置，如果为None则创建默认配置
        """
        self.config = config or SelectionModuleConfig()
        self.file_manager = FileManager(self.config)
        self.video_analyzer = VideoAnalyzer(self.config)
        
    def process_video(self, video_path: str, delete_if_not_static: bool = True) -> bool:
        """
        处理单个视频，如果是固定镜头则保存
        
        Args:
            video_path: 视频文件路径
            delete_if_not_static: 如果不是固定镜头，是否删除原始文件
            
        Returns:
            bool: 是否为固定镜头视频
        """
        logger.info(f"处理视频: {os.path.basename(video_path)}")
        
        # 检查是否为固定镜头
        is_static = self.video_analyzer.is_static_camera(video_path)
        
        if is_static:
            # 保存到输出目录
            output_dir = self.config.get("output_dir")
            saved = self.file_manager.save_static_video(video_path, output_dir)
            if saved:
                logger.info(f"已保存固定镜头视频: {os.path.basename(video_path)}")
            else:
                logger.error(f"保存固定镜头视频失败: {os.path.basename(video_path)}")
                is_static = False
        elif delete_if_not_static:
            # 删除非固定镜头视频
            self.file_manager.delete_file(video_path)
            logger.info(f"已删除非固定镜头视频: {os.path.basename(video_path)}")
        
        return is_static
    
    def run(self, clear_first: bool = True, import_videos: bool = True, video_count: int = 4) -> Dict[str, Any]:
        """
        运行静态相机检测流程
        
        Args:
            clear_first: 是否先清空输入目录
            import_videos: 是否从下载目录导入视频
            video_count: 导入的视频数量
            
        Returns:
            Dict[str, Any]: 包含运行结果的字典
        """
        input_dir = self.config.get("input_dir")
        output_dir = self.config.get("output_dir")
        
        # 确保目录存在
        ensure_directory(input_dir)
        ensure_directory(output_dir)
        
        # 清空输入目录
        if clear_first:
            self.file_manager.clear_directory(input_dir)
        
        # 从下载目录导入最新视频
        if import_videos:
            self.file_manager.import_latest_videos(video_count)
        
        # 获取所有视频文件
        video_files = self.file_manager.get_video_files(input_dir)
        
        if not video_files:
            logger.warning(f"没有找到要处理的视频文件: {input_dir}")
            return {
                "success": False,
                "message": "没有找到要处理的视频文件",
                "static_videos": 0,
                "total_videos": 0
            }
        
        # 处理所有视频
        static_videos = []
        for video_path in video_files:
            is_static = self.process_video(video_path)
            if is_static:
                static_videos.append(video_path)
        
        # 返回结果
        result = {
            "success": len(static_videos) > 0,
            "static_videos": len(static_videos),
            "total_videos": len(video_files),
            "static_video_paths": static_videos,
            "output_dir": output_dir
        }
        
        if result["static_videos"] > 0:
            logger.info(f"从 {result['total_videos']} 个视频中找到了 {result['static_videos']} 个固定镜头视频")
        else:
            logger.warning(f"在 {result['total_videos']} 个视频中没有找到固定镜头视频")
        
        return result

# 对外暴露的主函数
def select_static_videos(config: Optional[SelectionModuleConfig] = None, 
                        clear_first: bool = True, 
                        import_videos: bool = True, 
                        video_count: int = 4) -> Dict[str, Any]:
    """
    选择静态视频的主函数
    
    Args:
        config: 选择模块配置
        clear_first: 是否先清空输入目录
        import_videos: 是否从下载目录导入视频
        video_count: 导入的视频数量
        
    Returns:
        Dict[str, Any]: 包含运行结果的字典
    """
    detector = StaticCameraDetector(config)
    return detector.run(clear_first, import_videos, video_count) 