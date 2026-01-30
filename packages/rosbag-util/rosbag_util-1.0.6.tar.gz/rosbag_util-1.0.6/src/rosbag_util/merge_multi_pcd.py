#!/usr/bin/env python3
import argparse
import os
import json
from pathlib import Path
from typing import List

import numpy as np
import open3d as o3d


def euler_to_R_zyx(roll, pitch, yaw):
    cr, sr = np.cos(roll), np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw), np.sin(yaw)

    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]], dtype=np.float64)
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]], dtype=np.float64)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]], dtype=np.float64)
    return Rz @ Ry @ Rx


def build_T_world_from_gps(gps, gauss_scale=0.001, angle_scale_deg=0.01, yaw_only=True):
    x = float(gps["gaussX"]) * gauss_scale
    y = float(gps["gaussY"]) * gauss_scale
    z = float(gps.get("height", 0.0))

    yaw_deg = float(gps["azimuth"]) * angle_scale_deg
    pitch_deg = float(gps["pitch"]) * angle_scale_deg
    roll_deg = float(gps["roll"]) * angle_scale_deg

    yaw = np.deg2rad(yaw_deg)
    pitch = np.deg2rad(pitch_deg)
    roll = np.deg2rad(roll_deg)

    if yaw_only:
        pitch = 0.0
        roll = 0.0

    R = euler_to_R_zyx(roll, pitch, yaw)
    T = np.eye(4, dtype=np.float64)
    T[:3, :3] = R
    T[:3, 3] = np.array([x, y, z], dtype=np.float64)
    return T


def load_json_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
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


def list_pcd_files(folder: str):
    if not os.path.isdir(folder):
        return []
    files = [f for f in os.listdir(folder) if f.lower().endswith(".pcd")]
    files.sort()
    return files


def merge_frame(
    frame_name: str,
    root: str,
    cars: List[str],
    ref_car: str,
    out_frame: str,
    gauss_scale: float,
    angle_scale: float,
    yaw_only: bool,
):
    gps = {}
    pcd = {}
    for car in cars:
        gps_path = os.path.join(root, car, "gps", frame_name.replace(".pcd", ".json"))
        pcd_path = os.path.join(root, car, "pcd", frame_name)
        if not os.path.exists(gps_path) or not os.path.exists(pcd_path):
            return None, f"missing_{car}"
        gps[car] = load_json_file(gps_path)
        pcd[car] = o3d.io.read_point_cloud(pcd_path)
        if pcd[car].is_empty():
            return None, f"empty_{car}"

    T_w = {}
    for car in cars:
        T_w[car] = build_T_world_from_gps(
            gps[car], gauss_scale=gauss_scale, angle_scale_deg=angle_scale, yaw_only=yaw_only
        )

    if out_frame == "world":
        merged = o3d.geometry.PointCloud()
        for car in cars:
            pc = o3d.geometry.PointCloud(pcd[car])
            pc.transform(T_w[car])
            merged += pc
        return merged, None

    T_ref_w = np.linalg.inv(T_w[ref_car])
    merged = o3d.geometry.PointCloud(pcd[ref_car])
    for car in cars:
        if car == ref_car:
            continue
        T_ref_car = T_ref_w @ T_w[car]
        pc = o3d.geometry.PointCloud(pcd[car])
        pc.transform(T_ref_car)
        merged += pc
    return merged, None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", help="Config file path (JSON/TOML)")
    ap.add_argument("--root", default="cooperative/zhidao")
    ap.add_argument("--cars", nargs="+", help="Car IDs under root")
    ap.add_argument("--merge", default="merge_multi")
    ap.add_argument("--out_frame", choices=["world", "ref"], default="ref")
    ap.add_argument("--ref-car", help="Reference car ID for out_frame=ref (default: first in --cars)")
    ap.add_argument("--gauss_scale", type=float, default=0.001)
    ap.add_argument("--angle_scale", type=float, default=0.01)
    ap.add_argument("--yaw_only", action="store_true")
    ap.add_argument("--max_frames", type=int, default=-1)
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
    if not args.cars:
        ap.error("the following arguments are required: --cars")
    return args


def merge_multi_pcd(args) -> int:

    out_frame = "world" if args.out_frame == "world" else "ref"
    merge_dir = os.path.join(args.root, args.merge)
    os.makedirs(merge_dir, exist_ok=True)

    ref_car = args.ref_car or args.cars[0]
    if ref_car not in args.cars:
        raise SystemExit("--ref-car must be one of --cars")
    ref_pcd_dir = os.path.join(args.root, ref_car, "pcd")
    pcd_files = list_pcd_files(ref_pcd_dir)
    if not pcd_files:
        raise RuntimeError(f"No .pcd found in {ref_pcd_dir}")

    processed = merged_ok = skipped = 0
    reason_counts = {}

    for fname in pcd_files:
        if args.max_frames > 0 and processed >= args.max_frames:
            break
        processed += 1

        merged, reason = merge_frame(
            fname,
            args.root,
            args.cars,
            ref_car,
            out_frame,
            args.gauss_scale,
            args.angle_scale,
            args.yaw_only,
        )
        if merged is None:
            skipped += 1
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
            print(f"[SKIP] {fname}: {reason}")
            continue

        out_path = os.path.join(merge_dir, fname)
        o3d.io.write_point_cloud(out_path, merged)
        merged_ok += 1
        if merged_ok % 20 == 0:
            print(f"[OK] merged {merged_ok} latest={out_path}")

    print(f"[DONE] processed={processed}, merged_ok={merged_ok}, skipped={skipped}")
    for reason in sorted(reason_counts.keys()):
        print(f"[DONE] skip_reason {reason} -> {reason_counts[reason]}")
    print(f"[DONE] merge_dir = {os.path.abspath(merge_dir)}")
    return 0


def main(argv=None):
    return merge_multi_pcd(parse_args(argv))


if __name__ == "__main__":
    main()
