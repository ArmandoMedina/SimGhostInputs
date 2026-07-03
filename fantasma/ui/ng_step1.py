"""Paso 1 — Importar: cargar archivos de referencia y piloto (NiceGUI)."""

import os

from nicegui import ui

from .ng_helpers import (
    _FLOWS,
    _best_lap_index,
    _cleanup_upload,
    _corners_from_json,
    _fmt_lap,
    _lap_options,
    _load_laps,
    _missing_distance,
    _save_upload,
    render_breadcrumb,
)

_NO_DIST_MSG = (
    "Este CSV no incluye el canal Distance. SimGhostInputs compara por "
    "distancia (es el eje maestro), asi que sin ese canal no se puede analizar. "
    "Vuelve a exportarlo desde MoTeC i2 marcando Include Distance Data."
)


async def render(state, navigate):
    # ── Flow / labels (computed early, needed for breadcrumb + load button) ──
    flow = _FLOWS.get(state.flow_key)
    _next_step = flow["next"].get(1, 2) if flow else 2
    _load_labels = {2: "Cargar y ver análisis →", 3: "Cargar y generar overlay →"}
    _load_label = _load_labels.get(_next_step, "Cargar →")

    # ── Breadcrumb bar ──────────────────────────────────────────────────────
    render_breadcrumb(1)

    ui.html(
        '<h1 class="page-heading" style="font-size:1rem;margin-bottom:4px">'
        "Paso 1 — Importar telemetría</h1>"
    )
    ui.html(
        '<p class="page-sub">Sube los dos archivos CSV. '
        "La app detecta automáticamente las vueltas.</p>"
    )

    # ── Estado local (mutable dicts para que los closures capturen la referencia) ──
    ref_state = {
        "laps": state.ref_laps,
        "path": state.ref_path,
        "name": state.ref_name,
        "sel_i": 0,
    }
    drv_state = {
        "laps": state.drv_laps,
        "path": state.drv_path,
        "name": state.drv_name,
        "sel_i": 0,
    }
    corners_state = {"data": None}

    # Pre-seleccionar vueltas ya cargadas
    if ref_state["laps"]:
        ref_state["sel_i"] = _best_lap_index(ref_state["laps"])
    if drv_state["laps"]:
        drv_state["sel_i"] = _best_lap_index(drv_state["laps"])

    # Forward declarations — handlers close over these names; the variables are
    # assigned to ui elements further below before any handler can fire.
    ref_status = None  # noqa: F841  (assigned below)
    ref_lap_col = None  # noqa: F841
    drv_status = None  # noqa: F841
    drv_lap_col = None  # noqa: F841
    load_err = None  # noqa: F841

    # ── Upload handlers ──────────────────────────────────────────────────────

    async def handle_ref_upload(path, original_name=None):
        try:
            laps = _load_laps(path)
        except Exception as ex:
            ref_status.set_text(f"Error al leer el archivo: {ex}")
            ref_status.classes(remove="upload-status text-green-400 text-yellow-400")
            ref_status.classes("text-red-400")
            return
        finally:
            _cleanup_upload(path)
        if _missing_distance(laps):
            ref_status.set_text(_NO_DIST_MSG)
            ref_status.classes(remove="upload-status text-green-400 text-yellow-400")
            ref_status.classes("text-red-400")
            return
        if not laps:
            ref_status.set_text(
                "No se detectaron vueltas. Verifica que el CSV incluye distancia y tiempo."
            )
            ref_status.classes(remove="upload-status text-green-400 text-red-400")
            ref_status.classes("text-yellow-400")
            return
        ref_state["laps"] = laps
        ref_state["path"] = path  # ruta del temp ya borrado — solo informativa, no releer
        ref_state["name"] = original_name or os.path.basename(path)
        best_i = _best_lap_index(laps)
        ref_state["sel_i"] = best_i
        ref_status.set_text(
            "✓ Referencia cargada: %s (%d vueltas en el archivo)"
            % (_fmt_lap(laps[best_i].laptime), len(laps))
        )
        ref_status.classes(remove="text-red-400 text-yellow-400")
        ref_status.classes("upload-status")
        ref_lap_col.clear()
        if len(laps) > 1:
            _render_lap_selector(ref_lap_col, ref_state, "ref")

    async def handle_drv_upload(path, original_name=None):
        try:
            laps = _load_laps(path)
        except Exception as ex:
            drv_status.set_text(f"Error al leer el archivo: {ex}")
            drv_status.classes(remove="upload-status text-green-400 text-yellow-400")
            drv_status.classes("text-red-400")
            return
        finally:
            _cleanup_upload(path)
        if _missing_distance(laps):
            drv_status.set_text(_NO_DIST_MSG)
            drv_status.classes(remove="upload-status text-green-400 text-yellow-400")
            drv_status.classes("text-red-400")
            return
        if not laps:
            drv_status.set_text(
                "No se detectaron vueltas. Verifica que el CSV incluye distancia y tiempo."
            )
            drv_status.classes(remove="upload-status text-green-400 text-red-400")
            drv_status.classes("text-yellow-400")
            return
        drv_state["laps"] = laps
        drv_state["path"] = path  # ruta del temp ya borrado — solo informativa, no releer
        drv_state["name"] = original_name or os.path.basename(path)
        best_i = _best_lap_index(laps)
        drv_state["sel_i"] = best_i
        drv_status.set_text(
            "✓ Tu vuelta cargada: %s (%d vueltas en el archivo)"
            % (_fmt_lap(laps[best_i].laptime), len(laps))
        )
        drv_status.classes(remove="text-red-400 text-yellow-400")
        drv_status.classes("upload-status")
        drv_lap_col.clear()
        if len(laps) > 1:
            _render_lap_selector(drv_lap_col, drv_state, "drv")

    async def on_ref_upload(e):
        try:
            suffix = os.path.splitext(e.file.name)[1] or ".csv"
            path = _save_upload(await e.file.read(), suffix)
            await handle_ref_upload(path, original_name=e.file.name)
        except Exception as ex:
            ref_status.set_text(f"Error al procesar el archivo: {ex}")
            ref_status.classes(remove="upload-status text-green-400 text-yellow-400")
            ref_status.classes("text-red-400")

    async def on_drv_upload(e):
        try:
            suffix = os.path.splitext(e.file.name)[1] or ".csv"
            path = _save_upload(await e.file.read(), suffix)
            await handle_drv_upload(path, original_name=e.file.name)
        except Exception as ex:
            drv_status.set_text(f"Error al procesar el archivo: {ex}")
            drv_status.classes(remove="upload-status text-green-400 text-yellow-400")
            drv_status.classes("text-red-400")

    async def do_load():
        if not ref_state["laps"]:
            load_err.set_text("Sube el archivo de referencia primero.")
            return
        if not drv_state["laps"]:
            load_err.set_text("Sube tu archivo de telemetría primero.")
            return
        load_err.set_text("")
        try:
            state.clear_analysis()
            ref_lap = ref_state["laps"][ref_state["sel_i"]]
            drv_lap = drv_state["laps"][drv_state["sel_i"]]
            corners = corners_state["data"] or (state.corners if state.corners_editable else None)
            ref_col_map = None
            raw_map = col_map_state["text"].strip()
            if raw_map:
                ref_col_map = dict(p.partition("=")[::2] for p in raw_map.splitlines() if "=" in p)
            state.ref_path = ref_state["path"]
            state.drv_path = drv_state["path"]
            state.ref_name = ref_state["name"]
            state.drv_name = drv_state["name"]
            state.ref_laps = ref_state["laps"]
            state.drv_laps = drv_state["laps"]
            state.ref_lap = ref_lap
            state.drv_lap = drv_lap
            state.corners = corners
            state.ref_col_map = ref_col_map
            if corners_state["data"]:
                state.corners_editable = True
            await navigate(_next_step)
        except Exception as ex:
            load_err.set_text(f"Error al cargar: {ex}")

    # ── Upload grid ─────────────────────────────────────────────────────────
    with ui.element("div").classes("upload-grid"):
        # ── Panel izquierdo: Referencia ──────────────────────────────────
        with ui.element("div").classes("upload-panel"):
            ui.html(
                '<div class="upload-panel-header">'
                '<span class="upload-panel-title">① Vuelta de referencia</span>'
                '<span class="lap-badge ref">REF</span>'
                "</div>"
            )

            with ui.element("div").classes("upload-zone"):
                ui.html('<span class="upload-icon">📂</span>')
                ui.html('<div class="upload-label">Haz clic para seleccionar tu archivo</div>')
                ui.html('<div class="upload-hint">.csv · .xlsx · máx. 50 MB</div>')
                ui.upload(
                    label="Seleccionar CSV",
                    on_upload=on_ref_upload,
                    auto_upload=True,
                ).props('accept=".csv,.xlsx" flat').classes("w-full")

            ref_status = (
                ui.label(
                    "⬆ Sube el archivo de referencia para continuar."
                    if not ref_state["laps"]
                    else "✓ Referencia ya cargada: %s (%d vueltas)"
                    % (
                        _fmt_lap(ref_state["laps"][ref_state["sel_i"]].laptime),
                        len(ref_state["laps"]),
                    )
                )
                .classes("upload-status" if ref_state["laps"] else "text-yellow-400")
                .style("margin:0 0 8px;display:block")
            )

            ref_lap_col = ui.column().classes("w-full")
            if ref_state["laps"] and len(ref_state["laps"]) > 1:
                _render_lap_selector(ref_lap_col, ref_state, "ref")

            with ui.expansion(
                "¿No tienes vuelta de referencia externa?", icon="help_outline"
            ).classes("text-xs opacity-70 mt-1"):
                ui.label(
                    "Puedes cargar el mismo CSV como Referencia y como Piloto, "
                    "y elegir vueltas distintas — así te comparas contra tu mejor vuelta del mismo archivo."
                )

        # ── Panel derecho: Driver ────────────────────────────────────────
        with ui.element("div").classes("upload-panel"):
            ui.html(
                '<div class="upload-panel-header">'
                '<span class="upload-panel-title">② Tu vuelta de hoy</span>'
                '<span class="lap-badge own">HOY</span>'
                "</div>"
            )

            with ui.element("div").classes("upload-zone"):
                ui.html('<span class="upload-icon">📂</span>')
                ui.html('<div class="upload-label">Haz clic para seleccionar tu archivo</div>')
                ui.html('<div class="upload-hint">.csv · .xlsx · máx. 50 MB</div>')
                ui.upload(
                    label="Seleccionar CSV",
                    on_upload=on_drv_upload,
                    auto_upload=True,
                ).props('accept=".csv,.xlsx" flat').classes("w-full")

            drv_status = (
                ui.label(
                    "⬆ Sube tu archivo de telemetría para continuar."
                    if not drv_state["laps"]
                    else "✓ Tu vuelta cargada: %s (%d vueltas)"
                    % (
                        _fmt_lap(drv_state["laps"][drv_state["sel_i"]].laptime),
                        len(drv_state["laps"]),
                    )
                )
                .classes("upload-status" if drv_state["laps"] else "text-yellow-400")
                .style("margin:0 0 8px;display:block")
            )

            drv_lap_col = ui.column().classes("w-full")
            if drv_state["laps"] and len(drv_state["laps"]) > 1:
                _render_lap_selector(drv_lap_col, drv_state, "drv")

    # ── Opciones avanzadas ────────────────────────────────────────────────────
    col_map_state = {"text": ""}

    with ui.expansion(
        "Opciones avanzadas — nombres de curvas y mapeo de columnas", icon="settings"
    ).classes("w-full mb-4"):
        ui.label("Nombres de curvas (opcional pero recomendado)").classes(
            "text-sm font-bold text-gray-300 mb-1"
        )
        ui.label(
            "Por defecto las curvas se llaman C01, C02... "
            "Si les das nombres reales apareceran en el reporte y en el HUD."
        ).classes("text-xs text-gray-400 mb-2")

        async def handle_corners_upload(e):
            try:
                content = await e.file.read()
                corners = _corners_from_json(content)
                corners_state["data"] = corners
                ui.notify(f"{len(corners)} curvas cargadas desde JSON", type="positive")
            except Exception as ex:
                ui.notify(f"Error al leer corners.json: {ex}", type="negative")

        async def detect_corners():
            if not ref_state["laps"]:
                ui.notify("Primero sube el archivo de referencia.", type="warning")
                return
            try:
                from fantasma.core.corners import detect_corners as _dc
                from fantasma.core.corners import extract_milestones as _em
                from fantasma.core.normalize import fastest_lap as _fl

                _evs, _ = _dc(_fl(ref_state["laps"]))
                cdet = _em(_fl(ref_state["laps"]), _evs)
                corners_state["data"] = cdet
                state.corners = cdet
                state.corners_editable = True
                ui.notify(f"{len(cdet)} curvas detectadas automaticamente.", type="positive")
            except Exception as ex:
                ui.notify(f"Error: {ex}", type="negative")

        with ui.row().classes("gap-4"):
            ui.upload(
                label="Subir corners.json",
                on_upload=handle_corners_upload,
                auto_upload=True,
            ).props('accept=".json"')
            ui.button("Detectar curvas automaticamente", on_click=detect_corners).props(
                "flat color=secondary"
            )

        ui.separator().classes("my-2")
        ui.label("Mapeo de columnas (solo si el archivo no se leyó correctamente)").classes(
            "text-sm font-bold text-gray-300 mb-1"
        )
        col_map_input = ui.textarea(
            label="Columnas",
            placeholder="Ejemplo:\n  mi_distancia = dist\n  tiempo_s = time",
        ).classes("w-full")
        col_map_input.on("update:model-value", lambda e: col_map_state.update({"text": e.value}))

    # ── Bottom actions ────────────────────────────────────────────────────────
    ref_ok = ref_state["laps"] is not None and len(ref_state["laps"]) > 0
    drv_ok = drv_state["laps"] is not None and len(drv_state["laps"]) > 0
    ref_class = "ok" if ref_ok else ""
    drv_class = "ok" if drv_ok else ""

    with ui.element("div").classes("bottom-actions"):
        ui.html(
            f'<div class="readiness-indicators">'
            f'<span class="readiness-item {ref_class}">'
            f'<span class="readiness-dot"></span>Referencia</span>'
            f'<span class="readiness-item {drv_class}">'
            f'<span class="readiness-dot"></span>Tu vuelta</span>'
            f"</div>"
        )
        with ui.element("div").style("display:flex;gap:8px;align-items:center"):
            ui.button("← Volver", on_click=lambda: navigate(0)).classes("btn-ghost").props("flat")
            load_err = ui.label("").classes("text-xs text-red-400")
            ui.button(_load_label, on_click=do_load).classes("btn-primary")


def _render_lap_selector(container, lap_state, key):
    with container:
        with ui.element("div").classes("lap-selector"):
            opts = _lap_options(lap_state["laps"])
            sel_label = ui.select(
                options=opts,
                value=opts[lap_state["sel_i"]],
                label="Cambiar vuelta",
            ).classes("w-full")

            def on_change(e):
                try:
                    idx = opts.index(e.value)
                    lap_state["sel_i"] = idx
                except ValueError:
                    pass

            sel_label.on("update:model-value", on_change)
