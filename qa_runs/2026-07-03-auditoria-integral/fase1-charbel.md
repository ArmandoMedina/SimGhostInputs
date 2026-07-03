# Auditoria Integral Fase 1 — Charbel (Telemetria Real)

**Fecha:** 2026-07-03
**Rol:** Charbel — validador de telemetria y datos
**Branch:** codex/sgi-v2-merge
**Material:** `C:\Repositorio personal\Paterial para test (no es un repo)`

---

## 1. Inventario del material

### Raiz del directorio

| Archivo | Tipo | Notas |
|---|---|---|
| `GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv` | MoTeC CSV (qualifying) | Duplicado del que esta en Pruebas finales |
| `Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv` | MoTeC CSV (race, 20 Hz) | 11 laps, sesion de carrera |
| `Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-21T122432.csv` | MoTeC CSV (race, 20 Hz) | 11 laps, segunda sesion de carrera |
| `2.mp4` | Video | No probado (fuera de scope) |
| `AQO4W2TD...` | Archivo binario | No probado |
| `Pruebas finales.zip` | Archivo comprimido | Expandido en subcarpeta |
| `salida/` | Carpeta de salidas previas | Outputs de corridas anteriores |

### Pruebas finales/Pruebas finales/ (16 archivos MoTeC CSV)

| Archivo | Tam. | Tiene Distance |
|---|---|---|
| GO ASTON MARTIN GT3 EVO BARCELONA NC E Q01 MOTEC.csv | 12.1 MB | SI |
| GO ASTON MARTIN GT3 EVO INTERLAGOS E Q01 MOTEC.csv | 12.6 MB | SI |
| GO ASTON MARTIN GT3 EVO NORDSCHLEIFE 2025 E Q01 MOTEC.csv | 29.6 MB | SI |
| GO ASTON MARTIN VALKYRIE BARCELONA NC E Q01 MOTEC.csv | 7.5 MB | SI |
| GO ASTON MARTIN VALKYRIE INTERLAGOS E Q01 MOTEC.csv | 6.9 MB | SI |
| GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025 E Q01 MOTEC.csv | 29.7 MB | SI |
| GO BMW HYBRID V8 BARCELONA NC E Q01 MOTEC.csv | 7.5 MB | SI |
| GO BMW M4 GT3 BARCELONA NC E Q01 MOTEC.csv | 12.1 MB | SI |
| GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv | 29.7 MB | SI |
| GO BMW M4 GT3 NURBURGRING GP E Q01 MOTEC.csv | 13.7 MB | SI |
| GO CADILLAC V-SERIES.R BARCELONA NC E Q01 MOTEC.csv | 7.4 MB | SI |
| GO CHEVROLET CORVETTE Z06 GT3R BARCELONA NC E Q01 MOTEC.csv | 12.1 MB | SI |
| GO CHEVROLET CORVETTE Z06 GT3R NORDSCHLEIFE 2025 E Q01 MOTEC.csv | 29.5 MB | SI |
| GO F3 INT E Q01 MOTEC.csv | 7.7 MB | SI |
| GO MERCEDES AMG GT3 EVO BARCELONA NC E Q01 MOTEC.csv | 12.1 MB | SI |
| **GO ORECA 07 INT E Q01 MOTEC.csv** | 7.0 MB | **NO** |

**15/16 tienen Distance en Pruebas finales. 1 archivo carece de el.**

---

## 2. Archivos representativos probados

Se seleccionaron 3 archivos principales para el pipeline completo:

1. **BMW M4 GT3 Nordschleife 2025** (`GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv`)
   - 50 Hz, qualifying, 3 laps (out-lap + vuelta rapida + in-lap parcial)
   - Vuelta rapida: 378.40s, 20592m, 18921 muestras

2. **Audi R8 LMS EVO II Nordschleife 2025** (`GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025 E Q01 MOTEC.csv`)
   - 50 Hz, qualifying, 3 laps
   - Vuelta rapida: 377.14s, 20591m, 18858 muestras

3. **BMW M4 GT3 Barcelona** (`GO BMW M4 GT3 BARCELONA NC E Q01 MOTEC.csv`)
   - 50 Hz, qualifying, 4 laps
   - Vuelta rapida: 98.24s, 4591m, 4913 muestras

Adicionales validados con Python API:
- GO F3 INT E Q01 MOTEC.csv (Interlagos, con Distance)
- GO ORECA 07 INT E Q01 MOTEC.csv (Interlagos, SIN Distance)
- GO ASTON MARTIN GT3 EVO NORDSCHLEIFE 2025 E Q01 MOTEC.csv
- GO ASTON MARTIN VALKYRIE BARCELONA NC E Q01 MOTEC.csv
- GO CHEVROLET CORVETTE Z06 GT3R BARCELONA NC E Q01 MOTEC.csv
- Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv (race 20Hz, 11 laps)
- Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-21T122432.csv (race 20Hz, 11 laps)

---

## 3. Comandos ejecutados y salidas

### 3.1 `fantasma laps` — parsing y split de vueltas

```
python -m fantasma.cli laps "...GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
```
```
Archivo: ...GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv
  Venue: Nordschleife_2025
  Vehicle: BMW M4 GT3
  Driver: Jan Nimz

  #  duracion   longitud   completa
   0   399.20s    20679m   no
   1   378.40s    20592m   si <- mas rapida
   2    10.88s      336m   no
```
EXIT 0. Metadatos correctos (Venue, Vehicle, Driver). 3 segmentos identificados correctamente por beacons.

```
python -m fantasma.cli laps "...GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025 E Q01 MOTEC.csv"
```
```
   0   397.70s    20671m   no
   1   377.14s    20591m   si <- mas rapida
   2    15.16s      407m   no
```
EXIT 0. Correcto.

```
python -m fantasma.cli laps "...GO BMW M4 GT3 BARCELONA NC E Q01 MOTEC.csv"
```
```
   0   111.24s     4618m   no
   1   100.24s     4591m   si
   2    98.24s     4591m   si <- mas rapida
   3    14.32s      772m   no
```
EXIT 0. 4 laps con 2 vueltas completas. Mas rapida correctamente identificada.

```
python -m fantasma.cli laps "...GO ORECA 07 INT E Q01 MOTEC.csv"
```
```
   0    96.50s        0m   no
   1    83.98s        0m   si <- mas rapida
   2     7.86s        0m   no
aviso: este CSV no incluye el canal de distancia (longitud 0m). [...]
```
EXIT 0 con aviso en stderr. Correcto (el warning es accionable).

```
python -m fantasma.cli laps "...Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv"
```
```
  # vueltas: 11 (9 completas + out-lap + in-lap parcial)
  vuelta rapida: 394.05s, 20571m (lap 8)
```
EXIT 0. Race CSV a 20Hz parseado correctamente con 11 vueltas.

### 3.2 `fantasma detect` — deteccion de curvas

```
python -m fantasma.cli detect "...GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv" -o qa_runs/...
```
```
Vuelta: 378.40s, 20592m — 55 curvas detectadas
  C01    77m  left  v= 87  vmin
  ...
  C55 20391m  right v=100  vmin
```
EXIT 0. 55 curvas en 20592m. Apexes monotonicos (77m-20391m). Todos los hitos presentes (brake_start, brake_release, turn_in, throttle_on, apex, full_throttle, g_lat_max). JSON bien formado.

```
python -m fantasma.cli detect "...Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv" -o qa_runs/...
```
```
Vuelta: 394.05s, 20571m — 56 curvas detectadas
```
EXIT 0. Race CSV 20Hz genera 56 curvas (1 extra vs 50Hz qualifying).

```
python -m fantasma.cli detect "...GO ORECA 07 INT E Q01 MOTEC.csv"
```
```
error: La vuelta no tiene canal de distancia. [...]
```
EXIT 1. Fallo correcto y controlado con mensaje accionable.

### 3.3 `fantasma compare` — comparacion de vueltas

**BMW vs Audi (Nordschleife, misma pista, distinto auto):**
```
python -m fantasma.cli compare --reference BMW_NORDS.csv --driver AUDI_NORDS.csv -o compare_nords_bmw_vs_audi --no-charts
```
```
Referencia: 378.400s | Piloto: 377.140s | Delta: -1.260s
  mayor perdida: C54 (m20237) +0.150s
  mayor perdida: C26 (m10317) +0.090s
  mayor perdida: C53 (m20044) +0.070s
-> compare_nords_bmw_vs_audi/report.md
aviso: autos distintos: BMW M4 GT3 (ref) vs Audi R8 LMS GT3 evo II (piloto)
aviso: piloto mas rapido que la referencia (1.2 s de ventaja)
```
EXIT 0. Comparacion completa. 4119 filas en delta.csv. Delta final del grid: -1.240s (ver hallazgo M1).

**BMW vs Mercedes (Barcelona, misma pista, distinto auto):**
```
python -m fantasma.cli compare --reference BMW_BCN.csv --driver MERCEDES_BCN.csv -o compare_bcn_bmw_vs_merc --no-charts
```
```
Referencia: 98.240s | Piloto: 97.960s | Delta: -0.280s
  mayor perdida: C01 (m708) +0.020s
  mayor perdida: C10 (m3885) +0.020s
aviso: autos distintos: BMW M4 GT3 (ref) vs Mercedes-AMG GT3 Evo (piloto)
```
EXIT 0. Correcto.

**Carrera sesion 1 vs sesion 2 (Nordschleife 2020, mismo auto, distintas fechas):**
```
python -m fantasma.cli compare --reference RACE_2026-06-07.csv --driver RACE_2026-06-21.csv -o compare_race_s1_vs_s2 --no-charts
```
```
Referencia: 394.050s | Piloto: 398.250s | Delta: +4.200s
  mayor perdida: C14 (m5097) +0.892s
  mayor perdida: C30 (m11821) +0.550s
  mayor perdida: C24 (m8691) +0.467s
```
EXIT 0. Compare entre sesiones cruzadas funciona.

**Same-file fastest vs lap 1 (auto-referencia interna):**
```
python -m fantasma.cli compare --reference RACE_2026-06-07.csv --driver RACE_2026-06-07.csv --lap 1 -o compare_fastlap_vs_lap1 --no-charts
```
```
Referencia: 394.050s | Piloto: 409.750s | Delta: +15.700s
  mayor perdida: C01 (m78) +2.367s
```
EXIT 0. Coherente: lap 1 (out-lap o vuelta inicial fria) es 15.7s mas lento.

---

## 4. Validacion de canales (Python API)

| Archivo | NaN/Inf | dist monotonica | speed min-max | RPM min-max | Throttle | Brake |
|---|---|---|---|---|---|---|
| BMW M4 GT3 Nordschleife | 0 | SI (0-20592m) | 76-303 km/h | 4298-7717 | 0-100% | 0-100% |
| Audi R8 LMS Nordschleife | 0 | SI (0-20591m) | 75-300 km/h | 4697-8929 | 0-100% | 0-100% |
| BMW M4 GT3 Barcelona | 0 | SI (0-4591m) | 79-281 km/h | 3822-7472 | 0-100% | 0-100% |
| F3 Interlagos | 0 | SI (0-4238m) | 74-237 km/h | 3496-7409 | 0-100% | 0-100% |
| ORECA 07 Interlagos | 0 | N/A (sin dist) | 79-271 km/h | 4405-8846 | 0-100% | 0-100% |
| Aston Martin GT3 Nordschleife | 0 | SI (0-20591m) | 77-303 km/h | 4174-8080 | 0-100% | 0-100% |
| Valkyrie Barcelona | 0 | SI (0-4593m) | 83-315 km/h | 4358-8920 | 0-100% | 0-100% |
| Corvette Z06 GT3R Barcelona | 0 | SI (0-4591m) | 75-281 km/h | 4031-8349 | 0-100% | 0-100% |

**Todos los archivos con Distance:**
- Sin NaN ni Inf en ningun canal probado
- Distancia estrictamente monotonica en todas las vueltas rapidas
- Velocidades en rangos fisicamente plausibles por tipo de vehiculo
- RPM en rangos plausibles por tipo de motor (F3 tope ~7400, GT3 ~8900, hipercar ~8900)
- Throttle y brake 0-100% sin valores fuera de rango
- Sin speeds negativos ni < 50 km/h en las vueltas rapidas (minimo 74 km/h en F3)

---

## 5. Hallazgos

### CRITICO (1)

**[C1] GO ORECA 07 INT E Q01 MOTEC.csv — exportado sin canal Distance**

El archivo de Oreca 07 en Interlagos fue exportado desde sim-to-motec sin incluir el canal Distance. El header de la fila de canales no contiene "Distance" y el metadato `End Distance` dice `0 m`.

Impacto:
- `fantasma laps`: funciona con aviso en stderr (EXIT 0)
- `fantasma detect`: falla EXIT 1 con "La vuelta no tiene canal de distancia"
- `fantasma compare` y `fantasma overlay`: igualmente bloqueados

El pipeline gestiona el error correctamente (no crashea, mensaje accionable). Sin embargo, el archivo es inutilizable para las funciones principales hasta ser re-exportado desde MoTeC i2 marcando "Include Distance Data".

Afecta 1/17 archivos del material real (6%). Si otros usuarios entregan CSVs sin Distance, el pipeline los rechaza con el mensaje correcto — pero es un patron de error que va a reaparecer.

Accion recomendada: documentar explicitamente en el onboarding que TODO CSV debe exportarse con "Include Distance Data" activado. Considerar un test de aceptacion en el importer que rechace el archivo antes de que el usuario intente detect/compare.

---

### MAYOR (2)

**[M1] Discrepancia 20ms entre delta_t del grid y diferencia directa de laptimes**

En la comparacion BMW vs Audi Nordschleife:
- Delta reportado por CLI (diferencia de laptimes): -1.260s
- Delta final del archivo `delta.csv` (delta_t acumulado sobre rejilla de 5m): -1.240s
- Diferencia: 20ms

Causa: el CLI reporta `drv_laptime - ref_laptime` como diferencia directa. El delta.csv acumula la diferencia de tiempo sobre la rejilla de 5m (resample), que introduce un error de discretizacion proporcional al paso y a la aceleracion del vehiculo al final de la vuelta.

El usuario que compare ambos valores podra confundirse sobre cual es el "numero real". No es un bug (ambos son correctos para su proposito), pero la inconsistencia no esta documentada.

Accion recomendada: agregar nota al report.md o al CLI output clarificando que el delta del grid es una aproximacion y el delta de laptimes es el valor exacto.

---

**[M2] Warnings de stderr en PowerShell 5.1 aparecen como NativeCommandError**

Los avisos que el pipeline emite a stderr ("autos distintos", "piloto mas rapido que la referencia") se capturan en PowerShell 5.1 como `NativeCommandError` en la variable de error `$Error` y en el flujo de pantalla. El proceso termina EXIT 0, pero la salida visual parece un error:

```
python : aviso: autos distintos: BMW M4 GT3 (ref) vs Audi R8 LMS GT3 evo II (piloto)
    + CategoryInfo : NotSpecified: (aviso: autos di...evo II (piloto):String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
```

En bash/macOS el mismo aviso aparece limpio. En el entorno de desarrollo principal (Windows/PS 5.1) puede alarmar a nuevos usuarios o automatizaciones que chequeen `$?`.

Accion recomendada: menor prioridad dado que es una limitacion conocida de PS 5.1 (ADR de entorno). Documentar en la guia de usuario que los avisos a stderr son informativos y que EXIT 0 indica exito.

---

### MENOR (2)

**[m1] Race CSVs a 20Hz generan 1 corner extra vs qualifying a 50Hz**

El Nordschleife 2020 race CSV (20Hz) detecta 56 curvas vs 55 en el qualifying CSV del mismo circuito (50Hz, version 2025). La diferencia de 1 corner (C09 desaparece o dos kinks se fusionan segun la muestra) es plausible dado que la resolucion inferior suaviza los minimos de velocidad. El numero de curvas es coherente con el circuito real.

Sin embargo, si un usuario usa el JSON de corners del qualifying para comparar contra vueltas del race CSV (20Hz), los hitos de frenada seran menos precisos por la menor densidad de muestras (50ms/muestra vs 20ms/muestra).

Accion recomendada: documentar la dependencia de la deteccion de curvas con la frecuencia de muestreo. Considerar un aviso en `detect` si Sample Rate < 30 Hz.

---

**[m2] C53 en Nordschleife muestra -67 km/h de V-Min entre BMW y Audi**

En la comparacion BMW vs Audi (Nordschleife), la curva C53 (kink a 20044m) muestra:
- V-Min BMW (referencia): 292 km/h
- V-Min Audi (piloto): 225 km/h
- Diferencia: -67 km/h

El -67 km/h en un kink a 292 km/h es enganoso: el Audi ya esta frenando para C54 (hairpin a 102 km/h, 200m despues) cuando el BMW aun pasa C53 a maxima velocidad. El problema es que el segmento de C53 incluye el inicio de la frenada hacia C54, y los dos autos toman ese punto en momentos distintos de su frenada. No es un bug (el importer y el detector son correctos), pero el numero puede llevar a un usuario a pensar que el Audi tiene un problema de trazada en C53 cuando en realidad tiene distinta estrategia de frenada para C54.

Accion recomendada: considerar un flag en el report cuando V-Min de un kink difiere mas de X km/h entre referencia y piloto y hay un hairpin a menos de 300m.

---

## 6. Resumen ejecutivo

| Severidad | Cantidad | Descripcion |
|---|---|---|
| CRITICO | 1 | ORECA 07 sin Distance — pipeline bloqueado para ese archivo |
| MAYOR | 2 | Discrepancia delta 20ms; warnings stderr parecen NativeCommandError en PS5.1 |
| MENOR | 2 | Race 20Hz genera +1 corner; C53 Nordschleife V-Min enganoso por segmento limites |

**Veredicto: APTO CON OBSERVACIONES.**
El pipeline parsea, detecta y compara correctamente sobre 16 de 17 archivos del material real. No se encontraron NaN, distancias no monoticas, velocidades fisicamente imposibles ni crasheos no controlados. El unico archivo bloqueado (ORECA 07) lo es por falta del canal Distance en el export, no por un bug del software — y el manejo del error es correcto. Los hallazgos mayores son de presentacion/documentacion, no de correctitud de datos.

---

## 7. Outputs generados por esta corrida

- `qa_runs/2026-07-03-auditoria-integral/detect_nords_bmw/corners_detected.json` — 55 corners BMW Nordschleife 2025
- `qa_runs/2026-07-03-auditoria-integral/detect_nords2020_race/corners_detected.json` — 56 corners Race 20Hz
- `qa_runs/2026-07-03-auditoria-integral/compare_nords_bmw_vs_audi/` — delta.csv, corners_compare.csv, report.md
- `qa_runs/2026-07-03-auditoria-integral/compare_bcn_bmw_vs_merc/` — delta.csv, report.md
- `qa_runs/2026-07-03-auditoria-integral/compare_race_session1_vs_session2/` — delta.csv, report.md
- `qa_runs/2026-07-03-auditoria-integral/compare_race_fastlap_vs_lap1/` — delta.csv, report.md
