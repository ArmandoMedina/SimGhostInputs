"""CLI de SimGhostInputs: fantasma laps | detect | compare"""

import argparse
import csv
import json
import os
import sys
import tempfile

from . import importers
from .core.compare import compare
from .core.corners import detect_corners, extract_milestones
from .core.normalize import fastest_lap
from .viz.report import write_outputs


def _overlay_progress(n, total, status=None):
    """Callback de progreso para render_overlay.

    Acepta el kwarg ``status`` con que overlay.py lo invoca
    (``progress(enc, n_frames, status="Codificando video… frame N / M")``)
    y el piloto sin él (para homologar con RenderJob.progress_cb de ng_helpers.py).
    """
    pct = 100.0 * n / total if total else 0
    print("  frame %d/%d (%.0f%%)" % (n, total, pct))


def _parse_map(pairs):
    if not pairs:
        return None
    out = {}
    for p in pairs:
        k, _, v = p.partition("=")
        out[k] = v
    return out


def _load_lap(path, column_map=None, lap_index=None):
    laps = importers.load_laps(path, column_map)
    lap = laps[lap_index] if lap_index is not None else fastest_lap(laps)
    return laps, lap


def _require_distance(lap, role):
    if not lap.has("dist"):
        raise ValueError(
            "La vuelta de %s no tiene canal de distancia. En MoTeC i2 re-exporta el CSV "
            "incluyendo el canal 'Distance': es el eje maestro de comparacion del que "
            "dependen detect, compare y overlay." % role
        )


def cmd_laps(args):
    laps, best = _load_lap(args.file, _parse_map(args.map))
    print("Archivo: %s" % args.file)
    for k in ("Venue", "Vehicle", "Driver"):
        if k in best.meta:
            print("  %s: %s" % (k, best.meta[k]))
    if not any(l.has("dist") for l in laps):
        print(
            "aviso: este CSV no incluye el canal de distancia (longitud 0m). "
            "SimGhostInputs compara por distancia: re-exporta desde MoTeC i2 marcando "
            "'Include Distance Data' o detect/compare/overlay no podran ejecutarse.",
            file=sys.stderr,
        )
    print("\n  #  duracion   longitud   completa")
    for i, l in enumerate(laps):
        mark = " <- mas rapida" if l is best else ""
        print(
            "%4d  %7.2fs  %7.0fm   %s%s"
            % (i, l.laptime, l.length, "si" if l.meta.get("is_complete") else "no", mark)
        )


def cmd_detect(args):
    _, lap = _load_lap(args.file, _parse_map(args.map), args.lap)
    events, _ = detect_corners(lap)
    corners = extract_milestones(lap, events)
    print("Vuelta: %.2fs, %.0fm — %d curvas detectadas" % (lap.laptime, lap.length, len(corners)))
    for c in corners:
        ap = c["milestones"]["apex"]
        print(
            "  %s %5dm  %-5s v=%3d  %s%s"
            % (
                c["id"],
                ap["d"],
                c.get("direction", "?"),
                ap["v"],
                c["kind"],
                "  overlap %dm" % c["overlap_m"] if c.get("overlap_m") else "",
            )
        )
    if args.output:
        import os

        os.makedirs(args.output, exist_ok=True)
        path = os.path.join(args.output, "corners_detected.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"corners": corners}, f, indent=1, ensure_ascii=False)
        print("-> %s" % path)


def cmd_compare(args):
    _, ref = _load_lap(args.reference, _parse_map(args.map))
    _, drv = _load_lap(args.driver, _parse_map(args.map), args.lap)
    _require_distance(ref, "referencia")
    _require_distance(drv, "piloto")
    corners = None
    if args.corners:
        with open(args.corners, encoding="utf-8") as f:
            corners = json.load(f).get("corners")
    if corners is None:
        ev, _ = detect_corners(ref)
        corners = extract_milestones(ref, ev)
    trace, rows, summary = compare(ref, drv, step=args.step, corners=corners)
    meta = {"Referencia": args.reference, "Piloto": args.driver}
    report = write_outputs(args.output, trace, rows, summary, meta)
    if not args.no_charts:
        from .viz.charts import render_charts

        charts = render_charts(trace, rows, corners, args.output, top=args.charts_top)
        for c in charts:
            print("-> %s" % c)
    print(
        "Referencia: %.3fs | Piloto: %.3fs | Delta: %+.3fs"
        % (
            summary["ref_laptime"],
            summary["drv_laptime"],
            summary["drv_laptime"] - summary["ref_laptime"],
        )
    )
    losses = sorted(
        [r for r in rows if r["time_lost"] > 0], key=lambda r: r["time_lost"], reverse=True
    )
    for r in losses[:3]:
        print("  mayor perdida: %s (m%d) %+.3fs" % (r["name"], r["apex_d"], r["time_lost"]))
    for aviso in summary.get("avisos", []):
        print("aviso: %s" % aviso, file=sys.stderr)
    print("-> %s" % report)


def cmd_overlay(args):
    import os

    from .viz.overlay import render_overlay

    ref_laps, ref = _load_lap(args.reference, _parse_map(args.map))
    drv_laps, drv = _load_lap(args.driver, _parse_map(args.map), args.lap)
    _require_distance(ref, "referencia")
    _require_distance(drv, "piloto")

    corners = None
    if args.corners:
        with open(args.corners, encoding="utf-8") as f:
            corners = json.load(f).get("corners")
    else:
        ev, _ = detect_corners(ref)
        corners = extract_milestones(ref, ev)

    os.makedirs(args.output, exist_ok=True)

    if args.all_laps:
        complete = [l for l in drv_laps if l.meta.get("is_complete")]
        if complete:
            laps_to_render = complete
        else:
            maxlen = max(l.length for l in drv_laps)
            laps_to_render = [l for l in drv_laps if l.length >= maxlen * 0.9]
        webms = []
        for i, lap in enumerate(laps_to_render):
            lap_dir = os.path.join(args.output, "lap_%02d" % i)
            os.makedirs(lap_dir, exist_ok=True)
            print("Renderizando vuelta %d/%d (%.2fs)…" % (i + 1, len(laps_to_render), lap.laptime))
            out = render_overlay(
                ref,
                lap,
                corners,
                lap_dir,
                fps=args.fps,
                fmt=args.format,
                t_start=args.start,
                t_end=args.end,
                progress=_overlay_progress,
            )
            webms.append(out)
            print("-> %s" % out)

        if args.format != "png" and len(webms) > 1:
            _concat_videos(webms, os.path.join(args.output, "overlay_all.webm"), args.format)
            print("-> %s" % os.path.join(args.output, "overlay_all.webm"))
    else:
        out = render_overlay(
            ref,
            drv,
            corners,
            args.output,
            fps=args.fps,
            fmt=args.format,
            t_start=args.start,
            t_end=args.end,
            progress=_overlay_progress,
        )
        print("-> %s" % out)


def _concat_videos(paths, output, fmt):
    """Concatena varios archivos de video con ffmpeg."""
    import os
    import shutil
    import subprocess
    import tempfile

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("aviso: ffmpeg no disponible, no se pudo concatenar")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        for p in paths:
            f.write("file '%s'\n" % p.replace("\\", "/"))
        list_file = f.name
    try:
        subprocess.run(
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output],
            check=True,
            capture_output=True,
        )
    finally:
        os.unlink(list_file)


def cmd_compose(args):
    from .viz.compose import compose_video

    offset = args.offset
    lap = None

    if args.driver:
        try:
            _, lap = _load_lap(
                args.driver,
                _parse_map(getattr(args, "map", None)),
                getattr(args, "lap_idx", None),
            )
        except Exception as e:
            print("error cargando telemetria: %s" % e, file=sys.stderr)
            return 1

    if getattr(args, "auto_sync", False):
        if lap is None:
            print("error: --auto-sync requiere --driver <archivo_telemetria>", file=sys.stderr)
            return 1
        print("Detectando offset de sincronizacion…")
        try:
            from .viz.sync import (
                _MIN_SYNC_Z,
                sync_candidates,
                sync_gray_zone_warning,
                validate_offset,
            )

            result = sync_candidates(args.video, lap)
        except ImportError as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
        except Exception as e:
            print("error en auto-sync: %s" % e, file=sys.stderr)
            return 1

        cands = result["candidates"]
        if not cands or cands[0]["z"] < _MIN_SYNC_Z:
            print(
                "error en auto-sync: correlacion insuficiente; el video no parece "
                "corresponder a la vuelta. Usa --offset manual.",
                file=sys.stderr,
            )
            return 1

        if result["ambiguous"]:
            # ADR 0008: el video tiene varias vueltas parecidas; no adivinar, preguntar.
            print("\nEl video parece tener varias vueltas. Candidatos (minuto del video):")
            for i, c in enumerate(cands, 1):
                print("  %d) %s   (calidad %.1f σ)" % (i, c["mmss"], c["z"]))
            sel = input("¿Cual corresponde a tu vuelta? [1-%d] " % len(cands)).strip()
            try:
                chosen = cands[int(sel) - 1]
            except (ValueError, IndexError):
                print("error: seleccion invalida.", file=sys.stderr)
                return 1
        else:
            chosen = cands[0]

        offset = chosen["offset"]
        gz = sync_gray_zone_warning(chosen["z"])
        if gz:
            # Zona gris (ADR 0008): se acepta pero podria ser otra sesion; avisar.
            print("  aviso: %s" % gz, file=sys.stderr)
        pause_t = validate_offset(result, offset, lap)
        if pause_t is not None:
            pm, ps = int(pause_t) // 60, int(pause_t) % 60
            print(
                "  aviso: pausa detectada en el audio en %d:%02d dentro de la vuelta." % (pm, ps),
                file=sys.stderr,
            )
        print("  -> offset: %.3f s  (z=%.1f σ)" % (offset, chosen["z"]))

    lap_duration = lap.laptime if lap is not None else None
    if lap_duration:
        print("  -> recortando vuelta: %.2f s" % lap_duration)

    output = args.output
    if not output:
        base = os.path.splitext(os.path.basename(args.video))[0]
        output = os.path.join(os.path.dirname(args.video) or ".", base + "_composed.mp4")
    if args.pace_notes_dir and lap is None:
        print(
            "error: --pace-notes-dir requiere --driver para sincronizar por distancia",
            file=sys.stderr,
        )
        return 1

    if args.pace_notes_dir:
        from .viz.pacenotes import render_pace_notes_track

        with tempfile.TemporaryDirectory() as tmp:
            cue_audio = os.path.join(tmp, "pace_notes_preview.wav")
            render_pace_notes_track(
                args.pace_notes_dir,
                lap,
                cue_audio,
                volume=args.pace_notes_volume,
            )
            out = compose_video(
                args.video,
                args.overlay,
                output,
                position=args.position,
                offset=offset,
                scale=args.scale,
                lap_duration=lap_duration,
                cue_audio=cue_audio,
            )
    else:
        out = compose_video(
            args.video,
            args.overlay,
            output,
            position=args.position,
            offset=offset,
            scale=args.scale,
            lap_duration=lap_duration,
        )
    print("-> %s  [%s, %.0fs]" % (out["path"], out["encoder"], out["duration_s"]))


def cmd_pacenotes(args):
    from .viz.pacenotes import build_pack

    data = _load_corners_json(args.corners)
    corners = data["corners"]
    rows = _load_compare_csv(args.compare)
    track_name, outdir = _resolve_pacenotes_outdir(data, args.output_dir)
    freqs = {"brake": args.brake_freq, "apex": args.apex_freq, "gas": args.gas_freq}
    result = build_pack(
        rows,
        corners,
        outdir,
        mode=args.mode,
        top=args.top,
        lang=args.lang,
        freqs=freqs,
        duration=args.tone_duration,
        volume=args.volume,
        smart=not args.legacy_all_tones,
        track_name=track_name,
    )
    curves = _count_lost_curves(rows, args.top)
    print("✓ %d curvas, %d archivos en %s" % (curves, len(result["files"]), result["outdir"]))


def _load_corners_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"corners": data}
    corners = data.get("corners")
    if corners is None:
        raise ValueError("el archivo de corners no contiene la clave 'corners'")
    return data


def _load_compare_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _resolve_pacenotes_outdir(corners_data, output_dir_arg):
    """Devuelve (track_name, outdir). track_name puede ser None si se usa --output-dir."""
    if output_dir_arg:
        track = corners_data.get("track") or corners_data.get("trackName")
        return track, output_dir_arg
    track = corners_data.get("track") or corners_data.get("trackName")
    if not track:
        track = input("Nombre exacto de pista en CrewChief/AMS2: ").strip()
    if not track:
        raise ValueError("se requiere nombre de pista o --output-dir")
    outdir = os.path.join(
        os.path.expanduser("~"),
        "Documents",
        "CrewChiefV4",
        "pace_notes",
        "ams2",
        track,
    )
    return track, outdir


def _count_lost_curves(rows, top):
    losses = []
    for row in rows:
        try:
            loss = float(row.get("time_lost", 0) or 0)
        except ValueError:
            loss = 0
        if loss > 0:
            losses.append(loss)
    return min(len(losses), top)


def cmd_wear(args):
    """Medidor de desgaste de goma acumulable de un stint (ver ADR 0004 y 0009).

    Calcula la carga de deslizamiento (slip_load) de cada vuelta completa, la
    acumula y proyecta cuántas vueltas faltan para el reventón, estilo medidor de
    gasolina. La carga es una cantidad extensiva (aditiva entre vueltas), no el
    promedio slip_index — así es consistente con el acumulado del overlay (ADR 0009).
    """
    from .core import wear

    laps = importers.load_laps(args.file, _parse_map(args.map))
    complete = [l for l in laps if l.meta.get("is_complete")] or laps

    print("Archivo: %s" % args.file)
    print("\n  vuelta   carga (slip_load)")
    rates = []
    for i, lap in enumerate(complete):
        r = wear.slip_load(lap)
        rates.append(r)
        print("  %4d     %s" % (i, "—" if r is None else "%.2f" % r))

    th = {"yellow": args.yellow, "red": args.red, "burst": args.burst}
    b = wear.wear_budget(rates, th, recent_n=args.recent_n)
    if b is None:
        print("\nSin desgaste medible (¿faltan los canales de velocidad de rueda?).")
        return

    print("\nCarga acumulada: %.2f  [%s]" % (b["cumulative"], b["status"].upper()))
    print("Rate reciente: %.2f / vuelta  (últimas %d)" % (b["rate_recent"], args.recent_n))
    if "laps_to_burst" in b:
        print(
            "Vueltas estimadas a cambio: ~%.1f  (total del juego de gomas ~%.1f vueltas)"
            % (b["laps_to_burst"], b["est_total_laps"])
        )
    shown = " | ".join(
        "%s %g" % (k, v)
        for k, v in (("amarillo", args.yellow), ("rojo", args.red), ("reventón", args.burst))
        if v is not None
    )
    if shown:
        print("Umbrales: " + shown)
    else:
        print(
            "Umbrales: sin definir — la carga escala con la longitud del circuito; "
            "calíbralos con tus datos reales (--burst, --red, --yellow)."
        )


def _force_utf8_console():
    """Evita UnicodeEncodeError al imprimir en la consola de Windows.

    En Windows la consola usa cp1252 por defecto, y los avisos que incluyen
    caracteres como 'σ' (calidad de sincronía, "z=5.5 σ") lanzan
    UnicodeEncodeError ('charmap' codec can't encode character '\\u03c3') —
    visto en `fantasma compose` con el aviso de correlación moderada. Forzar
    UTF-8 en stdout/stderr lo evita sin perder el carácter. Silencioso si el
    stream no soporta reconfigure (p. ej. redirigido a un objeto sin el método).
    """
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main(argv=None):
    _force_utf8_console()
    p = argparse.ArgumentParser(
        prog="fantasma",
        description="Compara tus inputs contra una vuelta de referencia, por distancia.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("laps", help="listar las vueltas de un archivo")
    sp.add_argument("file")
    sp.add_argument("--map", action="append", help="columna=canal para CSV generico")
    sp.set_defaults(func=cmd_laps)

    sp = sub.add_parser("detect", help="detectar curvas e hitos de la vuelta mas rapida")
    sp.add_argument("file")
    sp.add_argument("--lap", type=int, help="indice de vuelta (por defecto: la mas rapida)")
    sp.add_argument("--map", action="append")
    sp.add_argument("-o", "--output", help="carpeta de salida para corners_detected.json")
    sp.set_defaults(func=cmd_detect)

    sp = sub.add_parser("compare", help="comparar piloto vs referencia")
    sp.add_argument("--reference", required=True)
    sp.add_argument("--driver", required=True)
    sp.add_argument(
        "--lap", type=int, help="indice de vuelta del piloto (por defecto: la mas rapida)"
    )
    sp.add_argument("--corners", help="corners.json con nombres/tolerancias (opcional)")
    sp.add_argument("--step", type=float, default=5.0, help="rejilla de distancia en m (default 5)")
    sp.add_argument("--map", action="append")
    sp.add_argument("-o", "--output", default="salida", help="carpeta de salida")
    sp.add_argument("--no-charts", action="store_true", help="no generar graficas")
    sp.add_argument(
        "--charts-top", type=int, default=5, help="graficas de las N curvas con mayor perdida"
    )
    sp.set_defaults(func=cmd_compare)

    sp = sub.add_parser("overlay", help="video HUD transparente para superponer sobre tu grabacion")
    sp.add_argument("--reference", required=True)
    sp.add_argument("--driver", required=True)
    sp.add_argument(
        "--lap", type=int, help="indice de vuelta del piloto (por defecto: la mas rapida)"
    )
    sp.add_argument(
        "--all-laps",
        action="store_true",
        help="renderiza todas las vueltas completas y las concatena en overlay_all.webm",
    )
    sp.add_argument("--corners", help="corners.json con nombres (opcional)")
    sp.add_argument("--fps", type=int, default=30)
    sp.add_argument(
        "--format",
        choices=["prores", "webm", "png"],
        default="webm",
        help="webm=VP9 con alfa (default), prores=.mov 4444 con alfa, png=solo frames",
    )
    sp.add_argument("--start", type=float, default=0.0, help="segundo inicial de la vuelta")
    sp.add_argument("--end", type=float, help="segundo final (por defecto: vuelta completa)")
    sp.add_argument("--map", action="append")
    sp.add_argument("-o", "--output", default="salida", help="carpeta de salida")
    sp.set_defaults(func=cmd_overlay)

    sp = sub.add_parser("wear", help="medidor de desgaste de goma acumulable de un stint")
    sp.add_argument("file")
    sp.add_argument(
        "--yellow",
        type=float,
        default=None,
        help="umbral amarillo (empírico; sin default, la carga escala con el circuito)",
    )
    sp.add_argument("--red", type=float, default=None, help="umbral rojo (empírico; sin default)")
    sp.add_argument(
        "--burst", type=float, default=None, help="umbral de reventón (empírico; sin default)"
    )
    sp.add_argument(
        "--recent-n",
        type=int,
        default=1,
        dest="recent_n",
        help="vueltas finales a promediar para proyectar (default 1)",
    )
    sp.add_argument("--map", action="append", help="columna=canal para CSV generico")
    sp.set_defaults(func=cmd_wear)

    sp = sub.add_parser(
        "compose", help="superponer overlay sobre tu grabacion y generar el video final"
    )
    sp.add_argument("--video", required=True, help="grabacion de la vuelta (.mp4, .mov, .mkv…)")
    sp.add_argument("--overlay", required=True, help="overlay con canal alfa (.webm o .mov)")
    sp.add_argument(
        "--position",
        choices=[
            "top-left",
            "top-right",
            "bottom-left",
            "bottom-right",
            "top-center",
            "bottom-center",
            "center",
        ],
        default="bottom-right",
        help="posicion del HUD en el video (default: bottom-right)",
    )
    sp.add_argument(
        "--offset",
        type=float,
        default=0.0,
        help="segundos de delay del overlay — util si el video arranca antes de la vuelta",
    )
    sp.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="factor de escala del HUD (ej. 0.5 = mitad de tamano; default: 1.0)",
    )
    sp.add_argument("-o", "--output", help="archivo de salida (default: <video>_composed.mp4)")
    sp.add_argument(
        "--auto-sync",
        action="store_true",
        help="detectar offset automaticamente con correlacion audio vs telemetria (requiere scipy)",
    )
    sp.add_argument("--driver", help="archivo de telemetria del piloto (necesario con --auto-sync)")
    sp.add_argument(
        "--lap-idx",
        type=int,
        dest="lap_idx",
        help="indice de vuelta del piloto para --auto-sync (por defecto: la mas rapida)",
    )
    sp.add_argument(
        "--map", action="append", help="columna=canal para CSV generico con --auto-sync"
    )
    sp.add_argument(
        "--pace-notes-dir",
        help="pack de Pace Notes para mezclar sus sonidos en el video (preview)",
    )
    sp.add_argument(
        "--pace-notes-volume",
        type=float,
        default=1.0,
        help="volumen de los sonidos de Pace Notes en el preview (default: 1.0)",
    )
    sp.set_defaults(func=cmd_compose)

    sp = sub.add_parser("pacenotes", help="generar pack de Pace Notes para CrewChief")
    sp.add_argument("--corners", required=True, help="corners.json generado por fantasma detect")
    sp.add_argument(
        "--compare", required=True, help="corners_compare.csv generado por fantasma compare"
    )
    sp.add_argument("--top", type=int, default=5, help="solo las N curvas con mayor perdida")
    sp.add_argument("--mode", choices=["tones", "voice", "both"], default="tones")
    sp.add_argument("--lang", default="es-MX", help="idioma/voz para mode voice o both")
    sp.add_argument("--output-dir", help="directorio destino del pack")
    sp.add_argument("--brake-freq", type=float, default=880)
    sp.add_argument("--apex-freq", type=float, default=440)
    sp.add_argument("--gas-freq", type=float, default=220)
    sp.add_argument("--tone-duration", type=float, default=0.12)
    sp.add_argument("--volume", type=float, default=0.8)
    sp.add_argument(
        "--legacy-all-tones",
        action="store_true",
        help="genera todos los hitos pedidos sin plan anti-saturacion",
    )
    sp.set_defaults(func=cmd_pacenotes)

    args = p.parse_args(argv)
    try:
        return args.func(args) or 0
    except Exception as e:
        print("error: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
