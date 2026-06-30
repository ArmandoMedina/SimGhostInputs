# Formato de datos

Referencia técnica del formato interno y los archivos de entrada/salida. Útil para contribuir importadores o consumir las salidas desde otras herramientas.

## Canales canónicos

Todo importador convierte a este modelo (`fantasma/core/lap.py`):

| Canal | Unidad | Obligatorio | Notas |
| :-- | :-- | :-- | :-- |
| `time` | s | ✅ | desde el inicio del segmento |
| `dist` | m | ✅ | desde el inicio del segmento. En MoTeC i2 requiere marcar **«Include Distance Data»** al exportar; sin este canal el motor se detiene con un aviso claro (no se sintetiza desde la velocidad — [ADR 0017](decisions/0017-distancia-canal-requerido.md)) |
| `speed` | km/h | recomendado | |
| `throttle` | % (0-100) | recomendado | |
| `brake` | % (0-100) | recomendado | |
| `steering` | grados | recomendado | **negativo = izquierda** |
| `gear` | - | recomendado | entero; discreto en el remuestreo |
| `glat` | G | opcional | convención del logger (en MoTeC/AMS2: positivo = izquierda) |
| `glong` | G | opcional | |
| `rpm` | rpm | opcional | |
| `alt` | m | opcional | habilita el cálculo de pendiente por curva |

## Separación de vueltas

`split_laps()` corta el outing por, en orden de preferencia:
1. **Beacons** del log MoTeC (`Beacon Markers` en los metadatos) — la primera y última porción se marcan como out-lap/in-lap incompletas;
2. cambios del canal `lap_number`;
3. reinicios del canal de distancia (caída > 100m).

`fastest_lap()` elige la vuelta completa más rápida entre las que miden ≥90% de la más larga.

## Convención de distancia

- Metro **0 = inicio de la vuelta** (cruce de meta).
- La comparación se hace **por distancia**, no por tiempo: remuestreo de ambas vueltas a una rejilla uniforme (5m por defecto, `--step`).
- Interpolación lineal para canales continuos; valor anterior para discretos (`gear`).

## Detección de curvas (resumen del algoritmo)

1. **V-Min**: mínimo local de velocidad con prominencia ≥3 km/h en ventana de ±1.2s.
2. **Kink**: pico de |G lateral| > 2.2 sostenido, sin V-Min en ±80m (curvas rápidas sin frenada).
3. **Segmentación**: cada curva solo analiza su tramo (punto medio con las curvas vecinas, con tope de 450 m hacia atrás y 350 m hacia adelante) — evita contaminarse con la frenada de la curva siguiente.
4. **Frenada real**: último bloque de freno con pico ≥50%; los blips del trail braking no cuentan como inicio de frenada.
5. Hitos: `brake_start`, `turn_in` (|volante|>8° hacia el lado de la curva), `brake_release` (<2%), `throttle_on` (>5%), `apex` (V-Min), `full_throttle` (≥98% sostenido), `g_lat_max`, `lift` (en curvas sin freno). Cada hito lleva `d` (m), `t` (s), `v` (km/h).
6. **Overlap**: si `throttle_on.d < brake_release.d`, se registra `overlap_m` (solape gas/freno).
7. **Pendiente**: si hay canal `alt`, gradiente ±100m alrededor del ápex → `slope` (subida/bajada/plano) y `slope_pct`.

## Esquema de corners JSON

`fantasma detect` produce (y `--corners` consume):

```json
{
  "corners": [
    {
      "id": "C07",
      "name": "Curva del puente",        // opcional, lo añades tú
      "kind": "vmin",                     // vmin | kink
      "direction": "left",
      "segment_m": [7048, 7487],
      "no_brake": false,
      "overlap_m": 1,                     // solo si existe
      "max_steering_deg": 31.8,
      "slope": "bajada", "slope_pct": -6.7,
      "delta_s": 9.84,
      "milestones": {
        "brake_start": {"d": 7167, "t": 133.9, "v": 142, "gear": 2, "brake_pct": 100},
        "turn_in":     {"d": 7204, "t": 134.8, "v": 110, "gear": 1},
        "brake_release":{"d": 7236, "t": 135.7, "v": 77},
        "throttle_on": {"d": 7220, "t": 135.2, "v": 90, "throttle_pct": 17},
        "apex":        {"d": 7233, "t": 135.6, "v": 76, "gear": 1, "g_lat": 2.42},
        "full_throttle":{"d": 7349, "t": 139.1, "v": 118, "gear": 2},
        "g_lat_max":   {"d": 7230, "g_lat": 2.5}
      },
      "tolerances": {"brake_start_m": 10, "vmin_kmh": 4}   // opcional, para avisos
    }
  ]
}
```

Campos extra (`voice_name`, `description`, `coaching_priority`...) se conservan y son libres — otras herramientas pueden usarlos.

## API pública de `fantasma.core`

El paquete declara `__all__` con los símbolos de uso externo: `Lap`, `samples`, `detect_corners`, `extract_milestones`, `compare`, `delta_trace`, `resample` y el módulo `wear`. Funciones internas de `wear` (`_slip_index`, `_assist_count`, `_tyre_temp_avg`) llevan el prefijo `_` y no forman parte de la API estable.

`samples(lap)` — convierte un `Lap` en lista de dicts `[{canal: valor, ...}]` por muestra; útil para consumir la telemetría desde scripts externos.

## Salidas de `compare`

**`delta.csv`** — una fila por paso de la rejilla: `dist`, `delta_t` (s, positivo = el piloto pierde), y `ref_*`/`drv_*` para `speed`, `throttle`, `brake`, `steering`, `gear` y, si están presentes en el archivo, `glat`/`glong`. Solo se escriben las columnas de los canales que existen.

**`corners_compare.csv`** — una fila por curva: `id`, `name`, `apex_d`, `ref_vmin`, `drv_vmin`, `d_vmin`, `ref_brake_d`, `drv_brake_d`, `d_brake_m` (positivo = el piloto frena más tarde), `d_gas100_m`, `time_lost` (s, delta acumulado entre los extremos del segmento), `flags`; y, cuando el archivo trae canales de rueda/ABS, `ref_slip`/`drv_slip` (proxy de desgaste por curva) y `ref_abs`/`drv_abs` (activaciones de ABS en el segmento). Las columnas dependen de los datos disponibles.

**`summary` (dict interno de `compare()`)** — incluye desde v1.0 el campo `avisos` (lista de strings): mensajes de diagnóstico emitidos durante la comparación. Actualmente puede contener:

- `"delta sospechosamente grande (X s sobre vuelta de Y s): ¿la referencia y el piloto son del mismo circuito?"` — se emite cuando `abs(total_delta) > ref_laptime * 0.5`. Indica que los datos probablemente no son del mismo circuito.
- `"autos distintos: <ref> (ref) vs <piloto> (piloto)"` — aviso informativo cuando ambas vueltas tienen metadato `Vehicle` y difieren. Solo se emite si el metadato está disponible en los dos archivos; si falta en alguno, la degradación es silenciosa.
