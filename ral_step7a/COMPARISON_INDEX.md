# Step 7A S-Graphs Comparison Index

This file separates the two S-Graphs conditions currently available for
analysis. They should not be treated as duplicate runs.

## Condition A: Standard S-Graphs Map Output

Run ID:

```text
spot_dinamicaStaticV0_sgraphs_step7a_old_002
```

Location:

```text
lidar_situational_graphs/ral_step7a/runs/spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/
```

Launch condition:

```text
compute_odom:=false
room_segmentation:=old
optimization timer: default S-Graphs behavior
```

Use:

- Useful as the standard S-Graphs baseline output.
- Includes `/s_graphs/odom2map`, so S-Graphs plane fields were converted from
  native `map` to `odom`.
- Best for direct geometric comparison against InGraph `WallLike`, after wall
  annotation/matching.

Interpretation:

- Persistent wall-plane hypotheses are available in both native `map` and
  converted `odom` fields.
- Visual overlay suggested that several hypotheses do not align cleanly with
  dominant physical walls, so this is a diagnostic baseline, not a validated
  wall reconstruction.

## Condition B: Frontend No-Optimization Timer

Run ID:

```text
spot_dinamicaStaticV0_sgraphs_frontend_noopt_001
```

Location:

```text
lidar_situational_graphs/ral_step7a/runs/spot_dinamicaStaticV0_sgraphs_frontend_noopt_001/
```

Launch condition:

```text
compute_odom:=false
room_segmentation:=old
enable_optimization_timer:=false
```

Use:

- Useful for checking S-Graphs wall-plane hypotheses with periodic backend
  optimization disabled.
- Closer to a frontend-only comparison condition.
- Keeps the raw recorded S-Graphs output bag for re-analysis.

Important limitation:

- `/s_graphs/odom2map` has zero messages in this run.
- Therefore `*_odom` fields are unavailable in the CSV.
- Plots for this condition should be read as native S-Graphs `map`-frame
  hypothesis diagnostics unless a separate transform assumption is justified.

Interpretation:

- The run produced 14 wall-plane IDs.
- Only 5 IDs pass the current persistent-plot threshold
  `MIN_OBSERVATIONS >= 20`.
- The `*_all_map.png` figures show all 14 plane IDs.
- The persistent/all distinction is important for fragmentation and duplicate
  hypothesis analysis.

## Recommended Paper Use

Use Condition A for the main direct S-Graphs-vs-InGraph wall comparison because
it provides odom-converted plane fields.

Use Condition B as an ablation-style diagnostic:

```text
What does S-Graphs publish when periodic backend optimization is disabled?
```

This is useful for arguing about frontend behavior, plane fragmentation, and
the effect of backend optimization, but it should not replace the direct
odom-frame comparison unless a defensible map-to-odom transform is available.

## Claims Supported At This Stage

Supported:

- S-Graphs publishes persistent wall-plane hypotheses on the Spot sequence.
- In the no-optimization condition, S-Graphs produces multiple plane IDs with
  uneven persistence, including short-lived hypotheses.
- Visual overlays show several hypotheses near visible structures and others
  that appear duplicated, fragmented, or displaced.

Not yet supported without annotation/matching:

- InGraph is quantitatively better than S-Graphs.
- Each S-Graphs plane ID corresponds to one physical wall.
- S-Graphs recall/precision against physical walls.
