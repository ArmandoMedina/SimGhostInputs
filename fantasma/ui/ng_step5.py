"""Paso 5 — Pace Notes: genera cues de audio para CrewChief (NiceGUI)."""

import os

from nicegui import run, ui

from .ng_helpers import _fmt_lap, render_breadcrumb


async def render(state, navigate):
    render_breadcrumb(5, state.flow_key if state.flow_chosen else None)
    ui.label("Paso 5 — Pace Notes para CrewChief").classes("step-header")
    ui.label(
        "Genera tonos o frases de audio sincronizados con las curvas donde más tiempo pierdes. "
        "El pack resultante se copia al directorio de CrewChief y se activa antes de salir a pista."
    ).classes("text-sm mb-4 text-gray-400")

    _meta = (state.ref_lap.meta or {}) if state.ref_lap else {}
    track = _meta.get("Venue") or _meta.get("track") or _meta.get("trackName") or ""

    from fantasma.viz.pacenotes import crewchief_pacenotes_dir

    _def_outdir = crewchief_pacenotes_dir(track) if track else ""

    ui.label("Primero genera el pack en ①; luego aplícalo a tu video en ②.").classes(
        "text-xs text-gray-400 mb-4"
    )

    # ── Distribución 2 columnas: Generar | Aplicar ────────────────────────────
    with ui.row().classes("gap-4 w-full items-start"):
        # ── Panel: Generación de Pace Notes ──────────────────────────────────
        with ui.element("div").classes("panel mb-4").style("flex:1;min-width:0"):
            ui.html(
                '<div class="panel-header">'
                '<span class="panel-title">① Generación de Pace Notes</span>'
                "</div>"
            )
            with ui.element("div").classes("panel-body"):
                if state.rows is None or not state.corners:
                    ui.label(
                        "Para GENERAR un pack nuevo, corre el Análisis (Paso 2). "
                        "Si YA TIENES el pack y tu video, usa el panel ② de la derecha."
                    ).classes("text-yellow-400 mb-2")
                    ui.button("← Ir al Paso 2", on_click=lambda: navigate(2)).classes(
                        "btn-secondary"
                    ).props("flat")
                else:
                    ui.label("Modo").classes("text-sm font-bold text-white mb-1")
                    mode_radio = (
                        ui.radio(
                            {"tones": "Tonos (rápido)", "voice": "Voz", "both": "Ambos"},
                            value="tones",
                        )
                        .props("inline")
                        .tooltip(
                            "Tonos: bip por curva. Voz: frase hablada (requiere edge-tts+ffmpeg). "
                            "Ambos: bip y frase."
                        )
                    )

                    from fantasma.viz.pacenotes import (
                        COUNTDOWN_SCALE,
                        DEFAULT_COUNTDOWN_S,
                        DEFAULT_FREQS,
                        MILESTONE_LABELS,
                        PLAN_CUES,
                    )

                    with ui.expansion("Leyenda de tonos (qué significa cada bip)").classes(
                        "w-full mt-3"
                    ):
                        ui.label(
                            "Los tonos marcan los puntos de la vuelta de REFERENCIA — dónde "
                            "frena o acelera quien va más rápido. Si no coinciden con lo que "
                            "haces, ese desfase es el consejo, no un error de sincronía."
                        ).classes("text-xs text-gray-400 mb-2")
                        _legend_rows = []
                        for _cue in PLAN_CUES:
                            _base = DEFAULT_FREQS.get(_cue, 0)
                            if _cue == "brake_countdown":
                                # frecuencias y anticipo derivados del motor
                                # (COUNTDOWN_SCALE, DEFAULT_COUNTDOWN_S): si el
                                # sintetizador cambia, la leyenda no miente.
                                _ticks = "-".join(str(round(_base * f)) for f in COUNTDOWN_SCALE)
                                _sound = "3 tics ascendentes (%s Hz), ~%.1f s antes" % (
                                    _ticks,
                                    DEFAULT_COUNTDOWN_S,
                                )
                            else:
                                _sound = "tono corto de %d Hz" % _base
                            _legend_rows.append(
                                {"tono": MILESTONE_LABELS.get(_cue, _cue), "sonido": _sound}
                            )
                        ui.table(
                            rows=_legend_rows,
                            columns=[
                                {
                                    "name": "tono",
                                    "label": "Tono",
                                    "field": "tono",
                                    "align": "left",
                                },
                                {
                                    "name": "sonido",
                                    "label": "Suena como",
                                    "field": "sonido",
                                    "align": "left",
                                },
                            ],
                        ).classes("w-full").props("dense flat hide-bottom")

                    ui.label("Curvas a cubrir").classes("text-sm font-bold text-white mb-1 mt-3")
                    all_corners_chk = ui.checkbox(
                        "Todas las curvas (pace notes de ritmo)", value=False
                    ).tooltip(
                        "Genera cues para todas las curvas detectadas, también donde no "
                        "pierdes tiempo (la frenada suena como marca de ritmo, estilo rally). "
                        "Ignora el Top N."
                    )
                    top_number = (
                        ui.number(value=5, min=1, max=99, label="Top N curvas")
                        .classes("w-32")
                        .tooltip("Cuántas curvas cubrir, de la que más tiempo pierdes hacia abajo.")
                    )

                    # Binding declarativo: sin handler manual (e.value no existe
                    # en GenericEventArguments de NiceGUI 3.14 — Reviewer) y sin
                    # estado que se desincronice si el checkbox se setea por codigo.
                    top_number.bind_enabled_from(all_corners_chk, "value", backward=lambda v: not v)

                    ui.label("Volumen").classes("text-sm font-bold text-white mb-1 mt-3")
                    vol_state = {"value": 0.8}
                    vol_label = ui.label("0.80").classes("text-xs text-gray-400")
                    vol_slider = (
                        ui.slider(min=0.1, max=1.0, step=0.05, value=0.8)
                        .classes("w-64")
                        .tooltip("Nivel de volumen de los archivos de audio generados.")
                    )

                    def _on_vol(e):
                        # on_value_change (ValueChangeEventArguments SI trae
                        # .value); el .on("update:model-value") previo recibia
                        # GenericEventArguments sin .value y moria en silencio,
                        # dejando el volumen clavado en el default (Reviewer).
                        vol_state["value"] = e.value or 0.8
                        vol_label.set_text("%.2f" % (e.value or 0.8))

                    vol_slider.on_value_change(_on_vol)

                    _lang_state = {"value": "es-MX"}

                    lang_container = ui.column().classes("w-full")
                    with lang_container:
                        ui.label("Idioma").classes("text-sm font-bold text-white mb-1 mt-3")
                        lang_select = (
                            ui.select(
                                ["es-MX", "es-ES", "en-US"],
                                value=_lang_state["value"],
                                label="Idioma",
                            )
                            .classes("w-48")
                            .tooltip("Idioma de la voz sintetizada (solo modos Voz y Ambos).")
                        )

                    lang_select.on_value_change(
                        lambda e: _lang_state.update({"value": e.value or "es-MX"})
                    )

                    lang_container.set_visibility(False)

                    def _update_lang_visibility():
                        lang_container.set_visibility(mode_radio.value in ("voice", "both"))

                    mode_radio.on_value_change(lambda _: _update_lang_visibility())

                    ui.label("Directorio de salida").classes(
                        "text-sm font-bold text-white mb-1 mt-3"
                    )
                    with ui.row().classes("w-full gap-2 items-end mb-2"):
                        outdir_input = (
                            ui.input(
                                label="Carpeta destino (CrewChief)",
                                value=_def_outdir,
                                placeholder=(
                                    "Nombre exacto de la pista en CrewChief/AMS2"
                                    if not track
                                    else _def_outdir
                                ),
                            )
                            .classes("flex-1")
                            .tooltip("Carpeta donde se guardan los archivos WAV del pack.")
                        )

                        def pick_outdir():
                            from .ng_helpers import _pick_folder

                            picked = _pick_folder(
                                "Elegir carpeta de pace notes",
                                initialdir=outdir_input.value or os.path.expanduser("~"),
                            )
                            if picked:
                                outdir_input.set_value(picked)

                        ui.button("Explorar...", on_click=pick_outdir).classes(
                            "btn-secondary"
                        ).props("flat").tooltip("Abrir selector de carpeta.")

                    result_area = ui.column().classes("w-full mb-2")

                    async def _generate():
                        _outdir = outdir_input.value or ""
                        if not _outdir:
                            ui.notify(
                                "Indica la carpeta de destino o el nombre de la pista",
                                type="warning",
                            )
                            return

                        _mode = mode_radio.value
                        # top=0 = todas las curvas (ADR 0024)
                        _top = 0 if all_corners_chk.value else int(top_number.value or 5)
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
                            ui.label("Directorio: %s" % res["outdir"]).classes(
                                "text-sm text-gray-400 mb-2"
                            )
                            ui.label(
                                "Se escribió al directorio de CrewChief; "
                                "actívalo en CrewChief antes de salir a pista."
                            ).classes("text-xs text-gray-400")

                    ui.button(
                        "Generar Pace Notes",
                        on_click=_generate,
                    ).classes("btn-primary text-base px-6 py-2").props("flat").tooltip(
                        "Genera los archivos de audio del pack en la carpeta indicada."
                    )

        # ── Panel: Aplicar sonido a video existente ───────────────────────────
        with ui.element("div").classes("panel mb-4").style("flex:1;min-width:0"):
            ui.html(
                '<div class="panel-header">'
                '<span class="panel-title">② Aplicar sonido a video existente</span>'
                "</div>"
            )
            with ui.element("div").classes("panel-body"):
                ui.label(
                    "Si ya tienes el video compuesto y solo quieres añadir el audio de pace notes, "
                    "usa esta opción. El stream de video se copia sin re-encodear — es mucho más "
                    "rápido. Requiere la vuelta del piloto cargada (Paso 1) para sincronizar los "
                    "cues."
                ).classes("text-xs mb-3 text-gray-400")

                with ui.row().classes("w-full gap-2 items-end mb-2"):
                    mux_video_input = (
                        ui.input(
                            label="Video existente (mp4, webm, mov...)",
                            placeholder=r"C:\Videos\2_composed.mp4",
                        )
                        .classes("flex-1")
                        .tooltip(
                            "Tu video ya compuesto; no se re-encodea, solo se le mezcla el audio."
                        )
                    )

                    def pick_mux_video():
                        from .ng_helpers import _pick_file

                        p = _pick_file(
                            "Seleccionar video",
                            [("Video", "*.mp4 *.webm *.mov"), ("Todos", "*.*")],
                        )
                        if p:
                            # set_value dispara on_value_change: el refresh del
                            # boton y del sidecar viene por ahi.
                            mux_video_input.set_value(p)

                    ui.button("Explorar...", on_click=pick_mux_video).classes(
                        "btn-secondary"
                    ).props("flat").tooltip("Abrir selector de archivo de video.")

                sidecar_label = ui.label("").classes("text-xs mb-2")

                def _update_sidecar_label():
                    """Coteja el sidecar .sync.json del video (ADR 0024) contra la
                    vuelta cargada, para avisar ANTES de apretar el botón. El
                    criterio vive en compose.sync_sidecar_mismatch — la misma
                    fuente que usa el mux para negarse, así aviso y rechazo no
                    pueden contradecirse (Reviewer)."""
                    sidecar_label.set_text("")
                    sidecar_label.classes(remove="text-yellow-400 text-green-500")
                    _v = mux_video_input.value or ""
                    _lap = state.drv_lap
                    if not _v or _lap is None:
                        return
                    from fantasma.viz.compose import read_sync_sidecar, sync_sidecar_mismatch

                    if read_sync_sidecar(_v) is None:
                        return  # video externo sin sidecar: nada que cotejar
                    _mm = sync_sidecar_mismatch(_v, _lap, source_name=state.drv_name)
                    if _mm is not None:
                        _src = os.path.basename(str(_mm["csv_path"] or "")) or "csv desconocido"
                        sidecar_label.set_text(
                            "⚠ Este video se compuso con una vuelta de %s (%s); la vuelta "
                            "cargada dura %s. El mux se negará: carga esa vuelta en el Paso 1."
                            % (_fmt_lap(_mm["expected"]), _src, _fmt_lap(_mm["actual"]))
                        )
                        sidecar_label.classes(add="text-yellow-400")
                    else:
                        sidecar_label.set_text(
                            "✓ Video verificado: corresponde a la vuelta cargada (%s)."
                            % _fmt_lap(_lap.laptime)
                        )
                        sidecar_label.classes(add="text-green-500")

                with ui.row().classes("w-full gap-2 items-end mb-2"):
                    mux_pn_input = (
                        ui.input(
                            label="Carpeta del pack de Pace Notes",
                            value=state.last_pacenotes or "",
                            placeholder=r"C:\Users\...\CrewChiefV4\pace_notes\ams2\MiCircuito",
                        )
                        .classes("flex-1")
                        .tooltip("Carpeta del pack generado en el panel ① (o uno anterior).")
                    )

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
                    ).tooltip("Abrir selector de carpeta del pack.")

                with ui.row().classes("w-full gap-2 items-end mb-2"):
                    mux_out_input = (
                        ui.input(
                            label="Ruta de salida (vacío = junto al video con sufijo _pacenotes)",
                            placeholder=r"C:\Videos\2_composed_pacenotes.mp4",
                        )
                        .classes("flex-1")
                        .tooltip(
                            "Ruta del video de salida con el sonido mezclado; "
                            "vacío usa el nombre del video con sufijo _pacenotes."
                        )
                    )

                ui.label("Volumen de pace notes").classes("text-sm font-bold text-white mb-1 mt-2")
                mux_vol_state = {"value": 1.0}
                mux_vol_label = ui.label("1.00").classes("text-xs text-gray-400")
                mux_vol_slider = (
                    ui.slider(min=0.1, max=1.0, step=0.05, value=1.0)
                    .classes("w-64")
                    .tooltip("Nivel de volumen del audio de pace notes en la mezcla.")
                )

                def _on_mux_vol(e):
                    mux_vol_state["value"] = e.value or 1.0
                    mux_vol_label.set_text("%.2f" % (e.value or 1.0))

                mux_vol_slider.on_value_change(_on_mux_vol)

                mux_result_area = ui.column().classes("w-full")

                _mux_state = {"running": False}

                async def _apply_mux():
                    # Guard de doble-click: ignora clicks mientras hay un mux en curso
                    # (evita dos procesos ffmpeg escribiendo al mismo archivo de salida).
                    if _mux_state["running"]:
                        return
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

                    _mux_state["running"] = True
                    apply_btn.disable()
                    mux_result_area.clear()
                    with mux_result_area:
                        ui.spinner()
                        ui.label("Aplicando sonido...").classes("text-sm text-gray-400")

                    def _do_mux():
                        from fantasma.viz.compose import mux_pace_notes_into_video

                        return mux_pace_notes_into_video(
                            _video,
                            _pn_dir,
                            _drv_lap,
                            _out,
                            volume=_vol,
                            source_name=state.drv_name,
                        )

                    try:
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
                    finally:
                        _mux_state["running"] = False
                        _update_apply_enabled()

                apply_btn = (
                    ui.button(
                        "Aplicar sonido",
                        on_click=_apply_mux,
                    )
                    .classes("btn-primary text-base px-6 py-2 mt-2")
                    .props("flat")
                    .tooltip(
                        "Mezcla el audio del pack al video; "
                        "copia el stream de video sin re-encodear."
                    )
                )
                # El botón gris sin explicación fue reporte directo del PO
                # (QA 2026-07-05): este caption dice QUÉ falta para habilitarlo.
                apply_hint = ui.label("").classes("text-xs text-yellow-400 mt-1")

                def _update_apply_enabled():
                    faltan = []
                    if state.drv_lap is None:
                        faltan.append("la vuelta del piloto (Paso 1)")
                    if not mux_video_input.value:
                        faltan.append("el video")
                    if not mux_pn_input.value:
                        faltan.append("la carpeta del pack")
                    if faltan:
                        apply_btn.disable()
                        apply_hint.set_text("Falta: " + ", ".join(faltan) + ".")
                    else:
                        apply_btn.enable()
                        apply_hint.set_text("")

                # on_value_change y NO .on("update:model-value"): el handler DOM
                # corre ANTES de que NiceGUI asigne element.value, asi que estos
                # refreshes leian el valor anterior y todo iba "una accion atras"
                # (el boton gris fantasma del QA del PO). El sidecar (I/O de
                # disco) solo se relee cuando cambia el VIDEO, con debounce para
                # no hacer stat por keystroke (rutas de red congelan el loop).
                mux_video_input.props("debounce=400")
                mux_video_input.on_value_change(
                    lambda _: (_update_apply_enabled(), _update_sidecar_label())
                )
                mux_pn_input.on_value_change(lambda _: _update_apply_enabled())
                _update_apply_enabled()
                _update_sidecar_label()
