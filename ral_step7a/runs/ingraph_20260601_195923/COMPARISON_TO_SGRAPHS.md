# Step 7A InGraph vs S-Graphs visual comparison

Dataset: `spot/dinamicaStaticV0`

Run commands from the workspace root that contains `lidar_situational_graphs/`.

Input bag used for both methods:

```bash
export BAG_PATH=/absolute/path/to/spot/dinamicaStaticV0
```

## Reproduce InGraph overlays

Confirmed WallLike + PillarLike context:

```bash
BAG_PATH="${BAG_PATH}" \
./lidar_situational_graphs/ral_step7a/scripts/plot_ingraph_structure_overlay.sh
```

Confirmed PillarLike only:

```bash
BAG_PATH="${BAG_PATH}" \
MODE=confirmed \
SNAPSHOT=latest \
CLASSES=pillar_like \
OUTPUT_PNG=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/plots/ingraph_lidar_overlay_confirmed_pillar_only.png \
SUMMARY_MD=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/README_confirmed_pillar_only.md \
./lidar_situational_graphs/ral_step7a/scripts/plot_ingraph_structure_overlay.sh
```

Ever-strong WallLike only:

```bash
BAG_PATH="${BAG_PATH}" \
MODE=strong \
SNAPSHOT=latest_strong \
CLASSES=wall_like \
OUTPUT_PNG=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/plots/ingraph_lidar_overlay_ever_strong_wall_only.png \
SUMMARY_MD=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/README_ever_strong_wall_only.md \
./lidar_situational_graphs/ral_step7a/scripts/plot_ingraph_structure_overlay.sh
```

Ever-strong WallLike + PillarLike:

```bash
BAG_PATH="${BAG_PATH}" \
MODE=strong \
SNAPSHOT=latest_strong \
CLASSES=wall_like,pillar_like \
OUTPUT_PNG=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/plots/ingraph_lidar_overlay_ever_strong_wall_pillar.png \
SUMMARY_MD=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/README_ever_strong_wall_pillar.md \
./lidar_situational_graphs/ral_step7a/scripts/plot_ingraph_structure_overlay.sh
```

Ever-strong PillarLike only:

```bash
BAG_PATH="${BAG_PATH}" \
MODE=strong \
SNAPSHOT=latest_strong \
CLASSES=pillar_like \
OUTPUT_PNG=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/plots/ingraph_lidar_overlay_ever_strong_pillar_only.png \
SUMMARY_MD=lidar_situational_graphs/ral_step7a/runs/ingraph_20260601_195923/README_ever_strong_pillar_only.md \
./lidar_situational_graphs/ral_step7a/scripts/plot_ingraph_structure_overlay.sh
```

Side-by-side panel:

```bash
./lidar_situational_graphs/ral_step7a/scripts/make_overlay_comparison_panel.sh
```

## Main artifacts

InGraph:

- `input/structure_anchor_tracks.csv`
- `input/structure_association_debug.csv`
- `input/structure_metrics.csv`
- `plots/ingraph_lidar_overlay_confirmed_wall_pillar.png`
- `plots/ingraph_lidar_overlay_confirmed_pillar_only.png`
- `plots/ingraph_lidar_overlay_ever_strong_wall_pillar.png`
- `plots/ingraph_lidar_overlay_ever_strong_wall_only.png`
- `plots/ingraph_lidar_overlay_ever_strong_pillar_only.png`
- `plots/step7a_sgraphs_vs_ingraph_ever_strong_overlay_panel.png`

S-Graphs baseline used in the panel:

- `../spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/plots/sgraphs_lidar_wall_overlay_odom.png`
- `../spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/sgraphs_wall_plane_summary.csv`
- `../spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/README.md`

Figure style:

- Article overlays use a shared crop around the mapped structure:
  `x=[-35, 10]`, `y=[-20, 20]` in the plotted odom-aligned frame.
- Grid, odometry axes, axis labels, and z colorbar are hidden to increase overlay visibility.
- Segment/track IDs are kept at the segment centroids because they are useful for tracing hypotheses back to the CSV summaries.
- Standalone centroid-only S-Graphs figures were removed because they do not add evidence beyond the overlay.

## Current evidence

S-Graphs optimized baseline:

- 540 wall-plane observations.
- 14 unique plane IDs.
- 540/540 plane observations converted to `odom`.
- Visual overlay shows some wall hypotheses near real structures, but also displaced, overlapping, or fragmented hypotheses.

InGraph latest tracks:

- 66 WallLike track IDs in the latest track table.
- 23 WallLike tracks pass the current `confirmed` plotting filter.
- 14 PillarLike tracks pass the current `confirmed` plotting filter.
- 3 WallLike tracks pass the `strong` plotting filter when only the latest row of each track is used.
- 22 WallLike tracks and 11 PillarLike tracks pass the historical `ever strong` filter when using `SNAPSHOT=latest_strong`.
- The confirmed WallLike overlay follows more of the visible room contour, but it also contains fragmented and short local wall tracks.

Important distinction:

- `SNAPSHOT=latest` uses the final row of each track.
- `SNAPSHOT=latest_strong` uses the last row in which each track had `is_strong=true`; therefore it includes IDs that became strong at any time during the sequence, even if the final row is no longer strong.
- Both snapshots use `centroid_odom_*` and `normal_odom_*`, so the plotted InGraph walls and pillars are in the shared `odom` frame.

## Analysis

Research question:

Can the frontend produce persistent structural hypotheses that are spatially
consistent with the same LiDAR scene, without relying on backend optimization
as the main source of geometric correction?

Controlled variables:

- Same Spot bag: `dinamicaStaticV0`.
- Same LiDAR evidence: `/velodyne/points`.
- Same reference frame for the overlays: `odom`.
- Same top-down qualitative check: structural hypotheses over sampled LiDAR.

What each InGraph figure means:

- `confirmed_wall_pillar`: final/latest map state. This shows what remains
  available at the end of the run under the `confirmed` filter.
- `confirmed_pillar_only`: final/latest pillar state. This isolates whether
  vertical structural elements are being tracked near visible scene support.
- `ever_strong_wall_pillar`: historical persistence evidence. A track is shown
  if it became strong at least once during the run.
- `ever_strong_wall_only`: wall-only historical persistence. This is the
  cleanest InGraph wall figure for comparison with S-Graphs wall planes.
- `ever_strong_pillar_only`: pillar-only historical persistence.
- `step7a_sgraphs_vs_ingraph_ever_strong_overlay_panel`: direct qualitative
  panel against the optimized S-Graphs baseline.

Interpretation of InGraph:

InGraph produces a richer structural frontend output than a wall-only baseline:
it separates WallLike and PillarLike anchors, provides lifecycle state, and
stores each anchor directly in `odom`. The latest confirmed state contains 23
WallLike and 14 PillarLike anchors. The historical ever-strong view contains 22
WallLike and 11 PillarLike anchors, showing that many structural hypotheses did
reach the strong persistence criterion at some point even if the final/latest
state is more selective.

The visual overlay suggests that several InGraph WallLike anchors follow the
dominant room boundary visible in the LiDAR cloud. However, the output is not a
perfect wall reconstruction: there are short local segments, fragmented tracks,
and nearby repeated wall hypotheses in some regions. Therefore the strongest
current claim is about structural persistence and spatial plausibility, not
about complete or metrically optimal wall reconstruction.

Interpretation of S-Graphs:

The optimized S-Graphs baseline exports 14 unique wall-plane IDs and 540
wall-plane observations in `odom`. This makes it usable as the direct S-Graphs
baseline for the overlay. Visually, the S-Graphs hypotheses are fewer but some
appear duplicated, displaced, or not well aligned with the dominant visible
room boundaries. This should be described as a limitation observed in this bag,
not as a universal limitation of S-Graphs.

Comparison:

In this run, S-Graphs gives a compact wall-plane set but shows weaker visual
agreement in several regions of the LiDAR overlay. InGraph gives a denser and
more semantically structured set of anchors, with better apparent coverage of
the room contour and additional PillarLike evidence, but it also exhibits
fragmentation. The comparison therefore favors InGraph for frontend structural
coverage and persistence evidence on this bag, while still requiring annotation
for any final quantitative claim.

Recommended figure for the paper:

Use `step7a_sgraphs_vs_ingraph_ever_strong_overlay_panel.png` as the main
qualitative comparison figure. It compares S-Graphs wall planes against
InGraph WallLike anchors that reached strong persistence at least once.

Recommended wording:

> In the `dinamicaStaticV0` Spot sequence, the S-Graphs frontend baseline
> produced 14 wall-plane IDs and 540 wall-plane observations after odom-frame
> conversion. InGraph produced 22 WallLike and 11 PillarLike anchors that
> reached the strong persistence criterion at least once. The overlay suggests
> that InGraph provides broader structural coverage of the visible room layout,
> while S-Graphs exhibits duplicated or displaced wall-plane hypotheses in this
> run. These observations are qualitative and should be paired with annotation-
> based matching before reporting final geometric accuracy metrics.

## Paper-safe interpretation

Use the optimized S-Graphs run as the main baseline for the direct visual
comparison because it has an `odom` conversion for all exported wall-plane
observations.

The current visual evidence supports the following claim:

> On the same Spot `dinamicaStaticV0` bag, S-Graphs produces fewer persistent
> wall-plane IDs with visible duplication and displacement in the LiDAR overlay,
> while InGraph produces more WallLike structural tracks that cover more of the
> visible room contour but still exhibit fragmentation and a conservative
> strong-track promotion.

Do not claim final quantitative superiority from these overlays alone. A
defensible quantitative comparison still needs either manual wall annotations or
a fixed matching rule in the shared `odom` frame.

## Suggested next comparison metrics

- Number of matched physical wall segments.
- Mean perpendicular distance from each detected wall segment to annotated wall
  lines.
- Angular error against annotated wall orientation.
- Fragmentation: number of hypotheses per annotated wall.
- Persistence: observation count or track age for each matched wall.
- False positives: hypotheses that do not overlap an annotated wall.
