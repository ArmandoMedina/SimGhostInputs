"""Estado por sesión para la UI NiceGUI de SimGhostInputs.

Cada propiedad lee/escribe en app.storage.user, garantizando aislamiento
por tab/conexión del navegador.
"""

from nicegui import app as _ng_app

from .ng_helpers import _DEFAULT_FLOW


class AppState:
    """Proxy sobre app.storage.user con valores por defecto tipados."""

    def _get(self, key, default=None):
        return _ng_app.storage.user.get(key, default)

    def _set(self, key, value):
        _ng_app.storage.user[key] = value

    def _get_tab(self, key, default=None):
        return _ng_app.storage.tab.get(key, default)

    def _set_tab(self, key, value):
        _ng_app.storage.tab[key] = value

    # ── navegación ────────────────────────────────────────────────────────────

    @property
    def flow_key(self):
        return self._get("flow_key", _DEFAULT_FLOW)

    @flow_key.setter
    def flow_key(self, v):
        self._set("flow_key", v)

    @property
    def nav_step(self):
        return self._get("nav_step", 0)

    @nav_step.setter
    def nav_step(self, v):
        self._set("nav_step", v)

    @property
    def flow_chosen(self):
        return self._get("flow_chosen", False)

    @flow_chosen.setter
    def flow_chosen(self, v):
        self._set("flow_chosen", v)

    # ── vueltas ───────────────────────────────────────────────────────────────

    @property
    def ref_lap(self):
        return self._get("ref_lap")

    @ref_lap.setter
    def ref_lap(self, v):
        self._set("ref_lap", v)

    @property
    def drv_lap(self):
        return self._get("drv_lap")

    @drv_lap.setter
    def drv_lap(self, v):
        self._set("drv_lap", v)

    @property
    def ref_laps(self):
        return self._get("ref_laps")

    @ref_laps.setter
    def ref_laps(self, v):
        self._set("ref_laps", v)

    @property
    def drv_laps(self):
        return self._get("drv_laps")

    @drv_laps.setter
    def drv_laps(self, v):
        self._set("drv_laps", v)

    # ── rutas ─────────────────────────────────────────────────────────────────

    @property
    def ref_path(self):
        return self._get("ref_path")

    @ref_path.setter
    def ref_path(self, v):
        self._set("ref_path", v)

    @property
    def drv_path(self):
        return self._get("drv_path")

    @drv_path.setter
    def drv_path(self, v):
        self._set("drv_path", v)

    @property
    def ref_name(self):
        return self._get("ref_name")

    @ref_name.setter
    def ref_name(self, v):
        self._set("ref_name", v)

    @property
    def drv_name(self):
        return self._get("drv_name")

    @drv_name.setter
    def drv_name(self, v):
        self._set("drv_name", v)

    # ── curvas ────────────────────────────────────────────────────────────────

    @property
    def corners(self):
        return self._get("corners")

    @corners.setter
    def corners(self, v):
        self._set("corners", v)

    @property
    def corners_editable(self):
        return self._get("corners_editable", False)

    @corners_editable.setter
    def corners_editable(self, v):
        self._set("corners_editable", v)

    @property
    def gear_shifts(self):
        """Cambios de marcha detectados sobre la vuelta de REFERENCIA
        (detect_gear_shifts, core/corners.py) -- mismo patron que `corners`.
        None hasta que algun flujo de deteccion (Paso 1/2/3) los calcula."""
        return self._get("gear_shifts")

    @gear_shifts.setter
    def gear_shifts(self, v):
        self._set("gear_shifts", v)

    # ── análisis ──────────────────────────────────────────────────────────────

    @property
    def ref_col_map(self):
        return self._get("ref_col_map")

    @ref_col_map.setter
    def ref_col_map(self, v):
        self._set("ref_col_map", v)

    @property
    def summary(self):
        return self._get("summary")

    @summary.setter
    def summary(self, v):
        self._set("summary", v)

    @property
    def trace(self):
        return self._get("trace")

    @trace.setter
    def trace(self, v):
        self._set("trace", v)

    @property
    def rows(self):
        return self._get("rows")

    @rows.setter
    def rows(self, v):
        self._set("rows", v)

    @property
    def charts_paths(self):
        return self._get("charts_paths")

    @charts_paths.setter
    def charts_paths(self, v):
        self._set("charts_paths", v)

    # ── outputs ───────────────────────────────────────────────────────────────

    @property
    def last_overlay(self):
        return self._get("last_overlay")

    @last_overlay.setter
    def last_overlay(self, v):
        self._set("last_overlay", v)

    @property
    def last_pacenotes(self):
        return self._get("last_pacenotes")

    @last_pacenotes.setter
    def last_pacenotes(self, v):
        self._set("last_pacenotes", v)

    @property
    def last_compose_video(self):
        return self._get("last_compose_video")

    @last_compose_video.setter
    def last_compose_video(self, v):
        self._set("last_compose_video", v)

    @property
    def compose_offset(self):
        return self._get("compose_offset", 0.0)

    @compose_offset.setter
    def compose_offset(self, v):
        self._set("compose_offset", v)

    # ── jobs en curso (memoria del proceso, no persistidos a disco) ─────────────

    @property
    def active_overlay_job(self):
        """RenderJob del overlay del Paso 3 en curso, o None (ng_helpers.RenderJob).

        A diferencia del resto de AppState, vive en app.storage.tab (memoria
        del proceso, atada a la pestaña del navegador vía tab_id) y no en
        app.storage.user: RenderJob trae un threading.Event, que no es
        serializable a JSON, y app.storage.user se respalda a disco en JSON
        en cada escritura (se rompería en el primer backup). app.storage.tab
        sobrevive tanto a la navegación entre pasos como a un refresh de
        página (F5) dentro de la misma pestaña -- a diferencia de
        app.storage.client, que se pierde con la conexión -- lo suficiente
        para detectar un render activo si el usuario sale del Paso 3 y
        vuelve, y no arrancar un segundo render sobre el mismo outdir
        (riesgo de corromper el .webm de salida).
        """
        return self._get_tab("active_overlay_job")

    @active_overlay_job.setter
    def active_overlay_job(self, v):
        self._set_tab("active_overlay_job", v)

    # ── pace notes / cues (Paso 5) ───────────────────────────────────────────

    @property
    def cue_config(self):
        """Overrides de cue_config del Paso 5 (WS-4); None = usa DEFAULT_CONFIG."""
        return self._get("cue_config")

    @cue_config.setter
    def cue_config(self, v):
        self._set("cue_config", v)

    # ── preferencias de flujo ─────────────────────────────────────────────────

    @property
    def auto_compose(self):
        return self._get("auto_compose", False)

    @auto_compose.setter
    def auto_compose(self, v):
        self._set("auto_compose", v)

    @property
    def pending_autocompose(self):
        return self._get("pending_autocompose", False)

    @pending_autocompose.setter
    def pending_autocompose(self, v):
        self._set("pending_autocompose", v)

    # ── helpers de limpieza ───────────────────────────────────────────────────

    def clear_analysis(self):
        """Limpia resultados de comparación para forzar recálculo en Paso 2."""
        for k in ("summary", "trace", "rows", "charts_paths"):
            _ng_app.storage.user.pop(k, None)

    def clear_drv(self):
        """Limpia datos de la vuelta del piloto para procesar otra vuelta."""
        for k in (
            "drv_lap",
            "drv_laps",
            "drv_path",
            "drv_name",
            "summary",
            "trace",
            "rows",
            "charts_paths",
            "last_overlay",
            "corners",
            "corners_editable",
            "gear_shifts",
            "compose_offset",
        ):
            _ng_app.storage.user.pop(k, None)
