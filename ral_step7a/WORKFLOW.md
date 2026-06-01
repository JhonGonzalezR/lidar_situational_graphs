# RA-L Step 7A Workflow

This document is the team-facing workflow for reproducing and interpreting the
S-Graphs 2.0 frontend baseline. The scripts are portable: machine-specific
paths are supplied through environment variables, not embedded in the shell
wrappers.

Default run artifacts are written under:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/
```

This keeps analysis files close to the repo. The `runs/` directory is ignored by
git because it may contain large rosbag `.db3` recordings.

Current analysis contains two useful S-Graphs conditions, not duplicates:

```text
runs/spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/
runs/spot_dinamicaStaticV0_sgraphs_frontend_noopt_001/
```

See `COMPARISON_INDEX.md` before deleting or merging outputs.

## 1. Goal

Evaluate S-Graphs 2.0 as a baseline for the shared wall-plane frontend subset.

Direct comparison target:

```text
S-Graphs wall planes <-> InGraph WallLike
```

Not direct comparison targets:

```text
InGraph PillarLike
InGraph PipeLike
```

Those should be reported as additional structural coverage, because S-Graphs
does not explicitly expose those classes as standalone frontend outputs.

## 2. Dataset Contract

Input bag:

```bash
export BAG_PATH=/absolute/path/to/rosbag_directory
```

Required topics:

| Role | Topic | Type | Frame |
|---|---|---|---|
| LiDAR | `/velodyne/points` | `sensor_msgs/msg/PointCloud2` | `sensor_origin_velodyne-point-cloud` |
| Odometry | `/odometry` | `nav_msgs/msg/Odometry` | `odom -> body` |
| TF | `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | bag-provided |

Important convention:

The Spot driver publishes the LiDAR cloud already aligned in an odometry-like
frame. Do not add a synthetic `body -> lidar` transform unless a later
validation proves it is necessary.

## 3. Run S-Graphs

Use external odometry and disable the periodic optimization timer:

```bash
cd <repo_root>

export BAG_PATH=/absolute/path/to/rosbag_directory
RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
CONTAINER_NAME=sgraphs_step7a \
ROOM_SEGMENTATION=old \
ENABLE_OPTIMIZATION_TIMER=false \
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

Why `compute_odom:=false`:

The paper comparison should isolate structural frontend behavior. It should not
compare S-Graphs odometry/backend against InGraph frontend-only outputs.

Why `enable_optimization_timer:=false`:

The direct target is the S-Graphs frontend wall-plane output under the same
odometry condition used by InGraph. Disabling the optimization timer prevents
the periodic backend optimizer from becoming the main source of plane-map
correction during this baseline run.

## 4. Record S-Graphs Outputs

In another terminal:

```bash
cd <repo_root>

RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
CONTAINER_NAME=sgraphs_step7a \
./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_topics.sh
```

This records:

```text
/s_graphs/all_map_planes
/s_graphs/map_planes
/s_graphs/graph_keyframes
/s_graphs/markers
/s_graphs/odom2map
/s_graphs/odom_pose_corrected
/s_graphs/odom_path_corrected
/tf
/tf_static
```

## 5. Play The Input Bag

In another terminal:

```bash
cd <repo_root>

CONTAINER_NAME=sgraphs_step7a \
RATE=1.0 \
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag_docker.sh
```

Playback must happen inside Docker/Humble. Host-side playback can fail to
communicate reliably with the S-Graphs Docker environment.

## 6. Convert To CSV

After the recording finishes:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
./lidar_situational_graphs/ral_step7a/scripts/convert_sgraphs_planes_to_csv_docker.sh
```

Output:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/sgraphs_wall_planes.csv
```

This CSV contains:

- native S-Graphs map-frame plane fields;
- odom-frame fields converted through `/s_graphs/odom2map`;
- support point count;
- support centroid;
- support extents;
- persistent S-Graphs plane ID.

## 7. Summarize And Plot

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
./lidar_situational_graphs/ral_step7a/scripts/summarize_sgraphs_wall_planes.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_planes.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_wall_segments.sh

RUN_ID=spot_dinamicaStaticV0_sgraphs_frontend_noopt_001 \
./lidar_situational_graphs/ral_step7a/scripts/plot_sgraphs_lidar_overlay.sh
```

Most interpretable diagnostic visual:

```text
standard optimized run: plots/sgraphs_lidar_wall_overlay_odom.png
frontend no-opt run: plots/sgraphs_lidar_wall_overlay_persistent_map.png
```

The overlay is the preferred visual sanity check because it shows sampled
LiDAR points and S-Graphs wall-plane hypotheses in the same odom-aligned
coordinate system. The segment-only plot is useful for inspecting S-Graphs IDs,
but it does not show the observed scene.

Do not interpret this figure as a ground-truth wall map. It shows S-Graphs
hypotheses. If the segments do not align with the live LiDAR cloud, report that
as a diagnostic finding and validate/tune before using the run for final
quantitative claims.

## 8. Store Shareable Artifacts

Lightweight artifacts go in:

```text
lidar_situational_graphs/ral_step7a/runs/<RUN_ID>/
```

Recommended contents:

```text
README.md
MANIFEST.md
sgraphs_wall_planes.csv
sgraphs_wall_plane_summary.csv
plots/*.png
sgraphs_topics_metadata/metadata.yaml
```

Keep raw run recordings in `runs/<RUN_ID>/`. Do not commit raw `.db3` rosbags.
For branch review, keep only lightweight CSVs, plots, metadata, and README
files under version control.

## 9. Visual Evidence In RViz

For live RViz inspection:

```bash
xhost +SI:localuser:root
```

Then run S-Graphs, launch RViz, and play the bag:

```bash
./lidar_situational_graphs/ral_step7a/scripts/launch_rviz_docker.sh
```

If RViz cannot connect to the display, use:

```bash
xhost +local:root
```

RViz is useful for qualitative evidence, but the current most useful visual
sanity check is:

```text
standard optimized run: plots/sgraphs_lidar_wall_overlay_odom.png
frontend no-opt run: plots/sgraphs_lidar_wall_overlay_persistent_map.png
```

because it directly overlays the wall-plane IDs used in the CSV analysis on the
input LiDAR evidence.

## 10. How To Interpret The Current Run

Current diagnostic run:

```text
spot_dinamicaStaticV0_sgraphs_step7a_old_002
```

Observed:

```text
54 /s_graphs/all_map_planes messages
540 plane observations
14 unique plane IDs
540 / 540 rows converted to odom
```

Numerical interpretation:

- S-Graphs produced wall-plane baseline outputs that can be inspected and
  matched.
- Dominant plane IDs persisted across many updates.
- Dominant plane normals were stable.
- Offset variation should be interpreted carefully and compared only after
  matching to physical walls or InGraph WallLike tracks.

Visual interpretation:

- The current segment plot and RViz/cloud view must be checked together.
- The overlay plot shows that several S-Graphs hypotheses do not cleanly follow
  the dominant physical walls visible in the sampled cloud.
- If the dominant S-Graphs segments do not match the dominant walls in the
  cloud, the result is a baseline diagnostic, not a successful wall-map result.
- This may indicate S-Graphs is sensitive to this Spot industrial scene,
  preprocessing, or the odom-aligned LiDAR frame convention.

What can be claimed:

> S-Graphs produced persistent wall-plane hypotheses on the Spot sequence using
> external odometry, enabling diagnostic wall-plane outputs for comparison with
> InGraph WallLike after annotation/matching.

What cannot be claimed yet:

- InGraph is better than S-Graphs.
- Each S-Graphs ID is already assigned to a physical wall.
- Non-wall InGraph classes are direct S-Graphs failures.
- The current S-Graphs hypotheses correctly reconstruct the physical wall
  layout.

## 11. Next Step

Collect or locate InGraph `WallLike` outputs for the same bag, then define a
physical-wall annotation or deterministic matching rule.
