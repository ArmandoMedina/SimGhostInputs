---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Overlay y composición de video

## Producto
- Fantasma

## Propósito
Generar el **HUD animado con canal alfa** (inputs del piloto y la referencia en simultáneo) y componerlo sobre la grabación del sim, para que la comparación sea visual e inmediata en el contexto real de la vuelta.

## Alcance
- Render del HUD `.webm`/`.mov` (canal alfa) con render paralelo por CPU.
- Composición con ffmpeg, NVENC automático si hay GPU NVIDIA (con fallback a CPU).
- Anatomía y código de color del HUD (dueño: [`hud-reference.md`](../../docs/hud-reference.md)).

**Fuera de alcance:** la sincronía con el video (es [[Sincronía audio-video]]); edición de video; uso de GPU durante la sesión (solo post-sesión).

## Módulos
- OVL — Render del overlay (HUD)
- CMPO — Composición con ffmpeg

## Relacionado con
- [[Sincronía audio-video]]
- [TEC-OVL-01 — Overlay HUD y NVENC](../../engineering/especificaciones/TEC-OVL-01%20-%20Overlay%20HUD%20y%20NVENC.md)
- [[ffmpeg]]
