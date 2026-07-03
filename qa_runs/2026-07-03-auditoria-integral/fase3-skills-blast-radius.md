# Fase 3 — Auditoría: Skills + Manifiesto blast-radius

**Fecha:** 2026-07-03
**Rama:** codex/sgi-v2-merge
**Scope:** `.claude/skills/*/SKILL.md` (ahiram, armando, charbel, escribano, mariana) + `.claude/commands/arranca.md` vs `docs/flujo-de-trabajo.md §4` + `CONTRIBUTING.md §8` + `tools/blast-radius.json`

---

## Veredicto

**Sistema funcional con brechas ejecutables reales:** 2 falsos positivos estructurales en el manifiesto (viz y core todo-o-nada), 5 filas de CONTRIBUTING §8 sin área ejecutable en el JSON, y 2 skills con referencias activas a Streamlit que guían mal post-migración v2 a NiceGUI.

---

## Conteo por severidad

| Severidad | Conteo |
|-----------|--------|
| CRÍTICO | 2 |
| ALTO | 5 |
| MEDIO | 4 |
| BAJO | 2 |
| **Total** | **13** |

---

## Los 3 hallazgos más graves

1. **[CRÍTICO] blast-radius "viz" bloquea hud-reference.md para TODO cambio en `fantasma/viz/*` sin granularidad visual/no-visual:** un refactor de rendimiento puro (caso vivido hoy en `overlay.py`) exige editar un doc irrelevante o hacer `--no-verify` — el bloqueo es estructuralmente falso para cambios internos. Propuesta concreta al final.

2. **[CRÍTICO] 5 filas de CONTRIBUTING §8 no tienen área ejecutable en blast-radius.json:** pyproject.toml (deps), PRODUCT_BRIEF.md (alcance), docs/glosario.md (vocabulario), release bump y decisiones de arquitectura no disparan ningún gate — el "espejo ejecutable" prometido tiene brechas materiales.

3. **[ALTO] Ahiram SKILL.md tiene consejo Streamlit activo desfasado post-v2:** línea 39 advierte que "`st.download_button` no es accesible desde `AppTest` en Streamlit 1.58.0" — un agente Ahiram que lee esto redactará tests basados en AppTest que ya no aplican al NiceGUI v2.0. Puede generar tests incorrectos y silenciosamente nunca ejecutarlos.

---

## Parte 1 — Auditoría de skills

### 1.1 Inventario

| Skill | Archivo | Existe |
|-------|---------|--------|
| ahiram | `.claude/skills/ahiram/SKILL.md` | sí |
| armando | `.claude/skills/armando/SKILL.md` | sí |
| charbel | `.claude/skills/charbel/SKILL.md` | sí |
| escribano | `.claude/skills/escribano/SKILL.md` | sí |
| mariana | `.claude/skills/mariana/SKILL.md` | sí |
| arranca | `.claude/commands/arranca.md` | sí — es un **slash command** de sesión, no un SKILL.md |

`arranca` no vive en `.claude/skills/` sino en `.claude/commands/`. Es el comando de inicio de Mau; no es un asiento ni tiene ambigüedad funcional. La confusión es solo de nombre: el sistema de skills lo presenta como "skill" en la lista del harness, pero su rol es activar la sesión (Mau), no operar un asiento. No hay SKILL.md de arranca porque Mau **es** la sesión, como lo indica flujo-de-trabajo.md §4. Correcto en diseño; ambiguo en nomenclatura.

### 1.2 Límites: ¿claros y mutuamente excluyentes?

#### Ahiram vs otros asientos

Ahiram implementa código en `fantasma/`; los demás validan o documentan. Los límites están escritos y son claros:

- vs Charbel: Ahiram escribe; Charbel valida datos/telemetría. Separación limpia.
- vs Mariana: Ahiram escribe `viz/`; Mariana hace QA visual. Separación limpia.
- vs Escribano: Ahiram entrega código limpio; Escribano sincroniza docs. Separación limpia.
- vs Armando: Ahiram no toca `product/`, `engineering/`, `docs/decisions/`, `CHANGELOG.md`, `CONTRIBUTING.md`. Explícito.

**Omisión menor:** Ahiram no dice explícitamente "no toques `.claude/skills/`". La fuente de ese área es "orquestacion" (rol Armando en blast-radius). No crea ambigüedad práctica, pero debería estar en el "No hace".

#### Armando vs Escribano

La distinción más sutil. Armando SKILL.md la resuelve explícitamente: "el Escribano cierra el desfase código→doc dueño de la §8 (reactivo a un diff de código). Armando diseña y mantiene el grafo de product/+engineering/ y redacta los ADRs." Y define el punto de cruce: "el Escribano señala el hueco y Armando lo llena." Límite claro y bien documentado.

#### Charbel vs Mariana

- Charbel: `core/` e `importers/` — "No toca `fantasma/viz/` ni `fantasma/ui/`."
- Mariana: `viz/` y `ui/` — "No toca `fantasma/core/` ni `fantasma/importers/`."

**Overlap superficial (MEDIO):** Charbel tarea 3 dice "Snapshot de imagen del HUD — genera o compara el snapshot de imagen del HUD". Mariana tarea 3 dice "Surtir capturas al PO". Ambos generan imágenes del HUD. La distinción conceptual es correcta (Charbel: correctitud del output; Mariana: juicio visual), pero en la práctica puede confundir quién genera el artefacto. La SKILL.md de Charbel llama "a prueba de migración" a su snapshot porque verifica el output, no el front; esto es coherente con ADR 0010 pero choca con el rol de Mariana como dueña de lo visual. Recomendable clarificar que el "snapshot de Charbel" es verificación de datos (¿los números son correctos?), no de UX.

#### ¿Ahiram pisa terreno de otro asiento?

No materialmente. Ahiram es el asiento de implementación; cubre todo `fantasma/` porque es el único desarrollador del motor. Los demás asientos son de validación o documentación. El blast-radius correctamente asigna el área "core" a Charbel (validación) y "viz/ui" a Mariana (QA visual), no la autoría de código.

### 1.3 Coincidencia con flujo-de-trabajo.md §4 y CONTRIBUTING.md §8

La tabla del casting en §4 lista: Mau, Ahiram, Armando, Charbel, Mariana, Escribano, Reviewer, Oscar.

- Todos los asientos con SKILL.md tienen skill (ahiram, armando, charbel, mariana, escribano). ✓
- Reviewer es `/code-review` (skill de sesión, no SKILL.md). ✓
- Oscar es agente de plataforma global, no vive en el repo. ✓
- Mau es la sesión principal; no tiene SKILL.md por diseño. ✓

La tabla §8 de roles validadores lista: Reviewer, Escribano (base), Charbel, Mariana, Armando, PO. Los skills están alineados con estos roles.

**Desalineación menor:** El mapa §9 de flujo-de-trabajo.md lista `.claude/skills/` como "escribano, armando (arquitecto), charbel, mariana" — no menciona ahiram (skill nuevo). Desactualización de documentación interna.

### 1.4 Referencias desfasadas post-migración v2

#### [CRÍTICO activo] Ahiram SKILL.md línea 39

```
**`st.download_button` no es accesible desde `AppTest`** en Streamlit 1.58.0 — solo
`at.button`, `at.button_group`, `at.menu_button`. Verificar que los tests usen lo que
existe.
```

El blast-radius.json área "ui" declara: "interfaz NiceGUI v2.0 y legacy Streamlit: ng_app.py, ng_step0-4.py, ng_helpers.py, ng_state.py, app.py, step0-4.py". La UI v2.0 usa NiceGUI; AppTest es el framework de testing de Streamlit, no de NiceGUI. Un agente Ahiram que recibe una tarea de test de UI en v2.0 y sigue este consejo escribirá tests AppTest que no aplican a NiceGUI y probablemente no se ejecutarán en CI.

**Acción recomendada:** Reemplazar el consejo Streamlit/AppTest por la estrategia de test para NiceGUI v2.0 (o eliminarlo y dejar que el ADR 0010 y la suite existente guíen).

#### [ALTO] Mariana SKILL.md línea 21

```
**Playwright para smoke visual acotado de la UI Streamlit** (ADR 0012)
```

Referencia explícita a "UI Streamlit" cuando v2.0 usa NiceGUI. El smoke visual debería apuntar al nuevo framework. ADR 0012 puede necesitar una enmienda (o uno nuevo) para NiceGUI.

#### [MEDIO] Charbel SKILL.md línea 21

```
**AppTest para la lógica de flujo 0 a 4**
```

AppTest es Streamlit. Con NiceGUI v2.0, este item de Charbel queda sin soporte de framework. La ADR 0010 "tests a prueba de migración" intentaba aislar esto, pero el texto de la SKILL sigue nombrando la tecnología Streamlit.

### 1.5 Escribano — referencia inexistente

**[ALTO]** Escribano SKILL.md línea 38:

```
No toma decisiones de arquitectura → eso es un ADR (skill `adr-helper`).
```

No existe `.claude/skills/adr-helper/SKILL.md`. Existe un skill global `adr-helper` en el harness de Claude Code (para cualquier repo), pero **no es un asiento de SimGhostInputs**. El asiento de ADRs es **Armando**. El texto correcto sería "→ señálalo al PO para que Armando lo redacte (skill `armando`)." Un agente Escribano que busque invocar `adr-helper` como asiento del repo no lo encontrará en `.claude/skills/`.

---

## Parte 2 — Manifiesto blast-radius.json vs CONTRIBUTING §8

### 2.1 Espejo por filas

| Fila CONTRIBUTING §8 | Área JSON | Veredicto |
|---|---|---|
| Flag/comando CLI nuevo | `cli` | PARCIAL: falta `docs/formato-datos.md` condicional |
| Cambio visual HUD/overlay | `viz` | PARCIAL: falta `README.md` (tabla colores); ADR excluido (juicio, aceptable) |
| Cambio UX/layout UI Streamlit | `ui` | OK — doc_bloquea, doc_avisa y product_avisa coinciden |
| Cambio en `core/` | `core` | OK — aunque `doc_avisa: []` omite "tests/ si cambian números" (no es un doc, aceptable) |
| Dependencia o extra nuevo | **SIN ÁREA** | BRECHA: pyproject.toml sin gate ejecutable |
| Importador o formato nuevo/mod | `importers` | PARCIAL: `doc_bloquea: []` — un cambio de canales no bloquea (permisivo) |
| Cambio de alcance o principio | **SIN ÁREA** | BRECHA: PRODUCT_BRIEF.md sin gate |
| Release / bump de versión | **SIN ÁREA** | BRECHA: sin área "release" |
| Decisión de arquitectura/diseño | **SIN ÁREA** | BRECHA: docs/decisions/ no gateada (auditar.ps1 lo cubre parcialmente, aceptable) |
| Término o concepto nuevo | **SIN ÁREA** | BRECHA: docs/glosario.md sin gate |
| Cambio en barreras/gobernanza | `barreras` | OK con nota: CONTRIBUTING dice "PO/Armando", JSON dice solo "Armando" |
| Capacidad/dominio/módulo nuevo | via product_avisa por área | OK — no es fila propia, se cubre distribuido |
| Archivo nuevo en raíz | `raiz` | OK |

**Áreas en JSON sin fila en CONTRIBUTING:** `orquestacion`, `setup`. Adiciones correctas del manifiesto, no discrepancias.

### 2.2 Discrepancias detalladas

#### [CRÍTICO] Área "viz" — todo-o-nada, sin granularidad

```json
"doc_bloquea": ["docs/hud-reference.md"]
```

Cualquier cambio en `fantasma/viz/*` — incluyendo refactors de rendimiento, mejoras de memoria, optimizaciones internas — dispara el bloqueo de `hud-reference.md`. El doc-gate no puede preguntar "¿cambió algo visual?"; solo sabe que se tocó `viz/`.

**Caso vivido hoy:** cambio de rendimiento en `fantasma/viz/overlay.py` sin modificación visual → push bloqueado hasta editar hud-reference.md (doc irrelevante).

**¿El manifiesto permite granularidad?** No. La arquitectura actual es todo-o-nada por área. No hay sub-patrones ni condiciones.

**¿Otras áreas con el mismo riesgo?**

- **`core/`**: Un refactor de rendimiento en normalización o comparación (mismo algoritmo, más rápido) bloquea por `docs/formato-datos.md` aunque el algoritmo y sus outputs sean idénticos.
- **`ui/`**: Un cambio de estilo interno (CSS, restructuración de código sin cambio de flujo) bloquea por `docs/guia-usuario.md` aunque el usuario no vea diferencia.
- **`importers/`**: No tiene `doc_bloquea`, pero doc_avisa dispara para cualquier cambio aunque sea solo refactor interno.

**Propuesta concreta y mínima para reducir el falso positivo sin abrir huecos:**

Para la área `viz`: mover `docs/hud-reference.md` de `doc_bloquea` a `doc_avisa`, y agregar un campo `mensaje` que indique cuándo es obligatorio actualizar. El gate deja de bloquear el push pero sigue avisando. El Escribano (que dispara por hook) puede evaluar si el aviso aplica.

```json
{
  "nombre": "viz",
  "doc_bloquea": [],
  "doc_avisa": ["docs/hud-reference.md", "docs/ux-patterns.md"],
  "mensaje": "Actualiza hud-reference.md SOLO si cambió algo visual (HUD color, panel, layout, dato mostrado). Refactors internos sin impacto visual no requieren editar el doc aunque el aviso aparezca."
}
```

**¿Abre huecos?** Ninguno. El aviso sigue presente; el Escribano lo ve en su corrida. Un cambio visual real que omita hud-reference.md queda en `doc_avisa` (avisa local) y en el job `audit` de CI (`auditar-radius.ps1` sobre el rango del PR). La barrera dura del CI permanece. Lo que se elimina es el bloqueo local en pushes de refactors.

El mismo tratamiento puede aplicarse a `core/` en el futuro: mover `docs/formato-datos.md` a `doc_avisa` con `mensaje`. No se hace aquí para no ampliar el cambio sin vivir el caso.

#### [CRÍTICO] 5 filas de CONTRIBUTING §8 sin área ejecutable

**1. "Dependencia o extra nuevo" (pyproject.toml, README, §3, setup.ps1)**

El área `setup` cubre solo `setup.ps1`. Un cambio en `pyproject.toml` — agregar una dependencia, cambiar un extra, actualizar una versión de dep — no dispara ningún área del manifiesto. Es un hueco real: `pyproject.toml` es el fichero más crítico del ciclo de release y no tiene gate.

**2. "Release / bump de versión" (pyproject.toml, CHANGELOG, ROADMAP, README, tag)**

Sin área "release". Un bump de versión toca `pyproject.toml`, `CHANGELOG.md`, `ROADMAP.md`, `README.md`. Ninguno de estos archivos está en `fuente` de ningún área (son destino, no fuente). El gate solo dispara cuando se toca el *código* de un área; el ritual de release no toca código de `fantasma/`. El hueco es sistémico: el release no está mapeado.

**3. "Cambio de alcance o principio de diseño" (PRODUCT_BRIEF.md, ROADMAP)**

`PRODUCT_BRIEF.md` no aparece en ninguna `fuente` ni en ningún `doc_avisa/doc_bloquea` del JSON. Hueco.

**4. "Decisión de arquitectura/diseño" (ADR nuevo + README.md de decisions)**

`docs/decisions/` no tiene área dedicada en el JSON. Se acepta como parcialmente cubierto porque `auditar.ps1` verifica la integridad del grafo de docs (frontmatter, wikilinks, criterios), no el blast-radius. Un ADR nuevo es judgment (Armando+PO) y se registra en el CHANGELOG. No es un hueco operacional grave, pero sí una discrepancia documental: CONTRIBUTING §8 promete que el JSON es el "espejo ejecutable" de la tabla, y esta fila no tiene espejo.

**5. "Término o concepto nuevo" (docs/glosario.md)**

`docs/glosario.md` no está en ningún `doc_avisa` ni `doc_bloquea`. CONTRIBUTING la enruta a "solo Reviewer" (que revisa todo cambio de código), así que el hueco es menor en práctica. Pero no es ejecutable por el gate.

#### [ALTO] Área "viz" falta README.md en doc_avisa

CONTRIBUTING §8 fila "Cambio visual del HUD/overlay":

> `hud-reference` · `README` (tabla de colores) · `ux-patterns.md` · ADR nuevo + README.md de decisions

blast-radius.json área "viz":
- `doc_bloquea`: `["docs/hud-reference.md"]`
- `doc_avisa`: `["docs/ux-patterns.md"]`

Falta `README.md` (tabla de colores del HUD). Si se cambia un color del HUD y no se actualiza la tabla del README, el gate no avisa sobre esa omisión. La tabla de colores del README es la referencia pública visible del producto.

#### [MEDIO] Rol desalineado en área "barreras"

CONTRIBUTING §8: "PO / Armando"
blast-radius.json: `"rol": "Armando"`

El PO (el humano) debería estar co-listado para cambios en las barreras o la gobernanza. No es grave porque el PO siempre es la última instancia, pero la desalineación existe.

#### [MEDIO] Área "importers" — permisividad en canales

`doc_bloquea: []`. Un cambio en `fantasma/importers/` que modifique los canales de salida (qué campos se parsean, qué columnas se exponen) debería bloquear `docs/formato-datos.md` porque ese doc es el SSOT del modelo de datos. Actualmente solo avisa. Dado que el rol de Charbel es validar telemetría, y que los tests deterministas deberían capturar cambios de canales, el riesgo es real pero mitigado. Aun así es una inconsistencia: `core/` bloquea por `formato-datos.md` y `importers/` no, aunque ambos producen datos que ese doc describe.

#### [BAJO] Área "cli" — condicional no expresable

CONTRIBUTING §8: "formato-datos si cambian las salidas". blast-radius.json área "cli" no incluye `docs/formato-datos.md` en `doc_avisa`. El JSON no tiene mecanismo para condiciones ("si X"). En la práctica, si el CLI cambia las salidas probablemente también toca `core/`, que sí gatea `formato-datos.md`. Hueco teórico, mitigado en práctica.

### 2.3 Resumen de discrepancias

| Tipo | Conteo | Descripción |
|------|--------|-------------|
| Área no ejecutable (en §8 pero no en JSON) | 5 | deps, release, alcance, glosario, decisiones |
| Doc faltante en área (JSON incompleto vs §8) | 2 | README.md en viz; formato-datos.md en importers |
| Rol desalineado | 1 | "PO/Armando" vs solo "Armando" en barreras |
| Falso positivo estructural | 2 | viz y core all-or-nothing (viz es el caso vivido) |
| Condicional no expresable | 1 | cli no puede decir "solo si cambian salidas" |

---

## Recomendaciones priorizadas

### P0 (bloqueo inmediato — caso vivido)

1. **Mover `docs/hud-reference.md` de `doc_bloquea` a `doc_avisa` en área "viz"** y agregar `mensaje` describiendo cuándo actualizar. Elimina el falso positivo hoy mismo sin abrir huecos.

### P1 (coherencia con la promesa del espejo ejecutable)

2. **Agregar área "deps"** en blast-radius.json: `fuente: ["pyproject.toml"]`, `doc_avisa: ["README.md", "CONTRIBUTING.md"]`, `rol: "Reviewer"`. Cubre la brecha más práctica de las 5.

3. **Agregar `README.md` a `doc_avisa` del área "viz"** para que el gate avise sobre la tabla de colores del HUD.

### P2 (skills desfasados — riesgo en sesiones con subagentes)

4. **Ahiram SKILL.md línea 39**: reemplazar el consejo AppTest/Streamlit por la estrategia de test para NiceGUI v2.0 (o eliminarlo, dejando la orientación en los tests existentes).

5. **Mariana SKILL.md línea 21**: reemplazar "UI Streamlit" por "UI NiceGUI v2.0" y citar el ADR 0012 o su enmienda para NiceGUI.

6. **Escribano SKILL.md línea 38**: reemplazar "(skill `adr-helper`)" por "(skill `armando`)".

### P3 (refinamientos menores)

7. Actualizar el mapa §9 de flujo-de-trabajo.md para incluir ahiram en la lista de skills.
8. Aclarar en Charbel SKILL.md que la tarea AppTest ya no aplica a NiceGUI v2.0.
9. Clarificar en Charbel y Mariana quién genera el artefacto de snapshot del HUD (hoy ambos describen la acción con diferente propósito pero sin handoff claro).

---

## Archivos fuente analizados

- `C:\Repositorio personal\SimGhostInputs\.claude\skills\ahiram\SKILL.md`
- `C:\Repositorio personal\SimGhostInputs\.claude\skills\armando\SKILL.md`
- `C:\Repositorio personal\SimGhostInputs\.claude\skills\charbel\SKILL.md`
- `C:\Repositorio personal\SimGhostInputs\.claude\skills\escribano\SKILL.md`
- `C:\Repositorio personal\SimGhostInputs\.claude\skills\mariana\SKILL.md`
- `C:\Repositorio personal\SimGhostInputs\.claude\commands\arranca.md`
- `C:\Repositorio personal\SimGhostInputs\docs\flujo-de-trabajo.md`
- `C:\Repositorio personal\SimGhostInputs\CONTRIBUTING.md`
- `C:\Repositorio personal\SimGhostInputs\tools\blast-radius.json`
