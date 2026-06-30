---
tipo: modulo
clave: SYN
dominio: Sincronía audio-video
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# SYN - Auto-sync por audio

## Dominio
- [[Sincronía audio-video]]

## Propósito del módulo
Detectar automáticamente el offset en segundos entre el inicio de la telemetría y el video de cámara, correlacionando la señal de rpm/velocidad con el audio del motor.

## Alcance
- Construcción de la señal de telemetría a partir de los canales `rpm` y `speed`.
- Lectura de audio WAV (16 bit) y detección de pausas por silencio.
- Ranking de candidatos de offset por calidad de correlación cruzada.
- Zona gris de confianza: candidatos entre 3σ y 6.5σ se aceptan con aviso; por debajo de 3σ se rechazan.

**No cubre:**
- Composición del video con el offset detectado (es [[CMPO - Composición de video]]).

## Regla funcional
Un candidato con z < 3σ se rechaza antes de llegar a la composición; entre 3σ y 6.5σ se acepta pero se emite un aviso de confianza moderada; sobre 6.5σ se acepta sin aviso.

## Secuencia funcional
- **Módulo anterior:** [[NRM - Normalización]]
- **Módulo siguiente:** [[CMPO - Composición de video]]

## Capacidades
- [[SYN-01 - Auto-detectar el offset por audio]]

## Dependencias funcionales
- [[NRM - Normalización]]

## Relacionado con
- [[Sincronía audio-video]]
- [TEC-SYN-01 — Auto-sync por audio](../../engineering/especificaciones/TEC-SYN-01%20-%20Auto-sync%20por%20audio.md)
