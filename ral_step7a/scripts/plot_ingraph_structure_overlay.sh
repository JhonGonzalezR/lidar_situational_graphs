#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${RUN_ID:-20260601_195923}"
STEP7A_ROOT="${STEP7A_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
INGRAPH_OUTPUT_RUN_DIR="${INGRAPH_OUTPUT_RUN_DIR:-${STEP7A_ROOT}/runs/ingraph_${RUN_ID}}"
DEFAULT_TRACKS_CSV="${INGRAPH_OUTPUT_RUN_DIR}/input/structure_anchor_tracks.csv"
if [[ ! -f "${DEFAULT_TRACKS_CSV}" ]]; then
  DEFAULT_TRACKS_CSV="${STEP7A_ROOT}/${RUN_ID}/structure_anchor_tracks.csv"
fi
TRACKS_CSV="${TRACKS_CSV:-${DEFAULT_TRACKS_CSV}}"
OUTPUT_DIR="${OUTPUT_DIR:-${INGRAPH_OUTPUT_RUN_DIR}/plots}"
OUTPUT_PNG="${OUTPUT_PNG:-${OUTPUT_DIR}/ingraph_lidar_overlay_confirmed_wall_pillar.png}"
SUMMARY_MD="${SUMMARY_MD:-${INGRAPH_OUTPUT_RUN_DIR}/README_confirmed_wall_pillar.md}"
MODE="${MODE:-confirmed}"
SNAPSHOT="${SNAPSHOT:-latest}"
CLASSES="${CLASSES:-wall_like,pillar_like,pipe_like}"
MIN_AGE="${MIN_AGE:-1}"
HIDE_NON_WALL="${HIDE_NON_WALL:-false}"
LIDAR_TOPIC="${LIDAR_TOPIC:-/velodyne/points}"
PAPER="${PAPER:-true}"
SHOW_IDS="${SHOW_IDS:-true}"
PAPER_XLIM="${PAPER_XLIM:--35 10}"
PAPER_YLIM="${PAPER_YLIM:--20 20}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mplconfig}"

if [[ -z "${BAG_PATH:-}" ]]; then
  echo "ERROR: BAG_PATH is required. Example:" >&2
  echo "  export BAG_PATH=/absolute/path/to/rosbag_directory" >&2
  exit 2
fi

mkdir -p "${OUTPUT_DIR}" "${MPLCONFIGDIR}"
export MPLCONFIGDIR

ARGS=(
  --tracks "${TRACKS_CSV}"
  --bag "${BAG_PATH}"
  --topic "${LIDAR_TOPIC}"
  --output "${OUTPUT_PNG}"
  --summary "${SUMMARY_MD}"
  --mode "${MODE}"
  --snapshot "${SNAPSHOT}"
  --classes "${CLASSES}"
  --min-age "${MIN_AGE}"
)

if [[ -n "${TITLE:-}" ]]; then
  ARGS+=(--title "${TITLE}")
fi

if [[ "${PAPER}" == "true" || "${PAPER}" == "1" ]]; then
  ARGS+=(--paper --xlim ${PAPER_XLIM} --ylim ${PAPER_YLIM})
fi

if [[ "${SHOW_IDS}" == "true" || "${SHOW_IDS}" == "1" ]]; then
  ARGS+=(--show-ids)
fi

if [[ "${HIDE_NON_WALL}" == "true" || "${HIDE_NON_WALL}" == "1" ]]; then
  ARGS+=(--hide-non-wall)
fi

exec python3 "$(dirname "$0")/plot_ingraph_structure_overlay.py" "${ARGS[@]}"
