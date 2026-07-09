# Antes/después — normalización de ventanas fijas en `throttle_on`/`full_throttle`

Rama `fix/corners-window-sample-rate`. Cambio en `fantasma/core/corners.py`
(`extract_milestones`): la ventana de sostenimiento del pedal de gas
(`throttle_on_window`) pasó de un conteo de muestras fijo (`15`) a un tiempo
en segundos (`throttle_on_window_s=0.3`) convertido a muestras vía el `dt`
real de la vuelta (`max(3, int(round(throttle_on_window_s / dt)))`, mismo
idioma que ya usa `detect_corners` para `vmin_window_s`/`kink`). `full_throttle`
tenía su **propio** hardcode independiente de `15` (`post[j : j + 15]`) que ni
siquiera reusaba el parámetro `throttle_on_window` — se corrigió también, es
el mismo bug de fondo (ROADMAP, sección "Deuda técnica", entrada
`throttle_on_window`/`full_throttle`).

## Archivo real usado

`GO BMW M4 GT3 BARCELONA NC E Q01 MOTEC.csv` (`C:\Users\jose_\Downloads\Pruebas finales`),
export MoTeC i2 de AMS2 vía `sim-to-motec`. Header confirma:

```
"Sample Rate","50.000","Hz"
```

Es decir, dt real = 0.020s exactos — el caso de calibración histórica
(15 muestras ⇒ 0.3s a 50Hz) que el fix debe reproducir bit a bit.

## Procedimiento

```powershell
# ANTES (throttle_on_window=15 fijo + full_throttle hardcode de 15)
python -m fantasma.cli detect "GO BMW M4 GT3 BARCELONA NC E Q01 MOTEC.csv" -o before

# DESPUES (con el fix: ventana en segundos, calibrada por dt real)
python -m fantasma.cli detect "GO BMW M4 GT3 BARCELONA NC E Q01 MOTEC.csv" -o after

diff before/corners_detected.json after/corners_detected.json
```

## Resultado

```
Vuelta: 98.24s, 4591m - 11 curvas detectadas
  C01   708m  right v=111  vmin
  ...
  C11  4149m  right v=168  vmin
  28 cambios de marcha detectados
```

Idéntico en ambas corridas. `diff before/corners_detected.json after/corners_detected.json`
no reporta ninguna diferencia — **el `corners_detected.json` es byte a byte
idéntico** antes y después del cambio, sobre telemetría real a 50Hz exactos.

## Cobertura sintética adicional (invariante + calibración a otro Hz)

Además de este antes/después, `tests/core/test_corners.py` añade el límite
exacto de la ventana:

- `test_throttle_on_window_matches_historical_15_samples_at_50hz` y
  `test_full_throttle_window_matches_historical_15_samples_at_50hz`: a 50Hz
  (`dt_s=0.02`), 14 muestras sostenidas de gas **no** disparan el hito, 15
  **sí** — reproduce el hardcode histórico exacto para ambos hitos.
- `test_throttle_on_window_calibrates_to_sample_rate_at_20hz`: a 20Hz
  (`dt_s=0.05`), la misma ventana de 0.3s exige 6 muestras (no 15): 5 no
  alcanzan, 6 sí — antes de este fix, a esta tasa se hubiera exigido 0.75s de
  sostenimiento real en vez de los 0.3s pretendidos.

`tests/conftest.py` (`make_lap`) se extendió con el parámetro `dt_s` para
poder fijar Hz explícito en vueltas sintéticas (antes solo muestreaba por
distancia fija, con Hz variable según la velocidad local) — cubierto por
`tests/test_conftest.py`.
