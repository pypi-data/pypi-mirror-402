#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch undistort images using OpenCV with selectable camera params and distortion model.

Examples:
  python -m rosbag_util.undistort_images --input ./imgs --output ./undist --cam 3 --model pinhole
  python -m rosbag_util.undistort_images --input ./imgs --output ./undist --cam 3 --model fisheye --balance 0.0
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def iter_images(input_path: Path):
    if input_path.is_file():
        yield input_path
        return
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    for p in sorted(input_path.rglob("*")):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def load_camera_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: Path) -> dict:
    ext = path.suffix.lower()
    if ext == ".json":
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    if ext in (".toml", ".tml"):
        try:
            import tomllib  # type: ignore
        except ModuleNotFoundError:
            try:
                import tomli as tomllib  # type: ignore
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "TOML config requires tomli (Python < 3.11) or Python 3.11+ with tomllib"
                ) from exc
        with path.open("rb") as f:
            return tomllib.load(f)
    raise RuntimeError("Unsupported config format; use .json or .toml")


def select_camera_params(cam_id: str, config: dict):
    cams = config.get("camera_params", [])

    for c in cams:
        if str(c.get("desc")) == str(cam_id):
            return c

    try:
        cam_pose = int(cam_id)
        for c in cams:
            if int(c.get("pose")) == cam_pose:
                return c
    except ValueError:
        pass

    available = sorted([(c.get("desc"), c.get("pose")) for c in cams], key=lambda x: str(x[0]))
    raise ValueError(f"Camera id '{cam_id}' not found. Available (desc,pose): {available}")


def intrinsics_to_K(intrinsics_list):
    return np.array(intrinsics_list, dtype=np.float64).reshape(3, 3)


def undistort_pinhole(img_bgr, K, dist5, alpha=0.0):
    h, w = img_bgr.shape[:2]
    newK, roi = cv2.getOptimalNewCameraMatrix(K, dist5, (w, h), alpha, (w, h))
    map1, map2 = cv2.initUndistortRectifyMap(K, dist5, None, newK, (w, h), cv2.CV_16SC2)
    undist = cv2.remap(img_bgr, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

    x, y, rw, rh = roi
    if rw > 0 and rh > 0 and alpha == 0.0:
        undist = undist[y : y + rh, x : x + rw]
    return undist


def _to_fisheye_D(dist):
    dist = np.array(dist, dtype=np.float64).flatten()
    if dist.size == 4:
        return dist.reshape(4, 1), False
    if dist.size == 5:
        k1, k2, p1, p2, k3 = dist.tolist()
        D = np.array([k1, k2, k3, 0.0], dtype=np.float64).reshape(4, 1)
        return D, True
    raise ValueError(f"Unsupported distortion length for fisheye: {dist.size} (need 4, or 5 with fallback).")


def undistort_fisheye(img_bgr, K, dist, balance=0.0):
    h, w = img_bgr.shape[:2]
    D, used_fallback = _to_fisheye_D(dist)

    K = np.array(K, dtype=np.float64)
    newK = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
        K, D, (w, h), np.eye(3), balance=balance
    )
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(
        K, D, np.eye(3), newK, (w, h), cv2.CV_16SC2
    )
    undist = cv2.remap(img_bgr, map1, map2, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return undist, used_fallback


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="Config file path (JSON/TOML)")
    ap.add_argument("--input", help="Input image file or directory")
    ap.add_argument("--output", help="Output directory")
    ap.add_argument("--cam", help="Camera id (match desc or pose), e.g. 0/1/2/3/6/7")
    ap.add_argument(
        "--camera-config",
        default=str(Path(__file__).resolve().parent.parent / "configs" / "camera_config.json"),
        help="Camera config JSON path",
    )
    ap.add_argument(
        "--model",
        choices=["pinhole", "fisheye"],
        default="pinhole",
        help="Undistort model: pinhole (default) or fisheye",
    )
    ap.add_argument("--alpha", type=float, default=0.0, help="(pinhole only) 0=crop borders, 1=keep all")
    ap.add_argument(
        "--balance",
        type=float,
        default=0.0,
        help="(fisheye only) 0=crop more, 1=keep more FOV",
    )
    ap.add_argument("--suffix", default="_undist", help="Suffix for output filename (default _undist)")
    return ap


def parse_args(argv=None):
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config", help="Config file path (JSON/TOML)")
    config_args, _ = config_parser.parse_known_args(argv)
    defaults = {}
    if config_args.config:
        cfg_path = Path(config_args.config).expanduser().resolve()
        cfg = load_config(cfg_path)
        if not isinstance(cfg, dict):
            raise RuntimeError("Config file must contain a top-level object/dict")
        defaults.update(cfg)

    ap = build_parser()
    if defaults:
        ap.set_defaults(**defaults)
    args = ap.parse_args(argv)
    if not args.input or not args.output or not args.cam:
        ap.error("the following arguments are required: --input, --output, --cam")
    return args


def undistort_images(args) -> int:
    in_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.output).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    config_path = Path(args.camera_config).expanduser().resolve()
    cam_config = load_camera_config(config_path)
    cam = select_camera_params(args.cam, cam_config)
    K = intrinsics_to_K(cam["intrinsics"])
    dist = cam["distortion"]

    print(f"Using camera: desc={cam.get('desc')} pose={cam.get('pose')} type={cam.get('type')}")
    print(f"Resolution in calib: {cam.get('width')}x{cam.get('height')}, fps={cam.get('fps')}")
    print(f"Model: {args.model}")
    print(f"K=\n{K}")
    print(f"dist(raw)= {dist}")

    count = 0
    for img_path in iter_images(in_path):
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            print(f"[WARN] Failed to read: {img_path}")
            continue

        if args.model == "pinhole":
            dist5 = np.array(dist, dtype=np.float64).reshape(-1, 1)
            undist = undistort_pinhole(img, K, dist5, alpha=args.alpha)
        else:
            undist, used_fallback = undistort_fisheye(img, K, dist, balance=args.balance)
            if used_fallback:
                print(
                    "[WARN] fisheye selected but distortion is pinhole [k1,k2,p1,p2,k3]; "
                    "fallback used: D=[k1,k2,k3,0], p1/p2 ignored. Result is approximate."
                )

        out_name = img_path.stem + args.suffix + img_path.suffix
        out_path = out_dir / out_name
        if not cv2.imwrite(str(out_path), undist):
            print(f"[WARN] Failed to write: {out_path}")
            continue

        count += 1
        print(
            f"[OK] {img_path.name} -> {out_path.name} "
            f"(orig {img.shape[1]}x{img.shape[0]}  undist {undist.shape[1]}x{undist.shape[0]})"
        )

    print(f"Done. Processed {count} image(s). Output: {out_dir}")
    return 0


def main(argv=None):
    return undistort_images(parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
