#!/usr/bin/env python3
"""Capture a single aligned RGB‑D frame from an Intel® RealSense™ camera.

执行流程：
1. 以 1280×720 开启彩色与深度流 → 对齐到彩色坐标系。
2. 居中裁剪左右各 100 px，得到 1080×720（3:2）。
3. 深度图经最近邻缩放到 720×480，并同步更新内参矩阵。
4. 按以下文件命名规则写入 *同级目录下的“captures”文件夹*：

   ├─ color_<stamp>.png  – 1080×720，8‑bit RGB
   ├─ depth_<stamp>.png  – 720×480，16‑bit Z16（毫米）
   └─ cam_K_<stamp>.txt  – 3×3 相机内参（COLMAP 格式）

*Stamp 默认为 UTC 毫秒级时间戳，可用 --no-timestamp 固定为 000000。
*如需更改输出子目录，只需改动全局常量 ``OUTPUT_SUBDIR``。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path
from typing import Final, List

import cv2  # type: ignore
import numpy as np  # type: ignore
import pyrealsense2 as rs  # type: ignore
from PIL import Image

###############################################################################
# ─── 常量定义 ─────────────────────────────────────────────────────────────── #
###############################################################################

# ⚠️ 只需在此处修改文件夹名即可改变输出位置
OUTPUT_SUBDIR: Final[str] = "035_power_drill"  # ← 输出文件夹（相对脚本所在目录）
DEFAULT_OUT_DIR: Final[Path] = Path(__file__).resolve().parent / OUTPUT_SUBDIR

LEFT_TRIM:  Final[int]   = 100          # 左右各裁 100 px → 1080×720
RIGHT_TRIM: Final[int]   = 1280 - LEFT_TRIM
SCALE_FAC:  Final[float] = 2 / 3        # 1080×720 → 720×480
COLOR_SIZE: Final[tuple[int, int]] = (1080, 720)  # (w, h)
DEPTH_SIZE: Final[tuple[int, int]] = (720, 480)   # (w, h)

###############################################################################
# ─── 工具函数 ─────────────────────────────────────────────────────────────── #
###############################################################################

def _save_cam_K_txt(cam_K: List[float], dst: Path) -> None:
    """按 COLMAP 格式保存 3×3 内参矩阵。"""
    lines = []
    for i in range(3):
        row = cam_K[i * 3 : (i + 1) * 3]
        lines.append(f"{i + 1} {' '.join(f'{x:.20e}' for x in row)}\n")
    dst.write_text("".join(lines), encoding="utf-8")


def _timestamp_str() -> str:
    """返回 *UTC* 毫秒级时间戳，如 20250611T031415926。"""
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S%f")[:-3]

###############################################################################
# ─── 主逻辑 ──────────────────────────────────────────────────────────────── #
###############################################################################

def capture_single_frame(out_dir: Path, *, use_timestamp: bool = True) -> None:
    """采集一帧 RGB‑D 并写入 *out_dir*。"""
    stamp = _timestamp_str() if use_timestamp else "000000"

    # 1) 设备初始化
    pipeline = rs.pipeline()
    config   = rs.config()
    config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)
    config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)

    try:
        pipeline.start(config)

        # 2) 自动曝光缓冲
        for _ in range(30):
            pipeline.wait_for_frames()

        # 3) 获取对齐帧
        align  = rs.align(rs.stream.color)
        frames = align.process(pipeline.wait_for_frames())
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()
        if not color_frame or not depth_frame:
            raise RuntimeError("未能获取到有效帧。")

        # 4) 转为 Numpy
        color_np = np.asanyarray(color_frame.get_data())  # (720,1280,3) uint8
        depth_np = np.asanyarray(depth_frame.get_data())  # (720,1280)   uint16

        # 5) 中心裁剪
        color_crop = color_np[:, LEFT_TRIM:RIGHT_TRIM, :]  # (720,1080,3)
        depth_crop = depth_np[:, LEFT_TRIM:RIGHT_TRIM]     # (720,1080)

        # 6) 深度下采样
        depth_down = cv2.resize(
            depth_crop,
            DEPTH_SIZE,
            interpolation=cv2.INTER_NEAREST,
        )

        # 7) 计算下采样后内参
        intr = color_frame.profile.as_video_stream_profile().get_intrinsics()
        fx, fy   = intr.fx, intr.fy
        ppx, ppy = intr.ppx - LEFT_TRIM, intr.ppy  # 主点平移
        fx_d, fy_d   = fx * SCALE_FAC, fy * SCALE_FAC
        ppx_d, ppy_d = ppx * SCALE_FAC, ppy * SCALE_FAC

        cam_K_depth = [
            fx_d, 0.0,  ppx_d,
            0.0,  fy_d, ppy_d,
            0.0,  0.0,  1.0,
        ]

        # 8) 生成输出路径
        out_dir.mkdir(parents=True, exist_ok=True)
        color_path = out_dir / f"color_{stamp}.png"
        depth_path = out_dir / f"depth_{stamp}.png"
        cam_K_path = out_dir / f"cam_K_{stamp}.txt"

        # 9) 保存文件
        Image.fromarray(color_crop).save(color_path)
        Image.fromarray(depth_down, mode="I;16").save(depth_path)
        _save_cam_K_txt(cam_K_depth, cam_K_path)

        print(f"[Saved] RGB   → {color_path}  ({COLOR_SIZE[0]}×{COLOR_SIZE[1]})")
        print(f"[Saved] Depth → {depth_path} ({DEPTH_SIZE[0]}×{DEPTH_SIZE[1]}, 16‑bit)")
        print(f"[Saved] K_txt → {cam_K_path}")

    finally:
        pipeline.stop()

###############################################################################
# ─── 命令行接口 ──────────────────────────────────────────────────────────── #
###############################################################################

def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="采集一帧对齐 RGB‑D 并保存到同级 ‘captures’ 子目录。",
    )
    parser.add_argument(
        "out_dir",
        type=Path,
        nargs="?",
        default=DEFAULT_OUT_DIR,
        help=f"输出文件夹（默认: {DEFAULT_OUT_DIR}）",
    )
    parser.add_argument(
        "--no-timestamp",
        action="store_true",
        help="使用固定文件名 000000（覆盖同名文件）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    capture_single_frame(args.out_dir, use_timestamp=not args.no_timestamp)


if __name__ == "__main__":
    main()