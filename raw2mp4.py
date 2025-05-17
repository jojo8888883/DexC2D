<<<<<<< HEAD
"""
依赖：
    pip install playwright psutil requests
    playwright install
运行：
    python sora_playwright_b.py
"""

import subprocess, time, os, sys, psutil
from pathlib import Path
from playwright.sync_api import sync_playwright

# ---------- 1) 启动带远程调试端口的 Chrome ----------
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
]
URL  = "https://sora.chatgpt.com/explore"
PORT = 9222                                 # 端口随意，只要未被占用
CHROME_EXE = next((p for p in CHROME_PATHS if Path(p).exists()), None)

if not CHROME_EXE:
    sys.exit("❌ 未找到 Chrome，请检查安装路径")

# 检查端口是否被占用
def is_port_in_use(port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if is_port_in_use(PORT):
    print(f"⚠️ 端口 {PORT} 已被占用，尝试关闭占用进程...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    time.sleep(1)

# 添加更多启动参数以确保调试端口正确启动
cmd = [
    CHROME_EXE,
    f"--remote-debugging-port={PORT}",
    "--remote-allow-origins=*",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--disable-extensions",
    "--disable-popup-blocking",
    "--disable-infobars",
    "--new-window", URL
]

print("▶ 启动 Chrome ...")
chrome_proc = subprocess.Popen(cmd)

# 等待Chrome启动并确保调试端口可用
max_wait = 30  # 最多等待30秒
start_time = time.time()
while time.time() - start_time < max_wait:
    try:
        import requests
        response = requests.get(f"http://localhost:{PORT}/json/version")
        if response.status_code == 200:
            print("✅ Chrome调试端口已就绪")
            break
    except:
        time.sleep(1)
        continue
else:
    print("❌ Chrome调试端口启动超时")
    chrome_proc.kill()
    sys.exit(1)

# ---------- 2) 用 Playwright 连接到已开的 Chrome ----------
print("▶ Playwright 连接到现有 Chrome ...")
with sync_playwright() as p:
    try:
        # 连接到调试端口
        browser = p.chromium.connect_over_cdp(f"http://localhost:{PORT}")
        
        # 获取第一个context
        context = browser.contexts[0]
        
        # 等待页面加载完成
        page = next(tab for tab in context.pages if "sora.chatgpt.com/explore" in tab.url)
        print("✅ 已找到目标页面")
        
        # 等待页面完全加载
        print("▶ 等待页面完全加载...")
        page.wait_for_load_state("networkidle")
        time.sleep(5)  # 额外等待5秒确保页面完全渲染
        
        # ---------- 3) 等待并点击视频按钮 ----------
        print("▶ 开始查找视频按钮...")
        
        # 使用更精确的JavaScript点击方法
        print("▶ 尝试使用精确的JavaScript点击...")
        success = page.evaluate("""() => {
            // 1. 首先尝试通过精确的类名和文本内容查找
            const button = document.querySelector('button.inline-flex[role="combobox"]');
            if (button && button.textContent.includes('Video')) {
                button.click();
                return true;
            }
            
            // 2. 如果没找到，尝试通过aria属性查找
            const buttonByAria = document.querySelector('button[aria-controls="radix-:r4t:"]');
            if (buttonByAria) {
                buttonByAria.click();
                return true;
            }
            
            // 3. 最后尝试通过文本内容查找
            const buttons = Array.from(document.querySelectorAll('button'));
            const videoButton = buttons.find(btn => btn.textContent.includes('Video'));
            if (videoButton) {
                videoButton.click();
                return true;
            }
            
            return false;
        }""")
        
        if success:
            print("✅ JavaScript点击成功")
        else:
            print("❌ JavaScript点击失败，尝试使用选择器...")
            
            # 使用选择器尝试点击
            selectors = [
                "button.inline-flex[role='combobox']",  # 最精确的选择器
                "button[aria-controls='radix-:r4t:']",  # 通过aria属性
                "button:has(span:has-text('Video'))",   # 通过嵌套文本
                "button:has-text('Video')"              # 通过文本内容
            ]
            
            for selector in selectors:
                try:
                    print(f"▶ 尝试选择器: {selector}")
                    button = page.wait_for_selector(selector, timeout=5_000)
                    if button:
                        # 确保按钮可见
                        button.wait_for_element_state("visible", timeout=5_000)
                        
                        # 获取按钮位置并点击
                        box = button.bounding_box()
                        if box:
                            # 点击按钮中心
                            page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            print(f"✅ 已通过鼠标点击按钮 (使用选择器: {selector})")
                            break
                except Exception as e:
                    print(f"选择器 {selector} 失败: {str(e)}")
                    continue
        
        # 等待一段时间观察结果
        print("▶ 等待5秒观察点击结果...")
        time.sleep(5)
        
        # ---------- 4) 断开 Playwright（保留 Chrome 打开的状态） ----------
        browser.disconnect()
        print("▶ Playwright 已断开连接，Chrome 仍保持打开状态")
        
    except Exception as e:
        print(f"❌ 发生错误: {str(e)}")
        browser.disconnect()
        chrome_proc.kill()
        sys.exit(1)

# ---------- 5) （可选）脚本结束时关闭 Chrome ----------
# 如果你想保留浏览器就别关；要自动关闭可以取消下面注释

print("▶ 关闭 Chrome ...")
for proc in psutil.process_iter(["name", "pid"]):
    if proc.info["name"] and "chrome.exe" in proc.info["name"].lower():
        try:
            proc.kill()
        except Exception:
            pass
print("✅ Chrome 已关闭")

=======
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
>>>>>>> 682e07b
