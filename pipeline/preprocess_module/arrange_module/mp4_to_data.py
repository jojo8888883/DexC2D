"""
MP4到数据转换模块，实现将MP4视频转换为数据集的功能
"""

import os
import re
import sys
import shutil
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union, Set

import cv2

from pipeline.logger_module.logger import get_logger
from pipeline.config.arrange_module_variant import ArrangeModuleConfig
from pipeline.config.capture_module_variant import CaptureModuleConfig
from pipeline.utils.common import ensure_directory, read_text_file, write_text_file, get_next_index

# 获取日志记录器
logger = get_logger("MP4ToData")

class MP4ToData:
    """MP4视频转换为数据集的类"""
    
    def __init__(self, 
                 arrange_config: Optional[ArrangeModuleConfig] = None,
                 capture_config: Optional[CaptureModuleConfig] = None):
        """
        初始化MP4到数据转换器
        
        Args:
            arrange_config: 排列模块配置，如果为None则创建默认配置
            capture_config: 捕获模块配置，如果为None则创建默认配置
        """
        self.arrange_config = arrange_config or ArrangeModuleConfig()
        self.capture_config = capture_config or CaptureModuleConfig()
        
    def process_videos(self, 
                       object_name: str,
                       viewpoint: str,
                       capture_dir: Optional[str] = None,
                       exts: Optional[List[str]] = None) -> Tuple[bool, bool]:
        """
        处理视频并转换为数据集
        
        Args:
            object_name: 物体名称
            viewpoint: 视角名称
            capture_dir: 捕获目录，如果为None则使用配置的默认路径
            exts: 视频扩展名列表，如果为None则默认为[".mp4"]
            
        Returns:
            Tuple[bool, bool]: (是否全部成功，是否需要重试)
        """
        # 设置默认值
        exts = exts or [".mp4"]
        
        # 获取配置路径
        videos_dir = Path(self.arrange_config.get_static_videos_dir())
        dataset_root = Path(self.arrange_config.get_dataset_root())
        gen_datas_dir = Path(self.arrange_config.get_gen_datas_dir())
        models_dir = Path(self.arrange_config.get_models_dir())
        meta_info_path = Path(self.arrange_config.get_meta_info_path())
        remove_src = self.arrange_config.get_remove_source_videos()
        
        # 使用提供的捕获目录或默认目录
        if capture_dir:
            capture_dir_path = Path(capture_dir)
        else:
            # 使用保存的捕获目录
            capture_dir_path = Path(os.path.join(
                self.capture_config.get_saved_capture_dir(),
                object_name,
                viewpoint
            ))
        
        # 检查视频目录是否存在
        if not videos_dir.exists():
            logger.error(f"视频目录 {videos_dir} 不存在")
            return False, True
        
        # 收集全部待处理文件
        videos: List[Path] = [
            p for ext in exts for p in videos_dir.rglob(f"*{ext}")
        ]
        
        if not videos:
            logger.warning("未找到任何视频文件")
            return False, True
        
        # 创建输出目录
        ensure_directory(str(gen_datas_dir))
        ensure_directory(str(models_dir))
        
        # 读取或创建元信息文件
        existing_meta: Set[str] = set()
        if meta_info_path.exists():
            content = read_text_file(str(meta_info_path))
            if content:
                existing_meta = set(content.splitlines())
        
        new_meta: List[str] = []
        
        # 处理所有视频
        all_success = True
        prefix = f"{object_name}_{viewpoint}"
        next_idx = get_next_index(str(gen_datas_dir), prefix)
        
        for video_path in videos:
            target_dir_name = f"{prefix}_{next_idx:03d}"
            next_idx += 1
            target_dir = gen_datas_dir / target_dir_name
            rgb_dir = target_dir / "rgb"
            
            try:
                # 创建目录
                ensure_directory(str(rgb_dir))
                
                # 读取视频
                cap = cv2.VideoCapture(str(video_path))
                if not cap.isOpened():
                    raise RuntimeError(f"VideoCapture 打开失败: {video_path}")
                
                # 读取并保存所有帧
                frame_idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 保存帧
                    frame_path = rgb_dir / f"frame_{frame_idx:06d}.png"
                    ok = cv2.imwrite(str(frame_path), frame)
                    if not ok:
                        raise RuntimeError(f"cv2.imwrite 写入失败（frame {frame_idx}）")
                    
                    frame_idx += 1
                
                cap.release()
                
                if frame_idx == 0:
                    raise RuntimeError("视频为空或帧提取失败")
                
                # 复制辅助文件
                for fname in ["cam_K.txt", "depth_000000.png"]:
                    src = capture_dir_path / fname
                    if src.exists():
                        dst = target_dir / fname
                        shutil.copy2(src, dst)
                        logger.info(f"已复制: {src} -> {dst}")
                    else:
                        logger.warning(f"辅助文件不存在: {src}")
                
                # 写 cad.info
                cad_info_path = target_dir / "cad.info"
                write_text_file(
                    str(cad_info_path),
                    f"{dataset_root}/models/{object_name}"
                )
                
                # 添加到元信息
                rel_path = f"gen_dataset/gen_datas/{target_dir_name}"
                new_meta.append(rel_path)
                logger.info(f"已处理 {video_path.name} -> {target_dir}")
                
                # 如果配置为删除源文件，则删除
                if remove_src:
                    try:
                        video_path.unlink(missing_ok=True)
                        logger.info(f"已删除源视频: {video_path}")
                    except Exception as e:
                        logger.error(f"删除源视频失败: {video_path}, 错误: {e}")
                
            except Exception as e:
                all_success = False
                logger.error(f"处理 {video_path} 失败: {e}")
                traceback.print_exc(file=sys.stdout)
                
                # 清理半成品目录
                if target_dir.exists():
                    try:
                        shutil.rmtree(target_dir, ignore_errors=True)
                        logger.info(f"已清理失败的目录: {target_dir}")
                    except Exception as e:
                        logger.error(f"清理目录失败: {target_dir}, 错误: {e}")
        
        # 更新元信息文件（去重）
        merged = sorted(existing_meta.union(new_meta))
        write_text_file(str(meta_info_path), "\n".join(merged) + ("\n" if merged else ""))
        
        # 计算结果
        need_retry = not all_success
        
        return all_success, need_retry
        
    def process_single_video(self, 
                           video_path: str,
                           object_name: str,
                           viewpoint: str,
                           capture_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        处理单个视频并转换为数据集
        
        Args:
            video_path: 视频文件路径
            object_name: 物体名称
            viewpoint: 视角名称
            capture_dir: 捕获目录，如果为None则使用配置的默认路径
            
        Returns:
            Dict[str, Any]: 包含处理结果的字典
        """
        # 构建视频路径为Path对象
        video = Path(video_path)
        if not video.exists():
            return {
                "success": False,
                "message": f"视频文件不存在: {video_path}"
            }
        
        # 处理单个视频
        all_success, _ = self.process_videos(
            object_name=object_name,
            viewpoint=viewpoint,
            capture_dir=capture_dir,
            exts=[video.suffix]
        )
        
        if all_success:
            return {
                "success": True,
                "message": f"成功处理视频: {video.name}"
            }
        else:
            return {
                "success": False,
                "message": f"处理视频失败: {video.name}"
            } 