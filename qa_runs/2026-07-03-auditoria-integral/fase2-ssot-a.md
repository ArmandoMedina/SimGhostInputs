# Auditoría de drift documentación↔código — Fase 2, Lote SSOT-A
**Fecha:** 2026-07-03  
**Rama:** codex/sgi-v2-merge  
**Scope:** README.md · docs/guia-usuario.md · CONTRIBUTING.md §3 (estructura/entorno) · CONTRIBUTING.md §7  
**Método:** contraste afirmación→código real (cli.py, pyproject.toml, fantasma/ui/, fantasma/viz/overlay.py, fantasma/importers/)  
**Auditora:** Fase 2 SSOT-A (orquestado por Claude)

---

## Tabla de severidades

| Severidad | Descripción |
| :-- | :-- |
| CRÍTICA | El documento describe una realidad que no existe o que activamente confunde a un contribuidor |
| ALTA | Hecho incorrecto o ausencia que impide reproducir el flujo descrito |
| MEDIA | Hecho incompleto o ambiguo que requiere interpretación extra |
| BAJA | Inconsistencia menor, vocabulario impreciso o información desactualizada sin impacto operacional |

---

## README.md

### Drift 1 — `[ui-ng]` extra ausente de la tabla de dependencias (ALTA)

**Afirmación (README §Instalación / tabla de dependencias):**
> `streamlit + pandas` | Python opcional | `fantasma ui` — interfaz gráfica local | `pip install 'fantasma-inputs[ui]'`

La tabla lista seis extras (xlsx, overlay/matplotlib/Pillow, charts, ui, sync, voice) pero omite completamente `[ui-ng]`.

**Realidad — pyproject.toml:**
```
ui-ng = ["nicegui>=3.14,<4", "pandas>=2,<3", "pywebview>=5,<6"]
```
El extra `[ui-ng]` existe en pyproject.toml y la entrada `[full]` lo incluye:
```
full = [..., "nicegui>=3.14,<4", "pywebview>=5,<6"]
```
El entry point `fantasma-ng` (declarado en `[project.scripts]`) apunta a `fantasma.ui.ng_app:run`.  
Un contribuidor o usuario que instale `[full]` obtiene NiceGUI sin saber que existe.  
Un usuario que instale `[ui]` no consigue el frontend v2.

**Consecuencia:** la tabla de dependencias es la SSOT de instalación (§8), y hoy oculta un extra entero con su propia UI y su propio entry point.

---

### Drift 2 — Licencias de terceros: NiceGUI y pywebview no mencionados (MEDIA)

**Afirmación (README §Licencia / Dependencias de terceros):**
> Streamlit usa Apache 2.0 [...] Todas las dependencias Python del proyecto (openpyxl, matplotlib, Pillow, pandas, scipy, numpy) son MIT o BSD.

**Realidad:**
`nicegui` (Apache 2.0) y `pywebview` (BSD-3-Clause) son dependencias reales del paquete (en `[ui-ng]` y `[full]`), no listadas. La lista "openpyxl, matplotlib, Pillow, pandas, scipy, numpy" está incompleta.  
Impacto práctico: ninguna de las dos licencias crea conflicto con AGPL-3.0, pero la omisión contradice la intención de exhaustividad de esta sección.

---

### Drift 3 — Badge/nota de estado "v1.0.0 estable" con código v2 activo en la rama (MEDIA)

**Afirmación (README línea 3 y bloque NOTE):**
> [![Estado](https://img.shields.io/badge/estado-v1.0.0%20estable-brightgreen)](CHANGELOG.md)  
> v1.0 — Pipeline AMS2 completo, documentado y probado.

**Realidad:**
- `pyproject.toml` sigue en `version = "1.0.0"` → badge técnicamente correcto para versión released.  
- La rama `codex/sgi-v2-merge` tiene en `[Unreleased]` del CHANGELOG: UI NiceGUI v2.0 completa (ng_app + ng_step0–4), Pace Notes CLI, render paralelo optimizado, 190+ tests, empaquetado Inno Setup. Este código ya existe en `fantasma/ui/ng_*.py`, `fantasma/viz/pacenotes.py`, `main_gui.py`, `tools/build_installer.py`, `tools/installer.iss`.
- El bloque NOTE dice "El motor CLI, la interfaz gráfica y el flujo de video con HUD están validados" — verdadero para Streamlit v1, pero la frase no avisa al lector de que la UI ya tiene un sucesor NiceGUI sin lanzar oficialmente.

**Consecuencia:** riesgo bajo si el lector ve solo la versión main; riesgo medio en esta rama porque el código real es v2 y la nota de vitrina sigue en v1.

---

### No-drift confirmados en README.md

| Aspecto | Veredicto |
| :-- | :-- |
| Comandos CLI (laps, detect, compare, overlay, compose, pacenotes, wear, ui) | OK — todos existen con los flags documentados |
| Flag `--format` de overlay (webm, prores, png) | OK — `choices=["prores","webm","png"]` en cli.py |
| Flag `--auto-sync` con `--driver` | OK — argumentos confirmados en cli.py |
| Flag `--pace-notes-dir` y `--pace-notes-volume` | OK — confirmados en cli.py |
| Tabla de colores HUD (verde/rojo/ámbar/violeta/amarillo/naranja) | OK — coincide con paleta de overlay.py (`_GAS`, `_FRENO`, `_ABS`, `_TCS`, `_GMED`, `_GMAX` y sus versiones dim de referencia) |
| Tabla de sims/importadores (AMS2 probado, otros vía sim-to-motec→i2→CSV) | OK — describe el flujo de captura, no importadores directos; los importers reales (motec_csv, generic_csv) soportan exactamente eso |
| Step de pip manual (xlsx, overlay, charts, ui, sync, voice, full, test) | OK — todos estos extras existen en pyproject.toml |
| Setup con setup.ps1 (flags -Full, -Yes -SkipSystem) | Sin código fuente de setup.ps1 en scope — no auditado directamente; asumido OK por git log |

---

## docs/guia-usuario.md

### Drift 4 — Descripción del UI mezcla features de NiceGUI con el comando `fantasma ui` (Streamlit) (ALTA)

Esta es la deriva más extendida del documento. La guía describe el wizard de 5 pasos como si fuera una sola interfaz, pero `fantasma ui` lanza Streamlit y `fantasma-ng` lanza NiceGUI. Varias features descritas solo existen en la NiceGUI:

**Afirmación §3 "Desde la UI" — encoder y duración al terminar (§7):**
> Una vez completada la composición, el Paso 4 muestra qué encoder se usó realmente (`h264_nvenc` si se detectó GPU NVIDIA, `libx264` si no) y cuánto tardó.

**Realidad:** Per CHANGELOG [Unreleased]:  
> "`compose_video()` devuelve dict `{"path", "encoder", "duration_s"}`. La UI **NiceGUI** Paso 4 muestra el encoder usado."

El Streamlit `step4.py` no tiene esta visualización del encoder. Quien usa `fantasma ui` (Streamlit) no ve este feedback.

**Afirmación §7:**
> Si usas `fantasma ui`, el Paso 4 incluye un botón «Detectar sincronía automáticamente» que hace lo mismo desde la interfaz gráfica.

**Realidad:** El botón "Detectar sincronía" existe en `ng_step4.py` (NiceGUI). En el `step4.py` de Streamlit hay detección de sync integrada en el flujo del paso, pero no como botón separado aislado con ese nombre. La guía atribuye a `fantasma ui` (=Streamlit) una UX que pertenece a `fantasma-ng` (=NiceGUI).

---

### Drift 5 — "modo oscuro siempre activo" para `fantasma ui` (ALTA)

**Afirmación §3:**
> `fantasma ui` abre un asistente local en **modo oscuro** (siempre activo; el exe nativo usa este modo para garantizar contraste legible).

**Realidad:**  
- `ng_app.py` (NiceGUI): `ui.dark_mode(True)` — dark mode forzado. ✓  
- `app.py` (Streamlit): no tiene `st.set_page_config(theme=...)` ni fuerza dark mode. El dark mode de Streamlit depende de la configuración del sistema del usuario o de `.streamlit/config.toml` (no existe en el repo).  
El paréntesis "el exe nativo usa este modo" es verdadero para el NiceGUI exe. Pero la frase completa hace que el lector asuma que `fantasma ui` (Streamlit) también garantiza dark mode, lo cual no está garantizado.

---

### Drift 6 — Breadcrumb y sidebar "✅ paso completado" (MEDIA)

**Afirmación §3:**
> El **sidebar izquierdo** muestra el progreso: ✅ paso completado, ▶️ paso actual, ○ paso pendiente en tu flujo, · paso opcional fuera del flujo elegido.

**Realidad:**  
- NiceGUI (`ng_app.py`): CHANGELOG menciona "sidebar con checkmark ✅ cuando el paso está completo" — feature v2.0.  
- Streamlit (`app.py`): el sidebar existe pero usa un sistema de emojis/marcas diferente (no auditado en detalle aquí; el step0.py Streamlit usa `st.container(border=True)` para las tarjetas, no breadcrumbs).  
La descripción en §3 es consistente con NiceGUI pero puede no corresponder a Streamlit.

---

### Drift 7 — "componente `ui.upload` de NiceGUI" vs descripción de Paso 1 (MEDIA)

**Afirmación §3 "El Paso 1":**
> aparece una zona de carga integrada en el browser: haz clic en ella para abrir el selector de archivos del sistema operativo, o arrastra el `.csv` (o `.xlsx`) directamente sobre la zona.

**Realidad:** Per CHANGELOG [Unreleased]:  
> "UI NiceGUI Paso 1: zona de carga de CSV migra de botón con diálogo nativo (tkinter) a componente `ui.upload` de NiceGUI — el picker pasa a ser un componente integrado en el browser con soporte de arrastre"

El Streamlit `step1.py` usa `_pick_file()` que abre un diálogo nativo del SO, no una zona drag-and-drop integrada. La descripción de "arrastra el `.csv` directamente sobre la zona" describe NiceGUI, no Streamlit.

---

### No-drift confirmados en guia-usuario.md

| Aspecto | Veredicto |
| :-- | :-- |
| Flujo CLI completo (laps, detect, compare, overlay, compose, pacenotes) | OK |
| Flags de overlay (--format, --start, --end, --fps, --all-laps, --corners) | OK — todos existen en cli.py |
| Flag --pace-notes-dir con --driver en compose | OK |
| Descripción de Pace Notes (plan.json, WAVs, countdown, separación mínima) | OK |
| Rutas CrewChiefV4/pace_notes/ams2/<pista> | OK — ver `_resolve_pacenotes_outdir` en cli.py |
| Descripción de correlación cruzada (150–500 Hz, z-score, ~0.5 s) | OK — consistente con viz/sync.py |

---

## CONTRIBUTING.md §3 — Entorno de desarrollo

### Drift 8 — Estructura del proyecto omite el frontend NiceGUI completo (CRÍTICA)

**Afirmación (CONTRIBUTING §3 "Estructura del proyecto"):**
```
ui/   interfaz Streamlit — app.py (router), step0-4.py (pasos), _helpers.py (compartido)
```

**Realidad — fantasma/ui/ en disco:**
```
app.py          # Streamlit router (sigue existiendo)
step0.py        # Streamlit paso 0
step1.py        # Streamlit paso 1
step2.py        # Streamlit paso 2
step3.py        # Streamlit paso 3
step4.py        # Streamlit paso 4
_helpers.py     # helpers compartidos Streamlit
ng_app.py       # NiceGUI router v2.0  ← NO MENCIONADO
ng_step0.py     # NiceGUI paso 0       ← NO MENCIONADO
ng_step1.py     # NiceGUI paso 1       ← NO MENCIONADO
ng_step2.py     # NiceGUI paso 2       ← NO MENCIONADO
ng_step3.py     # NiceGUI paso 3       ← NO MENCIONADO
ng_step4.py     # NiceGUI paso 4       ← NO MENCIONADO
ng_state.py     # AppState NiceGUI     ← NO MENCIONADO
ng_helpers.py   # helpers NiceGUI      ← NO MENCIONADO
__init__.py
```

`ng_app.py` ya tiene el docstring `"""NiceGUI entry point para SimGhostInputs v2.0."""` y `main_gui.py` en la raíz es su entry point para el empaquetado. La descripción "interfaz Streamlit" es factualmente incompleta: hay dos UIs completas, ocho archivos invisibles para el contribuidor que lea §3.

**Consecuencia operacional:** un contribuidor que quiera trabajar en la UI no sabrá que hay un segundo frontend activo. No entenderá qué instalar (`[ui]` vs `[ui-ng]`), qué probar ni cuál es la UI "principal" en v2.

---

### Drift 9 — `pip install -e ".[dev,test,ui,sync]"` no incluye `[ui-ng]` (MEDIA)

**Afirmación (CONTRIBUTING §3 "Puesta a punto del clon"):**
```powershell
pip install -e ".[dev,test,ui,sync]"
```

**Realidad:** Para trabajar en la UI NiceGUI v2.0 se necesita también `[ui-ng]`:
```
ui-ng = ["nicegui>=3.14,<4", "pandas>=2,<3", "pywebview>=5,<6"]
```
El comando recomendado no instala NiceGUI. Un contribuidor que siga las instrucciones al pie de la letra no puede levantar `fantasma-ng` ni correr los tests e2e del wizard NiceGUI (`tests/ui/test_e2e_wizard.py`).

---

### No-drift confirmados en CONTRIBUTING §3

| Aspecto | Veredicto |
| :-- | :-- |
| `pip install -e ".[full]"` | OK — extra `[full]` existe en pyproject.toml |
| `fantasma ui` para verificar | OK — `fantasma ui` lanza Streamlit correctamente |
| `fantasma --help` | OK — el entry point `fantasma = "fantasma.cli:main"` existe |
| `pip install -e ".[test]"` + `pytest` | OK |
| `git config core.hooksPath .githooks` | No auditado contra disco (fuera de scope directo) |
| core/ — normalize, corners, compare (lap.py existe) | OK — `fantasma/core/` tiene lap.py, normalize.py, corners.py, compare.py, wear.py |
| importers/ — MoTeC CSV/XLSX, CSV genérico | OK — motec_csv.py, generic_csv.py, _util.py |
| viz/ — gráficas, overlay HUD, composición de video, sincronía | OK — charts.py, overlay.py, compose.py, sync.py, report.py, pacenotes.py, hud_preview.py |
| cli.py — punto de entrada | OK |

---

## CONTRIBUTING.md §7 — Qué contribuciones son bienvenidas

### Drift 10 — "Empaquetado como `.exe` con PyInstaller" listado como bienvenido pero ya implementado (ALTA)

**Afirmación (CONTRIBUTING §7 "También bienvenido"):**
> Empaquetado como `.exe` con PyInstaller para usuarios sin Python

**Realidad:**
- `main_gui.py` es el entry point de empaquetado (docstring: `"Entry point para nicegui-pack / PyInstaller"`).
- `tools/build_installer.py` usa `nicegui-pack` (que usa PyInstaller bajo el capó) para generar un bundle one-dir.
- `tools/installer.iss` es el script Inno Setup para el instalador Windows doble-clic.
- Per CHANGELOG [Unreleased]: "Empaquetado Windows: `tools/build_installer.py` (nicegui-pack) y `tools/installer.iss` (Inno Setup) para instalador doble-clic."

La contribución está hecha. Listarla como "bienvenida" en §7 invita a duplicación o confunde sobre el estado real. Además, el término "PyInstaller" en §7 es impreciso: el enfoque adoptado es `nicegui-pack` (que envuelve PyInstaller pero tiene su propia CLI y convenciones). Un contribuidor que llegue con un PR de PyInstaller desnudo estaría duplicando trabajo existente con una herramienta diferente a la adoptada.

**Referencia cruzada:** CONTRIBUTING §8 SSOT table ya registra `tools/build_installer.py` y `tools/installer.iss` como dueños canónicos del empaquetado. La inconsistencia es entre §7 (presenta esto como pendiente) y §8 (ya lo registra como existente).

---

### No-drift confirmados en CONTRIBUTING §7

| Aspecto | Veredicto |
| :-- | :-- |
| Importadores nuevos (MoTeC .ld, iRacing .ibt, SimHub, ACC, rF2) como alta prioridad | OK — solo existen motec_csv.py y generic_csv.py, todos esos importadores siguen pendientes |
| Track packs JSON en repo comunitario | OK |
| Tests unitarios para core/ | OK — hay tests pero la cobertura de viz/ e importers sigue incompleta según §3 |
| Robustez del detector (artefactos >100 m) | OK — advertencia honesta, el problema sigue abierto |
| Traducciones de UI o documentación | OK — pendiente |
| Guías de exportación para sims no documentados | OK — pendiente |
| Mejoras de rendimiento con benchmarks | OK |

---

## Resumen ejecutivo

| Doc | Veredicto |
| :-- | :-- |
| README.md | 3 drifts: 1 ALTA (extra [ui-ng] ausente), 1 MEDIA (licencias incompletas), 1 MEDIA (badge v1.0.0 con código v2 activo). CLI, colores HUD y tabla de sims correctos. |
| docs/guia-usuario.md | 4 drifts: 2 ALTAS (features NiceGUI atribuidas a `fantasma ui`/Streamlit; dark mode no garantizado en Streamlit), 2 MEDIAS (sidebar ✅ / zona drag-and-drop solo en NiceGUI). Flujo CLI íntegro y correcto. |
| CONTRIBUTING.md §3 | 2 drifts: 1 CRÍTICA (estructura de ui/ omite 8 archivos NiceGUI), 1 MEDIA (comando de puesta a punto omite [ui-ng]). |
| CONTRIBUTING.md §7 | 1 drift ALTA (empaquetado PyInstaller listado como bienvenido, ya implementado con nicegui-pack + Inno Setup). |

### Conteo por severidad

| Severidad | Cantidad |
| :-- | :-- |
| CRÍTICA | 1 |
| ALTA | 4 |
| MEDIA | 4 |
| BAJA | 0 |
| **Total drifts** | **9** |

_(Nota: §8 de CONTRIBUTING tiene una fila de blast-radius que dice "la UI Streamlit" — no contabilizada porque cae fuera del scope §3+§7 del lote y su impacto es vocabulario, no operacional.)_

### Los 3 drifts más graves

1. **[CRÍTICA] CONTRIBUTING §3 — estructura de `ui/`**: describe solo la UI Streamlit, omite 8 archivos del frontend NiceGUI v2.0 — un contribuidor nuevo no sabe que existe la segunda UI, qué instalar ni qué probar.

2. **[ALTA] README.md — tabla de dependencias**: el extra `[ui-ng]` (NiceGUI + pywebview, con su entry point `fantasma-ng`) no existe en la tabla; `[full]` lo incluye silenciosamente. El SSOT de instalación está incompleto.

3. **[ALTA] docs/guia-usuario.md — features NiceGUI atribuidas a `fantasma ui` (Streamlit)**: el encoder mostrado en Paso 4, el dark mode garantizado y el botón "Detectar sincronía" son features del frontend NiceGUI; el comando `fantasma ui` lanza Streamlit y no tiene esas features. La guía induce al usuario a esperar comportamiento que no verá.

---

_Artefacto generado por auditoría SSOT-A en qa_runs/2026-07-03-auditoria-integral/fase2-ssot-a.md_
