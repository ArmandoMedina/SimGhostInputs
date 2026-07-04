"""Paso 3 — Overlay: generar el HUD animado (NiceGUI)."""

import os
import shutil

from nicegui import run, ui

from .ng_helpers import _DEFAULT_FLOW, _FLOWS, _STEPS, render_breadcrumb, start_bg_render


async def render(state, navigate):
    render_breadcrumb(3)
    ui.label("Paso 3 — Generar overlay HUD").classes("step-header")
    ui.label(
        "Genera el HUD animado sincronizado con tu vuelta. "
        "Es un archivo de video transparente (como un sticker animado) que en el Paso 4 "
        "se pega encima de tu grabacion. Muestra: barras de gas y freno, delta acumulado, "
        "velocidad, marcha, volante y G-lateral."
    ).classes("text-sm mb-4 text-gray-400")

    if shutil.which("ffmpeg") is None:
        import platform as _pl

        _os = _pl.system()
        _install_cmd = (
            "`winget install Gyan.FFmpeg`"
            if _os == "Windows"
            else "`brew install ffmpeg`"
            if _os == "Darwin"
            else "`sudo apt install ffmpeg`"
        )
        ui.label(
            f"ffmpeg no esta instalado y este paso lo necesita. "
            f"Instalalo y abre una terminal nueva: {_install_cmd}"
        ).classes("mb-4 text-red-400")
        return

    if state.ref_lap is None:
        ui.label("Primero carga los archivos en el Paso 1.").classes("text-yellow-400")
        ui.button("← Ir al Paso 1", on_click=lambda: navigate(1)).classes("btn-secondary").props(
            "flat"
        )
        return

    ref_lap = state.ref_lap
    drv_lap = state.drv_lap
    corners = state.corners if state.corners_editable else None

    if not corners:
        try:

            def _detect():
                from fantasma.core.corners import detect_corners, extract_milestones

                _evs, _ = detect_corners(ref_lap)
                return extract_milestones(ref_lap, _evs)

            corners = await run.io_bound(_detect)
            state.corners = corners
        except Exception:
            corners = []

    # Si ya hay overlay generado
    if state.last_overlay:
        ui.label(
            "✓ Ya tienes un overlay generado: %s" % os.path.basename(state.last_overlay)
        ).classes("mb-1 text-green-400")
        ui.label(
            "Si quieres regenerarlo con distintos parametros, usa las opciones de abajo."
        ).classes("text-xs mb-2 text-gray-400")
        _render_next_btn(state, 3, navigate)
        ui.separator().classes("my-4")

    # Carpeta de salida
    _def_out = os.path.join(os.path.expanduser("~"), "fantasma_salida")
    out_dir_input = (
        ui.input(
            label="Carpeta donde guardar el overlay",
            value=_def_out,
            placeholder=_def_out,
        )
        .classes("w-full mb-2")
        .style("max-width:600px")
        .props('input-style="color: white" label-color="grey-4"')
    )

    def pick_outdir():
        from .ng_helpers import _pick_folder

        picked = _pick_folder(
            "Elegir carpeta de salida", initialdir=out_dir_input.value or _def_out
        )
        if picked:
            out_dir_input.set_value(picked)

    ui.button("Explorar...", on_click=pick_outdir).classes("btn-secondary mb-4").props("flat")

    # FPS
    ui.label("FPS del overlay").classes("text-sm font-bold text-white mb-1")
    ui.label(
        "Usa el mismo valor que tiene tu video de grabacion. "
        "Si no sabes, 30 fps es el estandar mas comun."
    ).classes("text-xs mb-2 text-gray-400")

    fps_radio = ui.radio({24: "24 fps", 30: "30 fps", 60: "60 fps"}, value=30).props("inline")

    # Encadenado overlay a compose (solo en flujo compose)
    if state.flow_key == "compose":
        auto_cb = ui.checkbox("Al terminar, componer automaticamente", value=state.auto_compose)
        auto_cb.on_value_change(lambda e: setattr(state, "auto_compose", e.value))

    # Formato (solo relevante en flujo Solo overlay)
    fmt_state = {"value": "webm"}
    if state.flow_key == "overlay":
        with ui.expansion("Formato de salida", icon="settings").classes("w-full mb-2"):
            ui.label(
                "webm — Recomendado. Compatible con DaVinci Resolve, Kdenlive, Premiere."
            ).classes("text-xs text-gray-400")
            ui.label("prores — Para Final Cut Pro en Mac o maxima calidad sin compresion.").classes(
                "text-xs text-gray-400"
            )
            ui.label("png — Frames sueltos (una imagen por fotograma). Uso avanzado.").classes(
                "text-xs text-gray-400"
            )
            fmt_sel = ui.select(["webm", "prores", "png"], value="webm", label="Formato").classes(
                "w-48"
            )
            fmt_sel.on("update:model-value", lambda e: fmt_state.update({"value": e.value}))

    ui.html("""<div class="sgi-note" style="margin-bottom:1rem">
      <strong>Tiempo estimado de render:</strong> entre 5 y 30 minutos dependiendo de la duracion
      de la vuelta y el numero de cores de tu PC. El render usa todos los cores disponibles en paralelo.
      Tu PC seguira disponible mientras renderiza, solo ira mas lenta.
    </div>""")

    ui.separator().classes("my-4")

    # Area de resultado/progreso
    result_area = ui.column().classes("w-full")
    render_area = ui.column().classes("w-full")

    # Variable de estado del job activo (en closure)
    job_holder = {"job": None, "timer": None}
    _gen_btn_ref = {"btn": None}

    def _start_render():
        # Guard: ignorar clicks mientras hay un render en curso
        if job_holder["job"] is not None and not job_holder["job"].done:
            return
        if _gen_btn_ref["btn"] is not None:
            _gen_btn_ref["btn"].disable()

        out_dir = out_dir_input.value or _def_out
        _fps = fps_radio.value or 30
        _fmt = fmt_state["value"]

        try:
            from fantasma.viz.overlay import render_overlay as _ro
        except ImportError:
            result_area.clear()
            with result_area:
                ui.label(
                    'Faltan dependencias. Ejecuta: pip install "fantasma-inputs[overlay]"'
                ).classes("text-red-400")
            return

        os.makedirs(out_dir, exist_ok=True)
        job = start_bg_render(
            _ro,
            progress_kw="progress",
            ref=ref_lap,
            drv=drv_lap,
            corners=corners or [],
            outdir=out_dir,
            fps=_fps,
            fmt=_fmt,
        )
        job_holder["job"] = job

        render_area.clear()
        with render_area:
            progress_bar = ui.linear_progress(value=0).classes("w-full")
            status_label = ui.label("Iniciando...").classes("text-sm text-gray-400")

            def cancel():
                if job_holder["job"]:
                    job_holder["job"].cancel()

            cancel_btn = (
                ui.button("Detener render", on_click=cancel).classes("btn-secondary").props("flat")
            )

        async def poll():
            _job = job_holder["job"]
            if _job is None:
                return
            if _job.done:
                if job_holder["timer"]:
                    job_holder["timer"].cancel()
                    job_holder["timer"] = None
                progress_bar.delete()
                status_label.delete()
                cancel_btn.delete()
                if _gen_btn_ref["btn"] is not None:
                    _gen_btn_ref["btn"].enable()
                result_area.clear()
                with result_area:
                    if _job.error == "__CANCELLED__":
                        ui.label("Render cancelado.").classes("text-yellow-400")
                    elif _job.error:
                        if "ImportError" in str(_job.error) or "No module" in str(_job.error):
                            ui.label(
                                'Faltan dependencias. Ejecuta: pip install "fantasma-inputs[overlay]"'
                            ).classes("text-red-400")
                        else:
                            ui.label(f"Error en el render: {_job.error}").classes("text-red-400")
                    else:
                        state.last_overlay = _job.result
                        ui.label("✓ Overlay generado: %s" % os.path.basename(_job.result)).classes(
                            "font-bold text-green-400"
                        )
                        _next = _FLOWS.get(state.flow_key, _FLOWS[_DEFAULT_FLOW])["next"].get(3)
                        if state.auto_compose and _next == 4:
                            state.pending_autocompose = True
                            await navigate(4)
                        else:
                            _render_next_btn(state, 3, navigate)
                return
            pct = _job.n / _job.total if _job.total > 0 else 0
            progress_bar.set_value(pct)
            status_label.set_text(
                _job.status or ("Frame %d / %d (%.0f%%)" % (_job.n, _job.total, pct * 100))
            )

        timer = ui.timer(0.5, poll)
        job_holder["timer"] = timer

        def _cancel_on_nav():
            t = job_holder.get("timer")
            if t is not None:
                try:
                    t.cancel()
                except Exception:
                    pass
                job_holder["timer"] = None

        navigate._cancel_render = _cancel_on_nav

    if not job_holder["job"] or job_holder["job"].done:
        _gen_btn_ref["btn"] = (
            ui.button(
                "Generar overlay",
                on_click=_start_render,
            )
            .classes("btn-primary text-base px-6 py-2")
            .props("flat")
        )


def _render_next_btn(state, current_step, navigate):
    flow = _FLOWS.get(state.flow_key, _FLOWS[_DEFAULT_FLOW])
    next_i = flow["next"].get(current_step)
    if next_i is None:
        ui.label("Completaste todos los pasos de tu flujo!").classes("font-bold text-green-400")
    else:
        ui.button(
            "Ir al Paso %d — %s →" % (next_i, _STEPS[next_i]),
            on_click=lambda: navigate(next_i),
        ).classes("btn-primary").props("flat")
