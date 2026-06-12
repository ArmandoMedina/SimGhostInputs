"""CLI de Fantasma Inputs: fantasma laps | detect | compare"""
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
    trace, rows, summary = compare(ref, drv, step=args.step, corners=corners)
    meta = {"Referencia": args.reference, "Piloto": args.driver}
    report = write_outputs(args.output, trace, rows, summary, meta)
    print("Referencia: %.3fs | Piloto: %.3fs | Delta: %+.3fs" % (
        summary["ref_laptime"], summary["drv_laptime"],
        summary["drv_laptime"] - summary["ref_laptime"]))
    losses = sorted([r for r in rows if r["time_lost"] > 0],
                    key=lambda r: r["time_lost"], reverse=True)
    for r in losses[:3]:
        print("  mayor perdida: %s (m%d) %+.3fs" % (r["name"], r["apex_d"], r["time_lost"]))
    print("-> %s" % report)


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
    sp.set_defaults(func=cmd_compare)

    args = p.parse_args(argv)
    try:
        args.func(args)
    except Exception as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
