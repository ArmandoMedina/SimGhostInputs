"""Paso 4 — Componer: superponer overlay sobre la grabacion (NiceGUI).

La pieza estrella: preview reactiva del HUD en tiempo real mientras
el usuario mueve los sliders, sin recargar la pagina.
"""

import base64
import io as _io
import os
import shutil

from nicegui import run, ui

from .ng_helpers import (
    _DEFAULT_FLOW,
    _FLOWS,
    _POS_LABELS,
    _STEPS,
    _fmt_lap,
    _sync_quality_label,
    render_breadcrumb,
    start_bg_render,
)


async def render(state, navigate):
    render_breadcrumb(4)
    # Pide permiso de notificacion al entrar — fire-and-forget para no bloquear el render
    try:
        import asyncio as _asyncio

        _loop = _asyncio.get_event_loop()
        if _loop.is_running():
            _loop.create_task(
                ui.run_javascript(
                    "if ('Notification' in window && Notification.permission === 'default') "
                    "Notification.requestPermission()"
                )
            )
    except Exception:
        pass
    ui.label("Paso 4 — Componer video final").classes("step-header")
    ui.label(
        "Junta el overlay del Paso 3 con tu video de grabación. "
        "El resultado es un clip MP4 recortado exactamente a la duración de tu vuelta, "
        "con el HUD ya integrado y listo para subir."
    ).classes("text-sm mb-4 text-gray-400")

    # Prerrequisito: ffmpeg
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
            f"ffmpeg no está instalado y este paso lo necesita. "
            f"Instálalo y abre una terminal nueva: {_install_cmd}"
        ).classes("mb-4 text-red-400")
        return

    with ui.row().classes("gap-4 mb-4 w-full"):
        ui.html(
            '<div style="flex:1;background:var(--warning-bg);border:1px solid var(--warning-border);border-radius:6px;padding:0.8rem">'
            '<strong style="color:#facc15">El video DEBE tener audio del motor activado.</strong><br>'
            '<span style="color:#d1b47a;font-size:0.8rem">La sincronía automática analiza el sonido del motor para encontrar '
            "el segundo exacto en que cruzaste la meta. Sin audio tendrás que calcular el offset manualmente.</span>"
            "</div>"
        )
        ui.html(
            '<div style="flex:1;background:var(--info-bg);border:1px solid var(--info-border);border-radius:6px;padding:0.8rem">'
            '<strong style="color:#60a5fa">El output no es el video completo de tu sesion.</strong><br>'
            '<span style="color:#93c5fd;font-size:0.8rem">Se genera un clip recortado exactamente a tu vuelta: '
            "desde la meta hasta que la terminas. Mucho mas rapido de procesar y mas facil de compartir.</span>"
            "</div>"
        )

    ui.separator().classes("my-4")

    # ── Archivos de entrada ───────────────────────────────────────────────────
    ui.label("① Archivos de entrada").classes("text-sm font-bold text-white mb-2")

    with ui.row().classes("w-full gap-2 items-end mb-2"):
        video_input = ui.input(
            label="Tu video de grabación",
            value=state.last_compose_video or "",
            placeholder=r"C:\Videos\mi_sesion.mp4",
        ).classes("flex-1")

        def pick_video():
            from .ng_helpers import _pick_file

            p = _pick_file(
                "Seleccionar video de grabacion",
                [("Video", "*.mp4 *.mov *.mkv *.avi"), ("Todos", "*.*")],
            )
            if p:
                video_input.set_value(p)
                state.last_compose_video = p

        ui.button("Explorar...", on_click=pick_video).classes("btn-secondary").props("flat")

    with ui.row().classes("w-full gap-2 items-end mb-4"):
        overlay_input = ui.input(
            label="Overlay del HUD (generado en el Paso 3)",
            value=state.last_overlay or "",
            placeholder=r"C:\Users\TuNombre\fantasma_salida\overlay.webm",
        ).classes("flex-1")

        def pick_overlay():
            from .ng_helpers import _pick_file

            p = _pick_file(
                "Seleccionar overlay",
                [("WebM / MOV", "*.webm *.mov"), ("Todos", "*.*")],
            )
            if p:
                overlay_input.set_value(p)
                state.last_overlay = p

        ui.button("Explorar...", on_click=pick_overlay).classes("btn-secondary").props("flat")

    # ── Sincronia ─────────────────────────────────────────────────────────────
    ui.separator().classes("my-4")
    ui.label("② Sincronía: en qué segundo del video empieza tu vuelta?").classes(
        "text-sm font-bold text-white mb-1"
    )
    ui.label(
        "SimGhostInputs escucha el sonido del motor en tu video y lo compara con los RPM de la "
        "telemetría para encontrar automáticamente el segundo exacto en que cruzaste la meta. "
        "Precisión ~0.5 s · tarda ~30 segundos · necesitas scipy instalado."
    ).classes("text-xs mb-2 text-gray-400")

    drv_for_sync = state.drv_lap
    sync_result_area = ui.column().classes("w-full mb-2")
    sync_state = {
        "offset": state.compose_offset or 0.0,
        "z": None,
        "ambiguous": False,
        "candidates": [],
        "resolved": False,
        "error": None,
    }

    if drv_for_sync is None:
        ui.label(
            "Sube TU telemetria — la misma vuelta que grabaste en el video. "
            "No subas la de referencia: el sync compara el audio de tu motor con tus RPM."
        ).classes("text-sm mb-2 text-yellow-400")

        sync_drv_state = {"laps": None}

        async def handle_sync_drv(e):
            from .ng_helpers import _cleanup_upload, _load_laps, _save_upload

            content = await e.file.read()
            suffix = os.path.splitext(e.file.name)[1] or ".csv"
            path = _save_upload(content, suffix)
            try:
                laps = _load_laps(path)
            except Exception as ex:
                ui.notify(f"Error: {ex}", type="negative")
                return
            finally:
                _cleanup_upload(path)
            if laps:
                from fantasma.core.normalize import fastest_lap as _fl

                sync_drv_state["laps"] = laps
                drv_for_sync_local = _fl(laps)
                state.drv_lap = drv_for_sync_local
                ui.notify("Tu telemetria cargada.", type="positive")

        ui.upload(
            label="Tu CSV — la vuelta del video (NO la de referencia)",
            on_upload=handle_sync_drv,
            auto_upload=True,
        ).props('accept=".csv,.xlsx"').classes("mb-2")
    else:
        ui.label(
            "Usando tu vuelta del Paso 1 (%s) — la que corresponde al video."
            % _fmt_lap(drv_for_sync.laptime)
        ).classes("text-xs mb-2 text-gray-400")

    async def do_autosync():
        _video = video_input.value
        _drv = state.drv_lap
        if not _video or not _drv:
            ui.notify(
                "Necesitas el video y la telemetria para la deteccion automatica.", type="warning"
            )
            return
        sync_result_area.clear()
        with sync_result_area:
            ui.label("Analizando audio... (~30 s)").classes("text-sm text-gray-400")
        try:

            def _sync():
                from fantasma.viz.sync import _MIN_SYNC_Z, sync_candidates

                return sync_candidates(_video, _drv), _MIN_SYNC_Z

            res, MIN_Z = await run.io_bound(_sync)
        except ImportError as ie:
            sync_result_area.clear()
            with sync_result_area:
                ui.label(str(ie)).classes("text-sm text-red-400")
            return
        except Exception as se:
            sync_result_area.clear()
            with sync_result_area:
                ui.label(f"Error en auto-sync: {se}").classes("text-sm text-red-400")
            return

        sync_result_area.clear()
        cs = res["candidates"]
        with sync_result_area:
            if not cs or cs[0]["z"] < MIN_Z:
                ui.label(
                    "Correlación insuficiente: el video no parece corresponder a tu vuelta. "
                    "Usa la sincronía manual de abajo."
                ).classes("text-sm text-yellow-400")
                sync_state["error"] = True
            elif res["ambiguous"]:
                sync_state["ambiguous"] = True
                sync_state["candidates"] = cs
                ui.label(
                    "Tu video parece tener varias vueltas y suenan casi igual. Elige la que corresponde a tu vuelta."
                ).classes("text-sm mb-2 text-yellow-400")
                opts = {
                    i: "%s min · calidad %.1f sigma" % (cs[i]["mmss"], cs[i]["z"])
                    for i in range(len(cs))
                }
                choice_radio = ui.radio(opts, value=0)

                def confirm_choice():
                    idx = choice_radio.value
                    c = cs[idx]
                    sync_state["offset"] = c["offset"]
                    sync_state["z"] = c["z"]
                    sync_state["resolved"] = True
                    state.compose_offset = c["offset"]
                    offset_input.set_value(c["offset"])
                    ui.notify(f"Offset {c['offset']:.3f} s seleccionado.", type="positive")

                ui.button("Confirmar esta vuelta", on_click=confirm_choice).props("color=primary")
            else:
                _off = cs[0]["offset"]
                _z = cs[0]["z"]
                _ql = _sync_quality_label(_z)
                sync_state["offset"] = _off
                sync_state["z"] = _z
                state.compose_offset = _off
                offset_input.set_value(_off)
                ui.label(
                    "Offset detectado: %.3f s desde el inicio del video hasta el cruce de meta. "
                    "Calidad de sincronía: %s." % (_off, _ql)
                ).classes("text-sm text-green-400")
                # Zona gris
                try:
                    from fantasma.viz.sync import sync_gray_zone_warning

                    gz = sync_gray_zone_warning(_z)
                    if gz:
                        ui.label("⚠ " + gz[0].upper() + gz[1:]).classes("text-sm text-yellow-400")
                except ImportError:
                    pass

    ui.button(
        "Detectar sincronia automaticamente",
        on_click=do_autosync,
    ).props("color=primary").classes("mb-2")

    with ui.expansion(
        "Sincronizar manualmente (si la detección automática falló)", icon="tune"
    ).classes("w-full mb-4"):
        ui.markdown(
            "**Como encontrar el offset manualmente:**\n"
            "1. Abre el video en VLC.\n"
            "2. Busca el momento en que cruzas la linea de meta.\n"
            "3. Lee el tiempo en la barra de reproduccion (p. ej. `0:00:17`).\n"
            "4. Escribe ese valor en segundos abajo (p. ej. `17`)."
        )

    # ── Parametros del HUD + PREVIEW REACTIVA ────────────────────────────────
    ui.separator().classes("my-4")
    ui.label("③ Parámetros del HUD").classes("text-sm font-bold text-white mb-2")

    with ui.row().classes("gap-8 items-start w-full"):
        with ui.column().classes("gap-3").style("min-width:200px"):
            pos_select = ui.select(
                list(_POS_LABELS.keys()),
                value="Abajo derecha",
                label="Posición del HUD",
            ).classes("w-48")

            scale_slider = ui.slider(min=0.25, max=1.5, step=0.05, value=1.0).classes("w-48")
            scale_label = ui.label("Tamaño: 1.00×").classes("text-xs text-gray-400")

            offset_input = ui.number(
                label="Offset (s desde inicio del video hasta la meta)",
                value=state.compose_offset or 0.0,
                step=0.1,
                format="%.1f",
            ).classes("w-48")
            offset_input.on(
                "update:model-value",
                lambda e: state.__setattr__("compose_offset", float(e.value or 0.0)),
            )

        with ui.column().classes("gap-2"):
            preview_img = (
                ui.image("")
                .classes("rounded border border-gray-700")
                .style("max-width:420px;max-height:260px;background:#1e1e1e")
            )
            preview_status = ui.label("Carga el overlay para ver la preview").classes(
                "text-xs text-gray-500"
            )

    async def update_preview():
        _overlay_path = overlay_input.value
        if not _overlay_path or not os.path.exists(_overlay_path):
            return
        try:
            from fantasma.viz.hud_preview import compose_preview_frame

            pos = _POS_LABELS[pos_select.value]
            scale = scale_slider.value

            pil_img = await run.io_bound(compose_preview_frame, _overlay_path, pos, scale)
            buf = _io.BytesIO()
            pil_img.save(buf, format="PNG")
            buf.seek(0)
            b64 = base64.b64encode(buf.read()).decode()
            preview_img.set_source(f"data:image/png;base64,{b64}")
            preview_status.set_text("")
        except Exception as e:
            preview_status.set_text(f"Preview no disponible: {e}")

    pos_select.on("update:model-value", lambda _: update_preview())
    scale_slider.on(
        "update:model-value",
        lambda e: scale_label.set_text("Tamaño: %.2f×" % (e.value or 1.0)),
    )
    scale_slider.on("update:model-value", lambda _: update_preview())
    overlay_input.on("update:model-value", lambda _: update_preview())

    # Trigger inicial si ya hay overlay
    if state.last_overlay and os.path.exists(state.last_overlay):
        await update_preview()

    # ── Carpeta de salida ─────────────────────────────────────────────────────
    ui.separator().classes("my-4")
    ui.label("④ Carpeta de salida").classes("text-sm font-bold text-white mb-2")

    def _def_out_folder():
        _ov = overlay_input.value or ""
        _vi = video_input.value or ""
        if _ov and os.path.dirname(_ov):
            return os.path.dirname(_ov)
        if _vi and os.path.dirname(_vi):
            return os.path.dirname(_vi)
        return os.path.expanduser("~")

    out_folder_input = (
        ui.input(
            label="Carpeta donde guardar el video final",
            value=_def_out_folder(),
        )
        .classes("w-full mb-2")
        .style("max-width:600px")
    )

    def pick_out_folder():
        from .ng_helpers import _pick_folder

        p = _pick_folder(
            "Carpeta de salida", initialdir=out_folder_input.value or _def_out_folder()
        )
        if p:
            out_folder_input.set_value(p)

    ui.button("Explorar...", on_click=pick_out_folder).classes("btn-secondary mb-4").props("flat")

    # ── Pace Notes en el video compuesto (opcional) ───────────────────────────
    ui.separator().classes("my-4")
    ui.label("⑤ Pace Notes en el video compuesto (opcional)").classes(
        "text-sm font-bold text-white mb-2"
    )
    ui.label(
        "Mezcla los sonidos del pack de Pace Notes directamente en el audio del video final. "
        "Requiere haber generado el pack en el Paso 5 o indicar su carpeta aquí."
    ).classes("text-xs mb-2 text-gray-400")

    pn_check = ui.checkbox("Incluir pace notes en el video")
    pn_section = ui.column().classes("w-full mt-2")

    with pn_section:
        with ui.row().classes("w-full gap-2 items-end mb-2"):
            pn_dir_input = ui.input(
                label="Carpeta del pack de Pace Notes",
                value=state.last_pacenotes or "",
                placeholder=r"C:\Users\...\CrewChiefV4\pace_notes\ams2\MiCircuito",
            ).classes("flex-1")

            def pick_pn_folder():
                from .ng_helpers import _pick_folder

                p = _pick_folder(
                    "Seleccionar carpeta de Pace Notes",
                    initialdir=pn_dir_input.value or os.path.expanduser("~"),
                )
                if p:
                    pn_dir_input.set_value(p)

            ui.button("Explorar...", on_click=pick_pn_folder).classes("btn-secondary").props("flat")

    pn_section.set_visibility(False)

    def _toggle_pn_section(e):
        pn_section.set_visibility(e.value)

    pn_check.on("update:model-value", _toggle_pn_section)

    # Resumen pre-compose
    summary_area = ui.column().classes("w-full mb-4")

    def refresh_summary():
        _vid = video_input.value
        _ov = overlay_input.value
        if not _vid or not _ov:
            return
        summary_area.clear()
        _drv_lap = state.drv_lap
        _offset_val = float(offset_input.value or 0.0)

        def _mss(s):
            return "%d:%02d" % (int(s) // 60, int(s) % 60)

        if _drv_lap is not None:
            _clip_line = "Clip: desde %s min del video, recortado a la vuelta %s (%.0f s)" % (
                _mss(_offset_val),
                _mss(_drv_lap.laptime),
                _drv_lap.laptime,
            )
        else:
            _clip_line = (
                "Clip: overlay desde %s min (sin telemetria no se recorta a la vuelta)"
                % _mss(_offset_val)
            )

        with summary_area:
            ui.html(
                '<div class="sgi-note">'
                "<strong>Resumen:</strong><br>"
                f"· Video fuente: {os.path.basename(_vid)}<br>"
                f"· Overlay: {os.path.basename(_ov)}<br>"
                f"· {_clip_line}<br>"
                f"· HUD: {pos_select.value} · escala {scale_slider.value * 100:.0f}%<br>"
                "· Codec: NVENC (GPU NVIDIA) si está disponible, libx264 (CPU) si no."
                "</div>"
            )

    video_input.on("update:model-value", lambda _: refresh_summary())
    overlay_input.on("update:model-value", lambda _: refresh_summary())
    refresh_summary()

    ui.separator().classes("my-4")

    # Area de resultado/progreso
    result_area = ui.column().classes("w-full")
    compose_area = ui.column().classes("w-full")
    job_holder = {"job": None, "timer": None}

    def _start_compose():
        _vid = video_input.value
        _ov = overlay_input.value
        if not _vid:
            ui.notify("Elige tu video de grabacion.", type="warning")
            return
        if not _ov:
            ui.notify("Elige el archivo overlay del Paso 3.", type="warning")
            return
        if sync_state["ambiguous"] and not sync_state["resolved"]:
            ui.notify("Primero elige tu vuelta en la seccion de sincronia.", type="warning")
            return

        _out_folder_val = out_folder_input.value or _def_out_folder()
        _base = os.path.splitext(os.path.basename(_vid))[0]
        _out_path = os.path.join(_out_folder_val, _base + "_composed.mp4")
        os.makedirs(_out_folder_val, exist_ok=True)

        try:
            from fantasma.viz.compose import compose_video as _cv
        except ImportError as ie:
            result_area.clear()
            with result_area:
                ui.label(f"ffmpeg o dependencias faltantes: {ie}").classes("text-red-400")
            return

        _drv_lap = state.drv_lap
        _lap_dur = _drv_lap.laptime if _drv_lap is not None else None
        _position = _POS_LABELS[pos_select.value]
        _offset_val = float(offset_input.value or 0.0)
        _scale = scale_slider.value

        _pn_kwargs = {}
        if pn_check.value:
            if _drv_lap is None:
                ui.notify(
                    "Falta la vuelta del piloto para sincronizar las pace notes",
                    type="warning",
                )
                return
            if not pn_dir_input.value:
                ui.notify("Indica la carpeta del pack de Pace Notes", type="warning")
                return
            _pn_kwargs = {
                "pace_notes_dir": pn_dir_input.value,
                "pace_notes_volume": 1.0,
                "lap": _drv_lap,
            }

        job = start_bg_render(
            _cv,
            progress_kw="progress",
            video=_vid,
            overlay=_ov,
            output=_out_path,
            position=_position,
            offset=_offset_val,
            scale=_scale,
            lap_duration=_lap_dur,
            **_pn_kwargs,
        )
        job_holder["job"] = job

        compose_area.clear()
        with compose_area:
            progress_bar = ui.linear_progress(value=0).classes("w-full")
            status_label = ui.label("Iniciando...").classes("text-sm text-gray-400")

            def cancel():
                if job_holder["job"]:
                    job_holder["job"].cancel()

            cancel_btn = (
                ui.button("Detener composicion", on_click=cancel)
                .classes("btn-secondary")
                .props("flat")
            )

        def poll():
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
                result_area.clear()
                with result_area:
                    if _job.error == "__CANCELLED__":
                        ui.label("Composicion cancelada.").classes("text-yellow-400")
                    elif _job.error:
                        ui.label(f"Error: {_job.error}").classes("text-red-400")
                    else:
                        state.last_compose_video = _vid
                        _z_score = sync_state.get("z")
                        _out_name = os.path.basename(_out_path)
                        ui.label("✓ Video guardado: %s" % _out_name).classes(
                            "font-bold text-green-400"
                        )
                        ui.notify("Video listo: %s" % _out_name, type="positive", timeout=0)
                        try:
                            import asyncio as _asyncio

                            _js_body = _out_name.replace("'", "\\'")
                            _loop = _asyncio.get_event_loop()
                            if _loop.is_running():
                                _loop.create_task(
                                    ui.run_javascript(
                                        "try{if(Notification&&Notification.permission==='granted')"
                                        " new Notification('SimGhostInputs',"
                                        "{body:'Video listo: %s'})}catch(_){}" % _js_body
                                    )
                                )
                        except Exception:
                            pass
                        if isinstance(_job.result, dict):
                            ui.label(
                                "Codificado con %s · %.0fs"
                                % (_job.result["encoder"], _job.result["duration_s"])
                            ).classes("text-sm opacity-60")
                        if _z_score is not None:
                            ui.label(
                                "Calidad de sincronía: %s · offset %.2f s"
                                % (_sync_quality_label(_z_score), _offset_val)
                            ).classes("text-blue-300 text-sm")
                        _render_next_btn(state, 4, navigate)
                        ui.separator().classes("my-4")

                        def _otra_vuelta():
                            state.clear_drv()
                            navigate(1)

                        ui.button(
                            "Procesar otra vuelta",
                            on_click=_otra_vuelta,
                        ).classes("btn-secondary").props("flat")
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

    if not (job_holder["job"] and not job_holder["job"].done):
        compose_btn = (
            ui.button(
                "Componer video",
                on_click=_start_compose,
            )
            .classes("btn-primary text-base px-6 py-2")
            .props("flat")
        )

        def _update_compose_enabled():
            if video_input.value and overlay_input.value:
                compose_btn.enable()
            else:
                compose_btn.disable()

        video_input.on("update:model-value", lambda _: _update_compose_enabled())
        overlay_input.on("update:model-value", lambda _: _update_compose_enabled())
        _update_compose_enabled()

    # Auto-arranque si viene encadenado desde el Paso 3
    if state.pending_autocompose:
        state.pending_autocompose = False
        _vid_auto = video_input.value
        _ov_auto = overlay_input.value
        if _vid_auto and _ov_auto:
            _start_compose()
        else:
            ui.notify("Completa el video de grabacion para componer", type="warning")


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
