# ADR 0018 — Framework de UI v2.0: NiceGUI + nicegui-pack + Inno Setup

- **Estado:** Aceptada
- **Fecha:** 2026-06-30
- **Enmienda a:** [ADR 0010](0010-framework-ui-streamlit.md)

## Contexto

El ADR 0010 dejó como pendiente de v2.0 la evaluación del framework para el front custom,
con dos dolores declarados como gatillo: (1) techo de personalización de Streamlit y
(2) fricción de instalación. El benchmark completo está en
[`docs/benchmark-ui-framework.md`](../benchmark-ui-framework.md).

Hechos que enmarcan esta decisión:

- El usuario objetivo es **zero-técnico**: sim racer que no programa, que busca máxima
  eficiencia con mínimo esfuerzo. Para él, "instalar" significa doble-click en un `.exe`,
  no abrir una terminal.
- La dirección de migración está confirmada. La pregunta resuelta aquí es **cuál framework**
  logra los tres objetivos simultáneamente: (1) instalación doble-click sin Python preinstalado,
  (2) sin techo de personalización, (3) mejor instalador que el `setup.ps1` actual.
- NiceGUI v3.14.0 se publicó el 30-jun-2026. La incertidumbre de "v3.0 en progreso" del
  benchmark anterior queda resuelta — la API está estable.
- El PO confirma preferencia por **UI web** (tecnologías web bajo el capó) por compatibilidad
  cross-platform. El instalador `.exe` es Windows-first; el código corre igual en macOS y Linux.

## Decisión

La UI de v2.0 migra de Streamlit a **NiceGUI**, empaquetada con **nicegui-pack** (PyInstaller
oficial de NiceGUI) e instalada con **Inno Setup**.

**Modo de entrega:**

- **`.exe` empaquetado (usuario final):** `ui.run(native=True, reload=False)` — abre una
  ventana nativa (pywebview) sin browser visible. El usuario no ve `localhost`, no ve terminal.
  La app se abre como cualquier programa de Windows. Esto es lo correcto para el usuario
  zero-técnico: abrir en el browser del sistema crea confusión (pestañas, no sabe cómo cerrar,
  el servidor queda corriendo en segundo plano).
- **Modo dev / pip install / macOS / Linux:** `ui.run(native=False)` — sirve en `localhost`
  y abre el browser del usuario. Mismo código, mismo comportamiento, distinto modo de entrega.
  En macOS `nicegui-pack` puede generar un `.app`; en Linux, AppImage es posible. Eso es
  trabajo para cuando haya usuarios en esas plataformas — no bloquea v2.0.

**Instalador:**

- `nicegui-pack --onedir` genera la carpeta con Python embebido.
- Inno Setup toma esa carpeta y produce `SimGhostInputs-v2.0-Setup.exe` con:
  acceso directo en el Escritorio, entrada en "Agregar o quitar programas", desinstalador.
  El usuario descarga, doble-click, "Siguiente" tres veces, ícono en el Escritorio.
- El CI genera el instalador en cada tag y lo sube al GitHub Release.

## Razones

**NiceGUI resuelve los dos dolores simultáneamente, que ninguna otra opción logra.**

- **Personalización sin techo.** Modelo stateful sobre WebSocket (FastAPI persistente por
  sesión): un slider llama a un handler Python que hace `image.set_source(pil_image)` y empuja
  el update al browser per-tick, sin rerun completo. Es el patrón exacto que necesita la
  preview reactiva del HUD (dolor #1 de UX). Permite Vue.js, HTML/CSS/JS y componentes custom
  sin restricciones de layout.
- **Empaquetado oficial de primera clase.** `nicegui-pack` es mantenido por el mismo equipo.
  No es un workaround comunitario. Genera el `.exe` que incluye Python + todas las deps; el
  usuario no instala nada más (dolor #2 de instalación).
- **MIT — sin fricción con AGPL-3.0.**
- **Testabilidad comparable.** El fixture `user` de pytest de NiceGUI es el equivalente directo
  al `AppTest` de Streamlit: prueba la lógica de la UI en Python, sin browser. El fixture
  `screen` (Selenium) cubre lo que Playwright cubre hoy. Los tests de lógica de UI sobreviven
  a la migración; los smoke visuales se re-baselínean.
- **Costo de migración medio (3/5).** Los 6 archivos de `fantasma/ui/` se reescriben.
  `core/` no se toca — ADR 0010 honrado. El modelo mental Python-first, sin HTML/CSS obligatorio,
  es el más parecido a Streamlit de todas las alternativas evaluadas.
- **API estable.** v3.14.0 publicado el mismo día de esta decisión. No hay breaking change
  pendiente conocido.

## El camino que NO se toma (y por qué tienta)

- **Streamlit + fragments.** Tienta porque el costo de migración es cero. No resuelve: (a) el
  slider per-tick (solo dispara Python al soltar, no durante el drag — la preview live del HUD
  requeriría un custom component React/Svelte, trabajo equivalente a migrar); (b) el dolor de
  instalación (no hay ruta oficial a `.exe`). Resolver solo (a) dentro de Streamlit cuesta lo
  mismo que migrar a NiceGUI, y (b) queda sin resolver.
- **Flet.** Tienta por el bundle más pequeño y el `flet pack` oficial. Se descarta porque:
  paradigma Flutter (sin HTML/CSS), lo que obliga a rediseñar toda la UI en widgets tipados
  de Flutter; versión pre-1.0 (v0.85.x), API en flujo; sin pytest fixture para la UI.
  El costo de migración es 4/5 vs 3/5 de NiceGUI, sin ventaja que lo justifique.
- **Tauri + Python sidecar.** Tienta por el bundle pequeño del front Tauri (~5–15 MB).
  Pero el sidecar Python lleva el stack científico completo (numpy + scipy + PIL + matplotlib)
  y pesa 150–250 MB igual — no hay ahorro neto. Suma Rust + Node.js al toolchain de build.
  El WebView nativo no usa el browser del usuario, y en Linux depende de webkit2gtk
  (no siempre disponible). Demasiada complejidad para cero ganancia práctica.
- **Abrir en el browser del sistema (native=False) en el `.exe`.**  Tienta porque el PO
  prefiere UI web y cross-platform. Se descarta para el `.exe` porque confunde al usuario
  zero-técnico: el app "abre" el browser entre sus pestañas, no sabe cómo cerrarlo,
  el servidor queda corriendo en fondo. Con `native=True` la ventana se cierra limpiamente y
  el proceso termina. El código es web bajo el capó — la decisión es solo de entrega.

## Consecuencias

**Se gana:**
- Instalación doble-click sin Python preinstalado. Mejor que el `setup.ps1`.
- Preview reactiva del HUD per-tick, sin techo de personalización para futuras features de UI.
- Ventana propia que se comporta como cualquier app de escritorio para el usuario zero-técnico.
- CI genera el instalador automáticamente en cada release.

**Se acepta como costo:**
- Los 6 archivos de `fantasma/ui/` se reescriben. Trabajo estimado: ~2 semanas en sesiones
  normales (ver plan de migración en `docs/benchmark-ui-framework.md`).
- Bundle size ~150–250 MB (one-dir). Más que Streamlit sin empaquetar, pero comparable con
  cualquier app Python con stack científico. Verificar con spike antes de comunicar al usuario.
- `AppTest` (Streamlit) se reemplaza por el fixture `user` de NiceGUI. Los smoke visuales con
  Playwright se re-baselínean en el nuevo framework.
- Streamlit (`fantasma/ui/app.py` + pasos) se mantiene en paralelo hasta que la migración
  esté completa y probada — no se borra hasta que el nuevo UI pase todos los tests.

**Condición previa a iniciar la migración — spike obligatorio:**

Antes de escribir código de producción, verificar las 4 incertidumbres del benchmark:

| Incertidumbre | Cómo verificar |
|---|---|
| Bundle size real con stack completo | `nicegui-pack --onedir` en venv limpio; medir |
| Bug `--onefile` en Windows 11 24H2 | Probar en VM limpia (ya tenemos Hyper-V del spike de v1.0) |
| Latencia PIL per-tick en la preview del HUD | Prototipo: slider → PIL → `image.set_source()` → medir |
| AV false positives del `.exe` | Subir a VirusTotal |

## Enmiendas al ADR 0010

El ADR 0010 queda parcialmente reemplazado en su sección de consecuencias:

- La restricción "Mantener `core/` desacoplado" **se mantiene y se honra** — `core/` no cambia.
- La restricción "Testing a prueba de migración" **se actualiza**: AppTest → fixture `user` de
  NiceGUI (mismo nivel de abstracción, sin browser). Playwright para smoke visual se re-baselínea
  en la nueva UI en vez de tirarse.
- El ADR 0012 (Playwright para smoke visual) sigue siendo válido en espíritu; el baseline
  cambia de Streamlit a NiceGUI.
