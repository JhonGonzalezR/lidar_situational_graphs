# Resultados RA-L: comparación InGraph vs S-Graphs 2.0

Este documento organiza los resultados actuales para escribir la sección de
`Results and Discussion` del artículo. La idea principal es comparar
directamente `WallLike` de InGraph contra planos de pared de S-Graphs 2.0, y
reportar `PillarLike` y `PipeLike` como cobertura estructural adicional de
InGraph porque S-Graphs no expone esas clases como salidas frontend
equivalentes.

## Estado de las corridas

| Caso | InGraph | S-Graphs 2.0 | Estado para comparación directa |
|---|---|---|---|
| `walls_pillars_3` | `20260602_233151` | `walls_pillars_3_sgraphs_standard_optimized_old_001` | Completo |
| `teste_percepcion_5_0-001.mcap` | `20260603_014722` | `teste_percepcion_5_0_sgraphs_standard_optimized_old_001` | Completo con umbral S-Graphs adaptado |

Para el segundo caso existe la bag original:

```text
bags/teste_percepcion_5_0-001.mcap
```

Para reproducirla dentro del contenedor Humble de S-Graphs, la MCAP se
convirtió a una bag SQLite mínima con los tópicos requeridos:

```text
lidar_situational_graphs/ral_step7a/runs/teste_percepcion_5_0_sqlite_input/
```

La MCAP original no fue modificada.

## Fuentes usadas

### InGraph

```text
20260602_233151/structure_anchor_tracks.csv
20260602_233151/structure_metrics.csv
20260602_233151/structure_association_debug.csv
20260602_233151/plots/ingraph_lidar_overlay_ever_strong_all.png

20260603_014722/structure_anchor_tracks.csv
20260603_014722/structure_metrics.csv
20260603_014722/structure_association_debug.csv
20260603_014722/plots/ingraph_tracks_ever_strong_all.png
```

### S-Graphs 2.0

```text
lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv
lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_plane_summary.csv

lidar_situational_graphs/ral_step7a/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv
lidar_situational_graphs/ral_step7a/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/sgraphs_wall_plane_summary.csv
```

### Comparación derivada

```text
lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/data/
lidar_situational_graphs/ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/data/
```

## Métricas principales para el artículo

### Caso 1: `walls_pillars_3`

Esta es la comparación directa actualmente defendible, porque ambos métodos
procesaron la misma secuencia y sus hipótesis de pared están expresadas en el
marco `odom`.

#### Paredes: InGraph WallLike vs S-Graphs

| Métrica | InGraph | S-Graphs |
|---|---:|---:|
| IDs totales de pared | 133 | 15 |
| Paredes persistentes/maduras | 28 | 12 |
| Tasa de selección | 21.1% | 80.0% |
| Observaciones medianas por pared seleccionada | 69.5 | 40.5 |
| Duración mediana | 22.39 s | 89.20 s |
| Soporte mediano | 240.4 puntos | 388.0 puntos |
| Desviación mediana de normal | 0.457 grados | 2.027 grados |
| Desviación mediana de offset del plano | 0.080 m | 0.477 m |

Lectura:

- InGraph produjo más paredes que llegaron a madurar.
- S-Graphs produjo una representación más compacta y con mayor duración
  temporal.
- Las paredes maduras de InGraph tuvieron menor variación geométrica mediana.
- Los 133 IDs totales frente a 28 paredes maduras indican hipótesis transitorias,
  descarte y posible fragmentación.

#### Acuerdo geométrico tipo "precisión proxy"

Se realizó un emparejamiento uno-a-uno entre las 28 paredes `WallLike`
seleccionadas de InGraph y los 12 planos persistentes de S-Graphs.

Reglas de candidato:

```text
diferencia angular <= 15 grados
diferencia de offset <= 1.0 m
separación entre segmentos <= 3.0 m
```

Resultado:

| Métrica de acuerdo | Valor |
|---|---:|
| Pares compatibles uno-a-uno | 6 |
| Fracción de paredes InGraph emparejadas | 21.4% |
| Fracción de planos S-Graphs emparejados | 50.0% |
| Diferencia angular mediana entre pares | 4.21 grados |
| Diferencia mediana de offset entre pares | 0.404 m |
| Separación mediana entre segmentos | 0.0 m |
| Candidatos InGraph por plano S-Graphs emparejado | mediana 4.5, máximo 9 |
| Candidatos S-Graphs por pared InGraph emparejada | mediana 1.5, máximo 2 |

Esta métrica puede describirse como una **precisión proxy de alineamiento** si
se deja claro que S-Graphs no es verdad-terreno. Bajo esa lectura, 6 de 28
paredes maduras de InGraph tuvieron un plano S-Graphs compatible, mientras que
6 de 12 planos persistentes de S-Graphs tuvieron una pared InGraph compatible.

La multiplicidad de candidatos es importante para discutir fragmentación: en el
caso más fuerte, un mismo plano persistente de S-Graphs tuvo 9 candidatos de
InGraph geométricamente compatibles. Esto sugiere que InGraph puede representar
una misma estructura física mediante varios IDs, aunque sin anotación manual no
se puede afirmar que todos correspondan exactamente a la misma pared real.

#### Cobertura estructural adicional de InGraph

| Clase InGraph | IDs totales | Tracks fuertes alguna vez | Tasa de maduración | Duración mediana de tracks fuertes | Ratio `confirmed` por observaciones | Ratio `strong` por observaciones | Estado final de los tracks fuertes |
|---|---:|---:|---:|---:|---:|---:|---|
| `WallLike` | 133 | 28 | 21.1% | 22.39 s | 41.0% | 39.1% | 9 `confirmed`, 19 `stale` |
| `PillarLike` | 46 | 16 | 34.8% | 24.39 s | 11.0% | 9.5% | 1 `confirmed`, 15 `stale` |
| `PipeLike` | 14 | 1 | 7.1% | 22.80 s | 3.8% | 3.8% | 1 `stale` |

Lectura:

- `WallLike` muestra el resultado principal: muchas hipótesis iniciales, un
  subconjunto fuerte y baja variación geométrica.
- `PillarLike` sí exhibe maduración persistente, con 16 tracks fuertes.
- `PipeLike` es la clase más débil en esta secuencia: solo 1 track llegó a ser
  fuerte.

#### Edad de track y persistence score

| Clase InGraph | Edad mediana de tracks fuertes | `persistence_score` mediano en último registro |
|---|---:|---:|
| `WallLike` | 21.0 frames/updates | 0.527 |
| `PillarLike` | 15.0 frames/updates | 0.417 |
| `PipeLike` | 9.0 frames/updates | 0.396 |

La edad del track y el `persistence_score` refuerzan que las salidas
seleccionadas no son detecciones instantáneas. En esta corrida, las paredes
fuertes tienen mayor edad y mayor score mediano que pilares y tuberías, lo cual
coincide con que `WallLike` es la clase más consolidada del experimento.

#### Asociación por clase en InGraph

| Clase | Asociaciones aceptadas | Asociaciones rechazadas | Razón dominante de rechazo |
|---|---:|---:|---|
| `WallLike` | 1149 | 254 | `normal_angle` con 193 rechazos |
| `PillarLike` | 288 | 13 | `footprint_diff` con 11 rechazos |
| `PipeLike` | 12 | 240 | `young_mature_policy` con 237 rechazos |

Lectura:

- En paredes, las asociaciones aceptadas tuvieron diferencia angular mediana de
  0.815 grados, mientras que las rechazadas tuvieron 9.889 grados. Esto muestra
  que el filtro geométrico de asociación está separando evidencia compatible de
  evidencia inconsistente.
- En pilares, hubo muchas asociaciones aceptadas y pocos rechazos, lo cual
  respalda la estabilidad de esa clase en esta secuencia.
- En tuberías, el principal cuello de botella fue la política
  `young_mature_policy`: 237 de 240 rechazos. La clase no falla solo por no
  detectar, sino por una maduración muy conservadora.

#### Runtime

| Modelo | Frames procesados | Mediana | P95 | Máximo | ID-switch final |
|---|---:|---:|---:|---:|---:|
| InGraph | 702 | 47.11 ms | 58.50 ms | 75.39 ms | 0.010789 |
| S-Graphs | N/A | N/A | N/A | N/A | N/A |

Los artefactos actuales de S-Graphs no exponen runtime CPU equivalente ni una
métrica de ID-switch comparable. Para S-Graphs sí se registró duración de la
bag de salida, conteos de mensajes y planos publicados, pero eso no es lo mismo
que tiempo de procesamiento por frame.

Datos disponibles de la corrida S-Graphs `walls_pillars_3`:

```text
duration del output bag: 162.498 s
mensajes totales: 39122
/s_graphs/all_map_planes: 53 mensajes
plane observations: 546
unique plane IDs: 15
persistent wall segments plotted: 12
```

## Caso 2: `teste_percepcion_5_0-001.mcap` / `20260603_014722`

Esta corrida tiene métricas completas de InGraph y S-Graphs. La bag es corta
para S-Graphs: se grabaron 18 mensajes de `/s_graphs/all_map_planes`, 62
observaciones de planos y 6 IDs de pared. Como ningún ID puede llegar al umbral
fijo `observations>=20`, para esta secuencia se usa un umbral adaptado
`observations>=5`. Este umbral debe reportarse explícitamente si esta corrida
se usa en el artículo.

### Resultados InGraph

| Clase InGraph | IDs totales | Tracks fuertes alguna vez | Tasa de maduración | Duración mediana de tracks fuertes | Ratio `confirmed` por observaciones | Ratio `strong` por observaciones | Estado final de tracks fuertes |
|---|---:|---:|---:|---:|---:|---:|---|
| `WallLike` | 54 | 18 | 33.3% | 13.81 s | 33.6% | 32.3% | 5 `confirmed`, 13 `stale` |
| `PillarLike` | 16 | 0 | 0.0% | N/A | 0.0% | 0.0% | N/A |
| `PipeLike` | 7 | 2 | 28.6% | 25.79 s | 13.9% | 13.9% | 1 `confirmed`, 1 `stale` |

### Estabilidad de paredes: InGraph WallLike vs S-Graphs

| Métrica | InGraph | S-Graphs |
|---|---:|---:|
| IDs totales de pared | 54 | 6 |
| Paredes persistentes/maduras | 18 | 6 |
| Tasa de selección | 33.3% | 100.0% |
| Observaciones medianas por pared seleccionada | 65.0 | 9.5 |
| Duración mediana | 13.81 s | 16.60 s |
| Soporte mediano | 206.70 puntos | 146.0 puntos |
| Desviación mediana de normal | 0.372 grados | 0.004 grados |
| Desviación mediana de offset | 0.029 m | 0.023 m |

Lectura:

- `WallLike` fue estable en esta corrida y tuvo una tasa de maduración mayor
  que en `walls_pillars_3`.
- `PipeLike` funcionó mejor que en `walls_pillars_3`, con 2 tracks fuertes.
- `PillarLike` no produjo tracks fuertes en esta corrida.
- Con el umbral adaptado `observations>=5`, S-Graphs produjo pocos planos, pero
  muy estables en esta secuencia corta.
- La comparación de estabilidad debe interpretarse con cuidado porque el umbral
  S-Graphs no es el mismo usado en `walls_pillars_3`.

### Acuerdo geométrico tipo "precisión proxy"

| Métrica de acuerdo | Valor |
|---|---:|
| Pares compatibles uno-a-uno | 4 |
| Fracción de paredes InGraph emparejadas | 22.2% |
| Fracción de planos S-Graphs emparejados | 66.7% |
| Diferencia angular mediana entre pares | 2.51 grados |
| Diferencia mediana de offset entre pares | 0.241 m |
| Separación mediana entre segmentos | 0.0 m |
| Candidatos InGraph por plano S-Graphs emparejado | mediana 3.5, máximo 4 |
| Candidatos S-Graphs por pared InGraph emparejada | mediana 2.0, máximo 2 |

Lectura:

- La comparación encontró 4 pares de pared compatibles.
- La diferencia angular mediana fue menor que en `walls_pillars_3`, pero este
  resultado usa un umbral S-Graphs adaptado para secuencia corta.
- La presencia de hasta 4 candidatos InGraph para un plano S-Graphs vuelve a
  indicar fragmentación potencial de IDs.
- Igual que en el primer caso, esto es acuerdo entre modelos, no precisión
  contra verdad-terreno.

### Edad de track y persistence score

| Clase InGraph | Edad mediana de tracks fuertes | `persistence_score` mediano en último registro |
|---|---:|---:|
| `WallLike` | 13.0 frames/updates | 0.462 |
| `PillarLike` | N/A | N/A |
| `PipeLike` | 16.5 frames/updates | 0.548 |

En esta corrida, `PipeLike` tiene mayor `persistence_score` mediano que
`WallLike`, lo que respalda usarla como evidencia adicional de que las tuberías
pueden madurar cuando la geometría de la secuencia favorece la asociación por
eje.

### Asociación por clase en InGraph

| Clase | Asociaciones aceptadas | Asociaciones rechazadas | Razón dominante de rechazo |
|---|---:|---:|---|
| `WallLike` | 501 | 110 | `normal_angle` con 60 rechazos |
| `PillarLike` | 2 | 4 | `xy_distance` con 4 rechazos |
| `PipeLike` | 34 | 246 | `axis_distance` con 127 rechazos |

Lectura:

- En paredes, la asociación vuelve a separar candidatos compatibles de
  candidatos geométricamente más débiles.
- En tuberías, el cuello de botella cambia: la razón dominante ya no es
  `young_mature_policy`, sino `axis_distance`. Esto sugiere que en esta bag el
  problema está más ligado a continuidad/alineamiento del eje que a la política
  joven-maduro.
- En pilares, la evidencia fue muy débil: solo 2 aceptaciones y ningún track
  fuerte.

### Runtime

| Modelo | Frames procesados | Mediana | P95 | Máximo | ID-switch final |
|---|---:|---:|---:|---:|---:|
| InGraph | 240 | 29.14 ms | 58.63 ms | 84.08 ms | 0.003803 |
| S-Graphs | N/A | N/A | N/A | N/A | N/A |

Los artefactos S-Graphs tampoco exponen runtime CPU por frame para esta corrida.
Lo disponible es:

```text
recorded S-Graphs output bag duration: 59.10 s
/s_graphs/all_map_planes: 18 mensajes
plane observation rows: 62
unique plane IDs: 6
selected plane IDs with observations>=5: 6
selected plane IDs with observations>=20: 0
```

## Figuras recomendadas

### Para una página de resultados

Usaría una figura principal y una tabla compacta.

Figura principal:

```text
lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/wall_cross_model_agreement.png
```

Mensaje: acuerdo espacial entre las paredes persistentes de ambos modelos. La
figura muestra los 28 segmentos WallLike seleccionados, los 12 planos S-Graphs
persistentes y las correspondencias uno-a-uno. Para publicación conviene
regenerarla con líneas de correspondencia más gruesas o mostrando solo los
pares emparejados, porque al reducirla a una columna las líneas grises se ven
poco.

Tabla compacta:

```text
Total wall IDs
Paredes persistentes/maduras
Duración mediana
Normal std.
Offset std.
Pares emparejados
PillarLike fuertes
PipeLike fuertes
Runtime InGraph mediana / p95
```

Figura adicional si hay espacio:

```text
lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/evidence_ingraph_ever_strong_all.png
20260602_233151/plots/ingraph_lidar_overlay_ever_strong_all.png
```

Mensaje: InGraph no solo produce paredes; también exhibe anclas `PillarLike` y
`PipeLike`. Esta figura es especialmente útil para defender la contribución
multiclase.

Para `20260602_233151`, la figura `ingraph_lidar_overlay_ever_strong_all.png`
muestra 28 segmentos `WallLike`, 16 marcadores `PillarLike` y 1 marcador
`PipeLike`. Es una figura de tipo `latest_strong`: visualiza el último estado
en el que cada track fue fuerte, no necesariamente el estado final absoluto del
track.

### Figuras suplementarias o de respaldo

```text
lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/plots/wall_persistence_stability.png
lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/plots/sgraphs_lidar_wall_overlay_odom.png
lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/plots/sgraphs_wall_plane_segments_odom.png
lidar_situational_graphs/ral_step7a/runs/teste_percepcion_5_0_sgraphs_standard_optimized_old_001/plots/sgraphs_lidar_wall_overlay_odom_min5.png
lidar_situational_graphs/ral_step7a/comparisons/teste_percepcion_5_0_ingraph_vs_sgraphs/plots/wall_cross_model_agreement.png
```

Para `20260603_014722` ya existe una imagen útil para pipes:

```text
20260603_014722/plots/ingraph_tracks_ever_strong_all.png
```

Esa figura muestra 18 segmentos `WallLike`, 0 marcadores `PillarLike` y 2
marcadores `PipeLike`. También es un snapshot `latest_strong`, por lo que sirve
para evidenciar maduración histórica de pipes. Si se quiere que todo el
framework quede autocontenido dentro de `ral_step7a/runs`, conviene copiar o
regenerar esta figura dentro de una carpeta de corrida Step 7A.

## Texto corto recomendado para el artículo

```text
We evaluated InGraph and S-Graphs 2.0 on the matched walls_pillars_3
LiDAR--odometry sequence. The direct comparison was restricted to the shared
wall-plane subset, while PillarLike and PipeLike anchors were reported as
additional InGraph structural coverage.

InGraph produced 28 mature WallLike tracks, 16 PillarLike tracks, and one
PipeLike track. Compared with the 12 persistent S-Graphs wall planes, InGraph
WallLike anchors showed lower median geometric variation: 0.457 deg normal
variation and 0.080 m plane-offset variation, versus 2.027 deg and 0.477 m for
S-Graphs. S-Graphs, however, produced a more compact and temporally persistent
wall representation, with 89.20 s median duration compared with 22.39 s for
InGraph.

One-to-one geometric matching identified six compatible wall pairs on
walls_pillars_3. These pairs represent 21.4% of selected InGraph walls and
50.0% of selected S-Graphs planes, with median angular and offset differences
of 4.21 deg and 0.404 m. On teste_percepcion_5_0, using an adaptive
observations>=5 S-Graphs threshold due to the short sequence, matching
identified four compatible pairs with median angular and offset differences of
2.51 deg and 0.241 m. Since no manual physical-wall annotation is available,
these values are interpreted as cross-model agreement rather than ground-truth
precision.

The results support InGraph as a persistent multi-class structural frontend,
but also reveal remaining limitations: possible WallLike fragmentation, final
anchor availability changes due to lifecycle state, and conservative PipeLike
maturation in walls_pillars_3. Runtime for InGraph was 47.11 ms median and
58.50 ms p95 over 702 processed frames; equivalent S-Graphs runtime metrics are
not available in the current artifacts.
```

## Conclusión defendible

La conclusión más segura para RA-L es:

> InGraph demuestra valor como frontend estructural persistente y multiclase.
> En `walls_pillars_3`, sus paredes maduras tienen menor variación geométrica
> mediana que los planos persistentes de S-Graphs, y además produce anclas de
> pilares y tuberías. S-Graphs mantiene una representación de paredes más
> compacta y temporalmente más larga. La comparación muestra acuerdo geométrico
> parcial entre modelos, pero no debe presentarse como precisión absoluta sin
> anotación manual del entorno.

## Pendientes antes de cerrar resultados

1. Decidir si el artículo acepta el umbral adaptado `observations>=5` para
   `teste_percepcion_5_0`, o si esa corrida queda como evidencia adicional.
2. Integrar dentro del framework `ral_step7a/runs` el overlay ya existente de
   `20260603_014722` que incluye los 2 `PipeLike` fuertes.
3. Si se quiere hablar de precisión real, crear anotaciones manuales de las
   paredes físicas y calcular precisión, recall y fragmentación contra esa
   verdad-terreno.
