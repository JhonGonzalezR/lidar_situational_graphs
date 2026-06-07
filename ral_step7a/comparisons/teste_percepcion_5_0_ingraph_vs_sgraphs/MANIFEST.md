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
plots/wall_cross_model_agreement.png
plots/wall_persistence_stability.png
CHECKSUMS.sha256
```

