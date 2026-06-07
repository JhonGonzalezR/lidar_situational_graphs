# Comparación organizada: InGraph frente a S-Graphs

## Qué quise comparar

En este apartado comparé los dos modelos usando solamente los datos que
realmente permiten una comparación justa.

La comparación directa utiliza:

```text
Dataset compartido: walls_pillars_3
InGraph: 20260602_233151/structure_anchor_tracks.csv
S-Graphs: runs/walls_pillars_3_sgraphs_standard_optimized_old_001/
Marco común: odom
```

Elegí esta pareja porque sus tiempos corresponden a la misma bag y ambos
resultados pueden expresarse en `odom`. Las otras ejecuciones quedaron
organizadas como evidencia adicional, pero no las mezclé en la comparación
directa porque no comparten dataset.

## Qué significa cada modelo

InGraph publica tres clases estructurales:

```text
WallLike
PillarLike
PipeLike
```

S-Graphs publica planos verticales que pueden compararse con `WallLike`, pero no
expone pilares y tuberías como clases independientes. Por esta razón:

- las paredes sí tienen comparación directa;
- los pilares y las tuberías se reportan como cobertura adicional de InGraph;
- `N/A` para S-Graphs significa que la clase no está expuesta, no que el modelo
  haya detectado cero elementos.

## Pregunta que responde esta comparación

El artículo presenta InGraph como un frontend estructural intermedio, no como
un detector aislado ni como un sistema SLAM completo. Su función es transformar
evidencia LiDAR-odometría ruidosa, observada cuadro a cuadro, en anclas
estructurales persistentes que puedan ser utilizadas posteriormente por un
grafo.

Por eso, la pregunta principal de esta comparación no es solamente cuántos
elementos detectó cada modelo. La pregunta más importante es:

> ¿Las hipótesis creadas durante el recorrido maduran, se mantienen
> geométricamente estables y proporcionan una representación estructural útil?

La comparación de paredes con S-Graphs permite estudiar la parte compartida
entre ambos modelos. Los pilares y tuberías permiten estudiar la cobertura
estructural adicional de InGraph y el comportamiento de sus políticas
específicas por clase.

## Proceso que utilicé

### 1. Selección de hipótesis persistentes

Para evitar comparar detecciones temporales débiles:

- En InGraph seleccioné cada track `WallLike`, `PillarLike` o `PipeLike` que fue
  marcado como fuerte al menos una vez durante la ejecución (`ever_strong`).
- En S-Graphs seleccioné cada plano observado al menos 20 veces, siguiendo el
  umbral utilizado por los scripts de visualización existentes.

Estas reglas no son idénticas, porque los modelos no tienen el mismo ciclo de
vida. Son reglas equivalentes en intención: conservar hipótesis persistentes.

### 2. Métricas de paredes

Para cada pared persistente calculé:

- número de observaciones;
- duración entre primera y última observación;
- soporte medio de puntos;
- desviación angular de la normal;
- desviación del desplazamiento del plano en `odom`.

La estabilidad angular y del desplazamiento es especialmente importante porque
mide cuánto cambia una misma hipótesis mientras el robot recorre la escena.
Una variación menor significa una hipótesis más estable, pero no demuestra por
sí sola que la pared sea correcta.

### 3. Acuerdo geométrico entre modelos

Construí un emparejamiento uno-a-uno entre paredes de InGraph y S-Graphs usando:

```text
diferencia angular máxima: 15 grados
diferencia de desplazamiento máximo: 1.0 m
separación máxima entre segmentos: 3.0 m
```

Después seleccioné el conjunto de pares con menor costo global. Este resultado
mide cuándo ambos modelos proponen una pared geométricamente compatible.

No lo llamo precisión ni recall porque todavía no existe una anotación manual
de las paredes físicas que funcione como verdad-terreno.

### 4. Separación entre maduración histórica y estado final

En InGraph, `ever_strong` significa que un track cumplió la política de
fortaleza de su clase al menos una vez durante el recorrido. Esta selección
permite medir cuántas hipótesis lograron madurar, aunque algunas hayan pasado a
estado `stale` al terminar la ejecución.

Esto es diferente de afirmar que todas las hipótesis seleccionadas estaban
publicándose como anclas `graph-ready` en el último cuadro. Según el flujo
descrito en el artículo, una publicación actual requiere que la hipótesis esté
observada, confirmada y fuerte. Por lo tanto:

- `ever_strong` mide éxito de maduración durante el recorrido;
- el estado más reciente mide disponibilidad al final del recorrido;
- ambos valores responden preguntas distintas y deben analizarse juntos.

### 5. Límites de lo que se puede medir

Esta comparación estudia la calidad del frontend estructural: persistencia,
estabilidad, asociaciones, disponibilidad por clase y acuerdo geométrico entre
modelos. No mide directamente:

- exactitud contra las estructuras físicas reales;
- calidad final de una trayectoria SLAM optimizada;
- efecto de las anclas dentro de un backend de optimización;
- rendimiento relativo, porque no existen tiempos equivalentes de S-Graphs.

## Resultados principales

### Cobertura estructural persistente

| Clase | InGraph | S-Graphs |
|---|---:|---:|
| Paredes | 28 | 12 |
| Pilares | 16 | N/A |
| Tuberías | 1 | N/A |

InGraph produjo más hipótesis estructurales persistentes y además representó
pilares y tuberías. Sin embargo, más hipótesis no significa automáticamente
mejor resultado: también puede indicar fragmentación.

### Persistencia y estabilidad de paredes

| Métrica mediana | InGraph | S-Graphs |
|---|---:|---:|
| Hipótesis totales de pared | 133 | 15 |
| Hipótesis persistentes seleccionadas | 28 | 12 |
| Proporción seleccionada | 21.1% | 80.0% |
| Observaciones por hipótesis seleccionada | 69.5 | 40.5 |
| Duración | 22.39 s | 89.20 s |
| Desviación angular | 0.457 grados | 2.027 grados |
| Desviación del desplazamiento | 0.080 m | 0.477 m |

La lectura principal es:

- InGraph produjo más paredes y sus hipótesis seleccionadas fueron
  geométricamente más estables.
- S-Graphs produjo un conjunto mucho más compacto y sus planos persistieron
  durante más tiempo.
- InGraph creó 133 IDs de pared, pero solo 28 llegaron a ser fuertes. Esto
  muestra mayor cobertura potencial, junto con fragmentación o descarte de
  hipótesis.
- S-Graphs conservó 12 de sus 15 planos con el umbral de persistencia, aunque
  presentó mayor variación angular y de desplazamiento.

Los conteos de observaciones y soporte no deben compararse como tasas absolutas,
porque cada modelo publica y filtra con frecuencias diferentes.

En términos descriptivos para esta única secuencia, la desviación angular
mediana de InGraph fue aproximadamente 77.5% menor y la desviación del
desplazamiento fue aproximadamente 83.2% menor que en S-Graphs. En cambio, la
duración mediana de los planos de S-Graphs fue aproximadamente 4.0 veces la de
las paredes de InGraph. Estos porcentajes muestran un intercambio entre
estabilidad local, cantidad de hipótesis y continuidad temporal; no deben
generalizarse todavía a otros recorridos.

### Lectura desde el ciclo de vida de InGraph

De las 28 paredes que fueron fuertes al menos una vez, el último registro de
cada track mostró:

```text
9 paredes en estado confirmed
19 paredes en estado stale
```

Que una pared termine como `stale` no significa automáticamente que haya sido
una detección incorrecta. Puede indicar que dejó de ser observable cuando el
robot cambió de posición, pero que durante una parte del recorrido acumuló
suficiente evidencia para madurar. Este comportamiento es coherente con el
ciclo de vida candidato, débil, confirmado y stale/lost descrito en el
artículo.

Al mismo tiempo, la diferencia entre 28 paredes históricamente fuertes y 9
confirmadas al final muestra que la disponibilidad actual depende mucho de la
observabilidad y de la reasociación. Por eso, para evaluar el frontend no basta
con reportar el mapa final: también es necesario estudiar cómo evolucionan las
anclas durante todo el recorrido.

### Acuerdo entre ambos modelos

El emparejamiento encontró:

```text
6 pares de pared compatibles
21.4% de las paredes seleccionadas de InGraph emparejadas
50.0% de los planos seleccionados de S-Graphs emparejados
diferencia angular mediana: 4.21 grados
diferencia de desplazamiento mediana: 0.404 m
separación mediana de segmentos: 0.0 m
```

Esto significa que existe una región de acuerdo clara entre ambos modelos, pero
también que una parte importante de sus hipótesis no coincide bajo la regla
geométrica definida.

El acuerdo parcial también revela diferencias de representación. Algunos planos
de S-Graphs tuvieron varias paredes de InGraph geométricamente compatibles; en
el caso más marcado, un plano de S-Graphs tuvo hasta 9 candidatos de InGraph.
Esto es evidencia consistente con fragmentación o sobresegmentación de paredes
en InGraph. Sin verdad-terreno no se puede asegurar que todos esos candidatos
representen una sola pared física, porque también pueden existir divisiones
reales o criterios de segmentación diferentes.

El caso contrario también debe considerarse: una representación compacta puede
ser ventajosa, pero también podría unir fragmentos físicos distintos. Por esto,
el número de IDs no permite decidir por sí solo cuál representación es más
correcta.

### Pilares y tuberías

En la bag compartida, InGraph obtuvo:

```text
16 PillarLike persistentes
1 PipeLike persistente
```

S-Graphs no permite una comparación directa para estas clases. El resultado
correcto es reportarlas como cobertura estructural adicional de InGraph.

Los datos de asociación ayudan a interpretar el único `PipeLike` fuerte:
InGraph aceptó 12 asociaciones de tubería y rechazó 240; 237 rechazos fueron
por la política `young_mature_policy`. Esto indica que la promoción de
tuberías fue especialmente conservadora en esta ejecución.

La asociación por clase permite profundizar esta lectura:

| Clase InGraph | Asociaciones aceptadas | Asociaciones rechazadas | Lectura principal |
|---|---:|---:|---|
| WallLike | 1149 | 254 | La asociación separó candidatos geométricamente compatibles de candidatos con mayor distancia y diferencia angular. |
| PillarLike | 288 | 13 | Los pilares mostraron asociaciones consistentes y una alta capacidad de permanencia en esta secuencia. |
| PipeLike | 12 | 240 | La política de maduración fue muy restrictiva y limitó la consolidación de tuberías. |

En paredes, los candidatos aceptados tuvieron una distancia de centroide
mediana de `0.417 m` y una diferencia angular mediana de `0.815 grados`. Los
rechazados tuvieron medianas de `1.736 m` y `9.889 grados`. Esta separación
indica que la asociación de paredes sí está filtrando evidencia geométricamente
menos compatible, en lugar de aceptar indiscriminadamente las detecciones.

En pilares, las 288 asociaciones aceptadas frente a solo 13 rechazadas, junto
con 16 tracks fuertes, respaldan la utilidad de una política específica para
soportes compactos. En tuberías, el resultado muestra el principal cuello de
botella de esta ejecución: la política conservadora evita asociaciones
inestables, pero también impide que casi todas las hipótesis jóvenes maduren.

## Rendimiento disponible

Para InGraph se registraron:

```text
frames procesados: 702
tiempo de procesamiento mediano: 47.11 ms
percentil 95: 58.50 ms
máximo: 75.39 ms
id_switch_rate final: 0.010789
```

Los artefactos actuales de S-Graphs no incluyen métricas equivalentes de tiempo
o cambios de ID. Por lo tanto, no realicé una comparación de rendimiento entre
modelos.

## Análisis alineado con el artículo

### Calidad del frontend estructural

Los resultados respaldan la idea central del artículo de evaluar la evolución
de anclas persistentes y no solamente detecciones instantáneas. InGraph generó
hipótesis en las tres clases, permitió que un subconjunto madurara y mantuvo una
variación geométrica baja en las paredes seleccionadas. Además, el
`id_switch_rate` final de `0.010789` aporta evidencia de continuidad de
identidad, aunque debe repetirse en más secuencias para establecer una
conclusión general.

La diferencia entre hipótesis totales y fuertes también demuestra por qué el
ciclo de vida es necesario. InGraph no publica todas las detecciones como
estructura confiable: filtra, consolida o descarta hipótesis según la evidencia
acumulada. Sin embargo, los 133 IDs de pared y la multiplicidad de candidatos
compatibles con algunos planos de S-Graphs muestran que todavía existe margen
para mejorar la absorción de fragmentos y reducir duplicados.

### Comparación directa en paredes

En la clase compartida, ningún modelo domina en todas las métricas:

- InGraph produjo más paredes maduras y menor variación geométrica mediana.
- S-Graphs produjo menos planos, conservó una proporción mayor y mostró mucha
  más continuidad temporal.
- El acuerdo uno-a-uno confirmó que ambos modelos representan parte de las
  mismas estructuras, pero también que aplican criterios distintos de
  consolidación y segmentación.

Esta diferencia es coherente con el papel de cada sistema. InGraph busca crear
anclas estructurales multiclase para alimentar un grafo posterior, mientras
S-Graphs ya organiza una representación jerárquica centrada en planos. La
comparación más justa consiste en analizar sus paredes compartidas y tratar las
otras clases como cobertura adicional, no como fallos de S-Graphs.

### Resultado más importante

El resultado más importante no es que InGraph tenga 28 paredes frente a 12
planos. Lo más relevante es que, a partir de muchas hipótesis iniciales,
InGraph consiguió producir un subconjunto maduro con baja variación geométrica,
asociaciones selectivas y cobertura de pilares y tuberías. Esto demuestra el
valor del frontend como filtro temporal y estructural.

El resultado también identifica claramente sus debilidades actuales: la
fragmentación de paredes, la pérdida de disponibilidad final de varios tracks y
la política excesivamente restrictiva para tuberías. Estas observaciones son
más útiles para mejorar el modelo que una comparación basada únicamente en
conteos finales.

## Conclusiones

1. **Los resultados respaldan parcialmente la propuesta central de InGraph.**
   En la secuencia `walls_pillars_3`, el frontend transformó detecciones
   temporales en anclas maduras de varias clases y mantuvo paredes con baja
   variación geométrica.
2. **La fortaleza principal de InGraph es la combinación de estabilidad y
   cobertura multiclase.** Las paredes seleccionadas fueron más estables que
   los planos de S-Graphs en esta ejecución, y los pilares mostraron un
   comportamiento de asociación sólido.
3. **La fortaleza principal de S-Graphs es la compactación y continuidad de las
   paredes.** Conservó 12 de 15 planos con el umbral de persistencia y alcanzó
   duraciones considerablemente mayores.
4. **InGraph todavía debe mejorar la consolidación de paredes.** Los 133 IDs
   totales, los 28 tracks históricamente fuertes y la existencia de múltiples
   candidatos para algunos planos de S-Graphs muestran fragmentación potencial.
5. **PipeLike es la clase más débil en esta ejecución.** La política
   `young_mature_policy` explica 237 de los 240 rechazos, por lo que el balance
   entre robustez y capacidad de maduración necesita revisión.
6. **El acuerdo parcial no permite afirmar cuál modelo es más exacto.** Los 6
   pares compatibles demuestran que existe estructura común, pero no sustituyen
   una evaluación contra verdad-terreno.
7. **La conclusión debe mantenerse limitada a esta bag compartida.** Para
   sostener una afirmación general es necesario repetir el protocolo en más
   recorridos sincronizados y anotar manualmente las estructuras físicas.

Con los datos actuales, la afirmación más defendible para el artículo es:

> En `walls_pillars_3`, InGraph proporciona mayor cobertura semántica y menor
> variación geométrica mediana en las paredes que lograron madurar, mientras
> S-Graphs produce una representación de paredes más compacta y temporalmente
> duradera. El análisis del ciclo de vida y las asociaciones muestra que
> InGraph funciona como filtro estructural persistente, aunque todavía presenta
> fragmentación de paredes y una promoción muy conservadora de tuberías. Ambos
> modelos coinciden en parte del entorno, pero la exactitud final y la
> superioridad geométrica requieren anotaciones de verdad-terreno y más
> secuencias compartidas.

## Cómo explicaría el resultado

Primero aseguré que ambos modelos hubieran procesado la misma bag y que las
paredes estuvieran expresadas en el mismo marco `odom`. Después evité comparar
detectores instantáneos: seleccioné solamente hipótesis que demostraron
persistencia según las reglas disponibles en cada modelo. Finalmente comparé
su estabilidad durante el recorrido y busqué paredes geométricamente
compatibles entre ambos resultados.

Este proceso fue importante porque el objetivo del trabajo no es contar todas
las detecciones, sino estudiar cuáles logran convertirse en estructura útil y
persistente. La comparación muestra que InGraph consigue crear anclas estables
y representar más clases, mientras S-Graphs mantiene una representación de
paredes más compacta y duradera. También permitió encontrar problemas concretos
de InGraph: varias paredes pueden quedar fragmentadas y casi todas las tuberías
jóvenes son rechazadas antes de madurar.

La conclusión responsable es que InGraph muestra resultados prometedores como
frontend estructural multiclase, especialmente en estabilidad de paredes y
seguimiento de pilares, pero todavía no se puede afirmar que sea más exacto que
S-Graphs. Para responder esa pregunta se necesita comparar ambos resultados con
una anotación manual del entorno y repetir el experimento en más bags.

## Archivos importantes

Tablas principales:

```text
data/comparison_scope.csv
data/class_coverage.csv
data/class_metric_summary.csv
data/wall_model_summary.csv
data/wall_agreement_summary.csv
data/wall_cross_model_matches.csv
data/operational_metrics.csv
data/ingraph_association_summary.csv
```

Figuras principales:

```text
plots/class_coverage_matched_dataset.png
plots/wall_persistence_stability.png
plots/wall_cross_model_agreement.png
plots/evidence_side_by_side_panel.png
```

## Cómo reproducir

Desde la raíz `src/`:

```bash
python3 lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs/scripts/build_comparison.py \
  --ingraph-matched-tracks 20260602_233151/structure_anchor_tracks.csv \
  --ingraph-matched-metrics 20260602_233151/structure_metrics.csv \
  --ingraph-matched-association 20260602_233151/structure_association_debug.csv \
  --ingraph-additional-tracks 20260603_014722/structure_anchor_tracks.csv \
  --ingraph-additional-metrics 20260603_014722/structure_metrics.csv \
  --ingraph-additional-association 20260603_014722/structure_association_debug.csv \
  --sgraphs-matched-planes lidar_situational_graphs/ral_step7a/runs/walls_pillars_3_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv \
  --sgraphs-additional-planes lidar_situational_graphs/ral_step7a/runs/walls_pillars_2_sgraphs_standard_optimized_old_001/sgraphs_wall_planes.csv \
  --output lidar_situational_graphs/ral_step7a/comparisons/walls_pillars_3_ingraph_vs_sgraphs
```
