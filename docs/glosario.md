# Glosario

Definición canónica de los términos de SimGhostInputs. Si un término aparece en otro
documento y no se entiende, **aquí está su significado** — y aquí (no en cada doc) se
mantiene al día. Una palabra = una definición.

> Convención: cada término dice **qué es**, **para qué sirve** y, si aplica, **cómo se
> calcula** en una línea.

---

## Análisis y comparación

**Comparación por distancia**
El metro de pista es el índice maestro, no el tiempo. Ambas vueltas se remuestrean a una
rejilla uniforme de distancia y se comparan metro a metro. Es lo que permite decir "en este
punto de la pista vas más lento", independientemente de cuánto tardes.

**Vuelta de referencia / vuelta del piloto**
La *referencia* es la vuelta rápida contra la que te comparas (tuya histórica, de un
compañero, o cualquiera que tengas derecho a usar). El *piloto* (`driver`) es la vuelta que
quieres analizar. El proyecto no distribuye referencias: tú traes tus datos.

**GAP** *(franja del HUD)*
Diferencia de **tiempo acumulada** respecto a la referencia en el metro donde está el cursor.
Positivo (rojo) = vas más lento; negativo (verde) = más rápido. Responde *"¿gano o pierdo
hasta aquí?"*.

**ΔV** *(franja del HUD)*
Diferencia de **velocidad puntual** (piloto − referencia) en el metro exacto del cursor.
Negativo = llegas más lento que la referencia en ese punto.

**Tiempo perdido** (`time_lost`)
Por curva: cuánto delta de tiempo acumulas entre la entrada y la salida del segmento de esa
curva. Es la columna que ordena dónde está tu mayor palanca de mejora (insight 80/20).

**Delta continuo** (`delta.csv`)
La traza exacta del delta de tiempo metro a metro de toda la vuelta. Es la verdad de
referencia cuando la suma por curvas no cuadra (las rectas quedan fuera de las curvas).

---

## Curvas e hitos

**Curva `vmin` / curva `kink`**
`vmin` = curva con frenada y mínimo de velocidad (la mayoría). `kink` = curva rápida sin
frenada, detectada por un pico de G lateral sostenido sin caída de velocidad.

**V-Min (ápex)**
La velocidad mínima dentro de la curva: el punto de paso. "V-Min objetivo" en el HUD es la
V-Min de la referencia en esa curva.

**Hitos de la curva** (`milestones`)
Puntos clave que el detector marca en cada curva: `brake_start` (inicio de frenada real),
`turn_in` (giro de volante > 8°), `brake_release` (suelta freno < 2%), `throttle_on` (abre
gas > 5%), `apex` (V-Min), `full_throttle` (gas ≥ 98% sostenido), `g_lat_max`, `lift` (en
curvas sin freno). Cada uno lleva su metro, tiempo y velocidad.

**Solape gas/freno** (`overlap_m`)
Metros en los que pisas gas y freno a la vez (si abres gas antes de soltar el freno). Se
registra solo cuando ocurre.

**Segmento de curva** (`segment_m`)
El tramo de pista `[desde, hasta]` que "pertenece" a una curva. Se corta en el punto medio
con las curvas vecinas (tope 450 m atrás / 350 m adelante) para no contaminar una curva con
la frenada de la siguiente.

**Track pack** (`corners.json`)
El archivo con los nombres y metros de las curvas de un circuito. Lo generas con
`fantasma detect`, le pones nombres, y lo compartes con tu liga: los nombres de un trazado
son datos de la comunidad. `tolerances` por curva controla cuándo el reporte marca avisos.

---

## Desgaste de goma

> ⚠️ **DESLIZ y desgaste acumulado NO son lo mismo.** DESLIZ mide *intensidad* (qué tan duro
> castigas la goma **ahora**); el acumulado mide *cantidad* (cuánto llevas **gastado**). Uno
> sube y baja curva a curva; el otro solo crece. Ver [ADR 0009](decisions/0009-unidad-desgaste-acumulado.md).

**Deslizamiento (slip)**
Diferencia entre la velocidad de giro de la rueda y la velocidad real del coche. Negativo =
bloqueo en frenada; positivo = patinaje en aceleración. Es lo que gasta la goma. Se calibra
contra la velocidad real en tramos de rodadura libre.

**Banda muerta** (`deadband`, 2%)
Slip por debajo de este valor se considera ruido de medición y no cuenta como desgaste.

**DESLIZ** *(franja del HUD)* — **intensidad instantánea**
Promedio del exceso de slip sobre los últimos ~40 m **detrás** del cursor. Responde
*"¿dónde estoy castigando la goma ahora?"*. Sube en las curvas y baja en las rectas (no se
acumula — es a propósito; ver [ADR 0005](decisions/0005-indicadores-instantaneos.md)).

**`slip_index`** — **intensidad de un tramo**
El promedio del exceso de slip en un tramo (una curva o una vuelta entera). Mismo concepto
que DESLIZ pero sobre el tramo que se le pida. Es una *intensidad*, no una cantidad: **no se
puede sumar** entre curvas.

**Carga de deslizamiento** — **cantidad acumulable** *(planeado, [ADR 0009](decisions/0009-unidad-desgaste-acumulado.md))*
El slip **integrado sobre la distancia** (`Σ exceso de slip × metros`). A diferencia del
promedio, **sí es aditiva**: la carga de la curva 1 + la de la curva 2 = la de las dos
juntas. Es la base del medidor acumulado (cuánto has gastado). Físicamente ≈ distancia de
patinaje de la goma.

**Desgaste acumulado de la vuelta** *(planeado — overlay)*
La carga de deslizamiento corrida desde meta hasta el cursor, en el HUD. Crece a lo largo de
la vuelta. Es el "medidor de gasolina" de **una** vuelta.

**Desgaste acumulado del stint** (`fantasma wear`)
La carga acumulada **entre vueltas** de un stint, con estado (`ok`/`yellow`/`red`/`burst`) y
estimación de vueltas que faltan para el reventón, estilo medidor de gasolina. Los umbrales
los calibras tú: el número es un proxy en unidades arbitrarias, no un % físico de goma.

**Activaciones de ABS / TCS**
Cada vez que se dispara el ABS (casi-bloqueo en frenada) o el control de tracción (casi-
derrape en aceleración). En el HUD son luces que se encienden en el cursor; en el reporte,
un conteo por curva.

---

## Overlay y video

**Overlay / HUD**
El video transparente con los paneles (gas/freno/volante) y la franja de datos, sincronizado
con tu vuelta, que se superpone sobre la grabación del sim.

**Canal alfa**
La transparencia del overlay (`.webm` VP9 o `.mov` ProRes 4444): permite pegarlo sobre tu
grabación sin tapar la imagen.

**Cursor** *(HUD)*
La línea amarilla vertical = el instante actual. Lo de la izquierda ya pasó; lo de la derecha
viene. Cada panel muestra una ventana deslizante de 520 m (320 atrás, 200 adelante).

**`compose`**
El paso que fusiona el overlay con tu grabación en el video final (usa NVENC si hay GPU
NVIDIA).

**Auto-sync / offset**
El *offset* es el desfase (en segundos) entre el inicio del video y el inicio de tu vuelta.
*Auto-sync* lo detecta solo, correlacionando el audio del motor de la grabación con la señal
de RPM/velocidad de la telemetría.

---

## Telemetría y formato

**Outing**
La tanda completa que cargas (varias vueltas en un archivo) antes de separarla en vueltas.

**Stint**
La secuencia de vueltas con el mismo juego de gomas. Es la unidad sobre la que se acumula el
desgaste.

**Beacon**
Marcador de cruce de meta del log de MoTeC; la forma preferida de separar vueltas.

**Remuestreo / paso** (`step`)
Llevar los canales a una rejilla uniforme de distancia (5 m por defecto) para poder comparar
metro a metro. Interpolación lineal; para canales discretos (marcha) se usa el valor anterior.

---

*Falta un término? Añádelo aquí (una palabra = una definición) en vez de explicarlo suelto en
otro documento. Ver la matriz de mantenimiento en [`CONTRIBUTING.md` §8](../CONTRIBUTING.md#8-mantenimiento-de-documentación).*
