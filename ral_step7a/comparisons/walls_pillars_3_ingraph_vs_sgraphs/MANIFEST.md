# Manifest de la comparación

## Alcance

Comparación directa:

```text
InGraph 20260602_233151 frente a S-Graphs walls_pillars_3
```

Ejecuciones adicionales organizadas, pero no comparadas directamente:

```text
InGraph 20260603_014722
S-Graphs walls_pillars_2
S-Graphs walls_pillars bloqueada por bag truncada
```

## Estructura

```text
README.md
MANIFEST.md
data/
plots/
scripts/
shareable_bundle/
```

`CHECKSUMS.sha256` verifica los archivos ligeros de la comparación. El bundle
completo y su checksum están almacenados en `shareable_bundle/`.

## Contenido de `data/`

| Archivo | Propósito |
|---|---|
| `comparison_scope.csv` | Indica qué ejecuciones son comparables y cuáles no |
| `class_coverage.csv` | Cobertura de WallLike, PillarLike y PipeLike |
| `class_metric_summary.csv` | Resumen por clase y modelo |
| `wall_model_summary.csv` | Comparación principal de paredes persistentes |
| `hypothesis_metrics.csv` | Métricas por cada hipótesis estructural |
| `wall_cross_model_matches.csv` | Pares geométricos InGraph-S-Graphs |
| `wall_agreement_summary.csv` | Resumen del acuerdo entre modelos |
| `operational_metrics.csv` | Métricas operacionales disponibles |
| `ingraph_association_summary.csv` | Resumen de asociaciones aceptadas y rechazadas |

## Advertencia de interpretación

Los emparejamientos representan acuerdo geométrico entre modelos. No son
precisión, recall ni exactitud contra verdad-terreno.

PillarLike y PipeLike son clases no expuestas por S-Graphs; sus valores deben
mostrarse como `N/A`, no como cero detecciones.

## Nota sobre visualización S-Graphs

La figura `plots/evidence_sgraphs_persistent_walls.png` conserva el criterio
original de persistencia usado en la comparación tabular:
`observations>=20`. Bajo ese criterio se dibujan 12 de los 15 planos S-Graphs
publicados en `walls_pillars_3`.

La figura `plots/evidence_sgraphs_all_walls.png` muestra todos los planos
publicados por S-Graphs en la misma secuencia (`observations>=1`). Esta vista
es útil para inspeccionar qué hipótesis entran al sistema de S-Graphs antes de
aplicar nuestro filtro de persistencia para la comparación, pero no debe
mezclarse con las métricas de paredes persistentes salvo que se reconstruyan
las tablas con la misma regla.
