# Diagnóstico del "desync" de pace notes — 2026-07-05 (Charbel, en sesión)

**Contexto.** La sesión 1d56f67f murió con una hipótesis sin verificar: que la referencia
(`GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv`) y la vuelta del piloto
(`Nordschleife_2020_..._Race_2026-06-07T113535.csv`, lap de 394.05 s = video `2_composed.mp4`)
medían la pista con calibración de distancia distinta, y que eso causaba el desync audible.

## Veredicto

**Hipótesis REFUTADA.** Evidencia en `salida1-calibracion.txt` y `salida2-cues-reales.txt`
(scripts `diagnostico.py` / `diagnostico2.py`, reproducibles):

1. **Calibración de distancia: idéntica en la práctica.** Largo referencia = 20 592 m,
   piloto = 20 571 m (ratio 0.99898). Ajuste lineal entre apexes emparejados:
   `d_drv = 0.99969·d_ref + 6.7 m`. El "20 237 vs 20 571" de la sesión anterior comparaba
   el último cue contra el largo de pista — manzanas con peras.
2. **El mapeo distancia→tiempo es correcto.** `time` de la vuelta arranca en 0 y
   `_dist_to_time` da 0 s en d=0 y 394.05 s en d=fin. Los cues de apex de los packs que
   escuchó el PO caen a **±1.1 s del paso real** por la curva (mediana ~0.5 s). No hay
   deriva progresiva.

## Entonces, ¿por qué se OYE desincronizado?

Causas reales encontradas en los packs que el PO escuchó (`Downloads\0207`):

- **a) Cues clavados en t=0.** `C01 — punto de frenada` a d=0 → suena en el segundo 0.0 del
  video (también la voz de C01). Causa: `max(0, brake_d - 200)` / `max(0, brake_d - countdown_m)`
  clampa al 0 cuando la frenada está cerca de meta. Primera impresión inmediata de "esto está roto".
- **b) Sopa de tonos entre curvas encadenadas.** El `min_gap_m=50` solo aplica DENTRO de una
  curva; entre curvas no hay gap (ej.: soltar-freno C48 en 16 182 m y countdown C49 en 16 205 m
  = 23 m ≈ 0.4 s). En la zona C16–C18: 6 tonos intercalados de 3 curvas en 11 s. Con 51–111
  cues por vuelta y tonos de 0.12 s casi indistinguibles (sin leyenda en la UI, brake y
  countdown ambos a 880 Hz), el cerebro no puede asignar tono→evento → se percibe aleatorio.
- **c) Anticipación fija en metros.** `countdown_m=120` suena ~2 s antes a velocidad GT3 —
  "suena cuando no pasa nada". El PO pidió anticipación por TIEMPO (3–4 s).
- **d) Los cues marcan los puntos de la REFERENCIA.** Es coaching correcto, pero donde tu
  frenada difiere de la de la referencia (que es justo donde pierdes tiempo) el tono cae
  "corrido" respecto a lo que haces — sin leyenda, se lee como desync y no como consejo.
- **e) Sin vínculo video↔vuelta (sidecar pendiente).** En los demos de la sesión la vuelta
  correcta estaba controlada; en el exe, el panel ② muxea con la vuelta que esté cargada.
  Cargar otra vuelta/archivo produce desync REAL de segundos. Sigue siendo fix necesario.

## Qué NO está roto

- `render_pace_notes_track` y el mux (mecanismo confirmado también por el demo de marchas).
- El fix `normalize=0` de `compose.py` (working tree): sigue siendo válido e independiente
  de esto — sin él, además, los cues quedan −6 dB bajo el motor.
