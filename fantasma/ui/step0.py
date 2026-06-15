"""Paso 0 — Inicio: guía de exportación y selector de flujo."""
import streamlit as st

from ._helpers import _FLOWS, _go, _img_or_placeholder


def render():
    st.markdown('<div class="step-header">👻 Bienvenido a SimGhostInputs</div>', unsafe_allow_html=True)
    st.caption("Compara tus inputs de simracing contra una vuelta de referencia, curva a curva.")

    st.info(
        "**Una vuelta por flujo.** Cada vez que usas la app procesas exactamente una vuelta. "
        "Si tienes varias vueltas para analizar, al terminar el flujo el botón "
        "**«Procesar otra vuelta»** te devuelve aquí sin tener que recargar archivos ni la referencia."
    )

    # ── cómo exportar telemetría ──────────────────────────────────────────────
    st.subheader("① Antes de empezar: exporta tu telemetría")
    st.markdown(
        "SimGhostInputs necesita **archivos CSV** con los datos de la sesión. "
        "Se exportan desde **MoTeC i2** después de cada tanda usando el plugin gratuito **Sim To MoTeC**."
    )

    with st.expander("📋 Ver guía de exportación paso a paso", expanded=False):
        st.markdown("### 1. Instalar y abrir Sim To MoTeC")
        st.markdown(
            "Descarga e instala **[Sim To MoTeC](https://github.com/GeekyDeaks/sim-to-motec/releases)** "
            "(compatible con AMS2, ACC, iRacing, rFactor 2 y más). "
            "Ábrelo **antes** de arrancar el sim — captura en segundo plano mientras corres."
        )
        _img_or_placeholder("docs/guide/s2m_01_install.png",
                            "AMS2 logger v1.8.6 — la app lista antes de iniciar la sesión")

        st.markdown("### 2. Configurar y arrancar la captura")
        st.markdown(
            "Ajusta **Sampling Frequency a 20 Hz** y haz clic en **Start**. "
            "Los campos Vehicle, Venue y Lap se rellenan solos cuando entras en pista."
        )
        _img_or_placeholder("docs/guide/s2m_02_config.png",
                            "Sampling Frequency: 20 Hz · Log File: Not Started · Start activado")

        st.markdown("### 3. Abrir MoTeC i2 después de la sesión")
        st.markdown(
            "Abre **MoTeC i2 Standard** (se instala junto con Sim To MoTeC). "
            "Ve a **File → Open Log File** y abre el `.ld` que generó el logger "
            "(normalmente en `Documentos/MoTeC/`)."
        )
        _img_or_placeholder("docs/guide/s2m_03_i2_main.png",
                            "MoTeC i2 — File → Export Data...")

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
        _img_or_placeholder("docs/guide/s2m_04_export.gif",
                            "File → Export Data → opciones recomendadas → Export")

        st.info(
            "💡 Exporta **dos archivos**: uno con la vuelta de referencia "
            "(tu mejor tiempo anterior, o la de un coach) y otro con **tus vueltas de la sesión de hoy**."
        )

    st.divider()

    # ── ¿qué quieres obtener hoy? ─────────────────────────────────────────────
    st.subheader("② ¿Qué quieres obtener hoy?")
    st.caption(
        "Elige el flujo que mejor describe tu objetivo. "
        "La UI se adapta y solo te muestra los pasos que necesitas."
    )

    _flow_keys = list(_FLOWS.keys())
    _cols = st.columns(len(_flow_keys))
    for _ci, (_fk, _fv) in enumerate(_FLOWS.items()):
        with _cols[_ci]:
            _selected = st.session_state["flow_key"] == _fk
            _border   = "2px solid #00c853" if _selected else "1px solid #3d4450"
            st.markdown(
                "<div style='border:%s; border-radius:10px; padding:1rem; min-height:260px'>" % _border,
                unsafe_allow_html=True,
            )
            st.markdown("### %s" % _fk)
            st.caption(_fv["desc"])
            st.markdown("**Necesitas:**")
            for _r in _fv["requires"]:
                st.markdown("- %s" % _r)
            st.markdown("**Obtienes:**")
            for _d in _fv["deliverables"]:
                st.markdown("- %s" % _d)
            st.markdown("</div>", unsafe_allow_html=True)
            if not _selected:
                if st.button("Elegir este", key="flow_%d" % _ci, use_container_width=True):
                    st.session_state["flow_key"] = _fk
                    st.rerun()
            else:
                st.success("✓ Seleccionado")

    st.divider()
    if st.button("Empezar — Ir a Importar →", type="primary"):
        _go(1)
