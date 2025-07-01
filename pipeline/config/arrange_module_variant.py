"""
排列模块配置文件，定义排列模块的配置参数
"""

class ArrangeModuleConfig:
    """排列模块配置类"""
    
    def __init__(self):
        """初始化排列模块配置参数"""
        self.static_videos_dir = "assets/temp/static_videos"
        self.dataset_root = "assets/gen_datasets"
        self.gen_datas_dir = "assets/gen_datasets/gen_datas"
        self.models_dir = "assets/gen_datasets/models"
        self.meta_info_path = "assets/gen_datasets/meta.info"
        self.remove_source_videos = True
        
    def get_static_videos_dir(self):
        """获取静态视频目录"""
        return self.static_videos_dir
        
    def set_static_videos_dir(self, directory):
        """设置静态视频目录"""
        self.static_videos_dir = directory
        return self
        
    def get_dataset_root(self):
        """获取数据集根目录"""
        return self.dataset_root
        
    def set_dataset_root(self, directory):
        """设置数据集根目录"""
        self.dataset_root = directory
        return self
        
    def get_gen_datas_dir(self):
        """获取生成数据目录"""
        return self.gen_datas_dir
        
    def get_models_dir(self):
        """获取模型目录"""
        return self.models_dir
        
    def get_meta_info_path(self):
        """获取元信息路径"""
        return self.meta_info_path
        
    def get_remove_source_videos(self):
        """获取是否移除源视频设置"""
        return self.remove_source_videos
        
    def set_remove_source_videos(self, remove):
        """设置是否移除源视频"""
        self.remove_source_videos = remove
        return self 