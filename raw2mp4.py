import webbrowser
import os
import time
import psutil

def open_chrome():
    # Chrome 浏览器的默认安装路径
    chrome_path = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    chrome_path_x86 = 'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    
    # 检查 Chrome 是否安装在默认位置
    if os.path.exists(chrome_path):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path))
    elif os.path.exists(chrome_path_x86):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(chrome_path_x86))
    else:
        print("未找到 Chrome 浏览器，请确保已安装 Chrome")
        return

    try:
        # 使用 webbrowser 模块打开 Chrome
        webbrowser.get('chrome').open('https://www.google.com')
        print("Chrome 浏览器已成功打开")
    except Exception as e:
        print(f"打开 Chrome 时出错: {str(e)}")

def open_sora_page():
    try:
        # 打开 Sora 探索页面
        webbrowser.get('chrome').open('https://sora.chatgpt.com/explore')
        print("已打开 Sora 探索页面")
    except Exception as e:
        print(f"打开 Sora 页面时出错: {str(e)}")

def close_chrome():
    try:
        # 遍历所有进程
        for proc in psutil.process_iter(['name']):
            # 检查进程名称是否为 chrome.exe
            if proc.info['name'] and 'chrome.exe' in proc.info['name'].lower():
                # 终止进程
                proc.kill()
        print("Chrome 浏览器已成功关闭")
    except Exception as e:
        print(f"关闭 Chrome 时出错: {str(e)}")

if __name__ == "__main__":
    # 打开 Chrome
    open_chrome()
    
    # 等待 2 秒
    print("等待 2 秒...")
    time.sleep(2)
    
    # 打开 Sora 页面
    open_sora_page()
    
    # 等待 5 秒
    print("等待 5 秒...")
    time.sleep(5)
    
    # 关闭 Chrome
    close_chrome()
