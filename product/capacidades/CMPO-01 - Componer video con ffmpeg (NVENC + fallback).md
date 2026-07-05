---
tipo: capacidad
clave: CMPO-01
modulo: CMPO
dominio: Overlay y composición de video
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# CMPO-01 - Componer video con ffmpeg (NVENC + fallback)

## Módulo
- [[CMPO - Composición de video]]

## Propósito funcional
Superponer el HUD `.webm` sobre el video de cámara usando ffmpeg, con posición, escala y offset de sincronía configurables, usando NVENC si la GPU lo soporta y cayendo al codificador de CPU si no.

## Actor principal
Sistema (llamado con `fantasma compose`, desde el Paso 4 de la UI, o de forma encadenada desde el Paso 3 cuando está activo el auto-compose).

## Entradas funcionales
- Ruta al video de cámara.
- Ruta al HUD `.webm` (salida de [[OVL-01 - Generar overlay HUD con canal alfa]]).
- Posición del overlay (bottom-right, center, etc.), escala y offset en segundos.

## Salidas funcionales
- Video final compuesto en el directorio de salida.

## Reglas de negocio
- El filtro de escala usa el operador de multiplicación (`iw*factor:ih*factor`); escala 1.0 omite el paso de escala.
- El offset se aplica como `setpts=PTS+offset/TB`; offset 0.0 omite el setpts.
- Una posición desconocida cae en `bottom-right` como valor seguro por defecto.
- `_nvenc_available`: devuelve `True` solo si el probe a ffmpeg retorna exit code 0; cualquier error (exit code != 0 o excepción) devuelve `False` y la composición usa CPU.

## Criterios de aceptación
- Dado un overlay con escala 0.5, cuando se construye el filtro de ffmpeg, entonces incluye `scale=iw*0.500000:ih*0.500000`.
- Dado un offset de sincronía mayor que 0, cuando se construye el filtro, entonces incluye `setpts=PTS+<offset>/TB`; con offset 0 no incluye setpts.
- Dado que NVENC no está disponible (probe retorna exit code != 0 o lanza excepción), cuando se verifica la disponibilidad, entonces se devuelve `False` y la composición continúa con el codificador de CPU.
- Dado una posición desconocida, cuando se construye el filtro, entonces usa las coordenadas de `bottom-right`.

## Dependencias funcionales
- [[OVL-01 - Generar overlay HUD con canal alfa]]
- [[SYN-01 - Auto-detectar el offset por audio]]

## Fuera de alcance
- Generación del HUD (es [[OVL-01 - Generar overlay HUD con canal alfa]]).
- Formato ProRes (diferido post-v1.0 por bug de congelamiento en vueltas largas).

## Verificación
- Cubierta por `tests/viz/test_compose.py` (`test_build_filter_scale_has_multiply_operator`, `test_build_filter_setpts_only_with_offset`, `test_build_filter_unknown_position_falls_back_to_bottom_right`, `test_nvenc_available_false_on_nonzero`, `test_nvenc_available_false_on_exception`).

## Relacionado con
- [[Overlay y composición de video]]
- [TEC-OVL-01 — Overlay HUD y NVENC](../../engineering/especificaciones/TEC-OVL-01%20-%20Overlay%20HUD%20y%20NVENC.md)
