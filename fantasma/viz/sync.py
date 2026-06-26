"""
Auto-deteccion del offset temporal entre video de grabacion y overlay de telemetria.

Metodo:
    Correlacion cruzada entre la energia espectral del audio del video
    (banda de frecuencias del motor, 150-500 Hz) y la senal combinada
    de RPM + velocidad de la telemetria, resampleada a 2 Hz.

    El pico de correlacion indica cuantos segundos pasan desde el inicio
    del video hasta que comienza la vuelta telemetrada.

Uso:
    from fantasma.viz.sync import auto_sync
    offset, z = auto_sync("grabacion.mp4", drv_lap)
    # offset en segundos desde inicio del video hasta inicio de la vuelta
    # z es la calidad de la correlacion (sigma); mayor = mejor, minimo aceptable 3.0

Requiere:
    scipy (extra [sync]): pip install 'fantasma-inputs[sync]'
    ffmpeg en PATH
"""

import os
import shutil
import struct
import subprocess
import tempfile

import numpy as np

_ENGINE_LO = 150  # Hz — limite inferior de la banda del motor
_ENGINE_HI = 500  # Hz — limite superior
_SR = 8000  # Hz — frecuencia de muestreo del audio extraido
_CORR_HZ = 2  # Hz — resolucion de la correlacion (0.5 s/muestra)
_SEARCH_SEC = 300  # s  — lag maximo buscado en cada direccion


def _ffmpeg_path():
    f = shutil.which("ffmpeg")
    if not f:
        raise RuntimeError("ffmpeg no encontrado en PATH — instala con: winget install Gyan.FFmpeg")
    return f


def _read_wav_mono(path):
    """Lee un WAV mono PCM y devuelve array float32 normalizado [-1, 1]."""
    with open(path, "rb") as f:
        header = f.read(44)
        bits = struct.unpack_from("<H", header, 34)[0]
        raw = f.read()
    if bits == 16:
        return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    if bits == 8:
        return (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    raise RuntimeError("Formato WAV no soportado: %d bits/muestra" % bits)


def _audio_energy(video_path):
    """Energia espectral en la banda del motor, resampleada a _CORR_HZ Hz."""
    from scipy.signal import spectrogram as _sg

    ff = _ffmpeg_path()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.close()
    try:
        subprocess.run(
            [ff, "-y", "-i", video_path, "-ac", "1", "-ar", str(_SR), "-vn", "-f", "wav", tmp.name],
            check=True,
            capture_output=True,
        )
        audio = _read_wav_mono(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass

    freqs, times, Sxx = _sg(audio, fs=_SR, nperseg=512, noverlap=256)
    band = (freqs >= _ENGINE_LO) & (freqs <= _ENGINE_HI)
    energy = Sxx[band].mean(axis=0)

    dur = len(audio) / _SR
    t_out = np.arange(0, dur, 1.0 / _CORR_HZ)
    return np.interp(t_out, times, energy)


def _lap_signal(drv_lap):
    """Senal combinada RPM + velocidad a _CORR_HZ Hz (normalizada, media 0)."""
    ch = drv_lap.channels

    t_raw = ch.get("time")
    if t_raw is None:
        raise RuntimeError("Canal 'time' no encontrado en la telemetria")

    t = np.asarray(t_raw, dtype=float)
    t -= t[0]  # relativo al inicio de la vuelta (split_laps ya lo garantiza)
    t_uni = np.arange(0, t[-1], 1.0 / _CORR_HZ)

    parts, weights = [], []

    rpm = ch.get("rpm")
    if rpm is not None:
        r = np.interp(t_uni, t, np.asarray(rpm, dtype=float))
        parts.append((r - r.mean()) / (r.std() + 1e-9))
        weights.append(3.0)  # RPM es la senal mas discriminativa

    spd = ch.get("speed")
    if spd is not None:
        s = np.interp(t_uni, t, np.asarray(spd, dtype=float))
        parts.append((s - s.mean()) / (s.std() + 1e-9))
        weights.append(1.5)

    if not parts:
        raise RuntimeError(
            "No se encontraron canales 'rpm' ni 'speed' en la telemetria. "
            "Usa --map para mapear las columnas correctas."
        )

    w = np.array(weights) / sum(weights)
    return sum(wi * pi for wi, pi in zip(w, parts))


_MIN_SYNC_Z = 3.0  # sigma minimo para considerar la correlacion valida
_PAUSE_SILENCE_S = 3.0  # segundos de silencio consecutivos para detectar pausa
_PAUSE_THRESHOLD = 0.05  # fraccion de la energia media por debajo de la cual = silencio


def _detect_pause(ae, start_sec, end_sec):
    """Busca silencio prolongado dentro de la ventana [start_sec, end_sec].

    Devuelve el timestamp (en segundos desde el inicio del video) del primer
    silencio que supere _PAUSE_SILENCE_S, o None si no hay pausa.
    """
    i0 = max(0, int(start_sec * _CORR_HZ))
    i1 = min(len(ae), int(end_sec * _CORR_HZ))
    window = ae[i0:i1]
    if len(window) == 0:
        return None

    threshold = window.mean() * _PAUSE_THRESHOLD
    silence = (window < threshold).astype(int)
    min_samples = int(_PAUSE_SILENCE_S * _CORR_HZ)

    padded = np.concatenate([[0], silence, [0]])
    diff = np.diff(padded)
    starts = np.where(diff == 1)[0]
    ends = np.where(diff == -1)[0]
    for s, e in zip(starts, ends):
        if (e - s) >= min_samples:
            return start_sec + s / _CORR_HZ
    return None


def _rank_candidates(corr_w, lags_w, lap_dur, max_candidates=6, ambiguous_ratio=0.85):
    """Logica pura: dado el array de correlacion recortado y sus lags, detecta los
    picos (uno por vuelta en un video multi-vuelta), los rankea por calidad (z) y
    decide si el resultado es ambiguo. Separado de la extraccion de audio para poder
    testearlo sin ffmpeg ni video. Ver ADR 0008.

    Devuelve (candidates, ambiguous):
      candidates: lista de dicts {offset, z, mmss} ordenada por z desc.
      ambiguous : True si los dos mejores candidatos fuertes estan tan cerca en
                  calidad que no se puede decidir automaticamente.
    """
    from scipy.signal import find_peaks

    mean = float(corr_w.mean())
    std = float(corr_w.std()) + 1e-9
    # picos separados por ~media vuelta: una vuelta = un pico
    min_dist = max(1, int(lap_dur * 0.5 * _CORR_HZ))
    peaks, _ = find_peaks(corr_w, distance=min_dist)
    if len(peaks) == 0:
        peaks = np.array([int(np.argmax(corr_w))])
    peaks = peaks[np.argsort(corr_w[peaks])[::-1]][:max_candidates]
    cands = []
    for p in peaks:
        z = (float(corr_w[p]) - mean) / std
        off = float(lags_w[p])
        mm = max(0, int(round(off)))
        cands.append({"offset": off, "z": z, "mmss": "%d:%02d" % (mm // 60, mm % 60)})
    strong = [c for c in cands if c["z"] >= _MIN_SYNC_Z]
    ambiguous = len(strong) >= 2 and (strong[1]["z"] / strong[0]["z"] >= ambiguous_ratio)
    return cands, ambiguous


def sync_candidates(video_path, drv_lap, max_candidates=6):
    """Candidatos de offset entre video y telemetria, buscando en TODO el video
    (no solo +/-300 s). Para videos de varias vueltas devuelve un candidato por
    vuelta, rankeados por calidad. Ver ADR 0008.

    Devuelve dict {candidates, ambiguous, audio_dur, _ae}; '_ae' es interno
    (energia de audio) para validar pausas con validate_offset sin re-extraer.
    """
    try:
        import scipy  # noqa: F401
    except ImportError:
        raise ImportError("scipy es necesario para auto-sync: pip install 'fantasma-inputs[sync]'")
    from scipy.signal import correlate as _corr

    ae = _audio_energy(video_path)
    tele = _lap_signal(drv_lap)
    audio_dur = len(ae) / _CORR_HZ
    _MIN_AUDIO_SEC = 30
    if audio_dur < _MIN_AUDIO_SEC:
        raise RuntimeError(
            "auto_sync: video demasiado corto (%.0f s, mínimo %d s). "
            "El video debe contener la vuelta completa para que la correlación "
            "de audio tenga suficientes muestras." % (audio_dur, _MIN_AUDIO_SEC)
        )

    ae_n = (ae - ae.mean()) / (ae.std() + 1e-9)
    corr = _corr(ae_n, tele, mode="full")
    lags = (np.arange(len(corr)) - (len(tele) - 1)) / _CORR_HZ

    # Rango valido: la vuelta debe caber en el audio. Cubre TODO el video (no solo
    # +/-300 s), con un margen _SEARCH_SEC a cada lado.
    lap_dur = float(getattr(drv_lap, "laptime", 0)) or 1.0
    lo = -_SEARCH_SEC
    hi = audio_dur - lap_dur + _SEARCH_SEC
    mask = (lags >= lo) & (lags <= hi)
    if not mask.any():
        mask = np.abs(lags) <= _SEARCH_SEC

    cands, ambiguous = _rank_candidates(corr[mask], lags[mask], lap_dur, max_candidates)
    return {"candidates": cands, "ambiguous": ambiguous, "audio_dur": audio_dur, "_ae": ae}


def validate_offset(result, offset, drv_lap):
    """Detecta una pausa en el audio dentro de la vuelta que empieza en `offset`.
    Devuelve el timestamp de la pausa (s) o None. Reusa result['_ae'] (no re-extrae).
    """
    ae = result.get("_ae")
    lap_dur = float(getattr(drv_lap, "laptime", 0))
    if ae is None or lap_dur <= 0:
        return None
    return _detect_pause(ae, offset, offset + lap_dur)


def auto_sync(video_path, drv_lap):
    """Detecta el offset temporal entre video y telemetria via correlacion de audio.

    Extrae la energia del motor del audio del video (banda 150-500 Hz) y la
    correlaciona contra la senal combinada de RPM + velocidad de la telemetria.
    El pico de correlacion indica cuantos segundos pasan desde el inicio del
    video hasta que comienza la vuelta telemetrada.

    Args:
        video_path: ruta al video de grabacion (.mp4, .mov, .mkv...)
        drv_lap:    Lap del piloto con canales canonicos 'time', 'rpm', 'speed'

    Returns:
        (offset, z_score): offset en segundos desde el inicio del video hasta
            el inicio de la vuelta; z_score es la calidad de la correlacion
            (mayor = mejor, minimo aceptable _MIN_SYNC_Z).

    Raises:
        ImportError:  si scipy no esta instalado
        RuntimeError: si faltan canales de telemetria, ffmpeg no esta en PATH,
                      video demasiado corto, correlacion insuficiente (z < MIN),
                      o se detecta una pausa en el audio durante la vuelta
    """
    result = sync_candidates(video_path, drv_lap)
    cands = result["candidates"]
    if not cands or cands[0]["z"] < _MIN_SYNC_Z:
        z0 = cands[0]["z"] if cands else 0.0
        raise RuntimeError(
            "auto_sync: correlacion insuficiente (z=%.1f, mínimo %.1f σ). "
            "El video no parece corresponder a la vuelta telemetrada, o el audio "
            "no contiene señal de motor reconocible en la banda 150-500 Hz." % (z0, _MIN_SYNC_Z)
        )

    offset, z = cands[0]["offset"], cands[0]["z"]

    # Verificar que no haya pausas dentro de la ventana de la vuelta
    pause_t = validate_offset(result, offset, drv_lap)
    if pause_t is not None:
        m, s = int(pause_t) // 60, int(pause_t) % 60
        raise RuntimeError(
            "auto_sync: pausa detectada en el audio del video en %d:%02d "
            "(silencio > %.0f s dentro de la vuelta). "
            "El video debe grabarse sin pausas para que la sincronización sea válida."
            % (m, s, _PAUSE_SILENCE_S)
        )

    return offset, z
