#!/usr/bin/env python3
"""Capture a single aligned RGB-D frame from an Intel® RealSense™ camera.

执行流程：
1. 以 1280×720 开启彩色与深度流 → 对齐到彩色坐标系。
2. 居中裁剪左右各 100 px，得到 1080×720（3:2）。
3. 深度图经最近邻缩放到 720×480，并同步更新内参矩阵。
4. 按以下文件命名规则写入指定目录：

   ├─ color_000000.png  – 1080×720，8-bit RGB
   ├─ depth_000000.png  – 720×480，16-bit Z16（毫米）
   └─ cam_K.txt  – 3×3 相机内参（科学记数法格式）

*Stamp 默认为 UTC 毫秒级时间戳，仅用于目录命名，文件名固定为000000。
*必须通过位置参数或 --obj_id 参数指定输出目录（或生成基于对象ID的目录）。
*使用 --debug 参数可保存原始采集数据和处理后的数据。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Final, List, Optional, Tuple, Any, Dict

import cv2  # type: ignore
import numpy as np  # type: ignore
import pyrealsense2 as rs  # type: ignore
from PIL import Image

###############################################################################
# ─── 常量定义 ─────────────────────────────────────────────────────────────── #
###############################################################################

LEFT_TRIM:  Final[int]   = 100          # 左右各裁 100 px → 1080×720
RIGHT_TRIM: Final[int]   = 1280 - LEFT_TRIM
SCALE_FAC:  Final[float] = 2 / 3        # 1080×720 → 720×480
COLOR_SIZE: Final[tuple[int, int]] = (1080, 720)  # (w, h)
DEPTH_SIZE: Final[tuple[int, int]] = (720, 480)   # (w, h)
RAW_SIZE:   Final[tuple[int, int]] = (1280, 720)  # (w, h)

# YCB-Video 数据集 21 个常见物体标签
YCB_ITEMS: Final[list[str]] = [
    '002_master_chef_can', '003_cracker_box', '004_sugar_box',
    '005_tomato_soup_can', '006_mustard_bottle', '007_tuna_fish_can',
    '008_pudding_box', '009_gelatin_box', '010_potted_meat_can',
    '011_banana', '019_pitcher_base', '021_bleach_cleanser',
    '024_bowl', '025_mug', '035_power_drill', '036_wood_block',
    '037_scissors', '040_large_marker', '051_large_clamp',
    '052_extra_large_clamp', '061_foam_brick',
]
# 编号 → 完整标签映射表，如 '005' → '005_tomato_soup_can'
YCB_DICT: Final[dict[str, str]] = {item.split('_')[0]: item for item in YCB_ITEMS}

###############################################################################
# ─── 工具函数 ─────────────────────────────────────────────────────────────── #
###############################################################################

def _save_cam_K_txt(cam_K: List[float], dst: Path) -> None:
    """保存内参矩阵，使用科学记数法格式。

    Args:
        cam_K: 内参矩阵，按行排列的9个元素
        dst: 输出文件路径
    """
    lines = []
    for i in range(3):
        row = cam_K[i * 3 : (i + 1) * 3]
        lines.append(f"{' '.join(f'{x:.20e}' for x in row)}\n")
    dst.write_text("".join(lines), encoding="utf-8")


def _save_intrinsics_json(intr: Any, depth_scale: float, dst: Path) -> None:
    """保存完整内参信息为JSON格式。

    Args:
        intr: RealSense内参对象
        depth_scale: 深度比例因子
        dst: 输出文件路径
    """
    data = {
        "cam_K": [
            float(intr.fx), 0.0, float(intr.ppx),
            0.0, float(intr.fy), float(intr.ppy),
            0.0, 0.0, 1.0
        ],
        "depth_scale": float(depth_scale)
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def _save_intrinsics_simple_json(intr: Any, dst: Path) -> None:
    """保存简化内参信息为JSON格式。

    Args:
        intr: RealSense内参对象
        dst: 输出文件路径
    """
    data = {
        "intrinsics": {
            "fx": float(intr.fx),
            "fy": float(intr.fy),
            "cx": float(intr.ppx),
            "cy": float(intr.ppy)
        }
    }
    with open(dst, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _timestamp_str() -> str:
    """返回 *UTC* 毫秒级时间戳，如 20250611T031415926。"""
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")[:-3]

###############################################################################
# ─── RGBD捕获类 ───────────────────────────────────────────────────────────── #
###############################################################################

class RGBDCapture:
    """RGB-D捕获类，封装了捕获、处理和保存过程。"""
    
    def __init__(self, out_dir: Path, debug: bool = False):
        """
        初始化RGB-D捕获类。
        
        Args:
            out_dir: 输出目录路径
            debug: 是否保存原始采集数据
        """
        self.out_dir = out_dir
        self.debug = debug
        
        # 初始化变量
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        
        # 以下变量将在捕获过程中被设置
        self.color_frame: Any = None
        self.depth_frame: Any = None
        self.depth_scale: float = 1.0
        self.color_np: np.ndarray = np.array([])
        self.depth_np: np.ndarray = np.array([])
        self.color_crop: np.ndarray = np.array([])
        self.depth_crop: np.ndarray = np.array([])
        self.depth_down: np.ndarray = np.array([])
        self.intr: Any = None
        self.cam_K_raw: List[float] = []
        self.cam_K_depth: List[float] = []
    
    def configure_device(self) -> None:
        """配置设备参数。"""
        self.config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
        self.config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
    
    def start_capture(self) -> None:
        """启动采集设备。"""
        profile = self.pipeline.start(self.config)
        
        # 获取深度传感器和深度比例
        depth_sensor = profile.get_device().first_depth_sensor()
        self.depth_scale = depth_sensor.get_depth_scale()
        
        # 自动曝光缓冲
        for _ in range(30):
            self.pipeline.wait_for_frames()
    
    def capture_frames(self) -> None:
        """捕获对齐的RGB-D帧。"""
        align = rs.align(rs.stream.color)
        frames = align.process(self.pipeline.wait_for_frames())
        self.color_frame = frames.get_color_frame()
        self.depth_frame = frames.get_depth_frame()
        
        if not self.color_frame or not self.depth_frame:
            raise RuntimeError("未能获取到有效帧。")
        
        # 转为Numpy数组
        self.color_np = np.asanyarray(self.color_frame.get_data())  # (720,1280,3) uint8
        self.depth_np = np.asanyarray(self.depth_frame.get_data())  # (720,1280)   uint16
        
        # 获取内参
        self.intr = self.color_frame.profile.as_video_stream_profile().get_intrinsics()
        
        # 计算原始内参矩阵
        fx, fy = self.intr.fx, self.intr.fy
        ppx, ppy = self.intr.ppx, self.intr.ppy
        self.cam_K_raw = [
            fx, 0.0, ppx,
            0.0, fy, ppy,
            0.0, 0.0, 1.0,
        ]
    
    def process_frames(self) -> None:
        """处理捕获的帧（裁剪和下采样）。"""
        # 中心裁剪
        self.color_crop = self.color_np[:, LEFT_TRIM:RIGHT_TRIM, :]  # (720,1080,3)
        self.depth_crop = self.depth_np[:, LEFT_TRIM:RIGHT_TRIM]     # (720,1080)
        
        # 深度下采样
        self.depth_down = cv2.resize(
            self.depth_crop,
            DEPTH_SIZE,
            interpolation=cv2.INTER_NEAREST,
        )
        
        # 计算下采样后内参
        fx, fy = self.intr.fx, self.intr.fy
        ppx, ppy = self.intr.ppx - LEFT_TRIM, self.intr.ppy  # 主点平移
        fx_d, fy_d = fx * SCALE_FAC, fy * SCALE_FAC
        ppx_d, ppy_d = ppx * SCALE_FAC, ppy * SCALE_FAC
        
        self.cam_K_depth = [
            fx_d, 0.0, ppx_d,
            0.0, fy_d, ppy_d,
            0.0, 0.0, 1.0,
        ]
    
    def save_results(self) -> None:
        """保存处理结果。"""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存处理后的文件
        color_path = self.out_dir / "color_000000.png"
        depth_path = self.out_dir / "depth_000000.png"
        cam_K_path = self.out_dir / "cam_K.txt"
        
        Image.fromarray(self.color_crop).save(color_path)
        Image.fromarray(self.depth_down, mode="I;16").save(depth_path)
        _save_cam_K_txt(self.cam_K_depth, cam_K_path)
        
        print(f"[Saved] RGB   → {color_path}  ({COLOR_SIZE[0]}×{COLOR_SIZE[1]})")
        print(f"[Saved] Depth → {depth_path} ({DEPTH_SIZE[0]}×{DEPTH_SIZE[1]}, 16-bit)")
        print(f"[Saved] K_txt → {cam_K_path}")
        
        # 如果开启debug模式，保存原始数据
        if self.debug:
            # 保存原始RGB图
            raw_color_path = self.out_dir / "raw_color_000000.png"
            Image.fromarray(self.color_np).save(raw_color_path)
            
            # 保存原始深度图
            raw_depth_path = self.out_dir / "raw_depth_000000.png"
            Image.fromarray(self.depth_np, mode="I;16").save(raw_depth_path)
            
            # 保存原始内参 - 完整JSON格式
            raw_intr_path = self.out_dir / "raw_intrinsics.json"
            _save_intrinsics_json(self.intr, self.depth_scale, raw_intr_path)
            
            # 保存原始内参 - 简化JSON格式
            raw_intr_simple_path = self.out_dir / "raw_intrinsics_simple.json"
            _save_intrinsics_simple_json(self.intr, raw_intr_simple_path)
            
            # 保存原始内参矩阵 - 文本格式
            raw_cam_K_path = self.out_dir / "raw_cam_K.txt"
            _save_cam_K_txt(self.cam_K_raw, raw_cam_K_path)
            
            print(f"[Debug] Raw RGB   → {raw_color_path} ({RAW_SIZE[0]}×{RAW_SIZE[1]})")
            print(f"[Debug] Raw Depth → {raw_depth_path} ({RAW_SIZE[0]}×{RAW_SIZE[1]}, 16-bit)")
            print(f"[Debug] Raw Intr  → {raw_intr_path}")
            print(f"[Debug] Raw IntrS → {raw_intr_simple_path}")
            print(f"[Debug] Raw K_txt → {raw_cam_K_path}")
    
    def run(self) -> None:
        """执行完整的捕获、处理和保存流程。"""
        try:
            self.configure_device()
            self.start_capture()
            self.capture_frames()
            self.process_frames()
            self.save_results()
        finally:
            self.pipeline.stop()
    
    @classmethod
    def capture_single_frame(cls, out_dir: Path, *, debug: bool = False) -> None:
        """
        类方法：捕获单帧RGB-D并保存。
        
        Args:
            out_dir: 输出目录路径
            debug: 是否保存原始采集数据
        """
        capture = cls(out_dir, debug)
        capture.run()

###############################################################################
# ─── 命令行接口 ──────────────────────────────────────────────────────────── #
###############################################################################

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="采集一帧对齐 RGB-D 并保存到指定目录。",
    )
    parser.add_argument(
        "out_dir",
        type=Path,
        nargs="?",
        default=None,
        help="输出文件夹路径（若直接指定则优先使用）",
    )
    parser.add_argument(
        "--obj_id",
        type=str,
        help="YCB 物体三位编号（如 005）。若提供，将在脚本所在目录下自动创建形如 '005_tomato_soup_can_<timestamp>' 的文件夹",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="输出目录名中不使用时间戳（注意：会覆盖同名目录）",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="同时保存原始采集数据（原始RGB、深度图和内参）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])

    # 处理输出目录
    if args.out_dir is not None:
        # 如果直接提供了输出目录，优先使用
        output_dir = args.out_dir
    elif args.obj_id is not None:
        # 基于对象 ID 生成目录
        obj_id = args.obj_id.zfill(3)
        if obj_id not in YCB_DICT:
            raise SystemExit(f"未知的 obj_id: {args.obj_id}. 请使用下列之一: {', '.join(sorted(YCB_DICT))}")
        timestamp = "" if args.no_timestamp else f"_{_timestamp_str()}"
        base_dir = Path(__file__).resolve().parent
        output_dir = base_dir / f"{YCB_DICT[obj_id]}{timestamp}"
    else:
        # 没提供任何输出路径参数，报错
        raise SystemExit("必须提供输出目录的位置参数，或使用 --obj_id 指定对象编号")

    # 使用RGBDCapture类执行捕获
    RGBDCapture.capture_single_frame(output_dir, debug=args.debug)


if __name__ == "__main__":
    main()