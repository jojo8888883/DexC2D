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

    async def run(self):
        """运行Sora自动化流程"""
        async with async_playwright() as p:
            try:
                # 连接到已有的Chrome实例
                print("连接到您的桌面Chrome浏览器...")
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                print("成功连接到Chrome实例")
            except Exception as e:
                print(f"无法连接到Chrome: {e}")
                print("\n请确保您已经使用以下命令启动了Chrome:")
                print('"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222')
                print("或者运行use_desktop_chrome.bat批处理文件")
                return False
            
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
            
            if "login" in current_url:
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
                if "login" in page.url:
                    print("登录似乎失败，仍然在登录页面")
                    await browser.close()
                    return False
            
            # 保存页面截图和结构
            await page.screenshot(path="page_loaded.png")
            print(f"已保存页面截图到: page_loaded.png")
            
            # 查找输入框
            print("查找提示输入框...")
            textarea = None
            selectors = [
                "textarea", 
                "div[contenteditable='true']",
                "[role='textbox']",
                ".prompt-input",
                "div.prompt-textarea",
                "[data-testid='prompt-textarea']"
            ]
            
            for selector in selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        textarea = element
                        print(f"找到输入框: {selector}")
                        break
                except:
                    pass
            
            if not textarea:
                print("无法找到提示输入框，尝试键盘输入...")
                await page.click("body")
                await page.keyboard.type(self.prompt_text)
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
                    'button:has-text("上传")'
                ]
                
                for selector in upload_selectors:
                    try:
                        button = await page.wait_for_selector(selector, timeout=5000)
                        if button:
                            upload_button = button
                            print(f"找到上传按钮: {selector}")
                            break
                    except:
                        pass
                
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
                    'button:has-text("生成")'
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
            
            finally:
                # 关闭连接
                print("关闭浏览器连接")
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
