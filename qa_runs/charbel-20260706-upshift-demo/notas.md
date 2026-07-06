# Demo de upshifts — pedido del PO (2026-07-06)

**Qué es.** Video `C:\Users\amedina\Downloads\0207\_DEMO_UPSHIFT.mp4`: tu vuelta de 394.05 s
(`2_composed.mp4`) con un **beep corto de 1200 Hz en cada cambio de marcha HACIA ARRIBA**
de tu propia telemetría (no de la referencia — aquí el objetivo es sentir la sincronía
contra algo 100 % tuyo, como el demo de marchas de la sesión anterior pero solo subidas).

**Datos.** 60 upshifts detectados en el canal `gear` de la vuelta. Detalle técnico: el
canal pasa por 0 (neutral) durante cada cambio (`2→0→3`), así que la detección compara
contra la **última marcha engranada**, no contra la muestra anterior (la primera versión
del filtro solo atrapaba 2). Pack en `Downloads\0207\_pack_UPSHIFT` (60 WAVs + metadata).

**Mux.** `mux_pace_notes_into_video` con `normalize=0` ya mergeado (#25) — los beeps
suenan por encima del motor sin atenuarlo. Script reproducible: `demo_upshift.py`;
salida en `salida.txt`.

**Qué escuchar.** Cada beep debe coincidir con el corte de RPM del motor al subir marcha
en el audio del video. Si esto suena clavado, el mecanismo dist→tiempo queda validado a
oído con el evento más inequívoco que existe en la telemetría.
