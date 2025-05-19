import os, json, datetime
import numpy as np
import pyrealsense2 as rs
import cv2
from PIL import Image

# ---------- 常量 ----------
LEFT_TRIM  = 100                 # 裁掉左右各 100 → 1080×720
RIGHT_TRIM = 1280 - LEFT_TRIM
SCALE_FAC  = 2 / 3               # 1080×720 → 720×480（深度）
COLOR_SIZE = (1080, 720)         # (w, h)
DEPTH_SIZE = (720,  480)         # (w, h)

# 获取capture文件夹的路径
CAPTURE_DIR = os.path.dirname(os.path.abspath(__file__))

def save_cam_K_txt(cam_K, output_path):
    """将相机内参矩阵保存为指定格式的txt文件
    
    Args:
        cam_K: 相机内参矩阵（3x3）
        output_path: 输出文件路径
    """
    with open(output_path, 'w') as f:
        for i in range(3):
            row = cam_K[i*3:(i+1)*3]
            # 使用科学计数法格式化数字，保持20位精度
            formatted_row = [f"{x:.20e}" for x in row]
            # 添加行号（从1开始）
            f.write(f"{i+1} {' '.join(formatted_row)}\n")

def capture_single_frame():
    # ① RealSense
    pipeline = rs.pipeline()
    cfg      = rs.config()
    cfg.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
    cfg.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
    profile  = pipeline.start(cfg)

    # ② 自动曝光缓冲
    for _ in range(30):
        pipeline.wait_for_frames()

    # ③ 对齐帧
    align  = rs.align(rs.stream.color)
    frames = align.process(pipeline.wait_for_frames())
    color_frame, depth_frame = frames.first(rs.stream.color), frames.first(rs.stream.depth)

    # ④ numpy
    color_np = np.asanyarray(color_frame.get_data())          # (720,1280,3) uint8
    depth_np = np.asanyarray(depth_frame.get_data())          # (720,1280)   uint16

    # ⑤ 中心裁剪 → 3:2
    color_crop = color_np[:, LEFT_TRIM:RIGHT_TRIM, :]         # (720,1080,3)
    depth_crop = depth_np[:, LEFT_TRIM:RIGHT_TRIM]            # (720,1080)

    # ⑥ 深度下采样 → 720×480
    depth_down = cv2.resize(
        depth_crop,
        DEPTH_SIZE,                     # (w, h)
        interpolation=cv2.INTER_NEAREST
    )                                   # (480,720)

    # ⑦ 更新内参
    intr      = color_frame.profile.as_video_stream_profile().get_intrinsics()
    fx, fy    = intr.fx, intr.fy
    ppx, ppy  = intr.ppx - LEFT_TRIM, intr.ppy          # 主点先平移
    fx_d, fy_d      = fx * SCALE_FAC, fy * SCALE_FAC    # 然后缩放
    ppx_d, ppy_d    = ppx * SCALE_FAC, ppy * SCALE_FAC

    cam_K_depth = [                                   # ← 3×3 矩阵
        fx_d, 0.0,  ppx_d,
        0.0,  fy_d, ppy_d,
        0.0,  0.0,  1.0
    ]

    # ⑧ 路径
    stamp = 000000                                         # 你之前固定为 1，如需时间戳可改回来
    color_path = os.path.join(CAPTURE_DIR, "color_000000.png")
    depth_path = os.path.join(CAPTURE_DIR, "depth_000000.png")
    cam_K_txt_path = os.path.join(CAPTURE_DIR, "cam_K.txt")

    # ⑨ 保存
    Image.fromarray(color_crop).save(color_path)
    Image.fromarray(depth_down, mode='I;16').save(depth_path)

    # 保存相机内参矩阵为txt格式
    save_cam_K_txt(cam_K_depth, cam_K_txt_path)

    print(f"[Saved] RGB   → {color_path}  (1080×720)")
    print(f"[Saved] Depth → {depth_path} (720×480, 16-bit)")
    print(f"[Saved] K_txt → {cam_K_txt_path}")

    pipeline.stop()

if __name__ == "__main__":
    capture_single_frame()
