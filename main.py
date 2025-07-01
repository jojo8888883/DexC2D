"""
DexC2D主程序
"""

import os
import logging
import time
from pathlib import Path

from pipeline.logger_module.logger import get_logger
from pipeline.config.capture_module_variant import CaptureModuleConfig
from pipeline.config.generation_module_variant import GenerationModuleConfig
from pipeline.config.selection_module_variant import SelectionModuleConfig
from pipeline.config.arrange_module_variant import ArrangeModuleConfig
from pipeline.preprocess_module.capture_module.capture_temp import CaptureTemp
from pipeline.preprocess_module.generation_module.sora_web_automation.sora_web_automation import SoraWebAutomation
from pipeline.preprocess_module.selection_module.selector import select_static_videos
from pipeline.preprocess_module.arrange_module.mp4_to_data import MP4ToData

# 获取日志记录器
logger = get_logger("Main")

class Pipeline:
    """DexC2D处理流水线"""
    
    def __init__(self):
        """初始化流水线"""
        # 初始化各个模块的配置
        self.capture_config = CaptureModuleConfig()
        self.generation_config = GenerationModuleConfig()
        self.selection_config = SelectionModuleConfig()
        self.arrange_config = ArrangeModuleConfig()
        
    def run_full_pipeline(self, capture_new: bool = True) -> bool:
        """
        运行完整的处理流水线
        
        Args:
            capture_new: 是否捕获新图像
            
        Returns:
            bool: 是否成功完成
        """
        logger.info("开始执行DexC2D流水线")
        
        # 步骤1: 捕获图像
        if capture_new:
            capture_result = self.run_capture_step()
            if not capture_result["success"]:
                logger.error("捕获图像失败，流水线终止")
                return False
            
            capture_dir = capture_result["temp_dir"]
        else:
            # 使用已有的临时捕获目录
            capture_dir = self.capture_config.get_temp_capture_dir()
            logger.info(f"跳过捕获步骤，使用已有的捕获图像: {capture_dir}")
        
        # 步骤2: 生成视频
        generation_result = self.run_generation_step(capture_dir)
        if not generation_result["success"]:
            logger.error("生成视频失败，流水线终止")
            return False
        
        # 步骤3: 选择静态视频
        selection_result = self.run_selection_step()
        if not selection_result["success"]:
            logger.error("选择静态视频失败，流水线终止")
            return False
        
        # 步骤4: 处理视频数据
        arrangement_result = self.run_arrangement_step()
        if not arrangement_result["success"]:
            logger.error("处理视频数据失败，流水线终止")
            return False
        
        logger.info("DexC2D流水线执行完成")
        return True
        
    def run_capture_step(self) -> dict:
        """
        运行捕获步骤
        
        Returns:
            dict: 包含捕获结果的字典
        """
        logger.info("开始执行捕获步骤")
        
        capture_temp = CaptureTemp(self.capture_config)
        capture_result = capture_temp.capture_single_frame()
        
        if capture_result["success"]:
            logger.info("捕获步骤完成")
        else:
            logger.error("捕获步骤失败")
            
        return capture_result
        
    def run_generation_step(self, capture_dir: str) -> dict:
        """
        运行生成步骤
        
        Args:
            capture_dir: 捕获图像目录
            
        Returns:
            dict: 包含生成结果的字典
        """
        logger.info("开始执行生成步骤")
        
        sora_automation = SoraWebAutomation(
            gen_config=self.generation_config,
            capture_dir=capture_dir
        )
        
        generation_result = sora_automation.run()
        
        if generation_result["success"]:
            logger.info("生成步骤完成")
        else:
            logger.error("生成步骤失败")
            
        return generation_result
        
    def run_selection_step(self) -> dict:
        """
        运行选择步骤
        
        Returns:
            dict: 包含选择结果的字典
        """
        logger.info("开始执行选择步骤")
        
        selection_result = select_static_videos(
            config=self.selection_config,
            clear_first=False,  # 不清空输入目录，使用生成步骤下载的视频
            import_videos=True,
            video_count=4
        )
        
        if selection_result["success"]:
            logger.info("选择步骤完成")
        else:
            logger.error("选择步骤失败")
            
        return selection_result
        
    def run_arrangement_step(self) -> dict:
        """
        运行排列步骤
        
        Returns:
            dict: 包含排列结果的字典
        """
        logger.info("开始执行排列步骤")
        
        mp4_to_data = MP4ToData(
            arrange_config=self.arrange_config,
            capture_config=self.capture_config
        )
        
        object_name = self.capture_config.get_object_name()
        viewpoint = self.capture_config.get_viewpoint()
        
        success, need_retry = mp4_to_data.process_videos(
            object_name=object_name,
            viewpoint=viewpoint
        )
        
        result = {
            "success": success,
            "need_retry": need_retry
        }
        
        if success:
            logger.info("排列步骤完成")
        else:
            if need_retry:
                logger.warning("排列步骤需要重试")
            else:
                logger.error("排列步骤失败")
            
        return result
        
    def retry_pipeline(self, max_retries: int = 3) -> bool:
        """
        尝试执行流水线，如果失败则重试
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            bool: 是否最终成功
        """
        retry_count = 0
        capture_new = True  # 第一次执行时捕获新图像
        
        while retry_count < max_retries:
            if retry_count > 0:
                logger.info(f"重试流水线执行 ({retry_count}/{max_retries})")
                time.sleep(2)  # 等待一段时间后重试
            
            success = self.run_full_pipeline(capture_new)
            
            if success:
                return True
                
            retry_count += 1
            capture_new = False  # 重试时不再捕获新图像
        
        logger.error(f"流水线执行失败，已重试 {max_retries} 次")
        return False

def main():
    """主函数"""
    logger.info("DexC2D程序启动")
    
    pipeline = Pipeline()
    success = pipeline.retry_pipeline(max_retries=3)
    
    if success:
        logger.info("DexC2D程序执行成功")
        return 0
    else:
        logger.error("DexC2D程序执行失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

