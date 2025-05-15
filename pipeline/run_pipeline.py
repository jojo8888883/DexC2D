import os
import sys
import time
import asyncio
import argparse
import logging
from pathlib import Path
import yaml
import json
from typing import Dict, List, Optional, Union, Any

# 导入自定义模块
from utils import setup_logging, new_run_dir, read_meta_info, save_run_info
from capture import capture_and_save
from prompt_builder import build_and_save_prompt
from sora_client import generate_video
from rule_filter import filter_video as rule_filter_video
from model_filter import filter_video as model_filter_video
from video2png import video_to_frames

# 获取logger
logger = logging.getLogger('pipeline')

class Pipeline:
    """端到端自动化流水线"""
    
    def __init__(self, config_path=None):
        """
        初始化流水线
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        # 设置基本路径
        self.workspace_dir = Path(__file__).parent.parent
        self.gen_dataset_dir = self.workspace_dir / 'gen_dataset'
        self.gen_datas_dir = self.gen_dataset_dir / 'gen_datas'
        self.models_dir = self.gen_dataset_dir / 'models'
        
        # 确保目录存在
        self.gen_dataset_dir.mkdir(parents=True, exist_ok=True)
        self.gen_datas_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取meta.info
        self.meta_info = read_meta_info(self.gen_dataset_dir / 'meta.info')
        
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 任务状态
        self.current_run_dir = None
        self.stage_results = {}
    
    def _load_config(self, config_path=None):
        """
        加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        # 默认配置
        default_config = {
            'capture': {
                'camera_id': 0,
                'use_industry_cam': False
            },
            'prompt': {
                'hand_gesture': '握住'
            },
            'sora': {
                'api_key': os.environ.get('OPENAI_API_KEY')
            },
            'rule_filter': {
                'enabled': True,
                'flow_threshold': 1.5,
                'min_frame_ratio': 0.8
            },
            'model_filter': {
                'enabled': False,
                'model_path': None,
                'threshold': 0.7
            },
            'video2png': {
                'use_ffmpeg': True,
                'quality': 2
            },
            'pipeline': {
                'auto_retry': 3,
                'early_stop_on_failure': True
            }
        }
        
        # 如果提供了配置文件，加载它
        config = default_config.copy()
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = yaml.safe_load(f)
                
                # 更新配置
                for section, values in loaded_config.items():
                    if section in config:
                        config[section].update(values)
                    else:
                        config[section] = values
                
                logger.info(f"已加载配置: {config_path}")
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")
        
        return config
    
    def setup_run_dir(self, obj, ver=None):
        """
        设置运行目录
        
        Args:
            obj: 对象名称
            ver: 版本号，如果为None则自动计算
            
        Returns:
            运行目录路径
        """
        # 创建新的运行目录
        run_dir = new_run_dir(self.gen_datas_dir, obj, ver)
        self.current_run_dir = run_dir
        
        logger.info(f"创建运行目录: {run_dir}")
        
        # 初始化阶段结果
        self.stage_results = {
            'capture': {'status': 'pending'},
            'prompt': {'status': 'pending'},
            'sora': {'status': 'pending'},
            'rule_filter': {'status': 'pending'},
            'model_filter': {'status': 'pending'},
            'video2png': {'status': 'pending'}
        }
        
        # 初始化运行信息
        run_info = {
            'object': obj,
            'version': run_dir.name.split('_')[-1],
            'sequence': run_dir.name.split('_')[0],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'running'
        }
        save_run_info(run_dir, run_info)
        
        return run_dir
    
    async def run_capture_stage(self):
        """
        运行拍照阶段
        
        Returns:
            成功返回图像路径，失败返回None
        """
        logger.info("开始阶段1: 拍照")
        
        # 更新状态
        self.stage_results['capture']['status'] = 'running'
        
        try:
            # 获取配置
            camera_id = self.config['capture']['camera_id']
            use_industry_cam = self.config['capture']['use_industry_cam']
            
            # 运行拍照程序
            image_path = capture_and_save(
                self.current_run_dir,
                camera_id,
                use_industry_cam
            )
            
            if image_path:
                logger.info(f"拍照成功: {image_path}")
                self.stage_results['capture']['status'] = 'success'
                self.stage_results['capture']['image_path'] = str(image_path)
                return image_path
            else:
                logger.error("拍照失败")
                self.stage_results['capture']['status'] = 'failed'
                self.stage_results['capture']['error'] = "拍照失败"
                return None
                
        except Exception as e:
            logger.error(f"拍照阶段出错: {str(e)}")
            self.stage_results['capture']['status'] = 'failed'
            self.stage_results['capture']['error'] = str(e)
            return None
    
    async def run_prompt_stage(self, image_path, obj_name):
        """
        运行提示生成阶段
        
        Args:
            image_path: 图像路径
            obj_name: 对象名称
            
        Returns:
            成功返回提示字符串，失败返回None
        """
        logger.info("开始阶段2: 提示生成")
        
        # 更新状态
        self.stage_results['prompt']['status'] = 'running'
        
        try:
            # 获取配置
            hand_gesture = self.config['prompt']['hand_gesture']
            
            # 运行提示生成程序
            prompt = build_and_save_prompt(
                image_path,
                self.current_run_dir,
                obj_name,
                hand_gesture
            )
            
            if prompt:
                logger.info(f"提示生成成功: {prompt}")
                self.stage_results['prompt']['status'] = 'success'
                self.stage_results['prompt']['prompt'] = prompt
                return prompt
            else:
                logger.error("提示生成失败")
                self.stage_results['prompt']['status'] = 'failed'
                self.stage_results['prompt']['error'] = "提示生成失败"
                return None
                
        except Exception as e:
            logger.error(f"提示生成阶段出错: {str(e)}")
            self.stage_results['prompt']['status'] = 'failed'
            self.stage_results['prompt']['error'] = str(e)
            return None
    
    async def run_sora_stage(self, prompt):
        """
        运行Sora视频生成阶段
        
        Args:
            prompt: 提示字符串
            
        Returns:
            成功返回视频路径，失败返回None
        """
        logger.info("开始阶段3: Sora视频生成")
        
        # 更新状态
        self.stage_results['sora']['status'] = 'running'
        
        try:
            # 获取配置
            api_key = self.config['sora']['api_key']
            # 强制使用模拟模式，忽略配置文件中的设置
            use_mock = True
            
            # 设置输出路径
            video_dir = self.current_run_dir / 'video'
            video_dir.mkdir(exist_ok=True)
            video_path = video_dir / 'video.mp4'
            
            # 运行Sora客户端
            result_path = await generate_video(prompt, video_path, api_key, use_mock=use_mock)
            
            if result_path:
                logger.info(f"视频生成成功: {result_path}")
                self.stage_results['sora']['status'] = 'success'
                self.stage_results['sora']['video_path'] = str(result_path)
                return result_path
            else:
                logger.error("视频生成失败")
                self.stage_results['sora']['status'] = 'failed'
                self.stage_results['sora']['error'] = "视频生成失败"
                return None
                
        except Exception as e:
            logger.error(f"Sora阶段出错: {str(e)}")
            self.stage_results['sora']['status'] = 'failed'
            self.stage_results['sora']['error'] = str(e)
            return None
    
    async def run_rule_filter_stage(self, video_path, obj_name):
        """
        运行规则过滤阶段
        
        Args:
            video_path: 视频路径
            obj_name: 对象名称
            
        Returns:
            通过过滤返回True，否则返回False
        """
        logger.info("开始阶段4: 规则过滤")
        
        # 如果禁用了规则过滤，直接返回True
        if not self.config['rule_filter']['enabled']:
            logger.info("规则过滤已禁用，自动通过")
            self.stage_results['rule_filter']['status'] = 'skipped'
            return True
        
        # 更新状态
        self.stage_results['rule_filter']['status'] = 'running'
        
        try:
            # 获取配置
            # 可以在这里对特定物体设置特殊阈值
            
            # 设置输出路径
            output_info = self.current_run_dir / 'rule_filter.json'
            
            # 运行规则过滤
            passed = rule_filter_video(
                video_path,
                obj_name,  # 使用对象名称作为目标类别
                output_info
            )
            
            if passed:
                logger.info("视频通过规则过滤")
                self.stage_results['rule_filter']['status'] = 'success'
                self.stage_results['rule_filter']['passed'] = True
                return True
            else:
                logger.info("视频未通过规则过滤")
                self.stage_results['rule_filter']['status'] = 'success'
                self.stage_results['rule_filter']['passed'] = False
                return False
                
        except Exception as e:
            logger.error(f"规则过滤阶段出错: {str(e)}")
            self.stage_results['rule_filter']['status'] = 'failed'
            self.stage_results['rule_filter']['error'] = str(e)
            return False
    
    async def run_model_filter_stage(self, video_path):
        """
        运行模型过滤阶段
        
        Args:
            video_path: 视频路径
            
        Returns:
            通过过滤返回True，否则返回False
        """
        logger.info("开始阶段5: 模型过滤")
        
        # 如果禁用了模型过滤，直接返回True
        if not self.config['model_filter']['enabled']:
            logger.info("模型过滤已禁用，自动通过")
            self.stage_results['model_filter']['status'] = 'skipped'
            return True
        
        # 更新状态
        self.stage_results['model_filter']['status'] = 'running'
        
        try:
            # 获取配置
            model_path = self.config['model_filter']['model_path']
            threshold = self.config['model_filter']['threshold']
            
            # 设置输出路径
            output_info = self.current_run_dir / 'model_filter.json'
            
            # 运行模型过滤
            passed = model_filter_video(
                video_path,
                model_path,
                threshold,
                output_info
            )
            
            if passed:
                logger.info("视频通过模型过滤")
                self.stage_results['model_filter']['status'] = 'success'
                self.stage_results['model_filter']['passed'] = True
                return True
            else:
                logger.info("视频未通过模型过滤")
                self.stage_results['model_filter']['status'] = 'success'
                self.stage_results['model_filter']['passed'] = False
                return False
                
        except Exception as e:
            logger.error(f"模型过滤阶段出错: {str(e)}")
            self.stage_results['model_filter']['status'] = 'failed'
            self.stage_results['model_filter']['error'] = str(e)
            return False
    
    async def run_video2png_stage(self, video_path):
        """
        运行视频转PNG阶段
        
        Args:
            video_path: 视频路径
            
        Returns:
            成功返回True，失败返回False
        """
        logger.info("开始阶段6: 视频转PNG")
        
        # 更新状态
        self.stage_results['video2png']['status'] = 'running'
        
        try:
            # 获取配置
            use_ffmpeg = self.config['video2png']['use_ffmpeg']
            quality = self.config['video2png']['quality']
            
            # 设置输出路径
            output_dir = self.current_run_dir / 'rgb'
            
            # 运行视频转PNG
            success = video_to_frames(
                video_path,
                output_dir,
                use_ffmpeg,
                quality
            )
            
            if success:
                logger.info(f"视频已转换为PNG: {output_dir}")
                self.stage_results['video2png']['status'] = 'success'
                self.stage_results['video2png']['output_dir'] = str(output_dir)
                return True
            else:
                logger.error("视频转PNG失败")
                self.stage_results['video2png']['status'] = 'failed'
                self.stage_results['video2png']['error'] = "视频转PNG失败"
                return False
                
        except Exception as e:
            logger.error(f"视频转PNG阶段出错: {str(e)}")
            self.stage_results['video2png']['status'] = 'failed'
            self.stage_results['video2png']['error'] = str(e)
            return False
    
    async def run_pipeline(self, obj, ver=None, max_retries=None):
        """
        运行完整流水线
        
        Args:
            obj: 对象名称
            ver: 版本号，如果为None则自动计算
            max_retries: 最大重试次数，如果为None则使用配置中的值
            
        Returns:
            成功返回True，失败返回False
        """
        if max_retries is None:
            max_retries = self.config['pipeline']['auto_retry']
        
        # 检查对象是否存在于meta.info
        if obj not in self.meta_info and not obj.startswith('custom_'):
            logger.error(f"对象 '{obj}' 不在meta.info中")
            return False
        
        # 创建运行目录
        run_dir = self.setup_run_dir(obj, ver)
        
        # 运行流水线
        retry_count = 0
        success = False
        
        while retry_count <= max_retries and not success:
            if retry_count > 0:
                logger.info(f"第 {retry_count} 次重试...")
            
            # 阶段1: 拍照
            image_path = await self.run_capture_stage()
            if not image_path:
                if self.config['pipeline']['early_stop_on_failure']:
                    break
                retry_count += 1
                continue
            
            # 阶段2: 提示生成
            prompt = await self.run_prompt_stage(image_path, obj)
            if not prompt:
                if self.config['pipeline']['early_stop_on_failure']:
                    break
                retry_count += 1
                continue
            
            # 阶段3: Sora视频生成
            video_path = await self.run_sora_stage(prompt)
            if not video_path:
                if self.config['pipeline']['early_stop_on_failure']:
                    break
                retry_count += 1
                continue
            
            # 阶段4: 规则过滤
            rule_passed = await self.run_rule_filter_stage(video_path, obj)
            if not rule_passed:
                if self.config['pipeline']['early_stop_on_failure']:
                    break
                retry_count += 1
                continue
            
            # 阶段5: 模型过滤（可选）
            model_passed = await self.run_model_filter_stage(video_path)
            if not model_passed:
                if self.config['pipeline']['early_stop_on_failure']:
                    break
                retry_count += 1
                continue
            
            # 阶段6: 视频转PNG
            convert_success = await self.run_video2png_stage(video_path)
            if not convert_success:
                if self.config['pipeline']['early_stop_on_failure']:
                    break
                retry_count += 1
                continue
            
            # 所有阶段都成功
            success = True
            break
        
        # 更新运行信息
        run_info = {
            'object': obj,
            'version': run_dir.name.split('_')[-1],
            'sequence': run_dir.name.split('_')[0],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'success' if success else 'failed',
            'retry_count': retry_count,
            'stages': self.stage_results
        }
        save_run_info(run_dir, run_info)
        
        if success:
            logger.info(f"流水线运行成功: {run_dir}")
        else:
            logger.error(f"流水线运行失败: {run_dir}")
        
        return success
    
    async def run_watch_mode(self):
        """
        运行监听模式
        
        监听相机触发，自动运行流水线
        """
        logger.info("启动监听模式")
        
        while True:
            try:
                # 这里应该接入相机SDK的事件监听
                # 以下是简单的周期性轮询示例
                logger.info("等待相机触发...")
                await asyncio.sleep(5)  # 周期性检查
                
                # 如果有触发，则运行流水线
                # (实际代码应根据相机SDK的触发机制实现)
                
                # 示例: 每次循环询问是否捕获
                # 实际中应由相机事件触发
                # choice = input("是否捕获新图像？(y/n): ")
                # if choice.lower() == 'y':
                #     obj = input("输入对象名称: ")
                #     await self.run_pipeline(obj)
                
            except KeyboardInterrupt:
                logger.info("监听模式已停止")
                break
            except Exception as e:
                logger.error(f"监听模式出错: {str(e)}")
                await asyncio.sleep(10)  # 出错后等待一段时间再重试

async def main():
    """主函数"""
    # 设置命令行参数
    parser = argparse.ArgumentParser(description='端到端自动化流水线')
    parser.add_argument('--object', type=str, help='对象名称')
    parser.add_argument('--ver', type=str, help='版本号')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--watch', action='store_true', help='监听模式')
    parser.add_argument('--retry', type=int, default=None, help='最大重试次数')
    args = parser.parse_args()
    
    # 设置日志
    logger = setup_logging()
    
    # 初始化流水线
    pipeline = Pipeline(args.config)
    
    if args.watch:
        # 监听模式
        await pipeline.run_watch_mode()
    elif args.object:
        # 指定对象运行
        success = await pipeline.run_pipeline(args.object, args.ver, args.retry)
        if not success:
            sys.exit(1)
    else:
        logger.error("请指定对象名称或使用监听模式")
        sys.exit(1)

if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main()) 