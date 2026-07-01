"""Paso 0 — Inicio: selector de flujo (NiceGUI). Rediseno v2."""

from nicegui import ui

# Datos de cada flujo definidos localmente para step0.
# Tupla: (icon, title, desc, needs_list, out_list, featured)
_FLOWS: dict[str, tuple] = {
    "analisis": (
        "📊",
        "Solo análisis",
        "Delta table, gráficas y reporte",
        ["CSV referencia", "CSV piloto"],
        ["Reporte .md", "corners_compare.csv", "Gráficas"],
        False,
    ),
    "overlay": (
        "🎬",
        "Solo overlay",
        "HUD transparente para edición de video",
        ["CSV referencia", "CSV piloto"],
        ["overlay.webm (VP9 + alfa)"],
        False,
    ),
    "compose": (
        "🎥",
        "Video con HUD",
        "El video final ya con overlay y pace notes",
        ["CSV referencia", "CSV piloto", "Video de grabación (.mp4)"],
        ["overlay.webm", "final_composed.mp4", "Pace notes WAVs"],
        True,
    ),
}


async def render(state, navigate):
    # ── Encabezado de página ──────────────────────────────────────────────────
    ui.html('<h1 class="page-heading">SimGhostInputs</h1>')
    ui.html(
        '<p class="page-sub">'
        "Compara tu telemetría contra la vuelta de referencia, curva por curva."
        "</p>"
    )
    ui.html(
        '<div class="status-row">'
        '  <div class="status-chip"><div class="status-dot live"></div>Motor listo</div>'
        '  <div class="status-chip"><div class="status-dot"></div>Sin archivos</div>'
        "</div>"
    )

    # ── Subtítulo del selector ────────────────────────────────────────────────
    ui.html(
        '<div class="page-heading" style="font-size:1rem;margin-bottom:4px">'
        "¿Qué quieres obtener hoy?"
        "</div>"
    )
    ui.html(
        '<p class="page-sub">Elige el flujo que mejor se adapta a lo que tienes disponible.</p>'
    )

    # ── Grid de tarjetas ──────────────────────────────────────────────────────
    async def select_flow(fk: str):
        state.flow_key = fk
        state.flow_chosen = True
        await navigate(0)

    flow_grid = ui.element("div").classes("flow-grid")
    with flow_grid:
        for flow_key, (icon, title, desc, needs_list, out_list, featured) in _FLOWS.items():
            is_selected = state.flow_key == flow_key
            border_style = "border-color: var(--highlight)" if is_selected else ""
            card_classes = "flow-card" + ("  featured" if featured else "")

            with ui.card().classes(card_classes).style(f"border-radius:0;{border_style}"):
                if featured:
                    ui.html('<span class="featured-badge">MÁS COMPLETO</span>')

                ui.html(f'<span class="flow-icon">{icon}</span>')
                ui.label(title).classes("flow-title")
                ui.label(desc).classes("flow-desc")

                needs_items = "".join(f"<li>{n}</li>" for n in needs_list)
                out_items = "".join(f"<li>{d}</li>" for d in out_list)
                ui.html(
                    f'<div class="flow-needs">'
                    f'  <div class="flow-needs-label">Necesitas</div>'
                    f'  <ul class="needs-list">{needs_items}</ul>'
                    f'  <div class="flow-needs-label">Obtienes</div>'
                    f'  <ul class="needs-list">{out_items}</ul>'
                    f"</div>"
                )

                btn_label = "✓ Seleccionado" if is_selected else "Elegir este"
                btn_class = "btn-featured" if featured else "btn-secondary"
                ui.button(
                    btn_label,
                    on_click=lambda fk=flow_key: select_flow(fk),
                ).classes(btn_class).props("flat")

    # ── Footer info ───────────────────────────────────────────────────────────
    ui.html(
        '<div class="footer-info">'
        '  <span class="footer-text">'
        "Exporta telemetría desde MoTeC i2 con Include Distance Data activado."
        "  </span>"
        '  <div class="footer-links">'
        '    <span class="link-pill">Guía MoTeC</span>'
        '    <span class="link-pill">Ejemplo CSV</span>'
        "  </div>"
        "</div>"
    )

    ui.separator().classes("my-4")

    # ── Botón Empezar ─────────────────────────────────────────────────────────
    async def go_to_import():
        state.flow_chosen = True
        await navigate(1)

    ui.button(
        "Empezar → Ir a Importar",
        on_click=go_to_import,
    ).classes("btn-primary").props("flat")
