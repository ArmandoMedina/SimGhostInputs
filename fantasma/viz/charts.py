"""Graficas ghost: tus inputs sobre los de la referencia, por distancia.

Requiere matplotlib (opcional): pip install matplotlib
"""
import os


def _mpl():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        return None


REF_COLOR = "#9aa0a6"     # gris fantasma
DRV_COLOR = "#ff6d00"     # naranja piloto
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


def plot_corner(trace, corner, row, outdir, step=5.0, pad_m=120):
    """Grafica ghost de una curva: velocidad, gas y freno, piloto vs referencia."""
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
    fig, axes = plt.subplots(3, 1, figsize=(9, 6.5), sharex=True)
    fig.patch.set_facecolor(BG)

    ax = axes[0]
    ax.plot(d, [p.get("ref_speed", 0) for p in pts], color=REF_COLOR, lw=2, label="referencia")
    ax.plot(d, [p.get("drv_speed", 0) for p in pts], color=DRV_COLOR, lw=1.6, label="tú")
    _style(ax, "%s — velocidad (km/h)" % name)
    ax.legend(facecolor=BG, labelcolor=FG, edgecolor="#333", fontsize=8, loc="lower left")

    ax = axes[1]
    ax.plot(d, [p.get("ref_throttle", 0) for p in pts], color=REF_COLOR, lw=2)
    ax.plot(d, [p.get("drv_throttle", 0) for p in pts], color="#00c853", lw=1.6)
    ax.set_ylim(-5, 105)
    _style(ax, "gas (%)  — verde: tú")

    ax = axes[2]
    ax.plot(d, [p.get("ref_brake", 0) for p in pts], color=REF_COLOR, lw=2)
    ax.plot(d, [p.get("drv_brake", 0) for p in pts], color="#ff1744", lw=1.6)
    ax.set_ylim(-5, 105)
    _style(ax, "freno (%)  — rojo: tú")
    ax.set_xlabel("distancia (m)", color=FG, fontsize=8)

    # marcadores: apex de referencia y perdida de la curva
    apex_d = corner["milestones"]["apex"]["d"]
    for ax in axes:
        ax.axvline(apex_d, color="#fdd835", lw=0.8, ls="--", alpha=0.7)
    if row is not None:
        fig.suptitle("%s   tiempo perdido: %+.3f s   ΔV-Min: %+d km/h" % (
            name, row["time_lost"], row["d_vmin"]),
            color=FG, fontsize=11, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(corner.get("id", name)))
    path = os.path.join(outdir, "curva_%s.png" % safe)
    fig.savefig(path, dpi=110, facecolor=BG)
    plt.close(fig)
    return path


def plot_delta_map(trace, corner_rows, outdir):
    """Mapa de la vuelta completa: delta acumulado vs distancia, con las mayores perdidas marcadas."""
    plt = _mpl()
    if plt is None:
        return None
    d = [p["dist"] for p in trace]
    dt = [p["delta_t"] for p in trace]
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor(BG)
    ax.plot(d, dt, color=DRV_COLOR, lw=1.5)
    ax.fill_between(d, dt, 0, color=DRV_COLOR, alpha=0.15)
    _style(ax, "delta acumulado vs referencia (s) — sube = pierdes")
    ax.set_xlabel("distancia (m)", color=FG, fontsize=8)
    losses = sorted([r for r in corner_rows if r.get("time_lost", 0) > 0],
                    key=lambda r: r["time_lost"], reverse=True)[:5]
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


def render_charts(trace, corner_rows, corners, outdir, top=5):
    """Genera el mapa de delta + graficas de las `top` curvas con mayor perdida."""
    plt = _mpl()
    if plt is None:
        return []
    os.makedirs(outdir, exist_ok=True)
    out = []
    p = plot_delta_map(trace, corner_rows, outdir)
    if p:
        out.append(p)
    by_id = {c.get("id"): c for c in corners}
    losses = sorted([r for r in corner_rows if r.get("time_lost", 0) > 0],
                    key=lambda r: r["time_lost"], reverse=True)[:top]
    for r in losses:
        c = by_id.get(r["id"])
        if c:
            p = plot_corner(trace, c, r, outdir)
            if p:
                out.append(p)
    return out
