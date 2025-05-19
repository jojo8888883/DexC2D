import pyautogui
import time
import pygetwindow as gw
import logging
from typing import Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoClicker:
    def __init__(self):
        # 设置 PyAutoGUI 的安全特性
        pyautogui.FAILSAFE = True  # 将鼠标移动到屏幕左上角可以中断程序
        pyautogui.PAUSE = 0.5  # 每个操作之间的延迟时间
        
    def get_window_position(self, window_title: str) -> Optional[Tuple[int, int, int, int]]:
        """获取指定窗口的位置和大小"""
        try:
            window = gw.getWindowsWithTitle(window_title)[0]
            return (window.left, window.top, window.width, window.height)
        except IndexError:
            logger.error(f"未找到标题为 '{window_title}' 的窗口")
            return None
            
    def click_button(self, x: int, y: int, button: str = 'left') -> bool:
        """模拟鼠标点击"""
        try:
            pyautogui.moveTo(x, y, duration=0.5)
            pyautogui.click(button=button)
            logger.info(f"成功点击位置：({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"点击失败：{str(e)}")
            return False
            
    def paste_text(self, text: str) -> bool:
        """模拟粘贴文本"""
        try:
            pyautogui.write(text)
            logger.info(f"成功输入文本：{text}")
            return True
        except Exception as e:
            logger.error(f"输入文本失败：{str(e)}")
            return False
            
    def wait_for_image(self, image_path: str, timeout: int = 30, confidence: float = 0.8) -> Optional[Tuple[int, int, int, int]]:
        """等待并检测指定图像出现"""
        start_time = time.time()
        logger.info(f"开始等待图像：{image_path}")
        
        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location:
                    logger.info(f"找到图像，位置：{location}")
                    return location
            except Exception as e:
                logger.error(f"图像检测失败：{str(e)}")
            time.sleep(1)
            
        logger.warning(f"等待超时，未找到图像：{image_path}")
        return None
        
    def monitor_download(self, download_image_path: str, button_offset: Tuple[int, int] = (50, 30)) -> bool:
        """监控下载完成弹窗并点击确认按钮"""
        location = self.wait_for_image(download_image_path)
        if location:
            # 计算按钮位置（相对于弹窗的偏移）
            button_x = location.left + button_offset[0]
            button_y = location.top + button_offset[1]
            return self.click_button(button_x, button_y)
        return False
    
    def press_enter(self):
        pyautogui.press('enter')

    def press_shift(self):
        pyautogui.press('shift')

def main():
    # 创建自动点击器实例
    auto_clicker = AutoClicker()
    
    # 示例：等待 2 秒后开始操作
    time.sleep(2)
    
    # 示例：点击按钮
    auto_clicker.click_button(300, 400)
    
    # 示例：输入文本
    auto_clicker.paste_text("Hello, this is a test!")
    
    # 示例：监控下载完成弹窗
    download_image_path = "download_complete_popup.png"
    if auto_clicker.monitor_download(download_image_path):
        logger.info("成功处理下载完成弹窗")
    else:
        logger.error("处理下载完成弹窗失败")

if __name__ == "__main__":
    main() 