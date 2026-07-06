# ADR 0027 — Subtítulos de cues quemados en el video de estudio

- **Estado:** Aceptada
- **Fecha:** 2026-07-06

## Contexto

El Paso 4 ya puede mezclar los tonos del pack de Pace Notes en el audio del
video compuesto (ADR 0024). Pero al revisar la cinta, el piloto no siempre
distingue **qué significa cada bip**: la frenada, el contador de frenada, el
inicio de acelerador y el gas completo suenan parecido, y sin la telemetría
delante es fácil perderse. El PO lo dijo textual: «ando bien perdido con qué
significa cada sonido». Sin poder mapear sonido→significado no puede validar a
oído si los cues caen donde deben — y esa validación auditiva es el gate de
aceptación del rediseño de cues (ADR 0026).

Un prototipo desechable (script manual sobre un clip ya compuesto) confirmó que
un rótulo por cue, con color por tipo y una leyenda, vuelve la cinta legible.
Pero un entregable que sale de un script hecho a mano no es una prueba fiable de
lo que hace el producto: tiene que salir del flujo real de la UI.

## Decisión

Los subtítulos de cues son una **capacidad del compose**, no un script aparte.
`compose_video(..., burn_cue_subs=True)` genera un `.ass` desde el mismo pack
(`build_cue_ass` en `pacenotes.py`) y lo quema en el **mismo encode** que ya
superpone el HUD y mezcla los tonos. El Paso 4 lo expone como el checkbox
«Añadir subtítulos que nombran cada sonido», dentro de la sección de Pace Notes.

Cada rótulo usa el **mismo** `_dist_to_time(lap, dist)` que el audio de los cues
(`render_pace_notes_track`), así el texto y el tono caen juntos. El color por
etiqueta vive en una única fuente, `CUE_SUB_COLORS`, alineada con las etiquetas
que `MILESTONE_LABELS` ya escribe en `entry["description"]`.

## Razones

- **Fiable:** la cinta subtitulada sale del flujo con clics (E2E), no de un
  script — es lo que de verdad produce el usuario.
- **Un solo encode:** reusar `compose_video` evita un segundo re-encode y
  garantiza que subtítulo, HUD y tono comparten los mismos tiempos.
- **Fuente única de tiempos y colores:** el `.ass` y el WAV se sincronizan con
  la misma función; los colores no se duplican entre código y leyenda.
- **Windows-safe:** el `.ass` se referencia por nombre relativo y ffmpeg corre
  con `cwd` en su carpeta, esquivando el escape de `C:` en el filtro `ass`.

## El camino que NO se toma (y por qué tienta)

- **Un segundo paso «subtitular un video ya hecho»** (como el mux del Paso 5).
  Tienta porque no re-encoda, pero el `.ass` necesita la resolución y la vuelta
  del clip, y quemar texto SÍ re-encoda el video igual — no hay ahorro real, y
  duplica superficie de sincronía que ya resuelve el compose.
- **Subtítulos como pista `.srt` seleccionable** en vez de quemados. Tienta por
  reversible, pero el objetivo es una cinta de estudio que se ve igual en
  cualquier reproductor y al compartirla; un `.srt` suelto se pierde.
- **Colores nuevos inventados para los subtítulos.** Tienta para «que se vean
  bonitos», pero divergir de la semántica de sonidos confunde: la leyenda del
  subtítulo debe hablar el mismo idioma de color que el resto del producto.

## Consecuencias

- El Paso 4 puede producir una **cinta de estudio autoexplicativa** sin material
  manual. Desbloquea la validación auditiva del ADR 0026.
- `compose_video` gana un parámetro (`burn_cue_subs`) y una dependencia suave de
  `pacenotes.build_cue_ass`; sin `pace_notes_dir` + `lap` el flag no hace nada.
- Queda pendiente de validar a oído/vista por el PO que cada rótulo cae con su
  tono en una vuelta real (spot-check en la frenada y un par de curvas).
- La posición del rótulo despeja el HUD asumiendo su alto real (overlay·escala);
  si el HUD se coloca en una esquina inusual con escalas extremas, el rótulo
  podría acercarse — aceptable para la cinta de estudio (HUD abajo por defecto).
