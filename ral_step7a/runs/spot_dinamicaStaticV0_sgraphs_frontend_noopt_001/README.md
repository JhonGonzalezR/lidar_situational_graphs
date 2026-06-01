# S-Graphs Frontend No-Optimization Run

Run ID:

```text
spot_dinamicaStaticV0_sgraphs_frontend_noopt_001
```

This run was generated with:

```text
compute_odom:=false
enable_optimization_timer:=false
room_segmentation:=old
```

The run was first recorded under `/tmp/ral_step7a_sgraphs_runs` and then copied
to this repo-local `runs/` folder for stable analysis.

## Raw Recording

Recorded bag:

```text
sgraphs_topics/
```

Bag summary:

```text
Bag size: 931.3 MiB
Duration: 100.898972562 s
Messages: 26391
/s_graphs/all_map_planes: 32
/s_graphs/map_planes: 29
/s_graphs/graph_keyframes: 30
/s_graphs/odom2map: 0
```

Important interpretation note:

Because the optimization timer was disabled, `/s_graphs/odom2map` did not
publish transforms in this run. Therefore the CSV keeps native S-Graphs
`*_map` fields, but `*_odom` fields are unavailable. This is expected for the
current frontend/no-optimization condition and must be documented when comparing
against InGraph `WallLike`.

## Derived Files

```text
sgraphs_wall_planes.csv
sgraphs_wall_plane_summary.csv
plots/sgraphs_wall_plane_centroids_map.png
plots/sgraphs_wall_plane_id_counts.png
plots/sgraphs_wall_plane_segments_persistent_map.png
plots/sgraphs_lidar_wall_overlay_persistent_map.png
plots/sgraphs_wall_plane_segments_all_map.png
plots/sgraphs_lidar_wall_overlay_all_map.png
```

The overlay was generated with automatic frame fallback. Since odom-converted
S-Graphs fields were unavailable, the S-Graphs segments in the overlay are drawn
from native `map` fields and overlaid on the odom-aligned LiDAR cloud for visual
diagnosis.

Two plot variants are kept:

- Default persistent plots use `MIN_OBSERVATIONS=20`, so they show only the most
  persistent plane IDs.
- `*_all_map.png` plots use `MIN_OBSERVATIONS=1`, so they show all 14 S-Graphs
  plane IDs from this run.

## Checksums

```text
810b5410701e1600ad83a50511acf0b3c8f4d0d9590b7fe41aac892836c998bb  sgraphs_wall_planes.csv
a4b5ec78a7f5a6a8c6280dd674e99853a2b67786ae0d8ed29124ac3c38c0b5b9  sgraphs_wall_plane_summary.csv
d741ee59986d6d7064117ce98687e21866d197fd2ccade717904f28dd57039ed  plots/sgraphs_lidar_wall_overlay_persistent_map.png
eacf06a9a5b7859d1b8c85b09fc4db63c23aaee3ce7c1ebdf8ccd4c3e93d115b  plots/sgraphs_lidar_wall_overlay_all_map.png
e6a8530efe3183bc4f5e768ce2e144aa14ceb325ca1ef60d7e5bce10566547cd  plots/sgraphs_wall_plane_segments_persistent_map.png
84092435aa9309dd4fcb2711f938e43959ea90b115bc06d42bb304f01fa546ad  plots/sgraphs_wall_plane_segments_all_map.png
```
