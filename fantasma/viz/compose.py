"""Compositor: superpone el overlay (canal alfa) sobre el video de grabación con ffmpeg."""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time

POSITIONS = {
    "top-left": ("0", "0"),
    "top-right": ("W-w", "0"),
    "bottom-left": ("0", "H-h"),
    "bottom-right": ("W-w", "H-h"),
    "top-center": ("(W-w)/2", "0"),
    "bottom-center": ("(W-w)/2", "H-h"),
    "center": ("(W-w)/2", "(H-h)/2"),
}


def _ffprobe_path(ffmpeg_path):
    probe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
    return probe if shutil.which(probe) else (shutil.which("ffprobe") or "")


def _video_fps(ffprobe, video_path):
    """Devuelve los fps del video como float, o 0 si no se puede obtener."""
    try:
        r = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=r_frame_rate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        line = r.stdout.strip()
        num, _, den = line.partition("/")
        return float(num) / float(den) if den else float(num)
    except Exception:
        return 0.0


def _total_frames(ffmpeg_path, video_path, lap_duration=None):
    """Estima frames totales para la barra de progreso.

    Usa siempre fps * duración — nb_frames del contenedor es frecuentemente
    incorrecto (mezcla pistas de audio, encoders con metadatos erróneos, etc.).
    """
    ffprobe = _ffprobe_path(ffmpeg_path)
    if not ffprobe:
        return 0
    try:
        if lap_duration:
            fps = _video_fps(ffprobe, video_path)
            return int(lap_duration * fps) if fps else 0
        r = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=r_frame_rate",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        lines = [l.strip() for l in r.stdout.splitlines() if l.strip()]
        fps_line = next((l for l in lines if "/" in l), None)
        dur_line = next((l for l in lines if "." in l), None)
        if fps_line and dur_line:
            num, _, den = fps_line.partition("/")
            fps = float(num) / float(den) if den else float(num)
            return int(float(dur_line) * fps)
    except Exception:
        pass
    return 0


def _probe_resolution(ffmpeg_path, video_path):
    """Devuelve (ancho, alto) del primer stream de video, o (0, 0) si falla."""
    ffprobe = _ffprobe_path(ffmpeg_path)
    if not ffprobe:
        return (0, 0)
    try:
        r = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height",
                "-of",
                "csv=p=0:s=x",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        w, h = r.stdout.strip().split("x")[:2]
        return (int(w), int(h))
    except Exception:
        return (0, 0)


def _caption_margin_v(position, video_h, overlay_h, scale):
    """Margen inferior (px) para que los subtitulos no tapen el HUD.

    Los subtitulos van anclados abajo-centro; si el HUD tambien esta abajo hay
    que subirlos por encima de su alto (overlay_h·scale). Si el HUD esta arriba,
    basta un margen chico.
    """
    gap = int(video_h * 0.03)
    if position.startswith("bottom"):
        hud_h = int(overlay_h * scale) if overlay_h else int(video_h * 0.30)
        return hud_h + gap
    return gap


def _nvenc_available(ffmpeg_path):
    """Devuelve True si h264_nvenc realmente funciona en este equipo.

    Grep de `-encoders` da falsos positivos: el encoder puede estar compilado
    en ffmpeg pero fallar en runtime si no hay GPU NVIDIA o `nvcuda.dll` no
    carga (p. ej. equipos sin tarjeta NVIDIA). Probamos con un encode real de
    1 frame contra un source sintético; solo devolvemos True si termina en 0.

    OJO con la resolución del source: NVENC rechaza frames demasiado pequeños
    (un 64x64 falla con "no capable devices found" / "Invalid surface" aunque
    la GPU SÍ sirva) → falso NEGATIVO que mandaba TODO a CPU en equipos con
    GPU real. Por eso el test usa 320x240, holgadamente por encima del mínimo.
    """
    try:
        r = subprocess.run(
            [
                ffmpeg_path,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "color=black:s=320x240:d=1",
                "-frames:v",
                "1",
                "-c:v",
                "h264_nvenc",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
        )
        return r.returncode == 0
    except Exception:
        return False


def _build_filter(position, scale, offset=0.0, subs_file=None):
    """Construye el filtro ffmpeg para superponer el overlay.

    offset solo se usa en modo legacy (sin recorte). En modo recorte el seek
    ya posicionó el video y el overlay empieza en t=0.

    subs_file: si se provee, quema ese .ass sobre el video ya compuesto. Debe
    ser un nombre RELATIVO (el proceso ffmpeg corre con cwd en su carpeta) para
    esquivar el infierno de escapar 'C:' en el filtro ass de Windows.
    """
    px, py = POSITIONS.get(position, POSITIONS["bottom-right"])
    steps = []
    cur = "1:v"

    if scale != 1.0:
        steps.append("[%s]scale=iw*%.6f:ih*%.6f[ov_s]" % (cur, scale, scale))
        cur = "ov_s"

    if offset != 0.0:
        steps.append("[%s]setpts=PTS+%.6f/TB[ov_d]" % (cur, offset))
        cur = "ov_d"

    if subs_file:
        steps.append("[0:v][%s]overlay=x=%s:y=%s[ovl]" % (cur, px, py))
        steps.append("[ovl]ass=%s[out]" % subs_file)
    else:
        steps.append("[0:v][%s]overlay=x=%s:y=%s[out]" % (cur, px, py))
    return ";".join(steps)


def _has_audio(ffprobe, video_path):
    if not ffprobe:
        return False
    try:
        r = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=index",
                "-of",
                "csv=p=0",
                video_path,
            ],
            capture_output=True,
            text=True,
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


SYNC_SIDECAR_SUFFIX = ".sync.json"


def sync_sidecar_path(video_path):
    """Ruta del sidecar de sincronía de un video compuesto."""
    return video_path + SYNC_SIDECAR_SUFFIX


def write_sync_sidecar(video_path, info):
    """Escribe junto al video un JSON con la identidad de la vuelta que lo originó.

    Sin este vínculo el mux de pace notes es una lotería: el panel ② del Paso 5
    sincroniza con la vuelta que esté cargada en memoria, y dos vueltas de
    laptime parecido (394.05 vs 394.07) tienen splits distintos — deriva de
    segundos (ADR 0024). Campos esperados en info: ``csv_path``, ``laptime``,
    ``offset``, ``lap_duration`` (los ausentes simplemente no se validan).
    """
    path = sync_sidecar_path(video_path)
    payload = {"format": "sgi-sync-v1"}
    payload.update(info)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def read_sync_sidecar(video_path):
    """Lee el sidecar de sincronía del video, o None si no existe o es ilegible.

    Un ``format`` desconocido también devuelve None: un lector v1 no debe
    validar contra campos cuya semántica pudo cambiar en una versión futura.
    """
    path = sync_sidecar_path(video_path)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("format") != "sgi-sync-v1":
        return None
    return data


def sync_sidecar_mismatch(video_path, lap, source_name=None, tolerance_s=0.1):
    """Compara el sidecar del video contra la vuelta cargada.

    Fuente única del criterio "¿es la vuelta correcta?": la usan el mux (para
    negarse) y la UI del Paso 5 (para avisar antes de apretar el botón) — si
    divergieran, el aviso y el rechazo se contradirían.

    Dos llaves: el laptime (± tolerance_s) y, si ambos lados la traen, la
    identidad del archivo de origen (dos vueltas distintas pueden durar casi
    igual; el laptime solo es un proxy). source_name es el nombre del CSV de
    la vuelta cargada (opcional).

    Returns:
        None si no hay sidecar o la vuelta corresponde; si no, un dict con
        ``expected`` (laptime del sidecar), ``actual`` (laptime de la vuelta),
        ``csv_path`` (origen registrado en el sidecar, puede ser None) y
        ``reason`` ("laptime" o "origen").
    """
    sidecar = read_sync_sidecar(video_path)
    if not sidecar or sidecar.get("laptime") is None:
        return None
    expected = float(sidecar["laptime"])
    info = {
        "expected": expected,
        "actual": lap.laptime,
        "csv_path": sidecar.get("csv_path"),
        "sidecar_path": sync_sidecar_path(video_path),
    }
    if abs(expected - lap.laptime) > tolerance_s:
        return {**info, "reason": "laptime"}
    recorded = sidecar.get("csv_path") or sidecar.get("lap_name")
    if source_name and recorded:
        if os.path.basename(str(recorded)) != os.path.basename(str(source_name)):
            return {**info, "reason": "origen"}
    return None


def check_sync_sidecar(video_path, lap, source_name=None, tolerance_s=0.1):
    """Valida que la vuelta cargada corresponda al video, si hay sidecar.

    Lanza RuntimeError con mensaje accionable si el sidecar delata otra vuelta
    (ver sync_sidecar_mismatch). Sin sidecar (video externo) no valida nada —
    comportamiento previo intacto.
    """
    mismatch = sync_sidecar_mismatch(video_path, lap, source_name, tolerance_s)
    if mismatch is None:
        return
    raise RuntimeError(
        "Este video se compuso con una vuelta de %.2f s (%s), pero la vuelta "
        "cargada dura %.2f s: los cues quedarían desincronizados. Carga esa "
        "vuelta en el Paso 1, o borra el archivo %s para forzar el mux."
        % (
            mismatch["expected"],
            mismatch["csv_path"] or "csv de origen desconocido",
            mismatch["actual"],
            mismatch["sidecar_path"],
        )
    )


def _audio_mix_filter(video_has_audio, vid_stream="0:a", cue_stream="2:a"):
    """Genera el filtro amix para mezclar audio del video con un WAV de cues.

    Args:
        video_has_audio: True si el video de entrada tiene pista de audio.
        vid_stream:      Especificador del stream de audio del video (default ``0:a``).
        cue_stream:      Especificador del stream de audio del WAV de cues (default ``2:a``).
    """
    if video_has_audio:
        # normalize=0: amix por defecto divide cada entrada entre el nº de inputs
        # (mezclar 2 = -6 dB a todo), lo que ENTIERRA los cues bajo el audio del
        # motor. Con normalize=0 se suman sin atenuar y el motor conserva su nivel;
        # el volumen del cue ya se controla al renderizar el WAV (parámetro volume).
        # Requiere ffmpeg >= 4.4 (la opción normalize de amix existe desde ahí).
        # Al sumar sin normalizar puede clipear en picos motor+tono coincidentes;
        # aceptable por lo breve del tono (WAV ya viene clippeado a [-1,1]). Si
        # aparece distorsión audible, bajar `volume` del cue o añadir un alimiter.
        return "[%s][%s]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[aout]" % (
            vid_stream,
            cue_stream,
        )
    return "[%s]anull[aout]" % cue_stream


def compose_video(
    video,
    overlay,
    output,
    position="bottom-right",
    offset=0.0,
    scale=1.0,
    lap_duration=None,
    progress=None,
    cue_audio=None,
    pace_notes_dir=None,
    pace_notes_volume=1.0,
    lap=None,
    sync_info=None,
    burn_cue_subs=False,
):
    """Superpone overlay con canal alfa sobre el video de grabación.

    Cuando lap_duration está disponible (recomendado) el output es un clip
    recortado que empieza en `offset` y dura exactamente `lap_duration`
    segundos — sin importar la duración del video original. Esto garantiza
    tiempos de compose consistentes independientemente del largo de la sesión.

    Sin lap_duration el comportamiento es el legado: offset demora el overlay
    via setpts y el output tiene la duración completa del video.

    Args:
        video:             Ruta al video de grabación (mp4, mov, mkv…).
        overlay:           Ruta al overlay con canal alfa (.webm VP9 o .mov ProRes).
        output:            Ruta del archivo de salida.
        position:          Posición del HUD en pantalla.
        offset:            Segundos desde el inicio del video hasta la vuelta.
        scale:             Factor de escala del HUD (1.0 = tamaño original).
        lap_duration:      Duración de la vuelta en segundos. Si se provee, el
                           output se recorta a exactamente esa duración.
        progress:          Callback progress(n_frames, total_frames) para UI.
        cue_audio:         WAV externo para mezclar en el audio (pasa directo).
        pace_notes_dir:    Carpeta del pack de Pace Notes. Si se provee junto
                           con `lap` y no hay `cue_audio` explícito, renderiza
                           el track y lo mezcla en el encode.
        pace_notes_volume: Volumen de los Pace Notes (default 1.0).
        lap:               Vuelta del piloto requerida para sincronizar los
                           Pace Notes por distancia.
        sync_info:         Dict con la identidad de la vuelta del video
                           (``csv_path``, ``laptime``…). Si se provee, al
                           terminar se escribe el sidecar ``<output>.sync.json``
                           que el mux del Paso 5 valida (ADR 0024).
        burn_cue_subs:     Si True (requiere ``pace_notes_dir`` + ``lap``),
                           quema en el video un rótulo por cada cue nombrando
                           el sonido (etiqueta + curva) sincronizado con su
                           tono, más una leyenda de colores (ADR 0027).

    Returns:
        Dict con keys ``path``, ``encoder`` y ``duration_s``.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        import platform as _platform

        _sys = _platform.system()
        _cmd = (
            "winget install Gyan.FFmpeg"
            if _sys == "Windows"
            else "brew install ffmpeg"
            if _sys == "Darwin"
            else "sudo apt install ffmpeg"
        )
        raise RuntimeError("ffmpeg no encontrado en PATH — instálalo con: %s" % _cmd)

    out_dir = os.path.dirname(output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Pace notes: si se provee pace_notes_dir + lap y no hay cue_audio explícito,
    # renderizamos el track en un tmpdir local. La variable _pn_tmpdir mantiene la
    # referencia viva durante todo el encode (el directorio se borra al salir).
    _pn_tmpdir = None
    if pace_notes_dir and lap is not None and cue_audio is None:
        from .pacenotes import render_pace_notes_track as _render_pn

        _pn_tmpdir = tempfile.TemporaryDirectory()
        cue_audio = os.path.join(_pn_tmpdir.name, "pace_notes_preview.wav")
        _render_pn(pace_notes_dir, lap, cue_audio, volume=pace_notes_volume)

    # Subtitulos de cues (ADR 0027): rotulo por sonido, quemado en el mismo
    # encode. Necesita pace_notes_dir + lap. El .ass se referencia por nombre
    # RELATIVO y ffmpeg corre con cwd en su carpeta (esquiva el escape de 'C:'
    # en Windows). _subs_tmpdir reusa el de pace notes si existe.
    #
    # Los tiempos del .ass son relativos al inicio de la vuelta (t=0), que es
    # como queda el clip en modo recorte (lap_duration). En modo legacy (video
    # completo, sin recorte) el video NO empieza en la meta, asi que el texto
    # caeria adelantado por `offset` s; hoy solo la UI expone los subtitulos y
    # siempre pasa lap_duration cuando hay vuelta, asi que ese modo no se alcanza.
    _subs_tmpdir = None
    _subs_file = None
    _run_cwd = None
    if burn_cue_subs and pace_notes_dir and lap is not None:
        from .pacenotes import build_cue_ass

        vw, vh = _probe_resolution(ffmpeg, video)
        if not vw or not vh:
            vw, vh = 1920, 1080
        _, oh = _probe_resolution(ffmpeg, overlay)
        mv = _caption_margin_v(position, vh, oh, scale)
        ass_txt = build_cue_ass(pace_notes_dir, lap, vw, vh, hud_margin_v=mv)
        if ass_txt:
            _subs_tmpdir = _pn_tmpdir or tempfile.TemporaryDirectory()
            _subs_file = "cue_subs.ass"
            with open(os.path.join(_subs_tmpdir.name, _subs_file), "w", encoding="utf-8") as _f:
                _f.write(ass_txt)
            _run_cwd = _subs_tmpdir.name

    use_nvenc = _nvenc_available(ffmpeg)
    if use_nvenc:
        video_enc = ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "18", "-b:v", "0"]
    else:
        video_enc = ["-c:v", "libx264", "-crf", "18", "-preset", "fast"]

    n_frames = _total_frames(ffmpeg, video, lap_duration) if progress else 0

    cue_inputs = ["-i", cue_audio] if cue_audio else []
    audio_maps = ["-map", "0:a?"]
    audio_filter = ""
    if cue_audio:
        ffprobe = _ffprobe_path(ffmpeg)
        audio_filter = ";" + _audio_mix_filter(_has_audio(ffprobe, video))
        audio_maps = ["-map", "[aout]"]

    _t0 = time.time()

    if lap_duration:
        # Modo recorte: seek rápido al offset, output limitado a la vuelta.
        # El overlay empieza en t=0 del clip resultante (no necesita setpts).
        fc = _build_filter(position, scale, offset=0.0, subs_file=_subs_file)
        cmd = [
            ffmpeg,
            "-y",
            "-ss",
            "%.3f" % offset,
            "-i",
            video,
            "-i",
            overlay,
            *cue_inputs,
            "-filter_complex",
            fc + audio_filter,
            "-map",
            "[out]",
            *audio_maps,
            *video_enc,
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-t",
            "%.3f" % lap_duration,
            output,
        ]
    else:
        # Modo legado: overlay demora via setpts, video completo.
        fc = _build_filter(position, scale, offset, subs_file=_subs_file)
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            video,
            "-i",
            overlay,
            *cue_inputs,
            "-filter_complex",
            fc + audio_filter,
            "-map",
            "[out]",
            *audio_maps,
            *video_enc,
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            output,
        ]

    try:
        if progress:
            cmd_p = [cmd[0], "-progress", "pipe:1", "-nostats"] + cmd[1:]
            pat = re.compile(r"^frame=(\d+)")
            # stderr a un archivo temporal para poder reportar el motivo real del
            # fallo (antes iba a DEVNULL y solo quedaba un exit code críptico).
            err_f = tempfile.TemporaryFile(mode="w+")
            proc = subprocess.Popen(
                cmd_p, stdout=subprocess.PIPE, stderr=err_f, text=True, cwd=_run_cwd
            )
            try:
                for line in proc.stdout:
                    m = pat.match(line.strip())
                    if m and n_frames > 0:
                        f = int(m.group(1))
                        progress(f, n_frames)
            except BaseException:
                proc.kill()
                proc.wait()
                err_f.close()
                raise
            else:
                proc.wait()
            if proc.returncode != 0:
                err_f.seek(0)
                tail = "".join(err_f.readlines()[-15:]).strip()
                err_f.close()
                raise RuntimeError(
                    "ffmpeg falló (código %d). Últimas líneas:\n%s" % (proc.returncode, tail)
                )
            err_f.close()
        else:
            subprocess.run(cmd, check=True, cwd=_run_cwd)
    finally:
        if _pn_tmpdir is not None:
            _pn_tmpdir.cleanup()
        # Si los subtitulos usaron su propio tmpdir (no el de pace notes), limpiarlo.
        if _subs_tmpdir is not None and _subs_tmpdir is not _pn_tmpdir:
            _subs_tmpdir.cleanup()

    if sync_info is not None:
        info = dict(sync_info)
        info.setdefault("offset", offset)
        info.setdefault("lap_duration", lap_duration)
        write_sync_sidecar(output, info)
    else:
        # Sin identidad de vuelta, un sidecar de una corrida ANTERIOR al mismo
        # output quedaria huerfano y validaria el video nuevo contra la vuelta
        # vieja — falsa luz verde (Reviewer). Se elimina.
        try:
            os.remove(sync_sidecar_path(output))
        except OSError:
            pass

    _enc_name = "h264_nvenc" if use_nvenc else "libx264"
    return {"path": output, "encoder": _enc_name, "duration_s": round(time.time() - _t0, 1)}


def mux_pace_notes_into_video(video, pace_notes_dir, lap, output, volume=1.0, source_name=None):
    """Aplica el audio de pace notes a un video ya existente sin re-encodear el video.

    Copia el stream de video intacto (``-c:v copy``) y solo mezcla o añade el
    audio de pace notes generado por ``render_pace_notes_track``. Mucho mas
    rapido que ``compose_video`` porque no re-encodea el video.

    Args:
        video:          Ruta al video existente (mp4, mov, mkv...).
        pace_notes_dir: Carpeta del pack de pace notes con ``metadata.json``.
        lap:            Vuelta del piloto para sincronizar cues por distancia.
        output:         Ruta del video de salida.
        volume:         Volumen de los pace notes (default 1.0).
        source_name:    Nombre del CSV de la vuelta cargada (opcional; refuerza
                        la validación del sidecar comparando el origen).

    Returns:
        str: Ruta del video de salida (igual a ``output``).

    Raises:
        RuntimeError: si el video tiene sidecar de sincronía (ADR 0024) y la
            vuelta cargada no corresponde (laptime u origen distintos).
    """
    check_sync_sidecar(video, lap, source_name=source_name)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        import platform as _platform

        _sys = _platform.system()
        _cmd = (
            "winget install Gyan.FFmpeg"
            if _sys == "Windows"
            else "brew install ffmpeg"
            if _sys == "Darwin"
            else "sudo apt install ffmpeg"
        )
        raise RuntimeError("ffmpeg no encontrado en PATH — instálalo con: %s" % _cmd)

    out_dir = os.path.dirname(output)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    from .pacenotes import render_pace_notes_track as _render_pn

    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, "pace_notes_mux.wav")
        _render_pn(pace_notes_dir, lap, wav_path, volume=volume)

        ffprobe = _ffprobe_path(ffmpeg)
        video_has_audio = _has_audio(ffprobe, video)

        if video_has_audio:
            # Mezcla audio del video original con el WAV de pace notes.
            # Inputs: 0 = video, 1 = WAV. Reusa _audio_mix_filter con indices de mux.
            audio_filter = _audio_mix_filter(True, vid_stream="0:a", cue_stream="1:a")
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                video,
                "-i",
                wav_path,
                "-filter_complex",
                audio_filter,
                "-map",
                "0:v",
                "-map",
                "[aout]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                output,
            ]
        else:
            # El video no tiene audio: añade el WAV como nueva pista de audio.
            cmd = [
                ffmpeg,
                "-y",
                "-i",
                video,
                "-i",
                wav_path,
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                output,
            ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            tail = "\n".join((result.stderr or "").splitlines()[-10:])
            hint = ""
            if "normalize" in tail.lower():
                # La opcion normalize de amix existe desde ffmpeg 4.4; en
                # versiones previas el filtro truena con un error criptico.
                hint = " Pista: la mezcla usa amix normalize=0, que requiere ffmpeg 4.4 o mayor."
            raise RuntimeError(
                "ffmpeg falló al mezclar el audio (código %d).%s Últimas líneas:\n%s"
                % (result.returncode, hint, tail)
            )

    return output
