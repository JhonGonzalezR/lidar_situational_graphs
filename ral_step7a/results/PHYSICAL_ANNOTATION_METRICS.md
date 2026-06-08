# Physical Annotation Precision Metrics

These metrics compare frontend hypotheses against manually annotated structures in the fused LiDAR overlays.
The annotations are a LiDAR-derived physical reference, not a survey-grade ground-truth map.

Definitions:

- `alignment_precision`: fraction of predictions that pass the geometric gate against their nearest same-class physical annotation.
- `instance_precision`: unique physical structures recovered divided by number of predictions; this penalizes duplicate IDs on the same structure.
- `physical_recall`: fraction of annotated physical structures recovered by at least one aligned prediction.
- `fragmentation_index`: number of aligned predictions per recovered physical structure.

Alignment gates used in this report:

- walls: normal angle <= 8 deg, plane offset <= 0.40 m, projected gap <= 1.00 m, projected overlap ratio >= 0.25.
- pillars: XY distance <= 0.55 m.
- pipes: XY distance <= 0.35 m.

Every prediction is assigned to its nearest same-class physical annotation before the alignment gate is evaluated. Therefore, failed predictions still appear in `physical_annotation_prediction_matches_all.csv` with their nearest annotation and error values.

The `solid_wall_only_excluding_boundary_predictions` scope evaluates solid-wall precision after removing WallLike predictions that were already aligned with LiDAR-observable boundary annotations. This avoids counting useful boundary detections as false solid-wall detections.

## Summary

| Dataset | Scope | Model | Class | Predictions | GT annotations | Alignment precision | Instance precision | Physical recall | Fragmentation mean | Fragmentation max | Median wall angle | Median wall offset | Median XY error |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| walls_pillars_3 | walllike_boundary | InGraph | wall | 28 | 14 | 85.7% | 35.7% | 71.4% | 2.400000 | 8 | 0.456540 | 0.073871 | - |
| walls_pillars_3 | walllike_boundary | InGraph | pillar | 16 | 15 | 93.8% | 56.2% | 60.0% | 1.666667 | 3 | - | - | 0.194463 |
| walls_pillars_3 | walllike_boundary | InGraph | pipe | 1 | 0 | 0.0% | 0.0% | 0.0% | - | - | - | - | - |
| walls_pillars_3 | walllike_boundary | S-Graphs | wall | 15 | 14 | 40.0% | 26.7% | 28.6% | 1.500000 | 2 | 3.817848 | 0.182281 | - |
| teste_percepcion_5_0 | walllike_boundary | InGraph | wall | 18 | 11 | 94.4% | 44.4% | 72.7% | 2.125000 | 5 | 0.769732 | 0.057853 | - |
| teste_percepcion_5_0 | walllike_boundary | InGraph | pipe | 2 | 2 | 100.0% | 100.0% | 100.0% | 1.000000 | 1 | - | - | 0.060916 |
| teste_percepcion_5_0 | walllike_boundary | S-Graphs | wall | 6 | 11 | 66.7% | 33.3% | 18.2% | 2.000000 | 2 | 1.496253 | 0.300308 | - |
| teste_percepcion_5_0 | solid_wall_only | InGraph | wall | 18 | 7 | 55.6% | 22.2% | 57.1% | 2.500000 | 5 | 0.841242 | 0.041325 | - |
| teste_percepcion_5_0 | solid_wall_only | InGraph | pipe | 2 | 2 | 100.0% | 100.0% | 100.0% | 1.000000 | 1 | - | - | 0.060916 |
| teste_percepcion_5_0 | solid_wall_only | S-Graphs | wall | 6 | 7 | 33.3% | 16.7% | 14.3% | 2.000000 | 2 | 3.760453 | 0.181994 | - |
| teste_percepcion_5_0 | solid_wall_only_excluding_boundary_predictions | InGraph | wall | 11 | 7 | 90.9% | 36.4% | 57.1% | 2.500000 | 5 | 0.841242 | 0.041325 | - |
| teste_percepcion_5_0 | solid_wall_only_excluding_boundary_predictions | InGraph | pipe | 2 | 2 | 100.0% | 100.0% | 100.0% | 1.000000 | 1 | - | - | 0.060916 |
| teste_percepcion_5_0 | solid_wall_only_excluding_boundary_predictions | S-Graphs | wall | 4 | 7 | 50.0% | 25.0% | 14.3% | 2.000000 | 2 | 3.760453 | 0.181994 | - |

## Per-Structure Fragmentation

The file `physical_annotation_fragmentation_all.csv` reports, for every annotated structure, how many predictions selected it as nearest and how many passed the alignment gate.

## Non-Annotated Structural-Like Cases

In `walls_pillars_3`, one PipeLike track (`ID 5`) reached `confirmed`/`strong` even though no physical pipe was annotated in the scene; it is therefore counted as a PipeLike false positive under the current reference. The same run also contains PillarLike `ID 63`, which reached `confirmed`/`strong` but did not align with a physical pillar annotation (`6.83 m` XY error to the nearest annotated pillar). This detection is visually explainable as a protruding/glass-adjacent vertical structure, but remains a non-match for literal-pillar precision.

## Pillar Proximity Note

For `walls_pillars_3`, `walls_pillars_3_pillar_wall_proximity.csv` estimates how close each physical pillar annotation is to the nearest annotated wall segment. This helps separate open pillars from pillars that are very close to, or visually embedded in, wall returns.

| Pillar subset | GT pillars | Detected by aligned InGraph PillarLike | Detection rate |
|---|---:|---:|---:|
| near_or_embedded_wall | 10 | 4 | 40.0% |
| open_or_separated | 5 | 5 | 100.0% |

## Figures

- `physical_annotation_precision_recall.png`: alignment precision, instance precision, and physical recall by dataset/model/class.
- `walls_pillars_3_pillar_wall_proximity.png`: physical pillar distance to nearest wall and whether the pillar was aligned with an InGraph PillarLike prediction.
