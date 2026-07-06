# E2E del PR 2 (ADR 0024) — motor de cues con datos reales — 2026-07-05

**Setup.** Referencia `GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv` (vuelta 378.40 s) vs
piloto `Nordschleife_2020_..._Race_2026-06-07T113535.csv` (vuelta 394.05 s = video
`2_composed.mp4`). Script reproducible: `e2e.py`; salida completa: `salida-e2e.txt`.

## Resultados (todas las propiedades del ADR 0024 verificadas)

- **Pack**: `top=0` (todas las curvas) → 55 curvas, **101 cues** en `_pack_FIXED`.
- **Ningún cue en d ≤ 0**: el cue fantasma del segundo 0 (C01) quedó **descartado**
  (1 descarte con razón `antes_de_la_meta`).
- **Gap global**: ningún par de cues consecutivos a < 50 m; **16 cues de "sopa" eliminados**
  (razón `too_close_global`, sobrevive la prioridad mayor).
- **Anticipación por tiempo**: 27 countdowns con anticipo mediano de **3.60 s**
  (mín 2.76, máx 4.26) medido sobre el tiempo de la referencia — dentro de los 3–4 s
  pedidos por el PO (antes: ~2 s fijos a velocidad GT3).
- **Demo para el oído del PO**: `C:\Users\amedina\Downloads\0207\_DEMO_FIXED.mp4`
  (mux `-c:v copy` sobre el video real, pack nuevo, `normalize=0` activo).

## Pendiente de juicio humano

El PO debe escuchar `_DEMO_FIXED.mp4`: countdown a 3.5 s, frenada a 1000 Hz (ya distinguible
del countdown), sin sopa entre curvas encadenadas. La leyenda de tonos en la UI va en el PR 3.
