# Guía de usuario

> Documenta **SimGhostInputs** — la versión instalada aparece en el badge del pie del sidebar (ver §3 «Desde la UI»).

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

`fantasma-ng` abre un asistente en ventana de escritorio nativa (NiceGUI + pywebview) en **modo oscuro** (siempre activo, garantiza contraste legible). La app escucha exclusivamente en `127.0.0.1` — no es accesible desde otras máquinas en la red. En el **Paso 0** eliges qué salida quieres:

- **📊 Solo análisis**: reporte, CSVs y gráficas.
- **🎬 Solo overlay**: HUD transparente para editarlo aparte.
- **🎥 Video con HUD**: overlay y composición final (flujo por defecto).
- **🔔 Solo Pace Notes**: importar y analizar, luego generar el pack de audio para CrewChief — salta los pasos de overlay y composición de video. Ruta: Importar (1) → Análisis (2) → Pace Notes (5).

La pantalla inicial muestra los tres insumos del flujo: **referencia**, **piloto** y **salida**. El flujo por defecto aparece pre-seleccionado con un aviso neutro; pulsa «Empezar» para confirmar o elige otro con «Elegir este». Si no tienes una referencia externa, puedes cargar el mismo CSV como referencia y piloto y elegir dos vueltas distintas en el Paso 1 para compararte contra ti mismo.

El **sidebar izquierdo** muestra el progreso: ✅ paso completado, ▶️ paso actual, ○ paso pendiente en tu flujo, · paso opcional fuera del flujo elegido. El botón **🔄 Nueva sesión** al pie del sidebar borra todo el estado y vuelve al Paso 0 sin recargar la pestaña del navegador — útil para analizar otra tanda sin cerrar la app. En la esquina inferior izquierda hay un **badge de versión** (p. ej. «v2.2 · AMS2 · MoTeC») que muestra la versión instalada; cítalo al [reportar un bug](../CONTRIBUTING.md) (CONTRIBUTING §1 lo pide).

Los **botones de acción** (Empezar, Componer video, Generar overlay, etc.) se ven en **azul sólido con texto blanco cuando están listos** para pulsarse; cuando les falta algún requisito se ven **atenuados** y —en los pasos que lo indican— un texto debajo dice exactamente qué falta.

El **Paso 1** muestra dos paneles de carga, uno para la vuelta de referencia y otro para la tuya. En cada panel aparece una zona de carga integrada en el browser: haz clic en ella para abrir el selector de archivos del sistema operativo, o arrastra el `.csv` (o `.xlsx`) directamente sobre la zona. La app detecta las vueltas del archivo automáticamente; si hay más de una, aparece un desplegable para elegir cuál usar (por defecto se pre-selecciona la más rápida). Una vez subidos ambos archivos, pulsa el botón de avance para continuar.

## 4. Compara

```
fantasma compare --reference ref.csv --driver mi_outing.csv -o salida/
```

Lee `salida/report.md`. La columna **Tiempo perdido** es la verdad: cuánto delta acumulas entre la entrada y la salida de cada curva. **Δv** te dice si el problema es velocidad de paso; **Frenada Δm** si es el punto de frenada (positivo = frenas después que la referencia, negativo = antes).

### Desde la UI — Paso 2

La tabla de curvas muestra **Diferencia km/h** y **Tiempo ganado/perdido**. Los signos son opuestos a propósito: Diferencia km/h positivo (+) significa que vas más rápido que la referencia en ese ápex; Tiempo ganado/perdido positivo (+) significa que **pierdes** tiempo ahí (vas más lento en promedio en ese tramo). Las curvas se ordenan de mayor a menor impacto en el crono.

El Paso 2 se divide en pestañas. **Curvas prioritarias** es la primera y concentra la tabla, el selector **Curva a atacar** y el drill-down de la curva elegida. Por defecto queda seleccionada la curva donde más tiempo pierdes. El panel resume la palanca principal y muestra un plan de ataque con las señales disponibles: punto de frenada, pico de freno, V-Min, gas 100%, G lateral y marcha/RPM en ápex. Si falta un canal opcional (`gear`, `glat`, `rpm`), esa fila se omite sin romper el análisis.

Las pestañas **Resumen de vuelta** y **Vuelta completa** dejan el contexto pesado bajo demanda: mapa de delta, barras, G-G y la gráfica de todos los canales no compiten con el drill-down inicial.

Al pie de la pestaña **Curvas prioritarias** hay un botón **⬇️ Descargar tabla de curvas (CSV)** para guardar el reporte localmente.

Interpretación honesta:
- Δ de frenada menores de ~10m son ruido; mayores de ~100m suelen ser un artefacto del detector (frenadas distintas emparejadas), no un error tuyo de 100m.
- Una V-Min MÁS ALTA que la referencia con tiempo perdido es el clásico "rápido adentro, lento afuera": estás sacrificando la salida.

## 5. Nombres de curvas (track pack)

```
fantasma detect ref.csv -o salida/
```

Genera `corners_detected.json`. Edítalo: añade `"name": "Curva del puente"` a cada curva (los IDs son C01, C02... en orden de pista). Pásalo con `--corners` en todas tus comparaciones. Comparte el JSON con tu liga: los nombres y metros de un circuito son datos de la comunidad.

El mismo comando también detecta los **cambios de marcha** de esa vuelta y los guarda bajo la clave `gear_shifts` del mismo archivo (esquema en [`formato-datos.md`](formato-datos.md#cambios-de-marcha-gear_shifts)); alimenta el cue «Cambio de marcha» del Paso 5 / `fantasma pacenotes` (ver §6).

Ahí mismo puedes ajustar `"tolerances"` por curva: `vmin_kmh` y `brake_start_m` controlan cuándo el reporte marca avisos.

## 6. Pace Notes para CrewChief

Después de comparar, puedes convertir las curvas donde más pierdes en un pack de audio para CrewChief.

### Desde la UI — Paso 5

Se llega al **Paso 5** de dos formas:
- **Flujo habitual**: el botón **«🔔 Generar Pace Notes»** al pie del análisis del Paso 2.
- **Flujo "Solo Pace Notes"**: directo desde el Paso 0 eligiendo esa tarjeta; la ruta es Importar (1) → Análisis (2) → Pace Notes (5), saltando overlay y compose.

El Paso 5 tiene **dos paneles independientes**:

**① Generar pack nuevo** (panel izquierdo): requiere haber corrido el Análisis (Paso 2). Si el análisis no está disponible, este panel muestra un aviso con botón de vuelta al Paso 2.

1. Elige el **modo**: _Tonos (rápido)_ (sin dependencias extra), _Voz_ (requiere edge-tts) o _Ambos_.
2. Ajusta **Top N curvas** (cuántas cubrir), o marca **«Todas las curvas»** para cubrir cada curva detectada — también donde no pierdes tiempo (la frenada suena como marca de ritmo, estilo rally). Ajusta **volumen** y — en modo voz — el **idioma**.
3. La **leyenda de tonos** (panel plegable) explica qué significa cada bip y su frecuencia. Importante: los tonos marcan los puntos de la vuelta de **referencia** — si un tono no coincide con lo que haces, ese desfase es el consejo, no un error de sincronía. **Toda curva con frenada suena su tono**, exacto donde frena la referencia — ningún otro sonido se lo tapa ([ADR 0026](decisions/0026-cues-frenada-universal-countdown-oportunista.md)). El countdown (2 tics de aviso, separados por un gap uniforme de 0.75 s entre sí y hasta la frenada real, a tu velocidad de llegada — [ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)) aparece **solo donde cabe** junto a otros sonidos; en curvas encadenadas o densas puede faltar y solo suena el tono de frenada. El tono de **ápex** volvió al catálogo de cues como opción apagada por defecto (ver punto 4 más abajo) — el hito siempre se conserva en los datos y en las notas de voz, suene o no.
4. **Cues: selección y prioridad** (panel plegable, abierto por defecto): una fila por tipo de cue implementado — Countdown de frenada, Frenada, Soltar freno, Turn-in, Inicio de acelerador, Gas completo, Ápex, Coast (inercia) y **Cambio de marcha**. Cada fila trae una casilla para activarlo/apagarlo y un número de **prioridad** (mayor número gana el hueco cuando dos sonidos compiten por el mismo espacio). Coast trae además la casilla «Solo curvas sin frenada» (el resto de la curva ya lo cubre el freno/turn-in/release cuando sí hay frenada). Apagar «Frenada» apaga también el countdown, que depende de ella — un aviso lo señala, pero no se bloquea: la decisión es tuya. «Cambio de marcha» marca los cambios de marcha de la vuelta de **referencia** solo con **subtítulo, sin sonido todavía** (el tooltip de la casilla lo aclara) — evita meter una frecuencia nueva al catálogo sin comprobarla de oído primero ([ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)). Ápex, Coast y Cambio de marcha vienen **apagados por defecto** (no-regresión con el pack de siempre); actívalos si los quieres. El sonido «Inicio de acelerador» ahora exige que el gas se sostenga varias muestras seguidas — ya no dispara con un roce fugaz del pedal—; el tramo de inercia entre el fin de la frenada y ese gas sostenido, antes sin nombrar, es justo lo que marca Coast cuando lo activas. Ver [ADR 0027](decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md) para el porqué del catálogo configurable, el coast y los subtítulos quemados (sección 7 más abajo), y [ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md) para el reencuadre de prioridades/countdown/frecuencias y el cue `gear`.
   - **Perfiles de cues**: el desplegable «Cargar perfil» lista los perfiles guardados en tu carpeta de perfiles (`~/.simghostinputs/cue-profiles/`); elegir uno aplica su selección y prioridades de inmediato. «Importar…» abre cualquier archivo `.json` de perfil desde otra carpeta. «Guardar perfil» pide un nombre (y una descripción opcional) y guarda la configuración actual como un perfil reusable; si ya existe un perfil con ese nombre, pide confirmar antes de sobrescribirlo. Un perfil con formato inválido, tipos de dato torcidos (p. ej. una prioridad que no es número) o de una versión no soportada muestra un aviso claro, sin interrumpir el resto del Paso 5 — son datos compartibles entre usuarios (packs de comunidad) y un archivo malformado de un tercero nunca debe tumbar la app.
   - Tu selección se recuerda automáticamente entre sesiones (se guarda con tu perfil de usuario de la app); si nunca la tocas, el pack se genera igual que siempre.
5. El **directorio de salida** se pre-rellena automáticamente con la ruta de CrewChief detectada para el circuito. Si no se detecta, escribe el nombre exacto que CrewChief/AMS2 espera o usa «Explorar…» para navegar.
6. Pulsa **«Generar Pace Notes»**: un spinner indica el progreso; al terminar verás cuántas entradas se generaron y el sidebar marca el Paso 5 como completado (✅). El pack usa la selección y prioridad de cues configuradas arriba.

**② Aplicar sonido a un video existente** (panel derecho): siempre visible, sin importar si hay análisis disponible. Si ya tienes el video compuesto (por el flujo habitual u otro programa) y quieres añadirle el audio del pack, este panel lo hace sin re-encodear el video (ffmpeg `-c:v copy`). Requiere la vuelta del piloto cargada (Paso 1) para sincronizar los cues; ajusta el **volumen** del pack antes de aplicar. El botón «Aplicar sonido» se habilita cuando están el video, la carpeta del pack y la vuelta del piloto — y cuando algo falta, un texto bajo el botón dice exactamente qué.

> **Verificación video↔vuelta:** los videos compuestos por el Paso 4 llevan al lado un archivo `*.sync.json` con la identidad de la vuelta ([ADR 0024](decisions/0024-sincronia-pace-notes.md)). Al elegir uno, el panel avisa si la vuelta cargada no corresponde (✓ verde si coincide, ⚠ si no), y el mux se niega a mezclar con la vuelta equivocada — era la causa de cues corridos por segundos. Videos externos sin `.sync.json` se procesan como siempre.

> **Restricción de las Pace Notes:** exigen dos vueltas (referencia + piloto) porque priorizan las curvas por tiempo perdido. No se generan de una sola vuelta ni directamente desde un video.

La **barra de pasos** (breadcrumb) muestra solo los pasos de tu flujo: en "Solo Pace Notes" verás Inicio › Importar › Análisis › Pace Notes, sin Overlay ni Video. Antes de elegir un flujo en el Paso 0 (o si navegas a un paso fuera de tu flujo), la barra muestra los 6 pasos completos.

Activa las Pace Notes dentro de CrewChief antes de salir a pista.

### Desde el CLI

```
fantasma pacenotes --corners salida/corners_detected.json --compare salida/corners_compare.csv \
    --top 5 --mode tones --output-dir "%USERPROFILE%\Documents\CrewChiefV4\pace_notes\ams2\nordschleife"
```

El modo `tones` no usa red ni TTS: genera WAVs 24 kHz mono con tonos para los hitos elegidos. Por defecto no suena todo siempre: Fantasma escribe `plan.json` y limita cada curva a pocas señales útiles, con separación mínima entre eventos **también entre curvas encadenadas** (sobrevive la señal de mayor prioridad). El tono de frenada es la excepción: es **universal y protegido** ([ADR 0026](decisions/0026-cues-frenada-universal-countdown-oportunista.md)) — suena en toda curva con frenada, exacto en el punto de frenada de la referencia, sin que ningún gap lo descarte. El countdown (2 tics de aviso, separados por un gap uniforme de 0.75 s entre sí y hasta la frenada real, calculado a la velocidad de llegada — [ADR 0024](decisions/0024-sincronia-pace-notes.md), reencuadrado en [ADR 0028](decisions/0028-cues-reencuadre-prioridades-countdown-frecuencias-gear.md)) es **oportunista**: cada tic entra solo si cabe a la separación mínima de todo lo que ya suena (frenadas y tics de otras curvas incluidos); en curvas encadenadas o densas puede faltar y la curva queda solo con su tono de frenada. Las señales que caerían antes de la meta se descartan. Ya no hay tono de ápex (el hito se conserva en los datos). Con `--top 0` cubre todas las curvas detectadas (pace notes de ritmo).

Si no pasas `--output-dir`, Fantasma intenta usar el campo `track` del JSON de curvas; si no existe, te pregunta el nombre exacto de pista que CrewChief/AMS2 espera. Para voz contextual instala `pip install "fantasma-inputs[voice]"` y usa `--mode voice` o `--mode both`; requiere ffmpeg para convertir el audio a WAV.

Activa las Pace Notes dentro de CrewChief antes de salir a pista. Una vez activas, CrewChief reproduce los audios automáticamente en la siguiente vuelta.

## 7. Video con HUD transparente

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

# Preview de overlay + Pace Notes mezclados en el audio del video:
fantasma compose --video "grabacion.mp4" --overlay "salida/overlay.webm" \
    --driver "mi_outing.csv" --pace-notes-dir "salida/pace_notes" -o "preview_pacenotes.mp4"
```

La detección automática extrae la energía del motor del audio del video (banda 150–500 Hz) y la correlaciona con la señal de RPM/velocidad de la telemetría. Precisión ~0.5 s. Funciona con cualquier sim que exporte RPM o velocidad.

El preview de Pace Notes no sustituye a CrewChief: mezcla los mismos WAVs dentro del MP4 para escuchar si el plan de sonidos está demasiado cargado o llega a buen tiempo. Requiere `--driver` porque los metros del `metadata.json` se convierten a segundos con la telemetría de la vuelta.

Si usas `fantasma-ng`, el Paso 4 incluye un botón «Detectar sincronía automáticamente» que hace lo mismo desde la interfaz gráfica. Una vez completada la composición, el Paso 4 muestra qué encoder se usó realmente (`h264_nvenc` si se detectó GPU NVIDIA, `libx264` si no) y cuánto tardó — útil para diagnosticar si la GPU se está aprovechando.

El **Paso 3 (flujo «Video con HUD»)** incluye un checkbox «Al terminar, componer automáticamente»: al activarlo, al finalizar el overlay la app navega al Paso 4 y lanza la composición sin intervención; al terminar el compose recibirás una notificación de escritorio (o un aviso en pantalla si el navegador no lo soporta).

El **Paso 4** incluye una sección opcional **«Pace Notes en el video compuesto»**: activa el checkbox e indica la carpeta del pack generado en el Paso 5; los WAVs se mezclan en el audio del video final durante el compose. Si ya tienes un video compuesto al que solo quieres añadir el sonido del pack, usa el panel «Aplicar sonido a un video existente» del Paso 5 (sin re-encodear).

Dentro de esa misma sección, la casilla **«Quemar subtítulos de cues (nombra cada sonido + leyenda)»** rotula sobre el video, en el instante exacto de cada sonido, una etiqueta con color por tipo de cue más el nombre de la curva —sincronizada con el tono— más una leyenda de colores fija arriba a la izquierda. Solo se rotulan los cues habilitados en el Paso 5 (coast incluido, con la etiqueta «inercia»); si apagaste un cue, no aparece su subtítulo. La duración de cada rótulo es **adaptativa**: dura hasta que entra el siguiente cue (con un respiro breve), acotada entre un mínimo legible y un máximo, en vez de una ventana fija — así no se apaga antes de tiempo ni queda un rótulo viejo colgado en una recta larga. Es la forma más rápida de revisar o aprender un pack de cues antes de llevarlo a pista: detalle del código de colores en la [referencia del HUD](hud-reference.md) y diseño completo en el [ADR 0027](decisions/0027-cues-catalogo-configurable-perfiles-coast-subtitulos.md).

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
