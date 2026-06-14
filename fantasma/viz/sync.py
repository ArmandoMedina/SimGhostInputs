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

_ENGINE_LO  = 150   # Hz — limite inferior de la banda del motor
_ENGINE_HI  = 500   # Hz — limite superior
_SR         = 8000  # Hz — frecuencia de muestreo del audio extraido
_CORR_HZ    = 2     # Hz — resolucion de la correlacion (0.5 s/muestra)
_SEARCH_SEC = 300   # s  — lag maximo buscado en cada direccion


def _ffmpeg_path():
    f = shutil.which("ffmpeg")
    if not f:
        raise RuntimeError(
            "ffmpeg no encontrado en PATH — instala con: winget install Gyan.FFmpeg"
        )
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
            [ff, "-y", "-i", video_path,
             "-ac", "1", "-ar", str(_SR), "-vn", "-f", "wav", tmp.name],
            check=True, capture_output=True,
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
    t -= t[0]   # relativo al inicio de la vuelta (split_laps ya lo garantiza)
    t_uni = np.arange(0, t[-1], 1.0 / _CORR_HZ)

    parts, weights = [], []

    rpm = ch.get("rpm")
    if rpm is not None:
        r = np.interp(t_uni, t, np.asarray(rpm, dtype=float))
        parts.append((r - r.mean()) / (r.std() + 1e-9))
        weights.append(3.0)   # RPM es la senal mas discriminativa

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


_MIN_SYNC_Z      = 3.0   # sigma minimo para considerar la correlacion valida
_PAUSE_SILENCE_S = 3.0   # segundos de silencio consecutivos para detectar pausa
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
    ends   = np.where(diff == -1)[0]
    for s, e in zip(starts, ends):
        if (e - s) >= min_samples:
            return start_sec + s / _CORR_HZ
    return None


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
    try:
        import scipy  # noqa: F401
    except ImportError:
        raise ImportError(
            "scipy es necesario para auto-sync: "
            "pip install 'fantasma-inputs[sync]'"
        )

    from scipy.signal import correlate as _corr

    ae   = _audio_energy(video_path)
    tele = _lap_signal(drv_lap)

    _MIN_AUDIO_SEC = 30
    audio_dur = len(ae) / _CORR_HZ
    if audio_dur < _MIN_AUDIO_SEC:
        raise RuntimeError(
            "auto_sync: video demasiado corto (%.0f s, mínimo %d s). "
            "El video debe contener la vuelta completa para que la correlación "
            "de audio tenga suficientes muestras." % (audio_dur, _MIN_AUDIO_SEC)
        )

    ae_n = (ae - ae.mean()) / (ae.std() + 1e-9)

    corr = _corr(ae_n, tele, mode="full")
    lags = (np.arange(len(corr)) - (len(tele) - 1)) / _CORR_HZ
    mask = np.abs(lags) <= _SEARCH_SEC
    corr_w = corr[mask]
    peak_idx = np.argmax(corr_w)
    peak_val = corr_w[peak_idx]
    z = (peak_val - corr_w.mean()) / (corr_w.std() + 1e-9)
    if z < _MIN_SYNC_Z:
        raise RuntimeError(
            "auto_sync: correlacion insuficiente (z=%.1f, mínimo %.1f σ). "
            "El video no parece corresponder a la vuelta telemetrada, o el audio "
            "no contiene señal de motor reconocible en la banda 150-500 Hz." % (z, _MIN_SYNC_Z)
        )

    offset = float(lags[mask][peak_idx])

    # Verificar que no haya pausas dentro de la ventana de la vuelta
    lap_dur = float(getattr(drv_lap, "laptime", 0))
    if lap_dur > 0:
        pause_t = _detect_pause(ae, offset, offset + lap_dur)
        if pause_t is not None:
            m, s = int(pause_t) // 60, int(pause_t) % 60
            raise RuntimeError(
                "auto_sync: pausa detectada en el audio del video en %d:%02d "
                "(silencio > %.0f s dentro de la vuelta). "
                "El video debe grabarse sin pausas para que la sincronización sea válida." % (
                    m, s, _PAUSE_SILENCE_S)
            )

    return offset, z
