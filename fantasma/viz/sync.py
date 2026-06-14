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
    offset = auto_sync("grabacion.mp4", drv_lap)
    # -> offset en segundos desde inicio del video hasta inicio de la vuelta

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
        offset (float): segundos desde el inicio del video hasta el inicio
            de la vuelta telemetrada. Pasa este valor como ``--offset`` (CLI)
            o como "Retraso del HUD" en la UI al componer el video final.

    Raises:
        ImportError:  si scipy no esta instalado
        RuntimeError: si faltan canales de telemetria, ffmpeg no esta en PATH,
                      o la correlacion audio/tele es insuficiente (z < 3.0 sigma) —
                      indica que el video no corresponde a la vuelta telemetrada
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
    # lag > 0: vuelta empieza lag segundos DESPUES del inicio del video
    # lag < 0: vuelta empieza |lag| segundos ANTES del inicio del video
    lags = (np.arange(len(corr)) - (len(tele) - 1)) / _CORR_HZ
    mask = np.abs(lags) <= _SEARCH_SEC
    corr_w = corr[mask]
    peak_idx = np.argmax(corr_w)
    peak_val = corr_w[peak_idx]
    z = (peak_val - corr_w.mean()) / (corr_w.std() + 1e-9)
    if z < 3.0:
        raise RuntimeError(
            "auto_sync: pico de correlacion insuficiente (z=%.1f, minimo 3.0). "
            "El video no parece corresponder a la vuelta telemetrada, o el audio "
            "no contiene senal de motor reconocible en la banda 150-500 Hz." % z
        )
    offset = float(lags[mask][peak_idx])
    return offset
