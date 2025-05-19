import cv2
import numpy as np
import os
import shutil
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple, Union

# 全局配置实例
_config_instance = None

class Config:
    """配置管理类"""
    
    def __init__(self):
        self.settings: Dict[str, Union[str, float, int]] = {
            "download_dir": str(Path.home() / "Downloads"),  # 使用用户下载文件夹
            "input_dir": "select_mp4/input_video",
            "output_dir": r"F:\24-25spring\DexC2D\static_videos",  # 使用绝对路径
            "threshold": 4.0,  # 光流阈值
            "sample_frames": 10  # 采样帧数
        }
    
    def get(self, key: str) -> Union[str, float, int]:
        """获取配置项"""
        return self.settings[key]
    
    def set(self, key: str, value: Union[str, float, int]) -> None:
        """设置配置项"""
        self.settings[key] = value
    
    def display(self) -> None:
        """显示当前配置"""
        print("配置信息:")
        for key, value in self.settings.items():
            print(f"- {key}: {value}")

# 获取配置全局实例
def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

# 设置输出目录路径
def set_output_dir(directory: str) -> None:
    """设置视频输出目录路径"""
    config = get_config()
    config.set("output_dir", directory)
    logging.info(f"已设置视频输出目录: {directory}")

# 设置光流阈值
def set_threshold(value: float) -> None:
    """设置光流阈值"""
    config = get_config()
    config.set("threshold", value)
    logging.info(f"已设置光流阈值: {value}")


class FileManager:
    """文件操作管理类"""
    
    def __init__(self, config: Config):
        self.config = config
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """设置日志记录器"""
        self.logger = logging.getLogger("FileManager")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def import_latest_videos(self, count: int = 4) -> int:
        """
        从下载文件夹导入最新的视频到input_video文件夹
        
        参数:
            count: 导入的最新视频数量
        返回:
            导入的视频数量
        """
        source_dir = self.config.get("download_dir")
        target_dir = self.config.get("input_dir")
        
        self.logger.info(f"从 {source_dir} 导入最新的 {count} 个视频")
        
        # 确保目标文件夹存在
        os.makedirs(target_dir, exist_ok=True)
        
        # 获取下载文件夹中的所有视频文件
        video_files: List[Tuple[str, float]] = []
        for file in os.listdir(source_dir):
            if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                file_path = os.path.join(source_dir, file)
                video_files.append((file_path, os.path.getmtime(file_path)))
        
        if not video_files:
            self.logger.info(f"在 {source_dir} 中没有找到视频文件")
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
            self.logger.info(f"已复制: {file_name}")
            copied_count += 1
        
        self.logger.info(f"共导入 {copied_count} 个视频文件")
        return copied_count
    
    def clear_input_folder(self) -> int:
        """
        清空input_video文件夹
        返回: 删除的文件数量
        """
        input_dir = self.config.get("input_dir")
        deleted_count = 0
        
        if os.path.exists(input_dir):
            for file in os.listdir(input_dir):
                file_path = os.path.join(input_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        deleted_count += 1
                except Exception as e:
                    self.logger.error(f"删除文件时出错: {e}")
            self.logger.info(f"已清空 {input_dir} 文件夹，删除了 {deleted_count} 个文件")
        
        return deleted_count
    
    def cleanup_input_folder(self, delete_folder: bool = True) -> None:
        """
        清理输入文件夹
        
        参数:
            delete_folder: 如果为True，删除整个文件夹；如果为False，只删除文件
        """
        input_dir = self.config.get("input_dir")
        
        if not os.path.exists(input_dir):
            return
        
        if delete_folder:
            try:
                shutil.rmtree(input_dir)
                self.logger.info(f"已删除输入文件夹: {input_dir}")
            except Exception as e:
                self.logger.error(f"删除输入文件夹时出错: {e}")
                # 如果删除文件夹失败，尝试删除文件
                self.clear_input_folder()
        else:
            self.clear_input_folder()
    
    def get_video_files(self) -> List[str]:
        """
        获取输入目录中的所有视频文件
        
        返回:
            视频文件路径列表
        """
        input_dir = self.config.get("input_dir")
        if not os.path.exists(input_dir):
            return []
        
        return [
            os.path.join(input_dir, f) 
            for f in os.listdir(input_dir) 
            if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))
        ]
    
    def save_static_video(self, video_path: str) -> bool:
        """
        保存固定镜头视频到输出目录
        
        参数:
            video_path: 视频文件路径
            
        返回:
            是否保存成功
        """
        save_dir = self.config.get("output_dir")
        os.makedirs(save_dir, exist_ok=True)
        
        filename = os.path.basename(video_path)
        save_path = os.path.join(save_dir, filename)
        
        # 如果目标文件与源文件不同，则复制
        if os.path.abspath(save_path) != os.path.abspath(video_path):
            self.logger.info(f"固定镜头视频，保存到: {save_path}")
            shutil.copy2(video_path, save_path)
        else:
            self.logger.info(f"视频已在目标位置: {save_path}")
        
        return True
    
    def delete_file(self, file_path: str) -> bool:
        """
        删除文件
        
        参数:
            file_path: 文件路径
            
        返回:
            是否删除成功
        """
        try:
            os.remove(file_path)
            self.logger.info(f"已删除文件: {file_path}")
            return True
        except Exception as e:
            self.logger.error(f"删除文件时出错: {e}")
            return False


class VideoAnalyzer:
    """视频分析类"""
    
    def __init__(self, config: Config):
        self.config = config
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """设置日志记录器"""
        self.logger = logging.getLogger("VideoAnalyzer")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def is_static_camera(self, video_path: str, threshold: Optional[float] = None, sample_frames: Optional[int] = None) -> bool:
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
        threshold = threshold if threshold is not None else self.config.get("threshold")
        sample_frames = sample_frames if sample_frames is not None else self.config.get("sample_frames")
        
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.logger.error(f"无法打开视频: {video_path}")
            return False
        
        try:
            # 获取视频信息
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            self.logger.info(f"视频信息: {width}x{height}, {fps}fps, {frame_count}帧")
            
            # 如果帧数太少，无法进行光流分析
            if frame_count < 2:
                self.logger.warning("视频帧数太少，无法进行光流分析")
                return False
            
            # 计算采样间隔
            step = max(1, frame_count // sample_frames)
            
            # 读取第一帧
            ret, prev_frame = cap.read()
            if not ret:
                self.logger.error("无法读取第一帧")
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
            
            # 计算平均光流幅度
            if samples > 0:
                avg_flow = total_flow / samples
                self.logger.info(f"平均光流幅度: {avg_flow}, 阈值: {threshold}")
                
                # 判断是否为固定镜头
                is_static = avg_flow < threshold
                self.logger.info(f"判断结果: {'固定镜头' if is_static else '非固定镜头'}")
                return is_static
            else:
                self.logger.error("无法计算光流")
                return False
                
        finally:
            # 确保释放视频资源
            cap.release()


class StaticCameraDetector:
    """固定镜头检测主应用类"""
    
    def __init__(self):
        self.config = get_config()  # 使用全局配置实例
        self.file_manager = FileManager(self.config)
        self.video_analyzer = VideoAnalyzer(self.config)
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """设置日志记录器"""
        self.logger = logging.getLogger("StaticCameraDetector")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def process_video(self, video_path: str, delete_if_not_static: bool = True) -> bool:
        """
        处理视频：判断是否为固定镜头，然后保存或删除
        
        参数:
            video_path: 视频文件路径
            delete_if_not_static: 如果不是固定镜头是否删除
            
        返回:
            是否为固定镜头
        """
        self.logger.info(f"处理视频: {os.path.basename(video_path)}")
        
        # 判断是否为固定镜头
        is_static = self.video_analyzer.is_static_camera(video_path)
        
        if is_static:
            # 是固定镜头，保存到指定目录
            self.file_manager.save_static_video(video_path)
            return True
        else:
            # 不是固定镜头
            if delete_if_not_static:
                self.logger.info(f"非固定镜头视频，删除: {video_path}")
                self.file_manager.delete_file(video_path)
            else:
                self.logger.info(f"非固定镜头视频: {video_path}")
            
            return False
    
    def run(self, clear_first: bool = True, import_videos: bool = True, video_count: int = 4) -> None:
        """
        运行固定镜头检测流程
        
        参数:
            clear_first: 是否先清空输入文件夹
            import_videos: 是否从下载文件夹导入视频
            video_count: 导入的视频数量
        """
        self.logger.info("=== 启动固定镜头视频分析器 ===")
        self.config.display()
        
        # 确保输入目录存在
        input_dir = self.config.get("input_dir")
        os.makedirs(input_dir, exist_ok=True)
        
        # 是否清空输入文件夹
        if clear_first:
            self.file_manager.clear_input_folder()
        
        # 是否导入最新视频
        if import_videos:
            self.file_manager.import_latest_videos(count=video_count)
        
        # 获取所有视频文件
        video_files = self.file_manager.get_video_files()
        
        if not video_files:
            self.logger.info(f"在 {input_dir} 目录中没有找到视频文件")
            # 清理输入文件夹
            self.file_manager.cleanup_input_folder(True)
            return
        
        self.logger.info(f"找到 {len(video_files)} 个视频文件")
        
        # 处理每个视频文件
        processed_count = 0
        static_count = 0
        
        for video_path in video_files:
            self.logger.info(f"\n处理视频: {os.path.basename(video_path)}")
            
            if self.process_video(video_path, delete_if_not_static=True):
                static_count += 1
            
            processed_count += 1
        
        self.logger.info(f"\n=== 处理完成 ===")
        self.logger.info(f"总共处理: {processed_count} 个视频")
        self.logger.info(f"固定镜头: {static_count} 个")
        self.logger.info(f"非固定镜头: {processed_count - static_count} 个")
        
        # 清理输入文件夹
        self.logger.info("\n清理临时文件...")
        self.file_manager.cleanup_input_folder(True)


def main(clear_first: bool = True, import_videos: bool = True, video_count: int = 4) -> None:
    """
    主函数
    
    参数:
        clear_first: 是否先清空输入文件夹
        import_videos: 是否从下载文件夹导入视频
        video_count: 导入的视频数量
    """
    detector = StaticCameraDetector()
    detector.run(clear_first, import_videos, video_count)


if __name__ == "__main__":
    main(clear_first=True, import_videos=True, video_count=4)
