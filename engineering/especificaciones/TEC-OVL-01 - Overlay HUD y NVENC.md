---
tipo: especificacion_tecnica
clave: TEC-OVL-01
tecnologia: Python (extra opcional overlay: Pillow, matplotlib, numpy) + ffmpeg
estado: vigente
---

# TEC-OVL-01 — Overlay HUD y NVENC

## Contexto técnico
Genera el HUD animado con canal alfa y lo compone sobre el video. La **anatomía y el código de color** del HUD son dueño de [`../../docs/hud-reference.md`](../../docs/hud-reference.md); aquí va el **CÓMO técnico** del render. `fantasma/viz/overlay.py` + `compose.py`.

## Render del HUD (`overlay.py`)
- `_HUDFigure`: figura matplotlib reutilizable (~1870×572 px), 3 paneles `sharex` (gas, freno, volante) + franja superior con textos dinámicos (GAP, ΔV, DESLIZ, ABS/TC, GASTO, marcha, distancia, km/h, curva). `update()` modifica solo datos, no recrea la figura. `to_pil()` → PIL RGBA.
- Ventana: 320 m antes / 200 m después del cursor. ABS/TCS quedan encendidos 8 m tras la última activación.
- **Render paralelo** (`_render_parallel`): `cpu_count − 1` subprocesos vía `python -m fantasma.viz._overlay_worker`, args serializados a `.pkl` por chunk (evita el crash de `ProcessPoolExecutor` spawn bajo Streamlit). Fallback serial por chunk; cancelación mata workers.
- Formatos: `webm` (libvpx-vp9, yuva420p) o `prores` (.mov, prores_ks 4444, yuva444p10le).

## Composición (`compose.py`)
- `_build_filter(position, scale, offset)`: `scale=iw*factor` (si ≠1) → `setpts` (modo legado) → `overlay=x:y`. En modo recorte el `-ss` posiciona y no se necesita `setpts`.
- `_nvenc_available`: probe real de 1 frame **320×240** con `h264_nvenc` (320×240 porque NVENC rechaza frames diminutos — falso negativo con 64×64, corregido v0.12.0). Fallback CPU `libx264 -crf 18 -preset fast`. NVENC ~35% más rápido medido en el host.

## Decisiones de diseño del HUD
- Grosor uniforme, piloto siempre encima ([ADR 0006](../../docs/decisions/0006-grosor-uniforme-lineas-hud.md)); indicadores instantáneos ([ADR 0005](../../docs/decisions/0005-indicadores-instantaneos.md)); sin leyenda ([ADR 0007](../../docs/decisions/0007-hud-sin-leyenda.md)).

## Vinculado con
- [[Visualizacion y HUD]]
- [Referencia del HUD](../../docs/hud-reference.md)
- [[ffmpeg]]
