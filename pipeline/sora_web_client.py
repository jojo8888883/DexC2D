import os
import time
import json
import logging
import shutil
from pathlib import Path
import pyautogui
import cv2
import numpy as np
import yaml
import webbrowser
import requests
import subprocess
import platform

from rule_filter import filter_video
from video2png import video_to_frames

logger = logging.getLogger('pipeline')

class SoraWebClient:
    """Sora Web界面自动化客户端 - 使用PyAutoGUI控制本地Chrome浏览器"""
    
    def __init__(self, config_path="config.yaml", output_root="./output", temp_dir="./temp"):
        """
        初始化Sora Web客户端
        
        Args:
            config_path: 配置文件路径
            output_root: 输出根目录
            temp_dir: 临时目录
        """
        self.output_root = Path(output_root)
        self.temp_dir = Path(temp_dir)
        
        # 加载配置文件
        config_path = Path(config_path)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        
        # 获取Sora配置
        sora_config = self.config.get('sora', {})
        self.use_mock = False  # 强制禁用模拟模式
        
        # 创建目录
        self.output_root.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置PyAutoGUI的安全特性
        pyautogui.PAUSE = 1  # 每次PyAutoGUI函数执行后暂停1秒
        pyautogui.FAILSAFE = True  # 将鼠标移动到屏幕左上角会引发异常，用于紧急停止
        
        # 检查下载目录
        self.download_dir = Path.home() / "Downloads"
        if not self.download_dir.exists():
            logger.warning(f"默认下载目录不存在: {self.download_dir}，使用临时目录")
            self.download_dir = self.temp_dir
        
        # 记录当前浏览器是否已打开
        self.browser_opened = False
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # 不要关闭浏览器，因为这是用户已有的浏览器
        pass
        
    def start(self):
        """启动Chrome浏览器"""
        if self.browser_opened:
            logger.warning("浏览器已启动")
            return
            
        logger.info("启动桌面上的Chrome浏览器...")
        self._start_chrome()
        self.browser_opened = True
        
    def _start_chrome(self):
        """连接到系统已打开的Chrome浏览器"""
        system = platform.system()
        try:
            if system == "Windows":
                # 尝试附加到现有的Chrome窗口而不是启动新实例
                # 使用os.system命令尝试激活现有窗口
                os.system('powershell -command "(New-Object -ComObject WScript.Shell).AppActivate(\'Chrome\')"')
                # 如果桌面上没有打开的Chrome，则尝试打开一个新的Chrome
                # 但使用--profile-directory选项使用默认配置文件
                chrome_user_dir = self.config.get('sora', {}).get('chrome_user_dir')
                if chrome_user_dir:
                    logger.info(f"使用自定义Chrome配置文件: {chrome_user_dir}")
                    subprocess.Popen([r"C:\Program Files\Google\Chrome\Application\chrome.exe", f"--user-data-dir={chrome_user_dir}"])
                else:
                    # 尝试使用默认的用户数据目录
                    logger.info("使用默认Chrome配置文件")
                    subprocess.Popen([r"C:\Program Files\Google\Chrome\Application\chrome.exe"])
            elif system == "Darwin":  # macOS
                # 尝试先激活现有窗口
                subprocess.Popen(['osascript', '-e', 'tell application "Google Chrome" to activate'])
                time.sleep(1)
                # 如果没有打开的窗口，则打开一个新窗口
                subprocess.Popen(["open", "-a", "Google Chrome"])
            elif system == "Linux":
                # 尝试检查是否已经有Chrome运行
                ps_process = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
                output, _ = ps_process.communicate()
                if b'chrome' in output:
                    # 如果已经运行，发送命令激活窗口
                    subprocess.Popen(['wmctrl', '-a', 'Chrome'])
                else:
                    # 如果未运行，启动Chrome
                    subprocess.Popen(["google-chrome"])
            else:
                # 如果无法确定系统，则使用webbrowser模块
                webbrowser.get("chrome").open("")
            
            # 等待浏览器启动或激活
            time.sleep(2)
            logger.info("Chrome浏览器已激活或启动")
        except Exception as e:
            logger.error(f"激活Chrome浏览器失败: {str(e)}")
            # 使用webbrowser模块尝试打开默认浏览器
            try:
                webbrowser.open("")
                time.sleep(2)
                logger.info("已尝试打开默认浏览器")
            except Exception as e2:
                logger.error(f"打开默认浏览器也失败: {str(e2)}")
    
    def login_to_sora(self, url="https://sora.chatgpt.com/explore"):
        """访问Sora网站"""
        if not self.browser_opened:
            self.start()
            
        logger.info(f"导航到Sora网站: {url}")
        
        # 使用PyAutoGUI模拟键盘操作，打开新标签页并输入URL
        pyautogui.hotkey('ctrl', 't')  # 打开新标签页
        time.sleep(2)  # 等待新标签页完全打开
        
        # 按Ctrl+L激活地址栏
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(1.5)  # 给予更多时间确保地址栏激活
        
        # 清空地址栏并输入URL
        pyautogui.hotkey('ctrl', 'a')  # 全选当前地址
        time.sleep(0.5)
        pyautogui.press('delete')      # 删除当前地址
        time.sleep(1)
        
        # 输入URL并使用多种方式确保回车键被触发
        pyautogui.write(url)
        time.sleep(1.5)  # 给足时间让URL完整输入
        
        # 尝试多种方式触发回车键，提高成功率
        logger.info("尝试按下回车键...")
        pyautogui.press('enter')
        time.sleep(0.5)
        pyautogui.hotkey('enter')  # 使用hotkey方式再次尝试
        time.sleep(0.5)
        
        # 再次检查是否需要按回车，确保操作成功
        # 可以使用Alt+D回到地址栏
        pyautogui.hotkey('alt', 'd')
        time.sleep(0.5)
        pyautogui.press('end')  # 移动到URL末尾
        time.sleep(0.5)
        pyautogui.press('enter')  # 再次尝试回车
        
        logger.info("已尝试多种方法按下回车键，正在加载页面...")
        
        # 增加等待页面加载的时间
        logger.info("等待Sora页面加载...")
        time.sleep(10)  # 增加等待时间确保页面加载
        
        # 保存初始页面截图
        initial_screenshot = self._take_screenshot("initial_page.png")
        
        time.sleep(5)  # 再等待5秒确保页面完全加载
        
        # 保存加载后的截图
        sora_screenshot = self._take_screenshot("sora_page.png")
        
        # 检查是否需要登录
        # 简单检查页面上是否包含需要登录的元素
        # 这里无法进行精确的页面分析，所以使用一个简单的启发式方法
        try:
            is_login_page = pyautogui.locateOnScreen(
                os.path.join(os.path.dirname(__file__), "resources/login_button.png"), 
                confidence=0.7
            )
        except Exception as e:
            logger.warning(f"检查登录按钮出错: {str(e)}")
            is_login_page = None
        
        if is_login_page:
            logger.warning("需要登录，检测到登录页面")
            print("="*80)
            print("请在浏览器窗口中手动登录OpenAI账户")
            print("登录后请在60秒内完成，脚本将自动继续")
            print("="*80)
            
            # 等待用户手动登录，最多等待60秒
            login_success = False
            for i in range(60):
                time.sleep(1)
                # 检查是否已登录成功
                try:
                    check_login = pyautogui.locateOnScreen(
                        os.path.join(os.path.dirname(__file__), "resources/login_button.png"), 
                        confidence=0.7
                    )
                    login_success = not check_login
                except Exception as e:
                    logger.warning(f"检查登录状态出错: {str(e)}")
                    # 如果无法检查，假设登录成功
                    login_success = True
                
                if login_success:
                    logger.info(f"检测到登录成功，共等待 {i+1} 秒")
                    break
            
            # 再次等待页面加载
            time.sleep(5)
            self._take_screenshot("after_login.png")
        
        # 此时假设已登录成功
        logger.info("Sora页面已加载")
        return True
    
    def _take_screenshot(self, filename):
        """截取屏幕并保存"""
        screenshot = pyautogui.screenshot()
        screenshot_path = self.temp_dir / filename
        screenshot.save(str(screenshot_path))
        return screenshot_path
    
    def generate_videos(self, prompt, image_path, aspect_ratio="3:2", resolution="480p", count=4, duration="5"):
        """
        生成视频
        
        Args:
            prompt: 生成提示
            image_path: 输入图像路径
            aspect_ratio: 宽高比
            resolution: 分辨率
            count: 生成数量
            duration: 视频时长（秒）
            
        Returns:
            生成的视频文件路径列表
        """
        if not self.browser_opened:
            self.start()
            
        image_path = Path(image_path)
        if not image_path.exists():
            raise ValueError(f"图像文件不存在: {image_path}")
            
        logger.info(f"生成视频，提示: '{prompt}'")
        
        try:
            # 保存生成前的截图
            self._take_screenshot("before_create.png")
            
            # 导航到创建页面 - 使用现有窗口而不是打开新标签页
            pyautogui.hotkey('ctrl', 'l')  # 激活地址栏
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'a')  # 全选当前地址
            pyautogui.press('delete')
            time.sleep(0.5)
            pyautogui.write("https://sora.chatgpt.com/create")
            pyautogui.press('enter')
            time.sleep(5)  # 等待页面加载
            
            # 保存创建页面截图
            self._take_screenshot("create_page.png")
            
            # 查找提示输入框并点击
            # 首先尝试定位输入框元素
            input_area = self._find_text_input_area()
            if input_area:
                x, y, w, h = input_area
                logger.info(f"找到文本输入区域: {input_area}")
                pyautogui.click(x + w/2, y + h/2)  # 点击输入框中心
            else:
                # 如果找不到输入框，使用页面中心位置
                screen_width, screen_height = pyautogui.size()
                text_input_x = screen_width // 2
                text_input_y = int(screen_height * 0.4)  # 调整为页面40%的位置
                logger.info(f"找不到输入框，使用默认位置 ({text_input_x}, {text_input_y})")
                pyautogui.click(text_input_x, text_input_y)
            
            time.sleep(1)
            
            # 清空输入框并输入提示
            pyautogui.hotkey('ctrl', 'a')  # 全选
            pyautogui.press('delete')  # 删除已有内容
            time.sleep(0.5)
            pyautogui.write(prompt)
            time.sleep(1)
            
            # 保存输入提示后的截图
            self._take_screenshot("after_prompt.png")
            
            # 设置视频参数
            logger.info("设置视频参数...")
            self._set_video_parameters(aspect_ratio, resolution, count)
            
            # 上传图片
            logger.info(f"上传图片: {image_path}")
            self._upload_image(image_path)
            
            # 点击生成按钮
            logger.info("点击生成按钮...")
            generate_button = self._find_generate_button()
            if generate_button:
                x, y, w, h = generate_button
                logger.info(f"找到生成按钮: {generate_button}")
                pyautogui.click(x + w/2, y + h/2)
            else:
                # 如果找不到生成按钮，使用页面右下角位置
                screen_width, screen_height = pyautogui.size()
                generate_button_x = int(screen_width * 0.9)  # 右侧90%位置
                generate_button_y = int(screen_height * 0.9)  # 底部90%位置
                logger.info(f"找不到生成按钮，使用默认位置 ({generate_button_x}, {generate_button_y})")
                pyautogui.click(generate_button_x, generate_button_y)
            
            # 等待生成完成 - 最多等待15分钟
            logger.info("等待Sora生成视频，可能需要几分钟...")
            
            # 每30秒截图一次以监控进度
            generation_time = 900  # 最多等待15分钟
            start_time = time.time()
            
            # 等待视频生成完成
            self._wait_for_video_generation(start_time, generation_time)
            
            # 保存生成完成后的截图
            final_screenshot = self._take_screenshot("generation_complete.png")
            logger.info("已保存生成完成截图")
            
            # 下载视频
            logger.info("开始下载视频...")
            video_files = self._download_videos()
            
            if not video_files:
                logger.error("未找到下载的视频文件")
                return []
            
            logger.info(f"找到 {len(video_files)} 个视频文件")
            
            # 将视频文件移动到临时目录
            video_paths = []
            for i, video_file in enumerate(video_files):
                output_file = self.temp_dir / f"video_{i+1}.mp4"
                shutil.copy2(video_file, output_file)
                
                # 检查视频时长
                cap = cv2.VideoCapture(str(output_file))
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    video_duration = frame_count / fps if fps > 0 else 0
                    cap.release()
                    
                    logger.info(f"视频 #{i+1} 时长: {video_duration:.2f}秒")
                    
                    # 如果视频时长不足5秒，尝试延长
                    if video_duration < 4.9 and fps > 0:
                        logger.warning(f"视频 #{i+1} 时长不足5秒，尝试延长视频")
                        self._extend_video_to_5_seconds(output_file, fps)
                
                video_paths.append(output_file)
                logger.info(f"视频 #{i+1} 已保存: {output_file}")
            
            return video_paths
            
        except Exception as e:
            logger.error(f"生成视频时出错: {str(e)}")
            # 保存当前屏幕截图以便调试
            self._take_screenshot("generate_error.png")
            return []
    
    def _find_text_input_area(self):
        """尝试在页面上找到文本输入区域"""
        # 这里使用简单的图像识别方法
        # 实际项目中可能需要更复杂的方法
        try:
            return pyautogui.locateOnScreen(
                os.path.join(os.path.dirname(__file__), "resources/text_input.png"), 
                confidence=0.7
            )
        except Exception as e:
            logger.warning(f"检查文本输入区域出错: {str(e)}")
            # 返回None表示未找到输入框，调用者需要处理错误
            return None
    
    def _find_generate_button(self):
        """尝试在页面上找到生成按钮"""
        try:
            return pyautogui.locateOnScreen(
                os.path.join(os.path.dirname(__file__), "resources/generate_button.png"), 
                confidence=0.7
            )
        except Exception as e:
            logger.warning(f"检查生成按钮出错: {str(e)}")
            return None
        
    def _set_video_parameters(self, aspect_ratio="3:2", resolution="480p", count=4):
        """设置视频参数"""
        try:
            # 查找设置按钮
            try:
                settings_button = pyautogui.locateOnScreen(
                    os.path.join(os.path.dirname(__file__), "resources/settings_button.png"), 
                    confidence=0.7
                )
            except Exception as e:
                logger.warning(f"检查设置按钮出错: {str(e)}")
                settings_button = None
            
            if settings_button:
                x, y, w, h = settings_button
                logger.info(f"找到设置按钮: {settings_button}")
                pyautogui.click(x + w/2, y + h/2)
            else:
                # 如果找不到设置按钮，尝试点击页面右上角
                screen_width, screen_height = pyautogui.size()
                settings_x = int(screen_width * 0.9)
                settings_y = int(screen_height * 0.1)
                logger.info(f"找不到设置按钮，使用默认位置 ({settings_x}, {settings_y})")
                pyautogui.click(settings_x, settings_y)
                
            time.sleep(1)
            
            # 设置宽高比
            # 这里假设界面有下拉菜单
            pyautogui.press('tab')  # 切换到宽高比选项
            pyautogui.press('space')  # 打开下拉菜单
            time.sleep(0.5)
            
            # 查找3:2选项
            for _ in range(5):  # 最多按5次向下键
                pyautogui.press('down')
                time.sleep(0.2)
                # 这里可以添加图像识别来确认是否找到了3:2选项
                
            pyautogui.press('enter')  # 选择当前选项
            time.sleep(0.5)
            
            # 设置分辨率
            pyautogui.press('tab')  # 切换到分辨率选项
            pyautogui.press('space')  # 打开下拉菜单
            time.sleep(0.5)
            
            # 查找480p选项
            for _ in range(3):  # 最多按3次向下键
                pyautogui.press('down')
                time.sleep(0.2)
                
            pyautogui.press('enter')  # 选择当前选项
            time.sleep(0.5)
            
            # 设置生成数量
            pyautogui.press('tab')  # 切换到数量选项
            pyautogui.press('space')  # 打开下拉菜单
            time.sleep(0.5)
            
            # 选择生成4个视频
            for _ in range(3):  # 最多按3次向下键
                pyautogui.press('down')
                time.sleep(0.2)
                
            pyautogui.press('enter')  # 选择当前选项
            time.sleep(0.5)
            
            # 保存设置
            pyautogui.press('tab')
            pyautogui.press('enter')
            time.sleep(1)
            
            # 保存设置后的截图
            self._take_screenshot("after_settings.png")
            
        except Exception as e:
            logger.error(f"设置视频参数时出错: {str(e)}")
    
    def _upload_image(self, image_path):
        """上传图片"""
        try:
            # 查找上传按钮
            try:
                upload_button = pyautogui.locateOnScreen(
                    os.path.join(os.path.dirname(__file__), "resources/upload_button.png"), 
                    confidence=0.7
                )
            except Exception as e:
                logger.warning(f"检查上传按钮出错: {str(e)}")
                upload_button = None
            
            if upload_button:
                x, y, w, h = upload_button
                logger.info(f"找到上传按钮: {upload_button}")
                pyautogui.click(x + w/2, y + h/2)
            else:
                # 如果找不到上传按钮，尝试点击页面左上角
                screen_width, screen_height = pyautogui.size()
                upload_x = int(screen_width * 0.1)
                upload_y = int(screen_height * 0.1)
                logger.info(f"找不到上传按钮，使用默认位置 ({upload_x}, {upload_y})")
                pyautogui.click(upload_x, upload_y)
                
            time.sleep(2)
            
            # 等待文件选择对话框
            # 输入图像路径
            logger.info(f"输入图像路径: {image_path.absolute()}")
            pyautogui.write(str(image_path.absolute()))
            time.sleep(1)
            pyautogui.press('enter')
            time.sleep(3)  # 等待图片上传
            
            # 保存上传后的截图
            self._take_screenshot("after_upload.png")
            
        except Exception as e:
            logger.error(f"上传图片时出错: {str(e)}")
    
    def _wait_for_video_generation(self, start_time, max_wait_time):
        """等待视频生成完成"""
        while time.time() - start_time < max_wait_time:
            # 每30秒截图一次
            if int((time.time() - start_time) / 30) > 0 and int((time.time() - start_time) % 30) == 0:
                self._take_screenshot(f"generating_{int((time.time() - start_time) // 30)}.png")
                logger.info(f"已等待 {int((time.time() - start_time))} 秒...")
            
            # 查找下载按钮以确认视频是否生成完成
            try:
                download_button = pyautogui.locateOnScreen(
                    os.path.join(os.path.dirname(__file__), "resources/download_button.png"), 
                    confidence=0.7
                )
            except Exception as e:
                logger.warning(f"检查下载按钮出错: {str(e)}")
                download_button = None
            
            if download_button:
                logger.info("检测到下载按钮，视频已生成完成")
                return True
                
            # 如果等待时间超过2分钟，每30秒检查一次下载按钮
            if time.time() - start_time > 120 and int((time.time() - start_time) % 30) == 0:
                logger.info("等待超过2分钟，检查视频是否已生成...")
                
                # 这里可以添加额外的检查逻辑
                
            time.sleep(5)
        
        logger.warning(f"等待视频生成超时，已等待 {max_wait_time} 秒")
        return False
    
    def _download_videos(self):
        """下载生成的视频"""
        try:
            # 保存下载前的截图
            self._take_screenshot("before_download.png")
            
            # 查找所有下载按钮
            screen_width, screen_height = pyautogui.size()
            
            # 记录下载前下载目录中的视频文件
            before_videos = set(self.download_dir.glob("*.mp4"))
            
            # 检查是否可以自动找到下载按钮
            can_auto_download = False
            
            # 尝试自动下载
            for i in range(4):
                # 查找下载按钮
                try:
                    download_button = pyautogui.locateOnScreen(
                        os.path.join(os.path.dirname(__file__), "resources/download_button.png"), 
                        confidence=0.7
                    )
                except Exception as e:
                    logger.warning(f"检查下载按钮出错: {str(e)}")
                    download_button = None
                
                if download_button:
                    x, y, w, h = download_button
                    logger.info(f"找到下载按钮 #{i+1}: {download_button}")
                    pyautogui.click(x + w/2, y + h/2)
                    time.sleep(3)  # 等待下载开始
                    can_auto_download = True
                else:
                    break
            
            if not can_auto_download:
                # 如果无法自动下载，提示用户手动下载
                print("\n" + "="*80)
                print("请按以下步骤手动完成下载:")
                print("1. 点击每个视频下的下载按钮，将视频保存到默认下载文件夹")
                print("2. 所有视频下载完成后，按下Enter键继续")
                print("="*80 + "\n")
                
                input("所有视频下载完成后，请按Enter键继续...")
            
            # 等待下载完成
            time.sleep(5)
            
            # 保存下载后的截图
            self._take_screenshot("after_download.png")
            
            # 查找下载目录中的新视频文件
            after_videos = set(self.download_dir.glob("*.mp4"))
            new_videos = after_videos - before_videos
            
            # 如果没有找到新视频，尝试其他可能的文件名格式
            if not new_videos:
                all_videos = list(self.download_dir.glob("*.mp4"))
                # 只保留最近修改的4个视频文件
                all_videos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                new_videos = set(all_videos[:4])
            
            return list(new_videos)
            
        except Exception as e:
            logger.error(f"下载视频时出错: {str(e)}")
            return []
    
    def _extend_video_to_5_seconds(self, video_path, fps=30):
        """
        将视频延长到5秒
        
        Args:
            video_path: 视频文件路径
            fps: 帧率
            
        Returns:
            操作是否成功
        """
        try:
            # 读取视频
            video_path = Path(video_path)
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                return False
            
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS) if fps <= 0 else fps
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 计算需要的帧数
            target_frames = int(5 * fps)
            
            if frame_count >= target_frames:
                logger.info(f"视频已有足够的帧数: {frame_count} >= {target_frames}")
                cap.release()
                return True
            
            # 读取所有帧
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frames.append(frame)
            
            cap.release()
            
            # 创建新视频
            temp_path = video_path.with_name(f"{video_path.stem}_extended{video_path.suffix}")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(str(temp_path), fourcc, fps, (width, height))
            
            # 写入原始帧
            for frame in frames:
                out.write(frame)
            
            # 重复最后一帧直到达到目标帧数
            if frames:
                last_frame = frames[-1]
                for _ in range(target_frames - frame_count):
                    out.write(last_frame)
            
            out.release()
            
            # 替换原始视频
            temp_path.replace(video_path)
            
            logger.info(f"视频成功延长到5秒, 总帧数: {target_frames}")
            return True
            
        except Exception as e:
            logger.error(f"延长视频时出错: {str(e)}")
            return False
    
    def process_pipeline(self, prompt_file, image_file, output_dir=None):
        """
        处理完整的流水线
        
        Args:
            prompt_file: 提示文件路径
            image_file: 图像文件路径
            output_dir: 输出目录
            
        Returns:
            如果成功处理则返回True，否则返回False
        """
        prompt_file = Path(prompt_file)
        image_file = Path(image_file)
        
        if not prompt_file.exists():
            logger.error(f"提示文件不存在: {prompt_file}")
            return False
            
        if not image_file.exists():
            logger.error(f"图像文件不存在: {image_file}")
            return False
        
        # 创建输出目录
        if output_dir is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_root / f"output_{timestamp}"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取提示文件
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt = f.read().strip()
        except Exception as e:
            logger.error(f"读取提示文件时出错: {str(e)}")
            return False
        
        # 生成视频
        success = False
        videos = self.generate_videos(prompt, image_file, aspect_ratio="3:2", resolution="480p", count=4, duration="5")
        if not videos:
            logger.error("未生成任何视频")
            return False
        
        # 过滤视频
        valid_videos = []
        for i, video_path in enumerate(videos):
            logger.info(f"过滤视频 #{i+1}: {video_path}")
            
            # 创建过滤信息文件
            info_file = video_path.with_suffix('.json')
            
            # 使用规则过滤器
            passed = filter_video(video_path, output_info=info_file)
            
            if passed:
                valid_videos.append(video_path)
                logger.info(f"视频 #{i+1} 通过过滤")
            else:
                logger.info(f"视频 #{i+1} 未通过过滤")
        
        # 检查是否有有效视频
        if valid_videos:
            success = True
            logger.info(f"共有 {len(valid_videos)} 个视频通过过滤")
            
            # 处理有效视频
            for i, video_path in enumerate(valid_videos):
                # 创建输出子目录
                video_output_dir = output_dir / f"video_{i+1}"
                rgb_dir = video_output_dir / "rgb"
                rgb_dir.mkdir(parents=True, exist_ok=True)
                
                # 将视频转换为帧
                logger.info(f"将视频 #{i+1} 转换为帧")
                video_to_frames(video_path, rgb_dir)
                
                # 确保命名从frame_000000.png到frame_000149.png
                frames = list(rgb_dir.glob("*.png"))
                frames.sort()
                for i, frame in enumerate(frames[:150]):
                    new_name = rgb_dir / f"frame_{i:06d}.png"
                    if frame.name != new_name.name:
                        frame.rename(new_name)
                
                # 复制视频到输出目录
                video_dest = video_output_dir / "video.mp4"
                shutil.copy2(video_path, video_dest)
                
                # 将信息文件复制到输出目录
                info_file = video_path.with_suffix('.json')
                if info_file.exists():
                    info_dest = video_output_dir / "filter.json"
                    shutil.copy2(info_file, info_dest)
                
                logger.info(f"视频 #{i+1} 已处理并保存到: {video_output_dir}")
            
            # 创建成功标记
            with open(output_dir / "success.txt", 'w') as f:
                f.write(f"处理成功: {len(valid_videos)} 个视频通过过滤\n")
                f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"提示: {prompt}\n")
            
            return True
        else:
            logger.warning("所有视频都未通过过滤")
            return False

def main():
    """主函数"""
    from utils import setup_logging
    import argparse
    
    # 设置命令行参数
    parser = argparse.ArgumentParser(description="Sora Web自动化客户端")
    parser.add_argument("--prompt", required=True, help="提示文件路径")
    parser.add_argument("--image", required=True, help="图像文件路径")
    parser.add_argument("--output", help="输出目录")
    parser.add_argument("--headless", action="store_true", help="使用无头模式")
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 创建客户端
    with SoraWebClient() as client:
        # 登录
        if not client.login_to_sora():
            logger.error("登录失败，终止处理")
            return
        
        # 处理流水线
        success = client.process_pipeline(args.prompt, args.image, args.output)
        
        if success:
            logger.info("处理成功")
        else:
            logger.error("处理失败")

if __name__ == "__main__":
    main() 