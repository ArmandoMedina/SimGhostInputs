"""Paso 3 — Overlay: generar el HUD animado."""

import os

import streamlit as st

from ._helpers import _go, _next_step_btn, _pick_folder, _render_widget, _start_bg_render


def render():
    st.markdown(
        '<div class="step-header">Paso 3 — Generar overlay HUD</div>', unsafe_allow_html=True
    )
    st.caption(
        "Genera el **HUD animado** sincronizado con tu vuelta. "
        "Es un archivo de video **transparente** (como un sticker animado) que en el Paso 4 "
        "se pega encima de tu grabación. Muestra: barras de gas y freno, delta acumulado, "
        "velocidad, marcha, volante y G-lateral."
    )

    if "ref_lap" not in st.session_state:
        st.warning("Primero carga los archivos en el Paso 1.")
        if st.button("← Ir al Paso 1"):
            _go(1)
        st.stop()

    ref_lap = st.session_state["ref_lap"]
    drv_lap = st.session_state["drv_lap"]
    corners = st.session_state.get("corners") if st.session_state.get("corners_editable") else None

    if not corners:
        try:
            from fantasma.core.corners import detect_corners, extract_milestones

            _evs, _ = detect_corners(ref_lap)
            corners = extract_milestones(ref_lap, _evs)
            st.session_state["corners"] = corners
        except Exception:
            corners = []

    if "last_overlay" in st.session_state:
        st.success(
            "✓ Ya tienes un overlay generado: `%s`"
            % os.path.basename(st.session_state["last_overlay"])
        )
        st.caption("Si quieres regenerarlo con distintos parámetros, usa las opciones de abajo.")
        _next_step_btn(3)
        st.divider()

    # ── carpeta de salida ─────────────────────────────────────────────────────
    _def_out = st.session_state.get(
        "_overlay_out_dir", os.path.join(os.path.expanduser("~"), "fantasma_salida")
    )
    if "_overlay_out_dir_pending" in st.session_state:
        st.session_state["_overlay_out_dir_input"] = st.session_state.pop(
            "_overlay_out_dir_pending"
        )
    _oc1, _oc2 = st.columns([5, 1])
    _out_dir_input = _oc1.text_input(
        "Carpeta donde guardar el overlay",
        value=_def_out,
        key="_overlay_out_dir_input",
        help="Se crea automáticamente si no existe.",
    )
    if _oc2.button("Explorar…", key="_btn_pick_outdir"):
        _picked = _pick_folder("Elegir carpeta de salida", initialdir=_def_out)
        if _picked:
            st.session_state["_overlay_out_dir"] = _picked
            st.session_state["_overlay_out_dir_pending"] = _picked
            st.rerun()
    out_dir = _out_dir_input

    # ── FPS ───────────────────────────────────────────────────────────────────
    st.markdown("**FPS del overlay**")
    st.caption(
        "Usa el mismo valor que tiene tu video de grabación. "
        "Si no sabes, **30 fps** es el estándar más común. "
        "Un overlay a 30 sobre un video a 60 funciona bien; al revés puede verse entrecortado."
    )
    _fps_opt = st.radio(
        "FPS",
        [24, 30, 60],
        index=1,
        horizontal=True,
        label_visibility="collapsed",
        key="_overlay_fps",
    )
    _fps = int(_fps_opt)

    # ── formato — solo relevante en flujo "Solo overlay" ─────────────────────
    _flow_key = st.session_state.get("flow_key", "")
    if "Solo overlay" in _flow_key:
        with st.expander("⚙️ Formato de salida"):
            _fmt = st.selectbox(
                "Formato del overlay",
                ["webm", "prores", "png"],
                index=0,
                help=(
                    "webm — Recomendado. Compatible con DaVinci Resolve, Kdenlive, Premiere.\n"
                    "prores — Para Final Cut Pro en Mac o máxima calidad sin compresión.\n"
                    "png — Frames sueltos (una imagen por fotograma). Uso avanzado."
                ),
            )
    else:
        _fmt = "webm"

    st.info(
        "⏱️ **Tiempo estimado de render:** entre 5 y 30 minutos dependiendo de la duración de la vuelta "
        "y el número de cores de tu PC. El render usa todos los cores disponibles en paralelo. "
        "Tu PC seguirá disponible mientras renderiza, solo irá más lenta.  \n"
        "⚠️ **No cambies de paso mientras renderiza** — la barra de navegación se bloquea y "
        "aparece un botón **Detener** si necesitas cancelar."
    )

    # ── render en curso ───────────────────────────────────────────────────────
    _ov_done, _ov_err, _ov_result = _render_widget(3)
    if _ov_done:
        if _ov_err == "__CANCELLED__":
            st.warning("Render cancelado.")
        elif _ov_err:
            if "ImportError" in str(_ov_err) or "No module" in str(_ov_err):
                st.error("Faltan dependencias. Ejecuta: `pip install 'fantasma-inputs[overlay]'`")
            else:
                st.error("Error en el render: %s" % _ov_err)
        else:
            st.success("✓ Overlay generado: `%s`" % os.path.basename(_ov_result))
            st.session_state["last_overlay"] = _ov_result
            st.session_state["_overlay_out_dir"] = os.path.dirname(_ov_result)
            _next_step_btn(3)

    if not st.session_state.get("_render_active"):
        if st.button("Generar overlay", type="primary"):
            os.makedirs(out_dir, exist_ok=True)
            try:
                from fantasma.viz.overlay import render_overlay as _ro
            except ImportError:
                st.error("Faltan dependencias. Ejecuta: `pip install 'fantasma-inputs[overlay]'`")
                st.stop()
            _start_bg_render(
                3,
                _ro,
                progress_kw="progress",
                ref=ref_lap,
                drv=drv_lap,
                corners=corners or [],
                outdir=out_dir,
                fps=_fps,
                fmt=_fmt,
            )
            st.rerun()
