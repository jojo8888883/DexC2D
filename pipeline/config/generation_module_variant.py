"""
生成模块配置文件，定义生成模块的配置参数
"""

class GenerationModuleConfig:
    """生成模块配置类"""
    
    def __init__(self):
        """初始化生成模块配置参数"""
        # 坐标配置常量
        self.coordinates = {
            "add_image_button": (749, 1002),
            "local_image_button": (814, 945),
            "file_select": (642, 207),
            "prompt_input": (820, 1000),
            "view_all_videos": (1770, 193),
            "back_button": (1834, 1052),
            "download_button": (1751, 139),
            "watermark_option": (1700, 234),
            "confirm_download": (1068, 652),
            "refresh_button": (166, 93),
            "activity_button": (1843, 145),
            "latest_video_set": (1742, 204),
            "close_button": (3792, 30),
            "videos": {
                "top_left": (678, 365),
                "top_right": (1317, 353),
                "bottom_left": (688, 768),
                "bottom_right": (1311, 773)
            }
        }
        
        # 路径配置
        self.complete_image_path = "pipeline/preprocess_module/generation_module/sora_web_automation/complete.png"
        self.downloaded_videos_dir = "assets/temp/downloaded_videos"
        
    def get_coordinates(self):
        """获取坐标配置"""
        return self.coordinates
        
    def set_coordinates(self, coordinates):
        """设置坐标配置"""
        self.coordinates = coordinates
        return self
        
    def get_complete_image_path(self):
        """获取完成图像路径"""
        return self.complete_image_path
        
    def get_downloaded_videos_dir(self):
        """获取下载视频目录"""
        return self.downloaded_videos_dir 