import os
import logging
from select_mp4.selector import main as select_mp4_main
from raw2mp4.raw2mp4 import main as raw2mp4_main, set_input_image_dir as raw2mp4_set_input_dir
from capture.capture import capture_single_frame

# 全局配置
# 基础配置
OBJECT_NAME = "test"  # 当前要处理的物体名称
# prompt.txt中当前记录的物体名称，用于跟踪prompt文件的更新历史
# 如果手动修改prompt.txt，只需要同时更新CURRENT_OBJECT_IN_PROMPT即可
CURRENT_OBJECT_IN_PROMPT = "tomato soup can"  

BASE_DIR = os.path.dirname(__file__)

# 路径配置
INPUT_IMAGE_DIR = os.path.join(BASE_DIR, "capture")
PROMPT_FILE_PATH = os.path.join(BASE_DIR, "prompt.txt")
CAMERA_PARAMS_PATH = os.path.join(BASE_DIR, "capture", "cam_K.txt")

# 输出配置
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_VIDEOS_DIR = os.path.join(BASE_DIR, "static_videos")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Configuration:
    """配置管理类，用于控制全局参数"""
    
    def __init__(self):
        self.object_name = OBJECT_NAME
        self.input_image_dir = INPUT_IMAGE_DIR
        self.prompt_file_path = PROMPT_FILE_PATH
        self.camera_params_path = CAMERA_PARAMS_PATH
        self.output_dir = OUTPUT_DIR
        self.static_videos_dir = STATIC_VIDEOS_DIR
        self.current_object_in_prompt = CURRENT_OBJECT_IN_PROMPT  # 记录当前prompt中的物体名称
        
        # 初始化时创建必要的目录
        self._create_directories()
        # 验证配置
        self._validate_config()
        # 初始化raw2mp4模块的路径
        raw2mp4_set_input_dir(INPUT_IMAGE_DIR)
    
    def _create_directories(self):
        """创建必要的目录"""
        for directory in [self.input_image_dir, self.output_dir, self.static_videos_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"创建目录: {directory}")
    
    def _validate_config(self):
        """验证配置的有效性"""
        # 检查必要文件是否存在
        required_files = [
            (self.prompt_file_path, "prompt文件"),
            (self.camera_params_path, "相机参数文件")
        ]
        
        for file_path, file_desc in required_files:
            if not os.path.exists(file_path):
                logger.warning(f"{file_desc}不存在: {file_path}")
    
    def set_object_name(self, name):
        """设置物体名称并更新prompt文件"""
        self.object_name = name
        self._update_prompt()
        return self
    
    def _update_prompt(self):
        """更新prompt.txt文件中的物体名称"""
        try:
            # 读取prompt模板
            with open(self.prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_text = f.read()
            
            # 替换物体名称（使用当前记录的物体名称而非固定的字符串）
            updated_prompt = prompt_text.replace(self.current_object_in_prompt, self.object_name)
            
            # 写回文件
            with open(self.prompt_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_prompt)
            
            # 更新当前prompt中的物体名称记录
            self.current_object_in_prompt = self.object_name
                
            logger.info(f"成功更新prompt文件中的物体名称为: {self.object_name}")
            return True
        except Exception as e:
            logger.error(f"更新prompt文件时出错: {str(e)}")
            return False

# 创建全局配置实例
config = Configuration()

def main():
    """主函数"""
    logger.info("开始执行主程序")
    logger.info(f"当前配置: 物体名称={config.object_name}, 输入目录={config.input_image_dir}")
    
    # 先运行capture模块
    capture_single_frame()
    logger.info("完成图像捕获")
        
    # 再运行raw2mp4
    raw2mp4_main()
    logger.info("完成视频转换")

    # 最后运行select_mp4
    select_mp4_main()
    logger.info("完成视频选择")
    logger.info("程序执行完成")

if __name__ == "__main__":
    main()

