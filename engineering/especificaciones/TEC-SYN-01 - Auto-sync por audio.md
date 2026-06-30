---
tipo: especificacion_tecnica
clave: TEC-SYN-01
tecnologia: Python (extra opcional sync: scipy, numpy)
estado: vigente
---

# TEC-SYN-01 — Auto-sync por audio

## Contexto técnico
Detecta automáticamente el offset entre el video grabado y la telemetría, correlacionando la **energía de audio del motor** con una **señal sintética de RPM/velocidad**. Evita que el piloto cuente segundos a mano. `fantasma/viz/sync.py`. Decisión: [ADR 0001](../../docs/decisions/0001-sync-offset.md), enmienda [ADR 0008](../../docs/decisions/0008-sync-multivuelta-candidatos.md).

## Algoritmo
- **`_audio_energy(video)`** — extrae audio mono 8 kHz (ffmpeg), espectrograma (ventana 512, overlap 256), promedia la banda **150–500 Hz** (motor) e interpola a la rejilla de 2 Hz.
- **`_lap_signal(drv_lap)`** — señal normalizada RPM (peso 3.0) + speed (peso 1.5) a 2 Hz.
- **`sync_candidates`** — correlación cruzada normalizada (scipy `correlate`); `_rank_candidates` separa picos por ≥ 0.5× duración de vuelta y calcula `z = (pico − media)/std`. Devuelve `{offset, z, mmss}` rankeados.
- **`_detect_pause`** — bloques con energía < 5% de la media durante ≥3 s (≥6 muestras a 2 Hz).

## Umbrales de confianza
- Lag máximo de búsqueda ±300 s.
- `_MIN_SYNC_Z = 3.0σ` (mínimo aceptable), `_STRONG_SYNC_Z = 6.5σ` (robusto).
- **Zona gris** `[3.0, 6.5)σ`: se acepta pero **avisa** (enmienda 2026-06-28 al [ADR 0008](../../docs/decisions/0008-sync-multivuelta-candidatos.md)).
- Ambigüedad: ratio `z[1]/z[0] ≥ 0.85` con ≥2 candidatos fuertes → selección obligatoria del usuario.
- Rechaza si `z < 3.0σ` o hay pausa dentro de la ventana de la vuelta.

## Estrategia de mantenimiento
- **Dónde vive:** `fantasma/viz/sync.py`. La aritmética pura (offset, z-score) se testea sin ffmpeg (Tier 3); el render/audio real es QA manual.

## Vinculado con
- [[Sincronía audio-video]]
- [[ffmpeg]]
