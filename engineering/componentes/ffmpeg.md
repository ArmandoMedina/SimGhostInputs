---
tipo: componente
tecnologia: ffmpeg
administrador: sistema del usuario (PATH)
estado: vigente
---

# ffmpeg

## Propósito
Motor externo de video. SimGhostInputs no reimplementa codificación: delega en ffmpeg el render del HUD a `.webm`/`.mov` y la composición final sobre la grabación del sim. Es dependencia **de sistema** (no de pip): debe estar en el PATH.

## Funciones clave
- **Render del overlay** (`fantasma/viz/overlay.py`): codifica los frames del HUD. `webm` = libvpx-vp9, `yuva420p`, 2M bitrate, `row-mt`; `prores` = `.mov`, `prores_ks` profile 4444, `yuva444p10le` (ambos con canal alfa).
- **Composición** (`fantasma/viz/compose.py`): superpone el HUD sobre el video. Filtergraph en `_build_filter`: `scale=iw*factor` (si hay escala) → `setpts` (modo legado) → `overlay=x:y`.
- **Aceleración GPU**: `_nvenc_available` prueba un encode real de 1 frame **320×240** con `h264_nvenc` (320×240 y no 64×64 porque NVENC rechaza frames diminutos — falso negativo, [ver CHANGELOG C17]). Si falla, fallback CPU `libx264 -crf 18 -preset fast`.

## Conectividad y protocolos
- Se invoca por `subprocess`; nunca como librería. El stderr se captura para diagnosticar (lección: `stderr=DEVNULL` ocultaba el motivo real de cuelgues).

## Relacionado con
- [[arquitectura]]
- [Auto-sync (usa ffmpeg para extraer audio)](../especificaciones/TEC-SYN-01%20-%20Auto-sync%20por%20audio.md)
