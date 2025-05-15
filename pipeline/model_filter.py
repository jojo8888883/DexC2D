import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import logging
import json
import time
from typing import List, Dict, Tuple, Optional, Union

logger = logging.getLogger('pipeline')

class VideoDataset(Dataset):
    """视频数据集，用于处理单个视频文件"""
    
    def __init__(self, video_path, num_frames=16, transform=None):
        """
        初始化视频数据集
        
        Args:
            video_path: 视频文件路径
            num_frames: 要采样的帧数
            transform: 数据变换
        """
        self.video_path = Path(video_path)
        self.num_frames = num_frames
        self.transform = transform
        self.frames = self._load_frames()
        
    def _load_frames(self):
        """加载视频帧"""
        frames = []
        
        # 打开视频
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            logger.error(f"无法打开视频: {self.video_path}")
            return frames
        
        # 获取视频信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 计算采样间隔
        if total_frames <= self.num_frames:
            # 如果视频帧数少于需要的帧数，则重复帧
            indices = list(range(total_frames)) * (self.num_frames // total_frames + 1)
            indices = indices[:self.num_frames]
        else:
            # 均匀采样
            indices = np.linspace(0, total_frames - 1, self.num_frames, dtype=int)
        
        # 加载指定帧
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # 转换为RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
        
        # 释放视频
        cap.release()
        
        # 如果帧数不足，复制最后一帧
        while len(frames) < self.num_frames:
            frames.append(frames[-1] if frames else np.zeros((224, 224, 3), dtype=np.uint8))
        
        return frames
    
    def __len__(self):
        """返回数据集长度（始终为1，仅处理单个视频）"""
        return 1
    
    def __getitem__(self, idx):
        """获取视频帧张量"""
        # 转换为张量
        frames = np.array(self.frames) / 255.0  # 归一化到 [0, 1]
        
        # 应用变换
        if self.transform:
            transformed_frames = []
            for frame in frames:
                transformed_frames.append(self.transform(frame))
            frames = np.array(transformed_frames)
        
        # [T, H, W, C] -> [T, C, H, W]
        frames = frames.transpose(0, 3, 1, 2)
        
        # 转换为张量
        frames_tensor = torch.FloatTensor(frames)
        
        return frames_tensor

class SimplifiedVideoMAE(nn.Module):
    """简化版VideoMAE模型，用于物理可行性评估"""
    
    def __init__(self, num_frames=16, num_classes=2):
        """
        初始化模型
        
        Args:
            num_frames: 输入帧数
            num_classes: 输出类别数（2表示合理/不合理）
        """
        super(SimplifiedVideoMAE, self).__init__()
        
        # 使用预训练的ResNet作为骨干网络
        self.backbone = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
        
        # 移除最后的全连接层
        self.features = nn.Sequential(*list(self.backbone.children())[:-2])
        
        # 时间维度的处理
        self.temporal_pool = nn.AdaptiveAvgPool3d((4, 1, 1))
        
        # 分类头
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(512 * 4, 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        """
        前向传播
        
        Args:
            x: 输入张量，形状为[B, T, C, H, W]，B是批次大小，T是帧数
            
        Returns:
            输出张量，形状为[B, num_classes]
        """
        batch_size, t, c, h, w = x.shape
        
        # 重新排列为[B*T, C, H, W]以通过2D CNN
        x = x.view(batch_size * t, c, h, w)
        
        # 通过骨干网络
        x = self.features(x)
        
        # 重新排列为[B, T, C', H', W']
        _, c_new, h_new, w_new = x.shape
        x = x.view(batch_size, t, c_new, h_new, w_new)
        
        # 转置为[B, C', T, H', W']以适应3D池化
        x = x.permute(0, 2, 1, 3, 4)
        
        # 时间维度池化
        x = self.temporal_pool(x)
        
        # 分类
        x = self.classifier(x)
        
        return x

class ModelFilter:
    """基于深度学习模型的视频过滤器"""
    
    def __init__(self, model_path=None, device=None):
        """
        初始化过滤器
        
        Args:
            model_path: 模型路径，如果为None则使用预训练模型
            device: 设备（'cuda'或'cpu'）
        """
        # 设置设备
        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"使用设备: {self.device}")
        
        # 初始化模型
        self.model = SimplifiedVideoMAE(num_frames=16, num_classes=2)
        
        if model_path and Path(model_path).exists():
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"已加载模型: {model_path}")
            except Exception as e:
                logger.error(f"加载模型失败: {str(e)}")
                logger.warning("使用未训练的模型")
        else:
            logger.warning("未提供模型路径或模型不存在，使用未训练的模型")
        
        # 将模型移动到设备
        self.model.to(self.device)
        self.model.eval()
        
        # 默认阈值
        self.threshold = 0.7
    
    def preprocess_video(self, video_path):
        """
        预处理视频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            预处理后的视频张量
        """
        # 创建数据集和数据加载器
        dataset = VideoDataset(video_path, num_frames=16)
        dataloader = DataLoader(dataset, batch_size=1, shuffle=False)
        
        # 获取视频张量
        for batch in dataloader:
            return batch.to(self.device)
        
        return None
    
    def predict(self, video_path):
        """
        预测视频物理可行性
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            预测结果字典
        """
        video_path = Path(video_path)
        if not video_path.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return {'score': 0.0, 'label': 'unreasonable', 'confidence': 1.0}
        
        try:
            # 预处理视频
            video_tensor = self.preprocess_video(video_path)
            if video_tensor is None:
                logger.error(f"视频预处理失败: {video_path}")
                return {'score': 0.0, 'label': 'unreasonable', 'confidence': 1.0}
            
            # 推理
            with torch.no_grad():
                outputs = self.model(video_tensor)
                probabilities = F.softmax(outputs, dim=1)
                
                # 获取合理性得分（第二个类别的概率）
                score = probabilities[0, 1].item()
                confidence = max(probabilities[0, 0].item(), probabilities[0, 1].item())
                
                # 决定标签
                label = 'reasonable' if score >= self.threshold else 'unreasonable'
                
                result = {
                    'score': score,
                    'label': label,
                    'confidence': confidence
                }
                
                logger.info(f"预测结果: 视频={video_path.name}, 得分={score:.4f}, 标签={label}, 置信度={confidence:.4f}")
                return result
                
        except Exception as e:
            logger.error(f"预测失败: {str(e)}")
            return {'score': 0.0, 'label': 'unreasonable', 'confidence': 1.0}
    
    def filter_video(self, video_path, threshold=None, output_info=None):
        """
        过滤视频
        
        Args:
            video_path: 视频文件路径
            threshold: 阈值，如果为None则使用默认值
            output_info: 输出信息保存路径，如果为None则不保存
            
        Returns:
            如果视频通过过滤则返回True，否则返回False
        """
        threshold = threshold or self.threshold
        
        # 预测
        result = self.predict(video_path)
        score = result['score']
        label = result['label']
        
        # 判断是否通过
        passed = score >= threshold
        
        # 保存结果
        if output_info:
            result['threshold'] = threshold
            result['passed'] = passed
            
            with open(output_info, 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info(f"过滤结果已保存到: {output_info}")
        
        # 记录失败日志
        if not passed:
            video_path = Path(video_path)
            failed_log = video_path.parent / 'model_failed.log'
            with open(failed_log, 'a') as f:
                f.write(f"视频: {video_path.name}\n")
                f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"得分: {score:.4f} (阈值: {threshold})\n")
                f.write(f"标签: {label}\n")
                f.write("\n")
            
            logger.info(f"视频未通过模型过滤: {video_path}, 得分={score:.4f}, 阈值={threshold}")
        else:
            logger.info(f"视频通过模型过滤: {video_path}, 得分={score:.4f}, 阈值={threshold}")
        
        return passed

# 辅助函数：使用模型训练数据
def train_model(data_dir, output_model, epochs=10):
    """
    训练模型（用于未来升级）
    
    Args:
        data_dir: 数据目录，应包含reasonable和unreasonable两个子目录
        output_model: 输出模型路径
        epochs: 训练轮数
    """
    # 此函数实现留给未来升级
    logger.warning("训练功能尚未实现")
    pass
     
def filter_video(video_path, model_path=None, threshold=0.7, output_info=None):
    """
    过滤视频的便捷函数
    
    Args:
        video_path: 视频文件路径
        model_path: 模型路径
        threshold: 阈值
        output_info: 输出信息保存路径
        
    Returns:
        如果视频通过过滤则返回True，否则返回False
    """
    filter_obj = ModelFilter(model_path)
    return filter_obj.filter_video(video_path, threshold, output_info)

if __name__ == "__main__":
    import sys
    from utils import setup_logging
    
    # 设置日志
    logger = setup_logging()
    
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("用法: python model_filter.py <video_path> [model_path] [threshold] [output_info]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else None
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
    output_info = sys.argv[4] if len(sys.argv) > 4 else None
    
    # 过滤视频
    passed = filter_video(video_path, model_path, threshold, output_info)
    
    if passed:
        print(f"视频通过模型过滤: {video_path}")
    else:
        print(f"视频未通过模型过滤: {video_path}") 