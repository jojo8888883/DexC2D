"""
输入模块配置文件，定义输入模块的配置参数
"""

class InputModuleConfig:
    """输入模块配置类"""
    
    def __init__(self):
        """初始化输入模块配置参数"""
        self.prompt_file_path = "prompt.txt"
        
    def get_prompt_file_path(self):
        """获取prompt文件路径"""
        return self.prompt_file_path
        
    def set_prompt_file_path(self, path):
        """设置prompt文件路径"""
        self.prompt_file_path = path
        return self 