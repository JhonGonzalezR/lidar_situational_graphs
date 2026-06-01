# RViz Visual Evidence

Config:

```text
sgraphs_step7a_visual.rviz
```

This is based on the upstream S-Graphs ROS 2 RViz config and is used to inspect:

- `/s_graphs/markers`
- `/s_graphs/map_points`
- `/s_graphs/wall_points`
- `/s_graphs/odom_pose_corrected`
- TF in fixed frame `map`

## Live Inspection Workflow

Use four terminals:

1. Allow Docker to connect to the X server if needed:

```bash
xhost +local:docker
```

2. Start S-Graphs:

```bash
OUTPUT_ROOT=/tmp/ral_step7a_sgraphs_runs \
CONTAINER_NAME=sgraphs_step7a \
ROOM_SEGMENTATION=old \
./lidar_situational_graphs/ral_step7a/scripts/run_sgraphs_docker.sh
```

3. Start RViz:

```bash
./lidar_situational_graphs/ral_step7a/scripts/launch_rviz_docker.sh
```

4. Play the Spot bag inside the S-Graphs container:

```bash
CONTAINER_NAME=sgraphs_step7a \
RATE=1.0 \
./lidar_situational_graphs/ral_step7a/scripts/play_spot_bag_docker.sh
```

## Replayable Visual Evidence Workflow

Record a heavier visual bag while S-Graphs runs:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_visual_001 \
OUTPUT_ROOT=/tmp/ral_step7a_sgraphs_runs \
CONTAINER_NAME=sgraphs_step7a \
./lidar_situational_graphs/ral_step7a/scripts/record_sgraphs_visual_topics.sh
```

Then replay it with RViz:

```bash
RUN_ID=spot_dinamicaStaticV0_sgraphs_step7a_old_visual_001 \
./lidar_situational_graphs/ral_step7a/scripts/play_sgraphs_visual_bag_docker.sh
```

The visual bag includes point clouds and can be large. Do not commit it to git;
share it as an external artifact if needed.
