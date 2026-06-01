# Interpretation Guide For The RA-L Step 7A S-Graphs Baseline

This guide explains how to interpret the current S-Graphs 2.0 artifacts for the
paper. It separates what the evidence supports from what still requires InGraph
outputs or manual annotation.

## What Was Evaluated

Dataset:

```text
spot/dinamicaStaticV0
```

S-Graphs was run with:

```text
compute_odom:=false
lidar_topic:=/velodyne/points
odom_topic:=/odometry
base_frame:=body
odom_frame:=odom
map_frame:=map
room_segmentation:=old
```

This means S-Graphs used the same external odometry source intended for the
InGraph comparison. The run is therefore appropriate as a wall-plane frontend
baseline, not as an odometry/backend comparison.

## Where The Numbers Come From

The primary source is:

```text
/s_graphs/all_map_planes
```

This topic publishes S-Graphs mapped vertical planes. Each message contains:

- `x_planes`
- `y_planes`
- persistent `plane_id`
- plane normal `nx, ny, nz`
- plane offset `d`
- support points `plane_points`
- `data_source`

The converter writes one CSV row per observed plane per message:

```text
runs/spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/sgraphs_wall_planes.csv
```

The per-ID summary is:

```text
runs/spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/sgraphs_wall_plane_summary.csv
```

## Frame Convention

S-Graphs publishes native planes in its optimized `map` frame. InGraph wall
tracks are expected to be compared in `odom`. Therefore the converter also uses:

```text
/s_graphs/odom2map
```

to export:

```text
nx_odom, ny_odom, nz_odom, d_odom
centroid_x_odom, centroid_y_odom, centroid_z_odom
```

All 540 plane-observation rows in the current run were converted to `odom`.

## Current Diagnostic Results

The current run produced:

```text
54 /s_graphs/all_map_planes messages
540 plane observations
14 unique plane IDs
540 / 540 rows converted to odom
```

Dominant IDs:

| Plane ID | Observations | Duration | Normal std | d_odom std |
|---|---:|---:|---:|---:|
| `x:3` | 54 | 89.1 s | 0.57 deg | 0.044 m |
| `y:4` | 54 | 89.1 s | 0.62 deg | 0.732 m |
| `y:13` | 49 | 73.5 s | 0.98 deg | 0.843 m |
| `x:17` | 46 | 66.5 s | 0.85 deg | 0.637 m |
| `x:23` | 43 | 56.6 s | 0.92 deg | 0.190 m |

Initial numerical interpretation:

- S-Graphs produced persistent wall-plane hypotheses.
- Several wall IDs persist for most of the sequence.
- Plane normal estimates are stable for the dominant IDs.
- Some plane offsets vary more strongly; this should be interpreted carefully
  because S-Graphs is optimizing the map frame and incrementally updating plane
  support/associations.

Visual interpretation update:

The current visual evidence does **not** show a clean correspondence between the
dominant S-Graphs wall-plane hypotheses and the main walls visible in the live
LiDAR cloud. Therefore, the current run should be described as a diagnostic
execution that produced persistent plane hypotheses, not as proof that S-Graphs
successfully reconstructed the physical wall layout of this environment.

## How To Read The Figures

Available figures:

```text
plots/sgraphs_lidar_wall_overlay_odom.png
plots/sgraphs_wall_plane_centroids_map.png
plots/sgraphs_wall_plane_centroids_odom.png
plots/sgraphs_wall_plane_id_counts.png
plots/sgraphs_wall_plane_segments_odom.png
```

Use them as follows:

- `lidar_wall_overlay_odom`: overlays sampled input LiDAR points with
  persistent S-Graphs wall-plane hypotheses. This is the main visual sanity
  check for geometric plausibility.
- `centroids_map`: shows native S-Graphs map-frame support centroids.
- `centroids_odom`: shows support centroids after conversion to odom.
- `id_counts`: shows plane persistence proxy by counting repeated observations
  per plane ID.
- `segments_odom`: approximates each persistent plane ID as a top-down wall
  segment. This helps inspect S-Graphs hypotheses, but it should not be read as
  a ground-truth wall map.

The segment plot is diagnostic: it helps humans understand where S-Graphs thinks
walls are, but metrics should be computed from CSV values, not from the image.
The overlay plot should be used before any paper claim that S-Graphs recovered
physical walls in this scene.

Important limitation:

The segment plot is a visualization of S-Graphs hypotheses, not the original
LiDAR cloud. If the segments do not align with the live cloud, the correct
interpretation is that S-Graphs hypotheses need validation/tuning before being
used as a strong wall baseline.

Current overlay interpretation:

- Some persistent S-Graphs hypotheses lie near visible linear structures.
- Several hypotheses are displaced, fragmented, or do not correspond cleanly to
  dominant wall boundaries in the sampled LiDAR cloud.
- Therefore, the present run is evidence that the baseline publishes persistent
  plane hypotheses, not evidence that the physical layout was reconstructed
  correctly.

## What Can Be Claimed Now

Supported:

> S-Graphs 2.0 was successfully executed on the Spot sequence using external
> odometry and produced persistent wall-plane hypotheses. The run provides a
> diagnostic baseline candidate for the shared wall-plane subset of the
> comparison.

Supported:

> Dominant S-Graphs wall-plane IDs persisted across many map updates and showed
> stable normal estimates, with angular standard deviations below approximately
> one degree for the most persistent planes.

Supported:

> This establishes that the comparison protocol can produce S-Graphs wall-plane
> observations in the same `odom` frame required for comparison with InGraph
> `WallLike`.

Not yet supported:

> S-Graphs correctly recovered the dominant physical walls in this Spot scene.

That claim requires visual/annotation confirmation against the LiDAR cloud.

## What Cannot Be Claimed Yet

Do not claim yet:

- InGraph outperforms S-Graphs.
- S-Graphs fails on non-wall classes.
- Each S-Graphs plane ID corresponds to a specific physical wall.
- `d_odom` variation alone proves geometric error.
- The current S-Graphs segment plot is a correct wall layout of the scene.

Why:

- InGraph `WallLike` outputs for the same bag still need to be collected or
  located.
- A physical-wall annotation or explicit matching rule is still required.
- `PillarLike` and `PipeLike` are InGraph-only coverage metrics, not direct
  S-Graphs negatives.

## Recommended Paper Framing

Use S-Graphs as the wall-plane baseline candidate:

> We compare directly against S-Graphs 2.0 on the shared wall-plane subset. The
> S-Graphs run uses external odometry and publishes persistent mapped wall
> planes, which we convert to the odometric frame for comparison with InGraph
> `WallLike` tracks.

If the visual mismatch remains after tuning/validation, phrase it conservatively:

> On this Spot industrial sequence, S-Graphs produced persistent wall-plane
> hypotheses, but visual inspection showed that several hypotheses did not align
> cleanly with the dominant structures in the LiDAR cloud. We therefore report
> S-Graphs results on the wall-plane subset with explicit annotation-based
> matching rather than assuming all persistent hypotheses correspond to physical
> walls.

Report non-wall classes separately:

> Since S-Graphs 2.0 does not explicitly expose pillar-like or pipe-like
> structural anchors, InGraph `PillarLike` and `PipeLike` are reported as
> additional structural coverage rather than as direct baseline failures.

## Next Required Evidence

1. Overlay S-Graphs wall hypotheses with an accumulated/representative LiDAR
   cloud in the same frame.
2. Check whether S-Graphs preprocessing and frame settings are appropriate for
   the Spot odom-aligned LiDAR convention.
3. Generate or locate InGraph `WallLike` outputs on the same bag.
4. Define physical wall annotations or a deterministic matching rule.
5. Compute direct wall metrics:
   - availability,
   - unique IDs per wall,
   - dominant ID ratio,
   - fragmentation,
   - duplicate coexistence,
   - normal stability,
   - offset stability.
6. Report `PillarLike` and `PipeLike` separately as InGraph-only structural
   coverage.
