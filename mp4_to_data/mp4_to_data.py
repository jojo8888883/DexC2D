import os
import shutil
import cv2
from pathlib import Path

def process_videos(object_name: str, viewpoint: str) -> bool:
    """
    处理static_videos中的视频文件，转换为所需的数据格式
    
    Args:
        object_name: 物体名称
        viewpoint: 视角名称
    
    Returns:
        bool: 是否成功找到并处理了视频文件
    """
    # 检查static_videos目录是否存在
    static_videos_dir = Path("static_videos")
    if not static_videos_dir.exists():
        print("static_videos目录不存在")
        return False
    
    # 获取所有mp4文件
    mp4_files = list(static_videos_dir.glob("*.mp4"))
    if not mp4_files:
        print("未找到mp4文件")
        return False
    
    # 创建gen_dataset目录结构
    gen_dataset_dir = Path("gen_dataset")
    gen_datas_dir = gen_dataset_dir / "gen_datas"
    gen_datas_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理每个视频文件
    for idx, video_path in enumerate(mp4_files, 1):
        # 创建目标目录
        target_dir_name = f"{object_name}_{viewpoint}_{idx:03d}"
        target_dir = gen_datas_dir / target_dir_name
        rgb_dir = target_dir / "rgb"
        target_dir.mkdir(parents=True, exist_ok=True)
        rgb_dir.mkdir(parents=True, exist_ok=True)
        
        # 读取视频并保存帧
        cap = cv2.VideoCapture(str(video_path))
        frame_idx = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 保存帧为PNG
            frame_path = rgb_dir / f"frame_{frame_idx:06d}.png"
            cv2.imwrite(str(frame_path), frame)
            frame_idx += 1
        
        cap.release()
        
        # 复制cam_K.txt
        cam_k_src = Path("capture/cam_K.txt")
        if cam_k_src.exists():
            shutil.copy2(cam_k_src, target_dir / "cam_K.txt")
        
        # 复制depth_000000.png
        depth_src = Path("capture/depth_000000.png")
        if depth_src.exists():
            shutil.copy2(depth_src, target_dir / "depth_000000.png")
        
        # 创建cad.info
        with open(target_dir / "cad.info", "w") as f:
            f.write(f"gen_dataset/models/{object_name}")
        
        # 更新meta.info
        meta_info_path = gen_dataset_dir / "meta.info"
        with open(meta_info_path, "a") as f:
            f.write(f"gen_dataset/gen_datas/{target_dir_name}\n")
        
        print(f"已处理视频 {idx}: {target_dir}")
    
    # 删除处理过的视频文件
    for video_path in mp4_files:
        video_path.unlink()
    
    return True

if __name__ == "__main__":
    # 测试代码
    process_videos("test_object", "test_viewpoint")
