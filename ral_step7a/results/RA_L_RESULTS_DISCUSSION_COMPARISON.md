# RA-L Results Discussion: InGraph vs S-Graphs 2.0 with LiDAR-Derived Physical Reference

This document summarizes the current evidence for the RA-L `Results and Discussion` section. The comparison is framed around manually annotated physical structures in fused LiDAR overlays as a LiDAR-derived reference. S-Graphs 2.0 is retained as a wall-plane frontend baseline, while InGraph is evaluated as a multi-class structural anchoring frontend.

## Evaluation Scope

Two bags are currently evaluated:

| Case | InGraph run | S-Graphs 2.0 run | Physical reference status |
|---|---|---|---|
| `walls_pillars_3` | `20260602_233151` | `walls_pillars_3_sgraphs_standard_optimized_old_001` | Solid walls + physical pillars annotated |
| `teste_percepcion_5_0-001.mcap` | `20260603_014722` | `teste_percepcion_5_0_sgraphs_standard_optimized_old_001` | Solid walls + LiDAR-observable WallLike boundaries + pipes annotated |

The physical reference is not survey-grade ground truth. It is a manual annotation over fused top-down LiDAR overlays. This is appropriate for the present frontend evaluation because the system itself is LiDAR-only and does not use camera semantics.

## Reference Definitions

The evaluation separates semantic wall accuracy from LiDAR-geometric anchor usefulness:

| Scope | Meaning | Used for |
|---|---|---|
| `solid_wall_only` | Only manually marked solid architectural walls count as wall ground truth | Conservative semantic-wall evaluation |
| `walllike_boundary` | Solid walls plus LiDAR-observable planar boundaries, such as the experimental mesh/fence, count as WallLike reference | Geometry-first SLAM frontend evaluation |

This distinction is important in `teste_percepcion_5_0`: several InGraph WallLike IDs correspond to a mesh that bounds the experimental area. It is not a solid wall, but it produces stable LiDAR returns and geometrically delimits a corridor-like passage. In a LiDAR-only structural frontend, this is a valid WallLike boundary but should not be claimed as a semantic wall.

The evaluation gates are:

| Class | Alignment criterion |
|---|---|
| Wall / WallLike boundary | Normal angle <= 8 deg, plane offset <= 0.40 m, projected gap <= 1.00 m, projected overlap ratio >= 0.25 |
| Pillar | XY distance <= 0.55 m |
| Pipe | XY distance <= 0.35 m |

Each prediction is assigned to its nearest same-class physical annotation before the gate is evaluated. Therefore, failed predictions still appear in the per-prediction CSV with the closest physical structure and error values.

The key distinction is that `alignment_precision` measures whether a prediction is geometrically correct with respect to the annotated physical structure, while `instance_precision` penalizes duplicate IDs on the same structure. `physical_recall` measures how many annotated structures were recovered at least once.

Primary data files:

```text
ral_step7a/results/PHYSICAL_ANNOTATION_METRICS.md
ral_step7a/results/physical_annotation_metrics_summary.csv
ral_step7a/results/physical_annotation_prediction_matches_all.csv
ral_step7a/results/physical_annotation_fragmentation_all.csv
ral_step7a/results/walls_pillars_3_pillar_wall_proximity.csv
```

## Main Physical-Reference Metrics

### `walls_pillars_3`

| Model | Class | Predictions | Physical refs | Alignment precision | Instance precision | Physical recall | Fragmentation mean | Fragmentation max | Median error |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| InGraph | WallLike | 28 | 14 | 85.7% | 35.7% | 71.4% | 2.40 | 8 | 0.457 deg, 0.074 m offset |
| S-Graphs | wall planes | 15 | 14 | 40.0% | 26.7% | 28.6% | 1.50 | 2 | 3.818 deg, 0.182 m offset |
| InGraph | PillarLike | 16 | 15 | 93.8% | 56.2% | 60.0% | 1.67 | 3 | 0.194 m XY |

Interpretation:

- Against the physical wall annotations, InGraph achieves substantially higher WallLike alignment precision and physical recall than S-Graphs.
- InGraph also exposes PillarLike anchors, which S-Graphs does not expose as an equivalent frontend output. In this bag, 15 physical pillars were annotated and 9 were recovered by at least one aligned InGraph PillarLike prediction.
- The low instance precision and high fragmentation max for InGraph WallLike indicate that several physical walls are represented by multiple mature IDs. This is not purely a localization error; it is an identity/fragmentation issue.
- The PipeLike row is an explicit false positive under the current physical reference: one PipeLike track matured in a bag with no annotated physical pipes.
- S-Graphs is more compact, but lower recall against the annotated wall structures in this run.

### Pillar Proximity Analysis in `walls_pillars_3`

The physical annotation analysis also measures each annotated pillar's distance to the nearest annotated wall. This directly supports the qualitative observation that pillars are easier when they are visually separated from walls.

| Pillar subset | Physical refs | Detected by aligned InGraph PillarLike | Detection rate |
|---|---:|---:|---:|
| Near or embedded in wall, distance <= 0.75 m | 10 | 4 | 40.0% |
| Open or separated from wall | 5 | 5 | 100.0% |

Interpretation:

- InGraph detects all open/separated pillars in the current annotation.
- Pillars close to walls or embedded in wall returns remain harder. This supports a nuanced discussion: PillarLike is strong when the compact vertical support is separable in LiDAR, but wall-adjacent supports can merge into broader planar or cluttered returns.

### Non-Annotated Structural-Like Detections in `walls_pillars_3`

Two mature InGraph detections in `walls_pillars_3` deserve explicit treatment because they are informative failure cases for a LiDAR-only structural frontend.

| InGraph ID | Class | Lifecycle evidence | Physical-reference result | Interpretation |
|---:|---|---|---|---|
| 5 | PipeLike | reached `confirmed` and `strong`; selected age 9 | no physical pipe annotation exists in this bag | False positive for literal pipe detection; indicates that the current PipeLike geometry can mature on pipe-like clutter or local cylindrical evidence. |
| 63 | PillarLike | reached `confirmed` and `strong`; selected age 13 | nearest annotated pillar is `pillar_09`, XY error `6.83 m` | False positive for literal pillar detection, but visually explainable as a protruding/glass-adjacent structure that appears as a compact vertical support to LiDAR. |

These cases should not be hidden. They clarify the difference between geometric structural anchoring and semantic object recognition. With LiDAR-only evidence, a protruding vertical support or glass-adjacent edge can be a plausible PillarLike anchor even if it is not a literal building pillar. For the physical-reference metrics, however, both cases remain non-matches unless the annotation protocol explicitly includes them as valid structural-like references.

### `teste_percepcion_5_0`: Solid-Wall-Only vs WallLike-Boundary Evaluation

This sequence contains real pipes and a mesh/fence that behaves as a LiDAR-observable planar boundary. The distinction between solid semantic walls and WallLike boundaries changes the interpretation of InGraph performance.

| Scope | Model | Class | Predictions | Physical refs | Alignment precision | Instance precision | Physical recall | Fragmentation mean | Fragmentation max | Median error |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `solid_wall_only` | InGraph | WallLike | 18 | 7 | 55.6% | 22.2% | 57.1% | 2.50 | 5 | 0.841 deg, 0.041 m offset |
| `solid_wall_only` | S-Graphs | wall planes | 6 | 7 | 33.3% | 16.7% | 14.3% | 2.00 | 2 | 3.760 deg, 0.182 m offset |
| `solid_wall_only_excluding_boundary_predictions` | InGraph | WallLike | 11 | 7 | 90.9% | 36.4% | 57.1% | 2.50 | 5 | 0.841 deg, 0.041 m offset |
| `solid_wall_only_excluding_boundary_predictions` | S-Graphs | wall planes | 4 | 7 | 50.0% | 25.0% | 14.3% | 2.00 | 2 | 3.760 deg, 0.182 m offset |
| `walllike_boundary` | InGraph | WallLike | 18 | 11 | 94.4% | 44.4% | 72.7% | 2.13 | 5 | 0.770 deg, 0.058 m offset |
| `walllike_boundary` | S-Graphs | wall planes | 6 | 11 | 66.7% | 33.3% | 18.2% | 2.00 | 2 | 1.496 deg, 0.300 m offset |
| any | InGraph | PipeLike | 2 | 2 | 100.0% | 100.0% | 100.0% | 1.00 | 1 | 0.061 m XY |

Interpretation:

- Under the conservative `solid_wall_only` evaluation, InGraph still outperforms S-Graphs in wall alignment precision and recall, but several geometrically valid WallLike detections are penalized because they correspond to a mesh rather than a solid wall.
- When those already-explained boundary detections are excluded from the solid-wall denominator, InGraph reaches 90.9% solid-wall alignment precision, while S-Graphs reaches 50.0%. Physical recall is unchanged because this scope changes which predictions are counted, not which solid-wall annotations exist.
- Under the `walllike_boundary` evaluation, InGraph's WallLike alignment precision increases from 55.6% to 94.4%, and physical recall increases from 57.1% to 72.7%. This is the fairer metric for a LiDAR-only geometric frontend.
- S-Graphs also benefits from the boundary-aware reference, improving from 33.3% to 66.7% alignment precision, but its physical recall remains low at 18.2% because it exposes fewer wall-plane hypotheses in this short bag.
- PipeLike is the strongest result in this sequence: both annotated physical pipes are recovered with a median XY error of 0.061 m. S-Graphs does not expose equivalent PipeLike frontend anchors.

## Temporal and Lifecycle Metrics

Physical-reference alignment measures geometric correctness against annotated structures. The lifecycle metrics measure whether those detections are persistent enough to be useful as graph-ready anchors.

### Class Coverage

| Dataset | Model | Class | Total hypotheses | Mature/selected hypotheses | Selection rate | Median duration |
|---|---|---|---:|---:|---:|---:|
| `walls_pillars_3` | InGraph | WallLike | 133 | 28 | 21.1% | 22.39 s |
| `walls_pillars_3` | InGraph | PillarLike | 46 | 16 | 34.8% | 24.39 s |
| `walls_pillars_3` | InGraph | PipeLike | 14 | 1 | 7.1% | 22.80 s |
| `walls_pillars_3` | S-Graphs | wall planes | 15 | 12 | 80.0% | 89.20 s |
| `teste_percepcion_5_0` | InGraph | WallLike | 54 | 18 | 33.3% | 13.81 s |
| `teste_percepcion_5_0` | InGraph | PipeLike | 7 | 2 | 28.6% | 25.79 s |
| `teste_percepcion_5_0` | S-Graphs | wall planes | 6 | 6 | 100.0% | 16.60 s |

Interpretation:

- S-Graphs is more compact for walls, with fewer total IDs and longer wall-plane durations.
- InGraph produces more hypotheses, but its lifecycle filters select a mature subset and provide additional structural classes.
- The selected InGraph WallLike tracks have lower median normal/offset variation than S-Graphs in `walls_pillars_3` according to the previous stability summary, but the physical-reference results are now the stronger claim for alignment precision.

### Lifecycle State Metrics

The table below reports InGraph lifecycle metrics by dataset and class. The `confirmed` and `strong` ratios are observation-level ratios over all rows of `structure_anchor_tracks.csv`. The median age and median persistence score are computed over selected tracks, defined here as tracks that reached `is_strong=true` at least once.

| Dataset | Class | Total tracks | Selected tracks | Confirmed obs. ratio | Strong obs. ratio | Median selected age | Median selected persistence |
|---|---|---:|---:|---:|---:|---:|---:|
| `walls_pillars_3` | WallLike | 133 | 28 | 41.0% | 39.1% | 21.0 | 0.527 |
| `walls_pillars_3` | PillarLike | 46 | 16 | 11.0% | 9.5% | 15.0 | 0.417 |
| `walls_pillars_3` | PipeLike | 14 | 1 | 3.8% | 3.8% | 9.0 | 0.396 |
| `teste_percepcion_5_0` | WallLike | 54 | 18 | 33.6% | 32.3% | 13.0 | 0.462 |
| `teste_percepcion_5_0` | PillarLike | 16 | 0 | 0.0% | 0.0% | - | - |
| `teste_percepcion_5_0` | PipeLike | 7 | 2 | 13.9% | 13.9% | 16.5 | 0.548 |

Interpretation:

- WallLike is the most consistently mature class across both bags, with the largest selected-track counts and strong-state ratios.
- PillarLike matures clearly in `walls_pillars_3`, but not in `teste_percepcion_5_0`, which is consistent with the weaker pillar evidence in that sequence.
- PipeLike is sparse in `walls_pillars_3`, and its single selected track is not supported by a physical pipe annotation. In `teste_percepcion_5_0`, by contrast, the two selected PipeLike tracks align with the two annotated physical pipes and show the highest median persistence score among InGraph classes.

### Wall Age Comparison with S-Graphs 2.0

For WallLike-vs-S-Graphs comparison, age is reported using the closest available quantity in each system. InGraph reports `track_age` in lifecycle updates, while S-Graphs reports `observation_count` per wall-plane ID. These values are not identical counters, but both indicate how many times a wall hypothesis persisted through the frontend.

| Dataset | Model | Wall representation | Selected walls | Median age / observations | Median duration |
|---|---|---|---:|---:|---:|
| `walls_pillars_3` | InGraph | WallLike tracks | 28 | 21.0 updates | 22.39 s |
| `walls_pillars_3` | S-Graphs | wall-plane IDs | 12 | 40.5 observations | 89.20 s |
| `teste_percepcion_5_0` | InGraph | WallLike tracks | 18 | 13.0 updates | 13.81 s |
| `teste_percepcion_5_0` | S-Graphs | wall-plane IDs | 6 | 9.5 observations | 16.60 s |

Interpretation:

- S-Graphs wall-plane IDs are temporally more compact and longer-lived in `walls_pillars_3`.
- In `teste_percepcion_5_0`, both systems produce short-lived but persistent wall evidence, with S-Graphs exposing fewer wall-plane IDs and InGraph exposing more WallLike hypotheses plus PipeLike anchors.
- This comparison should be read as temporal persistence, not as geometric correctness; geometric correctness is evaluated against the LiDAR-derived physical reference above.

### Association Behavior in InGraph

| Dataset | Class | Accepted associations | Rejected associations | Dominant rejection reason |
|---|---|---:|---:|---|
| `walls_pillars_3` | WallLike | 1149 | 254 | `normal_angle` |
| `walls_pillars_3` | PillarLike | 288 | 13 | `footprint_diff` |
| `walls_pillars_3` | PipeLike | 12 | 240 | `young_mature_policy` |
| `teste_percepcion_5_0` | WallLike | 501 | 110 | `normal_angle` |
| `teste_percepcion_5_0` | PillarLike | 2 | 4 | `xy_distance` |
| `teste_percepcion_5_0` | PipeLike | 34 | 246 | `axis_distance` |

Interpretation:

- For WallLike, the dominant rejection reason is normal-angle inconsistency, which is coherent with a class-specific planar association policy.
- For PillarLike, the first bag shows stable associations, while the perception bag contains weak pillar evidence and no mature PillarLike tracks.
- For PipeLike, the two bags expose different bottlenecks: conservative young/mature policy and one mature false positive in `walls_pillars_3`, and axis-distance consistency in `teste_percepcion_5_0`, where the selected PipeLike tracks do correspond to annotated pipes.

## Runtime

| Dataset | Model | Frames | Median runtime | P95 runtime | Max runtime | Note |
|---|---|---:|---:|---:|---:|---|
| `walls_pillars_3` | InGraph | 702 | 47.11 ms | 58.50 ms | 75.39 ms | Available from InGraph metrics |
| `teste_percepcion_5_0` | InGraph | 240 | 29.14 ms | 58.63 ms | 84.08 ms | Available from InGraph metrics |
| both | S-Graphs | N/A | N/A | N/A | N/A | Current artifacts do not expose comparable per-frame CPU runtime |

The absence of S-Graphs runtime should be stated explicitly. The current comparison supports structural frontend quality and available anchor coverage, but not a fair runtime benchmark between both systems.

## Recommended Figures

Use figures that support the physical-reference evaluation first:

```text
ral_step7a/results/physical_annotation_precision_recall.png
ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/physical_annotations_ground_truth.png
ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/physical_annotation_alignment.png
ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/physical_annotations_ground_truth.png
ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/physical_annotation_alignment.png
ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/physical_annotation_alignment_solid_wall_only_no_boundaries.png
ral_step7a/results/walls_pillars_3_pillar_wall_proximity.png
```

Then use the frontend evidence overlays to show qualitative anchor coverage:

```text
ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/evidence_side_by_side_panel.png
ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_side_by_side_panel.png
ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/evidence_ingraph_ever_strong_pipes.png
```


## Suggested Paper Text

```text
We evaluated the structural frontend against manually annotated physical structures in fused top-down LiDAR overlays. The annotations are not survey-grade ground truth; rather, they provide a LiDAR-derived physical reference for assessing whether each mature frontend hypothesis is geometrically aligned with visible structures. Wall hypotheses were evaluated using normal-angle, plane-offset, projected-gap, and projected-overlap gates, while PillarLike and PipeLike anchors were evaluated by XY distance.

On walls_pillars_3, InGraph aligned 24 of 28 mature WallLike predictions with the annotated wall reference, yielding 85.7% alignment precision and 71.4% physical recall. S-Graphs aligned 6 of 15 wall-plane predictions, yielding 40.0% alignment precision and 28.6% physical recall. InGraph also recovered 9 of 15 annotated pillars with at least one aligned PillarLike prediction. Open or separated pillars were all recovered, whereas near-wall or embedded pillars were recovered in 40.0% of cases, indicating that PillarLike performance degrades when compact vertical supports merge with wall returns. This bag also exposes two useful failure cases: a PipeLike track matured despite the absence of annotated physical pipes, and one mature PillarLike track corresponded to a protruding/glass-adjacent structure rather than a literal pillar.

On teste_percepcion_5_0, the environment contains both solid walls and a mesh-like planar boundary. Since the frontend is LiDAR-only, this mesh is not a semantic wall but is a valid WallLike boundary when evaluated as a persistent planar obstacle observed by the sensor. Under the conservative solid-wall-only evaluation, InGraph reached 55.6% WallLike alignment precision and 57.1% physical recall. However, after removing WallLike predictions already aligned with LiDAR-observable boundaries, solid-wall alignment precision increased to 90.9%, showing that most apparent false positives were useful boundary detections rather than geometrically incorrect walls. When LiDAR-observable boundaries were included as valid WallLike references, InGraph reached 94.4% alignment precision and 72.7% recall, while S-Graphs reached 66.7% alignment precision and 18.2% recall. InGraph also recovered both annotated physical pipes with 100.0% PipeLike alignment precision and 0.061 m median XY error.

These results support InGraph as a multi-class structural anchoring frontend rather than only a wall-plane extractor. S-Graphs remains more compact for wall-plane entities, but the physical-reference evaluation shows that InGraph provides higher WallLike alignment and recall in the tested sequences while also exposing PillarLike and PipeLike anchors that are not available as equivalent S-Graphs frontend outputs. The current limitations are also clear: geometry-only anchoring can mature structural-like false positives when local LiDAR evidence resembles a compact support or cylindrical element.
```

## Defensible Conclusion

The strongest RA-L claim is:

> InGraph provides a persistent, multi-class structural frontend for LiDAR-only indoor-industrial mapping. Against a LiDAR-derived physical reference, it achieves higher WallLike alignment and recall than the S-Graphs wall-plane frontend in the evaluated bags, while additionally recovering compact vertical supports and real pipes when those structures are present and separable in LiDAR. Its main limitations are WallLike fragmentation, reduced PillarLike recall when physical supports are embedded in or very close to wall returns, and occasional structural-like false positives caused by LiDAR-only geometry.

## Remaining Caveats

1. The physical annotations are LiDAR-derived references, not surveyed ground truth.
2. `walllike_boundary` should be described carefully: it is a geometric boundary useful for LiDAR SLAM, not a semantic wall.
3. S-Graphs is a hierarchical SLAM system; the fair direct comparison here is limited to its exposed wall-plane frontend output.
4. InGraph has per-frame runtime metrics; equivalent S-Graphs CPU runtime metrics are not available in the current artifacts.
5. Fragmentation remains a real issue: high alignment precision does not imply one ID per physical structure.
6. Geometry-only structural anchoring is not semantic recognition: a glass-adjacent protrusion can become PillarLike, and pipe-like local geometry can become PipeLike even when no physical pipe is annotated.
