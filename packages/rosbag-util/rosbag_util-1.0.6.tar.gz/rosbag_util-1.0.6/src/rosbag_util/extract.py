#!/usr/bin/env python3
import argparse
import bisect
import concurrent.futures
import io
import json
import os
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import open3d as o3d
import rosbag
import sensor_msgs.point_cloud2 as pc2


def log_line(tag: str, msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[{tag}] {ts} {msg}")


def get_stamp_sec(msg, t):
    """Prefer header.stamp if present, otherwise fall back to bag time."""
    try:
        return msg.header.stamp.to_sec()
    except Exception:
        return t.to_sec()


def msg_to_xyz_numpy(msg):
    """Convert sensor_msgs/PointCloud2 to Nx3 float32 numpy array."""
    arr = np.fromiter(
        pc2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True),
        dtype=[("x", np.float32), ("y", np.float32), ("z", np.float32)],
    )
    if arr.size == 0:
        return np.empty((0, 3), dtype=np.float32)
    xyz = np.vstack((arr["x"], arr["y"], arr["z"])).T
    return xyz.astype(np.float32, copy=False)


def save_pcd(xyz: np.ndarray, path: str, binary: bool = True):
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64, copy=False))
    o3d.io.write_point_cloud(path, pcd, write_ascii=not binary, compressed=binary)


def topic_to_name(topic: str) -> str:
    name = topic.strip("/") or "camera"
    name = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    return name


def save_image_msg(msg, path_base: str) -> str:
    # CompressedImage: decode and save as PNG
    if hasattr(msg, "format") and hasattr(msg, "data"):
        data = bytes(getattr(msg, "data", b""))
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(data))
            out_path = f"{path_base}.png"
            img.save(out_path, format="PNG")
            return out_path
        except Exception:
            out_path = f"{path_base}.bin"
            with open(out_path, "wb") as f:
                f.write(data)
            meta_path = f"{path_base}.json"
            meta = {"format": getattr(msg, "format", ""), "type": "compressed"}
            save_json(meta, meta_path)
            return out_path

    encoding = (msg.encoding or "").lower()
    height = int(getattr(msg, "height", 0))
    width = int(getattr(msg, "width", 0))
    data = bytes(getattr(msg, "data", b""))

    if encoding in ("rgb8", "bgr8"):
        arr = np.frombuffer(data, dtype=np.uint8)
        if arr.size != height * width * 3:
            raise ValueError("Image data size mismatch for rgb/bgr8")
        arr = arr.reshape((height, width, 3))
        if encoding == "bgr8":
            arr = arr[:, :, ::-1]
        out_path = f"{path_base}.ppm"
        with open(out_path, "wb") as f:
            header = f"P6\n{width} {height}\n255\n".encode("ascii")
            f.write(header)
            f.write(arr.tobytes())
        return out_path

    if encoding == "mono8":
        arr = np.frombuffer(data, dtype=np.uint8)
        if arr.size != height * width:
            raise ValueError("Image data size mismatch for mono8")
        out_path = f"{path_base}.pgm"
        with open(out_path, "wb") as f:
            header = f"P5\n{width} {height}\n255\n".encode("ascii")
            f.write(header)
            f.write(arr.tobytes())
        return out_path

    out_path = f"{path_base}.bin"
    with open(out_path, "wb") as f:
        f.write(data)
    meta_path = f"{path_base}.json"
    meta = {
        "encoding": encoding,
        "height": height,
        "width": width,
        "step": int(getattr(msg, "step", 0)),
    }
    save_json(meta, meta_path)
    return out_path


def rosmsg_to_dict(msg):
    """Convert a ROS message to a JSON-serializable dict."""
    if msg is None:
        return None
    if isinstance(msg, (bool, int, float, str)):
        return msg
    if isinstance(msg, (bytes, bytearray)):
        return list(msg)
    if isinstance(msg, (list, tuple)):
        return [rosmsg_to_dict(x) for x in msg]
    if hasattr(msg, "__slots__"):
        out = {}
        for field in msg.__slots__:
            out[field] = rosmsg_to_dict(getattr(msg, field))
        return out
    return str(msg)


def save_json(obj: dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def save_frame(
    stamp_ms: int,
    t_main: float,
    car_ids: List[str],
    out_dirs: Dict[str, Tuple[str, str, Dict[Tuple[str, ...], str]]],
    matches_pc: Dict[int, Tuple[float, float, object]],
    matches_gps: Dict[int, Tuple[float, float, object]],
    matches_cam: Dict[Tuple[str, ...], Dict[int, Tuple[float, float, object, str]]],
    gps_topic: str,
    camera_groups: List[List[str]],
    binary: bool,
):
    for i, cid in enumerate(car_ids):
        pcd_dir, gps_dir, cam_dirs = out_dirs[cid]
        out_pc = os.path.join(pcd_dir, f"{stamp_ms}.pcd")
        _, _, pc_msg = matches_pc[i]
        xyz = msg_to_xyz_numpy(pc_msg)
        save_pcd(xyz, out_pc, binary=binary)

        if gps_topic:
            out_gps = os.path.join(gps_dir, f"{stamp_ms}.json")
            dt_gps, t_gps, gps_msg = matches_gps[i]
            gps_dict = rosmsg_to_dict(gps_msg)
            gps_dict["_sync_meta"] = {
                "ref_pc_time": t_main,
                "gps_time": t_gps,
                "dt_to_ref_ms": round(dt_gps * 1000.0, 3),
            }
            save_json(gps_dict, out_gps)

        if camera_groups:
            for group in camera_groups:
                cam_dir = cam_dirs[tuple(group)]
                out_base = os.path.join(cam_dir, f"{stamp_ms}")
                _, _, cam_msg, _used_topic = matches_cam[tuple(group)][i]
                save_image_msg(cam_msg, out_base)


def build_time_index(bag_path: str, topic: str):
    times, msgs = [], []
    with rosbag.Bag(bag_path, "r") as bag:
        for _, msg, t in bag.read_messages(topics=[topic]):
            times.append(get_stamp_sec(msg, t))
            msgs.append(msg)
    return times, msgs


def nearest_msg(times, msgs, target_t):
    if not times:
        return None, None, None
    idx = bisect.bisect_left(times, target_t)
    cand = []
    if idx < len(times):
        cand.append(idx)
    if idx > 0:
        cand.append(idx - 1)

    best_dt, best_time, best_msg = None, None, None
    for j in cand:
        dt = abs(times[j] - target_t)
        if best_dt is None or dt < best_dt:
            best_dt, best_time, best_msg = dt, times[j], msgs[j]
    return best_dt, best_time, best_msg


@dataclass
class BagIndex:
    pc_times: List[float]
    pc_msgs: List
    gps_times: List[float]
    gps_msgs: List
    cam_times: Dict[str, List[float]]
    cam_msgs: Dict[str, List]


def ensure_dirs(*dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def build_bag_index(
    bag_path: str,
    pc_topic: str,
    gps_topic: Optional[str],
    camera_topics: List[str],
    profile: bool = False,
) -> BagIndex:
    if profile:
        t0 = time.perf_counter()
    pc_times, pc_msgs = build_time_index(bag_path, pc_topic)
    if profile:
        dt = time.perf_counter() - t0
        log_line("PROFILE", f"Indexed {len(pc_times)} msgs on {pc_topic} in {dt:.2f}s")
    if gps_topic:
        if profile:
            t0 = time.perf_counter()
        gps_times, gps_msgs = build_time_index(bag_path, gps_topic)
        if profile:
            dt = time.perf_counter() - t0
            log_line("PROFILE", f"Indexed {len(gps_times)} msgs on {gps_topic} in {dt:.2f}s")
    else:
        gps_times, gps_msgs = [], []
    cam_times = {}
    cam_msgs = {}
    for topic in camera_topics:
        if profile:
            t0 = time.perf_counter()
        times, msgs = build_time_index(bag_path, topic)
        if profile:
            dt = time.perf_counter() - t0
            log_line("PROFILE", f"Indexed {len(times)} msgs on {topic} in {dt:.2f}s")
        cam_times[topic] = times
        cam_msgs[topic] = msgs
    return BagIndex(
        pc_times=pc_times,
        pc_msgs=pc_msgs,
        gps_times=gps_times,
        gps_msgs=gps_msgs,
        cam_times=cam_times,
        cam_msgs=cam_msgs,
    )


def load_config(path: str) -> dict:
    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    if ext in (".toml", ".tml"):
        # Python 3.11+ -> tomllib
        # Python <=3.10 -> tomli
        try:
            import tomllib  # type: ignore
        except ModuleNotFoundError:
            try:
                import tomli as tomllib  # type: ignore
            except ModuleNotFoundError as exc:
                raise RuntimeError(
                    "TOML config requires tomli (Python < 3.11) "
                    "or Python 3.11+ with tomllib"
                ) from exc

        with open(path, "rb") as f:
            return tomllib.load(f)

    raise RuntimeError("Unsupported config format; use .json or .toml")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="Path to JSON/TOML config file")
    parser.add_argument("--bags", nargs="+", help="Bag paths (one or more)")
    parser.add_argument("--car-ids", nargs="*", help="Optional car IDs (same count as bags)")
    parser.add_argument("--main", type=int, default=0, help="Main car index in --bags (default 0)")
    parser.add_argument("--pc-topic", default="/perception/lidar/concated_points_cloud")
    parser.add_argument("--gps-topic", default="/location/best_position")
    parser.add_argument("--camera-topics", nargs="*", help="Optional camera topics (can be multiple)")
    parser.add_argument("--out", default="cooperative", help="Output root directory")
    parser.add_argument("--max-dt", type=float, default=0.300, help="Max time diff in seconds")
    parser.add_argument("--max-frames", type=int, default=-1, help="Export at most N matched frames; -1 for all")
    parser.add_argument("--binary", action="store_true", help="Write PCD as binary_compressed")
    parser.add_argument("--save-workers", type=int, default=4, help="Worker threads for saving outputs")
    parser.add_argument("--index-threads", type=int, default=0, help="Threads for indexing bags (0=auto)")
    parser.add_argument("--profile", action="store_true", help="Print timing information")
    return parser


def parse_args(argv: Optional[List[str]] = None):
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config", help="Path to JSON/TOML config file")
    config_args, _ = config_parser.parse_known_args(argv)

    defaults = {}
    if config_args.config:
        config = load_config(config_args.config)
        if not isinstance(config, dict):
            raise RuntimeError("Config file must contain a top-level object/dict")
        defaults.update(config)

    parser = build_parser()
    if defaults:
        parser.set_defaults(**defaults)
    args = parser.parse_args(argv)
    if not args.bags:
        parser.error("the following arguments are required: --bags")
    return args


def extract(args_or_argv=None) -> int:
    args = parse_args(args_or_argv) if not isinstance(args_or_argv, argparse.Namespace) else args_or_argv
    t_start = time.perf_counter()
    bags = args.bags
    if args.main < 0 or args.main >= len(bags):
        raise SystemExit("--main index out of range for --bags")
    if args.car_ids:
        if len(args.car_ids) != len(bags):
            raise SystemExit("--car-ids length must match --bags length")
        car_ids = args.car_ids
    else:
        car_ids = [f"car{i + 1}" for i in range(len(bags))]

    gps_topic = args.gps_topic.strip() if args.gps_topic else ""
    camera_topics = [t for t in (args.camera_topics or []) if t.strip()]

    def camera_topic_group(topic: str) -> Tuple[str, List[str]]:
        if "/image_slave/" in topic:
            preferred = topic.replace("/image_slave/", "/image/")
            fallback = topic
        elif "/image/" in topic:
            preferred = topic
            fallback = topic.replace("/image/", "/image_slave/")
        else:
            preferred = topic
            fallback = topic
        if preferred == fallback:
            return preferred, [preferred]
        return preferred, [preferred, fallback]

    camera_group_map: Dict[str, List[str]] = {}
    preferred_order: List[str] = []
    for t in camera_topics:
        preferred, group = camera_topic_group(t)
        if preferred not in camera_group_map:
            camera_group_map[preferred] = group
            preferred_order.append(preferred)

    camera_groups = [camera_group_map[k] for k in preferred_order]
    camera_group_names = {tuple(g): topic_to_name(g[0]) for g in camera_groups}
    flat_camera_topics = []
    for group in camera_groups:
        for t in group:
            if t not in flat_camera_topics:
                flat_camera_topics.append(t)

    out_dirs = {}
    for cid in car_ids:
        pcd_dir = os.path.join(args.out, cid, "pcd")
        gps_dir = os.path.join(args.out, cid, "gps")
        cam_dirs = {}
        ensure_dirs(pcd_dir, gps_dir)
        for group in camera_groups:
            name = camera_group_names[tuple(group)]
            cam_dir = os.path.join(args.out, cid, "camera", name)
            ensure_dirs(cam_dir)
            cam_dirs[tuple(group)] = cam_dir
        out_dirs[cid] = (pcd_dir, gps_dir, cam_dirs)

    log_line("INFO", f"Main bag: {bags[args.main]}")
    log_line("INFO", f"Bags: {len(bags)} | Cars: {', '.join(car_ids)}")

    bag_indexes = {}
    index_workers = args.index_threads or min(4, len(bags))

    def index_one(i_bag):
        i, bag_path = i_bag
        log_line("INFO", f"Index bag{i + 1}: {bag_path}")
        if args.profile:
            t0 = time.perf_counter()
        idx = build_bag_index(bag_path, args.pc_topic, gps_topic, flat_camera_topics, profile=args.profile)
        if args.profile:
            dt = time.perf_counter() - t0
            log_line("PROFILE", f"Indexed bag{i + 1} in {dt:.2f}s")
        return i, idx

    with concurrent.futures.ThreadPoolExecutor(max_workers=index_workers) as executor:
        futures = [executor.submit(index_one, (i, bag_path)) for i, bag_path in enumerate(bags)]
        for fut in concurrent.futures.as_completed(futures):
            i, idx = fut.result()
            if not idx.pc_times:
                raise RuntimeError(f"No pointcloud messages found in bag{i + 1} on {args.pc_topic}")
            if gps_topic and not idx.gps_times:
                    log_line("WARN", f"No GPS messages found in bag{i + 1} on {gps_topic}")
            if camera_groups:
                for group in camera_groups:
                    if not any(idx.cam_times.get(t) for t in group):
                        pref = group[0]
                        log_line("WARN", f"No camera messages found in bag{i + 1} on {pref} (or fallback)")
            bag_indexes[i] = idx

    t_index_end = time.perf_counter()
    matched = 0
    saved = 0
    scanned = 0
    failure_counts = {}
    save_time_s = 0.0

    def record_save_error(err: Exception):
        failure_counts["save_error"] = failure_counts.get("save_error", 0) + 1
        log_line("WARN", f"Save failed: {err}")

    main_idx = bag_indexes[args.main]
    max_in_flight = max(1, max(1, args.save_workers) * 4)
    pending = deque()

    def consume_future(fut):
        nonlocal saved
        nonlocal save_time_s
        try:
            result = fut.result()
            if args.profile and isinstance(result, float):
                save_time_s += result
            saved += 1
            if saved % 20 == 0:
                log_line("INFO", f"Saved {saved} frames")
        except Exception as exc:
            record_save_error(exc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.save_workers)) as executor:
        for pc_main_msg, t_main in zip(main_idx.pc_msgs, main_idx.pc_times):
            scanned += 1
            stamp_ms = int(round(t_main * 1000.0))
            fail_reason = None

            # match pointclouds for all bags
            matches_pc = {args.main: (0.0, t_main, pc_main_msg)}
            for i, idx in bag_indexes.items():
                if i == args.main:
                    continue
                dt_pc, t_pc, pc_msg = nearest_msg(idx.pc_times, idx.pc_msgs, t_main)
                if dt_pc is None or dt_pc > args.max_dt:
                    msg = "No candidate" if dt_pc is None else f"nearest_dt={dt_pc*1000:.1f}ms"
                    log_line(
                        "WARN",
                        f"PC{i + 1} no match <= {args.max_dt*1000:.0f}ms for t={t_main:.6f}s ({msg})",
                    )
                    fail_reason = f"pc{i + 1}_no_match"
                    break
                matches_pc[i] = (dt_pc, t_pc, pc_msg)
            if fail_reason:
                failure_counts[fail_reason] = failure_counts.get(fail_reason, 0) + 1
                continue

            # match gps for all bags if topic provided
            matches_gps = {}
            if gps_topic:
                for i, idx in bag_indexes.items():
                    dt_gps, t_gps, gps_msg = nearest_msg(idx.gps_times, idx.gps_msgs, t_main)
                    if dt_gps is None or dt_gps > args.max_dt:
                        msg = "No candidate" if dt_gps is None else f"nearest_dt={dt_gps*1000:.1f}ms"
                        log_line(
                            "WARN",
                            f"GPS{i + 1} no match <= {args.max_dt*1000:.0f}ms for t={t_main:.6f}s ({msg})",
                        )
                        fail_reason = f"gps{i + 1}_no_match"
                        break
                    matches_gps[i] = (dt_gps, t_gps, gps_msg)
                if fail_reason:
                    failure_counts[fail_reason] = failure_counts.get(fail_reason, 0) + 1
                    continue

            # match camera for all bags if topics provided
            matches_cam = {}
            if camera_groups:
                for group in camera_groups:
                    topic_matches = {}
                    for i, idx in bag_indexes.items():
                        best = None
                        used_topic = None
                        for t in group:
                            times = idx.cam_times.get(t, [])
                            msgs = idx.cam_msgs.get(t, [])
                            dt_cam, t_cam, cam_msg = nearest_msg(times, msgs, t_main)
                            if dt_cam is None or dt_cam > args.max_dt:
                                continue
                            best = (dt_cam, t_cam, cam_msg)
                            used_topic = t
                            break
                        if best is None:
                            msg = "No candidate"
                            log_line(
                                "WARN",
                                f"CAM{i + 1} {group[0]} no match <= {args.max_dt*1000:.0f}ms "
                                f"for t={t_main:.6f}s ({msg})",
                            )
                            fail_reason = f"cam{i + 1}_{camera_group_names[tuple(group)]}_no_match"
                            break
                        topic_matches[i] = (best[0], best[1], best[2], used_topic)
                    if fail_reason:
                        break
                    matches_cam[tuple(group)] = topic_matches
                if fail_reason:
                    failure_counts[fail_reason] = failure_counts.get(fail_reason, 0) + 1
                    continue

            # save outputs for each car (parallel)
            if args.save_workers <= 1:
                try:
                    if args.profile:
                        t0 = time.perf_counter()
                    save_frame(
                        stamp_ms,
                        t_main,
                        car_ids,
                        out_dirs,
                        matches_pc,
                        matches_gps,
                        matches_cam,
                        gps_topic,
                        camera_groups,
                        args.binary,
                    )
                    if args.profile:
                        save_time_s += time.perf_counter() - t0
                    saved += 1
                    if saved % 20 == 0:
                        log_line("INFO", f"Saved {saved} frames")
                except Exception as exc:
                    record_save_error(exc)
            else:
                if args.profile:
                    def timed_save():
                        t0 = time.perf_counter()
                        save_frame(
                            stamp_ms,
                            t_main,
                            car_ids,
                            out_dirs,
                            matches_pc,
                            matches_gps,
                            matches_cam,
                            gps_topic,
                            camera_groups,
                            args.binary,
                        )
                        return time.perf_counter() - t0
                    fut = executor.submit(timed_save)
                else:
                    fut = executor.submit(
                        save_frame,
                        stamp_ms,
                        t_main,
                        car_ids,
                        out_dirs,
                        matches_pc,
                        matches_gps,
                        matches_cam,
                        gps_topic,
                        camera_groups,
                        args.binary,
                    )
                pending.append(fut)
                if len(pending) >= max_in_flight:
                    consume_future(pending.popleft())

            matched += 1
            if args.max_frames > 0 and matched >= args.max_frames:
                break

        while pending:
            consume_future(pending.popleft())

    t_end = time.perf_counter()
    log_line("DONE", f"Scanned main pointcloud frames: {scanned}")
    log_line("DONE", f"Matched frames               : {matched}")
    log_line("DONE", f"Saved frames                 : {saved}")
    failed = sum(failure_counts.values())
    log_line("DONE", f"Failed frames              : {failed}")
    for reason in sorted(failure_counts.keys()):
        log_line("DONE", f"Failure reason: {reason} -> {failure_counts[reason]}")
    for cid in car_ids:
        pcd_dir, gps_dir, cam_dirs = out_dirs[cid]
        log_line("DONE", f"{cid} pcd -> {os.path.abspath(pcd_dir)}")
        if gps_topic:
            log_line("DONE", f"{cid} gps -> {os.path.abspath(gps_dir)}")
        for group in camera_groups:
            pref = group[0]
            log_line("DONE", f"{cid} cam {pref} -> {os.path.abspath(cam_dirs[tuple(group)])}")

    if args.profile:
        log_line("PROFILE", f"Indexing time: {t_index_end - t_start:.2f}s")
        log_line("PROFILE", f"Total time: {t_end - t_start:.2f}s")
        if save_time_s:
            log_line("PROFILE", f"Save time (sum of save_frame): {save_time_s:.2f}s")

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    return extract(argv)


if __name__ == "__main__":
    raise SystemExit(main())
