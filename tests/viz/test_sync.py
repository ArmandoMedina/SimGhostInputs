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


# --- _rank_candidates: detección de candidatos y ambigüedad (ADR 0008) -------
# Lógica pura sobre el array de correlación; no requiere video ni audio, solo scipy.

def _corr_with_peaks(n, peaks):
    """Array de correlación plano (1.0) con picos en {indice: valor}."""
    c = np.ones(n)
    for i, v in peaks.items():
        c[i] = v
    return c


def test_rank_single_clear_peak_not_ambiguous():
    pytest.importorskip("scipy")
    corr = _corr_with_peaks(100, {50: 20.0})       # un pico dominante = una vuelta
    lags = np.arange(100, dtype=float)
    cands, ambiguous = sync._rank_candidates(corr, lags, lap_dur=4.0)
    assert abs(cands[0]["offset"] - 50.0) < 1e-6
    assert not ambiguous


def test_rank_multi_lap_is_ambiguous():
    pytest.importorskip("scipy")
    # 4 picos casi iguales = carrera de varias vueltas parecidas
    corr = _corr_with_peaks(200, {30: 18.0, 80: 17.8, 130: 18.2, 180: 17.9})
    lags = np.arange(200, dtype=float)
    cands, ambiguous = sync._rank_candidates(corr, lags, lap_dur=4.0)
    assert len(cands) >= 2
    assert ambiguous


def test_rank_orders_by_quality_desc():
    pytest.importorskip("scipy")
    corr = _corr_with_peaks(200, {30: 10.0, 100: 20.0, 170: 15.0})
    lags = np.arange(200, dtype=float)
    cands, _ = sync._rank_candidates(corr, lags, lap_dur=4.0)
    assert abs(cands[0]["offset"] - 100.0) < 1e-6   # el de mayor correlación primero
    zs = [c["z"] for c in cands]
    assert zs == sorted(zs, reverse=True)


def test_rank_dominant_peak_not_ambiguous():
    pytest.importorskip("scipy")
    # un pico domina y el otro es mucho menor -> no ambiguo (no llega al ratio)
    corr = _corr_with_peaks(200, {50: 30.0, 150: 5.0})
    lags = np.arange(200, dtype=float)
    _, ambiguous = sync._rank_candidates(corr, lags, lap_dur=4.0)
    assert not ambiguous


def test_rank_mmss_format_from_offset():
    pytest.importorskip("scipy")
    corr = _corr_with_peaks(100, {75: 20.0})
    lags = np.zeros(100)
    lags[75] = 1656.0                               # 27:36 dentro del video
    cands, _ = sync._rank_candidates(corr, lags, lap_dur=4.0)
    assert cands[0]["mmss"] == "27:36"


def test_rank_flat_correlation_no_crash():
    pytest.importorskip("scipy")
    # audio sin señal de motor -> correlación plana, sin picos. No debe crashear
    # y debe devolver al menos un candidato (débil, no ambiguo).
    corr = np.ones(100)
    lags = np.arange(100, dtype=float)
    cands, ambiguous = sync._rank_candidates(corr, lags, lap_dur=4.0)
    assert len(cands) >= 1
    assert not ambiguous
