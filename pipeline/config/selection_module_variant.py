"""
选择模块配置文件，定义选择模块的配置参数
"""

class SelectionModuleConfig:
    """选择模块配置类"""
    
    def __init__(self):
        """初始化选择模块配置参数"""
        self.settings = {
            "download_dir": "assets/temp/downloaded_videos",
            "input_dir": "assets/temp/downloaded_videos", 
            "output_dir": "assets/temp/static_videos",
            "threshold": 3,  # 光流阈值
            "sample_frames": 10  # 采样帧数
        }
        
    def get(self, key):
        """获取配置项"""
        return self.settings[key]
        
    def set(self, key, value):
        """设置配置项"""
        self.settings[key] = value
        return self
        
    def display(self):
        """显示当前配置"""
        print("选择模块配置信息:")
        for key, value in self.settings.items():
            print(f"- {key}: {value}")
        return self 