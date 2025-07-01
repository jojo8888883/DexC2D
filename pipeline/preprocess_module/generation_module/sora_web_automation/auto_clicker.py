"""
自动点击工具类，实现自动点击功能
"""

import time
import pyautogui
import pyperclip
import logging
from typing import Tuple, Optional, Any

from pipeline.logger_module.logger import get_logger

# 获取日志记录器
logger = get_logger("AutoClicker")

class AutoClicker:
    """自动点击工具类，封装自动操作功能"""
    
    def __init__(self):
        """初始化自动点击工具"""
        # 设置pyautogui安全措施
        pyautogui.PAUSE = 0.5  # 每个操作之间暂停0.5秒
        pyautogui.FAILSAFE = True  # 将鼠标移动到屏幕左上角将中断
        
    def click_button(self, x: int, y: int, clicks: int = 1, button: str = 'left') -> bool:
        """
        点击屏幕指定位置
        
        Args:
            x: 横坐标
            y: 纵坐标
            clicks: 点击次数
            button: 按钮类型 ('left', 'right', 'middle')
            
        Returns:
            bool: 是否点击成功
        """
        try:
            logger.info(f"点击位置: ({x}, {y}), 按钮: {button}, 次数: {clicks}")
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
            return True
        except Exception as e:
            logger.error(f"点击位置 ({x}, {y}) 失败: {e}")
            return False
    
    def paste_text(self, text: str) -> bool:
        """
        粘贴文本
        
        Args:
            text: 要粘贴的文本
            
        Returns:
            bool: 是否粘贴成功
        """
        try:
            # 使用pyperclip复制到剪贴板
            pyperclip.copy(text)
            # 使用Ctrl+V粘贴
            pyautogui.hotkey('ctrl', 'v')
            logger.info(f"已粘贴文本 (长度: {len(text)})")
            return True
        except Exception as e:
            logger.error(f"粘贴文本失败: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """
        按下键盘按键
        
        Args:
            key: 按键名称
            
        Returns:
            bool: 是否按键成功
        """
        try:
            logger.info(f"按下按键: {key}")
            pyautogui.press(key)
            return True
        except Exception as e:
            logger.error(f"按下按键 {key} 失败: {e}")
            return False
    
    def press_enter(self) -> bool:
        """
        按下回车键
        
        Returns:
            bool: 是否按键成功
        """
        return self.press_key('enter')
    
    def press_ctrl_l(self) -> bool:
        """
        按下Ctrl+L组合键（用于浏览器地址栏）
        
        Returns:
            bool: 是否按键成功
        """
        try:
            logger.info("按下组合键: Ctrl+L")
            pyautogui.hotkey('ctrl', 'l')
            return True
        except Exception as e:
            logger.error(f"按下组合键 Ctrl+L 失败: {e}")
            return False
    
    def wait_for_image(self, image_path: str, timeout: int = 60, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        等待屏幕上出现指定图像
        
        Args:
            image_path: 图像文件路径
            timeout: 超时时间（秒）
            confidence: 匹配置信度（0-1）
            
        Returns:
            Optional[Tuple[int, int]]: 如果找到图像，返回其中心坐标；否则返回None
        """
        logger.info(f"等待图像出现: {image_path}, 超时: {timeout}秒, 置信度: {confidence}")
        start_time = time.time()
        
        while True:
            # 检查是否超时
            if time.time() - start_time > timeout:
                logger.warning(f"等待图像超时: {image_path}")
                return None
                
            # 尝试在屏幕上定位图像
            try:
                location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
                if location:
                    x, y = location
                    logger.info(f"找到图像: {image_path}, 位置: ({x}, {y})")
                    return x, y
            except Exception as e:
                logger.error(f"查找图像 {image_path} 时出错: {e}")
                
            # 暂停后再次尝试
            time.sleep(1)
    
    def move_to(self, x: int, y: int, duration: float = 0.25) -> bool:
        """
        将鼠标移动到指定位置
        
        Args:
            x: 横坐标
            y: 纵坐标
            duration: 移动持续时间（秒）
            
        Returns:
            bool: 是否移动成功
        """
        try:
            logger.info(f"移动鼠标到: ({x}, {y})")
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            logger.error(f"移动鼠标到 ({x}, {y}) 失败: {e}")
            return False
    
    def scroll(self, clicks: int) -> bool:
        """
        滚动鼠标滚轮
        
        Args:
            clicks: 滚动的点击数（正数向上滚动，负数向下滚动）
            
        Returns:
            bool: 是否滚动成功
        """
        try:
            logger.info(f"滚动鼠标: {clicks} 次")
            pyautogui.scroll(clicks)
            return True
        except Exception as e:
            logger.error(f"滚动鼠标 {clicks} 次失败: {e}")
            return False 