"""Reporte Markdown del debrief y CSVs de salida."""
import csv
import os


def _fmt_t(s):
    m, sec = divmod(abs(s), 60)
    return "%s%d:%06.3f" % ("-" if s < 0 else "", int(m), sec)


def write_outputs(outdir, trace, corner_rows, summary, meta=None):
    os.makedirs(outdir, exist_ok=True)
    # delta.csv
    if trace:
        with open(os.path.join(outdir, "delta.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(trace[0].keys()))
            w.writeheader()
            w.writerows(trace)
    # corners_compare.csv
    if corner_rows:
        keys = []
        for r in corner_rows:
            for k in r:
                if k not in keys:
                    keys.append(k)
        with open(os.path.join(outdir, "corners_compare.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(corner_rows)
    # report.md
    with open(os.path.join(outdir, "report.md"), "w", encoding="utf-8") as f:
        f.write(render_markdown(trace, corner_rows, summary, meta))
    return os.path.join(outdir, "report.md")


def render_markdown(trace, corner_rows, summary, meta=None):
    meta = meta or {}
    out = []
    out.append("# 👻 SimGhostInputs — Debrief\n")
    if meta:
        ctx = " · ".join("%s: %s" % (k, v) for k, v in meta.items() if v)
        out.append("*%s*\n" % ctx)
    out.append("| | Referencia | Piloto | Delta |")
    out.append("| :-- | :-- | :-- | :-- |")
    out.append("| **Tiempo de vuelta** | %s | %s | **%+.3f s** |" % (
        _fmt_t(summary["ref_laptime"]), _fmt_t(summary["drv_laptime"]),
        summary["drv_laptime"] - summary["ref_laptime"]))
    rw, dw = summary.get("ref_wear") or {}, summary.get("drv_wear") or {}
    if "slip_index" in rw and "slip_index" in dw:
        out.append("| Índice de deslizamiento (desgaste) | %.2f | %.2f | %+.2f |" % (
            rw["slip_index"], dw["slip_index"], dw["slip_index"] - rw["slip_index"]))
    if "abs_count" in rw and "abs_count" in dw:
        out.append("| Activaciones de ABS | %d | %d | %+d |" % (
            rw["abs_count"], dw["abs_count"], dw["abs_count"] - rw["abs_count"]))
    if "tcs_count" in rw and "tcs_count" in dw:
        out.append("| Activaciones de TCS | %d | %d | %+d |" % (
            rw["tcs_count"], dw["tcs_count"], dw["tcs_count"] - rw["tcs_count"]))
    if "tyre_temp_avg" in rw and "tyre_temp_avg" in dw:
        out.append("| Temp. media de gomas (°C) | %.0f | %.0f | %+.0f |" % (
            rw["tyre_temp_avg"], dw["tyre_temp_avg"], dw["tyre_temp_avg"] - rw["tyre_temp_avg"]))
    if "fuel_used" in rw and "fuel_used" in dw:
        out.append("| Combustible usado (L) | %.2f | %.2f | %+.2f |" % (
            rw["fuel_used"], dw["fuel_used"], dw["fuel_used"] - rw["fuel_used"]))
    out.append("")
    losses = [r for r in corner_rows if r.get("time_lost") is not None]
    losses.sort(key=lambda r: r["time_lost"], reverse=True)
    if losses:
        out.append("## 🎯 Donde se va el tiempo (top 5)\n")
        for r in losses[:5]:
            if r["time_lost"] <= 0:
                continue
            parts = []
            if r.get("d_brake_m") is not None:
                if r["d_brake_m"] < -5:
                    parts.append("frenas %dm antes" % -r["d_brake_m"])
                elif r["d_brake_m"] > 5:
                    parts.append("frenas %dm tarde" % r["d_brake_m"])
            if abs(r["d_vmin"]) > 3:
                parts.append("V-Min %+d km/h" % r["d_vmin"])
            if r.get("d_gas100_m") is not None and r["d_gas100_m"] > 10:
                parts.append("gas 100%% %dm despues" % r["d_gas100_m"])
            detail = ("; ".join(parts)) or "revisar trazada"
            out.append("- **%s** (m%s): **%+.3f s** — %s" % (
                r["name"], "{:,}".format(r["apex_d"]), r["time_lost"], detail))
        out.append("")
    out.append("## 📊 Tabla por curva\n")
    out.append("| Curva | Ápex (m) | V-Min ref | V-Min tú | Δv | Frenada Δm | Tiempo perdido | Avisos |")
    out.append("| :-- | --: | --: | --: | --: | --: | --: | :-- |")
    for r in corner_rows:
        out.append("| %s | %s | %d | %d | %+d | %s | %+.3f s | %s |" % (
            r["name"], "{:,}".format(r["apex_d"]), r["ref_vmin"], r["drv_vmin"], r["d_vmin"],
            ("%+d" % r["d_brake_m"]) if r.get("d_brake_m") is not None else "—",
            r["time_lost"], r.get("flags", "")))
    out.append("")
    out.append("*Generado por [SimGhostInputs](https://github.com/) — AGPL-3.0-or-later. "
               "Comparacion por distancia; delta positivo = el piloto pierde tiempo.*")
    return "\n".join(out) + "\n"
