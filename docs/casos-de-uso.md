# Casos de uso — personas, combinaciones y evaluación

> **Para qué es este documento.** Mapea **quién** usa SimGhostInputs y **cómo**, en todas las
> combinaciones razonables (perfil × fuente de datos × referencia × objetivo × hardware ×
> interfaz), y **evalúa** si el producto actual los sirve bien. Es la lente para encontrar
> fricciones y gaps, y la rúbrica contra la que se mide la UX (ver
> [`docs/ux-patterns.md`](ux-patterns.md)). Alineado con el nicho del
> [`PRODUCT_BRIEF.md`](../PRODUCT_BRIEF.md): sim racer de hobby/semi-competitivo, **datos locales,
> sin IA en el pipeline, salidas estándar**.
>
> Generado 2026-06-28 en una pasada de evaluación. Cada caso tiene un veredicto:
> **✅ cubierto** · **⚠️ fricción** (funciona pero estorba) · **❌ gap** (no se puede hoy).

---

## 1. Las dimensiones que combinan a un usuario

Un usuario real es una **combinación** de estas variables. No son personas aisladas: el mismo
piloto puede ser "league racer + ACC + sin GPU + UI".

| Dimensión | Valores |
| :-- | :-- |
| **Perfil / intención** | Hobby (mejorar por gusto) · Semi-competitivo (liga) · Coach/mentor · Creador de contenido (YouTube/stream) |
| **Sim / fuente** | AMS2 (probado) · ACC/iRacing/rF2/LMU/GT7 vía sim-to-motec · CSV genérico (SimHub, apps de AC) · `.xlsx` de MoTeC |
| **Referencia** | Su propia mejor histórica · Vuelta de un coach/compañero · Solo tiene su outing (comparar dos vueltas del mismo archivo) |
| **Objetivo de salida** | Solo análisis (reporte) · Solo overlay (.webm) · Video completo (compose) |
| **Hardware** | GPU NVIDIA (NVENC) · Sin GPU (CPU) · Sin ffmpeg |
| **Interfaz** | UI Streamlit · CLI (scriptable/batch) |
| **Momento** | Primera vez (onboarding) · Recurrente (otra vuelta / otra sesión) |
| **Locale** | Export en-US (punto decimal, coma separador) · Export europeo (coma decimal, `;` separador) |

---

## 2. Personas base (arquetipos)

- **P1 · Marco, el de hobby.** AMS2 + VR, una liga casual los martes. Quiere saber dónde pierde
  tiempo sin volverse ingeniero de datos. Usa la **UI**. Tiene RTX. Compara contra su mejor vuelta.
- **P2 · Lucía, la de liga (semi-competitiva).** Corre ACC e iRacing. Le pasa la referencia un
  compañero más rápido. Quiere el reporte por curva **y** el overlay para estudiar la frenada.
- **P3 · Diego, el coach.** Analiza vueltas de sus alumnos. Necesita procesar **muchas vueltas/archivos**
  rápido y generar reportes repetibles. Cómodo con **CLI** y scripts. Reparte "track packs" (nombres de curva).
- **P4 · Sofía, la creadora.** Hace videos de YouTube. Lo que le importa es el **video con HUD**
  bien sincronizado y legible. No le interesa el CSV. Le importa que el overlay se vea **profesional**.
- **P5 · Andrés, el de sim raro / datos ajenos.** Usa Assetto Corsa con SimHub; su CSV no es de MoTeC.
  Necesita el **mapeo de columnas** (`--map`). Su Windows está en español → export con **coma decimal**.

---

## 3. Casos de uso evaluados

### 3.1 Onboarding y captura de datos

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C01 | Primera vez: instalar en Windows limpio | ⚠️→✅ | `setup.ps1` tenía fricciones reales en máquina virgen (stub de Python de la Store, `--source winget`, sin git, falta de `[test]`) — **corregidas** (commits 4a08f8b/288f66e). Queda: el flujo aún asume que sabes exportar de MoTeC. |
| C02 | Exportar telemetría de AMS2 (sim-to-motec → i2 → CSV) | ✅ | Guía paso a paso en Paso 0 (con placeholders de imágenes pendientes). |
| C03 | Entender qué CSV es "referencia" vs "piloto" | ⚠️ | El Paso 0 lo explica en texto, pero el concepto de "necesitas dos exports" es fácil de pasar por alto. Candidato a refuerzo visual. |
| C04 | Imágenes de la guía de exportación | ✅ | Las 4 imágenes (`s2m_01..04_*.png/gif`) **existen** en `docs/guide/` y se muestran en el Paso 0. (`_img_or_placeholder` solo cae a "pendiente" si faltan; aquí no faltan.) |

### 3.2 Importar y elegir vuelta

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C05 | Cargar CSV de MoTeC i2 (en-US) | ✅ | Importador probado. |
| C06 | Cargar `.xlsx` de MoTeC | ✅ | Requiere extra `[xlsx]`/openpyxl. |
| C07 | CSV genérico (SimHub/AC) con `--map` | ✅ | CLI con `--map`; **la UI sí tiene editor de mapeo** de columnas en "⚙️ Opciones avanzadas" del Paso 1 (`columna_original = canal`). Mejora posible: que aparezca de forma más visible cuando el archivo no parsea bien. |
| C08 | **Export europeo (coma decimal, `;`)** | ✅ | **Soportado en el código actual:** el importador maneja separador `;` y coma decimal; cubierto por tests (`test_semicolon_separator_supported`, `test_semicolon_with_decimal_comma`), **sin xfail**. (La memoria vieja del 17-jun lo daba como gap; se resolvió desde entonces — verificado contra el código de hoy.) |
| C09 | Elegir la vuelta a analizar | ✅ | Tabla por radio, marca la más rápida (🏆) y completas/incompletas. |
| C10 | Comparar dos vueltas del **mismo** outing (sin referencia externa) | ⚠️ | **Funciona** (cargar el mismo archivo como ref y piloto y elegir vueltas distintas con la tabla de vueltas), pero **no hay atajo guiado** "compárate contra ti mismo": el usuario sin referencia externa no sabe que puede. Mejora de onboarding, no un gap técnico. |

### 3.3 Análisis (Producto 1)

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C11 | Reporte por curva, delta, tiempo perdido | ✅ | `compare` + report.md + CSVs + PNGs. Núcleo sólido. |
| C12 | Avisos de comparación inválida (circuitos/autos distintos) | ⚠️→✅ | **Resuelto en NiceGUI v2.0** — `ng_step2.py` muestra cada aviso de `summary["avisos"]` al inicio del Paso 2 (etiqueta ⚠ amarilla por aviso). La UI Streamlit legacy aún no los muestra a nivel global (solo en la columna "Avisos" por curva). |
| C13 | Nombrar curvas / track pack | ✅ | CLI (`detect` + editar JSON) **y UI**: Paso 1 → "⚙️ Opciones avanzadas" detecta curvas y ofrece un `data_editor` para nombrarlas, o subir un `corners.json`. |
| C14 | Drill-down interactivo por curva | ❌ (futuro) | Visión capturada en PRODUCT_BRIEF §10, no implementada. Es el siguiente salto de valor de análisis. |

### 3.4 Overlay y video (Producto 2)

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C15 | Generar overlay.webm con alfa | ✅ | Render paralelo (N-1 cores). |
| C16 | Auto-sync por audio | ✅ | Correlación + aviso de zona gris (ADR 0008). |
| C17 | Compose con **GPU NVENC** | ⚠️ | NVENC se auto-detecta, pero en equipos con GPU NVIDIA usable la detección puede **caer a CPU** (hallazgo en la PC potente — en diagnóstico). Sofía (P4) con GPU paga render lento sin saber por qué. |
| C18 | Compose **sin GPU** (CPU libx264) | ✅ | Fallback correcto. |
| C19 | Compose **sin ffmpeg** | ⚠️ | `overlay` cae a frames PNG; `compose` falla con mensaje. No hay aviso temprano en la UI de que ffmpeg falta hasta que lo intentas. |
| C20 | Saber qué encoder se usó (GPU vs CPU) | ⚠️ | El Paso 4 anuncia la **política** ("NVENC si está disponible, libx264 si no") *antes* de componer, pero **no confirma el encoder real usado ni el tiempo** después; `compose_video()` no lo devuelve. El usuario no sabe si su GPU se aprovechó. Ata con C17. |
| C21 | Overlay legible / profesional | ⚠️ | Sujeto a evaluación visual (ver `ux-patterns.md` + ADR 0005-0007). Pendiente diagnóstico con capturas. |

### 3.5 Volumen, recurrencia y batch

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C22 | Procesar otra vuelta sin recargar | ✅ | Botón "Procesar otra vuelta" vuelve al inicio conservando archivos/referencia. |
| C23 | Batch de todas las vueltas (overlay) | ✅ (CLI) | `overlay --all-laps`. **No hay equivalente en la UI** (una vuelta por flujo, por diseño). Diego (P3) usa CLI. |
| C24 | Coach procesando N alumnos | ⚠️ | Viable por CLI scripteado, pero no hay un modo "lote de archivos" de primera clase. |
| C25 | Comparar entre sesiones (tendencia) | ❌ (futuro) | Diferido post-v1.0 (PRODUCT_BRIEF §7). |

### 3.6 Interfaz y hardware

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C26 | Todo desde CLI (scriptable) | ✅ | Principio "CLI primero". |
| C27 | Todo desde la UI sin tocar flags | ✅ | Wizard de 5 pasos con flujos. |
| C28 | Cancelar un render largo | ✅ | Botón Detener + cancelación al navegar (arreglado, race condition de sidebar). |
| C29 | Equipo potente como runner / VM limpia para probar setup | ✅ (infra) | PC potente como runner pesado de pruebas + VM `sgi-win11-clean` con snapshot (ver memoria de infra). |

---

## 4. Hallazgos priorizados (lo que sale de la evaluación)

> **Nota de honestidad.** Una primera pasada de este doc marcó como gaps varios casos (C04, C07,
> C08, C13) que **resultaron ya resueltos** al verificar contra el código actual — venían de
> memoria desactualizada. Corregidos arriba. La app está más completa de lo que parecía; los
> hallazgos reales son menos y más finos. Lección: evaluar siempre contra el código de hoy.

Ordenado por impacto en el nicho real (solo lo verificado contra el código):

1. **⚠️ C17 + C20 — GPU NVENC infrautilizada y sin confirmar el encoder real.** En la PC potente
   `compose` cae a CPU pese a haber GPU (en diagnóstico), y la UI no confirma qué encoder usó ni el
   tiempo. Va directo contra el objetivo "rápido". → diagnosticar la detección + que `compose_video`
   devuelva encoder y duración, y mostrarlos.
2. **⚠️ C12 — Avisos globales de comparación no se ven en la UI.** `summary["avisos"]` (autos/
   circuitos distintos, delta sospechoso) están en el motor pero el Paso 2 no los muestra. Fix chico
   y de alto valor (evita interpretar mal un reporte inválido). 
3. **⚠️ C19 — ffmpeg ausente sin aviso temprano.** Chequeo de prerrequisito al entrar al flujo de
   video, en vez de fallar al apretar "Componer".
4. **⚠️ C03 / C10 — Onboarding:** dejar más claro que se necesitan **dos** exports y que puedes
   **compararte contra ti mismo** del mismo archivo. UX, no técnica.
5. **❌ C14 — Drill-down por curva.** El mayor salto de valor de análisis (futuro, PRODUCT_BRIEF §10).
6. **⏳ C21 — Calidad visual del HUD y de la UI.** Pendiente del diagnóstico con capturas
   ([`docs/ux-patterns.md`](ux-patterns.md)) generadas en el host.

> Los hallazgos de UX visual (C21 y el detalle por pantalla) se desarrollan en
> [`docs/ux-patterns.md`](ux-patterns.md) con capturas, una vez generadas en el host.
