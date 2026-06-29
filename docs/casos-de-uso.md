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
| C04 | Imágenes de la guía de exportación | ❌ | Varias `docs/guide/*.png|gif` son **placeholders** (`_img_or_placeholder` muestra "Imagen pendiente"). La guía visual está incompleta. |

### 3.2 Importar y elegir vuelta

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C05 | Cargar CSV de MoTeC i2 (en-US) | ✅ | Importador probado. |
| C06 | Cargar `.xlsx` de MoTeC | ✅ | Requiere extra `[xlsx]`/openpyxl. |
| C07 | CSV genérico (SimHub/AC) con `--map` | ✅ (CLI) / ⚠️ (UI) | El CLI mapea columnas; **en la UI no hay editor de mapeo claro** para un CSV no-MoTeC. Andrés (P5) se atora si su CSV no tiene los headers esperados. |
| C08 | **Export europeo (coma decimal, `;`)** | ❌ | Gap conocido (xfail en la suite). Un Windows en español/UE exporta así y **el importador falla**. Afecta a una fracción grande de la comunidad objetivo (Europa). **Prioridad alta.** |
| C09 | Elegir la vuelta a analizar | ✅ | Tabla por radio, marca la más rápida (🏆) y completas/incompletas. |
| C10 | Comparar dos vueltas del **mismo** outing (sin referencia externa) | ⚠️ | Soportado conceptualmente (cargar el mismo archivo como ref y piloto, elegir vueltas distintas), pero **la UI no lo guía**: el usuario sin referencia externa no sabe que puede compararse consigo mismo del mismo archivo. |

### 3.3 Análisis (Producto 1)

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C11 | Reporte por curva, delta, tiempo perdido | ✅ | `compare` + report.md + CSVs + PNGs. Núcleo sólido. |
| C12 | Avisos de comparación inválida (circuitos/autos distintos) | ✅ | Avisos implementados (delta sospechoso, autos distintos). |
| C13 | Nombrar curvas / track pack | ✅ (CLI) / ⚠️ (UI) | `detect` + editar JSON es flujo CLI; en la UI no hay editor de nombres de curva cómodo. Diego (P3) lo hace a mano. |
| C14 | Drill-down interactivo por curva | ❌ (futuro) | Visión capturada en PRODUCT_BRIEF §10, no implementada. Es el siguiente salto de valor de análisis. |

### 3.4 Overlay y video (Producto 2)

| # | Caso | Veredicto | Notas |
| :-- | :-- | :-- | :-- |
| C15 | Generar overlay.webm con alfa | ✅ | Render paralelo (N-1 cores). |
| C16 | Auto-sync por audio | ✅ | Correlación + aviso de zona gris (ADR 0008). |
| C17 | Compose con **GPU NVENC** | ⚠️ | NVENC se auto-detecta, pero en equipos con GPU NVIDIA usable la detección puede **caer a CPU** (hallazgo en la PC potente — en diagnóstico). Sofía (P4) con GPU paga render lento sin saber por qué. |
| C18 | Compose **sin GPU** (CPU libx264) | ✅ | Fallback correcto. |
| C19 | Compose **sin ffmpeg** | ⚠️ | `overlay` cae a frames PNG; `compose` falla con mensaje. No hay aviso temprano en la UI de que ffmpeg falta hasta que lo intentas. |
| C20 | Saber qué encoder se usó (GPU vs CPU) | ❌ | La UI/CLI no dicen si compuso con NVENC o libx264 ni el tiempo — el usuario no puede saber si su GPU se está aprovechando. |
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

Ordenado por impacto en el nicho real:

1. **❌ C08 — Export europeo (coma decimal / `;`).** Rompe a la mitad de Europa. Es el gap más
   doloroso para el público objetivo. → arreglar el importador (detección de locale/separador).
2. **⚠️ C17/C20 — GPU NVENC infrautilizada + sin visibilidad del encoder.** Va contra el objetivo
   de "rápido"; el usuario no sabe si su GPU se usa. → diagnosticar detección + reportar encoder y tiempo.
3. **❌ C04 — Imágenes de la guía de exportación faltantes.** El onboarding visual está a medias.
4. **⚠️ C07/C10/C13 — Huecos de la UI vs CLI:** mapeo de columnas, compararse contra uno mismo,
   editar nombres de curva. La UI no expone capacidades que el CLI sí tiene.
5. **⚠️ C19 — ffmpeg ausente sin aviso temprano.** Chequeo de prerrequisitos al entrar al flujo de video.
6. **❌ C14 — Drill-down por curva.** El mayor salto de valor de análisis (futuro, post base).

> Los hallazgos de UX visual (C21 y el detalle de la UI) se desarrollan en
> [`docs/ux-patterns.md`](ux-patterns.md) con capturas, una vez generadas en el host.
