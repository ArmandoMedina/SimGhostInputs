---
tipo: capacidad
clave: SYN-01
modulo: SYN
dominio: Sincronía audio-video
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# SYN-01 - Auto-detectar el offset por audio

## Módulo
- [[SYN - Auto-sync por audio]]

## Propósito funcional
Detectar automáticamente el offset en segundos entre el inicio de la telemetría y el video de cámara, correlacionando la señal de rpm/velocidad con el audio del motor extraído del video.

## Actor principal
Sistema (llamado con `fantasma overlay` o desde el flujo de la UI antes de componer).

## Entradas funcionales
- Objeto `Lap` con canales `time` y `rpm` y/o `speed`.
- Archivo WAV del audio del motor (16 bit, mono).

## Salidas funcionales
- Offset en segundos (y en formato mm:ss) del candidato de mayor calidad.
- Lista de candidatos ordenados por calidad descendente.
- Flag de ambigüedad si varios candidatos tienen correlación similar.
- Aviso de zona gris si el candidato aceptado tiene confianza moderada (3σ a 6.5σ).

## Reglas de negocio
- La señal de telemetría combina `rpm` y `speed` normalizadas; sin canal `time` se lanza `RuntimeError`; sin `rpm` ni `speed` también.
- La señal resultante tiene media ~0 y está libre de NaN.
- Un candidato con z < 3σ se rechaza antes de llegar a composición.
- Entre 3σ y 6.5σ se acepta con aviso de confianza moderada; sobre 6.5σ se acepta sin aviso.
- Varios picos de correlación de amplitud similar producen resultado ambiguo.
- Correlación plana (audio sin señal de motor) no crashea y devuelve al menos un candidato débil.

## Criterios de aceptación
- Dado una vuelta con canales `time` y `rpm`/`speed`, cuando se genera la señal de telemetría, entonces es una señal con media ~0 y sin valores NaN o infinitos.
- Dado una correlación de audio con un único pico dominante, cuando se ranquean los candidatos, entonces hay un único candidato marcado como no ambiguo.
- Dado múltiples picos de correlación con amplitudes similares (sesión de varias vueltas parecidas), cuando se ranquean los candidatos, entonces el resultado se marca como ambiguo.
- Dado un candidato con z entre 3σ y 6.5σ (zona gris de confianza), cuando se evalúa la calidad del match, entonces se devuelve un aviso que incluye el valor de z y la palabra "moderada".

## Dependencias funcionales
- [[NRM-03 - Remuestrear por distancia]]

## Fuera de alcance
- Composición del video con el offset (es [[CMPO-01 - Componer video con ffmpeg (NVENC + fallback)]]).
- Validación manual del offset por el usuario.

## Verificación
- Cubierta por `tests/viz/test_sync.py` (`test_lap_signal_combines_rpm_and_speed`, `test_lap_signal_requires_time_channel`, `test_lap_signal_requires_rpm_or_speed`, `test_rank_single_clear_peak_not_ambiguous`, `test_rank_multi_lap_is_ambiguous`, `test_gray_zone_warns_on_wrong_session`, `test_gray_zone_no_warning_on_strong_match`).

## Relacionado con
- [[Sincronía audio-video]]
- [TEC-SYN-01 — Auto-sync por audio](../../engineering/especificaciones/TEC-SYN-01%20-%20Auto-sync%20por%20audio.md)
