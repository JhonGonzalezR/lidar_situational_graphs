#!/usr/bin/env bash
set -euo pipefail

# Play the audited Spot bag from inside the S-Graphs Humble Docker container.
# This is the preferred playback path because host ROS is Jazzy while the
# S-Graphs image is Humble.

CONTAINER_NAME="${CONTAINER_NAME:-sgraphs_step7a}"
CONTAINER_BAG_PATH="${CONTAINER_BAG_PATH:-/bags/input}"
RATE="${RATE:-1.0}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/velodyne/points}"
ODOM_TOPIC="${ODOM_TOPIC:-/odometry}"

exec docker exec -it "${CONTAINER_NAME}" bash -lc "
  source /opt/ros/humble/setup.bash
  source /workspace/install/setup.bash
  ros2 bag play '${CONTAINER_BAG_PATH}' \
    --topics '${LIDAR_TOPIC}' '${ODOM_TOPIC}' /tf /tf_static \
    --clock \
    --rate '${RATE}'
"
