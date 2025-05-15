import cv2
import numpy as np
import logging
import time
from pathlib import Path
import json

logger = logging.getLogger('pipeline')

class CameraCapture:
    """相机捕获类，支持OpenCV和行业相机"""
    
    def __init__(self, camera_id=0, use_industry_cam=False):
        """
        初始化相机捕获
        
        Args:
            camera_id: 相机ID或序列号
            use_industry_cam: 是否使用工业相机
        """
        self.camera_id = camera_id
        self.use_industry_cam = use_industry_cam
        self.cap = None
        self.cam_intrinsics = None
        
    def initialize(self):
        """初始化相机连接"""
        if self.use_industry_cam:
            try:
                # 这里应该导入工业相机SDK，例如PyCapture2
                # 根据实际使用的相机SDK修改这部分
                import PyCapture2 as pc2
                
                bus = pc2.BusManager()
                num_cams = bus.getNumOfCameras()
                
                if num_cams == 0:
                    logger.error("没有检测到工业相机")
                    return False
                
                # 使用第一个相机或指定ID的相机
                cam_idx = self.camera_id if isinstance(self.camera_id, int) else 0
                self.cap = pc2.Camera()
                self.cap.connect(bus.getCameraFromIndex(cam_idx))
                self.cap.startCapture()
                
                # 获取相机内参（仅为示例，真实场景需根据具体相机API获取）
                self.cam_intrinsics = {
                    'fx': 1000.0, 'fy': 1000.0,
                    'cx': 640.0,  'cy': 480.0
                }
                
                logger.info(f"工业相机已连接: ID={cam_idx}")
                return True
                
            except ImportError:
                logger.error("工业相机SDK未安装，将使用OpenCV摄像头")
                self.use_industry_cam = False
                return self.initialize()
                
            except Exception as e:
                logger.error(f"工业相机连接失败: {str(e)}")
                return False
        else:
            # 使用OpenCV相机
            try:
                self.cap = cv2.VideoCapture(self.camera_id)
                
                if not self.cap.isOpened():
                    logger.error(f"无法打开相机: ID={self.camera_id}")
                    return False
                
                # 设置分辨率
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                
                # 使用默认内参（仅为示例，实际应通过标定获取）
                self.cam_intrinsics = {
                    'fx': self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) * 0.8,
                    'fy': self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * 0.8,
                    'cx': self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) / 2,
                    'cy': self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) / 2
                }
                
                logger.info(f"OpenCV相机已连接: ID={self.camera_id}")
                return True
                
            except Exception as e:
                logger.error(f"OpenCV相机连接失败: {str(e)}")
                return False
    
    def capture(self):
        """捕获一帧图像"""
        if self.cap is None:
            logger.error("相机未初始化")
            return None
            
        if self.use_industry_cam:
            try:
                # 工业相机捕获（示例，需根据实际SDK修改）
                image = self.cap.retrieveBuffer()
                # 转换为OpenCV格式
                img_array = image.getData()
                img_array = np.array(img_array).reshape((image.getRows(), image.getCols()))
                frame = cv2.cvtColor(img_array, cv2.COLOR_BAYER_BG2RGB)
                return frame
            except Exception as e:
                logger.error(f"工业相机捕获失败: {str(e)}")
                return None
        else:
            # OpenCV相机捕获
            ret, frame = self.cap.read()
            if not ret:
                logger.error("OpenCV相机捕获失败")
                return None
            return frame
    
    def release(self):
        """释放相机资源"""
        if self.cap is not None:
            if self.use_industry_cam:
                try:
                    self.cap.stopCapture()
                    self.cap.disconnect()
                except Exception as e:
                    logger.error(f"释放工业相机资源失败: {str(e)}")
            else:
                self.cap.release()
            
            logger.info("相机已释放")
            self.cap = None

def save_camera_params(output_path, intrinsics):
    """
    保存相机内参到文件
    
    Args:
        output_path: 输出文件路径
        intrinsics: 内参字典，包含fx, fy, cx, cy
    """
    output_path = Path(output_path)
    
    # 保存为txt格式
    with open(output_path, 'w') as f:
        f.write(f"fx={intrinsics['fx']}\n")
        f.write(f"fy={intrinsics['fy']}\n")
        f.write(f"cx={intrinsics['cx']}\n")
        f.write(f"cy={intrinsics['cy']}\n")
    
    logger.info(f"相机内参已保存到: {output_path}")

def capture_and_save(output_dir, camera_id=0, use_industry_cam=False, mock_image=True):
    """
    捕获图像并保存图像和内参
    
    Args:
        output_dir: 输出目录
        camera_id: 相机ID
        use_industry_cam: 是否使用工业相机
        mock_image: 如果为True，则在没有相机的情况下创建模拟图像
        
    Returns:
        成功返回图像路径，失败返回None
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 如果使用模拟图像
    if mock_image:
        # 创建一个简单的模拟图像(白色背景上的灰色矩形)
        logger.info("使用模拟图像替代真实相机捕获")
        
        # 创建一个白色背景
        width, height = 640, 480
        frame = np.ones((height, width, 3), dtype=np.uint8) * 255
        
        # 添加一个灰色矩形作为"物体"
        rect_x, rect_y = width//4, height//4
        rect_w, rect_h = width//2, height//2
        frame[rect_y:rect_y+rect_h, rect_x:rect_x+rect_w] = 128
        
        # 保存图像
        image_path = output_dir / 'rgb_init.png'
        cv2.imwrite(str(image_path), frame)
        logger.info(f"已保存模拟图像到: {image_path}")
        
        # 保存相机内参
        cam_k_path = output_dir / 'cam_K.txt'
        cam_intrinsics = {
            'fx': width * 0.8,
            'fy': height * 0.8,
            'cx': width / 2,
            'cy': height / 2
        }
        save_camera_params(cam_k_path, cam_intrinsics)
        
        return image_path
    
    # 初始化相机
    camera = CameraCapture(camera_id, use_industry_cam)
    if not camera.initialize():
        logger.error("相机初始化失败")
        return None
    
    # 等待相机稳定
    logger.info("等待相机稳定...")
    time.sleep(1.0)
    
    # 捕获图像
    frame = camera.capture()
    if frame is None:
        logger.error("图像捕获失败")
        camera.release()
        return None
    
    # 保存图像
    image_path = output_dir / 'rgb_init.png'
    cv2.imwrite(str(image_path), frame)
    logger.info(f"已保存图像到: {image_path}")
    
    # 保存相机内参
    cam_k_path = output_dir / 'cam_K.txt'
    save_camera_params(cam_k_path, camera.cam_intrinsics)
    
    # 释放相机
    camera.release()
    
    return image_path

if __name__ == "__main__":
    import sys
    from utils import setup_logging
    
    # 设置日志
    logger = setup_logging()
    
    # 从命令行获取输出目录
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        output_dir = "capture_output"
    
    # 捕获图像并保存
    image_path = capture_and_save(output_dir)
    
    if image_path:
        print(f"成功捕获图像: {image_path}")
    else:
        print("图像捕获失败") 