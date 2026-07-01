"""Paso 2 — Comparar: análisis curva a curva (NiceGUI)."""

import os
import tempfile

from nicegui import run, ui

from .ng_helpers import _fmt_lap


async def render(state, navigate):
    ui.label('Paso 2 — Análisis por curva').classes('step-header')

    if state.ref_lap is None:
        ui.label('Primero carga los archivos en el Paso 1.').classes('text-yellow-400')
        ui.button('← Ir al Paso 1', on_click=lambda: navigate(1)).props('flat color=secondary')
        return

    ref_lap = state.ref_lap
    drv_lap = state.drv_lap
    corners = state.corners

    # Cabecera de vueltas
    _ref_name = state.ref_name or os.path.basename(state.ref_path or '—')
    _drv_name = state.drv_name or os.path.basename(state.drv_path or '—')
    with ui.row().classes('gap-4 mb-4 w-full'):
        ui.label(
            f'Referencia: {_ref_name} · {_fmt_lap(ref_lap.laptime)}'
        ).classes('text-sm text-blue-300 bg-blue-950 px-3 py-1 rounded')
        ui.label(
            f'Tu vuelta: {_drv_name} · {_fmt_lap(drv_lap.laptime)}'
        ).classes('text-sm text-purple-300 bg-purple-950 px-3 py-1 rounded')

    if state.summary is None:
        spinner = ui.spinner('dots').classes('text-blue-400')
        status_lbl = ui.label('Comparando vuelta metro a metro...').classes('text-gray-400')

        def _do_compare():
            from fantasma.core.compare import compare
            from fantasma.core.corners import detect_corners, extract_milestones
            _corners = corners
            if not _corners:
                _evs, _ = detect_corners(ref_lap)
                _corners = extract_milestones(ref_lap, _evs)
            t, r, s = compare(ref_lap, drv_lap, step=1.0, corners=_corners)
            return {'trace': t, 'rows': r, 'summary': s, 'corners': _corners}

        try:
            result = await run.io_bound(_do_compare)
            state.trace = result['trace']
            state.rows = result['rows']
            state.summary = result['summary']
            if not state.corners:
                state.corners = result['corners']
            state.charts_paths = None
            spinner.delete()
            status_lbl.delete()
        except Exception as e:
            spinner.delete()
            status_lbl.delete()
            ui.label(f'Error en comparacion: {e}').classes('text-red-400')
            return

    summary = state.summary
    rows = state.rows
    trace = state.trace

    # Avisos del motor
    for av in (summary.get('avisos') or []):
        ui.label(f'⚠ {av[0].upper() + av[1:] if av else av}').classes(
            'text-yellow-300 bg-yellow-950 px-3 py-2 rounded mb-1'
        )

    ui.separator().classes('my-3')

    # Metricas globales
    total_delta = summary['total_delta']
    _delta_color = 'text-green-400' if total_delta < 0 else 'text-red-400'
    with ui.row().classes('gap-8 mb-4'):
        with ui.column().classes('items-center'):
            ui.label('Tiempo referencia').classes('text-xs text-gray-400')
            ui.label(_fmt_lap(summary['ref_laptime'])).classes('text-xl font-bold text-white')
        with ui.column().classes('items-center'):
            ui.label('Tu tiempo').classes('text-xs text-gray-400')
            ui.label(_fmt_lap(summary['drv_laptime'])).classes('text-xl font-bold text-white')
        with ui.column().classes('items-center'):
            ui.label('Diferencia total').classes('text-xs text-gray-400')
            ui.label('%+.3f s' % total_delta).classes(f'text-xl font-bold {_delta_color}')

    # Generar graficas si no existen
    if state.charts_paths is None:
        _out = tempfile.mkdtemp()
        charts_err = None
        try:
            from fantasma.viz.charts import render_charts
            state.charts_paths = render_charts(
                trace, rows, state.corners or [], _out, top=None
            )
        except ImportError:
            state.charts_paths = []
            charts_err = 'matplotlib no instalado — ejecuta: pip install "fantasma-inputs[charts]"'
        except Exception as e:
            state.charts_paths = []
            charts_err = str(e)
        if charts_err:
            ui.label(charts_err).classes('text-yellow-400 text-sm mb-2')

    _charts = state.charts_paths or []

    def _charts_of(prefix):
        return [p for p in _charts if os.path.basename(p).startswith(prefix)]

    # Tabs
    with ui.tabs().classes('w-full') as tabs:
        tab_curvas = ui.tab('Curvas prioritarias')
        tab_resumen = ui.tab('Resumen de vuelta')
        tab_vuelta = ui.tab('Vuelta completa')

    with ui.tab_panels(tabs, value=tab_curvas).classes('w-full'):
        with ui.tab_panel(tab_curvas):
            _render_curvas_tab(rows, trace, _charts_of)

        with ui.tab_panel(tab_resumen):
            _render_resumen_tab(_charts_of)

        with ui.tab_panel(tab_vuelta):
            _render_vuelta_tab(_charts_of)

    ui.separator().classes('my-4')
    _render_next_btn(state, 2, navigate)


def _render_curvas_tab(rows, trace, charts_of):
    ui.label('¿Donde estas perdiendo tiempo?').classes('text-base font-bold text-white mb-1')
    ui.label(
        'Vel. minima en apex = la velocidad mas baja en el punto mas cerrado de la curva. '
        'Tiempo ganado/perdido: positivo (+) = pierdes tiempo aqui; negativo (-) = ganas tiempo. '
        'Curvas ordenadas por impacto en el crono.'
    ).classes('text-xs text-gray-400 mb-3')

    if not rows:
        ui.label(
            'No se detectaron curvas. Verifica que el CSV incluye el canal de distancia '
            'y que la vuelta tiene longitud suficiente para detectar frenadas.'
        ).classes('text-yellow-400')
        return

    # Tabla de curvas
    import pandas as pd

    df = pd.DataFrame(rows)[
        ['name', 'apex_d', 'ref_vmin', 'drv_vmin', 'd_vmin', 'time_lost', 'flags']
    ].sort_values('time_lost', ascending=False)
    df.columns = [
        'Curva', 'Apex (m)', 'Ref. vel. min. (km/h)', 'Tu vel. min. (km/h)',
        'Diferencia (km/h)', 'Tiempo ganado/perdido (s)', 'Avisos',
    ]
    # Formatear columnas numericas
    df['Tiempo ganado/perdido (s)'] = df['Tiempo ganado/perdido (s)'].map(lambda v: '%+.3f' % v if v is not None else '—')
    df['Diferencia (km/h)'] = df['Diferencia (km/h)'].map(lambda v: '%+.0f' % v if v is not None else '—')

    ui.table(
        columns=[{'name': c, 'label': c, 'field': c, 'align': 'left'} for c in df.columns],
        rows=df.to_dict('records'),
    ).classes('w-full text-xs').props('flat dense')

    # Drill-down por curva
    ui.separator().classes('my-3')
    ui.label('Detalle de curva').classes('text-sm font-bold text-white mb-1')

    _ordered_rows = sorted(rows, key=lambda r: r.get('time_lost', 0), reverse=True)
    _labels = [
        '%s · %+.3f s' % (r.get('name', r.get('id', '?')), r.get('time_lost', 0.0))
        for r in _ordered_rows
    ]

    detail_area = ui.column().classes('w-full')

    def _show_corner(label):
        try:
            idx = _labels.index(label)
        except ValueError:
            return
        row = _ordered_rows[idx]
        detail_area.clear()
        with detail_area:
            _render_corner_detail(row, trace)

    corner_sel = ui.select(options=_labels, value=_labels[0], label='Curva a atacar').classes('w-full mb-2')
    corner_sel.on('update:model-value', lambda e: _show_corner(e.value))
    _show_corner(_labels[0])

    # Graficas de curvas
    corners_charts = charts_of('curva_')
    if corners_charts:
        ui.label('Curvas con mayor perdida de tiempo').classes('text-sm font-bold text-white mt-4 mb-2')
        with ui.row().classes('gap-2 flex-wrap'):
            for p in corners_charts:
                try:
                    with open(p, 'rb') as f:
                        ui.image(f.read()).classes('rounded').style('max-width:400px')
                except Exception:
                    pass

    brakes = charts_of('frenada_')
    if brakes:
        ui.label('Detalle de zonas de frenada').classes('text-sm font-bold text-white mt-4 mb-2')
        with ui.row().classes('gap-2 flex-wrap'):
            for p in brakes:
                try:
                    with open(p, 'rb') as f:
                        ui.image(f.read()).classes('rounded').style('max-width:400px')
                except Exception:
                    pass

    # Descarga CSV
    import io as _io
    dl_df = pd.DataFrame(rows)[
        ['name', 'apex_d', 'ref_vmin', 'drv_vmin', 'd_vmin', 'time_lost', 'flags']
    ]
    dl_df.columns = [
        'Curva', 'Apex (m)', 'Ref. vel. min. (km/h)', 'Tu vel. min. (km/h)',
        'Diferencia (km/h)', 'Tiempo ganado/perdido (s)', 'Avisos',
    ]
    csv_buf = _io.StringIO()
    dl_df.to_csv(csv_buf, index=False)
    ui.download(csv_buf.getvalue().encode(), 'corners_compare.csv').classes('mt-2')


def _render_corner_detail(row, trace):
    from fantasma.core.compare import corner_coaching
    coach = corner_coaching(row, trace)

    _color_map = {'gain': 'text-green-400', 'neutral': 'text-blue-300', 'loss': 'text-yellow-400'}
    _bg_map = {'gain': 'bg-green-950', 'neutral': 'bg-blue-950', 'loss': 'bg-yellow-950'}
    status = coach.get('status', 'neutral')
    ui.label(coach.get('summary', '')).classes(
        f'{_color_map.get(status, "text-gray-300")} {_bg_map.get(status, "")} px-3 py-2 rounded mb-2 text-sm'
    )

    with ui.row().classes('gap-6 mb-2'):
        with ui.column().classes('items-center'):
            ui.label('Curva').classes('text-xs text-gray-400')
            ui.label(str(coach.get('name', '—'))).classes('font-bold text-white')
        with ui.column().classes('items-center'):
            ui.label('Impacto').classes('text-xs text-gray-400')
            _tl = coach.get('time_lost') or 0.0
            ui.label('%+.3f s' % _tl).classes('font-bold ' + ('text-green-400' if _tl < 0 else 'text-red-400'))
        with ui.column().classes('items-center'):
            ui.label('Apex').classes('text-xs text-gray-400')
            ui.label('%s m' % coach.get('apex', {}).get('ref_apex_m', '—')).classes('font-bold text-white')

    actions = coach.get('actions') or []
    if actions:
        ui.label('Plan de ataque').classes('text-sm font-bold text-white mb-1')
        for action in actions:
            ui.label(f'· {action}').classes('text-sm text-gray-300')

    detail_rows = []
    br = coach.get('braking') or {}
    if br.get('delta_start_m') is not None:
        detail_rows.append({'Punto clave': 'Frenada', 'Referencia': '%s m' % br.get('ref_start_m', '—'), 'Tu': '%s m' % br.get('drv_start_m', '—'), 'Diferencia': '%+d m' % br['delta_start_m']})
    if br.get('delta_peak_pct') is not None:
        detail_rows.append({'Punto clave': 'Pico de freno', 'Referencia': '%s%%' % br.get('ref_peak_pct', '—'), 'Tu': '%s%%' % br.get('drv_peak_pct', '—'), 'Diferencia': '%+d pp' % br['delta_peak_pct']})
    ap = coach.get('apex') or {}
    if ap.get('delta_vmin_kmh') is not None:
        detail_rows.append({'Punto clave': 'V-Min', 'Referencia': '%s km/h' % ap.get('ref_vmin_kmh', '—'), 'Tu': '%s km/h' % ap.get('drv_vmin_kmh', '—'), 'Diferencia': '%+d km/h' % ap['delta_vmin_kmh']})
    th = coach.get('throttle') or {}
    if th.get('delta_gas100_m') is not None:
        detail_rows.append({'Punto clave': 'Gas 100%', 'Referencia': '%s m' % th.get('ref_gas100_m', '—'), 'Tu': '%s m' % th.get('drv_gas100_m', '—'), 'Diferencia': '%+d m' % th['delta_gas100_m']})
    lat = coach.get('lateral') or {}
    if lat.get('delta_peak_g') is not None:
        detail_rows.append({'Punto clave': 'G lateral', 'Referencia': '%.2f G' % lat.get('ref_peak_g', 0.0), 'Tu': '%.2f G' % lat.get('drv_peak_g', 0.0), 'Diferencia': '%+.2f G' % lat['delta_peak_g']})
    gear = coach.get('gear') or {}
    if gear.get('ref') or gear.get('drv'):
        detail_rows.append({
            'Punto clave': 'Marcha/RPM en apex',
            'Referencia': '%s · %s rpm' % (gear.get('ref', {}).get('gear', '—'), gear.get('ref', {}).get('rpm', '—')),
            'Tu': '%s · %s rpm' % (gear.get('drv', {}).get('gear', '—'), gear.get('drv', {}).get('rpm', '—')),
            'Diferencia': '%+d rpm' % gear['delta_rpm'] if gear.get('delta_rpm') is not None else '—',
        })
    if detail_rows:
        cols = ['Punto clave', 'Referencia', 'Tu', 'Diferencia']
        ui.table(
            columns=[{'name': c, 'label': c, 'field': c, 'align': 'left'} for c in cols],
            rows=detail_rows,
        ).classes('w-full text-xs mt-2').props('flat dense')


def _render_resumen_tab(charts_of):
    ui.label('Resumen de vuelta').classes('text-base font-bold text-white mb-2')
    overview = charts_of('delta_map') + charts_of('time_loss_bar')
    if overview:
        with ui.row().classes('gap-2 flex-wrap'):
            for p in overview:
                try:
                    with open(p, 'rb') as f:
                        ui.image(f.read()).classes('rounded').style('max-width:500px')
                except Exception:
                    pass
    gg = charts_of('gg_diagram')
    if gg:
        ui.label('Circulo de friccion (G-G)').classes('text-sm font-bold text-white mt-3 mb-1')
        try:
            with open(gg[0], 'rb') as f:
                ui.image(f.read()).classes('rounded').style('max-width:400px')
        except Exception:
            pass
    if not overview and not gg:
        ui.label('No hay graficas de resumen disponibles para esta comparacion.').classes('text-gray-400')


def _render_vuelta_tab(charts_of):
    ui.label('Vista completa de la vuelta — todos los canales').classes('text-base font-bold text-white mb-2')
    full = charts_of('full_lap')
    if full:
        try:
            with open(full[0], 'rb') as f:
                ui.image(f.read()).classes('rounded w-full')
        except Exception:
            pass
    else:
        ui.label('No hay vista completa disponible para esta comparacion.').classes('text-gray-400')


def _render_next_btn(state, current_step, navigate):
    from .ng_helpers import _FLOWS, _STEPS, _DEFAULT_FLOW
    flow = _FLOWS.get(state.flow_key, _FLOWS[_DEFAULT_FLOW])
    if current_step not in flow['steps']:
        remaining = sorted(s for s in flow['steps'] if s > current_step)
        if remaining:
            next_i = remaining[0]
            ui.button(
                'Continuar con tu flujo — Ir al Paso %d (%s) →' % (next_i, _STEPS[next_i]),
                on_click=lambda: navigate(next_i),
            ).props('color=primary unelevated')
        return
    next_i = flow['next'].get(current_step)
    if next_i is None:
        ui.label('Completaste todos los pasos de tu flujo!').classes('text-green-400 font-bold')
    else:
        ui.button(
            'Ir al Paso %d — %s →' % (next_i, _STEPS[next_i]),
            on_click=lambda: navigate(next_i),
        ).props('color=primary unelevated')
