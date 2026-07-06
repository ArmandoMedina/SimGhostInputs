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

## Nota de interpretación al escucharlo

Los sonidos marcan a la referencia, no al PO: donde su manejo difiere del rápido (que es
donde pierde tiempo), el sonido caerá "corrido" respecto a lo que se ve en el video — ese
desfase ES la información. Los upshifts de referencia a 1500 Hz NO deben coincidir con los
cambios audibles del motor del PO cuando sus puntos de cambio difieren.
