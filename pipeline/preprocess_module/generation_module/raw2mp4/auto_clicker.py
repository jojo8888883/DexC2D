import pyautogui
import time
import platform
if platform.system() == "Windows":
    import pygetwindow as gw          # 仍兼容 Windows
else:
    import pywinctl as gw             # Linux / macOS 走 PyWinCtl

import logging
import pyperclip
from typing import Tuple, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutoClicker:
    def __init__(self):
        pyautogui.FAILSAFE = True     # 鼠标移到左上角可中断
        pyautogui.PAUSE = 0.5         # 每步操作之间的间隔

    # ---------------- 新增方法 ----------------
    def press_ctrl_l(self) -> bool:
        """按下 Ctrl+L（常用于聚焦地址栏 / 路径栏）"""
        try:
            pyautogui.hotkey('ctrl', 'l')
            logger.info("已按下 Ctrl+L")
            return True
        except Exception as e:
            logger.error(f"按 Ctrl+L 失败：{e}")
            return False
    # -----------------------------------------

    def get_window_position(self, window_title: str) -> Optional[Tuple[int, int, int, int]]:
        try:
            window = gw.getWindowsWithTitle(window_title)[0]
            return (window.left, window.top, window.width, window.height)
        except IndexError:
            logger.error(f"未找到标题为 '{window_title}' 的窗口")
            return None

    def click_button(self, x: int, y: int, button: str = 'left') -> bool:
        try:
            pyautogui.moveTo(x, y, duration=0.5)
            pyautogui.click(button=button)
            logger.info(f"成功点击位置：({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"点击失败：{e}")
            return False

    def paste_text(self, text: str) -> bool:
        try:
            pyperclip.copy(text)
            pyautogui.hotkey('ctrl', 'v')
            logger.info(f"成功粘贴文本：{text}")
            return True
        except Exception as e:
            logger.error(f"粘贴文本失败：{e}")
            return False

    def wait_for_image(self, image_path: str, timeout: int = 30, confidence: float = 0.8) -> Optional[Tuple[int, int, int, int]]:
        start_time = time.time()
        logger.info(f"开始等待图像：{image_path}")
        while time.time() - start_time < timeout:
            try:
                location = pyautogui.locateOnScreen(image_path, confidence=confidence)
                if location:
                    logger.info(f"找到图像，位置：{location}")
                    return location
            except Exception as e:
                logger.error(f"图像检测失败：{e}")
            time.sleep(1)
        logger.warning(f"等待超时，未找到图像：{image_path}")
        return None

    def monitor_download(self, download_image_path: str, button_offset: Tuple[int, int] = (50, 30)) -> bool:
        location = self.wait_for_image(download_image_path)
        if location:
            button_x = location.left + button_offset[0]
            button_y = location.top + button_offset[1]
            return self.click_button(button_x, button_y)
        return False

    def press_enter(self):
        pyautogui.press('enter')

    def press_shift(self):
        pyautogui.press('shift')

def main():
    auto_clicker = AutoClicker()
    time.sleep(2)

    # 示例：点击按钮
    auto_clicker.click_button(300, 400)

    # 示例：输入文本
    auto_clicker.paste_text("Hello, this is a test!")

    # 示例：按 Ctrl+L（重点演示）
    auto_clicker.press_ctrl_l()

    # 示例：监控下载完成弹窗
    if auto_clicker.monitor_download("download_complete_popup.png"):
        logger.info("成功处理下载完成弹窗")
    else:
        logger.error("处理下载完成弹窗失败")

if __name__ == "__main__":
    main()

