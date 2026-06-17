"""Tier 3 — aritmética pura de auto-sync (sin ffmpeg, sin scipy, sin video).

Solo se testean los helpers deterministas: la señal de telemetría, la detección
de pausa por silencio y la lectura de WAV. La correlación de audio real (auto_sync
completo) se valida en el QA manual con video real.
"""
import struct

import pytest

np = pytest.importorskip("numpy")
from fantasma.viz import sync  # noqa: E402
from fantasma.core.lap import Lap  # noqa: E402

from conftest import make_lap  # noqa: E402


# --- _lap_signal -----------------------------------------------------------

def test_lap_signal_combines_rpm_and_speed():
    lap = make_lap()  # tiene time, rpm, speed
    sig = sync._lap_signal(lap)
    assert len(sig) > 0
    assert np.all(np.isfinite(sig))
    # combinación de señales normalizadas (media 0) -> media ~0
    assert abs(float(np.mean(sig))) < 1e-9


def test_lap_signal_requires_time_channel():
    lap = Lap(channels={"rpm": [5000.0, 6000.0], "speed": [100.0, 120.0]})
    with pytest.raises(RuntimeError):
        sync._lap_signal(lap)


def test_lap_signal_requires_rpm_or_speed():
    lap = Lap(channels={"time": [0.0, 1.0, 2.0]})  # ni rpm ni speed
    with pytest.raises(RuntimeError):
        sync._lap_signal(lap)


# --- _detect_pause ---------------------------------------------------------

def test_detect_pause_finds_silence_gap():
    # 100 s de energía a 2 Hz; silencio de 5 s a partir del segundo 20
    ae = np.ones(200)
    ae[40:50] = 0.0
    t = sync._detect_pause(ae, start_sec=0.0, end_sec=100.0)
    assert t is not None
    assert abs(t - 20.0) < 1.0


def test_detect_pause_none_when_continuous():
    ae = np.ones(200)
    assert sync._detect_pause(ae, start_sec=0.0, end_sec=100.0) is None


# --- _read_wav_mono --------------------------------------------------------

def test_read_wav_mono_16bit(tmp_path):
    header = bytearray(44)
    struct.pack_into("<H", header, 34, 16)  # bits/muestra = 16
    samples = np.array([0, 16384, -16384], dtype=np.int16)
    p = tmp_path / "tone.wav"
    p.write_bytes(bytes(header) + samples.tobytes())
    out = sync._read_wav_mono(str(p))
    assert len(out) == 3
    assert abs(out[0] - 0.0) < 1e-6
    assert abs(out[1] - 0.5) < 1e-4
    assert abs(out[2] + 0.5) < 1e-4
