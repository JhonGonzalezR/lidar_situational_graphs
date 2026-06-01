# RA-L Step 7A: S-Graphs 2.0 Frontend Comparison Utilities

This folder contains local, paper-support utilities for the RA-L comparison
between InGraph Structure and S-Graphs 2.0.

It is intentionally separate from the upstream S-Graphs source tree. Scripts
created here should be small wrappers, loggers, or converters used to reproduce
the comparison; they should not change S-Graphs behavior unless explicitly
documented.

Start here for the team workflow:

```text
WORKFLOW.md
```

Use this interpretation guide when writing the paper:

```text
INTERPRETATION_GUIDE.md
```

Use this index to distinguish the optimized/default and no-optimization S-Graphs
conditions currently available:

```text
COMPARISON_INDEX.md
```

Use this short note for paper-facing interpretation:

```text
PAPER_INSIGHTS.md
```

## Dataset Contract

Provide the bag path through `BAG_PATH` instead of hard-coding a machine-local
path in the scripts:

```bash
export BAG_PATH=/absolute/path/to/rosbag_directory
```

Input topics:

| Role | Topic | Type | Frame |
|---|---|---|---|
| LiDAR | `/velodyne/points` | `sensor_msgs/msg/PointCloud2` | `sensor_origin_velodyne-point-cloud` |
| Odometry | `/odometry` | `nav_msgs/msg/Odometry` | `odom -> body` |
| TF | `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | bag-provided |

Important dataset-specific convention:

The Spot driver appears to emit the LiDAR cloud already aligned in an
odometry-like frame. There is no separate body-to-LiDAR extrinsic in this bag.
This should be documented in the paper protocol rather than silently corrected.

## S-Graphs Launch Contract

Use the Step 7A launch wrapper:

```bash
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

The wrapper mounts the local launch file:

```text
launch/s_graphs_frontend_comparison.launch.py
```

This launch keeps `compute_odom:=false` and sets
`enable_optimization_timer:=false` by default. That makes the S-Graphs run
closer to the frontend wall-plane comparison condition, because periodic graph
optimization is not allowed to rewrite the map before we evaluate plane
hypotheses.

## Output Topics Of Interest

Record:

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

The primary wall-plane comparison should use `/s_graphs/all_map_planes`.

## Current Runs

The two current S-Graphs conditions are stored under:

```text
runs/spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/
runs/spot_dinamicaStaticV0_sgraphs_frontend_noopt_001/
```

For what to commit to the branch:

```text
BRANCH_CHECKLIST.md
```

## Development Rules For This Folder

- Put runnable scripts under `scripts/`.
- Add a short README or usage block for every script.
- Keep scripts non-invasive: subscribe, record, convert, summarize.
- Do not modify upstream S-Graphs algorithms for the comparison baseline.
- If a script assumes the Spot odom-aligned LiDAR convention, state it in the
  script header or README.
