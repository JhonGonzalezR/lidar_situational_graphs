# S-Graphs Step 7A Run: `teste_percepcion_5_0_sgraphs_standard_optimized_old_001`

This run applies the RA-L Step 7A S-Graphs workflow to:

```text
bags/teste_percepcion_5_0-001.mcap
```

The original MCAP was not modified. Because the S-Graphs Humble container does
not provide MCAP playback support, a minimal SQLite input bag was derived with
only the required topics:

```text
lidar_situational_graphs/ral_step7a/runs/teste_percepcion_5_0_sqlite_input/
```

Input topics:

```text
/velodyne/points
/odometry
/tf
/tf_static
```

Configuration:

```text
compute_odom=false
room_segmentation=old
enable_optimization_timer=true
keyframe_delta=2.0
playback_rate=1.0
```

Recorded S-Graphs output:

```text
duration: 59.100 s
messages: 13146
/s_graphs/all_map_planes: 18
/s_graphs/map_planes: 14
/s_graphs/graph_keyframes: 15
/s_graphs/odom2map: 13
/s_graphs/odom_pose_corrected: 2531
/s_graphs/odom_path_corrected: 2531
```

Derived results:

```text
plane observations: 62
unique plane IDs: 6
odom-converted rows: 62 / 62
persistent planes with observations>=20: 0
short-sequence selected planes with observations>=5: 6
```

Important interpretation:

The standard `observations>=20` persistence threshold selects no S-Graphs planes
because this sequence is short and the maximum S-Graphs plane observation count
is 18. For the perception comparison, `observations>=5` is used as an adaptive
short-sequence threshold. This must be stated explicitly in paper text.

