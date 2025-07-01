"""
分辨率：3840*2160
网页缩放比例：80%
"""
import time
import os
import shutil 
import logging
import webbrowser
from raw2mp4.auto_clicker import AutoClicker

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 坐标配置常量
COORDINATES = {
    "add_image_button": (749, 1002),
    "local_image_button": (814, 945),
    # "file_select": (707, 233),
    "file_select":(642, 207),
    "prompt_input": (820, 1000),
    "view_all_videos": (1770, 193),
    "back_button": (1834, 1052),
    "download_button": (1751, 139),
    "watermark_option": (1700, 234),
    "confirm_download": (1068, 652),
    "refresh_button": (166, 93),
    "activity_button": (1843, 145),
    "latest_video_set": (1742, 204),
    "close_button": (3792, 30),
    "videos": {
        "top_left": (678, 365),
        "top_right": (1317, 353),
        "bottom_left": (688, 768),
        "bottom_right": (1311, 773)
    }
}

# 路径配置
COMPLETE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), "complete.png")
PROMPT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompt.txt")
INPUT_IMAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "capture")


def set_input_image_dir(directory):
    """设置输入图像目录路径"""
    global INPUT_IMAGE_DIR
    INPUT_IMAGE_DIR = directory
    logger.info(f"已设置输入图像目录：{directory}")
    return INPUT_IMAGE_DIR

def read_prompt_file(file_path=PROMPT_FILE_PATH):
    """读取prompt文件内容"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        logger.info(f"成功读取prompt文件：{file_path}")
        return content
    except Exception as e:
        logger.error(f"读取prompt文件时出错: {str(e)}")
        return False

def open_firefox():
    """在 Ubuntu 20.04 上打开（默认安装的）Firefox 浏览器"""
    
    # 1️⃣ 自动查找 firefox 可执行文件
    firefox_path = shutil.which('firefox')   # /usr/bin/firefox 或 /snap/bin/firefox
    
    if firefox_path is None or not os.path.exists(firefox_path):
        logger.error("未找到 Firefox，请确认已安装。")
        return False

    # 2️⃣ 向 webbrowser 模块登记
    webbrowser.register('firefox', None, webbrowser.BackgroundBrowser(firefox_path))
    
    # 3️⃣ 打开网页
    try:
        webbrowser.get('firefox').open('https://www.google.com')
        logger.info("Firefox 浏览器已成功打开")
        return True
    except Exception as e:
        logger.error(f"打开 Firefox 时出错: {e}")
        return False

def open_sora_page():
    """在已有的 Firefox 会话中打开 Sora 探索页面"""
    try:
        webbrowser.get('firefox').open_new_tab(
            'https://sora.chatgpt.com/explore'
        )
        logger.info("Sora 探索页面已在 Firefox 中打开")
        return True
    except webbrowser.Error as e:
        logger.error(f"打开 Sora 页面失败：{e}")
        return False

        
def close_firefox():
    """关闭 Firefox 浏览器"""
    try:
        # 点击窗口右上角的关闭按钮
        auto_clicker = AutoClicker()
        auto_clicker.click_button(*COORDINATES["close_button"])
        time.sleep(2)

        logger.info("Firefox 浏览器已成功关闭")
        return True
    except Exception as e:
        logger.error(f"关闭 Firefox 时出错: {e}")
        return False        

def download_video(auto_clicker, position_name):
    """下载单个视频的通用流程"""
    logger.info(f"开始下载{position_name}视频...")
    
    # 点击选择视频
    video_pos = COORDINATES["videos"][position_name]
    auto_clicker.click_button(*video_pos)
    time.sleep(2)
    
    # 点击下载按钮
    auto_clicker.click_button(*COORDINATES["download_button"])
    time.sleep(2)
    
    # 选择带水印的选项
    auto_clicker.click_button(*COORDINATES["watermark_option"])
    time.sleep(10)
    
    # 确认下载
    auto_clicker.click_button(*COORDINATES["confirm_download"])
    time.sleep(5)
    
    # 返回视频选择页面
    auto_clicker.click_button(*COORDINATES["back_button"])
    time.sleep(2)
    
    logger.info(f"{position_name}视频下载完成")

def upload_image_and_prompt(auto_clicker):
    """上传图片和prompt"""
    logger.info("上传图片和prompt...")
    
    # 点击添加图像按钮
    auto_clicker.click_button(*COORDINATES["add_image_button"])
    time.sleep(2)
    
    # 选择从本地添加图像
    auto_clicker.click_button(*COORDINATES["local_image_button"])
    time.sleep(2)
    
    # 输入文件路径
    auto_clicker.press_ctrl_l()
    time.sleep(2)
    auto_clicker.paste_text(INPUT_IMAGE_DIR)
    time.sleep(2)
    auto_clicker.press_enter()
    time.sleep(1)
    
    # 选择文件
    auto_clicker.click_button(*COORDINATES["file_select"])
    time.sleep(2)
    auto_clicker.press_enter()
    time.sleep(10)
    
    # 输入prompt
    auto_clicker.click_button(*COORDINATES["prompt_input"])
    time.sleep(5)
    prompt_text = read_prompt_file()
    auto_clicker.paste_text(prompt_text)
    time.sleep(2)
    auto_clicker.press_enter()
    time.sleep(2)

    logger.info("图片和prompt上传完成")

def download_all_videos(auto_clicker, normal_flow=True):
    """下载所有视频"""
    logger.info("开始下载所有视频...")
    
    if normal_flow:
        # 正常流程 - 点击查看所有视频
        auto_clicker.click_button(*COORDINATES["view_all_videos"])
    else:
        # 备选流程 - 通过Activity按钮查看视频
        auto_clicker.click_button(*COORDINATES["refresh_button"])
        time.sleep(2)
        auto_clicker.click_button(*COORDINATES["activity_button"])
        time.sleep(2)
        auto_clicker.click_button(*COORDINATES["latest_video_set"])
    
    time.sleep(2)
    
    # 依次下载四个视频
    for position in ["top_left", "top_right", "bottom_left", "bottom_right"]:
        download_video(auto_clicker, position)
    
    logger.info("所有视频下载完成")

def auto_sora_workflow():
    """Sora自动化工作流程"""
    # 打开浏览器
    if not open_firefox():
        logger.error("无法启动Firefox浏览器，流程终止")
        return False
    
    time.sleep(2)
    
    # 打开Sora页面
    if not open_sora_page():
        logger.error("无法打开Sora页面，流程终止")
        close_firefox()
        return False
    
    time.sleep(10)
    
    # 初始化自动点击器
    auto_clicker = AutoClicker()
    
    # 上传图片和prompt
    upload_image_and_prompt(auto_clicker)
    
    # 等待生成结果
    logger.info("等待生成完毕...")
    image_path = COMPLETE_IMAGE_PATH
    image_result = auto_clicker.wait_for_image(image_path, timeout=600, confidence=0.9)
    
    # 根据生成结果执行相应流程
    if image_result:
        logger.info("成功找到目标图像，执行正常下载流程")
        download_all_videos(auto_clicker, normal_flow=True)
    else:
        logger.warning("等待超时，执行备选下载流程")
        download_all_videos(auto_clicker, normal_flow=False)
    
    # 关闭浏览器
    close_firefox()
    return True

def main():
    """主函数"""
    logger.info("开始自动化流程")
    try:
        success = auto_sora_workflow()
        if success:
            logger.info("流程成功完成")
        else:
            logger.warning("流程未完全成功")
    except Exception as e:
        logger.error(f"流程执行出错: {str(e)}")
    finally:
        logger.info("流程结束")

if __name__ == "__main__":
    main() 
