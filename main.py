import os
from select_mp4.selector import main as select_mp4_main
from raw2mp4.raw2mp4 import main as raw2mp4_main, set_input_image_dir as raw2mp4_set_input_dir

class Configuration:
    """配置管理类，用于控制全局参数"""
    
    def __init__(self):
        self.object_name = "tomato soup can"  # 默认物体名称
        self.input_image_dir = r"F:\24-25spring\DEXHGR\cap2raw\left_highest\tomato_soup_can"  # 默认图像目录
        self.prompt_file_path = os.path.join(os.path.dirname(__file__), "prompt.txt")
        self.current_object_in_prompt = "tomato soup can"  # 记录当前prompt中的物体名称
    
    def set_object_name(self, name):
        """设置物体名称并更新prompt文件"""
        self.object_name = name
        self._update_prompt()
        return self
    
    def set_input_image_dir(self, directory):
        """设置输入图像目录"""
        self.input_image_dir = directory
        raw2mp4_set_input_dir(directory)  # 更新raw2mp4模块中的路径
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
                
            print(f"成功更新prompt文件中的物体名称为: {self.object_name}")
            return True
        except Exception as e:
            print(f"更新prompt文件时出错: {str(e)}")
            return False

# 创建全局配置实例
config = Configuration()

def set_object_name(name):
    """设置物体名称的全局接口"""
    return config.set_object_name(name)

def set_input_image_dir(directory):
    """设置输入图像目录的全局接口"""
    return config.set_input_image_dir(directory)

def main(object_name=None, input_image_dir=None):
    """
    主函数
    
    参数:
        object_name: 物体名称，会更新prompt.txt
        input_image_dir: 输入图像目录路径
    """
    # 如果提供了参数，则更新配置
    if object_name:
        config.set_object_name(object_name)
    
    if input_image_dir:
        config.set_input_image_dir(input_image_dir)
        
    # 先运行raw2mp4
    raw2mp4_main()

    # 再运行select_mp4
    select_mp4_main()

if __name__ == "__main__":
    # 示例：使用默认配置运行
    main("tomato_soup_can",r"F:\24-25spring\DEXHGR\cap2raw\left_highest\tomato_soup_can")

