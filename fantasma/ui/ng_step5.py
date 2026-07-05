"""Paso 5 — Pace Notes: genera cues de audio para CrewChief (NiceGUI)."""

import os

from nicegui import run, ui

from .ng_helpers import render_breadcrumb


async def render(state, navigate):
    render_breadcrumb(5)
    ui.label("Paso 5 — Pace Notes para CrewChief").classes("step-header")
    ui.label(
        "Genera tonos o frases de audio sincronizados con las curvas donde más tiempo pierdes. "
        "El pack resultante se copia al directorio de CrewChief y se activa antes de salir a pista."
    ).classes("text-sm mb-4 text-gray-400")

    if state.rows is None or not state.corners:
        ui.label("Primero corre el Análisis (Paso 2)").classes("text-yellow-400 mb-2")
        ui.button("← Ir al Paso 2", on_click=lambda: navigate(2)).classes("btn-secondary").props(
            "flat"
        )
        return

    _meta = (state.ref_lap.meta or {}) if state.ref_lap else {}
    track = _meta.get("Venue") or _meta.get("track") or _meta.get("trackName") or ""

    from fantasma.viz.pacenotes import crewchief_pacenotes_dir

    _def_outdir = crewchief_pacenotes_dir(track) if track else ""

    # ── Panel: Generación de Pace Notes ──────────────────────────────────────
    with ui.element("div").classes("panel mb-4"):
        ui.html(
            '<div class="panel-header">'
            '<span class="panel-title">① Generación de Pace Notes</span>'
            "</div>"
        )
        with ui.element("div").classes("panel-body"):
            ui.label("Modo").classes("text-sm font-bold text-white mb-1")
            mode_radio = ui.radio(
                {"tones": "Tonos (rápido)", "voice": "Voz", "both": "Ambos"},
                value="tones",
            ).props("inline")

            ui.label("Curvas a cubrir").classes("text-sm font-bold text-white mb-1 mt-3")
            top_number = ui.number(value=5, min=1, max=20, label="Top N curvas").classes("w-32")

            ui.label("Volumen").classes("text-sm font-bold text-white mb-1 mt-3")
            vol_state = {"value": 0.8}
            vol_label = ui.label("0.80").classes("text-xs text-gray-400")
            vol_slider = ui.slider(min=0.1, max=1.0, step=0.05, value=0.8).classes("w-64")

            def _on_vol(e):
                vol_state["value"] = e.value or 0.8
                vol_label.set_text("%.2f" % (e.value or 0.8))

            vol_slider.on("update:model-value", _on_vol)

            _lang_state = {"value": "es-MX"}

            lang_container = ui.column().classes("w-full")
            with lang_container:
                ui.label("Idioma").classes("text-sm font-bold text-white mb-1 mt-3")
                lang_select = ui.select(
                    ["es-MX", "es-ES", "en-US"], value=_lang_state["value"], label="Idioma"
                ).classes("w-48")

            lang_select.on(
                "update:model-value",
                lambda e: _lang_state.update({"value": e.value or "es-MX"}),
            )

            lang_container.set_visibility(False)

            def _update_lang_visibility():
                lang_container.set_visibility(mode_radio.value in ("voice", "both"))

            mode_radio.on("update:model-value", lambda _: _update_lang_visibility())

            ui.label("Directorio de salida").classes("text-sm font-bold text-white mb-1 mt-3")
            with ui.row().classes("w-full gap-2 items-end mb-2"):
                outdir_input = ui.input(
                    label="Carpeta destino (CrewChief)",
                    value=_def_outdir,
                    placeholder=(
                        "Nombre exacto de la pista en CrewChief/AMS2" if not track else _def_outdir
                    ),
                ).classes("flex-1")

                def pick_outdir():
                    from .ng_helpers import _pick_folder

                    picked = _pick_folder(
                        "Elegir carpeta de pace notes",
                        initialdir=outdir_input.value or os.path.expanduser("~"),
                    )
                    if picked:
                        outdir_input.set_value(picked)

                ui.button("Explorar...", on_click=pick_outdir).classes("btn-secondary").props(
                    "flat"
                )

            result_area = ui.column().classes("w-full mb-2")

            async def _generate():
                _outdir = outdir_input.value or ""
                if not _outdir:
                    ui.notify(
                        "Indica la carpeta de destino o el nombre de la pista", type="warning"
                    )
                    return

                _mode = mode_radio.value
                _top = int(top_number.value or 5)
                _vol = float(vol_state["value"])
                _lang = _lang_state["value"] if _mode in ("voice", "both") else "es-MX"
                _rows = state.rows
                _corners = state.corners
                _track = track or None

                result_area.clear()
                with result_area:
                    ui.spinner()
                    ui.label("Generando pace notes...").classes("text-sm text-gray-400")

                def _build():
                    from fantasma.viz.pacenotes import build_pack

                    return build_pack(
                        _rows,
                        _corners,
                        _outdir,
                        mode=_mode,
                        top=_top,
                        volume=_vol,
                        lang=_lang,
                        track_name=_track,
                    )

                try:
                    res = await run.io_bound(_build)
                except Exception as e:
                    result_area.clear()
                    with result_area:
                        ui.notify(str(e), type="negative")
                    return

                state.last_pacenotes = res["outdir"]
                result_area.clear()
                with result_area:
                    if res["entries"] == 0:
                        ui.label(
                            "Aviso: no se generaron entradas "
                            "(revisa si edge-tts y ffmpeg están instalados para modo voz)."
                        ).classes("text-yellow-400 mb-2")
                    else:
                        ui.label("Listo: %d entradas generadas" % res["entries"]).classes(
                            "font-bold text-green-400"
                        )
                    ui.label("Directorio: %s" % res["outdir"]).classes("text-sm text-gray-400 mb-2")
                    ui.label(
                        "Se escribió al directorio de CrewChief; "
                        "actívalo en CrewChief antes de salir a pista."
                    ).classes("text-xs text-gray-400")

            ui.button(
                "Generar Pace Notes",
                on_click=_generate,
            ).classes("btn-primary text-base px-6 py-2").props("flat")

    # ── Panel: Aplicar sonido a video existente ───────────────────────────────
    with ui.element("div").classes("panel mb-4"):
        ui.html(
            '<div class="panel-header">'
            '<span class="panel-title">② Aplicar sonido a video existente</span>'
            "</div>"
        )
        with ui.element("div").classes("panel-body"):
            ui.label(
                "Si ya tienes el video compuesto y solo quieres añadir el audio de pace notes, "
                "usa esta opción. El stream de video se copia sin re-encodear — es mucho más rápido. "
                "Requiere la vuelta del piloto cargada (Paso 1) para sincronizar los cues."
            ).classes("text-xs mb-3 text-gray-400")

            with ui.row().classes("w-full gap-2 items-end mb-2"):
                mux_video_input = ui.input(
                    label="Video existente (mp4, webm, mov...)",
                    placeholder=r"C:\Videos\2_composed.mp4",
                ).classes("flex-1")

                def pick_mux_video():
                    from .ng_helpers import _pick_file

                    p = _pick_file(
                        "Seleccionar video",
                        [("Video", "*.mp4 *.webm *.mov"), ("Todos", "*.*")],
                    )
                    if p:
                        mux_video_input.set_value(p)

                ui.button("Explorar...", on_click=pick_mux_video).classes("btn-secondary").props(
                    "flat"
                )

            with ui.row().classes("w-full gap-2 items-end mb-2"):
                mux_pn_input = ui.input(
                    label="Carpeta del pack de Pace Notes",
                    value=state.last_pacenotes or "",
                    placeholder=r"C:\Users\...\CrewChiefV4\pace_notes\ams2\MiCircuito",
                ).classes("flex-1")

                def pick_mux_pn():
                    from .ng_helpers import _pick_folder

                    p = _pick_folder(
                        "Seleccionar carpeta de Pace Notes",
                        initialdir=mux_pn_input.value or os.path.expanduser("~"),
                    )
                    if p:
                        mux_pn_input.set_value(p)

                ui.button("Explorar...", on_click=pick_mux_pn).classes("btn-secondary").props(
                    "flat"
                )

            with ui.row().classes("w-full gap-2 items-end mb-2"):
                mux_out_input = ui.input(
                    label="Ruta de salida (vacío = junto al video con sufijo _pacenotes)",
                    placeholder=r"C:\Videos\2_composed_pacenotes.mp4",
                ).classes("flex-1")

            ui.label("Volumen de pace notes").classes("text-sm font-bold text-white mb-1 mt-2")
            mux_vol_state = {"value": 1.0}
            mux_vol_label = ui.label("1.00").classes("text-xs text-gray-400")
            mux_vol_slider = ui.slider(min=0.1, max=1.0, step=0.05, value=1.0).classes("w-64")

            def _on_mux_vol(e):
                mux_vol_state["value"] = e.value or 1.0
                mux_vol_label.set_text("%.2f" % (e.value or 1.0))

            mux_vol_slider.on("update:model-value", _on_mux_vol)

            mux_result_area = ui.column().classes("w-full")

            async def _apply_mux():
                _drv_lap = state.drv_lap
                if _drv_lap is None:
                    ui.notify(
                        "Carga primero la vuelta del piloto (Paso 1) para sincronizar",
                        type="warning",
                    )
                    return
                _video = mux_video_input.value or ""
                if not _video:
                    ui.notify("Elige el video al que aplicar el sonido", type="warning")
                    return
                _pn_dir = mux_pn_input.value or ""
                if not _pn_dir:
                    ui.notify("Indica la carpeta del pack de pace notes", type="warning")
                    return
                _out = mux_out_input.value or ""
                if not _out:
                    _base, _ext = os.path.splitext(_video)
                    _out = _base + "_pacenotes" + (_ext or ".mp4")
                _vol = float(mux_vol_state["value"])

                mux_result_area.clear()
                with mux_result_area:
                    ui.spinner()
                    ui.label("Aplicando sonido...").classes("text-sm text-gray-400")

                def _do_mux():
                    from fantasma.viz.compose import mux_pace_notes_into_video

                    return mux_pace_notes_into_video(_video, _pn_dir, _drv_lap, _out, volume=_vol)

                try:
                    result_path = await run.io_bound(_do_mux)
                except Exception as e:
                    mux_result_area.clear()
                    with mux_result_area:
                        ui.notify(str(e), type="negative")
                    return

                mux_result_area.clear()
                with mux_result_area:
                    ui.label("Listo: %s" % result_path).classes("font-bold text-green-400")
                ui.notify(
                    "Video con sonido guardado: %s" % os.path.basename(result_path),
                    type="positive",
                )

            apply_btn = (
                ui.button(
                    "Aplicar sonido",
                    on_click=_apply_mux,
                )
                .classes("btn-primary text-base px-6 py-2 mt-2")
                .props("flat")
            )

            def _update_apply_enabled():
                if state.drv_lap is not None and mux_video_input.value and mux_pn_input.value:
                    apply_btn.enable()
                else:
                    apply_btn.disable()

            mux_video_input.on("update:model-value", lambda _: _update_apply_enabled())
            mux_pn_input.on("update:model-value", lambda _: _update_apply_enabled())
            _update_apply_enabled()
