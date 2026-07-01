"""NiceGUI entry point para SimGhostInputs v2.0."""

from nicegui import ui

from . import ng_step0, ng_step1, ng_step2, ng_step3, ng_step4
from .ng_helpers import _DEFAULT_FLOW, _FLOWS, _STEPS
from .ng_state import AppState


@ui.page("/")
async def main_page():
    state = AppState()

    ui.add_head_html("""<style>
      body { background: #0e1117; color: #fafafa; font-family: 'Inter', sans-serif; }
      .sgi-sidebar { background: #161b22; min-height: 100vh; padding: 1rem; }
      .step-header { font-size: 1.3rem; font-weight: 700; margin-bottom: 0.5rem; color: #fafafa; }
      .sgi-hero { border: 1px solid #30363d; border-radius: 8px; padding: 1.1rem 1.2rem;
                  background: #161b22; margin-bottom: 1.2rem; }
      .sgi-note { border-left: 4px solid #2d6cdf; background: #0d1117; padding: 0.8rem 1rem;
                  border-radius: 6px; color: #c9d1d9; margin-bottom: 1rem; }
      .nav-btn-active { background: #21262d !important; border-left: 3px solid #58a6ff !important; }
      .nicegui-content { padding: 0 !important; }
      .q-drawer { border-right: 1px solid #30363d; }
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
        with ui.column().classes("gap-1 w-full"):
            ui.label("SimGhostInputs").classes("text-lg font-bold text-white mb-1")
            ui.label("Analisis de simracing").classes("text-xs text-gray-400 mb-3")
            ui.separator()

            flow = _FLOWS.get(state.flow_key, _FLOWS[_DEFAULT_FLOW])
            for i, lbl in enumerate(_STEPS):
                _in_flow = i in flow["steps"]
                _is_current = state.nav_step == i
                _suffix = "" if _in_flow else "  (opc.)"
                _icon = "▶" if _is_current else ("✓" if _step_done(state, i) else "○")
                _base_cls = "w-full text-left text-sm py-2 px-3 rounded"
                _active_cls = " nav-btn-active" if _is_current else ""

                btn = (
                    ui.button(
                        f"{_icon}  {i} · {lbl}{_suffix}",
                        on_click=lambda s=i: navigate(s),
                    )
                    .classes(_base_cls + _active_cls)
                    .props("flat no-caps align=left")
                )
                nav_buttons.append(btn)

            ui.separator().classes("my-2")
            ui.label(f"Flujo: {state.flow_key}").classes("text-xs text-gray-400")
            ui.label("Tus datos nunca salen de tu maquina.").classes("text-xs text-gray-500 mt-2")

    await navigate(state.nav_step)


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
