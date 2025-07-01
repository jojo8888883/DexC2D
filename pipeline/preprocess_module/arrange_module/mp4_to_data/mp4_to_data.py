"""
mp4_to_data.py  ——  将 static_videos 中的 MP4 批量转换为帧数据目录
"""

from pathlib import Path
from typing import List, Tuple, Optional   # ✅ 新增 Optional
import shutil
import cv2
import re
import sys
import traceback


def _next_index(gen_datas_dir: Path, prefix: str) -> int:
    """根据已有目录前缀，返回下一个可用索引（3 位，起始 1）。"""
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d{{3}})$")
    max_idx = 0
    for p in gen_datas_dir.iterdir():
        if p.is_dir():
            m = pattern.match(p.name)
            if m:
                max_idx = max(max_idx, int(m.group(1)))
    return max_idx + 1


def process_videos(
    object_name: str,
    viewpoint: str,
    videos_dir: Path = Path("static_videos"),
    dataset_root: Path = Path("gen_dataset"),
    capture_dir: Path = Path("capture"),
    exts: Optional[List[str]] = None,      # ✅ 用 Optional[List[str]]
    remove_src: bool = True,
) -> Tuple[bool, bool]:
    """
    把指定目录下的视频转成帧 + 元数据目录结构。

    Returns:
        (all_success, need_retry)
    """
    exts = exts or [".mp4"]
    if not videos_dir.exists():
        print(f"[ERROR] 视频目录 {videos_dir} 不存在")
        return False, True

    # 收集全部待处理文件
    videos: List[Path] = [
        p for ext in exts for p in videos_dir.rglob(f"*{ext}")
    ]
    if not videos:
        print("[WARN] 未找到任何视频文件")
        return False, True

    # 创建输出目录
    gen_datas_dir = dataset_root / "gen_datas"
    gen_datas_dir.mkdir(parents=True, exist_ok=True)

    meta_path = dataset_root / "meta.info"
    existing_meta = (
        set(meta_path.read_text().splitlines()) if meta_path.exists() else set()
    )
    new_meta: List[str] = []

    all_success = True
    prefix = f"{object_name}_{viewpoint}"
    next_idx = _next_index(gen_datas_dir, prefix)

    for video_path in videos:
        target_dir_name = f"{prefix}_{next_idx:03d}"
        next_idx += 1
        target_dir = gen_datas_dir / target_dir_name
        rgb_dir = target_dir / "rgb"

        try:
            # -------- 创建目录 ----------
            rgb_dir.mkdir(parents=True, exist_ok=False)

            # -------- 读取视频 ----------
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise RuntimeError("VideoCapture 打开失败")

            frame_idx = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                ok = cv2.imwrite(str(rgb_dir / f"frame_{frame_idx:06d}.png"), frame)
                if not ok:
                    raise RuntimeError(f"cv2.imwrite 写入失败（frame {frame_idx}）")
                frame_idx += 1
            cap.release()

            if frame_idx == 0:
                raise RuntimeError("视频为空或帧提取失败")

            # -------- 复制辅助文件 ----------
            for fname in ["cam_K.txt", "depth_000000.png"]:
                src = capture_dir / fname
                if src.exists():
                    shutil.copy2(src, target_dir / fname)

            # -------- 写 cad.info ----------
            (target_dir / "cad.info").write_text(f"{dataset_root}/models/{object_name}")

            new_meta.append(f"gen_dataset/gen_datas/{target_dir_name}")
            print(f"[OK] 已处理 {video_path.name} -> {target_dir}")

            if remove_src:
                video_path.unlink(missing_ok=True)

        except Exception as e:
            all_success = False
            print(f"[ERROR] 处理 {video_path} 失败: {e}")
            traceback.print_exc(file=sys.stdout)
            # 清理半成品目录
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)

    # -------- 更新 meta.info （去重） --------
    merged = sorted(existing_meta.union(new_meta))
    meta_path.write_text("\n".join(merged) + ("\n" if merged else ""))

    need_retry = not all_success
    return all_success, need_retry


if __name__ == "__main__":
    succ, retry = process_videos("test_object", "test_view")
    print(f"\n=== 处理结果：succ={succ}, need_retry={retry} ===")
