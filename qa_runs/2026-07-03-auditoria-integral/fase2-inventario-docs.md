# Fase 2 — Inventario crítico de documentación

> Auditoría pre-v2.0 · asiento **Armando** (arquitecto de la documentación) · 2026-07-03.
> Pedido explícito del PO. **Solo diagnóstico y propuesta — no se editó ni borró nada.**
> Lente: CONTRIBUTING §8 (quién es dueño SSOT de qué; los demás **enlazan, no duplican**).
> Dolor específico del PO: **documentos pequeños que repiten pedazos de contenido que ya
> vive en otro lado**, en vez de enlazar.

---

## 0. Alcance y método

Se inventariaron **124 documentos de proyecto** (`.md`). Se **excluyen** como no-documentación:
- `dist/**` (3 `.md` de dependencias empaquetadas — altair, nicegui, pyarrow: third-party).
- `.pytest_cache/README.md` (autogenerado por pytest).
- `qa_runs/**/report.md` y `**/compare/**` (~30 artefactos de evidencia generados por el
  pipeline; por diseño no son docs — ADR 0016/0019). Sí se inventarían `qa_runs/README.md` y
  los `fase1-*.md` de esta misma auditoría.

Reparto de los 124: raíz 6 · `docs/` sueltos 11 · `docs/_diagramas/` 1 · `docs/decisions/` 21
(README + plantilla + 19 ADR) · `engineering/` 13 · `product/` 50 · `templates/` 13 ·
`.claude/` 6 · `qa_runs/` 3.

**Veredicto global de salud:** la documentación está, en general, **bien gobernada**. La capa
`product/`+`engineering/`+`templates/` respeta la disciplina "enlaza, no dupliques" (la vigila
`auditar.ps1`), y los docs SSOT técnicos (`formato-datos`, `hud-reference`, `glosario`) son
dueños limpios sin satélites que los pisen. **El dolor del PO existe pero está acotado a ~12
documentos**, casi todos por la **transición Streamlit→NiceGUI (v2.0) mal cerrada** en la capa
de notas, más un puñado de satélites que parafrasean en vez de enlazar.

- **Documentos con función difusa, contenido obsoleto o duplicación fragmentada: ~12 de 124.**
- Pares/grupos con traslape real detectados: **5** (detallados en §3).

---

## 1. Tabla de inventario — raíz y `docs/` sueltos (donde vive el dolor)

Veredicto: **OK** / **actualizar** / **consolidar-en-X** / **convertir-en-enlace** / **borrar**.

| Documento | Función | ¿Dueño SSOT? | Veredicto |
| :-- | :-- | :-- | :-- |
| `README.md` | Vitrina (qué hace, instalación, uso rápido, tabla colores HUD, tabla sims, badge) | Sí (§8) | **OK**. Duplicación *gestionada*: la tabla de colores del HUD coexiste con `hud-reference.md` por diseño (§8 la asigna y exige consistencia de vocabulario). |
| `CONTRIBUTING.md` | Estructura del proyecto, entorno dev, convenciones, **el mapa §8 (SSOT + blast-radius)** | Sí (§8 · estructura del proyecto) | **ACTUALIZAR §3.** La "Estructura del proyecto" (líneas 80-87) describe `ui/` **solo como Streamlit** (`app.py`, `step0-4.py`) — quedó obsoleta en v2.0 (no menciona NiceGUI/`ng_*`). Además es el hecho que `engineering/arquitectura.md` duplica y ya divergió (ver §3-B). |
| `PRODUCT_BRIEF.md` | El norte: alcance dentro/fuera, nicho, principios, landscape, §5 los dos productos, §10 drill-down | Sí (§8) | **OK**. Dueño limpio; las `soluciones/` deberían citarlo (hoy lo parafrasean, ver §3-C). |
| `ROADMAP.md` | Estado vivo, camino, gaps técnicos y deuda | Sí (§8) | **OK**. Reorganizado a "Post-v2.0"; ojo: el `backlog.md` apunta a anclas "§Diferido" que ya no existen (ver §3-D). |
| `CHANGELOG.md` | Historial por versión (Keep a Changelog) | Sí (§8) | **ACTUALIZAR (menor).** En `[Unreleased]` hay **dos encabezados `### Corregido`** separados (líneas 42 y 45) — fusionar. Formato, no contenido. |
| `HANDOFF.md` | Relevo efímero (dónde voy, qué falta ahora) | Sí (efímero, ADR 0019) | **ACTUALIZAR (consistencia).** Dice **201 tests** (línea 17); ROADMAP dice **193**; CHANGELOG cita 190. Regla de consistencia de vocabulario §8 (conteos): un solo número vivo. Es efímero por diseño, pero el conteo desincronizado engaña. |
| `docs/guia-usuario.md` | Flujo de usuario punta a punta (CLI + UI) | Sí (§8) | **OK**. Enlaza a `hud-reference` para el detalle del HUD (línea 99) — cesión SSOT ejemplar. |
| `docs/hud-reference.md` | Anatomía y código de colores del HUD | Sí (§8) | **OK**. Dueño limpio; README y capacidades le ceden el detalle. |
| `docs/formato-datos.md` | Modelo canónico, esquema corners JSON, salidas CSV, algoritmo detección | Sí (§8) | **OK**. Dueño limpio; capacidades técnicas le enlazan (ver §2). |
| `docs/glosario.md` | Definición canónica de términos | Sí (§8) | **OK**. Dueño limpio, disciplina "una palabra = una definición" respetada. |
| `docs/flujo-de-trabajo.md` | El sistema de barreras y el flujo explorar→commit→push, desde cero | Sí (§8) | **OK, con solape gestionado.** Doc grande; su §"El casting" y §"Roles que validan" **re-enumeran los roles** que también viven en CONTRIBUTING §8 (ver §3-E). Cruzan enlaces; el traslape es tolerable pero es el candidato #2 a adelgazar. |
| `docs/benchmark-linter.md` | Por qué ruff y no alternativas; cómo se configuró | Sí (§8) | **OK**. Autocontenido, licencias verificadas. |
| `docs/benchmark-ui-framework.md` | Por qué NiceGUI + nicegui-pack + Inno Setup | Sí (§8) | **OK**. Alimenta ADR 0018; por naturaleza comparte contenido con el ADR pero es su dueño declarado (el "cómo se empaqueta"). No es fragmento suelto. |
| `docs/casos-de-uso.md` | Personas × combinaciones × veredicto (rúbrica de gaps/UX) | No (satélite de evaluación) | **OK, borderline.** Se traslapa con `ux-patterns.md` en la evaluación de UX/gaps (C12/C17/C19/C21 aparecen en ambos). Cruzan enlaces y la frontera está declarada (casos-de-uso = insumo; ux-patterns = rúbrica+gate). No consolidar, pero vigilar que no dupliquen hallazgos (ver §3-E). |
| `docs/ux-patterns.md` | Estándar de UX/UI + gate de calidad de interfaz (rúbrica de Mariana) | Sí de facto (heurísticas + gate) | **OK**. Enlaza casos-de-uso y ADR 0012/0014. Su §5 "registro de cambios de patrón" es historial UX — roza el CHANGELOG pero con propósito distinto (contexto del baseline visual). |
| `docs/recursos-del-proyecto.md` | Recursos externos que la sesión no debe preguntar (material de test, cuentas gh, máquinas) | Sí (ADR 0019) | **OK**. Dueño limpio, no duplica. |
| `docs/entorno-windows-powershell51.md` | Recetario de trampas PS 5.1 (encoding, commits, sandbox) | Sí (ADR 0019) | **OK**. Los 5 SKILL.md llevan la versión de 5 líneas y **apuntan aquí** — SSOT respetado. |
| `docs/_diagramas/comparacion.md` | **SCRATCH:** comparar Mermaid vs BPMN para el diagrama del flujo | No (temporal) | **BORRAR.** El propio archivo (líneas 1-9) dice: "Archivo **temporal**… NO es parte de la documentación oficial. Cuando elijas, la ganadora se integra a `flujo-de-trabajo.md` y esta carpeta `_diagramas/` se borra." Ya se recomendó Mermaid (§Resumen). Muerto. |

---

## 2. Tabla de inventario — `product/`, `engineering/`, `templates/`, ADRs, `.claude/`, `qa_runs/`

Esta capa es la **bien gobernada**. Se agrupa por familia; se detallan solo las excepciones.

| Grupo | Función | ¿Dueño SSOT? | Veredicto |
| :-- | :-- | :-- | :-- |
| `product/README.md`, `engineering/README.md` | Índices de las dos capas (QUÉ / CÓMO) | Índice | **OK**. Declaran explícitamente que ceden a `PRODUCT_BRIEF`/`formato-datos`/`hud-reference` y "no duplican". |
| `product/ecosistema/`, `soluciones/`, `dominios/` (9), `modulos/` (14), `procesos/` | Jerarquía funcional navegable (despliega el BRIEF) | Notas de grafo | **OK salvo 3** (ver abajo): el módulo UI-Streamlit y las 2 soluciones. |
| `product/capacidades/` (21) | Unidad atómica con criterios Gherkin | Notas de grafo | **OK**. Spot-check de CMP-01/COR-01/OVL-01/WER-01: **enlazan a su dueño SSOT, no duplican**. OVL-01 es ejemplar ("Definición exacta de los indicadores del HUD → dueño: `docs/hud-reference.md`"); COR-01 cede a ADR 0017. |
| `product/modulos/UI - Interfaz Streamlit.md` | Módulo UI legacy | Nota de grafo | **ACTUALIZAR (obsoleto no marcado).** `estado: vigente` pese a que NiceGUI es la UI principal (v2.0); **no** enlaza a ADR 0010 ni se marca legacy, mientras su gemelo NiceGUI sí enlaza ADR 0018. Ver §3-A. |
| `product/modulos/UI - Interfaz NiceGUI.md` | Módulo UI principal | Nota de grafo | **OK** (copia una frase de "Regla funcional" del de Streamlit — traslape menor, ver §3-A). |
| `product/soluciones/Análisis Post-Tanda.md`, `Overlay de Video.md` | Los dos productos, vistos desde el usuario | Notas de grafo | **CONVERTIR-EN-ENLACE (parcial).** Parafrasean "qué resuelve / qué entrega" de `PRODUCT_BRIEF §5` sin enlazarlo. Ver §3-C. |
| `product/requerimientos/backlog.md` | Bandeja de lo diferido (puntero al dueño) | No (puntero) | **ACTUALIZAR.** 1 ítem muerto ("Front de escritorio custom" ya cumplido por ADR 0018), anclas rotas a "ROADMAP §Diferido", y prosa duplicada del ROADMAP. Ver §3-D. |
| `engineering/arquitectura.md` | Vista del paquete `fantasma/` (core sin deps) | Sí (arquitectura) | **ACTUALIZAR / consolidar.** Duplica el hecho "estructura del paquete" que §8 asigna a CONTRIBUTING §3, y ya **divergió** (arquitectura.md está correcto v2.0; CONTRIBUTING §3 quedó en Streamlit). Ver §3-B. |
| `engineering/pruebas.md` | Estrategia de pruebas (vista navegable) | Vista (cede a ADR 0003) | **OK**. Dice explícitamente "no duplica esa decisión, la enlaza"; cede el "cuándo corre" a `flujo-de-trabajo` y el conteo a HANDOFF/ROADMAP. Consolidación correcta. |
| `engineering/componentes/` (ffmpeg, motec-i2, nicegui, streamlit) | Sistemas/servicios que sostienen capacidades | Notas de grafo | **OK salvo streamlit.md:** cuerpo marca "legacy" correctamente y enlaza a `[[nicegui]]`, pero el frontmatter dice `estado: vigente` (debería `obsoleto`/`deprecado`). Inconsistencia menor. |
| `engineering/especificaciones/` (4), `modelos-de-datos/` (2) | Implementación concreta / estructuras | Notas de grafo | **OK**. Enlazan a `formato-datos` como dueño. |
| `templates/` (README + 12) | Moldes canónicos de cada tipo de nota | Sí (§8) | **OK**. Dueño limpio; capa *reference* de Diátaxis. |
| `docs/decisions/` (README + plantilla + 0001-0019) | El porqué de cada decisión + índice | Sí (§8) | **OK**. Un ADR por decisión, índice al día, superseciones enlazadas (0010→0018, 0001→0008). Sano. |
| `.claude/commands/arranca.md`, `skills/*` (5) | Método de sesión + asientos (skills) | Comportamiento | **OK**. Los SKILL.md llevan versión corta y apuntan a los docs dueños (entorno-ps51, flujo-de-trabajo). |
| `qa_runs/README.md` | Convención de evidencia de QA | Sí (ADR 0019) | **OK**. |
| `qa_runs/2026-07-03-auditoria-integral/fase1-cli.md`, `fase1-ui.md` | Salidas de esta auditoría (fase 1) | Evidencia | **OK** (artefactos de la auditoría en curso). |

---

## 3. Pares/grupos con traslape real (las secciones que se pisan)

### A. `UI - Interfaz Streamlit.md` (módulo) — obsoleto sin marcar + traslape con NiceGUI  ★ el más engañoso
- **Frontmatter `estado: vigente`** pese a que v2.0 hizo a Streamlit legacy (CHANGELOG `[Unreleased]`:
  "nuevo frontend… que **sustituye a Streamlit como UI principal**"; ADR 0018).
- Declara **el mismo propósito, las mismas 3 capacidades** (UI-01/02/03) y **las mismas 11
  dependencias** que el módulo NiceGUI. La "Regla funcional" es casi textual entre ambos.
- **No** enlaza a ADR 0010 ni dice "legacy" — mientras su gemelo `engineering/componentes/streamlit.md`
  sí lo dice en el cuerpo. Asimetría: dos notas del mismo componente, una avisa que es legacy y la otra no.
- **Riesgo:** una sesión futura lee "UI-Streamlit vigente" y trata la UI legacy como activa.

### B. `engineering/arquitectura.md` ↔ `CONTRIBUTING.md §3` — estructura del paquete duplicada y divergida
- Ambos pintan el árbol de `fantasma/`. **§8 declara a CONTRIBUTING dueño de "Estructura del proyecto".**
- CONTRIBUTING §3 (líneas 80-87): `ui/` = "interfaz **Streamlit** — app.py (router), step0-4.py…" — **sin NiceGUI**.
- `arquitectura.md` (líneas ~34-61): versión completa y correcta v2.0 (NiceGUI principal + Streamlit legacy, `ng_app.py`…`ng_step0-4.py`).
- Es el **caso de libro del dolor del PO**: el mismo hecho en dos dueños, y ya divergieron. El SSOT
  declarado (§3) es el que quedó obsoleto.

### C. `product/soluciones/{Análisis Post-Tanda, Overlay de Video}` ↔ `PRODUCT_BRIEF §5`
- Parafrasean el mismo contenido sin enlazar al dueño (§8 asigna alcance/productos al BRIEF):
  - Análisis Post-Tanda: "el piloto quiere saber **dónde perdió tiempo y qué hizo diferente**… del
    CSV al insight en **menos de cinco minutos**" ≈ BRIEF §5 (líneas 68/79) casi idéntico. La lista
    "Qué entrega" (reporte MD, gráficas ghost, diagrama G-G, mapa de delta, tabla de curvas) reproduce la del BRIEF.
  - Overlay de Video: reformula "los datos solos no bastan… ver la frenada mientras ves el video" y
    repite "qué entrega" (webm alfa, compose ffmpeg NVENC, auto-sync).
- Paráfrasis, no copy-paste literal — pero es **el mismo hecho contado dos veces sin puntero**.

### D. `product/requerimientos/backlog.md` ↔ `ROADMAP.md`
- **Ítem muerto:** "Front de escritorio custom (v2.0)" (líneas 15-17) describe "evaluar migrar de
  Streamlit a Tauri/pywebview/Electron… no es una migración decidida". **Ya ocurrió** (NiceGUI/pywebview,
  ADR 0018). Cerrar/marcar resuelto.
- **Anclas rotas:** casi todos los ítems apuntan a "`ROADMAP §Diferido — X`", pero el ROADMAP se
  reorganizó a "**Post-v2.0**" y ya no tiene esa sección/anclas.
- **Prosa duplicada:** "Histórico entre sesiones", "Nuevos importadores", "fantasma-live", "Lista de
  vueltas" repiten la **descripción** del ROADMAP, no solo el puntero (roza la propia regla de la línea 9
  del backlog: "No duplicar el contenido de esos documentos").

### E. `flujo-de-trabajo.md` §"El casting/Roles" ↔ `CONTRIBUTING.md §8` "Roles que validan"  (y `casos-de-uso` ↔ `ux-patterns`)
- Ambos enumeran los asientos (Mau, Ahiram, Armando, Charbel, Mariana, Escribano, Reviewer, PO).
  Cruzan enlaces y §8 dice "quién los ocupa, en flujo-de-trabajo §4", así que es **traslape gestionado**,
  pero flujo-de-trabajo es un doc muy grande que repite el router. Adelgazable a mediano plazo, no urgente.
- `casos-de-uso.md` y `ux-patterns.md` comparten los hallazgos UX (C12/C17/C19/C21). Frontera declarada
  (insumo vs rúbrica+gate); vigilar que no dupliquen los mismos hallazgos al crecer.

---

## 4. Documentos muertos / obsoletos (resumen)

| Documento | Estado | Acción |
| :-- | :-- | :-- |
| `docs/_diagramas/comparacion.md` (+ carpeta `_diagramas/`) | **Muerto** — scratch marcado para borrar, decisión ya tomada | **Borrar** |
| `product/modulos/UI - Interfaz Streamlit.md` | Obsoleto no marcado (`vigente`) | Marcar `obsoleto` + nota de superseción |
| `engineering/componentes/streamlit.md` | Frontmatter `vigente` vs cuerpo "legacy" | Alinear frontmatter a `obsoleto` |
| backlog · ítem "Front de escritorio custom" | Cumplido por ADR 0018 | Cerrar/marcar resuelto |
| `CONTRIBUTING.md §3` (estructura `ui/`) | Obsoleto (solo Streamlit) | Actualizar o enlazar a arquitectura.md |

No hay masa de borradores `en_definicion` abandonados: solo los índices `product/README` y
`engineering/README` están `en_definicion` (migración gradual, ADR 0015 — aceptable).

---

## 5. Propuesta de consolidación priorizada

### P1 — Cerrar la transición Streamlit→NiceGUI en la capa de notas  *(alto valor, bajo esfuerzo)*
Un solo cambio coherente elimina la duplicación más engañosa:
- `product/modulos/UI - Interfaz Streamlit.md` → `estado: obsoleto`/`deprecado` + nota "superseded by
  NiceGUI (ADR 0018)" + enlace a ADR 0010.
- `engineering/componentes/streamlit.md` → alinear frontmatter a `obsoleto`.
- Backlog → cerrar el ítem "Front de escritorio custom".
Resultado: nadie vuelve a leer "UI Streamlit vigente" como si fuera la UI activa.

### P2 — Un solo dueño para "estructura del paquete"  *(cierra el caso de libro del PO)*
Actualizar `CONTRIBUTING §3` a v2.0 (mencionar NiceGUI `ng_*` + Streamlit legacy) **o** —mejor por
SSOT— reducir §3 a un puntero: "estructura detallada en `engineering/arquitectura.md`". Elimina la
duplicación divergente. (Nota: §8 asigna el hecho a CONTRIBUTING; si se decide que el dueño real es
arquitectura.md, actualizar también la fila de §8.)

### P3 — `soluciones/` enlazan a `PRODUCT_BRIEF §5`, no lo reenuncian  *(satélite → enlace)*
Reemplazar el "qué resuelve / qué entrega" parafraseado por un enlace a `PRODUCT_BRIEF §5`, dejando en
la nota solo lo que la jerarquía aporta (wikilinks a dominios/módulos, no la narrativa del producto).

### P4 — Sanear `backlog.md` como puntero puro  *(repara enlaces + reduce prosa)*
Reparar las anclas "`ROADMAP §Diferido`" (ahora "Post-v2.0"), recortar la descripción en prosa a
1 línea + puntero (honra su propia regla de la línea 9), y quitar el ítem cumplido.

### P5 — Borrar `docs/_diagramas/`  *(muerto)*
Integrar el Mermaid ganador en `flujo-de-trabajo.md` (si no está ya) y borrar la carpeta scratch,
como el propio archivo instruye.

### Menores (barrer de paso)
- `CHANGELOG [Unreleased]`: fusionar los dos `### Corregido`.
- `HANDOFF`/`ROADMAP`/`CHANGELOG`: un solo conteo de tests vivo (hoy 201 / 193 / 190).
- Mediano plazo: adelgazar el solape del "casting de roles" entre `flujo-de-trabajo.md` y `CONTRIBUTING §8`.

---

*Diagnóstico producido sin modificar el repo. Ejecutar las acciones es decisión del PO;
las de `product/`+`engineering/` las verificará `auditar.ps1` al cerrar el cambio.*
