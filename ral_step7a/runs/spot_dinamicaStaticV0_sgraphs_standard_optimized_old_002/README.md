# S-Graphs Step 7A Run: `spot_dinamicaStaticV0_sgraphs_step7a_old_002`

Date: 2026-05-30

Purpose: first successful diagnostic S-Graphs 2.0 run on the Spot
`dinamicaStaticV0` bag for the RA-L frontend comparison plan.

## Input Dataset

Input bag:

```text
<bag_path>/dinamicaStaticV0
```

Input contract:

| Role | Topic | Type | Frame |
|---|---|---|---|
| LiDAR | `/velodyne/points` | `sensor_msgs/msg/PointCloud2` | `sensor_origin_velodyne-point-cloud` |
| Odometry | `/odometry` | `nav_msgs/msg/Odometry` | `odom -> body` |
| TF | `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | bag-provided |

Dataset convention:

The Spot driver publishes the LiDAR cloud already aligned in an odometry-like
frame. No synthetic `body -> lidar` extrinsic was added for this run.

## S-Graphs Launch

S-Graphs was run in Docker using external odometry:

```bash
OUTPUT_ROOT=/tmp/ral_step7a_sgraphs_runs \
CONTAINER_NAME=sgraphs_step7a \
ROOM_SEGMENTATION=old \
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

Recorder:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_002 \
OUTPUT_ROOT=/tmp/ral_step7a_sgraphs_runs \
CONTAINER_NAME=sgraphs_step7a \
./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_topics.sh
```

Playback was run inside the same Humble container:

```bash
CONTAINER_NAME=sgraphs_step7a \
RATE=1.0 \
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag_docker.sh
```

## Raw Recorded Bag

Raw recorded S-Graphs output bag location at generation time:

```text
/tmp/ral_step7a_sgraphs_runs/spot_dinamicaStaticV0_sgraphs_step7a_old_002/sgraphs_topics
```

This raw `.db3` is not copied into this directory because it is about 935.5 MiB.
Use the checksum in `MANIFEST.md` if sharing it through an external artifact
channel.

Raw bag summary:

```text
Bag size: 935.5 MiB
Duration: 165.094652311 s
Messages: 26779
```

Recorded topic counts:

| Topic | Count |
|---|---:|
| `/s_graphs/all_map_planes` | 54 |
| `/s_graphs/map_planes` | 29 |
| `/s_graphs/graph_keyframes` | 30 |
| `/s_graphs/markers` | 54 |
| `/s_graphs/odom2map` | 27 |
| `/s_graphs/odom_path_corrected` | 4647 |
| `/s_graphs/odom_pose_corrected` | 4647 |
| `/tf` | 15998 |
| `/tf_static` | 1293 |

## Derived Artifacts

CSV:

```text
sgraphs_wall_planes.csv
sgraphs_wall_plane_summary.csv
```

CSV summary:

```text
rows: 540 plane observations
x-plane rows: 268
y-plane rows: 272
unique plane ids by group: 14
point_count min/max/mean: 103 / 2373 / 565.27
map-to-odom conversion: 540 / 540 rows
odom2map dt min/max/mean: 0.0 / 0.0 / 0.0 s
```

Diagnostic plots:

```text
plots/sgraphs_lidar_wall_overlay_odom.png
plots/sgraphs_wall_plane_centroids_map.png
plots/sgraphs_wall_plane_centroids_odom.png
plots/sgraphs_wall_plane_id_counts.png
plots/sgraphs_wall_plane_segments_odom.png
```

## Interpretation

This run is suitable as a diagnostic baseline candidate because S-Graphs
produced repeated wall-plane IDs, non-empty support points, and odom-frame
converted fields for all plane observations.

However, visual comparison with the live LiDAR cloud suggests that the current
S-Graphs hypotheses do not yet cleanly represent the dominant physical wall
layout of the scene. Therefore this run should not be described as a successful
wall reconstruction without additional annotation, tuning, or visual overlay
validation.

The strongest current visual evidence is
`plots/sgraphs_lidar_wall_overlay_odom.png`. It overlays sampled input LiDAR
points with persistent S-Graphs wall hypotheses. It shows that some hypotheses
are near visible structures, while others are displaced or fragmented relative
to the dominant wall boundaries.

It is not yet a final quantitative comparison, because:

- Direct matching against InGraph `WallLike` still requires either manual wall
  annotations or an explicit matching rule.
- The current map-to-odom conversion has been implemented from S-Graphs
  `/s_graphs/odom2map`, but it should be cross-checked visually or with a small
  known transform sanity test before final paper metrics.
- The current S-Graphs segment plot is a hypothesis visualization, not ground
  truth and not a physical-wall annotation.
- S-Graphs printed one optimization warning:

```text
GRAPH RETURNED A NAN WAITING AFTER OPTIMIZATION
```

The warning should be tracked, but it did not prevent plane publication in this
diagnostic run.

## Next Step

Define a minimal physical-wall annotation file and match S-Graphs plane IDs
against InGraph `WallLike` tracks in the same `odom` frame.
