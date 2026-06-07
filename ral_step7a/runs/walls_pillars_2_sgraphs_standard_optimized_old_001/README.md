# S-Graphs Step 7A Run: `walls_pillars_2_sgraphs_standard_optimized_old_001`

Date: 2026-06-04

This run applies the RA-L Step 7A S-Graphs workflow to the original
`walls_pillars_2` dataset, using the standard optimized `old` room-segmentation
condition represented by the requested reference result.

## Input

Original bag:

```text
bags/walls_pillars_2-20260604T020305Z-3-002/walls_pillars_2
```

The original SQLite bag is healthy, but its downloaded `metadata.yaml`
referenced a nonexistent compressed filename. A temporary hard-linked input
directory was reindexed with ROS 2 Humble before playback. The original bag was
not modified.

Input contract:

| Role | Topic | Frame |
|---|---|---|
| LiDAR | `/velodyne/points` | `sensor_origin_velodyne-point-cloud` |
| Odometry | `/odometry` | `odom -> body` |
| TF | `/tf`, `/tf_static` | bag-provided |

## Configuration

```text
compute_odom=false
room_segmentation=old
enable_optimization_timer=true
keyframe_delta=2.0
playback_rate=1.0
```

## Recorded S-Graphs Output

```text
duration: 181.062 s
messages: 35017
/s_graphs/all_map_planes: 59
/s_graphs/map_planes: 40
/s_graphs/graph_keyframes: 41
/s_graphs/odom2map: 39
/s_graphs/odom_pose_corrected: 7944
/s_graphs/odom_path_corrected: 7944
```

The raw output bag was removed after derivation to leave the requested
lightweight result structure. Its rosbag metadata is preserved under
`sgraphs_topics_metadata/`.

## Derived Results

```text
plane observations: 365
x-plane observations: 216
y-plane observations: 149
unique plane IDs: 13
point_count min/max/mean: 114 / 1377 / 471.56
map-to-odom conversion: 365 / 365 rows
persistent wall segments plotted: 9
```

The preferred visual sanity check is
`plots/sgraphs_lidar_wall_overlay_odom.png`. These plots show S-Graphs
hypotheses and must not be interpreted as ground-truth wall annotations.

