"""
Sora网页自动化类，实现自动化生成视频的功能
"""

import os
import time
import shutil
import webbrowser
from typing import Dict, List, Optional, Any, Tuple

from pipeline.logger_module.logger import get_logger
from pipeline.preprocess_module.generation_module.sora_web_automation.auto_clicker import AutoClicker
from pipeline.config.generation_module_variant import GenerationModuleConfig
from pipeline.config.input_module_variant import InputModuleConfig
from pipeline.utils.common import ensure_directory, read_text_file

# 获取日志记录器
logger = get_logger("SoraWebAutomation")

class SoraWebAutomation:
    """Sora网页自动化类"""
    
    def __init__(self, 
                 gen_config: Optional[GenerationModuleConfig] = None,
                 input_config: Optional[InputModuleConfig] = None,
                 capture_dir: Optional[str] = None):
        """
        初始化Sora网页自动化
        
        Args:
            gen_config: 生成模块配置，如果为None则创建默认配置
            input_config: 输入模块配置，如果为None则创建默认配置
            capture_dir: 捕获图像目录，如果为None则使用配置中的默认路径
        """
        self.gen_config = gen_config or GenerationModuleConfig()
        self.input_config = input_config or InputModuleConfig()
        self.capture_dir = capture_dir
        self.auto_clicker = AutoClicker()
        
        # 获取坐标配置
        self.coordinates = self.gen_config.get_coordinates()
        
        # 获取下载目录
        self.downloaded_videos_dir = self.gen_config.get_downloaded_videos_dir()
        ensure_directory(self.downloaded_videos_dir)
        
        # 获取完成图片路径
        self.complete_image_path = self.gen_config.get_complete_image_path()
        
        # 获取prompt文件路径
        self.prompt_file_path = self.input_config.get_prompt_file_path()
        
    def read_prompt_file(self) -> str:
        """
        读取prompt文件内容
        
        Returns:
            str: prompt内容
        """
        content = read_text_file(self.prompt_file_path)
        if content is None:
            logger.error(f"读取prompt文件失败: {self.prompt_file_path}")
            return ""
            
        logger.info(f"成功读取prompt文件: {self.prompt_file_path}")
        return content.strip()
        
    def open_firefox(self) -> bool:
        """
        在Ubuntu上打开Firefox浏览器
        
        Returns:
            bool: 是否成功打开
        """
        try:
            # 查找firefox可执行文件
            firefox_path = shutil.which('firefox')
            
            if firefox_path is None or not os.path.exists(firefox_path):
                logger.error("未找到Firefox，请确认已安装。")
                return False
                
            # 向webbrowser模块登记
            webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))
            
            # 打开网页
            webbrowser.get('firefox').open('https://www.google.com')
            logger.info("Firefox浏览器已成功打开")
            
            # 给浏览器一些时间启动
            time.sleep(3)
            
            return True
        except Exception as e:
            logger.error(f"打开Firefox时出错: {e}")
            return False
            
    def open_sora_page(self) -> bool:
        """
        在已有的Firefox会话中打开Sora探索页面
        
        Returns:
            bool: 是否成功打开
        """
        try:
            webbrowser.get('firefox').open_new_tab(
                'https://sora.chatgpt.com/explore'
            )
            logger.info("Sora探索页面已在Firefox中打开")
            
            # 给页面一些时间加载
            time.sleep(10)
            
            return True
        except Exception as e:
            logger.error(f"打开Sora页面失败: {e}")
            return False
            
    def close_firefox(self) -> bool:
        """
        关闭Firefox浏览器
        
        Returns:
            bool: 是否成功关闭
        """
        try:
            # 点击窗口右上角的关闭按钮
            self.auto_clicker.click_button(*self.coordinates["close_button"])
            time.sleep(2)
            
            logger.info("Firefox浏览器已成功关闭")
            return True
        except Exception as e:
            logger.error(f"关闭Firefox时出错: {e}")
            return False
            
    def upload_image_and_prompt(self) -> bool:
        """
        上传图片和prompt
        
        Returns:
            bool: 是否成功上传
        """
        logger.info("上传图片和prompt...")
        
        try:
            # 点击添加图像按钮
            self.auto_clicker.click_button(*self.coordinates["add_image_button"])
            time.sleep(2)
            
            # 选择从本地添加图像
            self.auto_clicker.click_button(*self.coordinates["local_image_button"])
            time.sleep(2)
            
            # 输入文件路径
            self.auto_clicker.press_ctrl_l()
            time.sleep(2)
            
            # 使用提供的捕获目录或默认目录
            input_dir = self.capture_dir if self.capture_dir else "assets/raw_datas/temp"
            self.auto_clicker.paste_text(input_dir)
            time.sleep(2)
            self.auto_clicker.press_enter()
            time.sleep(1)
            
            # 选择文件
            self.auto_clicker.click_button(*self.coordinates["file_select"])
            time.sleep(2)
            self.auto_clicker.press_enter()
            time.sleep(10)
            
            # 输入prompt
            self.auto_clicker.click_button(*self.coordinates["prompt_input"])
            time.sleep(5)
            prompt_text = self.read_prompt_file()
            
            if not prompt_text:
                logger.error("prompt文本为空")
                return False
                
            self.auto_clicker.paste_text(prompt_text)
            time.sleep(2)
            self.auto_clicker.press_enter()
            time.sleep(2)
            
            logger.info("图片和prompt上传完成")
            return True
        except Exception as e:
            logger.error(f"上传图片和prompt失败: {e}")
            return False
            
    def download_video(self, position_name: str) -> bool:
        """
        下载单个视频
        
        Args:
            position_name: 位置名称（"top_left", "top_right", "bottom_left", "bottom_right"）
            
        Returns:
            bool: 是否成功下载
        """
        logger.info(f"开始下载{position_name}视频...")
        
        try:
            # 点击选择视频
            video_pos = self.coordinates["videos"][position_name]
            self.auto_clicker.click_button(*video_pos)
            time.sleep(2)
            
            # 点击下载按钮
            self.auto_clicker.click_button(*self.coordinates["download_button"])
            time.sleep(2)
            
            # 选择带水印的选项
            self.auto_clicker.click_button(*self.coordinates["watermark_option"])
            time.sleep(10)
            
            # 确认下载
            self.auto_clicker.click_button(*self.coordinates["confirm_download"])
            time.sleep(5)
            
            # 返回视频选择页面
            self.auto_clicker.click_button(*self.coordinates["back_button"])
            time.sleep(2)
            
            logger.info(f"{position_name}视频下载完成")
            return True
        except Exception as e:
            logger.error(f"下载{position_name}视频失败: {e}")
            return False
            
    def download_all_videos(self, normal_flow: bool = True) -> bool:
        """
        下载所有视频
        
        Args:
            normal_flow: 是否使用正常流程，False则使用备选流程
            
        Returns:
            bool: 是否成功下载所有视频
        """
        logger.info("开始下载所有视频...")
        
        try:
            if normal_flow:
                # 正常流程 - 点击查看所有视频
                self.auto_clicker.click_button(*self.coordinates["view_all_videos"])
            else:
                # 备选流程 - 通过Activity按钮查看视频
                self.auto_clicker.click_button(*self.coordinates["refresh_button"])
                time.sleep(2)
                self.auto_clicker.click_button(*self.coordinates["activity_button"])
                time.sleep(2)
                self.auto_clicker.click_button(*self.coordinates["latest_video_set"])
            
            time.sleep(2)
            
            # 依次下载四个视频
            positions = ["top_left", "top_right", "bottom_left", "bottom_right"]
            success = True
            
            for position in positions:
                if not self.download_video(position):
                    success = False
            
            logger.info("所有视频下载完成" if success else "部分视频下载失败")
            return success
        except Exception as e:
            logger.error(f"下载所有视频失败: {e}")
            return False
            
    def auto_sora_workflow(self) -> bool:
        """
        Sora自动化工作流程
        
        Returns:
            bool: 是否成功完成整个流程
        """
        # 打开浏览器
        if not self.open_firefox():
            logger.error("无法启动Firefox浏览器，流程终止")
            return False
        
        time.sleep(2)
        
        # 打开Sora页面
        if not self.open_sora_page():
            logger.error("无法打开Sora页面，流程终止")
            self.close_firefox()
            return False
        
        time.sleep(10)
        
        # 上传图片和prompt
        if not self.upload_image_and_prompt():
            logger.error("上传图片和prompt失败，流程终止")
            self.close_firefox()
            return False
        
        # 等待生成结果
        logger.info("等待生成完毕...")
        image_result = self.auto_clicker.wait_for_image(
            self.complete_image_path, 
            timeout=600,  # 10分钟超时
            confidence=0.9
        )
        
        # 根据生成结果执行相应流程
        download_success = False
        if image_result:
            logger.info("成功找到目标图像，执行正常下载流程")
            download_success = self.download_all_videos(normal_flow=True)
        else:
            logger.warning("等待超时，执行备选下载流程")
            download_success = self.download_all_videos(normal_flow=False)
        
        # 关闭浏览器
        self.close_firefox()
        
        return download_success
        
    def run(self) -> Dict[str, Any]:
        """
        运行Sora自动化流程
        
        Returns:
            Dict: 包含运行结果和下载视频路径的字典
        """
        logger.info("开始Sora自动化流程")
        
        try:
            success = self.auto_sora_workflow()
            
            if success:
                logger.info("Sora自动化流程成功完成")
                return {
                    "success": True,
                    "downloaded_dir": self.downloaded_videos_dir
                }
            else:
                logger.error("Sora自动化流程失败")
                return {
                    "success": False,
                    "downloaded_dir": self.downloaded_videos_dir
                }
        except Exception as e:
            logger.error(f"Sora自动化流程出错: {e}")
            return {
                "success": False,
                "error": str(e)
            } 