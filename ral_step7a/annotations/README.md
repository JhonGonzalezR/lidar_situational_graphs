# Physical Annotation Alignment

This folder stores manual LiDAR-overlay annotations used to evaluate geometric
precision against visible physical structures. These annotations are not a
survey-grade map. They are a LiDAR-derived reference created from the same
top-down point-cloud overlay used for visual inspection.

## Why This Exists

The current Step 7A comparison already measures cross-model agreement:

```text
InGraph WallLike <-> S-Graphs wall planes
```

That agreement is useful, but it is not physical precision. To report a
precision percentage, each method must be compared against an explicit reference
of the physical structures visible in the scene.

This workflow provides that reference:

```text
LiDAR overlay -> manual physical annotations -> prediction/reference matching
```

## Annotation Format

```csv
dataset,structure_id,structure_class,x0,y0,x1,y1,cx,cy,radius_m,notes
walls_pillars_3,wall_01,wall,-10.0,-4.0,-2.0,-4.0,,,,main wall
walls_pillars_3,pillar_01,pillar,,,,,1.2,-5.0,,visible compact support
walls_pillars_3,pipe_01,pipe,,,,,1.1,0.6,,vertical pipe
```

Rules:

- `wall` uses two endpoints: `x0,y0,x1,y1`.
- `pillar` uses a center point: `cx,cy`.
- `pipe` currently uses a center point: `cx,cy`, because the observed PipeLike
  anchors are vertical pipes in top-down projection.

## Interactive Annotation

Short wrappers:

```bash
cd /home/jhon/comparation_ra-l/lidar_situational_graphs

./ral_step7a/annotations/annotate_walls_pillars_3.sh
./ral_step7a/annotations/annotate_teste_percepcion_5_0.sh
```

## Multi-Window LiDAR Overlays

The annotation plot samples the beginning of each bag. For visual inspection
across the full trajectory, generate four evenly spaced LiDAR overlays:

```bash
cd /home/jhon/comparation_ra-l/lidar_situational_graphs

./ral_step7a/annotations/build_overlay_windows_walls_pillars_3.sh
./ral_step7a/annotations/build_overlay_windows_teste_percepcion_5_0.sh
```

To fuse selected windows into a single color-coded overlay:

```bash
./ral_step7a/annotations/fuse_overlay_windows_walls_pillars_3.sh
./ral_step7a/annotations/fuse_overlay_windows_teste_percepcion_5_0.sh
```

Defaults:

```text
walls_pillars_3: windows 2 and 3
teste_percepcion_5_0: windows 1, 2, and 3
```

The short annotation and evaluation wrappers use these fused overlays by
default. For `walls_pillars_3`, the default view is intentionally cropped to
the current region of interest:

```text
x > -30 m
y > -15 m
```

These wrappers write:

```text
comparisons/<dataset>_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_window_01.png
comparisons/<dataset>_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_window_02.png
comparisons/<dataset>_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_window_03.png
comparisons/<dataset>_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_window_04.png
comparisons/<dataset>_ingraph_vs_sgraphs/plots_overlay/lidar_overlay_windows_summary.csv
```

Use these images to decide where physical walls, pillars, and pipes are visible
before editing the annotation CSV. The summary CSV records the exact message
range used by each overlay.

After annotating, run:

```bash
./ral_step7a/annotations/evaluate_walls_pillars_3.sh
./ral_step7a/annotations/evaluate_teste_percepcion_5_0.sh
```

The evaluation wrappers write:

```text
comparisons/<dataset>_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions.csv
comparisons/<dataset>_ingraph_vs_sgraphs/data/physical_annotation_alignment_summary.csv
comparisons/<dataset>_ingraph_vs_sgraphs/plots/physical_annotation_alignment.png
```

For S-Graphs, the defaults are:

```text
walls_pillars_3: MIN_OBS=1
teste_percepcion_5_0: MIN_OBS=5
```

Override with, for example:

```bash
MIN_OBS=20 ./ral_step7a/annotations/evaluate_walls_pillars_3.sh
```

Example for `walls_pillars_3`:

```bash
cd /home/jhon/comparation_ra-l/lidar_situational_graphs

./ral_step7a/scripts/annotate_physical_structures.py \
  --dataset walls_pillars_3 \
  --bag /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3 \
  --output ral_step7a/annotations/walls_pillars_3_physical_annotations.csv \
  --xlim -35 10 \
  --ylim -20 20
```

Controls:

```text
w -> annotate wall with two clicks
b -> annotate LiDAR-observable WallLike boundary/mesh with two clicks
p -> annotate pillar with one click
i -> annotate pipe with one click
u -> undo last annotation
q -> finish and write CSV
```

Use `b` for structures that are not solid architectural walls but behave as
stable LiDAR-observable planar boundaries, such as a mesh fence. These are
stored as `structure_class=wall_like_boundary`.

Evaluation supports two wall scopes:

```text
solid_wall_only: only structure_class=wall annotations count as wall GT.
walllike_boundary: structure_class=wall and wall_like_boundary count as WallLike GT.
```

The consolidated results wrapper generates both scopes for
`teste_percepcion_5_0`:

```bash
./ral_step7a/annotations/build_physical_annotation_results.sh
```

## Evaluate Precision

Example for `walls_pillars_3`:

```bash
./ral_step7a/scripts/evaluate_physical_annotation_alignment.py \
  --dataset walls_pillars_3 \
  --annotations ral_step7a/annotations/walls_pillars_3_physical_annotations.csv \
  --ingraph-tracks ral_step7a/runs/20260602_233151/structure_anchor_tracks.csv \
  --sgraphs-planes ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv \
  --sgraphs-min-observations 1 \
  --output-predictions ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions.csv \
  --output-summary ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/physical_annotation_alignment_summary.csv
```

Use `--sgraphs-min-observations 1` when evaluating everything S-Graphs
published. Use `20` when evaluating only the persistent subset used in the
current comparison tables.

Default matching gates:

```text
wall angle <= 8 deg
wall perpendicular offset <= 0.40 m
wall projected gap <= 1.00 m
wall projected overlap ratio >= 0.25
pillar XY error <= 0.55 m
pipe XY error <= 0.35 m
```

Outputs:

```text
physical_annotation_alignment_predictions.csv
physical_annotation_alignment_summary.csv
```

The summary contains:

```text
alignment_precision = aligned_predictions / total_predictions
instance_precision = matched_annotations / total_predictions
physical_recall = matched_annotations / total_annotations
fragmentation_index = aligned_predictions per matched physical structure
median angular/offset/XY errors
```

Interpretation:

- `alignment_precision` measures how many predictions are geometrically
  compatible with a physical annotation. If five anchors fall on the same
  physical wall and satisfy the geometric gates, all five count as aligned.
- `instance_precision` is stricter and penalizes duplicated structural
  identities: if five predictions align with the same physical wall, only one
  physical wall is recovered as a unique instance and the remaining aligned
  predictions appear as fragmentation.
- `physical_recall` measures how many annotated physical structures are
  recovered by at least one prediction.

## Plot Alignment Result

```bash
./ral_step7a/scripts/plot_physical_annotation_alignment.py \
  --dataset walls_pillars_3 \
  --bag /home/jhon/ingraph_ws/src/multi_robot_spatial/data/datasets/rosbags/bags_articulo/walls_pillars_3 \
  --annotations ral_step7a/annotations/walls_pillars_3_physical_annotations.csv \
  --alignment ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/physical_annotation_alignment_predictions.csv \
  --ingraph-tracks ral_step7a/runs/20260602_233151/structure_anchor_tracks.csv \
  --sgraphs-planes ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv \
  --sgraphs-min-observations 1 \
  --output ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/physical_annotation_alignment.png \
  --xlim -35 10 \
  --ylim -20 20
```

Matched predictions are plotted in green; unmatched predictions are plotted in
red. Black segments/points are the physical annotations.

## Paper Wording

Recommended wording:

```text
We manually annotated visible physical structures in the top-down LiDAR overlay
and evaluated each frontend hypothesis against this LiDAR-derived reference.
We report alignment precision, instance precision, physical recall, and
fragmentation. Alignment precision measures whether predictions are
geometrically correct with respect to visible structures; instance precision and
fragmentation quantify whether the same physical structure is represented by
one persistent identity or by multiple duplicated/fractured anchors.
```

Avoid:

```text
The overlay is ground truth.
```

Use instead:

```text
LiDAR-derived physical reference
```
