#!/usr/bin/env bash
set -euo pipefail

# Play an input bag with only the topics required by S-Graphs Step 7A.

RATE="${RATE:-1.0}"
ROS_LOG_DIR="${ROS_LOG_DIR:-/tmp/ros_logs}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/velodyne/points}"
ODOM_TOPIC="${ODOM_TOPIC:-/odometry}"

if [[ -z "${BAG_PATH:-}" ]]; then
  echo "ERROR: BAG_PATH is required. Example:" >&2
  echo "  export BAG_PATH=/absolute/path/to/rosbag_directory" >&2
  exit 2
fi

if [[ ! -f "${BAG_PATH}/metadata.yaml" ]]; then
  echo "ERROR: BAG_PATH does not look like a ROS 2 bag directory:" >&2
  echo "  ${BAG_PATH}" >&2
  exit 2
fi

mkdir -p "${ROS_LOG_DIR}"
export ROS_LOG_DIR

exec ros2 bag play "${BAG_PATH}" \
  --topics "${LIDAR_TOPIC}" "${ODOM_TOPIC}" /tf /tf_static \
  --clock \
  --rate "${RATE}"
