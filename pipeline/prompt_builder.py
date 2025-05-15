import cv2
import numpy as np
from PIL import Image
import torch
import torchvision.transforms as transforms
import torchvision.models as models
from pathlib import Path
import logging
import json
from utils import generate_prompt

logger = logging.getLogger('pipeline')

class PromptBuilder:
    def __init__(self):
        """初始化提示生成器"""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        logger.info(f"使用设备: {self.device}")
        
        # 加载预训练模型用于特征提取（可选）
        try:
            self.model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
            self.model.to(self.device)
            self.model.eval()
            logger.info("目标检测模型已加载")
        except Exception as e:
            logger.error(f"模型加载失败: {str(e)}")
            self.model = None
    
    def extract_background_color(self, image_path):
        """
        提取图像的主要背景颜色
        
        Args:
            image_path: 图像路径
            
        Returns:
            颜色描述字符串
        """
        # 读取图像
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"无法读取图像: {image_path}")
            return "白色"  # 默认背景色
        
        # 转换为RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # 提取边缘区域作为背景样本
        h, w = img_rgb.shape[:2]
        margin = 50  # 边缘像素
        
        # 采样四个边缘
        top = img_rgb[:margin, :, :]
        bottom = img_rgb[h-margin:, :, :]
        left = img_rgb[:, :margin, :]
        right = img_rgb[:, w-margin:, :]
        
        # 合并边缘区域
        edges = np.vstack([top.reshape(-1, 3), 
                          bottom.reshape(-1, 3),
                          left.reshape(-1, 3),
                          right.reshape(-1, 3)])
        
        # 使用K-means聚类提取主要颜色
        pixels = np.float32(edges)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        k = 3  # 提取3个主要颜色
        _, labels, palette = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # 计算每个颜色的比例
        counts = np.bincount(labels.flatten())
        dominant_color = palette[np.argmax(counts)]
        
        # 将RGB值转换为颜色名称
        color_name = self._get_color_name(dominant_color)
        logger.info(f"检测到背景颜色: {color_name}")
        
        return color_name
    
    def _get_color_name(self, rgb):
        """
        将RGB值转换为颜色名称
        
        Args:
            rgb: RGB颜色值
            
        Returns:
            颜色名称
        """
        # 定义基本颜色字典 (RGB -> 名称)
        colors = {
            (255, 255, 255): "白色",
            (0, 0, 0): "黑色",
            (255, 0, 0): "红色",
            (0, 255, 0): "绿色",
            (0, 0, 255): "蓝色",
            (255, 255, 0): "黄色",
            (255, 0, 255): "粉色",
            (0, 255, 255): "青色",
            (128, 128, 128): "灰色",
            (165, 42, 42): "棕色",
            (255, 165, 0): "橙色",
            (128, 0, 128): "紫色"
        }
        
        # 计算给定RGB值与已知颜色的欧氏距离
        min_dist = float('inf')
        color_name = "未知颜色"
        
        for known_rgb, name in colors.items():
            dist = np.sqrt(np.sum(np.square(np.array(known_rgb) - rgb)))
            if dist < min_dist:
                min_dist = dist
                color_name = name
        
        return color_name
    
    def detect_object_bbox(self, image_path):
        """
        检测图像中的主要物体并返回边界框
        
        Args:
            image_path: 图像路径
            
        Returns:
            边界框坐标 (x1, y1, x2, y2) 或 None
        """
        if self.model is None:
            logger.warning("目标检测模型未加载，使用默认中心区域")
            # 使用图像中心区域作为默认边界框
            img = cv2.imread(str(image_path))
            h, w = img.shape[:2]
            center_x, center_y = w // 2, h // 2
            size = min(w, h) // 3
            return (center_x - size, center_y - size, 
                    center_x + size, center_y + size)
        
        # 使用目标检测模型
        try:
            # 加载并预处理图像
            image = Image.open(image_path).convert("RGB")
            transform = transforms.Compose([
                transforms.ToTensor()
            ])
            img_tensor = transform(image).to(self.device)
            
            # 推理
            with torch.no_grad():
                prediction = self.model([img_tensor])
                
            # 获取检测结果
            boxes = prediction[0]['boxes'].cpu().numpy()
            scores = prediction[0]['scores'].cpu().numpy()
            labels = prediction[0]['labels'].cpu().numpy()
            
            if len(boxes) == 0:
                logger.warning("未检测到物体，使用默认中心区域")
                # 使用默认值
                h, w = image.height, image.width
                center_x, center_y = w // 2, h // 2
                size = min(w, h) // 3
                return (center_x - size, center_y - size, 
                        center_x + size, center_y + size)
            
            # 选择得分最高的物体
            best_idx = np.argmax(scores)
            bbox = boxes[best_idx].astype(int)
            
            logger.info(f"检测到物体边界框: {bbox}")
            return tuple(bbox)
            
        except Exception as e:
            logger.error(f"目标检测失败: {str(e)}")
            # 使用默认值
            img = cv2.imread(str(image_path))
            h, w = img.shape[:2]
            center_x, center_y = w // 2, h // 2
            size = min(w, h) // 3
            return (center_x - size, center_y - size, 
                    center_x + size, center_y + size)
    
    def build_prompt(self, image_path, obj_name, hand_gesture="握住"):
        """
        根据图像和物体名称构建提示
        
        Args:
            image_path: 图像路径
            obj_name: 物体名称
            hand_gesture: 手势描述
            
        Returns:
            生成的提示字符串和提取的信息字典
        """
        # 提取背景颜色
        background_color = self.extract_background_color(image_path)
        
        # 检测物体边界框
        bbox = self.detect_object_bbox(image_path)
        
        # 使用工具函数生成提示
        prompt = generate_prompt(obj_name, background_color, hand_gesture)
        
        # 记录提取的信息
        info = {
            "background_color": background_color,
            "object_bbox": bbox,
            "object_name": obj_name,
            "hand_gesture": hand_gesture,
            "prompt": prompt
        }
        
        logger.info(f"生成提示: {prompt}")
        return prompt, info
    
    def save_prompt_info(self, output_dir, info):
        """
        保存提示信息到文件
        
        Args:
            output_dir: 输出目录
            info: 提示信息字典
        """
        output_dir = Path(output_dir)
        output_path = output_dir / 'prompt.info'
        
        with open(output_path, 'w') as f:
            json.dump(info, f, indent=2)
        
        logger.info(f"提示信息已保存到: {output_path}")

def build_and_save_prompt(image_path, output_dir, obj_name, hand_gesture="握住"):
    """
    构建提示并保存到文件
    
    Args:
        image_path: 输入图像路径
        output_dir: 输出目录
        obj_name: 物体名称
        hand_gesture: 手势描述
        
    Returns:
        生成的提示字符串
    """
    builder = PromptBuilder()
    prompt, info = builder.build_prompt(image_path, obj_name, hand_gesture)
    builder.save_prompt_info(output_dir, info)
    return prompt

if __name__ == "__main__":
    import sys
    from utils import setup_logging
    
    # 设置日志
    logger = setup_logging()
    
    # 获取命令行参数
    if len(sys.argv) < 3:
        print("用法: python prompt_builder.py <image_path> <obj_name> [output_dir] [hand_gesture]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    obj_name = sys.argv[2]
    output_dir = sys.argv[3] if len(sys.argv) > 3 else Path(image_path).parent
    hand_gesture = sys.argv[4] if len(sys.argv) > 4 else "握住"
    
    # 构建提示
    prompt = build_and_save_prompt(image_path, output_dir, obj_name, hand_gesture)
    print(f"生成的提示: {prompt}") 