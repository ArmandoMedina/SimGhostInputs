---
tipo: capacidad
clave: CHT-01
modulo: CHT
dominio: Reportería
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CHT-01 - Generar gráficas de análisis

## Módulo
- [[CHT - Gráficas]]

## Propósito funcional
Generar el conjunto de gráficas del debrief: delta map, barras de tiempo perdido, diagrama G-G, vuelta multi-canal, detalle de las curvas con mayor pérdida y zonas de frenada.

## Actor principal
Sistema (parte del pipeline `fantasma compare`; también accesible desde la UI).

## Entradas funcionales
- `trace`: delta continuo por distancia.
- `corner_rows`: métricas por curva.
- `corners`: lista de curvas con hitos (de COR-01).
- Directorio de salida.
- `top`: número de curvas a destacar (por defecto 5).

## Salidas funcionales
- Lista de rutas de archivos PNG creados (vacía si matplotlib no está instalado o no hay datos).
- Archivos: `delta_map.png`, `time_loss_bar.png`, `gg_diagram.png`, `full_lap.png`, `curva_<id>.png` (top-N), `frenada_<id>.png` (top-N).

## Reglas de negocio
- Si `matplotlib` no está instalado, `render_charts` devuelve `[]` sin lanzar excepción.
- El diagrama G-G solo se genera si hay canales `glat` y `glong` en el trace.
- Los gráficos por curva y de frenada solo se generan para las N curvas con mayor pérdida.

## Criterios de aceptación
- Dado que matplotlib está instalado y hay datos de `compare()`, cuando se llama a `render_charts`, entonces se crean al menos `delta_map.png`, `time_loss_bar.png` y `full_lap.png` en el directorio de salida.
- Dado que matplotlib no está instalado, cuando se llama a `render_charts`, entonces devuelve una lista vacía sin lanzar excepción.
- Dado que el trace no tiene canales `glat` ni `glong`, cuando se intenta generar el diagrama G-G, entonces la función devuelve `None` sin crashear.

## Dependencias funcionales
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[CMP-02 - Métricas y flags por curva]]
- [[COR-01 - Detectar curvas e hitos]]

## Fuera de alcance
- Reporte Markdown y CSVs (es [[REP-01 - Generar reporte Markdown]] y [[REP-02 - Exportar CSVs (delta, corners_compare)]]).
- HUD de video (es [[OVL-01 - Generar overlay HUD con canal alfa]]).

## Relacionado con
- [[Reportería]]

> **Nota:** No existe test unitario dedicado a esta capacidad. Los criterios se derivan de la inspección de `fantasma/viz/charts.py` (`render_charts` y `_mpl`).
