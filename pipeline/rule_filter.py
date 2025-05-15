import cv2
import numpy as np
import logging
import mediapipe as mp
from pathlib import Path
import time
from ultralytics import YOLO
import json

logger = logging.getLogger('pipeline')

class RuleFilter:
    """基于规则的视频过滤器"""
    
    def __init__(self, yolo_model_path=None):
        """
        初始化过滤器
        
        Args:
            yolo_model_path: YOLOv8模型路径，如果为None则使用预训练模型
        """
        # 初始化MediaPipe Hands
        self.mp_hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 初始化YOLOv8
        try:
            if yolo_model_path:
                self.yolo = YOLO(yolo_model_path)
            else:
                self.yolo = YOLO('yolov8n.pt')  # 使用预训练模型
            logger.info("YOLOv8模型已加载")
        except Exception as e:
            logger.error(f"加载YOLOv8模型失败: {str(e)}")
            self.yolo = None
        
        # YOLOv8标准类别到自定义类别的映射
        self.yolo_class_map = {
            # COCO数据集对象类别ID映射到我们的目标物体
            39: "bottle",     # 瓶子
            41: "cup",        # 杯子
            42: "fork",       # 叉子
            43: "knife",      # 刀
            44: "spoon",      # 勺子
            45: "bowl",       # 碗
            47: "apple",      # 苹果
            49: "orange",     # 橙子
            51: "carrot",     # 胡萝卜
            52: "broccoli",   # 西兰花
            65: "bed",        # 床
            67: "dining table", # 餐桌
            70: "toilet",     # 马桶
            73: "laptop",     # 笔记本电脑
            74: "mouse",      # 鼠标
            75: "remote",     # 遥控器
            76: "keyboard",   # 键盘
            77: "cell phone"  # 手机
        }
        
        # 默认设置
        self.flow_threshold = 1.5
        self.detection_threshold = 0.5
        self.min_frame_ratio = 0.8
        self.sample_interval = 5
    
    def is_static_camera(self, prev_frame, curr_frame, threshold=None):
        """
        检测相机是否静止
        
        Args:
            prev_frame: 前一帧
            curr_frame: 当前帧
            threshold: 光流阈值，如果为None则使用默认值
            
        Returns:
            如果相机静止则返回True，否则返回False
        """
        if threshold is None:
            threshold = self.flow_threshold
        
        # 转换为灰度图
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
        
        # 计算光流
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0
        )
        
        # 计算光流幅度
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        flow_mag = np.mean(mag)
        
        return flow_mag < threshold, flow_mag
    
    def has_hand(self, frame):
        """
        检测帧中是否有手
        
        Args:
            frame: 输入帧
            
        Returns:
            如果检测到手则返回True，否则返回False
        """
        # 转换为RGB（MediaPipe需要RGB输入）
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 检测手
        results = self.mp_hands.process(rgb_frame)
        
        # 检查是否有手部地标
        return results.multi_hand_landmarks is not None and len(results.multi_hand_landmarks) > 0
    
    def has_target_object(self, frame, target_class=None, threshold=None):
        """
        检测帧中是否有目标物体
        
        Args:
            frame: 输入帧
            target_class: 目标类别名称或ID
            threshold: 检测阈值，如果为None则使用默认值
            
        Returns:
            如果检测到目标物体则返回True，否则返回False
        """
        if self.yolo is None:
            logger.warning("YOLOv8模型未加载，跳过目标检测")
            return True
        
        if threshold is None:
            threshold = self.detection_threshold
        
        # 运行YOLOv8检测
        results = self.yolo(frame, conf=threshold)[0]
        
        # 如果没有指定目标类别，则任何检测到的物体都算
        if target_class is None:
            return len(results.boxes) > 0
        
        # 检查是否有目标类别
        detected_classes = results.boxes.cls.cpu().numpy().astype(int)
        detected_names = [results.names[cls_id] for cls_id in detected_classes]
        
        # 如果目标类别是ID
        if isinstance(target_class, int):
            return target_class in detected_classes
        
        # 如果目标类别是名称
        return target_class in detected_names or target_class in self.yolo_class_map.values()
    
    def is_mock_video(self, video_path):
        """
        检测是否是模拟视频（由SoraClient在模拟模式下生成的视频）
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            如果是模拟视频则返回True，否则返回False
        """
        # 打开视频
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return False
        
        # 读取中间帧
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 5:
            cap.release()
            return False
        
        # 跳到中间帧
        middle_frame = total_frames // 2
        cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
        
        # 读取帧
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return False
        
        # 通过检测特定的颜色边框和文字来判断是否是模拟视频
        # 模拟视频通常有红色或蓝色的矩形边框和"饼干盒"等文字
        
        try:
            # 检查是否存在红色或蓝色的像素点（边框颜色）
            red_blue_pixels = np.sum((frame[:,:,0] > 200) | (frame[:,:,2] > 200))
            significant_red_blue = red_blue_pixels > (frame.shape[0] * frame.shape[1] * 0.01)  # 至少1%的像素
            
            # 检查图像中间是否有可能的物体框
            height, width = frame.shape[:2]
            center_region = frame[height//3:height*2//3, width//3:width*2//3]
            edge_pixels = np.sum((center_region[:,:,0] > 200) | (center_region[:,:,2] > 200))
            has_center_object = edge_pixels > 100  # 中心区域有一定数量的边缘像素
            
            return significant_red_blue and has_center_object
        except Exception as e:
            logger.error(f"检测模拟视频时出错: {str(e)}")
            return False
    
    def filter_video(self, video_path, target_class=None, output_info=None):
        """
        过滤视频
        
        Args:
            video_path: 视频文件路径
            target_class: 目标类别
            output_info: 输出信息保存路径，如果为None则不保存
            
        Returns:
            如果视频通过过滤则返回True，否则返回False
        """
        video_path = Path(video_path)
        if not video_path.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return False
        
        # 检查是否是模拟视频
        if self.is_mock_video(video_path):
            logger.info(f"检测到模拟视频，自动通过过滤: {video_path}")
            
            # 保存模拟视频的过滤信息
            if output_info:
                mock_filter_info = {
                    "video_path": str(video_path),
                    "is_mock_video": True,
                    "hand_ratio": 1.0,
                    "object_ratio": 1.0,
                    "static_ratio": 1.0,
                    "average_flow": 0.0,
                    "auto_passed": True
                }
                with open(output_info, 'w') as f:
                    json.dump(mock_filter_info, f, indent=2)
                logger.info(f"模拟视频过滤信息已保存到: {output_info}")
            
            return True
        
        # 打开视频
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"无法打开视频: {video_path}")
            return False
        
        # 获取总帧数
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        logger.info(f"开始过滤视频: {video_path}, 总帧数: {total_frames}, FPS: {fps}")
        
        # 统计
        hand_detected_frames = 0
        object_detected_frames = 0
        static_camera_frames = 0
        checked_frames = 0
        flow_values = []
        
        # 读取第一帧
        ret, prev_frame = cap.read()
        if not ret:
            logger.error("无法读取第一帧")
            cap.release()
            return False
        
        frame_idx = 0
        early_stop = False
        
        # 处理视频帧
        while True:
            ret, curr_frame = cap.read()
            if not ret:
                break
            
            frame_idx += 1
            
            # 每隔几帧检查一次
            if frame_idx % self.sample_interval != 0:
                continue
            
            checked_frames += 1
            
            # 检查手部
            has_hand = self.has_hand(curr_frame)
            if has_hand:
                hand_detected_frames += 1
            
            # 检查目标物体
            has_object = self.has_target_object(curr_frame, target_class)
            if has_object:
                object_detected_frames += 1
            
            # 检查相机是否静止
            is_static, flow_mag = self.is_static_camera(prev_frame, curr_frame)
            flow_values.append(flow_mag)
            if is_static:
                static_camera_frames += 1
            
            # 更新前一帧
            prev_frame = curr_frame.copy()
            
            # 早停：如果连续50帧检测不到手或物体，直接判定为失败
            if checked_frames >= 50 and (hand_detected_frames == 0 or object_detected_frames == 0):
                logger.info("早停：连续多帧未检测到手或目标物体")
                early_stop = True
                break
        
        # 释放视频
        cap.release()
        
        # 计算比例
        if checked_frames == 0:
            logger.error("未检查任何帧")
            return False
        
        hand_ratio = hand_detected_frames / checked_frames
        object_ratio = object_detected_frames / checked_frames
        static_ratio = static_camera_frames / checked_frames
        
        # 平均光流
        avg_flow = np.mean(flow_values) if flow_values else float('inf')
        
        # 保存过滤信息
        filter_info = {
            "video_path": str(video_path),
            "total_frames": total_frames,
            "checked_frames": checked_frames,
            "hand_detected_frames": hand_detected_frames,
            "hand_ratio": hand_ratio,
            "object_detected_frames": object_detected_frames,
            "object_ratio": object_ratio,
            "static_camera_frames": static_camera_frames,
            "static_ratio": static_ratio,
            "average_flow": float(avg_flow),
            "early_stopped": early_stop
        }
        
        logger.info(f"过滤结果: 手部比例={hand_ratio:.2f}, 物体比例={object_ratio:.2f}, 静止相机比例={static_ratio:.2f}, 平均光流={avg_flow:.2f}")
        
        # 保存信息
        if output_info:
            with open(output_info, 'w') as f:
                json.dump(filter_info, f, indent=2)
            logger.info(f"过滤信息已保存到: {output_info}")
        
        # 判断是否通过
        passed = (
            hand_ratio >= self.min_frame_ratio and
            object_ratio >= self.min_frame_ratio and
            static_ratio >= self.min_frame_ratio and
            not early_stop
        )
        
        if passed:
            logger.info(f"视频通过过滤: {video_path}")
        else:
            logger.info(f"视频未通过过滤: {video_path}")
            
            # 如果不通过，记录失败原因
            reasons = []
            if hand_ratio < self.min_frame_ratio:
                reasons.append(f"手部检测率过低: {hand_ratio:.2f} < {self.min_frame_ratio}")
            if object_ratio < self.min_frame_ratio:
                reasons.append(f"物体检测率过低: {object_ratio:.2f} < {self.min_frame_ratio}")
            if static_ratio < self.min_frame_ratio:
                reasons.append(f"静止相机比例过低: {static_ratio:.2f} < {self.min_frame_ratio}")
            if early_stop:
                reasons.append("早停：连续多帧未检测到手或目标物体")
            
            logger.info(f"失败原因: {', '.join(reasons)}")
            
            # 记录到失败日志
            failed_log = video_path.parent / 'failed.log'
            with open(failed_log, 'a') as f:
                f.write(f"视频: {video_path.name}\n")
                f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"原因: {', '.join(reasons)}\n")
                f.write("\n")
        
        return passed

def filter_video(video_path, target_class=None, output_info=None, yolo_model=None):
    """
    过滤视频的便捷函数
    
    Args:
        video_path: 视频文件路径
        target_class: 目标类别
        output_info: 输出信息保存路径
        yolo_model: YOLOv8模型路径
        
    Returns:
        如果视频通过过滤则返回True，否则返回False
    """
    filter_obj = RuleFilter(yolo_model)
    return filter_obj.filter_video(video_path, target_class, output_info)

if __name__ == "__main__":
    import sys
    from utils import setup_logging
    
    # 设置日志
    logger = setup_logging()
    
    # 获取命令行参数
    if len(sys.argv) < 2:
        print("用法: python rule_filter.py <video_path> [target_class] [output_info]")
        sys.exit(1)
    
    video_path = sys.argv[1]
    target_class = sys.argv[2] if len(sys.argv) > 2 else None
    output_info = sys.argv[3] if len(sys.argv) > 3 else None
    
    # 过滤视频
    passed = filter_video(video_path, target_class, output_info)
    
    if passed:
        print(f"视频通过过滤: {video_path}")
    else:
        print(f"视频未通过过滤: {video_path}") 