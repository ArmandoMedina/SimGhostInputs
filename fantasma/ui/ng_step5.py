"""Paso 5 — Pace Notes: genera cues de audio para CrewChief (NiceGUI)."""

import os

from nicegui import run, ui

from .ng_helpers import render_breadcrumb


async def render(state, navigate):
    render_breadcrumb(5)
    ui.label("Paso 5 — Pace Notes para CrewChief").classes("step-header")
    ui.label(
        "Genera tonos o frases de audio sincronizados con las curvas donde mas tiempo pierdes. "
        "El pack resultante se copia al directorio de CrewChief y se activa antes de salir a pista."
    ).classes("text-sm mb-4 text-gray-400")

    if state.rows is None or not state.corners:
        ui.label("Primero corre el Analisis (Paso 2)").classes("text-yellow-400 mb-2")
        ui.button("← Ir al Paso 2", on_click=lambda: navigate(2)).classes("btn-secondary").props(
            "flat"
        )
        return

    _meta = (state.ref_lap.meta or {}) if state.ref_lap else {}
    track = _meta.get("Venue") or _meta.get("track") or _meta.get("trackName") or ""

    from fantasma.viz.pacenotes import crewchief_pacenotes_dir

    _def_outdir = crewchief_pacenotes_dir(track) if track else ""

    # ── Controls ──────────────────────────────────────────────────────────────

    ui.label("Modo").classes("text-sm font-bold text-white mb-1")
    mode_radio = ui.radio(
        {"tones": "Tonos (rapido)", "voice": "Voz", "both": "Ambos"},
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

    lang_container = ui.column().classes("w-full")
    with lang_container:
        ui.label("Idioma").classes("text-sm font-bold text-white mb-1 mt-3")
        lang_select = ui.select(["es-MX", "es-ES", "en-US"], value="es-MX", label="Idioma").classes(
            "w-48"
        )

    lang_container.set_visibility(False)

    def _update_lang_visibility():
        lang_container.set_visibility(mode_radio.value in ("voice", "both"))

    mode_radio.on("update:model-value", lambda _: _update_lang_visibility())

    ui.label("Directorio de salida").classes("text-sm font-bold text-white mb-1 mt-3")
    outdir_input = (
        ui.input(
            label="Carpeta destino (CrewChief)",
            value=_def_outdir,
            placeholder=(
                "Nombre exacto de la pista en CrewChief/AMS2" if not track else _def_outdir
            ),
        )
        .classes("w-full mb-2")
        .style("max-width:600px")
    )

    def pick_outdir():
        from .ng_helpers import _pick_folder

        picked = _pick_folder(
            "Elegir carpeta de pace notes",
            initialdir=outdir_input.value or os.path.expanduser("~"),
        )
        if picked:
            outdir_input.set_value(picked)

    ui.button("Explorar...", on_click=pick_outdir).classes("btn-secondary mb-4").props("flat")

    ui.separator().classes("my-4")

    result_area = ui.column().classes("w-full")

    async def _generate():
        _outdir = outdir_input.value or ""
        if not _outdir:
            ui.notify("Indica la carpeta de destino o el nombre de la pista", type="warning")
            return

        _mode = mode_radio.value
        _top = int(top_number.value or 5)
        _vol = float(vol_state["value"])
        _lang = lang_select.value if _mode in ("voice", "both") else "es-MX"
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
                    "(revisa si edge-tts y ffmpeg estan instalados para modo voz)."
                ).classes("text-yellow-400 mb-2")
            else:
                ui.label("Listo: %d entradas generadas" % res["entries"]).classes(
                    "font-bold text-green-400"
                )
            ui.label("Directorio: %s" % res["outdir"]).classes("text-sm text-gray-400 mb-2")
            ui.label(
                "Se escribio al directorio de CrewChief; "
                "activalo en CrewChief antes de salir a pista."
            ).classes("text-xs text-gray-400")

    ui.button(
        "Generar Pace Notes",
        on_click=_generate,
    ).classes("btn-primary text-base px-6 py-2").props("flat")
