"""
捕获模块配置文件，定义捕获模块的配置参数
"""

class CaptureModuleConfig:
    """捕获模块配置类"""
    
    def __init__(self):
        """初始化捕获模块配置参数"""
        self.object_name = "035_power_drill"
        self.viewpoint = "above"
        self.temp_capture_dir = "assets/raw_datas/temp"
        self.saved_capture_dir = "assets/raw_datas/saved"
        self.left_trim = 100
        self.right_trim = 1280 - self.left_trim
        self.scale_fac = 2 / 3
        self.color_size = (1080, 720)
        self.depth_size = (720, 480)
        
    def get_object_name(self):
        """获取物体名称"""
        return self.object_name
        
    def set_object_name(self, name):
        """设置物体名称"""
        self.object_name = name
        return self
        
    def get_viewpoint(self):
        """获取视角"""
        return self.viewpoint
        
    def set_viewpoint(self, viewpoint):
        """设置视角"""
        self.viewpoint = viewpoint
        return self
        
    def get_temp_capture_dir(self):
        """获取临时捕获目录"""
        return self.temp_capture_dir
        
    def get_saved_capture_dir(self):
        """获取已保存捕获目录"""
        return self.saved_capture_dir 