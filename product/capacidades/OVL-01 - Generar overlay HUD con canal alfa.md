---
tipo: capacidad
clave: OVL-01
modulo: OVL
dominio: Overlay y composición de video
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# OVL-01 - Generar overlay HUD con canal alfa

## Módulo
- [[OVL - Render del overlay]]

## Propósito funcional
Renderizar el HUD animado frame a frame como archivo `.webm` con canal alfa, con indicadores de velocidad, marcha, delta, G-lat, luces ABS y TC (con retención), y campo GASTO de desgaste acumulado.

## Actor principal
Sistema (llamado con `fantasma overlay` o desde el Paso 3 de la UI).

## Entradas funcionales
- Trace del análisis (salida de `compare()`).
- FPS del video objetivo.
- Parámetros de estilo del HUD (posición, tamaño, colores).

## Salidas funcionales
- Archivo `.webm` con canal alfa listo para composición.

## Reglas de negocio
- Las luces ABS y TC se encienden cuando el flag estuvo activo en los últimos N metros (ventana de retención configurable); se apagan solo cuando el cursor supera esa ventana.
- La luz permanece apagada si el flag nunca estuvo activo o si el canal de flag es `None`.
- El cursor que supera el final del array de flags se acota al último índice sin error.

## Criterios de aceptación
- Dado que un flag (ABS o TC) no ha estado activo en los últimos N metros de retención, cuando se consulta el estado de la luz en ese punto, entonces la luz está apagada.
- Dado que un flag estuvo activo dentro de la ventana de retención, cuando se consulta el estado antes de que expire la retención, entonces la luz permanece encendida.
- Dado que el cursor supera el final del array de flags, cuando se consulta el estado de la luz, entonces se acota al último índice y no se lanza excepción.

## Dependencias funcionales
- [[CMP-01 - Comparar dos vueltas por distancia]]
- [[SYN-01 - Auto-detectar el offset por audio]]

## Fuera de alcance
- Composición del HUD sobre el video de cámara (es [[CMPO-01 - Componer video con ffmpeg (NVENC + fallback)]]).
- Definición exacta de los indicadores del HUD (dueño: `docs/hud-reference.md`).

## Verificación
- Cubierta por `tests/viz/test_overlay.py` (`test_flag_recent_grid_none_is_off`, `test_flag_recent_grid_on_at_cursor`, `test_flag_recent_grid_holds_within_window`, `test_flag_recent_grid_off_beyond_hold`, `test_flag_recent_grid_clamps_index_past_end`).

## Relacionado con
- [[Overlay y composición de video]]
- [TEC-OVL-01 — Overlay HUD y NVENC](../../engineering/especificaciones/TEC-OVL-01%20-%20Overlay%20HUD%20y%20NVENC.md)
