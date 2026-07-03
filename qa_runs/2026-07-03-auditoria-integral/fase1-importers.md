# Auditoria Importers — fantasma/importers/

**Rama:** codex/sgi-v2-merge  
**Fecha:** 2026-07-03  
**Auditor:** Claude (Sonnet 4.6)  
**Archivos revisados:**
- `fantasma/importers/__init__.py`
- `fantasma/importers/_util.py`
- `fantasma/importers/motec_csv.py`
- `fantasma/importers/generic_csv.py`
- `tests/importers/test_motec_csv.py`
- `tests/importers/test_generic_csv.py`
- `tests/importers/fixtures/motec_mini.csv`

---

## Veredicto

**AREA NO APTA PARA RELEASE** — un bug critico de corrupcion silenciosa de datos (doble-append) afecta a ambos importers y no tiene test que lo detecte. Seis hallazgos mayores adicionales (crashes sin mensaje claro, inconsistencias de API) mas cuatro menores. Cobertura de tests insuficiente para los caminos de error mas importantes.

---

## Conteo por severidad

| Severidad | Cantidad |
|-----------|----------|
| CRITICO   | 1        |
| MAYOR     | 6        |
| MENOR     | 4        |
| **Total** | **11**   |

---

## Hallazgos

### H-01 [CRITICO] — Doble-append cuando dos columnas del header mapean al mismo canal canonico

**Archivos:** `fantasma/importers/motec_csv.py:95-100, 131-132` | `fantasma/importers/generic_csv.py:68-75, 84-88`

**Descripcion:**

`cols` es una lista de tuplas `(indice_columna, nombre_canonico)`. Si el header contiene dos columnas que MOTEC_MAP (o GUESS / column_map) resuelve al mismo canonico, ambas tuplas entran en `cols`. Ejemplo: `"Ground Speed"` y `"Speed"` mapean ambas a `"speed"`. En el loop de datos de `motec_csv.py`:

```python
# primer loop: vals["speed"] se asigna dos veces (el segundo sobreescribe al primero)
for i, cn in cols:
    vals[cn] = pfloat(row[i]) ...

# segundo loop: lap.channels["speed"].append(...) se ejecuta DOS VECES por fila
for _, cn in cols:
    lap.channels[cn].append(vals[cn])
```

Resultado: el canal `"speed"` acumula 2N muestras mientras `"time"` y `"dist"` acumulan N. El alineamiento entre canales queda roto y los datos son silenciosamente incorrectos. El valor almacenado en el double-append es siempre el de la SEGUNDA columna (el `vals[cn]` del ultimo `i`), descartando la primera sin aviso.

**El mismo bug existe en `generic_csv.py`** cuando `column_map` asigna dos claves diferentes al mismo canonico, o cuando el GUESS auto-detecta dos columnas del header como el mismo canonico (e.g., CSV con headers `["time", "SessionTime", "dist"]` produce doble-append en `"time"`).

**Pares de MOTEC_MAP que podrian coexistir en un export real:**
- `"Ground Speed"` y `"Speed"` → `"speed"`
- `"Throttle Pos"` y `"THROTTLE"` → `"throttle"`
- `"Brake Pos"` y `"BRAKE"` → `"brake"`
- `"Steering Pos"` y `"STEERANGLE"` → `"steering"`

**Impacto:** Corrupcion silenciosa de datos. El importer devuelve un `Lap` aparentemente valido pero con canales desalineados. `len(lap)` = N (basado en `"time"`), pero `lap.col("speed")` tiene 2N elementos. Cualquier pipeline downstream que haga zip de canales o use indices de `"time"` sobre `"speed"` produce resultados erroneos sin exception.

**No existe ningun test que cubra este camino.**

**Correccion sugerida:** Deduplicar `cols` antes del loop de datos o usar un `dict` en lugar de lista. Alternativamente, avisar si dos columnas del input mapean al mismo canonico.

---

### H-02 [MAYOR] — IndexError no manejado cuando una fila de datos esta truncada en la columna dist

**Archivo:** `fantasma/importers/motec_csv.py:127-129`

**Descripcion:**

Despues del loop de parseo de valores, hay un segundo acceso directo a `row[i_dist]`:

```python
if bad or (
    ("dist" in vals)
    and str(row[[i for i, c in cols if c == "dist"][0]]).strip() in ("", "None")
):
    continue
```

El subindice `[i for i, c in cols if c == "dist"][0]` calcula el indice de la columna dist en el CSV. Si la fila tiene menos columnas que ese indice (fila truncada o con columnas sobrantes cortadas), `row[i_dist]` lanza `IndexError` sin capturar. El importer se rompe con un traceback crudo en lugar de un mensaje de error util.

Ironicamente, el loop anterior ya maneja filas cortas graciosamente con `if i < len(row)`, pero la verificacion posterior no aplica la misma guarda.

**Impacto:** Crash con IndexError en archivos con filas de datos truncadas (archivos corruptos o exportaciones incompletas). El mensaje no indica el numero de fila ni la columna.

---

### H-03 [MAYOR] — StopIteration no manejada en archivo CSV vacio

**Archivo:** `fantasma/importers/generic_csv.py:64`

**Descripcion:**

```python
header = next(reader)
```

Si el archivo esta vacio (o contiene solo lineas en blanco que el `csv.reader` omite), `next(reader)` lanza `StopIteration`. En Python 3.7+ esta excepcion se convierte en `RuntimeError` si se propaga desde un generador, pero aqui es una funcion normal, por lo que `StopIteration` sale sin capturar.

El dispatcher en `__init__.py` solo captura `motec_csv.NotMotecFormat`, de modo que una llamada a `importers.load("empty.csv")` con un CSV vacio produce `StopIteration` sin mensaje de contexto.

**Impacto:** Error confuso para el usuario final. Deberia levantarse un `ValueError` con mensaje descriptivo.

---

### H-04 [MAYOR] — Fila de datos truncada produce 0.0 silencioso para time y dist sin marcar la fila como mala

**Archivo:** `fantasma/importers/motec_csv.py:118-122`

**Descripcion:**

```python
vals[cn] = pfloat(row[i]) if i < len(row) and str(row[i]).strip() != "" else 0.0
```

Cuando `i >= len(row)` (fila mas corta que el header), el valor cae directamente a `0.0` SIN pasar por el `except (ValueError, TypeError)` que pone `bad = True`. Por lo tanto:

- `vals["time"] = 0.0` para una fila corta donde la columna time esta fuera de rango.
- `vals["dist"] = 0.0` idem.
- `bad` permanece `False`.
- La segunda verificacion `(... str(row[i_dist]) ...)` puede fallar con `IndexError` (H-02) o, si dist esta en rango pero otras columnas no, la fila pasa con zeros silenciosos.

**Impacto:** En el caso donde dist esta en rango pero time no, se introduce una muestra con `time=0.0` en medio de la serie. Esto rompe la monotonidad temporal y puede causar errores en `split_laps` o `resample`.

---

### H-05 [MAYOR] — source_file inconsistente entre importers (ruta completa vs. basename)

**Archivos:** `fantasma/importers/generic_csv.py:61` vs `fantasma/importers/motec_csv.py:145`

**Descripcion:**

```python
# motec_csv.py (linea 145)
lap.meta["source_file"] = os.path.basename(path)

# generic_csv.py (linea 61)
lap = Lap(meta={"source_file": path, "beacons": []})
```

`motec_csv` guarda solo el nombre de archivo (ej. `"mi_vuelta.csv"`), mientras que `generic_csv` guarda la ruta completa (ej. `"C:/Users/piloto/datos/mi_vuelta.csv"`). Cualquier codigo que use `meta["source_file"]` para display, comparacion de archivos, o agrupacion de sesiones recibe formatos incompatibles dependiendo de que importer fue usado, sin ninguna advertencia.

**Impacto:** Bug silencioso en capas superiores. No hay test que verifique el formato de `source_file` para `generic_csv`.

---

### H-06 [MAYOR] — Beacon markers con un token invalido descarta silenciosamente TODOS los beacons validos

**Archivo:** `fantasma/importers/motec_csv.py:141-144`

**Descripcion:**

```python
try:
    lap.meta["beacons"] = [float(x) for x in bm.split()]
except ValueError:
    lap.meta["beacons"] = []
```

El list comprehension evalua todos los tokens juntos. Si `bm = "399.220 INVALID 777.622"`, el `float("INVALID")` lanza `ValueError` y el `except` captura el error entero, descartando los dos valores validos. El resultado es `beacons = []`.

Como `normalize.split_laps` usa beacons como primera estrategia de corte de vueltas (prioridad sobre lap_number y reinicio de distancia), descartar beacons silenciosamente puede causar que las vueltas NO se corten correctamente, con la segunda estrategia (lap_number) aplicandose en su lugar o que todo el outing se devuelva como una sola vuelta.

**Impacto:** Corrupcion logica silenciosa de la separacion de vueltas cuando el string de beacons tiene cualquier token malformado.

---

### H-07 [MAYOR] — wb.active puede ser None en un XLSX vacio, lanzando AttributeError

**Archivo:** `fantasma/importers/motec_csv.py:73-75`

**Descripcion:**

```python
def _rows_from_xlsx(path):
    ...
    wb = openpyxl.load_workbook(path, read_only=True)
    for row in wb.active.iter_rows(values_only=True):
```

`openpyxl.Workbook.active` retorna `None` si el workbook no tiene ninguna hoja definida (workbook vacio o creado programaticamente sin hojas). `None.iter_rows(...)` lanza `AttributeError: 'NoneType' object has no attribute 'iter_rows'` que no esta capturado ni en `_rows_from_xlsx` ni en `load()` ni en `__init__.load()`.

**Impacto:** Crash crudo con AttributeError al intentar cargar un XLSX vacio o estructuralmente invalido. Deberia lanzar `NotMotecFormat` con mensaje descriptivo.

---

### H-08 [MENOR] — pfloat no maneja separador de miles europeo (1.000,5)

**Archivo:** `fantasma/importers/_util.py:27-28`

**Descripcion:**

```python
if "," in s and "." not in s:
    s = s.replace(",", ".")
```

Esta logica solo sustituye la coma decimal cuando NO hay punto en el string. Para el formato europeo con separador de miles y coma decimal (e.g., `"1.000,5"`), hay tanto `.` como `,`, por lo que no se aplica ninguna transformacion y `float("1.000,5")` lanza `ValueError`. Este error queda silenciado en el catch del loop de datos (asigna 0.0). Algunos loggers europeos (RaceStudio3, logger ATLAS de MoTeC en configuracion ES) pueden exportar este formato.

**Impacto:** Valores silenciosamente convertidos a 0.0 para numeros con separador de miles europeo.

---

### H-09 [MENOR] — detect_delimiter abre el archivo dos veces en generic_csv.load

**Archivo:** `fantasma/importers/generic_csv.py:62-63`

**Descripcion:**

```python
with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
    reader = csv.reader(f, delimiter=detect_delimiter(path))
```

`detect_delimiter(path)` se evalua como argumento de `csv.reader` mientras el handle `f` ya esta abierto. Internamente, `detect_delimiter` abre un segundo handle al mismo archivo, lee la primera linea, y lo cierra. El handle `f` permanece al inicio (no se ve afectado), asi que el comportamiento es correcto. Sin embargo, se realizan dos aperturas de archivo y dos lecturas del primer sector del mismo archivo. En sistemas de archivos en red o discos lentos, esto es un costo innecesario.

**Impacto:** Solo eficiencia. Sin impacto en correctitud.

---

### H-10 [MENOR] — NotMotecFormat no exportada en el modulo publico

**Archivo:** `fantasma/importers/__init__.py`

**Descripcion:**

`__init__.load()` puede re-lanzar `motec_csv.NotMotecFormat` (cuando el archivo es `.xlsx` sin formato MoTeC). Sin embargo, `NotMotecFormat` no esta importada ni exportada en `__init__.py`. Los callers que quieran capturar este caso especifico deben hacer `from fantasma.importers import motec_csv` y capturar `motec_csv.NotMotecFormat`, lo cual no es obvio para quien solo usa la API publica (`importers.load(...)`).

**Impacto:** API inconsistente. Menor, pero puede causar confusion a callers del dispatcher.

---

### H-11 [MENOR] — GUESS no normaliza caracteres especiales, guiones ni parentesis

**Archivo:** `fantasma/importers/generic_csv.py:71`

**Descripcion:**

```python
elif key.lower().replace(" ", "") in GUESS:
```

La normalizacion solo elimina espacios y pasa a minusculas. Headers como `"Speed (km/h)"`, `"G-Force Lat"`, o `"Brake%"` no se normalizan a ninguna entrada de GUESS. El archivo csv con estos headers fallaria el auto-detect y requeriria `column_map` explicito, sin que el mensaje de error indique por que no se detecto el canal.

**Impacto:** Silencioso (el canal no se mapea, no hay aviso). Requiere documentacion o ampliacion de GUESS.

---

## Analisis de cobertura de tests

### tests/importers/test_motec_csv.py (8 tests)

**Cubierto:** mapeo de columnas, columna desconocida ignorada, metadata, archivo invalido, beacon markers, split de vueltas, separador `;`, decimales con coma europea.

**No cubierto:**
- Dos columnas que mapean al mismo canonico (el bug H-01).
- Carga de XLSX (ni con openpyxl presente ni sin el).
- Fila de datos truncada (H-02, H-04).
- Archivo XLSX vacio / wb.active None (H-07).
- Beacon string con token invalido en medio (H-06).
- Encoding Latin-1 / CP1252 con `errors="replace"`.
- Llamada a `__init__.load()` con archivo `.xlsx`.

### tests/importers/test_generic_csv.py (4 tests)

**Cubierto:** auto-deteccion de nombres comunes, column_map explicito, error si falta time/dist, valores malos → 0.0.

**No cubierto:**
- Archivo CSV vacio (H-03: StopIteration).
- Separador `;` en CSV generico.
- column_map con dos claves al mismo canonico (H-01 en generic_csv).
- Formato de `source_file` (H-05).
- Header unico con dos columnas que GUESS resuelve igual.
- Archivo con solo header sin filas de datos.

---

## Resumen de violaciones de principios de diseno

| Principio | Estado |
|-----------|--------|
| Importers = stdlib puro sin dependencias | **CUMPLIDO** — openpyxl importado lazily con degradacion con gracia |
| XLSX usa dependencia extra opcional | **CUMPLIDO** — `ImportError` da mensaje util |
| Fallo claro ante archivo malformado | **INCUMPLIDO** — H-02 (IndexError), H-03 (StopIteration), H-07 (AttributeError) |
| Sin datos silenciosamente malos | **INCUMPLIDO** — H-01 (doble-append), H-04 (0.0 silencioso), H-06 (beacons descartados) |
| API consistente entre importers | **INCUMPLIDO** — H-05 (source_file diferente) |
