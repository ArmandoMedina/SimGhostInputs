# Guía de usuario

Flujo completo: de una tanda en el simulador a un debrief con video.

## 1. Captura tu telemetría

Fantasma no captura datos en vivo; consume archivos. La ruta probada:

1. Instala [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) y déjalo corriendo mientras conduces (soporta AMS2 por shared memory y GT7 por UDP). Genera archivos `.ld` de MoTeC.
2. Abre el `.ld` en [MoTeC i2](https://www.motec.com.au/i2/i2downloads/) (gratuito) y exporta como **CSV** (`Export Data...`), con todas las vueltas del outing. También puedes guardarlo como `.xlsx`.
3. Cualquier otro logger que genere `.ld` o CSV sirve por la misma vía.

¿Tu telemetría es un CSV de otro origen (SimHub, apps de AC)? Usa `--map` para indicar las columnas:

```
fantasma compare --reference ref.csv --driver mi.csv --map "LapDist=dist" --map "SessTime=time" --map "Speed=speed"
```

Canales mínimos: `time` y `dist`. Recomendados: `speed`, `throttle`, `brake`, `steering`, `gear`. Opcionales: `glat`, `glong`, `rpm`, `alt`.

## 2. Consigue una referencia

Una vuelta más rápida que la tuya, **del mismo circuito y trazado** (idealmente el mismo coche). Puede ser:
- tu propia mejor vuelta histórica (compararte contra ti mismo es el uso más honesto),
- la vuelta de un compañero de equipo o liga que te la comparta,
- cualquier telemetría que tengas derecho a usar. Fantasma no distribuye referencias.

## 3. Explora el archivo

```
fantasma laps "mi_outing.csv"
```

Lista las vueltas con duración y longitud, y marca la más rápida (la que se usa por defecto). Para usar otra: `--lap N`.

## 4. Compara

```
fantasma compare --reference ref.csv --driver mi_outing.csv -o salida/
```

Lee `salida/report.md`. La columna **Tiempo perdido** es la verdad: cuánto delta acumulas entre la entrada y la salida de cada curva. **Δv** te dice si el problema es velocidad de paso; **Frenada Δm** si es el punto de frenada (positivo = frenas después que la referencia, negativo = antes).

Interpretación honesta:
- Δ de frenada menores de ~10m son ruido; mayores de ~100m suelen ser un artefacto del detector (frenadas distintas emparejadas), no un error tuyo de 100m.
- Una V-Min MÁS ALTA que la referencia con tiempo perdido es el clásico "rápido adentro, lento afuera": estás sacrificando la salida.

## 5. Nombres de curvas (track pack)

```
fantasma detect ref.csv -o salida/
```

Genera `corners_detected.json`. Edítalo: añade `"name": "Curva del puente"` a cada curva (los IDs son C01, C02... en orden de pista). Pásalo con `--corners` en todas tus comparaciones. Comparte el JSON con tu liga: los nombres y metros de un circuito son datos de la comunidad.

Ahí mismo puedes ajustar `"tolerances"` por curva: `vmin_kmh` y `brake_start_m` controlan cuándo el reporte marca avisos.

## 6. Video con HUD transparente

```
fantasma overlay --reference ref.csv --driver mi_outing.csv --corners salida/corners_detected.json -o salida/
```

Produce `overlay.mov` (ProRes 4444 con canal alfa) de la duración exacta de tu vuelta. En tu editor (Premiere, DaVinci, CapCut):

1. Pista 1: tu grabación de la vuelta (pantalla, replay o visor VR).
2. Pista 2: `overlay.mov`.
3. Alinea el **segundo 0 del overlay** con el frame donde cruzas la línea de meta.

Opciones útiles: `--format webm` (archivo mucho más pequeño, verifica que tu editor soporte alfa en VP9), `--start/--end` para renderizar solo un tramo (p. ej. una curva problemática), `--fps 60` si tu grabación es a 60.

Requiere [ffmpeg](https://ffmpeg.org/) en el PATH (en Windows: `winget install Gyan.FFmpeg`). Sin ffmpeg deja los frames PNG.

## Preguntas frecuentes

**¿Las vueltas tienen que medir exactamente lo mismo?** Diferencias de longitud <0.5% (línea de pilotaje, versión del trazado) son normales y el error de alineación resultante es de pocos metros. Trazados distintos (chicane vs sin chicane) no son comparables.

**¿Por qué mi delta total no coincide exacto con la suma por curvas?** Las curvas no cubren el 100% de la vuelta (las rectas puras quedan fuera) y los segmentos se redondean. La traza continua (`delta.csv`) es la referencia exacta.

**¿Funciona con vueltas mojadas vs secas, o coches distintos?** Funciona, pero el debrief mezclará diferencias de condiciones con errores de pilotaje. Compara como-con-como cuando puedas.
