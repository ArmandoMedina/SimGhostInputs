"""Paso 0 — Inicio: selector de flujo y guia de exportacion (NiceGUI)."""

from nicegui import ui

from .ng_helpers import _FLOWS, _DEFAULT_FLOW

_FLOW_PREVIEW = {
    "📊 Solo análisis": {"need": "2 CSVs", "out": "Reporte, CSVs y gráficas"},
    "🎬 Solo overlay": {"need": "2 CSVs", "out": "HUD transparente `.webm`"},
    "🎥 Video con HUD": {"need": "2 CSVs + video", "out": "MP4 final con HUD"},
}


async def render(state, navigate):
    ui.html('''<div class="sgi-hero">
      <h1 style="font-size:1.55rem;font-weight:700;margin:0 0 0.35rem 0;color:#fafafa">
        SimGhostInputs
      </h1>
      <p style="color:#8b949e;margin:0">
        Convierte una tanda en un debrief por curva y, si quieres,
        en un video con HUD listo para revisar.
      </p>
    </div>''')

    with ui.html('<div class="sgi-note" style="margin-bottom:1rem">').classes('w-full'):
        ui.html(
            '<strong>Una vuelta por flujo.</strong> Si quieres analizar varias, al terminar '
            'puedes volver aqui sin recargar la referencia. Para compararte contra ti mismo, '
            'carga el mismo CSV como referencia y piloto y elige dos vueltas distintas en el Paso 1.'
        )

    ui.label('¿Qué quieres obtener hoy?').classes('text-xl font-bold mt-4 mb-1 text-white')
    ui.label(
        'Elige el flujo que mejor describe tu objetivo. '
        'La UI se adapta y solo te muestra los pasos que necesitas.'
    ).classes('text-sm text-gray-400 mb-3')

    with ui.row().classes('gap-4 flex-wrap mb-4'):
        for fk, fv in _FLOWS.items():
            _render_flow_card(state, fk, fv, navigate)

    ui.separator().classes('my-4')

    # Guia de exportacion
    ui.label('Exporta la telemetría con distancia').classes('text-lg font-bold text-white mb-2')

    ui.markdown(
        'Necesitas CSVs exportados desde **MoTeC i2** con **Include Time Stamp** e '
        '**Include Distance Data** activados. Sin distancia, el análisis se detiene antes de comparar.\n\n'
        '- **Referencia:** vuelta rápida propia, coach o compañero.\n'
        '- **Piloto:** outing actual o el mismo CSV si quieres comparar dos vueltas tuyas.\n'
        '- **Video:** solo para el flujo **Video con HUD**.'
    ).classes('text-sm text-gray-300 mb-2')

    with ui.expansion('Ver guía de exportación paso a paso', icon='info').classes('w-full mb-4'):
        ui.markdown('''
### 1. Instalar y abrir Sim To MoTeC

Descarga e instala **[Sim To MoTeC](https://github.com/GeekyDeaks/sim-to-motec/releases)**
(compatible con AMS2, ACC, iRacing, rFactor 2 y más).
Ábrelo **antes** de arrancar el sim — captura en segundo plano mientras corres.

### 2. Configurar y arrancar la captura

Ajusta **Sampling Frequency a 20 Hz** y haz clic en **Start**.
Los campos Vehicle, Venue y Lap se rellenan solos cuando entras en pista.

### 3. Abrir MoTeC i2 después de la sesión

Abre **MoTeC i2 Standard** (se instala junto con Sim To MoTeC).
Ve a **File → Open Log File** y abre el `.ld` que generó el logger
(normalmente en `Documentos/MoTeC/`).

### 4. Exportar como CSV

En MoTeC i2: **File → Export Data...**

Opciones recomendadas:
- **Data Extent:** Entire Outing
- **Output File Format:** CSV File
- **Output Sample Rate:** Auto
- ✅ Include Time Stamp
- ✅ Include Distance Data

Haz clic en **Export** y guarda el archivo.
        ''')

    ui.separator().classes('my-4')

    async def _start():
        state.flow_chosen = True
        await navigate(1)

    ui.button(
        'Empezar — Ir a Importar →',
        on_click=_start,
    ).props('color=primary unelevated').classes('text-base px-6 py-2')


def _render_flow_card(state, fk, fv, navigate):
    selected = state.flow_key == fk
    preview = _FLOW_PREVIEW[fk]
    border_color = '#58a6ff' if selected else '#30363d'

    with ui.card().classes('p-4 cursor-pointer').style(
        'min-width:200px;max-width:280px;background:#161b22;'
        f'border:1.5px solid {border_color};border-radius:8px'
    ):
        ui.label(fk).classes('text-base font-bold text-white mb-1')
        ui.label(fv['desc']).classes('text-sm text-gray-400 mb-2')
        ui.label(f'Necesitas: {preview["need"]}').classes('text-xs text-gray-300')
        ui.label(f'Obtienes: {preview["out"]}').classes('text-xs text-gray-300 mb-2')

        with ui.expansion('Ver detalle').classes('text-xs text-gray-400'):
            ui.label('Requisitos').classes('text-xs font-bold text-gray-300 mt-1')
            for r in fv['requires']:
                ui.label(f'· {r}').classes('text-xs text-gray-400')
            ui.label('Archivos de salida').classes('text-xs font-bold text-gray-300 mt-1')
            for d in fv['deliverables']:
                ui.label(f'· {d}').classes('text-xs text-gray-400')

        if selected:
            ui.label('✓ Seleccionado').classes('text-green-400 text-xs font-bold mt-2')
        else:
            async def _choose(fk=fk):
                state.flow_key = fk
                state.flow_chosen = True
                # Rerender la pagina para reflejar la seleccion
                await navigate(0)

            ui.button('Elegir este', on_click=_choose).classes('w-full text-sm mt-2')
