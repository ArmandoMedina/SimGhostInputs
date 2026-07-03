# Auditoría Fase 1 — fantasma/core/

**Fecha:** 2026-07-03  
**Rama:** codex/sgi-v2-merge  
**Archivos auditados:** `lap.py`, `normalize.py`, `corners.py`, `compare.py`, `wear.py`, `__init__.py`  
**Tests contrastados:** `tests/core/` (6 archivos, cobertura estimada en la sección final)

---

## Veredicto

**El área core es funcionalmente sólida en el camino feliz, pero tiene 2 crashes alcanzables con entradas legítimas (críticos), 1 imprecisión sistemática en la métrica central del producto (delta por curva), y múltiples problemas de calidad que acumulan deuda técnica.**

---

## Hallazgos — ordenados por severidad

---

### [C-01] CRÍTICO · `normalize.py:44` — `fastest_lap` revienta con lista vacía

```python
def fastest_lap(laps, min_length_ratio=0.9):
    maxlen = max(l.length for l in laps)   # ValueError si laps == []
```

`max()` sobre un generador vacío lanza `ValueError: max() arg is an empty sequence`. La ruta normal que lo produce: `split_laps` filtra vueltas con `len(seg) <= 10` — si todas las vueltas de un outing son demasiado cortas (salida del pit, telemetría truncada), `laps` queda vacío y la llamada posterior a `fastest_lap(laps)` explota.

No existe ningún guard. La excepción no tiene contexto de usuario; el traceback sería confuso.

**Fix sugerido:** `if not laps: raise ValueError("No hay vueltas para comparar")` al inicio.

**Cobertura:** No hay ningún test con lista vacía.

---

### [C-02] CRÍTICO · `corners.py:53-54` — ZeroDivisionError en `detect_corners` cuando `dt = 0`

```python
dt = (data[-1]["time"] - data[0]["time"]) / max(1, len(data) - 1)
W  = max(3, int(round(vmin_window_s / dt)))   # ZeroDivisionError si dt == 0
```

Si `data` tiene exactamente 1 muestra: `dt = 0.0 / 1 = 0.0`, luego `1.2 / 0.0` = `ZeroDivisionError`.  
Si `data` tiene N >= 2 muestras pero todos los timestamps son idénticos (datos corruptos o simulador pausado): mismo resultado.

El `max(1, len(data) - 1)` protege el denominador del primer cálculo, pero **no** el de la división `vmin_window_s / dt`.

**Fix sugerido:** `if dt == 0.0: raise ValueError("La vuelta tiene duración cero o una sola muestra")`  
o `W = max(3, int(round(vmin_window_s / dt)) if dt > 0 else len(data) // 4)`.

**Cobertura:** No hay ningún test con vuelta de 1 muestra ni timestamps constantes.

---

### [M-01] MAYOR · `compare.py:360-362` — `delta_at` cuantiza a la rejilla sin interpolar; error sistémico en `time_lost`

```python
def delta_at(dist):
    i = min(int(dist / step), len(trace) - 1)
    return trace[max(0, i)]["delta_t"]
```

La traza proviene de `resample` con rejilla `[0, step, 2·step, …]`. Para `dist = 374.0` y `step = 5.0`, `int(374/5) = 74` → se usa el punto en `dist = 370.0`, ignorando los últimos 4 m del segmento. El error de truncamiento en cada límite es hasta `step = 5 m`.

A 100 km/h, 5 m equivale a ~0,18 s. El cálculo `time_lost = delta_at(hi) - delta_at(lo)` tiene errores independientes en `hi` y en `lo`; en el peor caso se acumulan. El producto imprime `time_lost` con **3 decimales** (milisegundos) pero la precisión real puede ser del orden de decenas de ms.

La solución correcta es interpolar linealmente entre `trace[i]` y `trace[i+1]`:
```python
i = min(int(dist / step), len(trace) - 2)
f = (dist - i * step) / step
return trace[i]["delta_t"] * (1 - f) + trace[i + 1]["delta_t"] * f
```

**Cobertura:** No hay ningún test que verifique la precisión numérica de `time_lost` por curva.

---

### [M-02] MAYOR · `compare.py:102` — `_fmt_signed` contiene un `replace` no-op; bug de display silencioso

```python
def _fmt_signed(value, unit="", digits=0):
    ...
    return ("%+.*f%s" % (digits, value, unit)).replace("+", "+")
```

`.replace("+", "+")` reemplaza `"+"` con `"+"`: es una operación nula. El formato `%+.*f` ya incluye signo, por lo que los valores positivos muestran `"+5"`, no `"5"`. Si la intención era eliminar el `+` de los positivos (convenio habitual en coaching en español) o reemplazarlo por un símbolo distinto, esa lógica está rota.

Los mensajes de `corner_coaching` usan `_fmt_signed` para `d_brake`, `d_peak`, `d_vmin`, `d_gas`, `d_g`. Los mensajes de acción ya incluyen `+%d m`/`-%d m` en texto literal, por lo que el output del coaching tiene doble codificación de signo en algunas ramas y ninguna en otras. El bug es silencioso — no crashea, solo muestra datos potencialmente confusos.

**Cobertura:** Los tests de coaching comprueban strings literales como `"Acelera antes"` pero no validan el formato numérico de los `signals[]`.

---

### [M-03] MAYOR · `normalize.py:33` y `37-38` — doble asignación de `is_complete`; código muerto que confunde

```python
# Línea 33 — primera asignación (dentro del bucle)
seg.meta["is_complete"] = i not in (0, len(bounds) - 2) or not cuts

# Líneas 37-38 — segunda asignación, SIEMPRE sobreescribe cuando cuts es truthy
if cuts:
    for lap_ in laps:
        lap_.meta["is_complete"] = 0 < lap_.meta["lap_index"] < len(bounds) - 2
```

Cuando `cuts` es truthy (beacon, lap_number o reinicio de dist), la línea 33 fija `is_complete`, pero inmediatamente después el bloque `if cuts:` la sobreescribe con exactamente el mismo criterio lógico. La línea 33 es **código muerto** cuando hay cortes.

Riesgo de mantenimiento: un futuro desarrollador que modifique la lógica en línea 33 sin saber que línea 38 la pisa (o viceversa) introducirá un bug difícil de detectar.

**Cobertura:** No hay ningún test que verifique el valor del campo `is_complete` en las vueltas resultantes.

---

### [M-04] MAYOR · `corners.py:109-116` / `compare.py:333-338` — duplicación exacta de detección de bloques de frenada

La lógica de agrupación de bloques de freno (gap < 0.3 s, umbral `brake_on = 10%`) está copiada literalmente en dos lugares distintos:

- `corners.py` → `extract_milestones` (líneas 109-116)
- `compare.py` → `_corner_metrics` (líneas 333-338)

Cualquier corrección en uno no se propaga al otro. El campo `brake_d` que `_corner_metrics` reporta en el `row` de comparación y el `brake_start` que `extract_milestones` pone en los milestones de la referencia usan criterios idénticos pero mantenidos por separado.

**Fix sugerido:** extraer en una función privada `_detect_brake_blocks(samples, brake_on=10, gap_s=0.3)` en un módulo compartido (o en `lap.py` / `normalize.py`).

---

### [M-05] MAYOR · `normalize.py:57` — `resample` empieza la rejilla en `x = 0.0` sin verificar `d[0]`

```python
x = 0.0
while x <= d[-1]:
    grid.append(x)
    x += step
```

Si se pasa una vuelta cuyo canal `dist` no empieza en 0 (p. ej. una vuelta cargada directamente sin pasar por `slice_time`), los primeros puntos de la rejilla quedan fuera del rango de los datos. El clamp `i = max(0, ...)` silencia el error y extrapola usando el primer par de muestras. El resultado es silenciosamente incorrecto y no hay ningún aviso.

Además, `resample` no valida que `lap.col("dist")` no sea `None`. Si el canal dist está ausente, `d = None` y `d[-1]` lanza `TypeError` sin contexto útil (a diferencia de `detect_corners` que da `ValueError` explícito con mensaje de usuario).

**Cobertura:** El test `test_resample_linear_interpolation_in_range` usa `dist = [0.0, 10.0]`, siempre parte de 0. No hay test con dist inicial distinto de 0.

---

### [m-01] MENOR · `compare.py:297` — `"Pierdes %.3f s" % time_lost` crashea si `time_lost` es `None` explícito

```python
time_lost = row.get("time_lost", 0.0)   # default 0.0 si KEY AUSENTE
# ...
lead = "Pierdes %.3f s en %s" % (time_lost, name)   # TypeError si value es None
```

`dict.get(k, default)` devuelve `None` si `row["time_lost"] = None` (la clave existe pero el valor es `None`). En ese caso `status` queda en "loss" (`_is_num(None)` es False) y la línea 297 lanza `TypeError: %f format: a real number is required, not NoneType`.

Ocurre si un importer escribe `row["time_lost"] = None` en lugar de omitir la clave.

**Fix:** `if time_lost is not None else "?"` o proteger con `_round_or_none`.

---

### [m-02] MENOR · `compare.py:317` — `_segment()` puede devolver `None`; unpack sin guard en dos sitios

```python
def _segment(corner):
    return corner.get("segment_m") or corner.get("range_m")   # None si ninguno existe
```

Ambos callers desempaquetan directamente:
- `compare.py:375`: `lo, hi = _segment(c)` → `TypeError: cannot unpack non-iterable NoneType`
- `compare.py:323`: `lo, hi = _segment(corner)` → ídem

Esto solo afecta si se pasan corners externos (sin `segment_m` ni `range_m`). `extract_milestones` siempre pone `segment_m`, pero la firma de `compare(..., corners=None)` acepta corners arbitrarios.

**Cobertura:** No hay ningún test con corners externos sin `segment_m`.

---

### [m-03] MENOR · `wear.py:45` — `ratios or calibrate(lap)` falla silenciosamente con dict vacío

```python
ratios = ratios or calibrate(lap)
```

En Python, `{}` es falsy. Si un caller pasa `ratios={}` (resultado de un calibrate parcial fallido que no devolvió `None`), se dispara `calibrate(lap)` inesperadamente. El contrato público debería ser `if ratios is None: ratios = calibrate(lap)`.

---

### [m-04] MENOR · `corners.py:37` — parámetro `sample_rate_hint` declarado pero nunca usado

```python
def detect_corners(lap, vmin_window_s=1.2, vmin_prominence_kmh=3.0, kink_glat=2.2, sample_rate_hint=None):
    """...
    sample_rate_hint: reservado para uso futuro; dt se calcula directamente de los datos.
    """
```

El parámetro figura en la API pública pero no hay ninguna referencia a `sample_rate_hint` en el cuerpo. Expande la superficie de la API sin beneficio y puede generar confusión (¿el hint tiene efecto? ¿en qué versión?).

---

### [m-05] MENOR · `corners.py:168` — IDs de curva no son secuenciales si hay eventos filtrados

```python
"id": "C%02d" % (n + 1),   # n = índice en events[], no en corners[]
```

Cuando un evento se salta (`if not pre or len(seg) < 5: continue`), el contador `n` sigue avanzando. El resultado: `C01`, `C03`, `C04` sin `C02`. Consumidores downstream que esperan IDs secuenciales (p. ej. lógica de comparación por ID) podrían perder curvas silenciosamente.

---

## Revisión de principios del repo

| Principio | Estado |
|-----------|--------|
| **Stdlib pura — sin dependencias externas** | Cumple. Imports: `dataclasses`, `bisect` (stdlib). Cero imports de terceros. |
| **Determinismo — misma entrada, misma salida** | Cumple. No hay estado global mutable, no hay `random`, no hay `datetime`, no hay I/O. |
| **Código muerto** | Hallazgo M-03 (doble asignación `is_complete`), M-02 (`_fmt_signed` replace nop). |

---

## Cobertura de tests — brechas críticas

| Comportamiento crítico | Test existe | Nota |
|------------------------|-------------|------|
| `fastest_lap([])` vacío | NO | C-01 sin cobertura |
| `detect_corners` con 1 muestra / dt=0 | NO | C-02 sin cobertura |
| `is_complete` correcto en split_laps | NO | M-03 sin cobertura |
| `time_lost` precisión por curva (delta_at) | NO | M-01 sin cobertura |
| Estrategia beacon en split_laps | NO | Solo lap_number está testeado |
| Estrategia dist-reset en split_laps | NO | Solo lap_number está testeado |
| Corners externos sin `segment_m` | NO | m-02 sin cobertura |
| `resample` con dist que no empieza en 0 | NO | M-05 sin cobertura |
| `corner_coaching` con `time_lost=None` | NO | m-01 sin cobertura |
| `_fmt_signed` formato de signo en signals[] | NO | M-02 sin cobertura |

Tests que sí cubren bien:
- Degradación graceful por canales ausentes (32 combinaciones en `test_degradacion_canales.py`) — excelente cobertura sistemática.
- `wear_budget` — cobertura completa incluyendo bordes.
- `slip_series` signos, índice, carga extensiva — bien cubierto.
- `detect_corners` requiere speed y dist — bien cubierto.
- Convención de signo `delta_t` (piloto más lento = positivo) — cubierto y documentado.

---

## Resumen de conteo

| Severidad | Cantidad |
|-----------|----------|
| CRÍTICO   | 2        |
| MAYOR     | 5        |
| MENOR     | 5        |
| **Total** | **12**   |
