---
tipo: modulo
clave: CMPO
dominio: Overlay y composición de video
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CMPO - Composición de video

## Dominio
- [[Overlay y composición de video]]

## Propósito del módulo
Componer el HUD generado sobre el video de cámara usando ffmpeg, con aceleración de hardware NVENC si hay GPU NVIDIA disponible y fallback automático a codificación por CPU.

## Alcance
- Construcción del filtro de ffmpeg: posición del overlay (bottom-right, center, etc.), escala y offset temporal.
- Detección de disponibilidad de NVENC mediante probe; fallback a CPU sin error.
- Aplicación del offset de sincronía entre HUD y video.

**No cubre:**
- Generación del HUD (es [[OVL - Render del overlay]]).
- Detección del offset de sincronía (es [[SYN - Auto-sync por audio]]).

## Regla funcional
Si NVENC no está disponible o el probe lanza excepción, la composición continúa con el codificador de CPU sin que el usuario vea un error; la posición desconocida cae en `bottom-right` como valor seguro.

## Secuencia funcional
- **Módulo anterior:** [[OVL - Render del overlay]]
- **Módulo siguiente:** No aplica

## Capacidades
- [[CMPO-01 - Componer video con ffmpeg (NVENC + fallback)]]

## Dependencias funcionales
- [[OVL - Render del overlay]]
- [[SYN - Auto-sync por audio]]

## Relacionado con
- [[Overlay y composición de video]]
- [TEC-OVL-01 — Overlay HUD y NVENC](../../engineering/especificaciones/TEC-OVL-01%20-%20Overlay%20HUD%20y%20NVENC.md)
