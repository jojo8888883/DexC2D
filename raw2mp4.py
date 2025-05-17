import time
from auto_clicker import AutoClicker
import webbrowser
import os
import psutil
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def open_chrome():
    chrome_path = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    chrome_path_x86 = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    if os.path.exists(chrome_path):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    elif os.path.exists(chrome_path_x86):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path_x86))
    else:
        logger.error("未找到 Chrome 浏览器，请确保已安装 Chrome")
        return False
    try:
        webbrowser.get('chrome').open('https://www.google.com')
        logger.info("Chrome 浏览器已成功打开")
        return True
    except Exception as e:
        logger.error(f"打开 Chrome 时出错: {str(e)}")
        return False

def open_sora_page():
    try:
        webbrowser.get('chrome').open('https://sora.chatgpt.com/explore')
        logger.info("已打开 Sora 探索页面")
    except Exception as e:
        logger.error(f"打开 Sora 页面时出错: {str(e)}")

def close_chrome():
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                proc.kill()
        logger.info("Chrome 浏览器已成功关闭")
    except Exception as e:
        logger.error(f"关闭 Chrome 时出错: {str(e)}")

def auto_sora_workflow():
    # 打开浏览器
    if not open_chrome():
        return
    time.sleep(2)
    # 打开 Sora 页面
    open_sora_page()
    time.sleep(5)
    # 自动化操作
    auto_clicker = AutoClicker()
    logger.info("自动点击 Sora 页面某个位置（请根据实际坐标修改）...")
    auto_clicker.click_button(1478, 1920)  # 示例坐标
    time.sleep(2)
    # 关闭浏览器
    close_chrome()

def main():
    logger.info("开始自动化流程")
    auto_sora_workflow()
    logger.info("流程结束")

if __name__ == "__main__":
    main() 
