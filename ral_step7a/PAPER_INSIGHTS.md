# Step 7A Paper Insights

This note summarizes the S-Graphs evidence for the RA-L comparison. It is meant
to be concise and paper-facing.

## Comparison Scope

Direct comparison:

```text
S-Graphs wall planes <-> InGraph WallLike
```

Not a direct comparison:

```text
S-Graphs wall planes <-> InGraph PillarLike / PipeLike
```

`PillarLike` and `PipeLike` should be reported as additional InGraph structural
coverage because S-Graphs does not expose those classes as standalone frontend
outputs.

## Runs Used

Main baseline:

```text
runs/spot_dinamicaStaticV0_sgraphs_standard_optimized_old_002/
```

This is the best run for direct comparison with InGraph because it includes
`/s_graphs/odom2map`, allowing S-Graphs planes to be expressed in `odom`.

Frontend/no-optimization diagnostic:

```text
runs/spot_dinamicaStaticV0_sgraphs_frontend_noopt_001/
```

This run disables periodic graph optimization:

```text
enable_optimization_timer:=false
```

It is useful for inspecting frontend-like plane fragmentation and persistence,
but it did not publish `/s_graphs/odom2map`, so its planes remain native
`map`-frame hypotheses.

## Main Observations

Standard/default S-Graphs:

```text
/s_graphs/all_map_planes: 54 messages
plane observations: 540
unique plane IDs: 14
odom-converted rows: 540 / 540
```

Frontend/no-optimization:

```text
/s_graphs/all_map_planes: 32 messages
plane observations: 235
unique plane IDs: 14
odom-converted rows: 0 / 235
```

The two conditions produced the same number of unique wall-plane IDs, but the
no-optimization run produced fewer global map-plane publications and fewer
observations. This suggests that disabling periodic optimization reduces global
map-state update/publication events, not necessarily the number of plane
hypotheses created by the frontend.

## Interpretation

The current evidence supports:

- S-Graphs publishes persistent wall-plane hypotheses on the Spot sequence.
- Several S-Graphs hypotheses appear duplicated, fragmented, or displaced in
  visual overlays.
- The no-optimization condition exposes uneven persistence: only 5 of 14 plane
  IDs pass `MIN_OBSERVATIONS >= 20`.
- Fragmentation/overlapping plane hypotheses appear to be present even when
  periodic optimization is disabled.

The current evidence does not yet support:

- InGraph is quantitatively better than S-Graphs.
- Each S-Graphs plane ID corresponds to one physical wall.
- S-Graphs precision/recall against physical walls.

Those claims require physical-wall annotation or deterministic matching against
InGraph `WallLike`.

## Recommended Paper Framing

Use the standard/default S-Graphs run as the main wall-plane baseline because it
provides odom-frame converted plane hypotheses.

Use the no-optimization run as an ablation-style diagnostic:

> Disabling the periodic optimization timer produced the same number of unique
> wall-plane IDs but fewer global map-plane publications. This condition exposes
> frontend-like wall-plane fragmentation and uneven persistence, while the
> standard run remains the primary odom-frame baseline for direct comparison
> with InGraph `WallLike`.

Conservative result statement:

> On the Spot sequence, S-Graphs produced persistent wall-plane hypotheses, but
> visual overlays showed several duplicated, fragmented, or displaced
> hypotheses. We therefore evaluate S-Graphs on the shared wall-plane subset and
> avoid treating each persistent plane ID as a validated physical wall without
> annotation-based matching.
