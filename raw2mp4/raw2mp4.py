"""
分辨率：3840*2160
网页缩放比例：80%
"""
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

def read_prompt_file(file_path="raw2mp4\prompt.txt"):
    """读取prompt文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        logger.info(f"成功读取prompt文件：{file_path}")
        return content
    except Exception as e:
        logger.error(f"读取prompt文件时出错: {str(e)}")
        return "a beautiful tomato soup can"  # 默认提示词

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
    time.sleep(6)
    # 自动化操作
    auto_clicker = AutoClicker()
    logger.info("自动点击 Sora 页面添加图像的加号...")
    auto_clicker.click_button(1478, 1920)  # 示例坐标
    time.sleep(2)
    logger.info("自动点击 从本地添加图像...")
    auto_clicker.click_button(1633, 1820)

    time.sleep(2)
    logger.info("自动点击 文件路径...")
    auto_clicker.click_button(1052, 97)
    time.sleep(2)
    logger.info("输入文件路径...")
    auto_clicker.paste_text(r"F:\24-25spring\DEXHGR\cap2raw\left_highest\tomato_soup_can")
    time.sleep(2)
    auto_clicker.press_enter()
    time.sleep(2)
    logger.info("自动点击 选择文件...")
    auto_clicker.click_button(460, 347)
    time.sleep(2)
    auto_clicker.press_enter()
    time.sleep(2)
    logger.info("自动点击 prompt输入框...")
    auto_clicker.click_button(1726, 1931)
    time.sleep(8)
    logger.info("读取prompt并输入...")
    prompt_text = read_prompt_file()
    auto_clicker.paste_text(prompt_text)
    time.sleep(2)
    logger.info("自动点击 回车...")
    auto_clicker.press_enter()
    time.sleep(2)
    logger.info("等待生成完毕...")
    # 等待图像出现，并根据返回结果决定后续操作
    image_result = auto_clicker.wait_for_image(r"raw2mp4\image.png", timeout=300, confidence=0.9)
    if image_result:
        logger.info("成功找到目标图像，继续执行正常流程...")
        time.sleep(2)
        logger.info("自动点击 查看四个视频...")
        auto_clicker.click_button(3549, 399)
        time.sleep(2)


        logger.info("自动点击 左上角视频...")
        auto_clicker.click_button(1317, 699)
        time.sleep(2)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
        logger.info("点右下角回到四个视频...")
        auto_clicker.click_button(3679, 2005)
        logger.info("自动点击 右上角视频...")
        auto_clicker.click_button(2511, 693)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
        logger.info("点右下角回到四个视频...")
        auto_clicker.click_button(3679, 2005)
        logger.info("自动点击 左下角视频...")
        auto_clicker.click_button(1466, 1467)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
        logger.info("点右下角回到四个视频...")
        auto_clicker.click_button(3679, 2005)
        logger.info("自动点击 右下角视频...")
        auto_clicker.click_button(2548, 1487)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
    else:
        logger.warning("等待超时，执行备选操作流程...")
        # 在这里添加超时后的备选操作
        time.sleep(2)
        logger.info("点击刷新按钮...")
        auto_clicker.click_button(195, 127)  # 假设这是刷新按钮的坐标
        time.sleep(2)
        logger.info("点击Activity按钮...")
        auto_clicker.click_button(3674, 307)
        logger.info("点击最新生成的视频集...")
        auto_clicker.click_button(3465, 417)
        time.sleep(2)
        

        logger.info("自动点击 左上角视频...")
        auto_clicker.click_button(1317, 699)
        time.sleep(2)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
        logger.info("点右下角回到四个视频...")
        auto_clicker.click_button(3679, 2005)
        logger.info("自动点击 右上角视频...")
        auto_clicker.click_button(2511, 693)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
        logger.info("点右下角回到四个视频...")
        auto_clicker.click_button(3679, 2005)
        logger.info("自动点击 左下角视频...")
        auto_clicker.click_button(1466, 1467)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
        logger.info("点右下角回到四个视频...")
        auto_clicker.click_button(3679, 2005)
        logger.info("自动点击 右下角视频...")
        auto_clicker.click_button(2548, 1487)
        logger.info("自动点击 下载...")
        auto_clicker.click_button(3542, 308)
        time.sleep(2)
        logger.info("自动点击 video(watermark)...")
        auto_clicker.click_button(3450, 482)
        time.sleep(10)
        logger.info("自动点击 download,等5s左右下载完毕...")
        auto_clicker.click_button(2040, 1266)
        time.sleep(5)
    # 关闭浏览器
    close_chrome()

def main():
    logger.info("开始自动化流程")
    auto_sora_workflow()
    logger.info("流程结束")

if __name__ == "__main__":
    main() 
