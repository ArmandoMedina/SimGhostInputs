"""Paso 0 — Inicio: guía de exportación y selector de flujo."""

import streamlit as st

from ._helpers import _FLOWS, _go, _img_or_placeholder

_FLOW_PREVIEW = {
    "📊 Solo análisis": {"need": "2 CSVs", "out": "Reporte, CSVs y gráficas"},
    "🎬 Solo overlay": {"need": "2 CSVs", "out": "HUD transparente `.webm`"},
    "🎥 Video con HUD": {"need": "2 CSVs + video", "out": "MP4 final con HUD"},
}


def render():
    st.markdown(
        """
<div class="sgi-hero">
  <h1>👻 SimGhostInputs</h1>
  <p>Convierte una tanda en un debrief por curva y, si quieres, en un video con HUD listo para revisar.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="step-header">Elige el resultado y carga tus vueltas</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="sgi-strip">
  <div class="sgi-strip-item">
    <strong>① Referencia</strong>
    <span>Tu mejor vuelta, una vuelta de coach o una vuelta del mismo archivo.</span>
  </div>
  <div class="sgi-strip-item">
    <strong>② Piloto</strong>
    <span>La vuelta que quieres entender hoy. La app elige la rápida y puedes cambiarla.</span>
  </div>
  <div class="sgi-strip-item">
    <strong>③ Salida</strong>
    <span>Reporte, overlay transparente o video final con HUD.</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="sgi-note">
  <strong>Una vuelta por flujo.</strong> Si quieres analizar varias, al terminar puedes volver aquí sin
  recargar la referencia. Para compararte contra ti mismo, carga el mismo CSV como referencia y piloto
  y elige dos vueltas distintas en el Paso 1.
</div>
""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── ¿qué quieres obtener hoy? ─────────────────────────────────────────────
    st.subheader("① ¿Qué quieres obtener hoy?")
    st.caption(
        "Elige el flujo que mejor describe tu objetivo. "
        "La UI se adapta y solo te muestra los pasos que necesitas."
    )

    _flow_keys = list(_FLOWS.keys())
    _cols = st.columns(len(_flow_keys))
    for _ci, (_fk, _fv) in enumerate(_FLOWS.items()):
        with _cols[_ci]:
            _selected = st.session_state["flow_key"] == _fk
            _preview = _FLOW_PREVIEW[_fk]
            # Tarjeta con el contenedor REAL de Streamlit: st.container(border)
            # envuelve los widgets de verdad. Un <div> por separado vía markdown
            # NO los contiene (abre/cierra solo en el DOM y deja una caja vacía).
            # height fija las tres a la misma altura para que el botón de abajo
            # —fuera del contenedor— quede a la misma línea base. Ver ADR 0011.
            with st.container(border=True, height=260):
                st.markdown(
                    '<div class="sgi-flow-card-title">%s</div>' % _fk, unsafe_allow_html=True
                )
                st.markdown(
                    '<div class="sgi-flow-meta">%s</div>' % _fv["desc"], unsafe_allow_html=True
                )
                st.markdown("**Necesitas:** %s" % _preview["need"])
                st.markdown("**Obtienes:** %s" % _preview["out"])
                with st.expander("Ver detalle"):
                    st.markdown("**Requisitos**")
                    for _r in _fv["requires"]:
                        st.markdown("- %s" % _r)
                    st.markdown("**Archivos de salida**")
                    for _d in _fv["deliverables"]:
                        st.markdown("- %s" % _d)
            if _selected:
                st.success("✓ Seleccionado")
            elif st.button("Elegir este", key="flow_%d" % _ci, use_container_width=True):
                st.session_state["flow_key"] = _fk
                st.rerun()

    st.divider()

    # ── cómo exportar telemetría ──────────────────────────────────────────────
    st.subheader("② Exporta la telemetría con distancia")
    _txt_col, _img_col = st.columns([1.2, 1])
    with _txt_col:
        st.markdown(
            "Necesitas CSVs exportados desde **MoTeC i2** con **Include Time Stamp** y "
            "**Include Distance Data** activados. Sin distancia, el análisis se detiene antes de comparar."
        )
        st.markdown(
            "- **Referencia:** vuelta rápida propia, coach o compañero.\n"
            "- **Piloto:** outing actual o el mismo CSV si quieres comparar dos vueltas tuyas.\n"
            "- **Video:** solo para el flujo **Video con HUD**."
        )
    with _img_col:
        _img_or_placeholder(
            "docs/guide/s2m_04_export.gif",
            "MoTeC i2 — Export Data con Time Stamp y Distance Data",
        )

    with st.expander("Ver guía de exportación paso a paso", expanded=False):
        st.markdown("### 1. Instalar y abrir Sim To MoTeC")
        st.markdown(
            "Descarga e instala **[Sim To MoTeC](https://github.com/GeekyDeaks/sim-to-motec/releases)** "
            "(compatible con AMS2, ACC, iRacing, rFactor 2 y más). "
            "Ábrelo **antes** de arrancar el sim — captura en segundo plano mientras corres."
        )
        _img_or_placeholder(
            "docs/guide/s2m_01_install.png",
            "AMS2 logger v1.8.6 — la app lista antes de iniciar la sesión",
        )

        st.markdown("### 2. Configurar y arrancar la captura")
        st.markdown(
            "Ajusta **Sampling Frequency a 20 Hz** y haz clic en **Start**. "
            "Los campos Vehicle, Venue y Lap se rellenan solos cuando entras en pista."
        )
        _img_or_placeholder(
            "docs/guide/s2m_02_config.png",
            "Sampling Frequency: 20 Hz · Log File: Not Started · Start activado",
        )

        st.markdown("### 3. Abrir MoTeC i2 después de la sesión")
        st.markdown(
            "Abre **MoTeC i2 Standard** (se instala junto con Sim To MoTeC). "
            "Ve a **File → Open Log File** y abre el `.ld` que generó el logger "
            "(normalmente en `Documentos/MoTeC/`)."
        )
        _img_or_placeholder("docs/guide/s2m_03_i2_main.png", "MoTeC i2 — File → Export Data...")

        st.markdown("### 4. Exportar como CSV")
        st.markdown(
            "En MoTeC i2: **File → Export Data...**  \n"
            "Opciones recomendadas:  \n"
            "- **Data Extent:** Entire Outing  \n"
            "- **Output File Format:** CSV File  \n"
            "- **Output Sample Rate:** Auto  \n"
            "- ✅ Include Time Stamp  \n"
            "- ✅ Include Distance Data  \n\n"
            "Haz clic en **Export** y guarda el archivo."
        )
        _img_or_placeholder(
            "docs/guide/s2m_04_export.gif", "File → Export Data → opciones recomendadas → Export"
        )

    if st.button("Empezar — Ir a Importar →", type="primary"):
        _go(1)
