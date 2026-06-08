# Manifest: `teste_percepcion_5_0_ingraph_vs_sgraphs`

## Alcance

Comparación directa:

```text
InGraph 20260603_014722 frente a S-Graphs teste_percepcion_5_0
```

Bag original:

```text
bags/teste_percepcion_5_0-001.mcap
```

S-Graphs run:

```text
lidar_situational_graphs/ral_step7a/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/
```

## Advertencia de interpretación

La secuencia es corta para S-Graphs. Con el umbral estándar
`observations>=20`, S-Graphs selecciona 0 planos. Para obtener una comparación
útil de percepción se usa `observations>=5`, indicado en los CSV como:

```text
observations>=5_short_sequence
```

Los emparejamientos WallLike/S-Graphs miden acuerdo geométrico entre modelos,
no precisión contra verdad-terreno.

## Contenido

```text
data/class_coverage.csv
data/class_metric_summary.csv
data/hypothesis_metrics.csv
data/ingraph_association_summary.csv
data/operational_metrics.csv
data/wall_agreement_summary.csv
data/wall_cross_model_matches.csv
data/wall_model_summary.csv
plots/class_coverage_matched_dataset.png
plots/evidence_ingraph_ever_strong_all.png
plots/evidence_ingraph_ever_strong_walls.png
plots/evidence_ingraph_ever_strong_pipes.png
plots/evidence_sgraphs_persistent_walls_min5.png
plots/evidence_side_by_side_panel.png
plots/summary_evidence_ingraph_ever_strong_all.md
plots/summary_evidence_ingraph_ever_strong_walls.md
plots/summary_evidence_ingraph_ever_strong_pipes.md
plots/wall_cross_model_agreement.png
plots/wall_persistence_stability.png
CHECKSUMS.sha256
```

Las figuras `evidence_*` usan la MCAP original
`teste_percepcion_5_0-001.mcap` como nube LiDAR de fondo. En S-Graphs se
mantiene el umbral adaptado `observations>=5`; en InGraph se muestran anchors
`ever-Strong`. La figura `evidence_ingraph_ever_strong_pipes.png` se conserva
por separado porque esta secuencia es la evidencia actual de tuberías reales.
