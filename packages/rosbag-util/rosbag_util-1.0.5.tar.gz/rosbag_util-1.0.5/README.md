# rosbag-util

Extract synchronized point cloud frames (and optional GPS) from one or more ROS bags.

## Install

```bash
pip install -e .
```

## Prerequisites

- ROS Python environment with `rosbag` and `sensor_msgs` available (e.g. ROS Noetic), and `source` your ROS setup.

## Usage

Single car:

```bash
rosbag-extract \
  --bags "/path/to/car1.bag" \
  --pc-topic "/perception/lidar/concated_points_cloud" \
  --gps-topic "/location/best_position" \
  --out "cooperative/car1" \
  --binary
```

Batch undistort images:

```bash
python -m rosbag_util.undistort_images \
  --input ./imgs \
  --output ./undist \
  --cam 3 \
  --model pinhole \
  --camera-config ./configs/camera_config.json
```

Using a config file:

```bash
python -m rosbag_util.undistort_images --config ./configs/undistort_config.json
```

Merge multi-car point clouds (same frame):

```bash
python -m rosbag_util.merge_multi_pcd \
  --root cooperative/zhidao \
  --cars car1 car2 car3 \
  --out_frame ref \
  --ref-car car1 \
  --yaw_only
```

Using a config file:

```bash
python -m rosbag_util.merge_multi_pcd --config ./configs/merge_multi_config.json
```

Multi car (car1 as main):

```bash
rosbag-extract \
  --bags "/path/to/car1.bag" "/path/to/car2.bag" \
  --main 0 \
  --pc-topic "/perception/lidar/concated_points_cloud" \
  --gps-topic "/location/best_position" \
  --out "cooperative/scene1" \
  --max-dt 0.300 \
  --save-workers 8 \
  --index-threads 2 \
  --binary
```

Config file (JSON):

```json
{
  "bags": ["/path/to/car1.bag", "/path/to/car2.bag"],
  "main": 0,
  "pc_topic": "/perception/lidar/concated_points_cloud",
  "gps_topic": "/location/best_position",
  "out": "cooperative/scene1",
  "max_dt": 0.3,
  "binary": true,
  "save_workers": 8,
  "index_threads": 2
}
```

```bash
rosbag-extract --config ./configs/config.json
```
