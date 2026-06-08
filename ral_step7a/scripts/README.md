# Scripts

Place RA-L Step 7A helper scripts here.

## Available Scripts

### `run_sgraphs_docker.sh`

Starts S-Graphs 2.0 in the official Docker image with external odometry:

```bash
BAG_PATH=/absolute/path/to/rosbag_directory \
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

Optional environment variables:

```bash
IMAGE=sntarg/s_graphs:latest
CONTAINER_NAME=sgraphs_step7a
ROOM_SEGMENTATION=old
ENABLE_OPTIMIZATION_TIMER=false
OUTPUT_ROOT=lidar_situational_graphs/ral_step7a/runs
BAG_PATH=/absolute/path/to/rosbag_directory
CONTAINER_BAG_PATH=/bags/input
LIDAR_TOPIC=/velodyne/points
ODOM_TOPIC=/odometry
BASE_FRAME=body
ODOM_FRAME=odom
MAP_FRAME=map
```

If `OUTPUT_ROOT` is omitted, outputs are written to:

```text
lidar_situational_graphs/ral_step7a/runs
```

The default uses `room_segmentation:=old` and
`enable_optimization_timer:=false` as the frontend-comparison baseline. If the
old pipeline is validated and the paper needs the newer reasoning stack, repeat
with:

```bash
ROOM_SEGMENTATION=new ./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

### `record_sgraphs_topics.sh`

Records comparison topics from inside the S-Graphs Humble container:

```bash
./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_topics.sh
```

This must be started after `run_sgraphs_docker.sh` is running.

Optional environment variables:

```bash
CONTAINER_NAME=sgraphs_step7a
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_manual01
OUTPUT_ROOT=lidar_situational_graphs/ral_step7a/runs
CONTAINER_OUTPUT_ROOT=lidar_situational_graphs/ral_step7a/runs
```

The companion Docker launch mounts `OUTPUT_ROOT` inside the container. Keep the
same `OUTPUT_ROOT` value in both scripts if overriding it. For normal team use,
omit `OUTPUT_ROOT` and use the repo-local `runs/` default.

### `play_spot_bag_docker.sh`

Preferred path. Plays the audited Spot bag from inside the same Humble Docker
container used by S-Graphs:

```bash
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag_docker.sh
```

This must be started after `run_sgraphs_docker.sh`, which mounts the bag at
`/bags/input` by default.

Optional environment variables:

```bash
CONTAINER_NAME=sgraphs_step7a
CONTAINER_BAG_PATH=/bags/input
RATE=1.0
LIDAR_TOPIC=/velodyne/points
ODOM_TOPIC=/odometry
```

### `play_spot_bag.sh`

Plays the audited Spot bag with only the topics required by S-Graphs:

```bash
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag.sh
```

Optional environment variables:

```bash
BAG_PATH=/absolute/path/to/rosbag_directory
RATE=1.0
LIDAR_TOPIC=/velodyne/points
ODOM_TOPIC=/odometry
```

### `convert_sgraphs_planes_to_csv_docker.sh`

Converts `/s_graphs/all_map_planes` from the recorded S-Graphs bag to CSV. Run
this after a successful recording:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/convert_sgraphs_planes_to_csv_docker.sh
```

Default output:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/sgraphs_wall_planes.csv
```

The converter runs inside Docker so that the custom S-Graphs message types are
available. It exports native S-Graphs map-frame values and odom-frame values
derived from `/s_graphs/odom2map`.

### `plot_sgraphs_wall_planes.sh`

Generates quick-look diagnostic plots from the CSV:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_planes.sh
```

Default outputs:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/plots/sgraphs_wall_plane_centroids_map.png
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/plots/sgraphs_wall_plane_centroids_odom.png
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/plots/sgraphs_wall_plane_id_counts.png
```

### `summarize_sgraphs_wall_planes.sh`

Creates a per-plane-ID summary table with persistence, point support, normal
stability, and offset stability:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/summarize_sgraphs_wall_planes.sh
```

Default output:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/sgraphs_wall_plane_summary.csv
```

### `plot_sgraphs_wall_segments.sh`

Generates a segment-only diagnostic plot: persistent wall-plane IDs as
approximate top-down segments in `odom`.

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_segments.sh
```

Default output:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/plots/sgraphs_wall_plane_segments_odom.png
```

### `plot_sgraphs_lidar_overlay.sh`

Generates the preferred visual sanity check for the paper: a sampled top-down
LiDAR cloud with persistent S-Graphs wall-plane hypotheses overlaid in the same
odom-aligned coordinate system.

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_lidar_overlay.sh
```

Default output:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/plots/sgraphs_lidar_wall_overlay_odom.png
```

This figure is for qualitative validation. It should be interpreted together
with the CSV summaries and should not be treated as a quantitative score.


### `build_teste_percepcion_visual_bundle.sh`

Rebuilds the complete visual bundle for the perception bag comparison. This is
the current real-pipe evidence sequence, so it generates the normal wall-plane
comparison plots plus a dedicated `PipeLike` overlay.

```bash
./lidar_situational_graphs/ral_step7a/scripts/build_teste_percepcion_visual_bundle.sh
```

Default inputs:

```text
InGraph: runs/20260603_014722/structure_anchor_tracks.csv
S-Graphs: runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv
Bag: /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/teste_percepcion_5_0-001.mcap
```

Default outputs:

```text
comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/class_coverage_matched_dataset.png
comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_ingraph_ever_strong_all.png
comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_ingraph_ever_strong_walls.png
comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_ingraph_ever_strong_pipes.png
comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_sgraphs_persistent_walls_min5.png
comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_side_by_side_panel.png
```

The wrapper keeps `MIN_OBSERVATIONS=5` for S-Graphs because this sequence is
short; with the standard threshold of 20 observations, S-Graphs selects no wall
planes for this bag.

### `plot_class_coverage.py`

Creates a compact class-coverage bar plot from a comparison
`data/class_coverage.csv` table.

```bash
python3 lidar_situational_graphs/ral_step7a/scripts/plot_class_coverage.py \
  --csv lidar_situational_graphs/ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/class_coverage.csv \
  --output /tmp/class_coverage.png
```

### `annotate_physical_structures.py`

Interactively annotates visible physical structures on the top-down LiDAR
overlay. Use it when the paper needs a percentage-style precision/recall metric
against a LiDAR-derived physical reference rather than only cross-model
agreement.

```bash
./lidar_situational_graphs/ral_step7a/scripts/annotate_physical_structures.py \
  --dataset walls_pillars_3 \
  --bag /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3 \
  --output lidar_situational_graphs/ral_step7a/annotations/walls_pillars_3_physical_annotations.csv \
  --xlim -35 10 \
  --ylim -20 20
```

Controls:

```text
w: wall, two clicks
p: pillar, one click
i: pipe, one click
u: undo last annotation
q: finish and save
```

### `evaluate_physical_annotation_alignment.py`

Evaluates InGraph and, for walls only, S-Graphs against the physical annotation
CSV. This produces per-prediction alignment results and a compact summary with
alignment precision, instance precision, physical recall, fragmentation, and
geometric errors.

```bash
./lidar_situational_graphs/ral_step7a/scripts/evaluate_physical_annotation_alignment.py \
  --dataset walls_pillars_3 \
  --annotations lidar_situational_graphs/ral_step7a/annotations/walls_pillars_3_physical_annotations.csv \
  --ingraph-tracks lidar_situational_graphs/ral_step7a/runs/20260602_233151/structure_anchor_tracks.csv \
  --sgraphs-planes lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv \
  --sgraphs-min-observations 1 \
  --output-predictions lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions.csv \
  --output-summary lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/physical_annotation_alignment_summary.csv
```

### `plot_physical_annotation_alignment.py`

Plots the annotated physical structures and marks matched predictions in green
and unmatched predictions in red.

```bash
./lidar_situational_graphs/ral_step7a/scripts/plot_physical_annotation_alignment.py \
  --dataset walls_pillars_3 \
  --bag /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3 \
  --annotations lidar_situational_graphs/ral_step7a/annotations/walls_pillars_3_physical_annotations.csv \
  --alignment lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions.csv \
  --ingraph-tracks lidar_situational_graphs/ral_step7a/runs/20260602_233151/structure_anchor_tracks.csv \
  --sgraphs-planes lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv \
  --sgraphs-min-observations 1 \
  --output lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/physical_annotation_alignment.png
```

### `launch_rviz_docker.sh`

Launches RViz2 from the S-Graphs Docker image with the Step 7A RViz config:

```bash
./lidar_situational_graphs/ral_step7a/scripts/launch_rviz_docker.sh
```

If the Docker container cannot connect to the display, run:

```bash
xhost +local:docker
```

### `record_sgraphs_visual_topics.sh`

Records a heavier RViz-oriented bag with markers, paths, TF, and point clouds:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_visual_001 \
  ./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_visual_topics.sh
```

This bag can be large and should not be committed.

### `play_sgraphs_visual_bag_docker.sh`

Replays the visual bag from Docker/Humble:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_visual_001 \
  ./lidar_situational_graphs/ral_step7a/scripts/play_sgraphs_visual_bag_docker.sh
```

## Manual Run Order

Use three terminals:

1. Start S-Graphs:

```bash
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

2. Start recording:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_001 \
  ./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_topics.sh
```

3. Play the bag:

```bash
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag_docker.sh
```

Stop recording after playback finishes.

Then convert and plot:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/convert_sgraphs_planes_to_csv_docker.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_planes.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/summarize_sgraphs_wall_planes.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_segments.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
  ./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_lidar_overlay.sh
```

## Dataset Assumption

The Spot driver publishes `/velodyne/points` in
`sensor_origin_velodyne-point-cloud`, which is already aligned with `odom` for
this bag. Do not add a synthetic `body -> lidar` extrinsic unless a later
validation proves that S-Graphs is geometrically misinterpreting the cloud.
