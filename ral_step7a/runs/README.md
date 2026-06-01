# RA-L Step 7A Runs

This directory contains the S-Graphs runs used for Step 7A analysis. It is
ignored by git because it may contain large rosbag `.db3` recordings.

## Runs

### `spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002`

Standard S-Graphs behavior with external odometry:

```text
compute_odom:=false
room_segmentation:=old
optimization timer: default S-Graphs behavior
```

Use this run as the main S-Graphs-vs-InGraph `WallLike` comparison candidate,
because it contains odom-converted plane fields derived from `/s_graphs/odom2map`.

Most relevant files:

```text
sgraphs_wall_planes.csv
sgraphs_wall_plane_summary.csv
plots/sgraphs_lidar_wall_overlay_odom.png
plots/sgraphs_wall_plane_segments_odom.png
plots/sgraphs_wall_plane_id_counts.png
README.md
MANIFEST.md
```

### `spot_dinamicaStaticV0_sgraphs_frontend_noopt_001`

Frontend/no-periodic-optimization diagnostic:

```text
compute_odom:=false
room_segmentation:=old
enable_optimization_timer:=false
```

Use this run as an ablation-style diagnostic for frontend behavior,
fragmentation, duplicate hypotheses, and persistence without periodic backend
optimization.

Important: `/s_graphs/odom2map` has zero messages in this run, so `*_odom`
fields are unavailable. Read its plots as native S-Graphs `map`-frame
hypotheses unless a separate transform assumption is justified.

Most relevant files:

```text
sgraphs_wall_planes.csv
sgraphs_wall_plane_summary.csv
plots/sgraphs_lidar_wall_overlay_all_map.png
plots/sgraphs_lidar_wall_overlay_persistent_map.png
plots/sgraphs_wall_plane_segments_all_map.png
plots/sgraphs_wall_plane_segments_persistent_map.png
plots/sgraphs_wall_plane_id_counts.png
README.md
```

## What To Commit

Commit scripts, launch files, and documentation from `ral_step7a/`.

Do not commit raw run bags:

```text
*/sgraphs_topics/*.db3
```

For paper review inside the branch, prefer committing lightweight derived
artifacts only if the team explicitly wants them in git:

```text
sgraphs_wall_plane_summary.csv
selected plots/*.png
README.md / MANIFEST.md
```

Otherwise, keep run artifacts local or share them through an external artifact
channel.
