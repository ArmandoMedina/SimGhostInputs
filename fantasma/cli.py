"""CLI de SimGhostInputs: fantasma laps | detect | compare"""
import argparse
import json
import sys

from . import importers
from .core.normalize import split_laps, fastest_lap
from .core.corners import detect_corners, extract_milestones
from .core.compare import compare
from .viz.report import write_outputs


def _parse_map(pairs):
    if not pairs:
        return None
    out = {}
    for p in pairs:
        k, _, v = p.partition("=")
        out[k] = v
    return out


def _load_lap(path, column_map=None, lap_index=None):
    outing = importers.load(path, column_map)
    laps = split_laps(outing)
    if lap_index is not None:
        lap = laps[lap_index]
    else:
        lap = fastest_lap(laps)
    return outing, laps, lap


def cmd_laps(args):
    outing, laps, best = _load_lap(args.file, _parse_map(args.map))
    print("Archivo: %s" % args.file)
    for k in ("Venue", "Vehicle", "Driver"):
        if k in outing.meta:
            print("  %s: %s" % (k, outing.meta[k]))
    print("\n  #  duracion   longitud   completa")
    for i, l in enumerate(laps):
        mark = " <- mas rapida" if l is best else ""
        print("%4d  %7.2fs  %7.0fm   %s%s" % (
            i, l.laptime, l.length, "si" if l.meta.get("is_complete") else "no", mark))


def cmd_detect(args):
    _, _, lap = _load_lap(args.file, _parse_map(args.map), args.lap)
    events, _ = detect_corners(lap)
    corners = extract_milestones(lap, events)
    print("Vuelta: %.2fs, %.0fm — %d curvas detectadas" % (lap.laptime, lap.length, len(corners)))
    for c in corners:
        ap = c["milestones"]["apex"]
        print("  %s %5dm  %-5s v=%3d  %s%s" % (
            c["id"], ap["d"], c.get("direction", "?"), ap["v"], c["kind"],
            "  overlap %dm" % c["overlap_m"] if c.get("overlap_m") else ""))
    if args.output:
        import os
        os.makedirs(args.output, exist_ok=True)
        path = os.path.join(args.output, "corners_detected.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"corners": corners}, f, indent=1, ensure_ascii=False)
        print("-> %s" % path)


def cmd_compare(args):
    _, _, ref = _load_lap(args.reference, _parse_map(args.map))
    _, _, drv = _load_lap(args.driver, _parse_map(args.map), args.lap)
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
    print("Referencia: %.3fs | Piloto: %.3fs | Delta: %+.3fs" % (
        summary["ref_laptime"], summary["drv_laptime"],
        summary["drv_laptime"] - summary["ref_laptime"]))
    losses = sorted([r for r in rows if r["time_lost"] > 0],
                    key=lambda r: r["time_lost"], reverse=True)
    for r in losses[:3]:
        print("  mayor perdida: %s (m%d) %+.3fs" % (r["name"], r["apex_d"], r["time_lost"]))
    print("-> %s" % report)


def cmd_overlay(args):
    import os
    from .viz.overlay import render_overlay

    _, ref_laps, ref = _load_lap(args.reference, _parse_map(args.map))
    _, drv_laps, drv = _load_lap(args.driver, _parse_map(args.map), args.lap)

    corners = None
    if args.corners:
        with open(args.corners, encoding="utf-8") as f:
            corners = json.load(f).get("corners")
    else:
        ev, _ = detect_corners(ref)
        corners = extract_milestones(ref, ev)

    os.makedirs(args.output, exist_ok=True)

    def progress(n, total):
        pct = 100.0 * n / total if total else 0
        print("  frame %d/%d (%.0f%%)" % (n, total, pct))

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
            out = render_overlay(ref, lap, corners, lap_dir, fps=args.fps,
                                 fmt=args.format, t_start=args.start,
                                 t_end=args.end, progress=progress)
            webms.append(out)
            print("-> %s" % out)

        if args.format != "png" and len(webms) > 1:
            _concat_videos(webms, os.path.join(args.output, "overlay_all.webm"), args.format)
            print("-> %s" % os.path.join(args.output, "overlay_all.webm"))
    else:
        out = render_overlay(ref, drv, corners, args.output, fps=args.fps,
                             fmt=args.format, t_start=args.start,
                             t_end=args.end, progress=progress)
        print("-> %s" % out)


def _concat_videos(paths, output, fmt):
    """Concatena varios archivos de video con ffmpeg."""
    import shutil, subprocess, tempfile, os
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
            [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
             "-c", "copy", output],
            check=True, capture_output=True,
        )
    finally:
        os.unlink(list_file)


def cmd_ui(args):
    import shutil, subprocess, os
    if not shutil.which("streamlit"):
        print("error: streamlit no instalado — ejecuta: pip install 'fantasma-inputs[ui]'",
              file=sys.stderr)
        return 1
    app = os.path.join(os.path.dirname(__file__), "ui", "app.py")
    subprocess.run(["streamlit", "run", app, "--server.port", str(args.port)], check=True)


def cmd_compose(args):
    import os
    from .viz.compose import compose_video

    offset = args.offset
    lap = None

    if args.driver:
        try:
            _, _, lap = _load_lap(
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
            from .viz.sync import auto_sync
            offset = auto_sync(args.video, lap)
            print("  -> offset detectado: %.3f s" % offset)
        except ImportError as e:
            print("error: %s" % e, file=sys.stderr)
            return 1
        except Exception as e:
            print("error en auto-sync: %s" % e, file=sys.stderr)
            return 1

    lap_duration = lap.laptime if lap is not None else None
    if lap_duration:
        print("  -> recortando vuelta: %.2f s" % lap_duration)

    output = args.output
    if not output:
        base = os.path.splitext(os.path.basename(args.video))[0]
        output = os.path.join(os.path.dirname(args.video) or ".", base + "_composed.mp4")
    out = compose_video(args.video, args.overlay, output,
                        position=args.position, offset=offset, scale=args.scale,
                        lap_duration=lap_duration)
    print("-> %s" % out)


def main(argv=None):
    p = argparse.ArgumentParser(prog="fantasma",
                                description="Compara tus inputs contra una vuelta de referencia, por distancia.")
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
    sp.add_argument("--lap", type=int, help="indice de vuelta del piloto (por defecto: la mas rapida)")
    sp.add_argument("--corners", help="corners.json con nombres/tolerancias (opcional)")
    sp.add_argument("--step", type=float, default=5.0, help="rejilla de distancia en m (default 5)")
    sp.add_argument("--map", action="append")
    sp.add_argument("-o", "--output", default="salida", help="carpeta de salida")
    sp.add_argument("--no-charts", action="store_true", help="no generar graficas")
    sp.add_argument("--charts-top", type=int, default=5, help="graficas de las N curvas con mayor perdida")
    sp.set_defaults(func=cmd_compare)

    sp = sub.add_parser("overlay", help="video HUD transparente para superponer sobre tu grabacion")
    sp.add_argument("--reference", required=True)
    sp.add_argument("--driver", required=True)
    sp.add_argument("--lap", type=int, help="indice de vuelta del piloto (por defecto: la mas rapida)")
    sp.add_argument("--all-laps", action="store_true",
                    help="renderiza todas las vueltas completas y las concatena en overlay_all.webm")
    sp.add_argument("--corners", help="corners.json con nombres (opcional)")
    sp.add_argument("--fps", type=int, default=30)
    sp.add_argument("--format", choices=["prores", "webm", "png"], default="webm",
                    help="webm=VP9 con alfa (default), prores=.mov 4444 con alfa, png=solo frames")
    sp.add_argument("--start", type=float, default=0.0, help="segundo inicial de la vuelta")
    sp.add_argument("--end", type=float, help="segundo final (por defecto: vuelta completa)")
    sp.add_argument("--map", action="append")
    sp.add_argument("-o", "--output", default="salida", help="carpeta de salida")
    sp.set_defaults(func=cmd_overlay)

    sp = sub.add_parser("ui", help="abre la interfaz grafica local en el navegador (requiere streamlit)")
    sp.add_argument("--port", type=int, default=8501, help="puerto local (default: 8501)")
    sp.set_defaults(func=cmd_ui)

    sp = sub.add_parser("compose",
                        help="superponer overlay sobre tu grabacion y generar el video final")
    sp.add_argument("--video",   required=True, help="grabacion de la vuelta (.mp4, .mov, .mkv…)")
    sp.add_argument("--overlay", required=True, help="overlay con canal alfa (.webm o .mov)")
    sp.add_argument("--position",
                    choices=["top-left", "top-right", "bottom-left", "bottom-right",
                             "top-center", "bottom-center", "center"],
                    default="bottom-right",
                    help="posicion del HUD en el video (default: bottom-right)")
    sp.add_argument("--offset", type=float, default=0.0,
                    help="segundos de delay del overlay — util si el video arranca antes de la vuelta")
    sp.add_argument("--scale", type=float, default=1.0,
                    help="factor de escala del HUD (ej. 0.5 = mitad de tamano; default: 1.0)")
    sp.add_argument("-o", "--output", help="archivo de salida (default: <video>_composed.mp4)")
    sp.add_argument("--auto-sync", action="store_true",
                    help="detectar offset automaticamente con correlacion audio vs telemetria (requiere scipy)")
    sp.add_argument("--driver",  help="archivo de telemetria del piloto (necesario con --auto-sync)")
    sp.add_argument("--lap-idx", type=int, dest="lap_idx",
                    help="indice de vuelta del piloto para --auto-sync (por defecto: la mas rapida)")
    sp.add_argument("--map", action="append",
                    help="columna=canal para CSV generico con --auto-sync")
    sp.set_defaults(func=cmd_compose)

    args = p.parse_args(argv)
    try:
        args.func(args)
    except Exception as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
