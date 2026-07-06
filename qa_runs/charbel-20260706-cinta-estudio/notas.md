# Cinta de estudio — corrección de rumbo del PO (2026-07-06)

**Corrección de entendimiento (PO, textual):** los sonidos en pista existen para "marcar
las referencias de cómo manejar" — **TODOS salen de la vuelta de REFERENCIA** (dónde frena,
acelera y cambia de marcha el rápido). La vuelta del piloto solo sirve para mapear
distancia→tiempo sobre SU video. Y los sonidos se **agregan** unos a otros (banda sonora
completa), no se sustituyen. El demo anterior (`_DEMO_UPSHIFT.mp4`) violó ambas cosas:
upshifts de la vuelta del PO y sin los demás cues — **no volver a ese camino**.

**El propósito del video completo:** cinta de estudio — verlo y oírlo para aprender qué
significa cada sonido, cuándo llega y en qué circunstancias, y practicar sin estar en
carrera (sin imaginación mental ni técnicas de visualización).

## Qué es `_DEMO_COMPLETO.mp4`

`C:\Users\amedina\Downloads\0207\_DEMO_COMPLETO.mp4` = video del PO (vuelta 394.05 s) +
**174 sonidos, todos de la referencia** (378.40 s):

- **101 cues de coaching** (pack ADR 0024, todas las curvas): countdown de frenada
  660-770-880 Hz ~3.5 s antes, frenada 1000 Hz, soltar freno 720, turn-in 660, apex 440,
  gas 260, gas a fondo 180.
- **73 upshifts de la referencia** a **1500 Hz** (más agudo que todo lo demás): "aquí sube
  marcha el rápido".

Script reproducible: `demo_completo.py`; salida en `salida.txt`. Pack en
`Downloads\0207\_pack_COMPLETO`.

## Iteración 2 — subtítulos (feedback del PO tras escuchar)

Veredicto del PO sobre la iteración 1: **upshifts perfectamente sincronizados** (el
mecanismo dist→tiempo queda validado a oído); las frenadas confunden — no sabía qué
significaba el countdown de 3 tics — y "creo que en algunas curvas faltan" (correcto: 16
cues descartados por gap global + máx. 3 por curva; el detalle vive en `plan.json`).

Solución al "¿qué significa cada sonido?": **subtítulos**. `subtitulos.py` genera un `.srt`
desde el metadata del pack (mismo mapeo dist→tiempo del mux) con un rótulo por sonido
("🔔 3-2-1 FRENA en ~3 s — C13", "⬆ subida a 4a — así cambia el rápido"), agrupando sonidos
a <1 s en un solo rótulo (138 rótulos / 174 sonidos), y lo incrusta como pista `mov_text`
**sin re-encodear** (`-c copy`): `_DEMO_COMPLETO_SUBS.mp4` (subtítulos apagables en el
reproductor; el `.srt` suelto queda junto al video para cualquier player).

**Candidata a motor/UI si al PO le funciona:** generar el `.srt` es un subproducto natural
de `render_pace_notes_track` (ya conoce distancia, tiempo y descripción de cada entry).

## Iteración 3 — "el 3 debe ser el ya" (feedback del PO en el metro 4463)

Reporte del PO viendo la cinta: "metro 4463 salen los 3 bips de frenada y no hay ni cerca
ninguna frenada […] el 3er bip tiene que coincidir siempre con el inicio de la frenada,
nada de 1,2,3, ya; el 3 debe ser el ya". Diagnóstico con datos: era el countdown de C13
sonando completo en 4408 (los 3 tics en un solo WAV, 274 m antes) con la frenada real de
la referencia en **4682** (282 km/h) — diseño viejo correcto según ADR 0024, pero confuso:
tras el tercer tic venían ~3.5 s de silencio y nada marcaba la frenada.

**Rediseño (rama `feat/countdown-el-3-es-el-ya`):** el evento `brake_countdown` se ancla
en la FRENADA y lleva `lead_m`; `build_tone_pack` lo expande en WAVs independientes:
2 tics de aviso (660/770 Hz) a `lead_m` y `lead_m/2` antes, y el "¡ya!" es el **tono de
frenada (1000 Hz)** exacto donde frena la referencia. Tics que caen a <50 m de otro cue o
en d≤0 se omiten; el "¡ya!" nunca se pierde.

Cinta regenerada (203 sonidos = 130 coaching + 73 upshifts; el conteo sube porque cada
countdown ahora son hasta 3 WAVs). Verificado en el metadata: C13 tics en 4408 y 4545,
"punto de frenada" exacto en **4682**; en C14 los 2 tics se omitieron por encimarse con
los cues de C13 pero su "¡ya!" está en 4850. Rótulos: 161 (`_DEMO_COMPLETO_SUBS.mp4`
regenerado).

**Pendiente:** el PO dijo "ya vi los problemas" (plural) — solo ha reportado este; falta
recibir el resto de la lista.

## Nota de interpretación al escucharlo

Los sonidos marcan a la referencia, no al PO: donde su manejo difiere del rápido (que es
donde pierde tiempo), el sonido caerá "corrido" respecto a lo que se ve en el video — ese
desfase ES la información. Los upshifts de referencia a 1500 Hz NO deben coincidir con los
cambios audibles del motor del PO cuando sus puntos de cambio difieren.
