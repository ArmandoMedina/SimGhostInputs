---
tipo: modulo
clave: OVL
dominio: Overlay y composición de video
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# OVL - Render del overlay

## Dominio
- [[Overlay y composición de video]]

## Propósito del módulo
Generar el HUD animado frame a frame con canal alfa como archivo `.webm`, listo para superponerse sobre el video de cámara sin fondo opaco.

## Alcance
- Render de cada frame del HUD con indicadores de velocidad, marcha, G-lat, delta, luces ABS y TC, y campo GASTO (desgaste acumulado de vuelta).
- Lógica de retención de luces ABS/TC: la luz permanece encendida durante una ventana de metros tras la última activación.
- Salida en formato VP9 con canal alfa (`.webm`).

**No cubre:**
- Composición del HUD sobre el video de cámara (es [[CMPO - Composición de video]]).
- Detección del offset de sincronía (es [[SYN - Auto-sync por audio]]).

## Regla funcional
El canal alfa permite superponer el HUD sobre cualquier video sin región de fondo negro; la lógica de retención de luces garantiza que las activaciones breves de ABS/TC sean visibles al ojo humano.

## Secuencia funcional
- **Módulo anterior:** [[CMP - Comparación]]
- **Módulo siguiente:** [[CMPO - Composición de video]]

## Capacidades
- [[OVL-01 - Generar overlay HUD con canal alfa]]

## Dependencias funcionales
- [[CMP - Comparación]]
- [[SYN - Auto-sync por audio]]

## Relacionado con
- [[Overlay y composición de video]]
- [TEC-OVL-01 — Overlay HUD y NVENC](../../engineering/especificaciones/TEC-OVL-01%20-%20Overlay%20HUD%20y%20NVENC.md)
