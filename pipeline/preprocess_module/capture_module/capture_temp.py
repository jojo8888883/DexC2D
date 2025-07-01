"""
临时捕获模块，实现临时捕获图像的功能
"""

import os
import shutil
from typing import Dict, Any, Optional

from pipeline.logger_module.logger import get_logger
from pipeline.device_module.camera.d435i import D435iCamera
from pipeline.config.capture_module_variant import CaptureModuleConfig
from pipeline.utils.common import ensure_directory

# 获取日志记录器
logger = get_logger("CaptureTemp")

class CaptureTemp:
    """临时捕获类"""
    
    def __init__(self, config: Optional[CaptureModuleConfig] = None):
        """
        初始化临时捕获
        
        Args:
            config: 捕获模块配置，如果为None则创建默认配置
        """
        self.config = config or CaptureModuleConfig()
        self.camera = D435iCamera()
        
    def capture_single_frame(self) -> Dict[str, Any]:
        """
        捕获单帧图像
        
        Returns:
            Dict: 包含捕获结果和路径的字典
        """
        # 获取临时捕获目录
        temp_dir = self.config.get_temp_capture_dir()
        ensure_directory(temp_dir)
        
        # 捕获图像
        result = self.camera.capture_frame()
        if not result["success"]:
            logger.error("捕获图像失败")
            return {"success": False}
        
        # 保存图像
        save_success = self.camera.save_frame(
            output_dir=temp_dir,
            color=result["color"],
            depth=result["depth"],
            cam_K=result["cam_K"]
        )
        
        if not save_success:
            logger.error("保存图像失败")
            return {"success": False}
        
        logger.info(f"临时捕获成功，保存到: {temp_dir}")
        
        return {
            "success": True,
            "temp_dir": temp_dir,
            "color_path": os.path.join(temp_dir, "color_000000.png"),
            "depth_path": os.path.join(temp_dir, "depth_000000.png"),
            "cam_K_path": os.path.join(temp_dir, "cam_K.txt")
        }
        
    def save_captured_frame(self) -> Dict[str, Any]:
        """
        将临时捕获的图像保存为永久图像
        
        Returns:
            Dict: 包含保存结果和路径的字典
        """
        # 获取目录路径
        temp_dir = self.config.get_temp_capture_dir()
        saved_dir = self.config.get_saved_capture_dir()
        
        # 检查临时目录是否存在
        if not os.path.exists(temp_dir):
            logger.error(f"临时捕获目录不存在: {temp_dir}")
            return {"success": False}
        
        # 检查是否有捕获的文件
        color_path = os.path.join(temp_dir, "color_000000.png")
        depth_path = os.path.join(temp_dir, "depth_000000.png")
        cam_K_path = os.path.join(temp_dir, "cam_K.txt")
        
        required_files = [color_path, depth_path, cam_K_path]
        for file_path in required_files:
            if not os.path.exists(file_path):
                logger.error(f"临时捕获文件不存在: {file_path}")
                return {"success": False}
        
        # 创建对象和视角特定的保存目录
        object_name = self.config.get_object_name()
        viewpoint = self.config.get_viewpoint()
        target_dir = os.path.join(saved_dir, object_name, viewpoint)
        ensure_directory(target_dir)
        
        # 复制文件
        try:
            for src_file in required_files:
                filename = os.path.basename(src_file)
                dst_file = os.path.join(target_dir, filename)
                shutil.copy2(src_file, dst_file)
                logger.info(f"已复制: {src_file} -> {dst_file}")
                
            logger.info(f"已将临时捕获保存到: {target_dir}")
            
            return {
                "success": True,
                "saved_dir": target_dir,
                "color_path": os.path.join(target_dir, "color_000000.png"),
                "depth_path": os.path.join(target_dir, "depth_000000.png"),
                "cam_K_path": os.path.join(target_dir, "cam_K.txt")
            }
        except Exception as e:
            logger.error(f"保存捕获文件失败: {e}")
            return {"success": False} 