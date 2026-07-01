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
| C10 | Comparar dos vueltas del **mismo** outing (sin referencia externa) | ⚠️ | **Funciona** (cargar el mismo archivo como ref y piloto y elegir vueltas distintas con la tabla de vueltas), pero **no hay atajo guiado** "compárate contra ti mismo": el usuario sin referencia externa no sabe que puede. Mejora de onboarding, no un gap técnico. Parcialmente mejorado: el Paso 1 NiceGUI incluye un hint explicando cómo cargar el mismo CSV como referencia y piloto para compararse contra sí mismo. |

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
| C17 | Compose con **GPU NVENC** | ⚠️ | NVENC se auto-detecta, pero en equipos con GPU NVIDIA usable la detección puede **caer a CPU** (hallazgo en la PC potente — en diagnóstico). Sofía (P4) con GPU paga render lento sin saber por qué. Parcialmente mejorado: ahora el Paso 4 confirma qué encoder se usó realmente; si cae a CPU siendo inexplicable, el usuario puede reportarlo con evidencia. |
| C18 | Compose **sin GPU** (CPU libx264) | ✅ | Fallback correcto. |
| C19 | Compose **sin ffmpeg** | ⚠️→✅ | `overlay` cae a frames PNG; `compose` falla con mensaje. **Resuelto en NiceGUI v2.0**: el Paso 0 muestra aviso al seleccionar el flujo "Video con HUD" o "Solo overlay" si ffmpeg no está instalado; el Paso 3 y el Paso 4 bloquean el render con instrucción de instalación. El usuario recibe la alerta antes de perder tiempo. |
| C20 | Saber qué encoder se usó (GPU vs CPU) | ✅ | Resuelto — `compose_video()` devuelve `encoder` y `duration_s`; el Paso 4 NiceGUI los muestra post-compose. |
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

### 3.7 Combos de material de test — circuitos, clases y sesiones reales

> Material disponible (añadido 2026-07-01): 16 CSVs en `Pruebas finales/Pruebas finales/` + `GO BMW M4 GT3 NORDSCHLEIFE 2025 E Q01 MOTEC.csv` y dos sesiones del piloto `jocmaster` (Nordschleife, BMW M4 GT3, junio 2026), ambas en el root de `Paterial para test (no es un repo)/`.
> **Circuitos cubiertos:** Barcelona NC (~4.6 km) · Interlagos (~4.3 km) · Nordschleife 2025 (~20 km) · Nurburgring GP (~5.1 km).
> **Clases cubiertas:** GT3 (Aston Martin GT3 Evo, Audi R8 LMS EVO II, BMW M4 GT3, Chevrolet Corvette Z06 GT3R, Mercedes AMG GT3 Evo) · LMDh/Hypercar (Aston Martin Valkyrie, BMW Hybrid V8, Cadillac V-Series.R) · LMP2 (Oreca 07) · Fórmula (F3).
> **Anomalía de nomenclatura detectada:** `GO F3 INT E Q01 MOTEC.csv` y `GO ORECA 07 INT E Q01 MOTEC.csv` usan `INT` como código de pista en lugar del nombre completo `INTERLAGOS` que usan otros archivos del mismo set. No es un error de datos, pero rompe la homogeneidad del naming de los CSVs de test.

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C30 | Circuito corto vs largo: Barcelona NC vs Nordschleife — impacto en detección de vueltas y selección de fastest lap | ✅ | El par `GO BMW M4 GT3 BARCELONA NC` y `GO BMW M4 GT3 NORDSCHLEIFE 2025` ejercita los dos extremos de longitud. Barcelona NC (~12.7 MB): laptime ~1:45, outing de qualy con varios beacons, `fastest_lap()` elige entre múltiples candidatas. Nordschleife (~31 MB): laptime ~8–9 min, un qualy suele tener 1–2 vueltas completas — el filtro ≥90% de la más larga puede dejar una sola candidata. Caso crítico: qualy mono-vuelta en Nordschleife = `fastest_lap()` devuelve esa vuelta directamente sin comparar tiempos entre candidatas. La tabla de vueltas en la UI debe reflejar esto de forma clara (sin confundir "la única vuelta" con "la más rápida entre varias"). Verificado como flujo posible; la UI ya marca la seleccionada con 🏆. |
| C31 | Cross-car GT3 en Nordschleife: BMW M4 GT3 (ref) vs Audi R8 LMS EVO II (driver) — referencia cruzada dentro de la misma clase | ⚠️ | `GO BMW M4 GT3 NORDSCHLEIFE 2025` (ref, ~31 MB) + `GO AUDI R8 LMS EVO II NORDSCHLEIFE 2025` (driver, ~31 MB). Mismo circuito, misma clase GT3, distinto fabricante. Esperado: aviso `"autos distintos: BMW M4 GT3 (ref) vs Audi R8 LMS EVO II (piloto)"` si el metadato `Vehicle` está en el CSV de AMS2. La comparación técnica es válida — dentro del GT3 las geometrías de frenada y línea son comparables entre fabricantes. El ⚠️ es que el aviso actual no matiza "cross-car dentro de la misma clase" (legítimo y frecuente) vs "clases incompatibles" (probablemente inválido). Mejora futura: calibrar la severidad del aviso según la diferencia porcentual de laptime entre ref y driver. |
| C32 | Clases distintas en Interlagos: LMP2 Oreca 07 (driver) vs GT3 Aston Martin GT3 Evo (ref) | ⚠️ | `GO ASTON MARTIN GT3 EVO INTERLAGOS` (ref) + `GO ORECA 07 INT` (driver, INT = Interlagos según la anomalía de nomenclatura descrita arriba). Clases muy distintas: LMP2 vs GT3. Esperado: aviso `"autos distintos"` + probable `"delta sospechosamente grande"` si el LMP2 supera al GT3 en más del 50% del laptime de referencia (diferencia de clase típicamente > 10–15 s en Interlagos). Los canales disponibles en el CSV de Oreca vs GT3 pueden diferir (configuración de ABS/TC en LMP2 vs GT3). Si los metadatos `Vehicle` no están presentes en el export de AMS2, el aviso puede no emitirse — la comparación procedería sin advertencia. Pendiente de verificación real con los archivos. |
| C33 | Hypercar vs GT3 en Barcelona NC: Aston Martin Valkyrie (driver) vs Aston Martin GT3 Evo (ref) — diferencia de clase en el mismo circuito | ⚠️ | `GO ASTON MARTIN GT3 EVO BARCELONA NC` (ref, ~12.7 MB) + `GO ASTON MARTIN VALKYRIE BARCELONA NC` (driver, ~7.8 MB). Misma marca, distinta categoría: Hypercar vs GT3. Esperado: aviso `"autos distintos"` + aviso `"piloto más rápido que la referencia"` (Valkyrie es varios segundos por vuelta más rápido que el GT3 Evo en el mismo circuito). El tamaño menor del archivo del Valkyrie (~7.8 MB vs ~12.7 MB del GT3) a pesar de ser el mismo circuito sugiere menor cantidad de datos por vuelta o menos vueltas — posiblemente sesión más corta. Caso límite de uso pedagógico: ilustra cómo luce una comparación de clases distintas y qué avisos genera el sistema. No es una comparación accionable para mejorar técnica de conducción. |
| C34 | Flujo headless sin video: solo compare + pacenotes, sin overlay ni compose | ✅ | Cualquier par de CSVs de Pruebas finales sin video asociado. CLI: `fantasma compare <ref> <driver> [--corners <json>]` genera `report.md`, `delta.csv`, `corners_compare.csv`; luego `fantasma pacenotes` con el JSON de curvas detectado genera el pack WAV para CrewChief (`metadata.json` + archivos `.wav` por hito). Flujo completo de análisis + audio sin ffmpeg ni GPU: el caso más común de P3 (Diego, coach) cuando el alumno no tiene grabación de video. Nordschleife es el circuito de mayor valor para pacenotes: ~20 km de trazado, docenas de segmentos, el cue de audio previo a cada curva tiene impacto real sobre el piloto. Ninguno de los videos del material de test es necesario para este flujo. |
| C35 | Dos sesiones del mismo piloto en Nordschleife: evolución entre fechas (jocmaster jun-07 vs jun-21 de 2026) | ⚠️ | `Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-07T113535.csv` (~62 MB, sesión más antigua, como ref) vs `Nordschleife_2020_BMW_M4_GT3_jocmaster_Race_2026-06-21T122432.csv` (~56.1 MB, sesión más reciente, como driver). Mismo piloto, mismo auto (BMW M4 GT3), misma pista (Nordschleife layout 2020). Objetivo: medir evolución entre dos sesiones de carrera. Tres fricciones: (1) el nombre de pista es `Nordschleife_2020` mientras los CSVs de referencia GO usan `NORDSCHLEIFE 2025` — layouts distintos podría invalidar una comparación directa entre los jocmaster y los GO; (2) los tamaños de archivo distintos (62 MB vs 56.1 MB) indican diferente número de vueltas por sesión — `fastest_lap()` opera sobre cada outing por separado, lo que es correcto; (3) sesiones tipo `Race` incluyen in-lap, out-lap y posiblemente vueltas con tráfico o safety car — el filtro de completitud (≥90% de la más larga) debe descartar correctamente las vueltas atípicas. Pendiente de verificación con los archivos reales. |

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
7. **⚠️ C31 — Aviso "autos distintos" no distingue cross-car dentro de la misma clase de
   comparaciones entre clases incompatibles.** Comparar BMW M4 GT3 vs Audi R8 LMS EVO II en
   Nordschleife es un caso de uso legítimo y frecuente (mismo circuito, misma clase, distinto
   fabricante), pero el aviso actual tiene la misma severidad que comparar un LMP2 contra un GT3.
   Mejora: calibrar el aviso según la diferencia porcentual de laptime — si la diferencia es
   pequeña (<3%) y ambos autos tienen metadato de clase compatible, bajar la alarma a "informativo".

> Los hallazgos de UX visual (C21 y el detalle por pantalla) se desarrollan en
> [`docs/ux-patterns.md`](ux-patterns.md) con capturas, una vez generadas en el host.
