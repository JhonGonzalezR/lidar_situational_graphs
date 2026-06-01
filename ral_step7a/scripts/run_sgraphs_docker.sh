#!/usr/bin/env bash
set -euo pipefail

# Launch S-Graphs 2.0 in the official Docker image for the RA-L Step 7A
# frontend comparison. Machine-specific paths must be supplied through
# environment variables; see ../env.example.

IMAGE="${IMAGE:-sntarg/s_graphs:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-sgraphs_step7a}"
ROOM_SEGMENTATION="${ROOM_SEGMENTATION:-old}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
OUTPUT_ROOT="${OUTPUT_ROOT:-${STEP7A_ROOT}/runs}"
CONTAINER_OUTPUT_ROOT="${CONTAINER_OUTPUT_ROOT:-${OUTPUT_ROOT}}"
CONTAINER_BAG_PATH="${CONTAINER_BAG_PATH:-/bags/input}"
STEP7A_LAUNCH_DIR="${STEP7A_LAUNCH_DIR:-${STEP7A_ROOT}/launch}"
CONTAINER_STEP7A_LAUNCH_DIR="${CONTAINER_STEP7A_LAUNCH_DIR:-/ral_step7a/launch}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/velodyne/points}"
ODOM_TOPIC="${ODOM_TOPIC:-/odometry}"
BASE_FRAME="${BASE_FRAME:-body}"
ODOM_FRAME="${ODOM_FRAME:-odom}"
MAP_FRAME="${MAP_FRAME:-map}"
KEYFRAME_DELTA="${KEYFRAME_DELTA:-2.0}"
VIZ_DENSE_MAP="${VIZ_DENSE_MAP:-false}"
ENABLE_OPTIMIZATION_TIMER="${ENABLE_OPTIMIZATION_TIMER:-false}"

if [[ -z "${BAG_PATH:-}" ]]; then
  echo "ERROR: BAG_PATH is required. Example:" >&2
  echo "  export BAG_PATH=/absolute/path/to/rosbag_directory" >&2
  exit 2
fi

if [[ ! -d "${BAG_PATH}" ]]; then
  echo "ERROR: BAG_PATH does not exist or is not a directory:" >&2
  echo "  ${BAG_PATH}" >&2
  exit 2
fi

if [[ ! -f "${BAG_PATH}/metadata.yaml" ]]; then
  echo "ERROR: BAG_PATH does not look like a ROS 2 bag directory:" >&2
  echo "  ${BAG_PATH}" >&2
  echo "Expected file:" >&2
  echo "  ${BAG_PATH}/metadata.yaml" >&2
  exit 2
fi

mkdir -p "${OUTPUT_ROOT}"
chmod a+rwX "${OUTPUT_ROOT}"

exec docker run --rm -it --net=host \
  --name "${CONTAINER_NAME}" \
  -v "${OUTPUT_ROOT}:${CONTAINER_OUTPUT_ROOT}:rw" \
  -v "${BAG_PATH}:${CONTAINER_BAG_PATH}:ro" \
  -v "${STEP7A_LAUNCH_DIR}:${CONTAINER_STEP7A_LAUNCH_DIR}:ro" \
  "${IMAGE}" \
  bash -lc "
    source /opt/ros/humble/setup.bash
    source /workspace/install/setup.bash
    umask 000
    ros2 launch ${CONTAINER_STEP7A_LAUNCH_DIR}/s_graphs_frontend_comparison.launch.py \
      compute_odom:=false \
      lidar_topic:=${LIDAR_TOPIC} \
      odom_topic:=${ODOM_TOPIC} \
      base_frame:=${BASE_FRAME} \
      odom_frame:=${ODOM_FRAME} \
      map_frame:=${MAP_FRAME} \
      keyframe_delta:=${KEYFRAME_DELTA} \
      viz_dense_map:=${VIZ_DENSE_MAP} \
      room_segmentation:=${ROOM_SEGMENTATION} \
      enable_optimization_timer:=${ENABLE_OPTIMIZATION_TIMER}
  "
