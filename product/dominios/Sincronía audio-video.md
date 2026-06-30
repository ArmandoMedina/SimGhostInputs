---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Sincronía audio-video

## Producto
- Fantasma

## Propósito
Detectar **automáticamente el offset** entre el video grabado y la telemetría, correlacionando el audio del motor con una señal de RPM/velocidad, para que el piloto no tenga que alinear video y datos a mano.

## Alcance
- Extracción de energía de audio (banda del motor) y señal sintética de telemetría.
- Correlación cruzada, ranking de candidatos y confianza (z-score, zona gris).
- Selección obligatoria del usuario cuando hay candidatos ambiguos; rechazo si la confianza es baja o hay pausa.

**Fuera de alcance:** el render del HUD (es [[Overlay y composición de video]]); sincronía manual fina (el usuario puede ajustar el offset propuesto).

## Módulos
- SYN — Auto-sync por audio

## Relacionado con
- [[Overlay y composición de video]]
- [TEC-SYN-01 — Auto-sync por audio](../../engineering/especificaciones/TEC-SYN-01%20-%20Auto-sync%20por%20audio.md)
- [ADR 0008 — Auto-sync multi-vuelta](../../docs/decisions/0008-sync-multivuelta-candidatos.md)
