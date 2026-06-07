# S-Graphs Step 7A Run: `walls_pillars_3_sgraphs_standard_optimized_old_001`

Date: 2026-06-04

This run applies the RA-L Step 7A S-Graphs workflow to the original
`walls_pillars_3` dataset, using the standard optimized `old` room-segmentation
condition represented by the requested reference result.

## Input

Original bag:

```text
bags/walls_pillars_3-20260604T015907Z-3-002/walls_pillars_3
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
duration: 162.498 s
messages: 39122
/s_graphs/all_map_planes: 53
/s_graphs/map_planes: 32
/s_graphs/graph_keyframes: 33
/s_graphs/odom2map: 33
/s_graphs/odom_pose_corrected: 7050
/s_graphs/odom_path_corrected: 7050
```

The raw output bag was removed after derivation to leave the requested
lightweight result structure. Its rosbag metadata is preserved under
`sgraphs_topics_metadata/`.

## Derived Results

```text
plane observations: 546
x-plane observations: 184
y-plane observations: 362
unique plane IDs: 15
point_count min/max/mean: 108 / 2980 / 600.92
map-to-odom conversion: 546 / 546 rows
persistent wall segments plotted: 12
```

The run printed one transient `GRAPH RETURNED A NAN WAITING AFTER OPTIMIZATION`
warning after loop closure. Optimization continued, and plane publication and
all requested artifacts completed successfully.

The preferred visual sanity check is
`plots/sgraphs_lidar_wall_overlay_odom.png`. These plots show S-Graphs
hypotheses and must not be interpreted as ground-truth wall annotations.

