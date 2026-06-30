# Guía de usuario

Flujo completo: de una tanda en el simulador a un debrief con video.

## 1. Captura tu telemetría

Fantasma no captura datos en vivo; consume archivos. La ruta probada:

1. Instala [sim-to-motec](https://github.com/GeekyDeaks/sim-to-motec) y déjalo corriendo mientras conduces (soporta AMS2 por shared memory y GT7 por UDP). Genera archivos `.ld` de MoTeC.
2. Abre el `.ld` en [MoTeC i2](https://www.motec.com.au/i2/i2downloads/) (gratuito) y exporta como **CSV** (`Export Data...`), con todas las vueltas del outing. También puedes guardarlo como `.xlsx`. **Marca la casilla «Include Distance Data»**: Fantasma compara por distancia, así que sin ese canal no puede analizar la vuelta (te avisará y no continuará; ver [ADR 0017](decisions/0017-distancia-canal-requerido.md)).
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

### Desde la UI

`fantasma ui` abre un asistente local. En el **Paso 0** eliges qué salida quieres:

- **📊 Solo análisis**: reporte, CSVs y gráficas.
- **🎬 Solo overlay**: HUD transparente para editarlo aparte.
- **🎥 Video con HUD**: overlay y composición final (flujo por defecto).

La pantalla inicial muestra los tres insumos del flujo: **referencia**, **piloto** y **salida**. El flujo por defecto aparece pre-seleccionado con un aviso neutro; pulsa «Empezar» para confirmar o elige otro con «Elegir este». Si no tienes una referencia externa, puedes cargar el mismo CSV como referencia y piloto y elegir dos vueltas distintas en el Paso 1 para compararte contra ti mismo.

El **sidebar izquierdo** muestra el progreso: ✅ paso completado, ▶️ paso actual, ○ paso pendiente en tu flujo, · paso opcional fuera del flujo elegido. El botón **🔄 Nueva sesión** al pie del sidebar borra todo el estado y vuelve al Paso 0 sin recargar la pestaña del navegador — útil para analizar otra tanda sin cerrar la app.

## 4. Compara

```
fantasma compare --reference ref.csv --driver mi_outing.csv -o salida/
```

Lee `salida/report.md`. La columna **Tiempo perdido** es la verdad: cuánto delta acumulas entre la entrada y la salida de cada curva. **Δv** te dice si el problema es velocidad de paso; **Frenada Δm** si es el punto de frenada (positivo = frenas después que la referencia, negativo = antes).

### Desde la UI — Paso 2

La tabla de curvas muestra **Diferencia km/h** y **Tiempo ganado/perdido**. Los signos son opuestos a propósito: Diferencia km/h positivo (+) significa que vas más rápido que la referencia en ese ápex; Tiempo ganado/perdido positivo (+) significa que **pierdes** tiempo ahí (vas más lento en promedio en ese tramo). Las curvas se ordenan de mayor a menor impacto en el crono.

Al pie de la tabla hay un botón **⬇️ Descargar tabla de curvas (CSV)** para guardar el reporte localmente.

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

> Para una descripción detallada de cada elemento visual del HUD (paneles, colores, franja de datos) consulta la [referencia del HUD](hud-reference.md).

```
fantasma overlay --reference ref.csv --driver mi_outing.csv --corners salida/corners_detected.json -o salida/
```

Produce `overlay.webm` (VP9 con canal alfa) o `overlay.mov` (ProRes 4444) de la duración exacta de tu vuelta. En máquinas multi-core el render se paralela automáticamente (`N_cores − 1` procesos).

Requiere [ffmpeg](https://ffmpeg.org/) en el PATH. Sin ffmpeg genera los frames PNG igualmente.

```
# Windows — instalar ffmpeg de una vez:
winget install Gyan.FFmpeg
```

### Previsualizar el overlay

Abre `overlay.webm` en [VLC](https://www.videolan.org/vlc/) para verificar que el HUD se ve correcto antes de editar. VLC reproduce WebM con alfa sin configuración adicional.

```
winget install VideoLAN.VLC
```

### Sincronizar y componer con `fantasma compose` (recomendado)

Una vez que tienes el overlay y la grabación, el comando `compose` los fusiona automáticamente:

```
# Con offset manual (sabes cuántos segundos de preámbulo tiene el video):
fantasma compose --video "grabacion.mp4" --overlay "salida/overlay.webm" --offset 5.0 -o "resultado.mp4"

# Con detección automática de offset por correlación de audio (requiere scipy):
pip install "fantasma-inputs[sync]"
fantasma compose --video "grabacion.mp4" --overlay "salida/overlay.webm" \
    --auto-sync --driver "mi_outing.csv" -o "resultado.mp4"
```

La detección automática extrae la energía del motor del audio del video (banda 150–500 Hz) y la correlaciona con la señal de RPM/velocidad de la telemetría. Precisión ~0.5 s. Funciona con cualquier sim que exporte RPM o velocidad.

Si usas `fantasma ui`, el Paso 4 incluye un botón «Detectar sincronía automáticamente» que hace lo mismo desde la interfaz gráfica.

> **Aviso de «correlación moderada».** Si la sincronía se aceptó pero con una correlación solo
> moderada (calidad media), verás un aviso de que el video **podría no corresponder a esa vuelta**
> — típico cuando se elige por error un video de la **misma pista y el mismo auto pero de otra
> sesión/fecha**. No se bloquea: el offset se carga igual, pero conviene **verificar el inicio del
> HUD** (que la marcha/velocidad/distancia coincidan con el video) antes de exportar. Un match
> robusto (calidad alta) no muestra este aviso.

#### Referencia visual de sincronía

El HUD muestra en todo momento la **marcha** (1–6/N/R), la **velocidad en km/h** y la **distancia en metros**. Si el video tiene el velocímetro o el contador de marchas visible, puedes verificar visualmente que el HUD coincide con lo que se ve en pantalla.

### Sincronizar manualmente con un editor de video

Si prefieres componer el video con un editor externo, la opción open source recomendada es **[Kdenlive](https://kdenlive.org/)** (GPL, Windows/Mac/Linux):

```
winget install KDE.Kdenlive
```

Flujo en Kdenlive:

1. **Proyecto nuevo** → ajusta la resolución a la de tu grabación (p. ej. 1920×1080).
2. **Pista V1** (abajo): tu grabación de la vuelta.
3. **Pista V2** (arriba): `overlay.webm` — Kdenlive aplica el canal alfa automáticamente.
4. **Sincronización**: usa los campos de marcha/velocidad/distancia del HUD como referencia visual, o calcula el offset con `fantasma compose --auto-sync` y aplícalo como blank inicial en la pista del overlay.
5. **Exportar**: H.264 MP4 con el perfil que prefieras.

Otras opciones compatibles: Premiere Pro, DaVinci Resolve (gratuito), CapCut.

Opciones útiles del comando `overlay`: `--format webm` (predeterminado) o `--format prores` (.mov, máxima calidad), `--start/--end` para renderizar solo un tramo, `--fps 60` si tu grabación es a 60, `--all-laps` para renderizar todas las vueltas completas del archivo en lote.

## Preguntas frecuentes

**¿Las vueltas tienen que medir exactamente lo mismo?** Diferencias de longitud <0.5% (línea de pilotaje, versión del trazado) son normales y el error de alineación resultante es de pocos metros. Trazados distintos (chicane vs sin chicane) no son comparables.

**¿Por qué mi delta total no coincide exacto con la suma por curvas?** Las curvas no cubren el 100% de la vuelta (las rectas puras quedan fuera) y los segmentos se redondean. La traza continua (`delta.csv`) es la referencia exacta.

**¿Funciona con vueltas mojadas vs secas, o coches distintos?** Funciona, pero el debrief mezclará diferencias de condiciones con errores de pilotaje. Compara como-con-como cuando puedas.
