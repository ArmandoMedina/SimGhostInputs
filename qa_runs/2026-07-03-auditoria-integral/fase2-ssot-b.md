# Auditoría SSOT-B — Lote docs/formato-datos.md, docs/hud-reference.md, docs/glosario.md, PRODUCT_BRIEF.md

**Fecha**: 2026-07-03  
**Rama**: codex/sgi-v2-merge  
**Auditor**: Agente de QA (Claude Sonnet 4.6)  
**Método**: Lectura directa de los 4 docs + código canónico (`fantasma/core/*.py`, `fantasma/viz/overlay.py`, `fantasma/importers/__init__.py`). Sin ediciones.

---

## Criterios aplicados

- §8 CONTRIBUTING.md: cada hecho vive en un único doc; los demás enlazan.
- Regla de vocabulario §8: nombres de colores README↔hud-reference y campos de salida formato-datos↔código deben coincidir literal.
- Se verificaron: parámetros de algoritmos, hex de colores, nombres de campos, orden de campos en la franja, tipos de retorno de API, y alcance implementado vs declarado.

---

## 1. docs/formato-datos.md

Código de referencia: `fantasma/core/lap.py`, `corners.py`, `compare.py`, `normalize.py`, `wear.py`, `__init__.py`.

### Verificaciones que pasan ✅

| Afirmación en doc | Verificación |
| :-- | :-- |
| Canales canónicos: `time`, `dist`, `speed`, `throttle`, `brake`, `steering`, `gear`, `glat`, `glong`, `rpm`, `alt` | Coincide con docstring de `lap.py` campo por campo |
| `split_laps()` orden: beacons → `lap_number` → dist drop > 100 m | Coincide con lógica en `normalize.py` líneas 16-25 |
| `fastest_lap()`: vuelta completa más rápida entre las ≥ 90% de la más larga | `min_length_ratio=0.9` en `normalize.py` línea 42 |
| V-Min: prominencia ≥ 3 km/h en ventana ±1.2 s | `vmin_window_s=1.2, vmin_prominence_kmh=3.0` en `corners.py` línea 36 |
| Kink: |G lateral| > 2.2, sin V-Min en ±80 m | `kink_glat=2.2` y guarda de 80 m en `corners.py` líneas 76-78 |
| Segmentación: tope 450 m atrás / 350 m adelante | `max(lo, ad - 450), min(hi, ad + 350)` en `corners.py` líneas 100 |
| Frenada real: último bloque con pico ≥ 50% | `brake_strong=50` en `corners.py` línea 86 |
| Hitos: `brake_start`, `turn_in` (> 8°), `brake_release` (< 2%), `throttle_on` (> 5%), `apex`, `full_throttle` (≥ 98%), `g_lat_max`, `lift` | Todos presentes en `extract_milestones()` |
| `overlap_m`: si `throttle_on.d < brake_release.d` | Lógica coincide en `corners.py` líneas 154-155 |
| Pendiente ±100 m alrededor del ápex | `ad - 100` / `ad + 100` en `corners.py` líneas 189-190 |
| `delta.csv` columnas: `dist`, `delta_t`, `ref_*`/`drv_*` para speed/throttle/brake/steering/gear/glat/glong/rpm | Loop exacto en `delta_trace()`, `compare.py` líneas 20-26 |
| `corners_compare.csv` columnas: id, name, segment_start_m, segment_end_m, apex_d, ref_vmin, drv_vmin, drv_vmin_d, d_vmin, ref_brake_d, drv_brake_d, d_brake_m, ref_gas100_d, drv_gas100_d, d_gas100_m, time_lost, flags, ref_slip/drv_slip, ref_abs/drv_abs | Coincide con `compare()` en `compare.py` |
| `corner_coaching` devuelve: status (loss/gain/neutral), summary, actions, segment_m, braking, apex, throttle, lateral, gear | Coincide con `return` en `corner_coaching()` |
| Avisos: 3 mensajes (delta grande, autos distintos, piloto más rápido) | Los 3 presentes en `compare.py` líneas 419-434 |
| `__all__`: Lap, samples, detect_corners, extract_milestones, compare, corner_coaching, delta_trace, resample, wear | Exacto en `core/__init__.py` |
| Funciones privadas de wear: `_slip_index`, `_assist_count`, `_tyre_temp_avg` | Prefijo `_` confirmado en `wear.py` |
| DEADBAND 2% para slip | `DEADBAND_PCT = 2.0` en `wear.py` línea 13 |

### Drifts encontrados

#### DRIFT FD-01 — ALTO: `samples(lap)` devuelve tupla, no lista

**Afirmación doc** (§ "API pública de fantasma.core"):
> `samples(lap)` — convierte un `Lap` en lista de dicts `[{canal: valor, ...}]` por muestra; útil para consumir la telemetría desde scripts externos.

**Realidad en código** (`corners.py`, línea 14-33):
```python
def samples(lap):
    keys = [...]
    n = len(lap)
    return [{k: lap.col(k)[i] for k in keys} for i in range(n)], keys
```
La función devuelve una **tupla** `(list[dict], list[str])`, no una lista de dicts. Todos los sitios internos que la llaman hacen unpacking `data, _ = samples(lap)` o `data, keys = samples(lap)`. Un llamador externo que espere `[{...}]` recibirá un `tuple` y romperá si itera esperando solo dicts con los canales en la primera posición.

**Severidad**: ALTA — `samples` está en `__all__` y el doc lo propone como API de integración con scripts externos.

---

**Veredicto global para formato-datos.md**: 1 drift ALTO (tipo de retorno de `samples`), resto de afirmaciones verificadas y correctas.

---

## 2. docs/hud-reference.md

Código de referencia: `fantasma/viz/overlay.py`.

### Verificaciones que pasan ✅

| Afirmación en doc | Verificación |
| :-- | :-- |
| Panel gas — piloto normal: verde `#00c853` | `_GAS = "#00c853"` ✅ |
| Panel gas — piloto TCS: violeta `#e040fb` | `_TCS = "#e040fb"` ✅ |
| Panel gas — ref normal: gris `#9aa0a6` | `_REF = "#9aa0a6"` ✅ |
| Panel gas — ref TCS: violeta tenue `#a87fd0` | `_RTCS = "#a87fd0"` ✅ |
| Panel freno — piloto normal: rojo `#ff1744` | `_FRENO = "#ff1744"` ✅ |
| Panel freno — piloto ABS: ámbar `#ffab00` | `_ABS = "#ffab00"` ✅ |
| Panel freno — ref normal: gris `#9aa0a6` | `_REF = "#9aa0a6"` ✅ |
| Panel freno — ref ABS: ámbar tenue `#e0a526` | `_RABS = "#e0a526"` ✅ |
| Panel volante — piloto normal (< P75): azul `#40c4ff` | `_VOL = "#40c4ff"` ✅ |
| Panel volante — piloto P75–P90: amarillo `#fdd835` | `_GMED = "#fdd835"` ✅ |
| Panel volante — piloto > P90: naranja `#ff6d00` | `_GMAX = "#ff6d00"` ✅ |
| Panel volante — ref normal: gris `#9aa0a6` | `_REF = "#9aa0a6"` ✅ |
| Panel volante — ref P75–P90: amarillo apagado `#6b5e00` | `_RGMED = "#6b5e00"` ✅ |
| Panel volante — ref > P90: naranja apagado `#7a3300` | `_RGMAX = "#7a3300"` ✅ |
| Ventana deslizante 520 m (320 atrás, 200 adelante) | `W_BEFORE = 320`, `W_AFTER = 200` ✅ |
| Cursor: línea amarilla vertical | `axvline(color=_YEL)` donde `_YEL = "#fdd835"` ✅ |
| Retención ABS/TC: ~8 m | `HOLD_M = 8` ✅ |
| DESLIZ: ventana ~40 m detrás del cursor | `SLIP_WIN_M = 40` ✅ |
| P75/P90 calculados sobre el `|G-lat|` de la referencia | `glat_sorted = sorted(abs(x) for x in glat_raw)` + percentiles ✅ |
| Render paralelo: `cpu_count() - 1` workers | `n_workers = max(1, (os.cpu_count() or 1) - 1)` ✅ |
| Pickle compacto por chunk (~4 MB → ~1 MB, Nordschleife) | `_render_parallel` slice por rango de distancia ✅ |
| Curva/V-Min objetivo: nombre del track pack o id `C01…` | `c.get("name", c.get("id", ""))` ✅ |
| GAP positivo → rojo, negativo → verde | `set_color(_FRENO if gap > 0 else _GAS)` ✅ |

### Drifts encontrados

#### DRIFT HUD-01 — ALTO: orden de campos km/h y metros invertido en anatomía y tabla

**Afirmación doc** — anatomy ASCII:
```
│  GAP +0.41s │ ΔV -8 │ DESLIZ 1.2 │ ABS TC │ GASTO 12 │ M 3 │ 187 km/h │ 3412 m │
```
Orden al final: **gear → km/h → metros**

**Afirmación doc** — tabla "Franja de datos":
Las filas aparecen en orden: MARCHA → **km/h** → **metros**.

**Realidad en código** (posiciones x en `overlay.py`):
```python
self.t_gear_val  = fig.text(0.690, ...)   # MARCHA (valor)
fig.text(0.635, 0.97, "MARCHA", ...)      # MARCHA (label)
fig.text(0.730, 0.97, "m", ...)           # metros (label)
self.t_dist_val  = fig.text(0.755, ...)   # metros (valor)
fig.text(0.812, 0.97, "km/h", ...)        # km/h (label)
self.t_spd_val   = fig.text(0.835, ...)   # km/h (valor)
```
Orden real: **MARCHA (0.690) → m/metros (0.730-0.755) → km/h (0.812-0.835)**

El doc dice "M 3 | 187 km/h | 3412 m" pero el código renderiza "MARCHA | m | km/h". Los dos últimos campos están **al revés** en el doc.

**Severidad**: ALTA — la anatomía es la guía visual que usa el piloto para entender el HUD. Alguien leyendo el doc y mirando el overlay verá los campos en el orden opuesto al documentado.

---

#### DRIFT HUD-02 — MEDIO: tabla de "Avisos en el reporte de comparación" omite el tercer aviso

**Afirmación doc** — tabla §"Avisos en el reporte de comparación":
Solo lista 2 avisos:
1. "Delta sospechosamente grande" — condición `abs(total_delta) > ref_laptime * 0.5`
2. "Autos distintos" — metadato `Vehicle` disponible y difiere

**Realidad en código** (`compare.py`, líneas 419-434):
```python
avisos.append("delta sospechosamente grande...")   # aviso 1
avisos.append("autos distintos: ...")              # aviso 2
avisos.append("piloto más rápido que la referencia (%.1f s de ventaja)...")  # aviso 3 — AUSENTE EN DOC
```
El tercer aviso se emite cuando `total_delta < -1.0` y se agregó en `compare.py` (commit del Unreleased: "aviso cuando el piloto va más de 1 s más rápido que la referencia"). La tabla de `hud-reference.md` no lo refleja.

Nota: `formato-datos.md` sí documenta los 3 avisos correctamente. El drift es específico de `hud-reference.md`.

**Severidad**: MEDIA — omisión de un aviso de diagnóstico documentado en el SSOT primario (`formato-datos.md`) pero ausente en este doc secundario.

---

#### DRIFT HUD-03 — BAJO: inconsistencia TCS / TC en el propio doc

**Afirmación doc** — franja de datos (campo):
> "ABS / TC | Luces de estado: el texto se enciende en su color (ABS ámbar, **TC** violeta)"

**Afirmación doc** — tabla colores gas:
> "**TCS** activo (el sim está limitando el gas por deslizamiento)"

**Afirmación doc** — glosario (referenciado):
> "Activaciones de ABS / **TCS**"

**Realidad en código**:
```python
self.t_tc_light = fig.text(0.448, 0.985, "TC", ...)   # label visible = "TC"
_TCS = "#e040fb"   # nombre de constante interna
```
El label visible en el HUD es "TC" (no "TCS"), lo que coincide con la descripción de la franja y la anatomía ASCII del doc. Sin embargo, las tablas de colores del mismo `hud-reference.md` dicen "TCS activo". El doc es internamente inconsistente; la inconsistencia con el código (que muestra "TC") existe en las tablas de colores.

**Severidad**: BAJA — solo en las tablas de colores; la descripción funcional dice "TC" correctamente. No rompe el uso del HUD.

---

**Veredicto global para hud-reference.md**: 1 drift ALTO (orden km/h vs metros), 1 MEDIO (aviso 3 ausente), 1 BAJO (TCS/TC en tablas de colores).

---

## 3. docs/glosario.md

Código de referencia: `fantasma/core/wear.py`, `corners.py`, `normalize.py`, `compare.py`, `viz/overlay.py`.

### Verificaciones que pasan ✅

| Término | Verificación |
| :-- | :-- |
| Comparación por distancia | Coincide con `delta_trace()` en `compare.py` |
| GAP: positivo (rojo) = piloto más lento; negativo (verde) = más rápido | Coincide con `overlay.py` lógica de color |
| ΔV: piloto − referencia en metro del cursor | Coincide con `dv = int(drv_v - ref_v)` en `overlay.py` |
| `time_lost`: delta acumulado entre extremos del segmento | Coincide con `compare.py` línea 386 |
| V-Min: velocidad mínima dentro de la curva | Coincide con `apex = min(..., key=lambda s: s["speed"])` |
| Hitos: los 8 hitos con sus umbrales (8°, 2%, 5%, 98%) | Coinciden con los defaults de `extract_milestones()` |
| `overlap_m`: metros con gas y freno simultáneos | Coincide con lógica en `corners.py` |
| `segment_m`: tope 450 m atrás / 350 m adelante | Coincide con `corners.py` |
| Deslizamiento (slip): negativo = bloqueo, positivo = patinaje | Coincide con `slip_series()` en `wear.py` |
| Banda muerta 2% | `DEADBAND_PCT = 2.0` en `wear.py` ✅ |
| DESLIZ: promedio ~40 m detrás del cursor | `SLIP_WIN_M = 40` ✅ |
| Carga de deslizamiento: slip integrado sobre distancia, aditiva | Coincide con `slip_load()` en `wear.py` |
| Estado desgaste stint: ok/yellow/red/burst | Coincide con `wear_budget()` en `wear.py` |
| Cursor: línea amarilla vertical, 320 m atrás / 200 m adelante | Coincide con `W_BEFORE=320`, `W_AFTER=200`, `_YEL` en `overlay.py` |
| Paso (step): 5 m por defecto, interpolación lineal; discretos = valor anterior | Coincide con `resample()` en `normalize.py` |
| Beacon: marcador de cruce de meta del log MoTeC | Coincide con `split_laps()` lógica beacons |

### Drifts encontrados

#### DRIFT GLO-01 — MEDIO: `slip_index` sin prefijo de privado

**Afirmación doc** (sección "Desgaste de goma"):
> **`slip_index`** — **intensidad de un tramo**
> El promedio del exceso de slip en un tramo (una curva o una vuelta entera). Mismo concepto que DESLIZ pero sobre el tramo que se le pida. Es una *intensidad*, no una cantidad: **no se puede sumar** entre curvas.

**Realidad en código** (`wear.py`, línea 67):
```python
def _slip_index(lap, d0=None, d1=None, slip=None, ratios=None):
```
El glosario documenta `slip_index` (sin guion bajo) como concepto accesible, pero el código lo implementa como `_slip_index` (privado). `formato-datos.md` lo llama correctamente `_slip_index` y lo lista como función privada no estable. El glosario omite el prefijo `_`, contradiciendo a `formato-datos.md` y potencialmente llevando a contributors a llamar `wear._slip_index()` directamente.

**Severidad**: MEDIA — inconsistencia entre docs sobre si es API pública o privada; `formato-datos.md` (SSOT para la API) dice privado.

---

#### DRIFT GLO-02 — BAJO: función pública `slip_load` no tiene entrada en el glosario

**Afirmación doc**: El glosario define "Carga de deslizamiento" como concepto pero no menciona la función `slip_load` por nombre.

**Realidad en código** (`wear.py`, línea 84):
```python
def slip_load(lap, d0=None, d1=None, slip=None, ratios=None):
```
`slip_load` es pública (sin prefijo `_`). Su par de concepto está en el glosario bajo "Carga de deslizamiento" pero la función en sí no está nombrada. Igual para `wear_budget` (pública, línea 157) que aparece como concepto bajo "Desgaste acumulado del stint (fantasma wear)" sin nombrar la función.

**Severidad**: BAJA — el concepto está cubierto; falta solo el nombre de símbolo de código.

---

#### DRIFT GLO-03 — BAJO: TCS/TC (mismo que HUD-03)

El glosario dice "Activaciones de ABS / **TCS**" pero el HUD muestra "TC". Misma raíz que HUD-03. Baja severidad.

---

**Veredicto global para glosario.md**: 1 drift MEDIO (slip_index sin guion bajo), 2 drifts BAJOS (slip_load/wear_budget sin nombre de símbolo, TCS/TC). No hay términos de v2 significativos que falten respecto al código (compose y cursor ya están definidos).

---

## 4. PRODUCT_BRIEF.md

Código de referencia: `fantasma/importers/__init__.py`, `fantasma/ui/` (estructura de archivos), CHANGELOG.md.

### Verificaciones que pasan ✅

| Afirmación en doc | Verificación |
| :-- | :-- |
| Comparación metro a metro, sin IA, sin red, sin nube | Sigue siendo correcto; `compare.py` es aritmética pura |
| CLI primero, UI como capa opcional | Sigue correcto; `fantasma/cli.py` existe |
| Salidas estándar: CSV, Markdown, PNG, WebM | Confirmado en `compare.py`, `viz/report.py`, `viz/overlay.py` |
| Overlay VP9/ProRes con canal alfa | Confirmado en `render_overlay()`, `overlay.py` |
| Auto-sincronización | `fantasma/viz/sync.py` existe |
| Sin IA o LLM en el pipeline | Confirmado: `corner_coaching()` es aritmética pura |
| AGPL-3.0 | No revisado en código; pertenece a `pyproject.toml` (fuera de scope) |
| Importadores: MoTeC CSV/XLSX, CSV genérico | Confirmado en `importers/__init__.py` — únicos implementados |

### Drifts encontrados

#### DRIFT PB-01 — CRÍTICO: UI declarada como Streamlit; es NiceGUI desde v2.0

**Afirmación doc** (§6 "Está dentro de este repositorio"):
> | Interfaz gráfica local | Streamlit en localhost, sin hosting, datos siempre locales |

**Realidad en código**:
- Archivos `fantasma/ui/ng_app.py`, `ng_step0.py`–`ng_step4.py`, `ng_state.py`, `ng_helpers.py` — frontend NiceGUI
- CHANGELOG Unreleased: *"UI NiceGUI v2.0: nuevo frontend de escritorio nativo (pywebview) que **sustituye a Streamlit como UI principal**. Entry point `fantasma-ng`."*
- `CONTRIBUTING.md` §8 SSOT table: `docs/benchmark-ui-framework.md | Por qué NiceGUI y no las alternativas; cómo se empaqueta como instalador doble-click`

El doc fundacional del proyecto (`PRODUCT_BRIEF` es "el norte") declara la tecnología de UI incorrecta. NiceGUI no aparece en ningún lugar del documento. El empaquetado como instalador doble-clic (via `nicegui-pack` + Inno Setup) es una característica central de v2.0 que también está ausente.

**Severidad**: CRÍTICA — es el doc de norte y describe la UI con la tecnología equivocada.

---

#### DRIFT PB-02 — MEDIO: "Nuevos importadores" (iRacing .ibt, .ld, SimHub CSV) en tabla "Está dentro" pero no implementados

**Afirmación doc** (§6, tabla "Está dentro"):
> | Nuevos importadores | iRacing `.ibt`, `.ld` directo, SimHub CSV, otros formatos |

**Realidad en código** (`fantasma/importers/__init__.py`):
```python
if ext in (".csv", ".xlsx"):
    # MoTeC CSV o genérico
    ...
raise ValueError("Formato no soportado: %s" % ext)
```
Los únicos formatos soportados son `.csv` y `.xlsx` (MoTeC o CSV genérico). No existe ningún importador de iRacing `.ibt`, `.ld`, ni SimHub CSV en `fantasma/importers/`. Listarlo en "Está dentro" es falso; debería estar en §7 "Pendiente post-v1.0".

**Severidad**: MEDIA — declara capacidad no implementada como dentro de scope actual.

---

#### DRIFT PB-03 — MEDIO: "Historial entre sesiones" aparece en §6 "Está dentro" Y en §7 "Pendiente"

**Afirmación doc §6** (tabla "Está dentro"):
> | Historial entre sesiones | Comparación de tendencias entre tandas (diferido a post-v1.0) |

**Afirmación doc §7** (tabla "Pendiente post-v1.0"):
> | Histórico entre sesiones | Comparar el rendimiento en una curva a lo largo de varias tandas. Ver si se progresa o se retrocede |

El mismo ítem aparece en dos secciones contradictorias. Además, la nota "(diferido a post-v1.0)" dentro de la tabla "Está dentro" es internamente incoherente: si está diferido, no está dentro.

**Severidad**: MEDIA — confunde el alcance actual vs. futuro.

---

#### DRIFT PB-04 — BAJO: §10 titulado "Concepto de UX" cuando ya está implementado

**Afirmación doc** (§10 encabezado):
> ## 10. Concepto de UX — Drill-down por curva

El cuerpo del mismo §10 dice: *"Primera versión implementada el 2026-06-30 como panel de Paso 2 basado en `corner_coaching(row, trace)`."*

CHANGELOG v1.0.0: *"Drill-down por curva en UI Paso 2: la tabla de curvas ahora selecciona por defecto la mayor pérdida y muestra un panel accionable..."*

La sección dice "Concepto" pero la característica está en producción desde v1.0.0. El cuerpo lo reconoce, pero el encabezado es engañoso.

**Severidad**: BAJA — inconsistencia de encabezado, subsanada en el cuerpo del propio §10.

---

**Veredicto global para PRODUCT_BRIEF.md**: 1 drift CRÍTICO (Streamlit vs NiceGUI), 2 drifts MEDIOS (importadores no implementados en scope, historial en dos tablas), 1 BAJO (título de §10).

---

## Resumen ejecutivo

### Veredicto por documento

| Documento | Veredicto | Drifts |
| :-- | :-- | :-- |
| `docs/formato-datos.md` | 1 drift ALTO localizado — el resto del contenido es fiel al código | 1 ALTO |
| `docs/hud-reference.md` | 3 drifts — el orden visual del HUD y el aviso faltante son los más urgentes | 1 ALTO, 1 MEDIO, 1 BAJO |
| `docs/glosario.md` | 3 drifts menores — vocabulario correcto, gaps de exactitud de símbolo | 1 MEDIO, 2 BAJOS |
| `PRODUCT_BRIEF.md` | Doc de norte con la tecnología de UI equivocada — corrección urgente | 1 CRÍTICO, 2 MEDIOS, 1 BAJO |

### Conteo por severidad

| Severidad | Cantidad |
| :-- | :-- |
| CRÍTICO | 1 |
| ALTO | 2 |
| MEDIO | 4 |
| BAJO | 5 |
| **Total** | **12** |

### Los 3 drifts más graves

1. **PB-01 (CRÍTICO)** — `PRODUCT_BRIEF.md` §6 dice "Streamlit en localhost" como UI; la UI principal desde v2.0 es NiceGUI con pywebview. NiceGUI no aparece en ningún lugar del doc de norte. El empaquetado como instalador Windows doble-clic (nicegui-pack + Inno Setup) también está ausente.

2. **HUD-01 (ALTO)** — `hud-reference.md` anatomy ASCII y tabla de franja muestran el orden `MARCHA | km/h | metros`, pero el código renderiza `MARCHA | m (dist) | km/h`. Los últimos dos campos están invertidos respecto al doc. Posiciones en `overlay.py`: metros en 0.730-0.755, km/h en 0.812-0.835.

3. **FD-01 (ALTO)** — `formato-datos.md` declara que `samples(lap)` (API pública en `__all__`) devuelve `[{canal: valor, ...}]`, pero el código devuelve la tupla `(list[dict], list[str])`. Todo uso interno hace unpacking `data, _ = samples(lap)`; un script externo que trate el resultado como lista romperá.

---

*Reporte solo de lectura — no se editó ningún archivo del repositorio.*
