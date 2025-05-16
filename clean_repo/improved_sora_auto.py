#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import os
import sys
import time
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

class SoraAutomation:
    def __init__(self, image_path, prompt_path, output_dir="./videos"):
        self.image_path = Path(image_path).absolute()
        self.prompt_text = Path(prompt_path).read_text(encoding="utf-8")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        if not self.image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {self.image_path}")
            
        print(f"图片路径: {self.image_path}")
        print(f"提示文本: {self.prompt_text[:50]}...")
        print(f"输出目录: {self.output_dir}")

    async def connect_to_browser(self, playwright):
        """尝试连接到已运行的Chrome浏览器，如果失败则启动新实例"""
        # 尝试多种连接地址格式
        connection_urls = [
            "http://localhost:9222",
            "http://127.0.0.1:9222",
            "ws://localhost:9222/devtools/browser",
            "ws://127.0.0.1:9222/devtools/browser"
        ]
        
        print("尝试连接到已有的Chrome浏览器...")
        for url in connection_urls:
            try:
                print(f"尝试连接到: {url}")
                browser = await playwright.chromium.connect_over_cdp(url)
                print(f"成功连接到Chrome实例: {url}")
                return browser
            except Exception as e:
                print(f"连接到 {url} 失败: {str(e)[:100]}...")
        
        print("所有连接尝试均失败")
        
        # 检查Chrome进程是否在运行
        try:
            print("检查Chrome进程...")
            result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq chrome.exe"], capture_output=True, text=True)
            if "chrome.exe" in result.stdout:
                print("检测到Chrome进程正在运行")
                print("建议: 请确保Chrome使用--remote-debugging-port=9222参数启动")
            else:
                print("未检测到Chrome进程")
        except Exception as e:
            print(f"检查Chrome进程失败: {e}")
        
        # 询问用户是否希望启动新的Chrome实例
        choice = input("\n是否要启动新的Chrome实例？(y/n): ").strip().lower()
        if choice != 'y':
            print("操作已取消")
            return None
            
        # 启动一个新的Chrome实例
        print("\n尝试启动新的Chrome实例...")
        try:
            # 先尝试启动无配置的Chrome
            browser = await playwright.chromium.launch(
                headless=False,
                args=[
                    "--remote-debugging-port=9222",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-default-apps",
                    "--disable-popup-blocking",
                    "--start-maximized"
                ]
            )
            print("成功启动无配置的Chrome")
            return browser
        except Exception as no_profile_error:
            print(f"启动无配置Chrome失败: {no_profile_error}")
            
            try:
                # 尝试使用用户的配置文件
                user_data_dir = os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data"
                print(f"尝试使用用户配置文件启动Chrome: {user_data_dir}")
                browser = await playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir,
                    headless=False,
                    channel="chrome",
                    args=[
                        "--remote-debugging-port=9222",
                        "--start-maximized"
                    ]
                )
                print("已启动带个人配置的Chrome")
                return browser
            except Exception as profile_error:
                print(f"使用个人配置启动Chrome失败: {profile_error}")
                print("所有尝试均失败，请手动运行Chrome后再尝试")
                return None

    async def run(self):
        """运行Sora自动化流程"""
        async with async_playwright() as p:
            # 连接或启动浏览器
            browser = await self.connect_to_browser(p)
            if not browser:
                print("无法连接或启动浏览器，操作已终止")
                return False
                
            try:
                # 创建新标签页并访问Sora
                print("打开Sora页面...")
                page = await browser.new_page()
                await page.goto("https://sora.chatgpt.com/explore", timeout=60000)
                
                # 等待页面加载
                print("等待页面加载完成...")
                await page.wait_for_load_state("networkidle", timeout=30000)
                
                # 检查当前URL，判断是否需要登录
                current_url = page.url
                print(f"当前页面URL: {current_url}")
                
                if "login" in current_url or "/auth/" in current_url:
                    print("\n" + "="*80)
                    print("检测到需要登录，请在Chrome浏览器中手动登录")
                    print("完成登录后，请按Enter键继续...")
                    print("="*80 + "\n")
                    
                    # 保存登录页面截图
                    await page.screenshot(path="login_page.png")
                    print("已保存登录页面截图到 login_page.png")
                    
                    # 等待用户手动登录
                    input("在Chrome完成登录后，按Enter键继续...")
                    
                    # 重新导航到Sora页面
                    print("重新导航到Sora页面...")
                    await page.goto("https://sora.chatgpt.com/explore", timeout=60000)
                    
                    # 再次检查是否成功登录
                    if "login" in page.url or "/auth/" in page.url:
                        print("登录似乎失败，仍然在登录页面")
                        return False
                
                # 保存页面截图和结构
                await page.screenshot(path="page_loaded.png")
                print(f"已保存页面截图到: page_loaded.png")
                
                # 找到Create按钮并点击进入创建页面
                print("查找Create按钮...")
                try:
                    # 如果在探索页面，找到Create按钮点击
                    if "/explore" in page.url:
                        print("尝试查找各种可能的创建按钮...")
                        create_button = None
                        create_selectors = [
                            "text=Create", 
                            '[data-testid="create-button"]',
                            'a[href="/create"]',
                            'button:has-text("Create")',
                            'a:has-text("Create")'
                        ]
                        
                        for selector in create_selectors:
                            try:
                                print(f"尝试选择器: {selector}")
                                button = await page.wait_for_selector(selector, timeout=2000)
                                if button:
                                    create_button = button
                                    print(f"找到Create按钮: {selector}")
                                    break
                            except Exception as e:
                                print(f"选择器 {selector} 失败: {e}")
                        
                        if create_button:
                            print("点击创建按钮，进入创建页面")
                            await create_button.click()
                            await page.wait_for_load_state("networkidle")
                        else:
                            print("未找到任何创建按钮，尝试直接导航到create页面")
                            await page.goto("https://sora.chatgpt.com/create", timeout=30000)
                    else:
                        print("当前不在explore页面，尝试直接导航到create页面")
                        await page.goto("https://sora.chatgpt.com/create", timeout=30000)
                except Exception as e:
                    print(f"无法找到或点击Create按钮: {e}")
                
                # 查找输入框
                print("查找提示输入框...")
                textarea = None
                selectors = [
                    "textarea", 
                    "div[contenteditable='true']",
                    "[role='textbox']",
                    ".prompt-input",
                    "div.prompt-textarea",
                    "[data-testid='prompt-textarea']",
                    "[placeholder*='Describe']",
                    "[placeholder*='描述']",
                    "form textarea",
                    "div.ProseMirror"
                ]
                
                # 增加等待时间以确保页面完全加载
                print("等待页面完全加载...")
                await page.wait_for_load_state("networkidle", timeout=15000)
                
                for selector in selectors:
                    try:
                        print(f"尝试选择器: {selector}")
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            textarea = element
                            print(f"找到输入框: {selector}")
                            break
                    except Exception as e:
                        print(f"选择器 {selector} 失败: {e}")
                
                if not textarea:
                    print("无法找到提示输入框，尝试键盘输入...")
                    await page.click("body")
                    await page.keyboard.type(self.prompt_text)
                    await page.screenshot(path="input_not_found.png")
                    print("已保存截图: input_not_found.png")
                else:
                    print("输入提示文本...")
                    await textarea.fill(self.prompt_text)
                    print("提示文本已填写")
                
                # 设置视频拦截
                video_urls = []
                
                async def on_response(response):
                    url = response.url
                    if url.endswith(".mp4") and response.status == 200:
                        print(f"捕获到视频URL: {url}")
                        video_urls.append(url)
                
                page.on("response", on_response)
                
                # 执行操作流程
                try:
                    # 上传图片
                    print("查找上传按钮...")
                    upload_button = None
                    upload_selectors = [
                        'button:has-text("Upload")', 
                        'button:has-text("上传")',
                        '[aria-label="Upload image"]',
                        'input[type="file"]',
                        '[data-testid*="upload"]',
                        'button:has-text("Image")',
                        'button:has-text("图片")',
                        'button svg[viewBox*="24"]'  # 许多上传图标使用这种SVG
                    ]
                    
                    # 截图页面，帮助找到上传按钮
                    await page.screenshot(path="create_page.png")
                    print("已保存创建页面截图: create_page.png")
                    
                    for selector in upload_selectors:
                        try:
                            print(f"尝试选择器: {selector}")
                            button = await page.wait_for_selector(selector, timeout=5000)
                            if button:
                                upload_button = button
                                print(f"找到上传按钮: {selector}")
                                break
                        except Exception as e:
                            print(f"选择器 {selector} 失败: {e}")
                    
                    if not upload_button:
                        print("无法找到上传按钮，请查看截图")
                        await page.screenshot(path="no_upload_button.png")
                        print("已保存截图: no_upload_button.png")
                        return False
                    
                    # 上传图片
                    print("准备上传图片...")
                    try:
                        # 创建文件选择器Promise并点击上传按钮
                        async with page.expect_file_chooser() as fc_info:
                            await upload_button.click()
                            file_chooser = await fc_info.value
                            await file_chooser.set_files(str(self.image_path))
                            print(f"已上传图片: {self.image_path}")
                    except Exception as e:
                        print(f"上传图片时出错: {e}")
                        await page.screenshot(path="upload_error.png")
                        print("已保存截图: upload_error.png")
                        return False
                    
                    # 等待图片上传完成
                    print("等待图片上传完成...")
                    try:
                        await page.wait_for_selector('img[alt="Uploaded image"]', timeout=30000)
                        print("图片上传成功")
                    except Exception as e:
                        print(f"等待图片上传完成时出错: {e}")
                        print("继续执行，可能已上传成功")
                    
                    # 查找并点击生成按钮
                    print("查找生成按钮...")
                    generate_button = None
                    generate_selectors = [
                        'button:has-text("Generate")',
                        'button:has-text("生成")',
                        '[data-testid="generate-button"]'
                    ]
                    
                    for selector in generate_selectors:
                        try:
                            button = await page.wait_for_selector(selector, timeout=5000)
                            if button:
                                generate_button = button
                                print(f"找到生成按钮: {selector}")
                                break
                        except:
                            pass
                    
                    if not generate_button:
                        print("无法找到生成按钮，请查看截图")
                        await page.screenshot(path="no_generate_button.png")
                        print("已保存截图: no_generate_button.png")
                        return False
                    
                    # 点击生成按钮
                    print("点击生成按钮，开始生成视频...")
                    await generate_button.click()
                    
                    # 等待视频生成完成
                    print("等待视频生成，可能需要几分钟...")
                    try:
                        await page.wait_for_response(
                            lambda r: r.url.endswith(".mp4") and r.status == 200, 
                            timeout=900000  # 15分钟
                        )
                        print(f"视频生成完成，捕获到 {len(video_urls)} 个视频URL")
                    except Exception as e:
                        print(f"等待视频生成超时: {e}")
                        if video_urls:
                            print(f"但已捕获到 {len(video_urls)} 个视频URL")
                        else:
                            print("未捕获到视频URL，尝试寻找下载按钮...")
                            await page.screenshot(path="generation_timeout.png")
                    
                    # 下载视频
                    if video_urls:
                        print(f"下载 {len(video_urls)} 个视频...")
                        for idx, url in enumerate(video_urls):
                            try:
                                filename = f"video_{idx+1}.mp4"
                                filepath = self.output_dir / filename
                                
                                print(f"下载视频 {idx+1}/{len(video_urls)}: {filename}")
                                resp = await page.request.get(url)
                                data = await resp.body()
                                
                                filepath.write_bytes(data)
                                print(f"已保存: {filepath}")
                            except Exception as e:
                                print(f"下载视频失败: {e}")
                    else:
                        # 尝试通过下载按钮下载
                        print("尝试通过下载按钮下载视频...")
                        download_buttons = await page.query_selector_all('button:has-text("Download")')
                        
                        if download_buttons:
                            print(f"找到 {len(download_buttons)} 个下载按钮")
                            for idx, button in enumerate(download_buttons):
                                try:
                                    # 保存到视频目录
                                    download_path = self.output_dir / f"video_manual_{idx+1}.mp4"
                                    
                                    # 点击下载按钮
                                    async with page.expect_download() as download_info:
                                        await button.click()
                                        download = await download_info.value
                                        await download.save_as(download_path)
                                        print(f"已保存视频: {download_path}")
                                except Exception as e:
                                    print(f"下载视频失败: {e}")
                        else:
                            print("未找到下载按钮，生成可能失败")
                            await page.screenshot(path="no_download_buttons.png")
                    
                    print("处理完成")
                    return True
                
                except Exception as e:
                    print(f"执行出错: {e}")
                    await page.screenshot(path="error.png")
                    print("已保存错误截图: error.png")
                    return False
                
            except Exception as e:
                print(f"脚本执行出错: {e}")
                return False
                
            finally:
                # 关闭浏览器连接，但不关闭浏览器窗口
                print("关闭浏览器连接（浏览器窗口保持打开）")
                await browser.close()

async def amain():
    # 默认参数
    image_path = "color_000000.png"
    prompt_path = "prompt.txt"
    output_dir = "./videos"
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    if len(sys.argv) > 2:
        prompt_path = sys.argv[2]
    if len(sys.argv) > 3:
        output_dir = sys.argv[3]
    
    # 运行自动化流程
    automation = SoraAutomation(image_path, prompt_path, output_dir)
    success = await automation.run()
    
    return 0 if success else 1

def main():
    """同步入口点"""
    exit_code = asyncio.run(amain())
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 