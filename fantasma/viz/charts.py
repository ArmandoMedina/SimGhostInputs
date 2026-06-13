"""Graficas ghost: tus inputs sobre los de la referencia, por distancia.

Requiere matplotlib (opcional): pip install matplotlib
"""
import math
import os


def _mpl():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        return None


REF_COLOR  = "#9aa0a6"   # gris fantasma
DRV_COLOR  = "#ff6d00"   # naranja piloto
GAS_COLOR  = "#00c853"   # verde gas
BRAKE_COLOR = "#ff1744"  # rojo freno
STEER_COLOR = "#40c4ff"  # azul volante
GLAT_COLOR  = "#fdd835"  # amarillo G-lat
GLONG_COLOR = "#e040fb"  # violeta G-long
BG = "#111418"
FG = "#e8eaed"


def _style(ax, title=None):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color("#333")
    ax.tick_params(colors=FG, labelsize=8)
    ax.grid(color="#2a2e33", linewidth=0.5)
    if title:
        ax.set_title(title, color=FG, fontsize=9, loc="left")


# ---------------------------------------------------------------------------
# 1. Gráfica por curva: velocidad / gas / freno / volante / G-lat
# ---------------------------------------------------------------------------

def plot_corner(trace, corner, row, outdir, step=5.0, pad_m=120):
    """Gráfica ghost de una curva: hasta 5 paneles (velocidad, gas, freno, volante, G-lat)."""
    plt = _mpl()
    if plt is None:
        return None
    lo, hi = corner.get("segment_m") or corner.get("range_m")
    lo, hi = lo - pad_m, hi + pad_m
    pts = [p for p in trace if lo <= p["dist"] <= hi]
    if len(pts) < 5:
        return None
    d = [p["dist"] for p in pts]
    name = corner.get("name", corner.get("id", "?"))

    has_steer = any("ref_steering" in p or "drv_steering" in p for p in pts)
    has_glat  = any("ref_glat" in p or "drv_glat" in p for p in pts)
    n_panels  = 3 + int(has_steer) + int(has_glat)
    heights   = [2, 1, 1] + ([1] if has_steer else []) + ([1] if has_glat else [])

    fig, axes = plt.subplots(
        n_panels, 1,
        figsize=(9, 2 + n_panels * 1.6),
        sharex=True,
        gridspec_kw={"height_ratios": heights},
    )
    fig.patch.set_facecolor(BG)
    if n_panels == 1:
        axes = [axes]

    ax = axes[0]
    ax.plot(d, [p.get("ref_speed", 0) for p in pts], color=REF_COLOR, lw=2, label="referencia")
    ax.plot(d, [p.get("drv_speed", 0) for p in pts], color=DRV_COLOR, lw=1.6, label="tú")
    _style(ax, "%s — velocidad (km/h)" % name)
    ax.legend(facecolor=BG, labelcolor=FG, edgecolor="#333", fontsize=8, loc="lower left")

    ax = axes[1]
    ax.plot(d, [p.get("ref_throttle", 0) for p in pts], color=REF_COLOR, lw=2)
    ax.plot(d, [p.get("drv_throttle", 0) for p in pts], color=GAS_COLOR, lw=1.6)
    ax.set_ylim(-5, 105)
    _style(ax, "gas (%)  — verde: tú")

    ax = axes[2]
    ax.plot(d, [p.get("ref_brake", 0) for p in pts], color=REF_COLOR, lw=2)
    ax.plot(d, [p.get("drv_brake", 0) for p in pts], color=BRAKE_COLOR, lw=1.6)
    ax.set_ylim(-5, 105)
    _style(ax, "freno (%)  — rojo: tú")

    ax_idx = 3
    if has_steer:
        ax = axes[ax_idx]
        ax.plot(d, [p.get("ref_steering", 0) for p in pts], color=REF_COLOR, lw=2)
        ax.plot(d, [p.get("drv_steering", 0) for p in pts], color=STEER_COLOR, lw=1.6)
        _style(ax, "volante (°)  — azul: tú")
        ax_idx += 1

    if has_glat:
        ax = axes[ax_idx]
        ax.plot(d, [p.get("ref_glat", 0) for p in pts], color=REF_COLOR, lw=2)
        ax.plot(d, [p.get("drv_glat", 0) for p in pts], color=GLAT_COLOR, lw=1.6)
        _style(ax, "G-lat  — amarillo: tú")

    axes[-1].set_xlabel("distancia (m)", color=FG, fontsize=8)

    apex_d = corner["milestones"]["apex"]["d"]
    for ax in axes:
        ax.axvline(apex_d, color="#fdd835", lw=0.8, ls="--", alpha=0.7)

    if row is not None:
        fig.suptitle(
            "%s   tiempo perdido: %+.3f s   ΔV-Min: %+d km/h" % (
                name, row["time_lost"], row["d_vmin"]),
            color=FG, fontsize=11, x=0.01, ha="left",
        )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(corner.get("id", name)))
    path = os.path.join(outdir, "curva_%s.png" % safe)
    fig.savefig(path, dpi=110, facecolor=BG)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 2. Delta map: delta acumulado vs distancia
# ---------------------------------------------------------------------------

def plot_delta_map(trace, corner_rows, outdir):
    """Mapa de la vuelta completa: delta acumulado vs distancia, con las mayores pérdidas marcadas."""
    plt = _mpl()
    if plt is None:
        return None
    d  = [p["dist"] for p in trace]
    dt = [p["delta_t"] for p in trace]
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor(BG)
    ax.plot(d, dt, color=DRV_COLOR, lw=1.5)
    ax.fill_between(d, dt, 0, color=DRV_COLOR, alpha=0.15)
    _style(ax, "delta acumulado vs referencia (s) — sube = pierdes")
    ax.set_xlabel("distancia (m)", color=FG, fontsize=8)
    losses = sorted(
        [r for r in corner_rows if r.get("time_lost", 0) > 0],
        key=lambda r: r["time_lost"], reverse=True,
    )[:5]
    for r in losses:
        x = r["apex_d"]
        i = min(range(len(d)), key=lambda j: abs(d[j] - x))
        ax.annotate(r["name"], (x, dt[i]), color=FG, fontsize=7,
                    textcoords="offset points", xytext=(0, 8), ha="center")
        ax.plot([x], [dt[i]], "o", color="#fdd835", ms=4)
    fig.tight_layout()
    path = os.path.join(outdir, "delta_map.png")
    fig.savefig(path, dpi=110, facecolor=BG)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 3. Bar chart: tiempo perdido por curva
# ---------------------------------------------------------------------------

def plot_time_loss_bar(corner_rows, outdir):
    """Barras horizontales: tiempo perdido por curva, ordenado de mayor a menor pérdida."""
    plt = _mpl()
    if plt is None:
        return None
    rows = [r for r in corner_rows if r.get("time_lost", 0) != 0]
    if not rows:
        return None
    rows = sorted(rows, key=lambda r: r["time_lost"], reverse=True)
    names  = [r["name"] for r in rows]
    losses = [r["time_lost"] for r in rows]
    colors = ["#ff1744" if v > 0 else "#00c853" for v in losses]

    fig_h = max(3.5, len(rows) * 0.45 + 1.0)
    fig, ax = plt.subplots(figsize=(10, fig_h))
    fig.patch.set_facecolor(BG)
    bars = ax.barh(names, losses, color=colors, height=0.6)
    ax.axvline(0, color=FG, lw=0.8)
    for bar, val in zip(bars, losses):
        offset = 0.005 if val >= 0 else -0.005
        ax.text(
            val + offset, bar.get_y() + bar.get_height() / 2,
            "%+.3f s" % val,
            va="center", ha="left" if val >= 0 else "right",
            color=FG, fontsize=8,
        )
    ax.invert_yaxis()
    _style(ax, "tiempo perdido por curva (s)  — rojo: pierdes · verde: ganas")
    ax.set_xlabel("segundos", color=FG, fontsize=8)
    fig.tight_layout()
    path = os.path.join(outdir, "time_loss_bar.png")
    fig.savefig(path, dpi=110, facecolor=BG)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 4. G-G diagram (friction circle)
# ---------------------------------------------------------------------------

def plot_gg_diagram(trace, outdir):
    """Scatter G-lat vs G-long: muestra si el piloto está usando el círculo de fricción."""
    plt = _mpl()
    if plt is None:
        return None

    def _col(key):
        return [p[key] for p in trace if key in p]

    drv_glat  = _col("drv_glat")
    drv_glong = _col("drv_glong")
    if not drv_glat or not drv_glong or len(drv_glat) != len(drv_glong):
        return None

    ref_glat  = _col("ref_glat")
    ref_glong = _col("ref_glong")

    all_g = drv_glat + drv_glong + ref_glat + ref_glong
    max_g = max(abs(g) for g in all_g) * 1.12 if all_g else 2.0

    circle = [2 * math.pi * i / 200 for i in range(201)]
    cx = [max_g * math.cos(t) for t in circle]
    cy = [max_g * math.sin(t) for t in circle]

    fig, ax = plt.subplots(figsize=(7, 7))
    fig.patch.set_facecolor(BG)
    ax.plot(cx, cy, color="#2a2e33", lw=1.2, ls="--", label="límite aprox.")

    if ref_glat and len(ref_glat) == len(ref_glong):
        ax.scatter(ref_glong, ref_glat, c=REF_COLOR, s=1.2, alpha=0.25, label="referencia")
    ax.scatter(drv_glong, drv_glat, c=DRV_COLOR, s=1.5, alpha=0.35, label="tú")

    ax.axhline(0, color="#2a2e33", lw=0.6)
    ax.axvline(0, color="#2a2e33", lw=0.6)
    ax.set_aspect("equal")
    lim = max_g * 1.05
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)

    for txt, x, y in [
        ("ACELERA →",   lim * 0.60,  0),
        ("← FRENA",    -lim * 0.60,  0),
        ("DERECHA ↑",   0,            lim * 0.65),
        ("↓ IZQUIERDA", 0,           -lim * 0.65),
    ]:
        ax.text(x, y, txt, color="#444", fontsize=7, ha="center", va="center", alpha=0.7)

    _style(ax, "Diagrama G-G — círculo de fricción")
    ax.set_xlabel("G-long  (negativo = freno, positivo = gas)", color=FG, fontsize=8)
    ax.set_ylabel("G-lat  (positivo = derecha, negativo = izquierda)", color=FG, fontsize=8)
    ax.legend(facecolor=BG, labelcolor=FG, edgecolor="#333", fontsize=8, markerscale=6)
    fig.tight_layout()
    path = os.path.join(outdir, "gg_diagram.png")
    fig.savefig(path, dpi=110, facecolor=BG)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 5. Vista multi-canal de la vuelta completa
# ---------------------------------------------------------------------------

def plot_full_lap(trace, outdir):
    """PNG horizontal con todos los canales disponibles a lo largo de la vuelta completa."""
    plt = _mpl()
    if plt is None:
        return None
    d = [p["dist"] for p in trace]

    _channels = [
        ("delta_t",   "delta (s)",      DRV_COLOR,   BRAKE_COLOR,  None,  None),
        ("speed",     "velocidad (km/h)", REF_COLOR,  DRV_COLOR,    None,  None),
        ("throttle",  "gas (%)",         REF_COLOR,   GAS_COLOR,    -5,    105),
        ("brake",     "freno (%)",        REF_COLOR,  BRAKE_COLOR,  -5,    105),
        ("steering",  "volante (°)",      REF_COLOR,  STEER_COLOR,  None,  None),
        ("gear",      "marcha",           REF_COLOR,  DRV_COLOR,    None,  None),
        ("glat",      "G-lat",            REF_COLOR,  GLAT_COLOR,   None,  None),
        ("glong",     "G-long",           REF_COLOR,  GLONG_COLOR,  None,  None),
    ]

    active = []
    for ch, label, rc, dc, ylo, yhi in _channels:
        if ch == "delta_t":
            active.append((ch, label, rc, dc, ylo, yhi))
        elif any("ref_" + ch in p or "drv_" + ch in p for p in trace):
            active.append((ch, label, rc, dc, ylo, yhi))
    if not active:
        return None

    n = len(active)
    heights = [2] + [1] * (n - 1)
    fig, axes = plt.subplots(
        n, 1,
        figsize=(16, 1.5 + n * 1.3),
        sharex=True,
        gridspec_kw={"height_ratios": heights},
    )
    fig.patch.set_facecolor(BG)
    if n == 1:
        axes = [axes]

    for ax, (ch, label, rc, dc, ylo, yhi) in zip(axes, active):
        if ch == "delta_t":
            vals = [p["delta_t"] for p in trace]
            ax.plot(d, vals, color=DRV_COLOR, lw=1.2)
            ax.fill_between(d, vals, 0, color=DRV_COLOR, alpha=0.15)
            ax.axhline(0, color=REF_COLOR, lw=0.5, ls="--")
        else:
            rvals = [p.get("ref_" + ch) for p in trace]
            dvals = [p.get("drv_" + ch) for p in trace]
            if any(v is not None for v in rvals):
                ax.plot(d, [v or 0 for v in rvals], color=rc, lw=1.2, alpha=0.6)
            if any(v is not None for v in dvals):
                ax.plot(d, [v or 0 for v in dvals], color=dc, lw=1.0)
        if ylo is not None:
            ax.set_ylim(ylo, yhi)
        _style(ax, label)

    axes[-1].set_xlabel("distancia (m)", color=FG, fontsize=8)
    fig.tight_layout()
    path = os.path.join(outdir, "full_lap.png")
    fig.savefig(path, dpi=110, facecolor=BG)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# 6. Detalle de zonas de frenada
# ---------------------------------------------------------------------------

def plot_brake_zones(trace, corner_rows, corners, outdir, top=5):
    """Zoom en las frenadas con mayor pérdida: velocidad + presión de freno + G-long."""
    plt = _mpl()
    if plt is None:
        return []
    by_id = {c.get("id"): c for c in corners}
    losses = sorted(
        [r for r in corner_rows if r.get("time_lost", 0) > 0 and "ref_brake_d" in r],
        key=lambda r: r["time_lost"], reverse=True,
    )[:top]

    out = []
    for r in losses:
        c = by_id.get(r["id"])
        if c is None:
            continue
        ref_bd = r["ref_brake_d"]
        drv_bd = r.get("drv_brake_d", ref_bd)
        lo = min(ref_bd, drv_bd) - 80
        hi = c["milestones"]["apex"]["d"] + 60
        pts = [p for p in trace if lo <= p["dist"] <= hi]
        if len(pts) < 5:
            continue
        d = [p["dist"] for p in pts]

        has_glong = any("ref_glong" in p or "drv_glong" in p for p in pts)
        n_panels  = 3 if has_glong else 2
        heights   = [2, 1] + ([1] if has_glong else [])

        name = r["name"]
        fig, axes = plt.subplots(
            n_panels, 1,
            figsize=(9, 1.5 + n_panels * 1.8),
            sharex=True,
            gridspec_kw={"height_ratios": heights},
        )
        fig.patch.set_facecolor(BG)
        if n_panels == 1:
            axes = [axes]

        ax = axes[0]
        ax.plot(d, [p.get("ref_speed", 0) for p in pts], color=REF_COLOR, lw=2, label="referencia")
        ax.plot(d, [p.get("drv_speed", 0) for p in pts], color=DRV_COLOR, lw=1.6, label="tú")
        _style(ax, "%s — velocidad (km/h)" % name)
        ax.legend(facecolor=BG, labelcolor=FG, edgecolor="#333", fontsize=8)

        ax = axes[1]
        ax.plot(d, [p.get("ref_brake", 0) for p in pts], color=REF_COLOR, lw=2)
        ax.plot(d, [p.get("drv_brake", 0) for p in pts], color=BRAKE_COLOR, lw=1.6)
        ax.set_ylim(-5, 105)
        _style(ax, "freno (%)")

        if has_glong:
            ax = axes[2]
            ax.plot(d, [p.get("ref_glong", 0) for p in pts], color=REF_COLOR, lw=2)
            ax.plot(d, [p.get("drv_glong", 0) for p in pts], color=GLONG_COLOR, lw=1.6)
            _style(ax, "G-long (desaceleración)  — violeta: tú")

        axes[-1].set_xlabel("distancia (m)", color=FG, fontsize=8)

        for ax in axes:
            ax.axvline(ref_bd, color=REF_COLOR, lw=1.0, ls=":", alpha=0.9, label="frena ref")
            ax.axvline(drv_bd, color=DRV_COLOR, lw=1.0, ls=":", alpha=0.9, label="frenas tú")

        delta_m = r.get("d_brake_m")
        suffix  = ("  (Δ%+dm)" % delta_m) if delta_m is not None else ""
        fig.suptitle(
            "%s — frenada ref %dm · tú %dm%s" % (name, ref_bd, drv_bd, suffix),
            color=FG, fontsize=10, x=0.01, ha="left",
        )
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(r["id"]))
        path = os.path.join(outdir, "frenada_%s.png" % safe)
        fig.savefig(path, dpi=110, facecolor=BG)
        plt.close(fig)
        out.append(path)
    return out


# ---------------------------------------------------------------------------
# Punto de entrada: genera todos los charts
# ---------------------------------------------------------------------------

def render_charts(trace, corner_rows, corners, outdir, top=5):
    """Genera todos los charts disponibles y devuelve la lista de rutas creadas."""
    plt = _mpl()
    if plt is None:
        return []
    os.makedirs(outdir, exist_ok=True)
    out = []

    p = plot_delta_map(trace, corner_rows, outdir)
    if p:
        out.append(p)

    p = plot_time_loss_bar(corner_rows, outdir)
    if p:
        out.append(p)

    p = plot_gg_diagram(trace, outdir)
    if p:
        out.append(p)

    p = plot_full_lap(trace, outdir)
    if p:
        out.append(p)

    by_id = {c.get("id"): c for c in corners}
    losses = sorted(
        [r for r in corner_rows if r.get("time_lost", 0) > 0],
        key=lambda r: r["time_lost"], reverse=True,
    )[:top]
    for r in losses:
        c = by_id.get(r["id"])
        if c:
            p = plot_corner(trace, c, r, outdir)
            if p:
                out.append(p)

    brake_paths = plot_brake_zones(trace, corner_rows, corners, outdir, top=top)
    out.extend(brake_paths)

    return out
