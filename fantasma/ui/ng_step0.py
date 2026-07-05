"""Paso 0 — Inicio: selector de flujo (NiceGUI). Rediseno v2."""

import shutil

from nicegui import ui

from .ng_helpers import render_breadcrumb

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
    render_breadcrumb(0)

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
            is_selected = state.flow_chosen and state.flow_key == flow_key
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

    # ── Aviso ffmpeg temprano ─────────────────────────────────────────────────
    if state.flow_chosen and state.flow_key in ("overlay", "compose"):
        if shutil.which("ffmpeg") is None:
            ui.label(
                "⚠️ ffmpeg no detectado — este flujo lo necesita para generar el video. "
                "Instálalo antes de continuar: winget install Gyan.FFmpeg"
            ).classes("text-sm mt-2 text-yellow-400")

    # ── Dialogs de ayuda ──────────────────────────────────────────────────────
    with ui.dialog() as motec_dialog, ui.card().style("max-width:500px"):
        ui.label("Guía MoTeC i2 — Exportar telemetría").classes("font-bold text-lg mb-3")
        ui.html(
            "<ol style='padding-left:1.5rem;line-height:2;font-size:13px'>"
            "<li>Abre tu sesión en MoTeC i2.</li>"
            "<li>Ve a <strong>File &gt; Export</strong>.</li>"
            "<li>Elige el formato <strong>CSV</strong>.</li>"
            "<li>Activa la opción <strong>Include Distance Data</strong>.</li>"
            "<li>Guarda el archivo y súbelo aquí.</li>"
            "</ol>"
        )
        ui.button("Cerrar", on_click=motec_dialog.close).props("flat").classes("mt-2")

    with ui.dialog() as csv_dialog, ui.card().style("max-width:500px"):
        ui.label("Formato CSV esperado").classes("font-bold text-lg mb-3")
        ui.label("El CSV debe tener estas columnas (los nombres pueden variar):").classes(
            "text-sm mb-2"
        )
        ui.html(
            "<pre style='font-size:11px;background:#111;padding:12px;border-radius:4px'>"
            "Time,Distance,Speed,Throttle,Brake,Gear\n"
            "0.000,0.0,0.0,0.0,0.0,1\n"
            "0.010,0.1,5.2,0.15,0.0,1\n"
            "0.020,0.3,10.1,0.42,0.0,1"
            "</pre>"
        )
        ui.button("Cerrar", on_click=csv_dialog.close).props("flat").classes("mt-2")

    # ── Footer info ───────────────────────────────────────────────────────────
    with ui.element("div").classes("footer-info"):
        ui.html(
            '<span class="footer-text">'
            "Exporta telemetría desde MoTeC i2 con Include Distance Data activado."
            "</span>"
        )
        with ui.element("div").classes("footer-links"):
            ui.html('<span class="link-pill">Guía MoTeC</span>').on("click", motec_dialog.open)
            ui.html('<span class="link-pill">Ejemplo CSV</span>').on("click", csv_dialog.open)

    ui.separator().classes("my-4")

    # ── Botón Empezar ─────────────────────────────────────────────────────────
    async def go_to_import():
        if not state.flow_chosen:
            ui.notify("Elige un flujo antes de continuar.", type="warning", position="top")
            return
        await navigate(1)

    btn_cls = "btn-primary" if state.flow_chosen else "btn-secondary"
    ui.button(
        "Empezar → Ir a Importar",
        on_click=go_to_import,
    ).classes(btn_cls).props("flat")
