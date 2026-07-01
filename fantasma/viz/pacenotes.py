"""Genera un pack de Pace Notes para CrewChief desde el analisis de SimGhostInputs."""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

DEFAULT_MILESTONES = ["brake", "apex", "gas"]
DEFAULT_FREQS = {"brake": 880, "apex": 440, "gas": 220, "gas_100": 180}
MILESTONE_ALIASES = {
    "brake": ["brake", "brake_start"],
    "apex": ["apex"],
    "gas": ["gas", "full_throttle"],
    "gas_100": ["gas_100", "full_throttle"],
    "turn_in": ["turn_in"],
}
MILESTONE_LABELS = {
    "brake": "punto de frenada",
    "apex": "apex",
    "gas": "punto de gas",
    "gas_100": "gas completo",
    "turn_in": "turn-in",
}


def generate_tone(freq_hz, duration_s, volume=0.8, sample_rate=24000) -> bytes:
    import numpy as np

    t = np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)
    fade = min(int(sample_rate * 0.01), len(t) // 2)
    envelope = np.ones(len(t))
    if fade > 0:
        envelope[:fade] = np.linspace(0, 1, fade)
        envelope[-fade:] = np.linspace(1, 0, fade)
    samples = (np.sin(2 * np.pi * freq_hz * t) * envelope * volume * 32767).astype(np.int16)
    return _make_wav_bytes(samples, sample_rate=sample_rate)


def _make_wav_bytes(samples_int16, sample_rate=24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples_int16.tobytes())
    return buf.getvalue()


def build_tone_pack(
    rows,
    corners,
    outdir,
    top=5,
    milestones=None,
    freqs=None,
    duration=0.12,
    volume=0.8,
) -> dict:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    milestones = milestones or DEFAULT_MILESTONES
    freqs = {**DEFAULT_FREQS, **(freqs or {})}
    entries = []
    files = []

    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        name = _corner_name(row, corner)
        for milestone in milestones:
            m = _milestone(corner, milestone) or _milestone(row, milestone)
            if not m or m.get("d") is None:
                continue
            distance = int(round(_as_float(m["d"])))
            filename = "%d_0.wav" % distance
            path = out / filename
            path.write_bytes(generate_tone(freqs.get(milestone, 440), duration, volume=volume))
            files.append(str(path))
            entries.append(_metadata_entry(name, milestone, distance, filename))

    metadata_path = _write_metadata(out, entries)
    files.append(str(metadata_path))
    return {"outdir": str(out), "files": files, "entries": len(entries)}


def build_voice_pack(rows, corners, outdir, top=5, lang="es-MX") -> dict:
    if importlib.util.find_spec("edge_tts") is None:
        raise RuntimeError("edge-tts no instalado: ejecuta pip install 'fantasma-inputs[voice]'")

    import asyncio

    import edge_tts

    ffmpeg = shutil.which("ffmpeg")
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    files = []
    voice = _voice_for_lang(lang)

    if not ffmpeg:
        print("aviso: ffmpeg no disponible; se omiten las pace notes de voz", file=sys.stderr)
        metadata_path = _write_metadata(out, entries)
        return {"outdir": str(out), "files": [str(metadata_path)], "entries": 0}

    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        brake = _milestone(corner, "brake") or _milestone(row, "brake")
        if not brake or brake.get("d") is None:
            continue
        distance = max(0, int(round(_as_float(brake["d"]) - 200)))
        name = _corner_name(row, corner)
        filename = "%d_0.wav" % distance
        text = _voice_text(row, name)
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = os.path.join(tmp, "note.mp3")
            wav = out / filename
            asyncio.run(edge_tts.Communicate(text, voice=voice).save(mp3))
            try:
                subprocess.run(
                    [
                        ffmpeg,
                        "-y",
                        "-i",
                        mp3,
                        "-ar",
                        "24000",
                        "-ac",
                        "1",
                        "-sample_fmt",
                        "s16",
                        str(wav),
                    ],
                    check=True,
                    capture_output=True,
                )
            except (OSError, subprocess.CalledProcessError) as e:
                print("aviso: no se pudo convertir voz para %s: %s" % (name, e), file=sys.stderr)
                continue
        files.append(str(out / filename))
        entries.append(_metadata_entry(name, "voice", distance, filename))

    metadata_path = _write_metadata(out, entries)
    files.append(str(metadata_path))
    return {"outdir": str(out), "files": files, "entries": len(entries)}


def build_pack(rows, corners, outdir, mode="tones", top=5, **kwargs) -> dict:
    if mode == "tones":
        tone_kwargs = {k: v for k, v in kwargs.items() if k != "lang"}
        return build_tone_pack(rows, corners, outdir, top=top, **tone_kwargs)
    if mode == "voice":
        return build_voice_pack(rows, corners, outdir, top=top, lang=kwargs.get("lang", "es-MX"))
    if mode != "both":
        raise ValueError("modo invalido: %s" % mode)

    tone_kwargs = {k: v for k, v in kwargs.items() if k != "lang"}
    tones = build_tone_pack(rows, corners, outdir, top=top, **tone_kwargs)
    tone_entries = _read_entries(Path(outdir) / "metadata.json")
    voice = build_voice_pack(rows, corners, outdir, top=top, lang=kwargs.get("lang", "es-MX"))
    voice_entries = _read_entries(Path(outdir) / "metadata.json")
    _write_metadata(Path(outdir), tone_entries + voice_entries)
    files = list(dict.fromkeys(tones["files"] + voice["files"]))
    return {
        "outdir": str(Path(outdir)),
        "files": files,
        "entries": len(tone_entries) + len(voice_entries),
    }


def _top_rows(rows, top):
    losses = [r for r in rows if _as_float(r.get("time_lost", 0)) > 0]
    losses.sort(key=lambda r: _as_float(r.get("time_lost", 0)), reverse=True)
    return losses[:top]


def _find_corner(row, corners):
    by_key = {}
    for corner in corners:
        for key in (corner.get("id"), corner.get("name")):
            if key:
                by_key[str(key)] = corner
    for key in (row.get("id"), row.get("name")):
        if key and str(key) in by_key:
            return by_key[str(key)]
    row_apex = row.get("apex_d")
    if row_apex is not None:
        row_apex = _as_float(row_apex)
        for corner in corners:
            apex = _milestone(corner, "apex")
            if apex and apex.get("d") is not None and abs(_as_float(apex["d"]) - row_apex) <= 1:
                return corner
    return None


def _milestone(corner, name):
    milestones = corner.get("milestones") or {}
    for key in MILESTONE_ALIASES.get(name, [name]):
        if key in milestones:
            return milestones[key]
    return None


def _metadata_entry(name, milestone, distance, filename):
    label = MILESTONE_LABELS.get(milestone, milestone)
    return {
        "description": "%s — %s" % (name, label),
        "distanceRoundTrack": distance,
        "lapNumber": None,
        "minimumSpeed": None,
        "maximumSpeed": None,
        "minimumYawAngle": None,
        "maximumYawAngle": None,
        "recordingNames": [filename],
        "fileNames": [filename],
        "playAllInOrder": False,
    }


def _write_metadata(outdir, entries):
    metadata = {
        "description": "Generado por SimGhostInputs",
        "gameEnumName": "AMS2",
        "carClassName": None,
        "trackName": None,
        "entries": entries,
    }
    path = outdir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _read_entries(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("entries", [])


def _corner_name(row, corner):
    return str(row.get("name") or corner.get("name") or corner.get("id") or "?")


def _as_float(value):
    if value in (None, ""):
        return 0.0
    return float(value)


def _voice_text(row, name):
    loss = _as_float(row.get("time_lost", 0))
    return "%s. Frena antes. Pierdes %.1f segundos." % (name, loss)


def _voice_for_lang(lang):
    voices = {
        "es-MX": "es-MX-JorgeNeural",
        "es-ES": "es-ES-AlvaroNeural",
        "en-US": "en-US-GuyNeural",
    }
    return voices.get(lang, lang)
