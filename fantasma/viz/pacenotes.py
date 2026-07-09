"""Genera un pack de Pace Notes para CrewChief desde el analisis de SimGhostInputs."""

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import wave
from pathlib import Path


def crewchief_pacenotes_dir(track_name: str) -> str:
    """Devuelve el directorio estándar de CrewChief para pace notes de AMS2."""
    return os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "CrewChiefV4",
        "pace_notes",
        "ams2",
        track_name,
    )


DEFAULT_MILESTONES = ["brake", "apex", "gas"]
# Gap UNIFORME entre los 3 sonidos del countdown de frenada (tic1 -> tic2 ->
# frenada), en segundos. Reemplaza la vieja formula de fracciones atada a un
# "anticipo total" (DEFAULT_COUNTDOWN_S=3.5, ~1.75s por gap): el PO reporto el
# contador "muy lento y a veces no completa los 3 sonidos" (QA 2026-07-08).
# Fuente unica: la UI (leyenda del Paso 5) y las firmas de este modulo lo leen
# de aqui — no lo dupliques.
DEFAULT_COUNTDOWN_GAP_S = 0.75
# Escala de los tics de AVISO del countdown (fracciones de la frecuencia base).
# El "¡ya!" no esta aqui: es el tono de frenada (DEFAULT_FREQS["brake"]) y suena
# EXACTO en el punto de frenada de la referencia — el PO: "el 3er bip tiene que
# coincidir con el inicio de la frenada, el 3 debe ser el ya" (QA 2026-07-06).
# La leyenda de la UI la deriva de aqui; _render_cue la consume por `step`.
COUNTDOWN_SCALE = (0.75, 0.875)
# Gap minimo global entre cues (metros). Fuente unica: plan_tone_events y la
# expansion del countdown en build_tone_pack lo comparten. build_voice_pack
# tambien lo comparte (ADR 0024, enmienda "notas de voz") via _resolve_min_gap.
DEFAULT_MIN_GAP_M = 50
# Anticipo POR TIEMPO de una nota de VOZ antes del punto de frenada, mismo
# criterio que el countdown de tonos (_countdown_lead_m, ADR 0024): el oido
# juzga en segundos, no en metros -- 200 m fijos son ~3 s a 216 km/h pero
# ~10 s a 70 km/h. lead_m = v/3.6 * DEFAULT_VOICE_LEAD_S, acotado a
# [DEFAULT_VOICE_LEAD_MIN_M, DEFAULT_VOICE_LEAD_MAX_M].
DEFAULT_VOICE_LEAD_S = 4.0
DEFAULT_VOICE_LEAD_MIN_M = 60
DEFAULT_VOICE_LEAD_MAX_M = 400
# Fallback cuando el milestone de frenada no trae "v" (corners JSON viejos,
# tests sinteticos): el mismo anticipo fijo de 200 m que build_voice_pack
# usaba hardcodeado antes de este fix -- no-regresion exacta para fixtures
# sin canal de velocidad.
DEFAULT_VOICE_LEAD_FALLBACK_M = 200
DEFAULT_FREQS = {
    # brake_countdown a 800 Hz, brake a 1000 Hz: distintos entre si (QA
    # 2026-07-05, ADR 0024) y turn_in ya no comparte 660 Hz con ningun tic
    # resultante (800*COUNTDOWN_SCALE = 600, 700 Hz) — el PO reporto que el
    # primer tic sonaba igual que turn_in (QA 2026-07-08, ver tabla de
    # frecuencias del reencuadre).
    "brake_countdown": 800,
    "brake": 1000,
    "brake_release": 820,
    # gear (cambio de marcha): sound=False por defecto en DEFAULT_CONFIG (sin
    # QA de oido todavia), pero un perfil de terceros puede forzar sound=true
    # (cue_profiles.py ya coacciona ese campo) -- sin esta entrada, _render_cue
    # caeria al fallback de 440 Hz, que casi no separa de apex (400, ratio
    # 1.1) ni de turn_in (500, ratio 1.14 al filo). 650 Hz cae en el hueco
    # entre turn_in (500) y brake_countdown (800), bien separado de ambos.
    "gear": 650,
    "turn_in": 500,
    "apex": 400,
    "throttle_on": 250,
    "gas": 220,
    "gas_100": 190,
    "full_throttle": 320,
    "coast": 160,
}
MILESTONE_ALIASES = {
    "brake": ["brake", "brake_start"],
    "brake_release": ["brake_release", "release"],
    "apex": ["apex"],
    "gas": ["throttle_on", "gas", "full_throttle"],
    "throttle_on": ["throttle_on", "gas"],
    "gas_100": ["gas_100", "full_throttle"],
    "full_throttle": ["full_throttle", "gas_100"],
    "turn_in": ["turn_in"],
}
MILESTONE_LABELS = {
    "brake_countdown": "contador de frenada",
    "brake_tic": "contador de frenada",
    "brake": "punto de frenada",
    "brake_release": "soltar freno",
    "apex": "apex",
    "throttle_on": "inicio de acelerador",
    "gas": "inicio de acelerador",
    "gas_100": "gas completo",
    "full_throttle": "gas completo",
    "turn_in": "turn-in",
    "coast": "inercia",
    "gear": "cambio de marcha",
}
# Color .ass (&HAABBGGRR, alpha 00 = opaco) por etiqueta legible — la misma que
# MILESTONE_LABELS pone en entry["description"]. Fuente unica del codigo de color
# de los subtitulos quemados (build_cue_ass) y de su leyenda. Un cue cuya etiqueta
# no este aqui cae a blanco.
CUE_SUB_COLORS = {
    "punto de frenada": "&H002020FF",  # rojo
    "contador de frenada": "&H0000A5FF",  # naranja
    "inicio de acelerador": "&H0000FF00",  # verde
    "gas completo": "&H0000FF88",  # verde claro
    "soltar freno": "&H0000FFFF",  # amarillo
    "turn-in": "&H00FFFFFF",  # blanco
    "apex": "&H000099FF",  # ambar
    "inercia": "&H00FFFF00",  # cian (coast: ni freno ni gas)
    "cambio de marcha": "&H00FF00FF",  # magenta (gear: solo subtitulo, sin sonido)
}
# Ventana de cada subtitulo (s). La #32 usaba una ventana FIJA [t-0.15, t+1.35]
# que se apagaba antes de tiempo. Ahora el rotulo dura hasta el siguiente cue
# (LEAD antes del tono, GAP de respiro antes del siguiente), acotado entre un
# minimo legible y un maximo para no dejar un rotulo viejo colgado en una recta.
CUE_SUB_LEAD_S = 0.15
CUE_SUB_MIN_S = 1.2
CUE_SUB_MAX_S = 3.5
CUE_SUB_GAP_S = 0.08
PLAN_CUES = [
    "brake_countdown",
    "brake",
    "brake_release",
    "turn_in",
    "throttle_on",
    "full_throttle",
]
# Catalogo COMPLETO de tipos de cue con su configuracion por defecto (enabled +
# priority). PLAN_CUES arriba sigue siendo la lista que consume la leyenda de
# la UI (Paso 5, WS-4) y NO se toca aqui: enumera solo los tipos que suenan
# HOY por defecto. DEFAULT_CONFIG es el catalogo mas amplio (incluye tipos
# apagados por defecto) que se threadea por el pipeline via cue_config. Con
# DEFAULT_CONFIG el pack es identico al de hoy (no-regresion): mismos tipos
# activos, mismas prioridades que antes vivian hardcodeadas en
# _corner_candidates.
DEFAULT_CONFIG = {
    # Prioridades reencuadradas (QA 2026-07-08 sobre la cinta del PR #35):
    # freno/gas arriba, turn_in su propio escalon, countdown/soltar-freno/coast
    # oportunistas ("solo si cabe"). brake sigue protegido (R1) sin importar
    # su numero; el resto participa en la cabida global por prioridad.
    #
    # enabled gatea si se generan candidatos de ese tipo en plan_tone_events
    # (para brake_countdown: la frenada protegida sigue sonando aunque el
    # countdown este apagado — el countdown se apaga, la frenada no).
    # sound gatea si ese candidato se sintetiza a WAV en build_tone_pack: en
    # True para todos salvo gear (solo subtitulo, sin audio todavia — no se
    # quiso meter una frecuencia nueva sin QA de oido).
    "brake_countdown": {"enabled": True, "priority": 50, "sound": True},
    "brake": {"enabled": True, "priority": 100, "sound": True},
    "brake_release": {"enabled": True, "priority": 45, "sound": True},
    "turn_in": {"enabled": True, "priority": 70, "sound": True},
    "throttle_on": {"enabled": True, "priority": 95, "sound": True},
    "full_throttle": {"enabled": True, "priority": 90, "sound": True},
    # Reincorporado al catalogo (ADR 0026 lo apago, no lo borro). Apagado por
    # defecto: no-regresion con el pack de hoy, que no suena en el apex. El PO
    # no lo menciono en el reencuadre de prioridades; queda igual (90) aunque
    # empate en numero con full_throttle — sigue apagado, no es urgente.
    "apex": {"enabled": False, "priority": 90, "sound": True},
    # Coast/inercia (WS-1: milestones coast_start/coast_end en corners.py). Un
    # solo cue en coast_start, no dos: coast_end no marca una accion del
    # piloto, solo el fin del hueco de inercia — un cue de entrada basta para
    # avisar "aqui no hay ni freno ni gas". solo_sin_frenada=True: en curvas
    # CON frenada el freno-turn_in-release ya cubre esa fase; el coast se
    # reserva para curvas sin freno, donde es la unica pista de que hay que
    # soltar el pedal antes de dar gas. Apagado por defecto.
    "coast": {"enabled": False, "priority": 20, "solo_sin_frenada": True, "sound": True},
    # Cambio de marcha (detect_gear_shifts en core/corners.py): implementado
    # acotado a SUBTITULO, sin sonido (sound=False) — evita meter una
    # frecuencia nueva sin QA de oido. Apagado por defecto (no-regresion); al
    # habilitarlo, los eventos "gear" compiten en la MISMA resolucion de
    # cabida/prioridad global que el resto del catalogo.
    "gear": {"enabled": False, "priority": 75, "sound": False},
}


def generate_tone(freq_hz, duration_s, volume=0.8, sample_rate=24000) -> bytes:
    """Seno puro con fade anti-clic — el sonido del perfil 'seno'.

    Se expresa sobre la MISMA tuberia que las variantes (``_wave_sine`` +
    ``_float_to_wav``) para que compartan un unico fade (``_FADE_S``) y el clip
    se aplique DESPUES del volumen. Antes esta funcion duplicaba la tuberia con
    un fade de 0.01 s mientras ``_wave_sine`` usaba 0.008 s: esa divergencia
    sesgaba la comparacion de oido entre 'seno' y las paletas. La unificacion es
    byte-identica para 'seno' (mismo time-base, mismo fade de 0.01 s, mismo
    orden de operaciones cuando no hay recorte).
    """
    return _float_to_wav(_wave_sine(freq_hz, duration_s, sample_rate), volume, sample_rate)


def _make_wav_bytes(samples_int16, sample_rate=24000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(samples_int16.tobytes())
    return buf.getvalue()


# ── Perfiles de sonido de los cues (QA 2026-07-09) ────────────────────────────
# El PO reporto que todos los cues suenan igual: hoy un cue solo cambia de
# FRECUENCIA (seno puro de generate_tone). "seno" es ese comportamiento de HOY
# (byte-identico); los otros tres dan a cada familia una FORMA DE ONDA / DURACION
# / ENVOLVENTE distinta para que se distingan de oido, SIN tocar DEFAULT_FREQS.
# La sintesis de las variantes viene de la evidencia de
# qa_runs/2026-07-09-sonidos/ (Mariana). El PO todavia NO eligio cual adoptar.
#
#   seno   -> comportamiento actual: seno puro, solo cambia la frecuencia.
#   timbre -> (A) una forma de onda por familia: freno=cuadrada band-limited,
#             tics=seno limpio, gas=triangular, turn_in/apex=pulso percusivo.
#   ritmo  -> (B) mismo seno de hoy, separado por DURACION/PATRON: freno del
#             doble de largo, gas doble-blip, turn_in pulso unico, tics iguales.
#   chirp  -> (C) barridos: el freno baja de frecuencia, el gas sube.
#
# NO se coloca en DEFAULT_CONFIG: ese dict es un catalogo POR TIPO DE CUE
# (cada valor es {enabled, priority, ...}) que cue_profiles.config_to_profile
# recorre con `for cue_type in DEFAULT_CONFIG` y resuelve con _cue_cfg (que hace
# dict(DEFAULT_CONFIG[cue])); una clave escalar "sound_profile" reventaria esa
# serializacion. El perfil es GLOBAL al pack, no por cue: viaja como parametro
# `sound_profile` de build_tone_pack/build_pack (ver docstrings).
DEFAULT_SOUND_PROFILE = "seno"
SOUND_PROFILES = ("seno", "timbre", "ritmo", "chirp")
# Solo se suman armonicos por debajo de 0.45*SR (~10.8 kHz a 24 kHz): ninguna
# componente pasa de Nyquist, asi no hay alias audible. Nunca se muestrea una
# discontinuidad (cuadrada/sierra por formula directa) — todo timbre no senoidal
# es SINTESIS ADITIVA de armonicos band-limited (QA 2026-07-09).
_NYQ_MARGIN = 0.45
# Fade-in/out UNICO (s) de todo cue tonal: el seno de generate_tone y las tres
# paletas comparten este anti-clic para que el unico contraste audible entre
# ellas sea la forma de onda, no un fade distinto (antes 0.01 vs 0.008 s).
_FADE_S = 0.01
# Duracion de REFERENCIA (s) a la que estan expresadas las duraciones de diseno
# de _PROFILE_SIGNALS. Con otra `duration`, cada cue de cada paleta se escala
# proporcionalmente (dur_efectiva = dur_diseno * duration / _PROFILE_REF_DURATION),
# asi `duration` MANDA en todas las paletas (no solo en 'seno') sin perder el
# contraste relativo entre cues. A duration == _PROFILE_REF_DURATION las paletas
# quedan exactamente en su duracion de diseno (evidencia qa_runs/2026-07-09).
_PROFILE_REF_DURATION = 0.12


def _tone_time(duration_s, sample_rate):
    import numpy as np

    # linspace (no arange) para casar EXACTO el time-base de generate_tone y
    # garantizar que 'seno' sea byte-identico a antes de unificar la tuberia.
    return np.linspace(0, duration_s, int(sample_rate * duration_s), endpoint=False)


def _tone_fade(sig, sample_rate, fade_s=_FADE_S):
    """Fade-in/out lineal para no meter un clic de discontinuidad en los bordes."""
    import numpy as np

    n = len(sig)
    f = min(int(sample_rate * fade_s), n // 2)
    if f > 0:
        env = np.ones(n)
        env[:f] = np.linspace(0, 1, f)
        env[-f:] = np.linspace(1, 0, f)
        sig = sig * env
    return sig


def _tone_norm(sig):
    import numpy as np

    peak = np.max(np.abs(sig))
    return sig / peak if peak > 0 else sig


def _odd_harmonics(freq, sample_rate):
    """Armonicos IMPARES de `freq` estrictamente por debajo de _NYQ_MARGIN*SR.

    Fuente unica del limite de banda de la cuadrada y la triangular: el armonico
    mas alto que devuelve cumple n*freq < 0.45*SR, garantia anti-alias.

    Falla RUIDOSAMENTE en los dos bordes que antes eran trampas silenciosas:
      - ``freq <= 0`` colgaba el ``while`` para siempre (la lista crecia hasta
        agotar memoria) — ahora ValueError inmediato.
      - ``freq >= _NYQ_MARGIN*SR`` devolvia lista vacia y dejaba la onda en todo
        ceros: un cue MUDO sin aviso. Un cue mudo en un sistema de seguridad es
        inaceptable en silencio — ahora ValueError accionable.
    """
    if freq <= 0:
        raise ValueError("frecuencia invalida para sintesis aditiva: %r (debe ser > 0)" % (freq,))
    harmonics = []
    n = 1
    while n * freq < _NYQ_MARGIN * sample_rate:
        harmonics.append(n)
        n += 2
    if not harmonics:
        raise ValueError(
            "frecuencia %r demasiado alta para una onda band-limited a %d Hz "
            "(el primer armonico ya supera %g*SR = %g Hz): saldria un cue mudo"
            % (freq, sample_rate, _NYQ_MARGIN, _NYQ_MARGIN * sample_rate)
        )
    return harmonics


def _wave_sine(freq, dur, sample_rate, fade_s=_FADE_S):
    import numpy as np

    return _tone_fade(np.sin(2 * np.pi * freq * _tone_time(dur, sample_rate)), sample_rate, fade_s)


def _wave_band_square(freq, dur, sample_rate, fade_s=_FADE_S):
    """Cuadrada band-limited: suma de armonicos impares con amplitud 1/n."""
    import numpy as np

    t = _tone_time(dur, sample_rate)
    sig = np.zeros_like(t)
    for n in _odd_harmonics(freq, sample_rate):
        sig += np.sin(2 * np.pi * n * freq * t) / n
    return _tone_fade(_tone_norm(sig), sample_rate, fade_s)


def _wave_band_triangle(freq, dur, sample_rate, fade_s=_FADE_S):
    """Triangular band-limited: armonicos impares con amplitud 1/n^2 y signo alterno."""
    import numpy as np

    t = _tone_time(dur, sample_rate)
    sig = np.zeros_like(t)
    for k, n in enumerate(_odd_harmonics(freq, sample_rate)):
        sig += ((-1) ** k) * np.sin(2 * np.pi * n * freq * t) / (n * n)
    return _tone_fade(_tone_norm(sig), sample_rate, fade_s)


def _wave_pulse(freq, dur, sample_rate):
    """Pulso percusivo: seno con decaimiento exponencial (se lee como 'golpe')."""
    import numpy as np

    t = _tone_time(dur, sample_rate)
    sig = np.sin(2 * np.pi * freq * t) * np.exp(-t / (dur * 0.35))
    fin = min(int(sample_rate * 0.002), len(sig) // 2)
    if fin > 0:
        sig[:fin] *= np.linspace(0, 1, fin)
    return _tone_norm(sig)


def _wave_chirp(f0, f1, dur, sample_rate, fade_s=_FADE_S):
    """Barrido lineal f0->f1. Frecuencia instantanea siempre < Nyquist: no aliasa."""
    import numpy as np

    t = _tone_time(dur, sample_rate)
    phase = 2 * np.pi * (f0 * t + (f1 - f0) / (2 * dur) * t**2)
    return _tone_fade(np.sin(phase), sample_rate, fade_s)


def _wave_double_blip(freq, sample_rate, blip_s=0.05, gap_s=0.05):
    """Dos pulsos de seno separados por un silencio corto: patron 'ta-ta'."""
    import numpy as np

    b = _wave_sine(freq, blip_s, sample_rate, fade_s=0.006)
    g = np.zeros(int(sample_rate * gap_s))
    return np.concatenate([b, g, b])


def _float_to_wav(sig, volume, sample_rate) -> bytes:
    import numpy as np

    # Recorte DESPUES de aplicar el volumen: con volume > 1 el clip previo a la
    # multiplicacion no protegia nada (0.8*1.5 = 1.2 -> 39320 desbordaba int16 y
    # daba la vuelta a negativo, un chasquido con el signo invertido). Ahora
    # satura limpio a +/-1.0 sea cual sea el volumen.
    samples = (np.clip(sig * volume, -1.0, 1.0) * 32767).astype(np.int16)
    return _make_wav_bytes(samples, sample_rate=sample_rate)


def _tic_freq(freqs, step):
    """Frecuencia del tic `step` del countdown: brake_countdown * COUNTDOWN_SCALE.

    Misma fuente que el perfil seno (_render_cue) — el perfil solo cambia la
    FORMA de onda, no la frecuencia base. El fallback sale de DEFAULT_FREQS (no
    de un literal suelto) para que seno y las paletas nunca discrepen en el tono
    base del tic si `freqs` llegara sin "brake_countdown".
    """
    return freqs.get("brake_countdown", DEFAULT_FREQS["brake_countdown"]) * COUNTDOWN_SCALE[step]


# Duraciones de DISENO de cada paleta (s), a _PROFILE_REF_DURATION. Cada una es
# el MULTIPLICADOR implicito (valor / _PROFILE_REF_DURATION) que escala con la
# `duration` pedida: p.ej. el freno de 'ritmo' (0.24) dura 2x la base y sus tics
# (0.08) ~0.67x — el contraste relativo se conserva a cualquier `duration`.
def _dur_scale(duration):
    return duration / _PROFILE_REF_DURATION


def _signal_timbre(cue, step, freqs, sample_rate, duration):
    s = _dur_scale(duration)
    if cue == "brake_tic":
        return _wave_sine(_tic_freq(freqs, step), 0.07 * s, sample_rate)
    if cue == "brake":
        return _wave_band_square(freqs.get("brake", 1000), 0.14 * s, sample_rate)
    if cue in ("turn_in", "apex"):
        return _wave_pulse(
            freqs.get(cue, 440), (0.09 if cue == "turn_in" else 0.10) * s, sample_rate
        )
    triangle_dur = {
        "throttle_on": 0.12,
        "gas": 0.12,
        "full_throttle": 0.12,
        "brake_release": 0.10,
        "coast": 0.14,
    }
    if cue in triangle_dur:
        return _wave_band_triangle(freqs.get(cue, 440), triangle_dur[cue] * s, sample_rate)
    return _wave_sine(freqs.get(cue, 440), 0.12 * s, sample_rate)


def _signal_ritmo(cue, step, freqs, sample_rate, duration):
    s = _dur_scale(duration)
    if cue == "brake_tic":
        # Los dos tics IGUALES entre si (misma freq y duracion): leen 'aviso, aviso'.
        return _wave_sine(_tic_freq(freqs, 1), 0.08 * s, sample_rate)
    if cue == "brake":
        return _wave_sine(freqs.get("brake", 1000), 0.24 * s, sample_rate)
    if cue in ("throttle_on", "gas", "full_throttle"):
        return _wave_double_blip(freqs.get(cue, 440), sample_rate, blip_s=0.05 * s, gap_s=0.05 * s)
    ritmo_dur = {"turn_in": 0.05, "brake_release": 0.12, "coast": 0.18, "apex": 0.10}
    return _wave_sine(freqs.get(cue, 440), ritmo_dur.get(cue, 0.12) * s, sample_rate)


def _signal_chirp(cue, step, freqs, sample_rate, duration):
    s = _dur_scale(duration)
    if cue == "brake_tic":
        # Barrido ascendente centrado en la MISMA frecuencia base del tic seno
        # (_tic_freq -> brake_countdown*COUNTDOWN_SCALE[step]). Antes indexaba una
        # tupla fija de longitud 2 con `step`, acoplada por convencion —no por
        # codigo— a COUNTDOWN_SCALE: si el countdown creciera a 3 tics, 'chirp'
        # reventaba con IndexError mientras las otras paletas seguian. Derivarlo
        # de _tic_freq lo blinda para cualquier longitud de COUNTDOWN_SCALE.
        f = _tic_freq(freqs, step)
        return _wave_chirp(f * 0.88, f * 1.08, 0.07 * s, sample_rate)
    if cue == "brake":
        return _wave_chirp(1200, 550, 0.16 * s, sample_rate)
    sweeps = {
        "throttle_on": (220, 460, 0.14),
        "gas": (200, 420, 0.14),
        "full_throttle": (300, 560, 0.14),
        "turn_in": (560, 470, 0.09),
        "brake_release": (700, 900, 0.12),
        "coast": (180, 150, 0.16),
    }
    if cue in sweeps:
        f0, f1, dur = sweeps[cue]
        return _wave_chirp(f0, f1, dur * s, sample_rate)
    # apex y cualquier cue sin barrido definido: referencia estable (seno).
    return _wave_sine(freqs.get(cue, 440), 0.10 * s, sample_rate)


_PROFILE_SIGNALS = {
    "timbre": _signal_timbre,
    "ritmo": _signal_ritmo,
    "chirp": _signal_chirp,
}


def _validate_sound_profile(sound_profile):
    if sound_profile not in SOUND_PROFILES:
        raise ValueError(
            "perfil de sonido desconocido: %r (validos: %s)"
            % (sound_profile, ", ".join(SOUND_PROFILES))
        )


def _validate_freqs(freqs, sample_rate=24000):
    """Toda frecuencia base debe ser positiva y por debajo de Nyquist (SR/2).

    build_tone_pack fusiona ``{**DEFAULT_FREQS, **freqs}`` con overrides del
    usuario (la CLI expone --brake-freq/--apex-freq/--gas-freq): sin este guard,
    un ``freq <= 0`` colgaba la sintesis aditiva de las paletas (bucle infinito
    en ``_odd_harmonics``) en vez de fallar, y un ``freq >= SR/2`` produce alias.
    Falla temprano y accionable, nombrando la clave y el valor infractores.
    """
    nyquist = sample_rate / 2
    malas = {
        k: v for k, v in freqs.items() if not (isinstance(v, (int, float)) and 0 < v < nyquist)
    }
    if malas:
        detalle = ", ".join("%s=%r" % (k, v) for k, v in sorted(malas.items()))
        raise ValueError(
            "frecuencia(s) fuera de rango (0, %g) Hz: %s — revisa --brake-freq/"
            "--apex-freq/--gas-freq o el dict `freqs`" % (nyquist, detalle)
        )


def build_tone_pack(
    rows,
    corners,
    outdir,
    top=5,
    milestones=None,
    freqs=None,
    duration=0.12,
    volume=0.8,
    smart=True,
    track_name=None,
    countdown_gap_s=DEFAULT_COUNTDOWN_GAP_S,
    cue_config=None,
    gear_shifts=None,
    sound_profile=DEFAULT_SOUND_PROFILE,
) -> dict:
    _validate_sound_profile(sound_profile)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    milestones = milestones or DEFAULT_MILESTONES
    freqs = {**DEFAULT_FREQS, **(freqs or {})}
    _validate_freqs(freqs)
    entries = []
    files = []
    plan = (
        plan_tone_events(
            rows,
            corners,
            top=top,
            countdown_gap_s=countdown_gap_s,
            cue_config=cue_config,
            gear_shifts=gear_shifts,
        )
        if smart
        else _legacy_tone_events(rows, corners, top, milestones)
    )
    variants = {}

    for event in plan["events"]:
        distance = int(event["distance"])
        cue = event["cue"]
        filename = None
        if _cue_sound_enabled(cue_config, cue):
            data = _render_cue(event, freqs, duration, volume, sound_profile=sound_profile)
            variant = variants.get(distance, 0)
            variants[distance] = variant + 1
            filename = "%d_%d.wav" % (distance, variant)
            path = out / filename
            path.write_bytes(data)
            files.append(str(path))
        entries.append(_metadata_entry(event["corner_name"], cue, distance, filename))

    metadata_path = _write_metadata(out, entries, track_name=track_name)
    plan_path = _write_plan(out, plan)
    files.append(str(metadata_path))
    files.append(str(plan_path))
    return {"outdir": str(out), "files": files, "entries": len(entries)}


def plan_tone_events(
    rows,
    corners,
    top=5,
    min_gap_m=DEFAULT_MIN_GAP_M,
    max_events_per_corner=3,
    countdown_m=120,
    countdown_gap_s=DEFAULT_COUNTDOWN_GAP_S,
    cue_config=None,
    gear_shifts=None,
) -> dict:
    cue_config = cue_config or DEFAULT_CONFIG
    events = []
    corners_plan = []

    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        candidates = _corner_candidates(row, corner, countdown_m, countdown_gap_s, cue_config)
        selected = []
        skipped = []
        for candidate in sorted(candidates, key=lambda c: (-c["priority"], c["distance"])):
            if candidate["distance"] <= 0:
                # El anticipo cayo antes de la meta (curva pegada al inicio de
                # vuelta): descartar, no clampear a 0 — un cue en t=0 del video
                # suena aleatorio (QA 2026-07-05).
                skipped.append({**candidate, "reason": "antes_de_la_meta"})
                continue
            if candidate.get("protected"):
                # El tono de frenada nunca cede a un gap (R1): entra siempre.
                selected.append(candidate)
                continue
            if len(selected) >= max_events_per_corner:
                skipped.append({**candidate, "reason": "max_events_per_corner"})
                continue
            if any(abs(candidate["distance"] - s["distance"]) < min_gap_m for s in selected):
                skipped.append({**candidate, "reason": "too_close_in_corner"})
                continue
            selected.append(candidate)

        selected.sort(key=lambda c: c["distance"])
        for candidate in selected:
            events.append(candidate)
        corners_plan.append(
            {
                "id": row.get("id", corner.get("id")),
                "name": _corner_name(row, corner),
                "time_lost": _as_float(row.get("time_lost", 0)),
                "selected": [_plan_public(c) for c in selected],
                "skipped": [_plan_public(c) for c in skipped],
            }
        )

    # Cambios de marcha (detect_gear_shifts, lap-wide): entran a la MISMA lista
    # de candidatos que las curvas, ANTES del sort, para participar en la
    # resolucion de cabida/prioridad global de abajo (sin duplicar esa logica
    # aqui). No pertenecen a ninguna curva: no entran a corners_plan (mismo
    # criterio que brake_tic, agregado mas abajo). Mismo guard que el resto de
    # candidatos por curva (linea ~267): un cambio de marcha cuyo anticipo (o
    # dato malformado) cae en distance<=0 se descarta, no se clampea a 0 (un
    # cue en t=0 del video suena aleatorio, QA 2026-07-05).
    gear_cfg = _cue_cfg(cue_config, "gear")
    if gear_cfg["enabled"]:
        for gs in gear_shifts or []:
            gear_event = _gear_shift_event(gs, gear_cfg["priority"])
            if gear_event is None or gear_event["distance"] <= 0:
                continue
            events.append(gear_event)

    # Cues MUDOS (sound=False, p.ej. gear) no pelean por cabida de AUDIO: el
    # gap global de abajo existe para evitar "sopa de tonos" (QA 2026-07-05),
    # pero un cue sin WAV no suena, asi que no tiene sentido que desplace a uno
    # que si suena solo por estar cerca en distancia. Sin este corte, un lap
    # con muchos cambios de marcha (mudos, alta prioridad) vaciaba por completo
    # cues de audio reales de menor prioridad (coast, full_throttle) en zonas
    # sin relacion (QA 2026-07-08, regresion detectada al activar "gear" +
    # "Coast" juntos en la cinta de estudio). Los mudos resuelven su propia
    # cabida entre ellos (mismo criterio de prioridad/tie-break) para que dos
    # subtitulos no se pisen, y se recombinan con los de audio despues.
    # protected (freno) siempre cuenta como sonoro sin importar el campo
    # "sound" resuelto: es el ÚNICO cue que R1 garantiza que nunca cede un
    # hueco, y esa garantia es cruzada contra CUALQUIER cue de audio cercano.
    # Un perfil de terceros con {"type": "brake", "sound": false} (cue_profiles
    # acepta "sound" en cualquier tipo, no solo "gear") no debe poder sacar la
    # frenada del pool sonoro y romper esa garantia (Reviewer 2026-07-08).
    sound_events = [
        e for e in events if e.get("protected") or _cue_sound_enabled(cue_config, e["cue"])
    ]
    silent_events = [
        e for e in events if not e.get("protected") and not _cue_sound_enabled(cue_config, e["cue"])
    ]

    # Gap minimo GLOBAL: el de arriba (linea ~287) solo separa cues DENTRO de
    # una curva; en curvas encadenadas quedaban cues de curvas vecinas a <1 s
    # (sopa de tonos, QA 2026-07-05). _resolve_min_gap (compartida con
    # build_voice_pack, ADR 0024 enmienda "notas de voz") resuelve esto.
    kept_sound, skipped_sound = _resolve_min_gap(sound_events, min_gap_m)
    kept_silent, skipped_silent = _resolve_min_gap(silent_events, min_gap_m)
    kept = sorted(kept_sound + kept_silent, key=lambda c: c["distance"])
    skipped_global = skipped_sound + skipped_silent

    # Reconciliar el plan por curva: un cue descartado globalmente NO puede
    # seguir en "selected" (plan.json es la auditoria de que suena y que no).
    # Nota: los brake_tic se agregan despues, a plan["events"] pero NO a los
    # "selected" por-curva; la fuente de verdad de lo que se renderiza es
    # plan["events"], no la suma de los "selected".
    dropped = {(e["corner_id"], e["cue"], e["distance"]) for e in skipped_global}
    for corner_plan in corners_plan:
        still = []
        for sel in corner_plan["selected"]:
            if (sel["corner_id"], sel["cue"], sel["distance"]) in dropped:
                corner_plan["skipped"].append({**sel, "reason": "too_close_global"})
            else:
                still.append(sel)
        corner_plan["selected"] = still

    # Countdown OPORTUNISTA: por cada frenada protegida con lead_m, 2 tics de
    # aviso antes de la frenada (en brake_d - lead_m y brake_d - lead_m/2). Cada
    # tic entra SOLO si cabe a >=min_gap de TODO sonido de OTRO grupo ya en la
    # linea de tiempo (frenadas y tics de OTRAS curvas). El tono de frenada de
    # SU MISMA curva y su tic hermano quedan fuera de la comparacion: son un
    # solo grupo cohesivo (2 tics + el "ya" en brake_d, ADR 0026) y un tic no
    # puede auto-rechazarse contra el evento que anuncia. Sin esta exclusion,
    # lead_m < 2*min_gap_m (curvas por debajo de ~103 km/h con el default de
    # 3.5 s) tiraba el tic step=1 contra su propia frenada. Se recorren en
    # orden de distancia (greedy) para resolver tic-vs-tic entre curvas.
    # brake_countdown.enabled gatea este bloque completo: si esta apagado no
    # se genera ningun tic, pero la frenada protegida (ya en "kept") sigue
    # sonando intacta. brake_countdown.priority reemplaza el 100 que antes
    # vivia hardcodeado aqui; no participa en la regla de cabida de arriba
    # (own_idx sigue siendo la unica exclusion, sin tocar).
    countdown_cfg = _cue_cfg(cue_config, "brake_countdown")
    tics = []
    countdown_skipped = []
    if countdown_cfg["enabled"]:
        # Igual que en la resolucion de cabida global de arriba: un tic de
        # countdown SI suena, asi que solo debe medirse contra otros eventos
        # que TAMBIEN suenan. Sin este filtro, un cambio de marcha mudo cerca
        # de un tic candidato lo tira sin razon -- mismo bug que motivo el
        # split sound/silent, encontrado en el mismo diff (Reviewer 2026-07-08).
        # Cada entrada lleva (group_idx, distancia, evento_real): el group_idx es
        # el indice en `kept` de la FRENADA que ancla el grupo cohesivo (para un
        # evento normal de kept, su propio indice; para un tic aceptado, el
        # own_idx de su curva). Se guarda el EVENTO REAL que ocupa ese metro
        # -- no un indice a kept -- para que `against` reporte el cue y la
        # distancia del sonido que de verdad estorbo (un tic ya aceptado
        # reporta brake_tic + su distancia, no la frenada de su curva).
        timeline = [
            (idx, e["distance"], e)
            for idx, e in enumerate(kept)
            if _cue_sound_enabled(cue_config, e["cue"])
        ]
        tic_candidates = []
        for idx, e in enumerate(kept):
            if e.get("protected") and e.get("lead_m"):
                for step, frac in ((0, 1.0), (1, 0.5)):
                    d = int(round(e["distance"] - e["lead_m"] * frac))
                    tic_candidates.append((d, step, idx, e))
        for d, step, own_idx, e in sorted(tic_candidates, key=lambda x: x[0]):
            tic = {
                "corner_id": e["corner_id"],
                "corner_name": e["corner_name"],
                "cue": "brake_tic",
                "distance": d,
                "priority": countdown_cfg["priority"],
                "reason": "aviso de frenada",
                "step": step,
            }
            # Trazabilidad: un tic descartado deja rastro en skipped_global (antes
            # se perdia con un `continue` mudo y plan.json mentia por omision).
            # NO entra en plan["events"], que sigue siendo la fuente de verdad de
            # lo que se renderiza.
            if d <= 0:
                countdown_skipped.append({**tic, "reason": "antes_de_la_meta"})
                continue
            # Estorbo mas cercano que viola el gap: se registra contra que evento
            # choco (cue, curva, distancia) para que el PO pueda auditar.
            clash = None
            for group_idx, t, ev in timeline:
                # Un tic no choca contra el grupo cohesivo de SU MISMA curva
                # (su frenada y su tic hermano comparten own_idx): se salta por
                # group_idx, no por la identidad del evento.
                if group_idx == own_idx:
                    continue
                if abs(d - t) < min_gap_m and (clash is None or abs(d - t) < abs(d - clash[0])):
                    clash = (t, ev)
            if clash is not None:
                against = clash[1]
                countdown_skipped.append(
                    {
                        **tic,
                        "reason": "tic_sin_espacio",
                        "against": {
                            "corner_id": against["corner_id"],
                            "cue": against["cue"],
                            "distance": against["distance"],
                        },
                    }
                )
                continue
            timeline.append((own_idx, d, tic))
            tics.append(tic)

    all_events = sorted(kept + tics, key=lambda c: c["distance"])
    return {
        "events": [_plan_public(e) for e in all_events],
        "corners": corners_plan,
        "skipped_global": [_plan_public(e) for e in skipped_global + countdown_skipped],
    }


def _run_async_in_thread(coro):
    """Ejecuta una corutina en un thread con su propio event-loop.

    Seguro si hay un loop activo (p.ej. NiceGUI/uvicorn), donde
    asyncio.run() lanzaria RuntimeError: This event loop is already running.
    """
    import asyncio

    exc: list = []

    def _target():
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(coro)
        except Exception as e:  # noqa: BLE001
            exc.append(e)
        finally:
            loop.close()

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if exc:
        raise exc[0]


def build_voice_pack(
    rows,
    corners,
    outdir,
    top=5,
    lang="es-MX",
    track_name=None,
    min_gap_m=DEFAULT_MIN_GAP_M,
    voice_lead_s=DEFAULT_VOICE_LEAD_S,
) -> dict:
    """Genera un pack de notas de VOZ (edge-tts), una por curva top-N.

    Pasa por el MISMO gap minimo global que ``plan_tone_events``
    (``_resolve_min_gap``, ADR 0024) para que dos narraciones de curvas
    encadenadas no se encimen — antes este pack no aplicaba ningun gap entre
    curvas (ROADMAP: "las notas de VOZ no pasan por el plan anti-
    saturacion"). El limite de una nota por curva es estructural (un
    candidato por fila, milestone de frenada), sin necesidad de un
    ``max_events_per_corner`` explicito.

    El anticipo (antes 200 m fijos) se deriva ahora de la velocidad de
    llegada a la frenada, igual criterio que el countdown de tonos
    (``_voice_lead_m``): el tiempo de reaccion se mide en segundos, no en
    metros.
    """
    if importlib.util.find_spec("edge_tts") is None:
        raise RuntimeError("edge-tts no instalado: ejecuta pip install 'fantasma-inputs[voice]'")

    import edge_tts

    ffmpeg = shutil.which("ffmpeg")
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    entries = []
    files = []
    voice = _voice_for_lang(lang)

    if not ffmpeg:
        print("aviso: ffmpeg no disponible; se omiten las pace notes de voz", file=sys.stderr)
        metadata_path = _write_metadata(out, entries, track_name=track_name)
        return {"outdir": str(out), "files": [str(metadata_path)], "entries": 0}

    candidates = []
    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        brake = _milestone(corner, "brake") or _milestone(row, "brake")
        if not brake or brake.get("d") is None:
            continue
        name = _corner_name(row, corner)
        raw_distance = _as_float(brake["d"]) - _voice_lead_m(brake, voice_lead_s)
        if raw_distance <= 0:
            # La nota caeria antes de la meta (curva pegada al inicio): saltarla,
            # no clampear a 0 — una voz en t=0 del video suena aleatoria. Con
            # aviso: un descarte silencioso hace creer que edge-tts fallo.
            print(
                "aviso: nota de voz de %s descartada (caeria antes de la meta)" % name,
                file=sys.stderr,
            )
            continue
        # Prioridad = tiempo perdido: si dos narraciones colisionan por el gap
        # global, sobrevive la curva donde mas se pierde (la que mas vale la
        # pena narrar). "row" viaja aparte (_event no lo conoce) para
        # recuperar flags/time_lost al armar el texto tras el gap.
        priority = int(round(_as_float(row.get("time_lost", 0)) * 100))
        candidate = _event(row, corner, "voice", raw_distance, priority, "nota de voz")
        candidate["row"] = row
        candidates.append(candidate)

    kept, skipped = _resolve_min_gap(candidates, min_gap_m)
    for c in skipped:
        print(
            "aviso: nota de voz de %s descartada (muy cerca de otra narracion)" % c["corner_name"],
            file=sys.stderr,
        )

    for event in sorted(kept, key=lambda c: c["distance"]):
        row = event["row"]
        name = event["corner_name"]
        distance = event["distance"]
        filename = "%d_0.wav" % distance
        text = _voice_text(row, name)
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = os.path.join(tmp, "note.mp3")
            wav = out / filename
            _run_async_in_thread(edge_tts.Communicate(text, voice=voice).save(mp3))
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

    metadata_path = _write_metadata(out, entries, track_name=track_name)
    files.append(str(metadata_path))
    return {"outdir": str(out), "files": files, "entries": len(entries)}


# Kwargs de build_pack que solo entiende build_voice_pack (min_gap_m,
# voice_lead_s): se excluyen de tone_kwargs (build_tone_pack no los acepta,
# TypeError si se colaran en modo "both") y se reenvian aparte a
# build_voice_pack -- mismo criterio que "lang", que ya se excluia de
# tone_kwargs por la misma razon.
_VOICE_ONLY_KWARGS = ("min_gap_m", "voice_lead_s")


def build_pack(rows, corners, outdir, mode="tones", top=5, cue_config=None, **kwargs) -> dict:
    track_name = kwargs.pop("track_name", None)
    voice_kwargs = {k: kwargs[k] for k in _VOICE_ONLY_KWARGS if k in kwargs}
    if mode == "tones":
        tone_kwargs = {k: v for k, v in kwargs.items() if k != "lang" and k not in voice_kwargs}
        return build_tone_pack(
            rows,
            corners,
            outdir,
            top=top,
            track_name=track_name,
            cue_config=cue_config,
            **tone_kwargs,
        )
    if mode == "voice":
        return build_voice_pack(
            rows,
            corners,
            outdir,
            top=top,
            lang=kwargs.get("lang", "es-MX"),
            track_name=track_name,
            **voice_kwargs,
        )
    if mode != "both":
        raise ValueError("modo invalido: %s" % mode)

    tone_kwargs = {k: v for k, v in kwargs.items() if k != "lang" and k not in voice_kwargs}
    tones = build_tone_pack(
        rows, corners, outdir, top=top, track_name=track_name, cue_config=cue_config, **tone_kwargs
    )
    tone_entries = _read_entries(Path(outdir) / "metadata.json")
    voice = build_voice_pack(
        rows,
        corners,
        outdir,
        top=top,
        lang=kwargs.get("lang", "es-MX"),
        track_name=track_name,
        **voice_kwargs,
    )
    voice_entries = _read_entries(Path(outdir) / "metadata.json")
    _write_metadata(Path(outdir), tone_entries + voice_entries, track_name=track_name)
    files = list(dict.fromkeys(tones["files"] + voice["files"]))
    return {
        "outdir": str(Path(outdir)),
        "files": files,
        "entries": len(tone_entries) + len(voice_entries),
    }


def render_pace_notes_track(pace_notes_dir, lap, output, sample_rate=24000, volume=1.0) -> str:
    import numpy as np

    metadata_path = Path(pace_notes_dir) / "metadata.json"
    if not metadata_path.exists():
        raise RuntimeError("no existe metadata.json en %s" % pace_notes_dir)
    if not lap.has("dist") or not lap.has("time"):
        raise RuntimeError("la telemetria necesita canales time y dist para sincronizar sonidos")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    total_frames = int((lap.laptime + 1.0) * sample_rate)
    mixed = np.zeros(total_frames, dtype=np.float32)
    for entry in metadata.get("entries", []):
        t = _dist_to_time(lap, _as_float(entry.get("distanceRoundTrack")))
        start = max(0, int(t * sample_rate))
        for filename in entry.get("fileNames", []):
            wav_path = Path(pace_notes_dir) / filename
            if not wav_path.exists():
                continue
            samples, rate = _read_wav_int16(wav_path)
            if rate != sample_rate:
                continue
            end = min(len(mixed), start + len(samples))
            if end > start:
                mixed[start:end] += samples[: end - start] * volume

    mixed = (mixed.clip(-1.0, 1.0) * 32767).astype(np.int16)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_bytes(_make_wav_bytes(mixed, sample_rate=sample_rate))
    return str(output)


def _top_rows(rows, top):
    if not top:
        # top=0 (o None): TODAS las curvas detectadas, tambien donde no se
        # pierde tiempo — el cue de frenada actua como pace note de ritmo,
        # estilo rally (pedido del PO, ADR 0024).
        return list(rows)
    losses = [r for r in rows if _as_float(r.get("time_lost", 0)) > 0]
    losses.sort(key=lambda r: _as_float(r.get("time_lost", 0)), reverse=True)
    return losses[:top]


def _legacy_tone_events(rows, corners, top, milestones):
    events = []
    corners_plan = []
    for row in _top_rows(rows, top):
        corner = _find_corner(row, corners)
        if not corner:
            continue
        selected = []
        for milestone in milestones:
            m = _milestone(corner, milestone) or _milestone(row, milestone)
            if not m or m.get("d") is None:
                continue
            selected.append(
                _event(row, corner, milestone, _as_float(m["d"]), 0, "legacy:%s" % milestone)
            )
        events.extend(selected)
        corners_plan.append(
            {
                "id": row.get("id", corner.get("id")),
                "name": _corner_name(row, corner),
                "time_lost": _as_float(row.get("time_lost", 0)),
                "selected": [_plan_public(e) for e in selected],
                "skipped": [],
            }
        )
    # skipped_global vacio para que el esquema del plan sea el mismo que el smart
    return {
        "events": [_plan_public(e) for e in events],
        "corners": corners_plan,
        "skipped_global": [],
    }


def _countdown_lead_m(brake, countdown_m, countdown_gap_s, min_lead_m=30, max_lead_m=250):
    """Distancia de anticipo del countdown de frenada.

    lead_m representa DOS gaps de countdown_gap_s segundos cada uno (tic1 ->
    tic2 -> frenada), a la velocidad de llegada a la frenada (v del milestone,
    km/h): lead_m = v/3.6 * countdown_gap_s * 2, acotado a [min_lead_m,
    max_lead_m]. plan_tone_events reparte ese lead_m en los tics con las
    fracciones (1.0, 0.5) de COUNTDOWN_SCALE-como-distancia — como ambos
    gaps resultantes son lead_m/2, salen SIEMPRE iguales entre si sin importar
    el clamp (uniformidad garantizada por construccion, no por el valor
    exacto de lead_m). Fallback al countdown_m fijo si el milestone no trae v
    (corners JSON viejos, tests sinteticos).
    """
    v = brake.get("v")
    if not v:
        return countdown_m
    lead = _as_float(v) / 3.6 * countdown_gap_s * 2
    return max(min_lead_m, min(max_lead_m, lead))


def _resolve_min_gap(evs, min_gap_m):
    """Gap minimo GLOBAL entre eventos candidatos, compartido por
    ``plan_tone_events`` y ``build_voice_pack`` (ADR 0024, enmienda "notas de
    voz" — antes vivia como funcion anidada solo dentro de plan_tone_events).

    Un evento PROTEGIDO (p.ej. el tono de frenada, R1) nunca se descarta:
    protegido vs protegido se quedan ambos (dos frenadas reales pegadas
    siguen sonando ambas); protegido vs no-protegido cae el no-protegido.
    Entre no-protegidos gana el de mayor ``priority``; en empate sobrevive el
    que aparece primero (orden de distancia). Nota: al reemplazar al vecino
    anterior no hace falta re-verificar hacia atras — el reemplazado ya
    respetaba el gap con su predecesor y el nuevo esta aun mas adelante.

    build_voice_pack NO marca sus eventos como protegidos: la garantia R1 es
    una decision especifica del beep de frenada (0.12 s, nunca se pisa de
    verdad); una narracion hablada de ~7.5 s si debe poder ceder su hueco
    ante una curva vecina, o dos frases se encabalgan (ROADMAP, deuda "las
    notas de VOZ no pasan por el plan anti-saturacion").
    """
    evs = sorted(evs, key=lambda c: c["distance"])
    kept = []
    skipped = []
    for event in evs:
        if kept and event["distance"] - kept[-1]["distance"] < min_gap_m:
            prev = kept[-1]
            ev_prot = event.get("protected")
            prev_prot = prev.get("protected")
            if ev_prot and prev_prot:
                kept.append(event)
            elif ev_prot and not prev_prot:
                skipped.append({**kept.pop(), "reason": "too_close_global"})
                kept.append(event)
            elif prev_prot and not ev_prot:
                skipped.append({**event, "reason": "too_close_global"})
            elif event["priority"] > prev["priority"]:
                skipped.append({**kept.pop(), "reason": "too_close_global"})
                kept.append(event)
            else:
                skipped.append({**event, "reason": "too_close_global"})
        else:
            kept.append(event)
    return kept, skipped


def _voice_lead_m(brake, lead_s):
    """Anticipo (m) de una nota de VOZ antes del punto de frenada.

    Ver DEFAULT_VOICE_LEAD_S: lead_m = v/3.6 * lead_s, acotado a
    [DEFAULT_VOICE_LEAD_MIN_M, DEFAULT_VOICE_LEAD_MAX_M]. Sin ``v`` en el
    milestone, cae a DEFAULT_VOICE_LEAD_FALLBACK_M (el fijo de 200 m que este
    modulo ya usaba antes de este fix).
    """
    v = brake.get("v")
    if not v:
        return DEFAULT_VOICE_LEAD_FALLBACK_M
    lead = _as_float(v) / 3.6 * lead_s
    return max(DEFAULT_VOICE_LEAD_MIN_M, min(DEFAULT_VOICE_LEAD_MAX_M, lead))


def _cue_cfg(cue_config, cue):
    """Config RESUELTA de un tipo de cue: DEFAULT_CONFIG mezclado campo a
    campo con el override del usuario.

    Una clave ausente en el override, o presente con valor None (una UI
    futura podria mandar {"priority": None} para "usa el default"), cae al
    valor de DEFAULT_CONFIG — nunca None. Devuelve el dict completo (enabled,
    priority y demas campos del tipo) para que los call sites lean
    cfg["priority"] / cfg["enabled"] directo, sin un literal de fallback que
    duplique los numeros de DEFAULT_CONFIG.
    """
    resolved = dict(DEFAULT_CONFIG.get(cue, {"enabled": True, "priority": 50, "sound": True}))
    override = (cue_config or {}).get(cue) or {}
    for key, value in override.items():
        if value is not None:
            resolved[key] = value
    return resolved


def _corner_candidates(
    row, corner, countdown_m, countdown_gap_s=DEFAULT_COUNTDOWN_GAP_S, cue_config=None
):
    loss = _as_float(row.get("time_lost", 0))
    flags = str(row.get("flags", ""))
    d_brake = _as_float(row.get("d_brake_m", 0)) if row.get("d_brake_m") not in (None, "") else 0
    d_gas = _as_float(row.get("d_gas100_m", 0)) if row.get("d_gas100_m") not in (None, "") else 0
    braking_issue = "frenada" in flags or d_brake > 15
    exit_issue = abs(d_gas) > 20 or (loss >= 0.25 and "vmin" not in flags)
    apex_issue = "vmin" in flags or loss >= 0.25
    candidates = []

    brake_cfg = _cue_cfg(cue_config, "brake")
    brake = _milestone(corner, "brake")
    if brake_cfg["enabled"] and brake and brake.get("d") is not None:
        brake_d = _as_float(brake["d"])
        lead_m = _countdown_lead_m(brake, countdown_m, countdown_gap_s)
        # Tono de frenada UNIVERSAL: toda curva con milestone de frenada suena,
        # sin importar severidad. Es PROTEGIDO — ningun gap lo descarta (R1), sin
        # importar su prioridad en config. El countdown (tics de aviso) se
        # coloca aparte y de forma oportunista en plan_tone_events usando lead_m.
        candidates.append(
            _event(
                row,
                corner,
                "brake",
                brake_d,
                brake_cfg["priority"],
                "marca frenada",
                lead_m=lead_m,
                protected=True,
            )
        )

    release_cfg = _cue_cfg(cue_config, "brake_release")
    release = _milestone(corner, "brake_release")
    if release_cfg["enabled"] and release and release.get("d") is not None and braking_issue:
        candidates.append(
            _event(
                row,
                corner,
                "brake_release",
                _as_float(release["d"]),
                release_cfg["priority"],
                "salida de freno",
            )
        )

    turn_cfg = _cue_cfg(cue_config, "turn_in")
    turn = _milestone(corner, "turn_in")
    if turn_cfg["enabled"] and turn and turn.get("d") is not None and loss >= 0.25:
        candidates.append(
            _event(
                row,
                corner,
                "turn_in",
                _as_float(turn["d"]),
                turn_cfg["priority"],
                "inicio de giro",
            )
        )

    throttle_cfg = _cue_cfg(cue_config, "throttle_on")
    throttle = _milestone(corner, "throttle_on")
    if throttle_cfg["enabled"] and throttle and throttle.get("d") is not None and exit_issue:
        candidates.append(
            _event(
                row,
                corner,
                "throttle_on",
                _as_float(throttle["d"]),
                throttle_cfg["priority"],
                "inicio de gas",
            )
        )

    full_cfg = _cue_cfg(cue_config, "full_throttle")
    full = _milestone(corner, "full_throttle")
    if full_cfg["enabled"] and full and full.get("d") is not None and (exit_issue or loss >= 0.25):
        candidates.append(
            _event(
                row,
                corner,
                "full_throttle",
                _as_float(full["d"]),
                full_cfg["priority"],
                "gas a fondo",
            )
        )

    apex_cfg = _cue_cfg(cue_config, "apex")
    apex = _milestone(corner, "apex")
    if apex_cfg["enabled"] and apex and apex.get("d") is not None and apex_issue:
        candidates.append(
            _event(
                row,
                corner,
                "apex",
                _as_float(apex["d"]),
                apex_cfg["priority"],
                "corrige V-Min/apex",
            )
        )

    coast_cfg = _cue_cfg(cue_config, "coast")
    coast = _milestone(corner, "coast_start")
    if coast_cfg["enabled"] and coast and coast.get("d") is not None:
        # Sin frenada: no hay milestone "brake" en esta curva (turn_in +
        # release ya cubren la fase de freno cuando si la hay).
        sin_frenada = _milestone(corner, "brake") is None
        if not coast_cfg["solo_sin_frenada"] or sin_frenada:
            candidates.append(
                _event(
                    row,
                    corner,
                    "coast",
                    _as_float(coast["d"]),
                    coast_cfg["priority"],
                    "inercia",
                )
            )

    return candidates


def _event(row, corner, cue, distance, priority, reason, lead_m=None, protected=False):
    event = {
        "corner_id": str(row.get("id") or corner.get("id") or "?"),
        "corner_name": _corner_name(row, corner),
        "cue": cue,
        "distance": int(round(distance)),
        "priority": priority,
        "reason": reason,
    }
    if lead_m is not None:
        event["lead_m"] = int(round(lead_m))
    if protected:
        event["protected"] = True
    return event


def _gear_label(gear):
    """Etiqueta corta de una marcha: N (neutro), R (reversa) o el numero.

    Mismo criterio que overlay.py (t_gear_val): gear==0 es neutro, gear<0 es
    reversa — no asumimos que solo existan marchas positivas.
    """
    g = int(gear)
    if g == 0:
        return "N"
    if g < 0:
        return "R"
    return "%dª" % g


def _gear_shift_event(gs, priority):
    """Evento de cue `gear` (shape de `_event`) a partir de un cambio de
    marcha detectado por `detect_gear_shifts` (core/corners.py).

    No pertenece a ninguna curva — `corner_id` es sintetico (unico por
    distancia) y `corner_name` lleva el texto del subtitulo ("cambio a 3ª"),
    que `_metadata_entry`/`build_cue_ass` ya saben mostrar como el "nombre"
    bajo la etiqueta del cue. Sin `lead_m` ni `protected`: un cambio de
    marcha compite por cabida como cualquier otro cue no protegido.

    Frontera robusta (Reviewer): `gs` puede venir de un
    ``corners_detected.json`` cargado o editado a mano, sin las claves que
    `detect_gear_shifts` siempre genera. Una entrada sin "distance"/"gear_to"
    validos devuelve None (se descarta esa entrada, no revienta el pack
    completo) -- mismo espiritu que `cue_profiles.py` con perfiles de
    terceros.
    """
    distance = gs.get("distance")
    gear_to = gs.get("gear_to")
    if distance is None or gear_to is None:
        return None
    try:
        distance = _as_float(distance)
        gear_to = int(gear_to)
    except (TypeError, ValueError):
        return None
    return {
        "corner_id": "gear-%d" % int(round(distance)),
        "corner_name": "cambio a %s" % _gear_label(gear_to),
        "cue": "gear",
        "distance": int(round(distance)),
        "priority": priority,
        "reason": "cambio de marcha",
    }


def _cue_sound_enabled(cue_config, cue):
    """Si el cue debe sintetizarse a WAV (True) o solo subtitularse (False).

    `brake_tic` no tiene entrada propia en DEFAULT_CONFIG: su sonido cuelga
    de `brake_countdown` (mismo criterio que `enabled`/`priority` en
    plan_tone_events).
    """
    key = "brake_countdown" if cue == "brake_tic" else cue
    return bool(_cue_cfg(cue_config, key).get("sound", True))


def _plan_public(event):
    keys = (
        "corner_id",
        "corner_name",
        "cue",
        "distance",
        "priority",
        "reason",
        "lead_m",
        "protected",
        "step",
        "against",
    )
    return {k: event[k] for k in keys if k in event}


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
    """Entrada de metadata.json para un cue.

    filename=None (cue con sound=False, p.ej. gear): sin WAV que reproducir,
    pero la entrada se conserva igual con listas vacias -- build_cue_ass
    solo lee "description"/"distanceRoundTrack", asi el cue se sigue
    subtitulando aunque no suene.
    """
    label = MILESTONE_LABELS.get(milestone, milestone)
    names = [filename] if filename else []
    return {
        "description": "%s — %s" % (name, label),
        "distanceRoundTrack": distance,
        "lapNumber": None,
        "minimumSpeed": None,
        "maximumSpeed": None,
        "minimumYawAngle": None,
        "maximumYawAngle": None,
        "recordingNames": names,
        "fileNames": names,
        "playAllInOrder": False,
    }


def _render_cue(event, freqs, duration, volume, sound_profile=DEFAULT_SOUND_PROFILE):
    """Sintetiza el WAV de un evento del plan segun su cue y el perfil de sonido.

    Cada evento del plan ya trae su distancia final (los tics del countdown y
    el tono de frenada son eventos independientes, colocados en plan_tone_events).
    El tic asciende en frecuencia por su `step` (COUNTDOWN_SCALE); el tono de
    frenada suena mas largo y a otra frecuencia para no confundirlo con el tic.

    `sound_profile` cambia SOLO la forma de onda / duracion / envolvente, nunca
    las frecuencias base (DEFAULT_FREQS). "seno" (default) es el comportamiento
    de HOY, byte-identico; timbre/ritmo/chirp son las variantes de la evidencia
    de qa_runs/2026-07-09-sonidos/ (ver SOUND_PROFILES).
    """
    cue = event["cue"]
    if sound_profile == "seno":
        if cue == "brake_tic":
            base = freqs.get("brake_countdown", DEFAULT_FREQS["brake_countdown"])
            scale = COUNTDOWN_SCALE[event.get("step", 0)]
            return generate_tone(base * scale, 0.08, volume=volume)
        if cue == "brake":
            return generate_tone(freqs.get("brake", 1000), duration, volume=volume)
        return generate_tone(freqs.get(cue, 440), duration, volume=volume)
    _validate_sound_profile(sound_profile)
    sig = _PROFILE_SIGNALS[sound_profile](cue, event.get("step", 0), freqs, 24000, duration)
    return _float_to_wav(sig, volume, 24000)


def _write_metadata(outdir, entries, track_name=None):
    metadata = {
        "description": "Generado por SimGhostInputs",
        "gameEnumName": "AMS2",
        "carClassName": None,
        "trackName": track_name,
        "entries": entries,
    }
    path = outdir / "metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _write_plan(outdir, plan):
    path = outdir / "plan.json"
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
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


def _dist_to_time(lap, dist):
    d = lap.col("dist")
    t = lap.col("time")
    if not d or not t:
        return 0.0
    if dist <= d[0]:
        return t[0]
    for i in range(1, len(d)):
        if d[i] >= dist:
            span = d[i] - d[i - 1]
            if span <= 0:
                return t[i]
            ratio = (dist - d[i - 1]) / span
            return t[i - 1] + ratio * (t[i] - t[i - 1])
    return t[-1]


def _ass_time(seconds):
    """Formatea segundos al reloj de un evento .ass (H:MM:SS.cc)."""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    return "%d:%02d:%05.2f" % (h, m, seconds % 60)


def _split_cue_desc(description):
    """Parte ``"Nombre curva — etiqueta"`` en (nombre, etiqueta).

    ``_metadata_entry`` siempre arma la descripcion con " — " como separador;
    usamos rsplit por si el nombre de la curva trajera un guion largo propio.
    """
    parts = description.rsplit(" — ", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return description.strip(), description.strip()


def build_cue_ass(pace_notes_dir, lap, video_w, video_h, hud_margin_v=None):
    """Genera el contenido de un subtitulo .ass que nombra cada cue del pack.

    Cada entrada del pack se rotula con su etiqueta (color por tipo, ver
    CUE_SUB_COLORS) y el nombre de la curva, anclado por encima del HUD para
    que el piloto sepa que significa cada sonido cuando suena. El tiempo de cada
    rotulo usa el MISMO ``_dist_to_time(lap, dist)`` que el audio de los cues
    (render_pace_notes_track), asi el texto y el tono caen juntos.

    El pack ya viene filtrado por ``cue_config`` aguas arriba (build_pack), asi
    que aqui solo se rotulan los cues que de verdad suenan — incluido ``coast``
    (etiqueta "inercia") cuando el perfil lo habilita.

    La duracion de cada rotulo es ADAPTATIVA: dura hasta el siguiente cue (menos
    un respiro), acotada entre CUE_SUB_MIN_S y CUE_SUB_MAX_S. Reemplaza la
    ventana fija de 1.5 s de la #32, que apagaba el rotulo antes de tiempo.

    Args:
        pace_notes_dir: Carpeta del pack con ``metadata.json``.
        lap:            Vuelta del piloto (t=0 en la meta) para mapear distancia→tiempo.
        video_w:        Ancho del video final en px (PlayResX del .ass).
        video_h:        Alto del video final en px (escala fuentes y margen).
        hud_margin_v:   Margen inferior en px para despejar el HUD; si es None,
                        usa 0.34·alto (HUD abajo a escala tipica).

    Returns:
        str con el contenido .ass, o None si ninguna entrada cae dentro de la
        vuelta (nada que rotular).
    """
    metadata_path = Path(pace_notes_dir) / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    vw, vh = int(video_w), int(video_h)
    fs_cue = max(28, int(vh * 0.052))
    fs_name = max(16, int(vh * 0.030))
    fs_leg = max(14, int(vh * 0.026))
    mv_cue = hud_margin_v if hud_margin_v is not None else int(vh * 0.34)

    # 1) Recolectar (t, texto) de cada cue dentro de la vuelta. La duracion se
    # decide en el paso 2, cuando ya conocemos el tiempo del cue siguiente.
    cues = []
    used = []
    for entry in metadata.get("entries", []):
        dist = entry.get("distanceRoundTrack")
        if dist is None:
            continue
        t = _dist_to_time(lap, _as_float(dist))
        if t < 0 or t > lap.laptime:
            continue
        name, label = _split_cue_desc(entry.get("description", ""))
        color = CUE_SUB_COLORS.get(label, "&H00FFFFFF")
        if label not in used:
            used.append(label)
        text = "{\\c%s}%s  \\N{\\fs%d}%s{\\c&H00FFFFFF}" % (color, label, fs_name, name)
        cues.append((t, text))

    if not cues:
        return None

    # 2) Ventana adaptativa: cada rotulo dura hasta el siguiente cue (menos GAP),
    # nunca menos de MIN (legible) ni mas de MAX (no colgarlo en una recta).
    cues.sort(key=lambda c: c[0])
    dialogues = []
    for i, (t, text) in enumerate(cues):
        if i + 1 < len(cues):
            end = cues[i + 1][0] - CUE_SUB_GAP_S
        else:
            end = t + CUE_SUB_MAX_S
        end = max(t + CUE_SUB_MIN_S, min(end, t + CUE_SUB_MAX_S))
        end = min(end, lap.laptime)
        dialogues.append(
            "Dialogue: 0,%s,%s,Cue,,0,0,0,,%s"
            % (_ass_time(t - CUE_SUB_LEAD_S), _ass_time(end), text)
        )

    # Leyenda fija arriba-izquierda: solo las etiquetas que de verdad suenan,
    # en el orden canonico de CUE_SUB_COLORS.
    legend_items = [(lbl, CUE_SUB_COLORS[lbl]) for lbl in CUE_SUB_COLORS if lbl in used]
    legend_txt = "\\N".join(
        "{\\c%s}%s{\\c&H00FFFFFF}" % (color, lbl) for lbl, color in legend_items
    )
    legend = "Dialogue: 0,%s,%s,Legend,,0,0,0,,{\\pos(24,24)}LEYENDA DE SONIDOS\\N%s" % (
        _ass_time(0),
        _ass_time(lap.laptime),
        legend_txt,
    )

    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: %d\n"
        "PlayResY: %d\n"
        "WrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
        "Bold, Alignment, MarginL, MarginR, MarginV, BorderStyle, Outline, Shadow\n"
        "Style: Cue,Arial,%d,&H00FFFFFF,&H00000000,&H90000000,1,2,40,40,%d,1,3,1\n"
        "Style: Legend,Arial,%d,&H00FFFFFF,&H00000000,&H90000000,0,7,24,24,24,1,2,1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "%s\n%s\n"
    ) % (vw, vh, fs_cue, mv_cue, fs_leg, legend, "\n".join(dialogues))


def _read_wav_int16(path):
    import numpy as np

    with wave.open(str(path), "rb") as wav:
        if wav.getnchannels() != 1 or wav.getsampwidth() != 2:
            raise RuntimeError("WAV no soportado para preview: %s" % path)
        rate = wav.getframerate()
        raw = wav.readframes(wav.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0, rate


def _voice_text(row, name):
    loss = _as_float(row.get("time_lost", 0))
    flags = str(row.get("flags", ""))
    has_brake = "frenada" in flags
    has_vmin = "vmin" in flags
    if has_brake and has_vmin:
        return "%s. Frena mas tarde y sube el apex. Pierdes %.1f segundos." % (name, loss)
    if has_brake:
        return "%s. Frena mas tarde. Pierdes %.1f segundos." % (name, loss)
    if has_vmin:
        return "%s. Sube la velocidad en el apex. Pierdes %.1f segundos." % (name, loss)
    return "%s. Pierdes %.1f segundos." % (name, loss)


def _voice_for_lang(lang):
    voices = {
        "es-MX": "es-MX-JorgeNeural",
        "es-ES": "es-ES-AlvaroNeural",
        "en-US": "en-US-GuyNeural",
    }
    return voices.get(lang, lang)
