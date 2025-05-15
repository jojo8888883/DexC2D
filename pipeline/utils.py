import logging
import os
from pathlib import Path
from datetime import datetime

# 设置日志
def setup_logging():
    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler('pipeline/pipeline.log')
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建新的运行目录
def new_run_dir(base: Path, obj: str, ver: str = None) -> Path:
    """
    创建新的运行目录
    
    Args:
        base: 基础目录路径
        obj: 对象名称
        ver: 版本号，如果为None则自动计算
        
    Returns:
        新创建的运行目录路径
    """
    # 确保基础目录存在
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    
    # 查找已存在的序列号并计算新序列号
    seq = max([int(p.name.split('_')[0]) 
               for p in base.glob('[0-9][0-9][0-9]_*')], default=-1) + 1
    
    # 如果没有提供版本号，计算同一对象的最新版本号
    if ver is None:
        existing_vers = [p.name.split('_')[-1] for p in base.glob(f'[0-9][0-9][0-9]_{obj}_*')]
        if existing_vers:
            # 假设版本号格式为nn，提取数字部分并找到最大值
            ver_nums = [int(v) for v in existing_vers if v.isdigit()]
            ver = f"{max(ver_nums, default=0) + 1:02d}"
        else:
            ver = "01"
    
    # 创建运行目录名称
    run_name = f'{seq:03d}_{obj}_{ver}'
    run_dir = base / run_name
    
    # 创建子目录
    (run_dir / 'rgb').mkdir(parents=True, exist_ok=True)
    (run_dir / 'video').mkdir(parents=True, exist_ok=True)
    
    return run_dir

# 生成 Sora 提示
def generate_prompt(obj_name, background_color, hand_gesture="握住"):
    """
    生成用于 Sora 的提示
    
    Args:
        obj_name: 物体名称
        background_color: 背景颜色
        hand_gesture: 手势描述，默认为"握住"
        
    Returns:
        生成的提示字符串
    """
    # 物体名称映射到中文（如果需要）
    obj_map = {
        "cracker_box": "饼干盒",
        "sugar_box": "糖盒",
        "tomato_soup_can": "番茄汤罐",
        # 可以根据需要添加更多映射
    }
    
    # 获取中文物体名称
    obj_cn = obj_map.get(obj_name, obj_name)
    
    # 构建提示
    prompt = f"静止镜头。一只手{hand_gesture}{obj_cn}，在{background_color}背景前展示。"
    
    return prompt

# 读取物体与CAD模型映射
def read_meta_info(meta_path):
    """
    读取meta.info文件中的对象到CAD模型映射
    
    Args:
        meta_path: meta.info文件路径
        
    Returns:
        包含映射关系的字典
    """
    meta = {}
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    parts = line.split('=')
                    if len(parts) == 2:
                        key, value = parts
                        meta[key.strip()] = value.strip()
    except FileNotFoundError:
        logging.warning(f"Meta文件未找到: {meta_path}")
    
    return meta

# 保存运行信息
def save_run_info(run_dir, info):
    """
    保存运行信息到run.info文件
    
    Args:
        run_dir: 运行目录
        info: 要保存的信息字典
    """
    with open(run_dir / 'run.info', 'w', encoding='utf-8') as f:
        for key, value in info.items():
            f.write(f"{key}={value}\n") 