import os
import time
import json
import asyncio
import logging
import aiohttp
import aiofiles
from pathlib import Path
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger('pipeline')

class SoraClient:
    """Sora API客户端"""
    
    def __init__(self, api_key=None, use_mock=False):
        """
        初始化Sora客户端
        
        Args:
            api_key: OpenAI API密钥，如果为None则从环境变量获取
            use_mock: 是否使用模拟模式（不调用真实API）
        """
        self.use_mock = use_mock
        
        # 只在非模拟模式下设置API密钥和创建客户端
        if not use_mock:
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                logger.warning("未设置API密钥，请设置OPENAI_API_KEY环境变量或在初始化时提供")
            
            self.client = AsyncOpenAI(api_key=self.api_key, timeout=60.0)  # 增加超时时间到60秒
        else:
            self.api_key = None
            self.client = None
            
        self.max_retries = 5
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
    async def generate_video(self, prompt, output_path=None):
        """
        生成视频
        
        Args:
            prompt: 用于生成视频的提示
            output_path: 视频保存路径，如果为None，则使用临时文件
            
        Returns:
            成功时返回视频文件路径，失败时返回None
        """
        # 在模拟模式下不需要API密钥
        if not self.use_mock and not self.api_key:
            logger.error("未设置API密钥")
            return None
        
        if output_path:
            output_path = Path(output_path)
            output_dir = output_path.parent
            output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"开始生成视频，提示: '{prompt}'")
            
            # 确定输出路径
            if output_path:
                # 确保输出路径有.mp4扩展名
                if not str(output_path).lower().endswith('.mp4'):
                    output_path = output_path.with_suffix('.mp4')
                video_path = output_path
            else:
                # 使用临时文件
                video_path = Path(f"temp_video_{int(time.time())}.mp4")
            
            # 模拟模式，直接创建视频
            if self.use_mock:
                logger.info("使用模拟模式创建视频")
                success = await self._create_mock_video(prompt, video_path)
                if not success:
                    logger.error("模拟视频创建失败")
                    return None
                logger.info(f"模拟视频已保存到: {video_path}")
                return video_path
            
            # 使用图像生成API模拟视频生成
            # 注意：由于Sora API尚未公开，这里使用图像生成作为替代
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024",
                response_format="url"
            )
            
            # 获取生成的图像URL
            image_url = response.data[0].url
            
            if not image_url:
                logger.error("生成失败，未获取到图像URL")
                return None
            
            # 下载图像并转换为静态视频文件
            # 实际生产环境中这里应该下载真正的视频文件
            success = await self._download_image_as_video(image_url, video_path)
            if not success:
                logger.error("视频下载失败")
                return None
            
            logger.info(f"视频已保存到: {video_path}")
            return video_path
            
        except Exception as e:
            logger.error(f"生成视频时出错: {str(e)}")
            # 记录失败日志
            if output_path:
                failed_log = output_path.parent / 'failed.log'
                with open(failed_log, 'w') as f:
                    f.write(f"提示: {prompt}\n")
                    f.write(f"错误: {str(e)}\n")
                    f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            return None
    
    async def _poll_job_status(self, job_id, max_attempts=30, interval=10):
        """
        轮询任务状态
        
        Args:
            job_id: 任务ID
            max_attempts: 最大尝试次数
            interval: 轮询间隔（秒）
            
        Returns:
            成功时返回视频URL，失败时返回None
        """
        logger.info(f"开始轮询任务状态: {job_id}")
        
        for attempt in range(max_attempts):
            try:
                # 查询任务状态 - 模拟查询过程
                # 当Sora API正式发布后，应替换为正确的检索方法
                await asyncio.sleep(interval)
                status = "completed"  # 模拟完成状态
                
                if status == "completed":
                    logger.info(f"任务已完成: {job_id}")
                    return f"https://example.com/mock_video_{job_id}.mp4"  # 模拟URL
                elif status == "failed":
                    logger.error(f"任务失败: {job_id}")
                    return None
                else:
                    logger.info(f"任务进行中 ({attempt+1}/{max_attempts}): {status}")
                    await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"查询任务状态时出错: {str(e)}")
                await asyncio.sleep(interval)
        
        logger.error(f"轮询超时: {job_id}")
        return None
    
    async def _download_video(self, url, path):
        """
        下载视频
        
        Args:
            url: 视频URL
            path: 保存路径
            
        Returns:
            下载成功返回True，否则返回False
        """
        logger.info(f"开始下载视频: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=60) as response:  # 增加超时时间
                    if response.status != 200:
                        logger.error(f"下载失败，状态码: {response.status}")
                        return False
                    
                    async with aiofiles.open(path, 'wb') as f:
                        while True:
                            chunk = await response.content.read(1024 * 1024)  # 1MB chunks
                            if not chunk:
                                break
                            await f.write(chunk)
            
            logger.info(f"视频下载完成: {path}")
            return True
            
        except Exception as e:
            logger.error(f"下载视频时出错: {str(e)}")
            # 如果文件已部分下载，删除它
            if path.exists():
                path.unlink()
            return False

    async def _download_image_as_video(self, url, path):
        """
        下载图像并转换为简单视频
        
        Args:
            url: 图像URL
            path: 保存路径
            
        Returns:
            下载并转换成功返回True，否则返回False
        """
        import cv2
        import numpy as np
        
        logger.info(f"开始下载图像并转换为视频: {url}")
        
        try:
            # 下载图像
            temp_img_path = path.with_suffix('.jpg')
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=60) as response:  # 增加超时时间
                    if response.status != 200:
                        logger.error(f"下载失败，状态码: {response.status}")
                        return False
                    
                    async with aiofiles.open(temp_img_path, 'wb') as f:
                        await f.write(await response.read())
            
            # 读取图像
            img = cv2.imread(str(temp_img_path))
            if img is None:
                logger.error(f"无法读取下载的图像: {temp_img_path}")
                return False
            
            # 创建简单的3秒视频，每秒30帧
            height, width, _ = img.shape
            fps = 30
            duration = 3  # 秒
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
            
            # 将图像写入视频3秒
            for _ in range(fps * duration):
                video_writer.write(img)
            
            # 释放资源
            video_writer.release()
            
            # 删除临时图像
            temp_img_path.unlink()
            
            logger.info(f"图像已转换为视频: {path}")
            return True
            
        except Exception as e:
            logger.error(f"图像转视频时出错: {str(e)}")
            # 如果文件已部分下载，删除它
            if path.exists():
                path.unlink()
            return False
    
    async def _create_mock_video(self, prompt, path):
        """
        创建模拟视频，完全不调用API
        
        Args:
            prompt: 提示文本
            path: 保存路径
            
        Returns:
            创建成功返回True，否则返回False
        """
        import cv2
        import numpy as np
        from PIL import Image, ImageDraw, ImageFont
        
        logger.info(f"创建模拟视频: {path}")
        
        try:
            # 创建一个白色背景图像
            width, height = 1024, 1024
            image = Image.new('RGB', (width, height), color='white')
            draw = ImageDraw.Draw(image)
            
            # 尝试加载字体，失败时使用默认字体
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            
            # 在图像上绘制提示文本
            text_color = (0, 0, 0)  # 黑色文字
            text_position = (50, 50)
            
            # 换行处理长文本
            words = prompt.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                if draw.textlength(test_line, font=font) > width - 100:
                    current_line.pop()
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # 绘制文本
            y_position = text_position[1]
            for line in lines:
                draw.text((text_position[0], y_position), line, font=font, fill=text_color)
                y_position += 50
            
            # 绘制一个矩形框，模拟产品展示
            rect_left = width // 4
            rect_top = height // 2
            rect_right = width * 3 // 4
            rect_bottom = height * 3 // 4
            draw.rectangle([rect_left, rect_top, rect_right, rect_bottom], outline=(0, 0, 255), width=5)
            
            # 添加文字说明物体
            obj_name = "饼干盒" if "饼干盒" in prompt else "物体"
            draw.text((width // 2 - 50, rect_top - 50), obj_name, font=font, fill=(255, 0, 0))
            
            # 临时保存图像
            temp_img_path = path.with_suffix('.jpg')
            image.save(str(temp_img_path))
            
            # 将图像转换为OpenCV格式
            img = cv2.imread(str(temp_img_path))
            
            # 创建视频
            fps = 30
            duration = 3  # 秒
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
            
            # 将图像写入视频，添加一些简单动画效果
            for frame in range(fps * duration):
                current_frame = img.copy()
                
                # 添加闪烁的边框，每半秒变换一次颜色
                if (frame // 15) % 2 == 0:
                    cv2.rectangle(current_frame, 
                                 (rect_left, rect_top), 
                                 (rect_right, rect_bottom), 
                                 (0, 0, 255), 5)
                else:
                    cv2.rectangle(current_frame, 
                                 (rect_left, rect_top), 
                                 (rect_right, rect_bottom), 
                                 (255, 0, 0), 5)
                
                video_writer.write(current_frame)
            
            # 释放资源
            video_writer.release()
            
            # 删除临时图像
            temp_img_path.unlink()
            
            logger.info(f"模拟视频创建成功: {path}")
            return True
            
        except Exception as e:
            logger.error(f"创建模拟视频时出错: {str(e)}")
            if path.exists():
                path.unlink()
            return False

async def generate_video(prompt, output_path=None, api_key=None, use_mock=False):
    """
    使用Sora生成视频的便捷函数
    
    Args:
        prompt: 用于生成视频的提示
        output_path: 视频保存路径
        api_key: OpenAI API密钥
        use_mock: 是否使用模拟模式
        
    Returns:
        成功时返回视频文件路径，失败时返回None
    """
    client = SoraClient(api_key, use_mock)
    return await client.generate_video(prompt, output_path)

if __name__ == "__main__":
    import sys
    import asyncio
    from utils import setup_logging
    
    # 设置日志
    logger = setup_logging()
    
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("用法: python sora_client.py <prompt> [output_path] [--mock]")
        sys.exit(1)
        
    prompt = sys.argv[1]
    output_path = None
    use_mock = False
    
    # 解析剩余参数
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == "--mock":
            use_mock = True
        elif not output_path and not sys.argv[i].startswith("--"):
            output_path = sys.argv[i]
    
    # 运行
    async def main():
        result = await generate_video(prompt, output_path, use_mock=use_mock)
        if result:
            print(f"成功: {result}")
        else:
            print("失败")
    
    asyncio.run(main()) 