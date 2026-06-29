"""Paso 4 — Componer: superponer overlay sobre la grabación."""

import os
import shutil

import streamlit as st

from ._helpers import (
    _POS_LABELS,
    _cache_file,
    _fmt_lap,
    _next_step_btn,
    _pick_file,
    _pick_folder,
    _render_widget,
    _start_bg_render,
    _sync_quality_label,
)


def render():
    st.markdown(
        '<div class="step-header">Paso 4 — Componer video final</div>', unsafe_allow_html=True
    )
    st.caption(
        "Junta el overlay del Paso 3 con tu video de grabación. "
        "El resultado es un **clip MP4 recortado exactamente a la duración de tu vuelta**, "
        "con el HUD ya integrado y listo para subir."
    )

    # Prerrequisito: compose NECESITA ffmpeg. Avisar temprano (caso C19) en vez de dejar fallar
    # al apretar "Componer". El overlay del Paso 3 sí degrada a PNG sin ffmpeg; compose no.
    if shutil.which("ffmpeg") is None:
        st.error(
            "⚠️ **ffmpeg no está instalado** y este paso lo necesita para generar el video.  \n"
            "Instálalo y reinicia la terminal: `winget install Gyan.FFmpeg`  \n"
            "(El overlay del Paso 3 sí funciona sin ffmpeg, generando frames PNG.)"
        )

    _col_k1, _col_k2 = st.columns(2)
    _col_k1.warning(
        "🎙️ **El video DEBE tener audio del motor activado.**  \n"
        "La sincronía automática analiza el sonido del motor para encontrar el segundo exacto "
        "en que cruzaste la meta. Sin audio tendrás que calcular el offset manualmente."
    )
    _col_k2.info(
        "✂️ **El output no es el video completo de tu sesión.**  \n"
        "Se genera un clip recortado exactamente a tu vuelta: desde la meta hasta que la terminas. "
        "Mucho más rápido de procesar y más fácil de compartir."
    )

    st.divider()

    # ── ① Archivos de entrada ─────────────────────────────────────────────────
    st.markdown("**① Archivos de entrada**")
    st.caption("Usa el botón «Explorar…» para abrir el selector de archivos del sistema.")

    if "_compose_video_pending" in st.session_state:
        st.session_state["_compose_video_input"] = st.session_state.pop("_compose_video_pending")
    _vc1, _vc2 = st.columns([5, 1])
    _video_path = _vc1.text_input(
        "Tu video de grabación",
        value=st.session_state.get("last_compose_video", ""),
        placeholder=r"C:\Videos\mi_sesion_nordschleife.mp4",
        key="_compose_video_input",
    )
    if _vc2.button("Explorar…", key="_btn_pick_video"):
        _p = _pick_file(
            "Seleccionar video de grabación",
            [("Video", "*.mp4 *.mov *.mkv *.avi"), ("Todos", "*.*")],
        )
        if _p:
            st.session_state["last_compose_video"] = _p
            st.session_state["_compose_video_pending"] = _p
            st.rerun()

    _def_overlay = st.session_state.get("last_overlay", "")
    if "_compose_overlay_pending" in st.session_state:
        st.session_state["_compose_overlay_input"] = st.session_state.pop(
            "_compose_overlay_pending"
        )
    _oc1, _oc2 = st.columns([5, 1])
    _overlay_path = _oc1.text_input(
        "Overlay del HUD (generado en el Paso 3)",
        value=_def_overlay,
        placeholder=r"C:\Users\TuNombre\fantasma_salida\overlay.webm",
        key="_compose_overlay_input",
    )
    if _oc2.button("Explorar…", key="_btn_pick_overlay"):
        _p = _pick_file("Seleccionar overlay", [("WebM / MOV", "*.webm *.mov"), ("Todos", "*.*")])
        if _p:
            st.session_state["last_overlay"] = _p
            st.session_state["_compose_overlay_pending"] = _p
            st.rerun()

    # ── ② Sincronía ───────────────────────────────────────────────────────────
    st.divider()
    st.markdown("**② Sincronía: ¿en qué segundo del video empieza tu vuelta?**")
    st.caption(
        "SimGhostInputs escucha el sonido del motor en tu video y lo compara con los RPM de la "
        "telemetría para encontrar automáticamente el segundo exacto en que cruzaste la meta. "
        "Precisión ~0.5 s · tarda ~30 segundos · necesitas **scipy** instalado."
    )

    _drv_for_sync = st.session_state.get("drv_lap")
    if _drv_for_sync is None:
        st.warning(
            "⚠️ **Sube TU telemetría — la misma vuelta que grabaste en el video.**  \n"
            "**No** subas aquí la de referencia: el sync compara el audio de *tu* motor con *tus* "
            "RPM, así que tiene que ser la vuelta que se ve en el video. La de referencia es otro "
            "motor/otra vuelta y el sync fallaría."
        )
        _sync_up = st.file_uploader(
            "Tu CSV — la vuelta del video (NO la de referencia)",
            type=["csv", "xlsx"],
            key="sync_drv_upload",
            help="El mismo CSV de tus vueltas que usarías en el Paso 1. La sincronía necesita "
            "los RPM de la vuelta que estás viendo en el video, no los de la referencia.",
        )
        if _sync_up:
            _sc = _cache_file(_sync_up)
            if _sc["ok"] and _sc["laps"]:
                from fantasma.core.normalize import fastest_lap as _fl

                _drv_for_sync = _fl(_sc["laps"])
                st.success("✓ Tu telemetría cargada.")
    else:
        st.caption(
            "Usando tu vuelta del Paso 1 (%s) — la que corresponde al video."
            % _fmt_lap(_drv_for_sync.laptime)
        )

    _can_sync = bool(_video_path and _drv_for_sync)
    _sc1, _sc2 = st.columns([3, 1])
    with _sc2:
        if not _can_sync:
            st.caption("Necesitas el video y la telemetría.")
        if st.button(
            "Detectar sincronía",
            disabled=not _can_sync,
            type="primary" if _can_sync else "secondary",
            key="btn_autosync",
        ):
            with st.spinner("Analizando audio… (~30 s)"):
                _res = None
                try:
                    from fantasma.viz.sync import _MIN_SYNC_Z, sync_candidates

                    _res = sync_candidates(_video_path, _drv_for_sync)
                except ImportError as _ie:
                    st.error(str(_ie))
                except Exception as _se:
                    st.error("Error en auto-sync: %s" % _se)
                if _res is not None:
                    for _k in (
                        "_sync_cands",
                        "_sync_ambiguous",
                        "_sync_resolved",
                        "_autosync_detected",
                        "_autosync_z",
                        "_autosync_error",
                    ):
                        st.session_state.pop(_k, None)
                    _cs = _res["candidates"]
                    if not _cs or _cs[0]["z"] < _MIN_SYNC_Z:
                        st.session_state["_autosync_error"] = (
                            "Correlación insuficiente: el video no parece corresponder a tu "
                            "vuelta. Usa la sincronía manual de abajo."
                        )
                    elif _res["ambiguous"]:
                        # ADR 0008: varias vueltas parecidas — selección obligatoria.
                        st.session_state["_sync_cands"] = _cs
                        st.session_state["_sync_ambiguous"] = True
                    else:
                        st.session_state["_autosync_detected"] = _cs[0]["offset"]
                        st.session_state["_autosync_z"] = _cs[0]["z"]
                        st.session_state["compose_offset"] = _cs[0]["offset"]
                    st.rerun()

    with _sc1:
        if st.session_state.get("_autosync_error"):
            st.error(st.session_state["_autosync_error"])
        elif "_autosync_detected" in st.session_state and not st.session_state.get(
            "_sync_ambiguous"
        ):
            _off = st.session_state["_autosync_detected"]
            _z_s = st.session_state.get("_autosync_z", 0.0)
            _qlbl = _sync_quality_label(_z_s)
            st.success(
                "✓ **Offset detectado: %.3f s** desde el inicio del video hasta el cruce de meta.  \n"
                "Calidad de sincronía: **%s** — el valor se cargó en el campo de abajo."
                % (_off, _qlbl)
            )
            # Zona gris (ADR 0008): pasa el mínimo pero no es robusto; podría ser
            # un video de otra sesión. Se acepta pero se avisa (no bloquea).
            from fantasma.viz.sync import sync_gray_zone_warning

            _gz = sync_gray_zone_warning(_z_s)
            if _gz:
                st.warning("⚠️ " + _gz[0].upper() + _gz[1:])

    # Selector bloqueante de vuelta (ADR 0008): con video de varias vueltas el audio
    # no distingue cuál es la del piloto, así que el usuario DEBE elegir para continuar.
    _sync_pending = bool(
        st.session_state.get("_sync_ambiguous") and not st.session_state.get("_sync_resolved")
    )
    if _sync_pending:
        _cands = st.session_state.get("_sync_cands", [])
        st.warning(
            "⚠️ Tu video parece tener **varias vueltas** y suenan casi igual, así que no se "
            "puede saber solo cuál es la tuya. **Elige la vuelta para poder componer.**"
        )
        _idx = st.radio(
            "¿Cuál corresponde a tu vuelta?  (minuto dentro del video)",
            list(range(len(_cands))),
            format_func=lambda i: (
                "%s min    ·    calidad %.1f σ" % (_cands[i]["mmss"], _cands[i]["z"])
            ),
            key="_sync_choice",
        )
        if st.button("Confirmar esta vuelta", type="primary", key="btn_confirm_lap"):
            _c = _cands[_idx]
            st.session_state["compose_offset"] = _c["offset"]
            st.session_state["_autosync_detected"] = _c["offset"]
            st.session_state["_autosync_z"] = _c["z"]
            st.session_state["_sync_resolved"] = True
            st.rerun()

    with st.expander("⚙️ Sincronizar manualmente (avanzado)"):
        st.warning(
            "⚠️ Usa esto solo si la detección automática falló o el video no tiene audio del motor. "
            "Necesitarás reproducir el video y anotar el segundo exacto en que cruzas la meta."
        )
        st.markdown(
            "**Cómo encontrar el offset manualmente:**  \n"
            "1. Abre el video en VLC.  \n"
            "2. Busca el momento en que cruzas la línea de meta.  \n"
            "3. Lee el tiempo en la barra de reproducción (p. ej. `0:00:17`).  \n"
            "4. Escribe ese valor en segundos abajo (p. ej. `17`)."
        )

    # ── ③ Parámetros del HUD ──────────────────────────────────────────────────
    st.divider()
    st.markdown("**③ Parámetros del HUD**")
    _col3, _col4, _col5 = st.columns(3)
    _pos_sel = _col3.selectbox(
        "Posición del HUD en pantalla",
        list(_POS_LABELS.keys()),
        help="Dónde se coloca el HUD dentro del frame del video.",
    )
    _position = _POS_LABELS[_pos_sel]
    _offset = _col4.number_input(
        "Offset (s desde inicio del video hasta la meta)",
        value=float(st.session_state.get("compose_offset", 0.0)),
        step=0.1,
        key="compose_offset",
        help=(
            "El segundo del video en que tu auto cruza la línea de meta. "
            "Si usaste «Detectar sincronía» este campo se rellena solo."
        ),
    )
    _scale = _col5.slider(
        "Tamaño del HUD",
        0.25,
        1.5,
        1.0,
        0.05,
        help="1.0 = tamaño original del render. 0.7 = más pequeño.",
    )

    # ── ④ Carpeta de salida ───────────────────────────────────────────────────
    st.divider()
    st.markdown("**④ Carpeta de salida**")
    _def_out_folder = (
        os.path.dirname(_overlay_path)
        if _overlay_path and os.path.dirname(_overlay_path)
        else os.path.dirname(_video_path)
        if _video_path and os.path.dirname(_video_path)
        else os.path.expanduser("~")
    )
    if "_compose_out_folder_pending" in st.session_state:
        st.session_state["_compose_out_folder_input"] = st.session_state.pop(
            "_compose_out_folder_pending"
        )
    _of1, _of2 = st.columns([5, 1])
    _out_folder = _of1.text_input(
        "Carpeta donde guardar el video final",
        value=st.session_state.get("_compose_out_folder", _def_out_folder),
        key="_compose_out_folder_input",
        help="Por defecto se usa la carpeta del overlay. Puedes cambiarlo aquí.",
    )
    if _of2.button("Explorar…", key="_btn_pick_compose_out"):
        _p = _pick_folder("Carpeta de salida", initialdir=_def_out_folder)
        if _p:
            st.session_state["_compose_out_folder"] = _p
            st.session_state["_compose_out_folder_pending"] = _p
            st.rerun()

    # ── resumen pre-compose ───────────────────────────────────────────────────
    # _drv_for_sync unifica la telemetría del Paso 1 y la subida aquí en el Paso 4,
    # así el recorte a la vuelta funciona también con el CSV cargado en este paso.
    _drv_lap = _drv_for_sync
    if _video_path and _overlay_path:

        def _mss(s):
            return "%d:%02d" % (int(s) // 60, int(s) % 60)

        _offset_val = float(st.session_state.get("compose_offset", 0.0))
        if _drv_lap is not None:
            _clip_line = (
                "- Clip: desde **%s min** del video → recortado a la vuelta **%s** (%.0f s)  \n"
                % (_mss(_offset_val), _mss(_drv_lap.laptime), _drv_lap.laptime)
            )
        else:
            _clip_line = (
                "- Clip: overlay aplicado desde **%s min** del video → **duración completa** "
                "(sin telemetría no se recorta a la vuelta)  \n" % _mss(_offset_val)
            )
        st.info(
            "**Resumen:**  \n"
            "- Video fuente: `%s`  \n"
            "- Overlay: `%s`  \n"
            "%s"
            "- HUD: %s · escala %.0f%%  \n"
            "- Codec: NVENC (GPU NVIDIA) si está disponible, libx264 (CPU) si no."
            % (
                os.path.basename(_video_path),
                os.path.basename(_overlay_path),
                _clip_line,
                _pos_sel,
                _scale * 100,
            )
        )

    st.divider()
    if not _video_path:
        st.caption("⬆️ Elige tu video de grabación para habilitar el botón.")
    elif not _overlay_path:
        st.caption("⬆️ Elige el archivo overlay del Paso 3 para habilitar el botón.")

    # ── render en curso ───────────────────────────────────────────────────────
    _cp_done, _cp_err, _cp_result = _render_widget(4)
    if _cp_done:
        if _cp_err == "__CANCELLED__":
            st.warning("Composición cancelada.")
        elif _cp_err:
            st.error("Error: %s" % _cp_err)
        else:

            def _mss(s):
                return "%d:%02d" % (int(s) // 60, int(s) % 60)

            st.success("✓ Video guardado en: `%s`" % _cp_result)
            _z_score = st.session_state.get("_autosync_z")
            if _z_score is not None:
                st.info(
                    "Calidad de sincronía: **%s** · offset %.2f s"
                    % (
                        _sync_quality_label(_z_score),
                        float(st.session_state.get("compose_offset", 0.0)),
                    )
                )
            st.session_state["last_compose_video"] = _video_path
            st.balloons()
            _next_step_btn(4)
            st.divider()
            if st.button(
                "🔄 Procesar otra vuelta",
                help="Vuelve al Paso 1 para elegir otra vuelta. Mantiene la referencia y el video.",
            ):
                for _k in [
                    "drv_lap",
                    "drv_laps",
                    "drv_path",
                    "summary",
                    "trace",
                    "rows",
                    "charts_paths",
                    "last_overlay",
                    "_autosync_detected",
                    "_autosync_z",
                    "compose_offset",
                    "corners",
                    "corners_editable",
                    "_sync_cands",
                    "_sync_ambiguous",
                    "_sync_resolved",
                    "_sync_choice",
                    "_autosync_error",
                ]:
                    st.session_state.pop(_k, None)
                for _k in list(st.session_state.keys()):
                    if _k.startswith("drv_sel_") or _k == "drv_lap_tbl":
                        st.session_state.pop(_k, None)
                st.session_state["nav_step"] = 1
                st.rerun()

    if not st.session_state.get("_render_active"):
        if _sync_pending:
            st.caption("🔒 Primero elige tu vuelta arriba para poder componer.")
        if st.button(
            "Componer video",
            type="primary",
            disabled=not (_video_path and _overlay_path) or _sync_pending,
        ):
            _out_folder_val = _out_folder or _def_out_folder
            _base = os.path.splitext(os.path.basename(_video_path))[0]
            _out_path = os.path.join(_out_folder_val, _base + "_composed.mp4")
            os.makedirs(_out_folder_val, exist_ok=True)
            try:
                from fantasma.viz.compose import compose_video as _cv
            except ImportError as _ie:
                st.error("ffmpeg o dependencias faltantes: %s" % _ie)
                st.stop()
            _lap_dur = _drv_lap.laptime if _drv_lap is not None else None
            _start_bg_render(
                4,
                _cv,
                progress_kw="progress",
                video=_video_path,
                overlay=_overlay_path,
                output=_out_path,
                position=_position,
                offset=float(st.session_state.get("compose_offset", 0.0)),
                scale=_scale,
                lap_duration=_lap_dur,
            )
            st.rerun()
