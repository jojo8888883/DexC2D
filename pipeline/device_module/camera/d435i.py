"""
D435i相机设备模块，封装Intel RealSense D435i相机的操作
"""

import numpy as np
import pyrealsense2 as rs
import cv2
from PIL import Image
import os
from typing import Tuple, Dict, Optional, Any

from pipeline.logger_module.logger import get_logger

# 获取日志记录器
logger = get_logger("D435iCamera")

class D435iCamera:
    """Intel RealSense D435i相机操作类"""
    
    def __init__(self, 
                 left_trim: int = 100,
                 color_size: Tuple[int, int] = (1080, 720),
                 depth_size: Tuple[int, int] = (720, 480)):
        """
        初始化D435i相机
        
        Args:
            left_trim: 裁剪左边的像素数
            color_size: 彩色图像尺寸 (width, height)
            depth_size: 深度图像尺寸 (width, height)
        """
        self.left_trim = left_trim
        self.right_trim = 1280 - left_trim
        self.color_size = color_size
        self.depth_size = depth_size
        self.scale_fac = depth_size[0] / color_size[0]  # 缩放因子
        
        self.pipeline = None
        self.config = None
        self.profile = None
        
    def _initialize(self) -> bool:
        """初始化相机配置"""
        try:
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
            self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
            self.profile = self.pipeline.start(self.config)
            logger.info("相机初始化成功")
            return True
        except Exception as e:
            logger.error(f"相机初始化失败: {e}")
            return False
            
    def _stop(self) -> None:
        """停止相机"""
        if self.pipeline:
            self.pipeline.stop()
            logger.info("相机已停止")
            
    def capture_frame(self) -> Dict[str, Any]:
        """
        捕获一帧图像
        
        Returns:
            Dict: 包含彩色图像、深度图像和相机内参的字典
        """
        result = {"success": False, "color": None, "depth": None, "cam_K": None}
        
        if not self._initialize():
            return result
            
        try:
            # 自动曝光缓冲
            for _ in range(30):
                self.pipeline.wait_for_frames()
                
            # 对齐帧
            align = rs.align(rs.stream.color)
            frames = align.process(self.pipeline.wait_for_frames())
            color_frame = frames.first(rs.stream.color)
            depth_frame = frames.first(rs.stream.depth)
            
            # 转换为numpy数组
            color_np = np.asanyarray(color_frame.get_data())          # (720,1280,3) uint8
            depth_np = np.asanyarray(depth_frame.get_data())          # (720,1280)   uint16
            
            # 中心裁剪 → 3:2
            color_crop = color_np[:, self.left_trim:self.right_trim, :]         # (720,1080,3)
            depth_crop = depth_np[:, self.left_trim:self.right_trim]            # (720,1080)
            
            # 深度下采样
            depth_down = cv2.resize(
                depth_crop,
                self.depth_size,                     # (w, h)
                interpolation=cv2.INTER_NEAREST
            )                                       # (480,720)
            
            # 更新内参
            intr = color_frame.profile.as_video_stream_profile().get_intrinsics()
            fx, fy = intr.fx, intr.fy
            ppx, ppy = intr.ppx - self.left_trim, intr.ppy          # 主点先平移
            fx_d, fy_d = fx * self.scale_fac, fy * self.scale_fac    # 然后缩放
            ppx_d, ppy_d = ppx * self.scale_fac, ppy * self.scale_fac
            
            cam_K_depth = [                                   # ← 3×3 矩阵
                fx_d, 0.0,  ppx_d,
                0.0,  fy_d, ppy_d,
                0.0,  0.0,  1.0
            ]
            
            result = {
                "success": True,
                "color": color_crop,
                "depth": depth_down,
                "cam_K": cam_K_depth
            }
            
            logger.info("成功捕获一帧图像")
            return result
        except Exception as e:
            logger.error(f"捕获图像失败: {e}")
            return result
        finally:
            self._stop()
            
    def save_frame(self, output_dir: str, 
                  color: Optional[np.ndarray] = None,
                  depth: Optional[np.ndarray] = None,
                  cam_K: Optional[list] = None) -> bool:
        """
        保存捕获的帧
        
        Args:
            output_dir: 输出目录
            color: 彩色图像数据，如果为None则会捕获一帧
            depth: 深度图像数据，如果为None则会捕获一帧
            cam_K: 相机内参，如果为None则会捕获一帧
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 如果没有提供图像数据，则捕获一帧
            if color is None or depth is None or cam_K is None:
                result = self.capture_frame()
                if not result["success"]:
                    return False
                color = result["color"]
                depth = result["depth"]
                cam_K = result["cam_K"]
            
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 保存路径
            color_path = os.path.join(output_dir, "color_000000.png")
            depth_path = os.path.join(output_dir, "depth_000000.png")
            cam_K_txt_path = os.path.join(output_dir, "cam_K.txt")
            
            # 保存彩色图像
            Image.fromarray(color).save(color_path)
            
            # 保存深度图像
            Image.fromarray(depth, mode='I;16').save(depth_path)
            
            # 保存相机内参
            self._save_cam_K_txt(cam_K, cam_K_txt_path)
            
            logger.info(f"已保存图像到 {output_dir}")
            logger.info(f"[Saved] RGB   → {color_path}  ({self.color_size[0]}×{self.color_size[1]})")
            logger.info(f"[Saved] Depth → {depth_path} ({self.depth_size[0]}×{self.depth_size[1]}, 16-bit)")
            logger.info(f"[Saved] K_txt → {cam_K_txt_path}")
            
            return True
        except Exception as e:
            logger.error(f"保存图像失败: {e}")
            return False
            
    def _save_cam_K_txt(self, cam_K: list, output_path: str) -> None:
        """
        将相机内参矩阵保存为指定格式的txt文件
        
        Args:
            cam_K: 相机内参矩阵（3x3）
            output_path: 输出文件路径
        """
        with open(output_path, 'w') as f:
            for i in range(3):
                row = cam_K[i*3:(i+1)*3]
                # 使用科学计数法格式化数字，保持20位精度
                formatted_row = [f"{x:.20e}" for x in row]
                # 添加行号（从1开始）
                f.write(f"{i+1} {' '.join(formatted_row)}\n") 