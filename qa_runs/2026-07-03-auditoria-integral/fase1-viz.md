# Auditoria fase 1 — fantasma/viz/ (pre-release v2.0.0)

**Fecha:** 2026-07-03
**Rama:** codex/sgi-v2-merge
**Auditor:** agente QA integral
**Alcance:** fantasma/viz/ (charts, compose, hud_preview, pacenotes, report, sync, overlay
interacciones con compose/sync) — *se excluye la logica interna del render paralelo de
overlay.py revisada por separado (commit 73f5ac1).*

---

## Resumen ejecutivo

El area tiene deuda tecnica concentrada en tres puntos: (a) manejo de errores de
subprocesos ffmpeg inconsistente entre modulos, (b) uso de asyncio.run() en un modulo
que se llama desde un event-loop activo (NiceGUI), y (c) tres modulos sin ninguna
cobertura de tests. No hay bugs de logica pura criticos en compose/sync/pacenotes;
los hallazgos mas graves son de estabilidad operativa e infraestructura de calidad.

---

## Hallazgos

### H-01 [CRITICO] overlay.py:627 — _run_ffmpeg descarta stderr; fallo de encoding es opaco

**Archivo:** `fantasma/viz/overlay.py` lineas 623-644

```python
proc = subprocess.Popen(cmd_p, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
```

Cuando la codificacion VP9 o ProRes falla (disco lleno, codec no compilado, etc.),
`proc.returncode != 0` y se lanza `subprocess.CalledProcessError(proc.returncode, cmd)`.
El mensaje de error NO incluye ninguna salida de ffmpeg porque stderr va a DEVNULL.
El usuario solo ve el codigo de retorno y la lista de argumentos del comando.

El contraste con `compose.py` es directo: la rama con `progress=True` captura stderr
en un `TemporaryFile` y extrae las ultimas 15 lineas en el RuntimeError. `_run_ffmpeg`
debia adoptar el mismo patron.

La gravedad es critica porque este paso ocurre DESPUES de potencialmente decenas de
minutos de render de frames: un fallo silencioso aqui desperdicia todo ese tiempo sin
dar informacion para diagnosticar.

**Impacto:** usuario incapaz de diagnosticar fallos de encoding; workaround: ninguno desde
la UI.
**Correccion:** capturar stderr en TemporaryFile o PIPE, incluirlo en la excepcion (igual
que compose.py lineas 316-337).

---

### H-02 [CRITICO] pacenotes.py:227 — asyncio.run() dentro de un event-loop activo (NiceGUI crash)

**Archivo:** `fantasma/viz/pacenotes.py` lineas 213-254 (funcion `build_voice_pack`)

```python
asyncio.run(edge_tts.Communicate(text, voice=voice).save(mp3))
```

`asyncio.run()` crea y destruye un nuevo event-loop. Si se invoca desde un contexto
donde ya hay un loop en ejecucion (NiceGUI usa un loop de uvicorn/asyncio permanente;
Streamlit async handlers tambien), lanza:

    RuntimeError: This event loop is already running

Esto hace que la generacion de pace notes de voz sea **completamente inutilizable desde
la UI NiceGUI** (el path ui-ng es el UI principal del proyecto en v2).

El patron correcto en NiceGUI es `await edge_tts.Communicate(...).save(mp3)` dentro de
una corutina, o usar `asyncio.get_event_loop().run_in_executor` para delegar a un thread.

La llamada es ademas dentro de un `for` sobre curvas: incluso en contexto sin loop activo,
crear y destruir un event-loop N veces es ineficiente; un unico `asyncio.run` que procese
todas las curvas seria la refactorizacion correcta.

**Impacto:** crash garantizado al llamar pace notes de voz desde NiceGUI.
**Correccion:** convertir `build_voice_pack` en corutina (`async def`) y usar `await`; o
generar todas las notas en una unica coroutine via `asyncio.gather`.

---

### H-03 [MAYOR] hud_preview.py:20 — "ffmpeg" hardcodeado; sin shutil.which; CalledProcessError opaco

**Archivo:** `fantasma/viz/hud_preview.py` lineas 19-23

```python
subprocess.run(
    ["ffmpeg", "-y", "-i", overlay_path, "-vframes", "1", "-q:v", "2", tmp_path],
    capture_output=True,
    check=True,
)
```

Tres problemas en un bloque:

1. **Cadena "ffmpeg" sin localizacion.** `compose.py` y `sync.py` usan `shutil.which("ffmpeg")`
   y lanzan `RuntimeError` con instrucciones de instalacion si no se encuentra. Aqui, si
   ffmpeg no esta en PATH, el usuario recibe `FileNotFoundError: [WinError 2] El sistema no
   puede encontrar el archivo especificado` — confuso, sin diagnostico.

2. **CalledProcessError opaco.** `capture_output=True` captura stderr en `e.stderr`, pero
   el codigo no relanza con ese contexto; la excepcion llega al caller de `compose_preview_frame`
   sin saber QUE fallo en ffmpeg.

3. **Windows: ffmpeg no en PATH es el caso mas comun** para usuarios que instalaron ffmpeg
   manualmente en una ruta personalizada y la configuraron en un bundle, no en PATH global.

**Impacto:** UX confusa en la UI de preview; el usuario ve un traceback de Python en lugar
de "instala ffmpeg con winget install Gyan.FFmpeg".
**Correccion:** usar `shutil.which("ffmpeg")` y lanzar RuntimeError si no existe; rodear
`subprocess.run` con try/except CalledProcessError y relanzar con `e.stderr.decode()`.

---

### H-04 [MAYOR] overlay.py:806 — frames_dir no se limpia si el encoding ffmpeg falla

**Archivo:** `fantasma/viz/overlay.py` lineas 803-806

```python
_run_ffmpeg(cmd, n_frames, progress)
shutil.rmtree(frames_dir, ignore_errors=True)
return out
```

Si `_run_ffmpeg` lanza una excepcion (fallo de encoding), `shutil.rmtree` nunca se
ejecuta y `frames_dir` queda en disco con todos los frames PNG. Para una vuelta de 2 min
a 60 fps son ~7 200 frames de ~500 KB cada uno — aprox. 3,6 GB de archivos huerfanos
en `outdir/frames/`.

El mismo problema ocurre si el render de frames falla a mitad: `os.makedirs(frames_dir)`
ya creo el directorio pero los arrays parcialmente renderizados quedan.

**Impacto:** agotamiento silencioso de disco despues de fallos de encoding.
**Correccion:** envolver `_run_ffmpeg` en try/finally o usar un context manager que llame
`shutil.rmtree(frames_dir, ignore_errors=True)` en el bloque finally.

---

### H-05 [MAYOR] compose.py:340 — rama sin progress descarta stderr de ffmpeg

**Archivo:** `fantasma/viz/compose.py` linea 340

```python
subprocess.run(cmd, check=True)
```

Cuando `progress=None`, ffmpeg corre con `subprocess.run(cmd, check=True)` sin redirigir
stderr. En un proceso de GUI (NiceGUI, Streamlit), el stderr del subprocess se pierde en
el void y el caller solo recibe `CalledProcessError(returncode, cmd)`. El usuario ve el
codigo de error pero no el mensaje de ffmpeg.

La rama `progress is not None` (lineas 317-338) resuelve esto correctamente con
`TemporaryFile` para stderr. Ambas ramas deberian dar el mismo nivel de diagnostico.

**Impacto:** usuarios CLI/GUI sin `progress` callback no pueden diagnosticar errores de
ffmpeg; el fallo se reporta como "codigo N" sin contexto.
**Correccion:** redirigir stderr a `subprocess.PIPE` (o a TemporaryFile) y incluirlo en
la excepcion si returncode != 0, igual que la rama con progress.

---

### H-06 [MAYOR] charts.py:53 — TypeError al desempaquetar si corner no tiene segment_m ni range_m

**Archivo:** `fantasma/viz/charts.py` linea 53

```python
lo, hi = corner.get("segment_m") or corner.get("range_m")
```

Si ambas claves son `None` o estan ausentes, `None or None` evalua a `None` y Python
lanza `TypeError: cannot unpack non-iterable NoneType object`. Esto crashea `plot_corner`
sin un mensaje claro.

Contraste: en `overlay.py` linea 712, el mismo patron tiene fallback:
```python
return c.get("segment_m") or c.get("range_m") or [0.0, 0.0]
```

El mismo error potencial existe en `plot_brake_zones` (linea 370), que delega a
`_milestone(corner, ...)` pero asume que `c["milestones"]["apex"]["d"]` existe (linea 380).

**Impacto:** crash al generar graficas para tracks con datos de esquinas incompletos.
**Correccion:** agregar fallback `or [0.0, 0.0]` igual que overlay.py; agregar guard
`if lo == hi == 0.0: return None`.

---

### H-07 [MAYOR] charts.py — zero cobertura de tests (6 funciones publicas, >350 lineas)

**Modulo:** `fantasma/viz/charts.py`
**Tests existentes:** ninguno en `tests/viz/`

Las siguientes funciones no tienen ningun test automatizado:
- `plot_corner` (lógica de ventana, seleccion de paneles, manejo de milestones)
- `plot_delta_map` (anotaciones de perdida de tiempo)
- `plot_time_loss_bar` (colores condicionales por signo)
- `plot_gg_diagram` (filtros de longitud de vectores ref/drv)
- `plot_full_lap` (canal delta_t hardcodeado, gestion de canales opcionales)
- `plot_brake_zones` (filtros de curvas, delegacion a `_milestone`)
- `render_charts` (orquestador)

Cualquier regresion en logica de graficas (p.ej. el KeyError de H-06) pasaria a
produccion sin ser detectada.

**Correccion:** tests Tier-3 (helpers puros) para `_style`, seleccion de paneles,
manejo de trace vacio, corner sin segmento; tests Tier-4 (con matplotlib Agg) para
validar que las funciones retornan una ruta valida y no crashean con datos tipicos.

---

### H-08 [MAYOR] report.py — zero cobertura de tests (render_markdown + write_outputs)

**Modulo:** `fantasma/viz/report.py`
**Tests existentes:** ninguno en `tests/viz/`

`render_markdown` construye una tabla Markdown accediendo a claves como `r["apex_d"]`,
`r["ref_vmin"]`, `r["drv_vmin"]`, `r["d_vmin"]`, `r["time_lost"]` directamente (sin
`.get()`). Si alguna fila de `corner_rows` omite estas claves (datos de importadores
parciales), el resultado es un `KeyError` no manejado.

`write_outputs` usa `csv.DictWriter(f, fieldnames=list(trace[0].keys()))` — si `trace`
es una lista vacia, `trace[0]` lanza `IndexError`. La guarda `if trace:` (linea 15) ya
existe pero el caso `trace=[]` no esta cubierto por ningun test.

**Impacto:** fallos silenciosos al generar el reporte de debrief.
**Correccion:** tests Tier-3 con datos tipicos y con listas vacias; usar `.get()` con
defaults en las claves criticas de `render_markdown`.

---

### H-09 [MENOR] charts.py:111 — KeyError si corner.milestones.apex.d esta ausente

**Archivo:** `fantasma/viz/charts.py` linea 111

```python
apex_d = corner["milestones"]["apex"]["d"]
```

Sin guard; si el milestone `apex` existe pero no tiene clave `d` (p.ej. datos de tracks
con milestones parciales), lanza `KeyError: 'd'`. La funcion usa `.get()` en todas
partes menos aqui.

**Correccion:** `apex_d = (corner.get("milestones") or {}).get("apex", {}).get("d", 0.0)`
con guard `if not apex_d: return path` antes del bucle de anotacion.

---

### H-10 [MENOR] hud_preview.py:24 — PIL mantiene handle de archivo abierto en Windows

**Archivo:** `fantasma/viz/hud_preview.py` lineas 24-28

```python
hud = Image.open(tmp_path).convert("RGBA")
# ...
finally:
    try:
        os.unlink(tmp_path)
    except Exception:
        pass
```

En Windows, Pillow mantiene el archivo abierto hasta que el objeto Image es recolectado
por GC. `os.unlink(tmp_path)` dentro del `finally` falla silenciosamente
(`PermissionError` capturado por `except Exception: pass`) y el archivo .png temporal
queda en `%TEMP%`. Con llamadas frecuentes a `compose_preview_frame` (cada cambio de
posicion/escala en la UI), el directorio temporal se llena.

**Correccion:** cerrar el handle antes de unlink:
```python
hud_raw = Image.open(tmp_path)
hud = hud_raw.convert("RGBA")
hud_raw.close()
```
O usar `hud = Image.open(tmp_path).copy(); hud.info = {}` para forzar el desenganche.

---

### H-11 [MENOR] pacenotes.py:305 — mismatch de sample_rate en WAV ignorado sin aviso

**Archivo:** `fantasma/viz/pacenotes.py` lineas 305-308

```python
if rate != sample_rate:
    continue
```

Si un archivo WAV del pack tiene sample_rate distinto al esperado (p.ej. pack generado
con `sample_rate=44100` pero reproducido con el default 24000), la entrada se salta en
silencio. El usuario no escucha ningun cue para esa curva y no recibe ningun aviso.

**Correccion:** loggear un warning: `print("aviso: %s ignorado (rate %d != %d)" % (filename, rate, sample_rate), file=sys.stderr)`.

---

### H-12 [MENOR] sync.py:29 — numpy importado incondicionalmente a nivel de modulo

**Archivo:** `fantasma/viz/sync.py` linea 29

```python
import numpy as np
```

`numpy` es un extra opcional (`[sync]`), pero se importa al nivel del modulo sin un
bloque `try/except ImportError`. Cualquier `from fantasma.viz import sync` sin numpy
instalado lanza `ModuleNotFoundError: No module named 'numpy'` sin mensaje de orientacion
al usuario. Contraste: scipy se importa lazily dentro de `_audio_energy` y `_rank_candidates`
con mensajes de error utiles.

La guarda de scipy en `sync_candidates` (lineas 229-231) advierte correctamente al usuario:
```python
try:
    import scipy
except ImportError:
    raise ImportError("scipy es necesario para auto-sync: ...")
```
numpy deberia recibir el mismo tratamiento.

**Correccion:** envolver `import numpy as np` en un try/except ImportError en la funcion
de entrada, o agregar una guarda al inicio del modulo.

---

## Cobertura de tests — mapa de huecos

| Modulo | Tests existentes | Funciones sin cobertura |
|---|---|---|
| charts.py | ninguno | todas (7 funciones pub.) |
| hud_preview.py | ninguno | compose_preview_frame |
| report.py | ninguno | render_markdown, write_outputs |
| compose.py | test_compose.py, test_compose_encoder.py | _video_fps, _total_frames, _has_audio |
| sync.py | test_sync.py | _audio_energy (requiere video real) |
| pacenotes.py | test_pacenotes.py | build_voice_pack (requiere edge-tts) |
| overlay.py | test_overlay.py | render_overlay (requiere ffmpeg+mpl) |

---

## Resumen por severidad

| Severidad | Conteo | Hallazgos |
|---|---|---|
| CRITICO | 2 | H-01, H-02 |
| MAYOR | 6 | H-03 a H-08 |
| MENOR | 4 | H-09 a H-12 |

**Total: 12 hallazgos**

---

## Top 3 mas graves (una linea cada uno)

1. **H-01** `overlay.py:627` — stderr=DEVNULL en _run_ffmpeg: encoding VP9/ProRes falla en
   silencio tras horas de render, sin ningun mensaje diagnostico para el usuario.

2. **H-02** `pacenotes.py:227` — `asyncio.run()` dentro del event-loop de NiceGUI crashea
   con RuntimeError, haciendo inaccesible la generacion de voice pace notes desde la UI.

3. **H-03** `hud_preview.py:20` — "ffmpeg" hardcodeado sin shutil.which: en Windows, si
   ffmpeg no esta en PATH el usuario recibe FileNotFoundError en lugar de instrucciones claras.
