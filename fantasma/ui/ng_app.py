"""NiceGUI entry point para SimGhostInputs v2.0."""

from nicegui import ui

from . import ng_step0, ng_step1, ng_step2, ng_step3, ng_step4
from .ng_state import AppState


@ui.page("/")
async def main_page():
    state = AppState()

    ui.add_head_html("""<style>
      :root {
        --bg: #08090d; --card-bg: #111318; --sidebar-bg: #0d0e13;
        --accent: #2d6cdf; --highlight: #4f8ef7; --text: #f0f2f5;
        --muted: #6b7280; --border: #1e2330; --success: #22c55e;
        --danger: #ef4444; --warning: #f59e0b;
      }
      html, body { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, -apple-system, sans-serif; font-size: 14px; }

      /* Layout */
      .sgi-sidebar { background: var(--sidebar-bg); border-right: 1px solid var(--border); }
      .nicegui-content { padding: 0 !important; }
      .q-drawer { border-right: 1px solid var(--border) !important; }

      /* Sidebar brand */
      .sidebar-brand { padding: 20px 20px 16px; border-bottom: 1px solid var(--border); display: flex; flex-direction: row; align-items: center; gap: 10px; }
      .brand-icon { width: 28px; height: 28px; background: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0; }
      .brand-name { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; color: var(--text); text-transform: uppercase; }
      .brand-sub { font-size: 10px; color: var(--muted); }

      /* Sidebar nav */
      .nav-section-label { font-size: 9px; font-weight: 600; letter-spacing: 0.1em; color: var(--muted); text-transform: uppercase; padding: 12px 16px 4px; }
      .nav-item { display: flex; align-items: center; gap: 8px; padding: 7px 16px; border-left: 2px solid transparent; cursor: pointer; color: var(--muted); font-size: 12px; transition: color 0.15s, background 0.15s; }
      .nav-item:hover { color: var(--text); background: rgba(255,255,255,0.03); }
      .nav-item.active { color: var(--highlight); border-left-color: var(--highlight); background: rgba(79,142,247,0.08); }
      .nav-icon { width: 16px; text-align: center; flex-shrink: 0; }

      /* nav-btn: resets Quasar button styles to look like nav-item */
      .nav-btn { background: transparent !important; border: none !important; border-left: 2px solid transparent !important; color: var(--muted) !important; padding: 7px 16px !important; text-align: left !important; font-size: 12px !important; width: 100% !important; cursor: pointer !important; border-radius: 0 !important; box-shadow: none !important; transition: color 0.15s, background 0.15s !important; }
      .nav-btn .q-btn__content { justify-content: flex-start !important; }
      .nav-btn:hover { color: var(--text) !important; background: rgba(255,255,255,0.03) !important; }
      .nav-btn-active { color: var(--highlight) !important; border-left-color: var(--highlight) !important; background: rgba(79,142,247,0.08) !important; }

      /* Sidebar footer */
      .sidebar-footer { margin-top: auto; padding: 12px 16px; border-top: 1px solid var(--border); }
      .version-badge { font-size: 10px; color: var(--muted); }
      .version-badge span { color: var(--accent); }

      /* Step header */
      .step-header { font-size: 1.2rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); margin-bottom: 0.25rem; }

      /* Flow grid */
      .flow-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 16px; margin-bottom: 1.5rem; }
      .flow-card { background: var(--card-bg); border: 1px solid var(--border); padding: 24px; cursor: pointer; transition: border-color 0.15s; position: relative; border-radius: 0; }
      .flow-card:hover { border-color: rgba(79,142,247,0.4); }
      .flow-card.selected { border-color: var(--highlight); }
      .flow-card.featured { background: #0f1420; border-color: rgba(79,142,247,0.35); }
      .featured-badge { position: absolute; top: 12px; right: 12px; background: var(--accent); color: white; font-size: 9px; font-weight: 700; letter-spacing: 0.08em; padding: 2px 6px; }
      .flow-icon { font-size: 20px; margin-bottom: 10px; display: block; }
      .flow-title { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
      .flow-desc { font-size: 11px; color: var(--muted); margin-bottom: 12px; line-height: 1.5; }
      .flow-needs { border-top: 1px solid var(--border); padding-top: 10px; margin-top: 10px; font-size: 11px; }
      .flow-needs-label { color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px; font-weight: 600; }
      .needs-list { list-style: none; padding: 0; margin: 0 0 8px; }
      .needs-list li { color: var(--muted); padding-left: 12px; position: relative; line-height: 1.6; }
      .needs-list li::before { content: "·"; position: absolute; left: 0; color: var(--muted); }
      .needs-list li.ok::before { color: var(--success); }

      /* Status row */
      .status-row { display: flex; gap: 12px; margin-bottom: 20px; }
      .status-chip { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--muted); background: var(--card-bg); border: 1px solid var(--border); padding: 4px 10px; }
      .status-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--muted); }
      .status-dot.live { background: var(--success); animation: pulse 2s infinite; }
      @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }

      /* Page heading */
      .page-heading { font-size: 1.3rem; font-weight: 700; letter-spacing: -0.02em; color: var(--text); margin: 0 0 4px; }
      .page-sub { font-size: 12px; color: var(--muted); margin: 0 0 20px; }

      /* Footer */
      .footer-info { border-top: 1px solid var(--border); padding-top: 16px; margin-top: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; }
      .footer-text { font-size: 11px; color: var(--muted); }
      .footer-links { display: flex; gap: 8px; }
      .link-pill { font-size: 10px; color: var(--accent); border: 1px solid rgba(45,108,223,0.3); padding: 3px 8px; cursor: pointer; }

      /* Upload */
      .upload-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 16px; }
      .upload-panel { background: var(--card-bg); border: 1px solid var(--border); padding: 20px; }
      .upload-panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
      .upload-panel-title { font-size: 13px; font-weight: 700; color: var(--text); }
      .lap-badge { font-size: 10px; padding: 2px 8px; font-weight: 600; }
      .lap-badge.ref { background: rgba(45,108,223,0.15); color: #7eb3ff; }
      .lap-badge.own { background: rgba(239,68,68,0.15); color: #ff8a8a; }
      .upload-zone { border: 1.5px dashed var(--border); padding: 24px; text-align: center; cursor: pointer; transition: border-color 0.15s; margin-bottom: 12px; }
      .upload-zone:hover, .upload-zone.dragover { border-color: var(--accent); }
      .upload-zone.loaded { border-style: solid; border-color: var(--success); }
      .upload-icon { font-size: 24px; margin-bottom: 8px; display: block; }
      .upload-label { font-size: 12px; color: var(--muted); }
      .upload-hint { font-size: 10px; color: var(--border); margin-top: 4px; }
      .upload-status { background: rgba(34,197,94,0.06); border: 1px solid rgba(34,197,94,0.2); padding: 10px 14px; margin-bottom: 10px; }
      .upload-filename { font-size: 12px; font-weight: 600; font-family: monospace; color: var(--success); margin-bottom: 2px; }

      /* Breadcrumb */
      .breadcrumb-bar { display: flex; align-items: center; gap: 8px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
      .breadcrumb-step { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; border: 1px solid var(--border); color: var(--muted); flex-shrink: 0; }
      .breadcrumb-step.done { background: rgba(34,197,94,0.1); border-color: var(--success); color: var(--success); }
      .breadcrumb-step.active { background: var(--highlight); border-color: var(--highlight); color: white; }
      .breadcrumb-arrow { color: var(--border); font-size: 16px; }
      .breadcrumb-label { font-size: 11px; color: var(--muted); }
      .breadcrumb-step.active + .breadcrumb-label { color: var(--text); }

      /* Summary bar */
      .summary-bar { display: grid; grid-template-columns: repeat(5,1fr); border: 1px solid var(--border); margin-bottom: 20px; }
      .summary-cell { padding: 12px 16px; border-right: 1px solid var(--border); }
      .summary-cell:last-child { border-right: none; }
      .summary-label-sm { font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 700; margin-bottom: 4px; }
      .summary-value { font-size: 16px; font-weight: 700; font-family: monospace; }
      .summary-value.ref { color: var(--accent); }
      .summary-value.own { color: var(--danger); }
      .summary-value.delta-neg { color: var(--danger); }
      .summary-value.delta-pos { color: var(--success); }
      .summary-sub-sm { font-size: 10px; color: var(--muted); margin-top: 2px; }

      /* Analysis cols */
      .analysis-cols { display: grid; grid-template-columns: 1fr 320px; gap: 20px; align-items: start; }
      .panel { background: var(--card-bg); border: 1px solid var(--border); }
      .panel-header { padding: 12px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
      .panel-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); }
      .panel-body { padding: 16px; }

      /* Data table */
      .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
      .data-table th { text-align: left; padding: 6px 10px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); border-bottom: 1px solid var(--border); font-weight: 600; }
      .data-table td { padding: 7px 10px; border-bottom: 1px solid rgba(30,35,48,0.6); color: var(--text); }
      .data-table tr.worst-row { background: rgba(239,68,68,0.04); }
      .data-table tr.total-row { border-top: 2px solid var(--border); font-weight: 700; }
      .delta-neg { color: var(--danger); }
      .delta-pos { color: var(--success); }
      .delta-warn { color: var(--warning); }
      .flag-chip { display: inline-block; font-size: 9px; padding: 1px 5px; font-weight: 600; letter-spacing: 0.04em; margin-right: 2px; }
      .flag-chip.brake { background: rgba(239,68,68,0.12); color: #ff8a8a; }
      .flag-chip.vmin { background: rgba(79,142,247,0.12); color: #7eb3ff; }

      /* Export strip */
      .export-strip { border-top: 1px solid var(--border); padding: 12px 0; display: flex; justify-content: space-between; align-items: center; margin-top: 20px; }

      /* Buttons */
      .btn-primary { background: var(--accent); color: white; border: none; padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer; border-radius: 0; font-family: inherit; transition: background 0.15s; }
      .btn-primary:hover { background: var(--highlight); }
      .btn-primary:disabled { opacity: 0.4; cursor: default; }
      .btn-secondary { background: transparent; color: var(--muted); border: 1px solid var(--border); padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer; border-radius: 0; font-family: inherit; transition: color 0.15s, border-color 0.15s; }
      .btn-secondary:hover { color: var(--text); border-color: rgba(255,255,255,0.2); }
      .btn-ghost { background: transparent; color: var(--muted); border: none; padding: 8px 16px; font-size: 13px; cursor: pointer; font-family: inherit; }
      .btn-mini { font-size: 10px; padding: 4px 10px; background: transparent; border: 1px solid var(--border); color: var(--muted); cursor: pointer; font-family: inherit; border-radius: 0; }
      .btn-featured { background: var(--highlight); color: white; border: none; padding: 8px 20px; font-size: 13px; font-weight: 600; cursor: pointer; border-radius: 0; width: 100%; font-family: inherit; margin-top: 12px; }

      /* Scanline overlay */
      .scanline { position: fixed; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 9999; background: repeating-linear-gradient(0deg, rgba(0,0,0,0.015) 0px, rgba(0,0,0,0.015) 1px, transparent 1px, transparent 2px); }

      /* Bottom actions */
      .bottom-actions { display: flex; justify-content: space-between; align-items: center; padding-top: 16px; border-top: 1px solid var(--border); margin-top: 16px; }
      .readiness-indicators { display: flex; gap: 16px; }
      .readiness-item { font-size: 11px; color: var(--muted); display: flex; align-items: center; gap: 6px; }
      .readiness-item.ok { color: var(--success); }
      .readiness-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }
    </style>""")

    content = ui.column().classes("w-full p-4")
    nav_buttons = []

    async def navigate(step: int):
        state.nav_step = step
        content.clear()
        # Actualizar estado visual de botones
        for i, btn in enumerate(nav_buttons):
            if i == step:
                btn.classes("nav-btn-active", remove="")
            else:
                btn.classes(remove="nav-btn-active")
        with content:
            if step == 0:
                await ng_step0.render(state, navigate)
            elif step == 1:
                await ng_step1.render(state, navigate)
            elif step == 2:
                await ng_step2.render(state, navigate)
            elif step == 3:
                await ng_step3.render(state, navigate)
            elif step == 4:
                await ng_step4.render(state, navigate)

    with ui.left_drawer(fixed=True).classes("sgi-sidebar").style("width:240px"):
        # Brand block
        ui.html("""<div class="sidebar-brand">
            <div class="brand-icon">&#9889;</div>
            <div><div class="brand-name">SimGhostInputs</div>
            <div class="brand-sub">Análisis de simracing</div></div>
        </div>""")

        with ui.column().classes("gap-0 w-full").style("flex:1"):
            ui.html('<div class="nav-section-label">Principal</div>')

            # Steps 0-2: Principal section
            principal_steps = [(0, "Inicio"), (1, "Importar"), (2, "Análisis")]
            for step_idx, step_label in principal_steps:
                _is_current = state.nav_step == step_idx
                _active_cls = " nav-btn-active" if _is_current else ""
                btn = (
                    ui.button(
                        step_label,
                        on_click=lambda s=step_idx: navigate(s),
                    )
                    .classes(f"nav-btn{_active_cls}")
                    .props("flat no-caps align=left")
                )
                nav_buttons.append(btn)

            ui.html('<div class="nav-section-label" style="margin-top:8px">Salidas</div>')

            # Steps 3-4: Salidas section
            salidas_steps = [(3, "Overlay"), (4, "Video")]
            for step_idx, step_label in salidas_steps:
                _is_current = state.nav_step == step_idx
                _active_cls = " nav-btn-active" if _is_current else ""
                btn = (
                    ui.button(
                        step_label,
                        on_click=lambda s=step_idx: navigate(s),
                    )
                    .classes(f"nav-btn{_active_cls}")
                    .props("flat no-caps align=left")
                )
                nav_buttons.append(btn)

        ui.html("""<div class="sidebar-footer">
            <div class="version-badge"><span>v2.0</span> · AMS2 · MoTeC</div>
        </div>""")

    await navigate(state.nav_step)
    ui.html('<div class="scanline"></div>')


def _step_done(state, i):
    checks = [
        state.flow_chosen,
        state.ref_lap is not None,
        state.summary is not None,
        state.last_overlay is not None,
        state.last_compose_video is not None,
    ]
    return checks[i] if i < len(checks) else False


def run():
    ui.run(
        title="SimGhostInputs",
        favicon="👻",
        native=True,
        reload=False,
        storage_secret="sgi-v2-secret",
        port=8765,
    )


if __name__ in ("__main__", "__mp_main__"):
    run()
