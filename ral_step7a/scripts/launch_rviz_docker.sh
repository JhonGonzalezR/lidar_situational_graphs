#!/usr/bin/env bash
set -euo pipefail

# Launch RViz2 from the S-Graphs Docker image for visual inspection of the
# Step 7A run. Use while S-Graphs is running live, or while replaying a recorded
# visual bag.

IMAGE="${IMAGE:-sntarg/s_graphs:latest}"
DISPLAY="${DISPLAY:-:0}"
RVIZ_CONFIG="${RVIZ_CONFIG:-$(pwd)/lidar_situational_graphs/ral_step7a/rviz/sgraphs_step7a_visual.rviz}"

if [[ ! -f "${RVIZ_CONFIG}" ]]; then
  echo "RViz config not found: ${RVIZ_CONFIG}" >&2
  exit 1
fi

exec docker run --rm -it --net=host \
  -e DISPLAY="${DISPLAY}" \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v "${RVIZ_CONFIG}:/ral_step7a/sgraphs_step7a_visual.rviz:ro" \
  "${IMAGE}" \
  bash -lc "
    source /opt/ros/humble/setup.bash
    source /workspace/install/setup.bash
    rviz2 -d /ral_step7a/sgraphs_step7a_visual.rviz
  "
