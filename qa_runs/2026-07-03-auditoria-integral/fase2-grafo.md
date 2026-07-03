---
tipo: auditoria
fase: 2 - juicio del grafo
auditor: agente general (claude-sonnet-4-6)
fecha: 2026-07-03
alcance: product/ + engineering/ (jerarquia, criterios, tests, DRY, arquitectura)
---

# Fase 2 — Juicio del grafo de documentacion funcional

> El gate determinista (`tools/auditar.ps1`) ya corre en paralelo por otro agente.
> Esta fase aplica el juicio que el gate no puede dar: calidad, veracidad y coherencia
> con el codigo real (v2.0 NiceGUI, render paralelo, empaquetado).

---

## Veredicto ejecutivo

**El grafo describe correctamente la mayoria del producto v2.0, pero tiene tres puntos de quiebre
graves: (1) el backlog lista como diferido lo que ya existe y es vigente; (2) dos documentos
de engineering describen el backend de estado NiceGUI con el storage incorrecto; (3) las secciones
de verificacion NiceGUI de UI-02 y UI-03 citan tests que no cubren los criterios reclamados.**
El resto de la jerarquia (nucleo, importadores, overlay, sync, pace notes) esta solida y los
criterios Gherkin del core son reales y verificables.

---

## Conteo por severidad

| Severidad | Hallazgos |
|-----------|-----------|
| GRAVE     | 3         |
| MEDIO     | 3         |
| BAJO      | 2         |
| **Total** | **8**     |

---

## Los 3 hallazgos mas graves

**GRAVE-1 — backlog.md lista como diferidos tres entregables ya implementados y vigentes.**
`product/requerimientos/backlog.md` sigue declarando como "post-v1.0 diferido" el front de
escritorio custom (NiceGUI, ya en `fantasma/ui/ng_*.py`), el coaching de voz/pace notes (modulo
PAC, capacidades PAC-01 y PAC-02 vigentes, tests en `tests/viz/test_pacenotes.py`) y el
drill-down por curva (capacidad UI-03 vigente). Cualquier agente que lea el backlog antes de
implementar estos modulos los construira por segunda vez o introducira colision.

**GRAVE-2 — engineering/ describe el storage de AppState con el backend incorrecto.**
`engineering/arquitectura.md` linea 56 y `engineering/componentes/nicegui.md` lineas 17, 22-23
dicen `app.storage.client`. El codigo real (`fantasma/ui/ng_state.py` — verificado) usa
`app.storage.user`. La distincion es semanticamente relevante: `storage.client` es per-tab
(no persiste entre tabs del mismo browser); `storage.user` es per-user-session. Un agente que
construya sobre la spec escrita montara el estado sobre el backend equivocado.

**GRAVE-3 — UI-02 y UI-03 citan tests NiceGUI que no cubren los criterios declarados.**
`UI-02` (avisos del motor) afirma en su seccion de Verificacion: "`tests/ui/test_ng_step4.py` —
aviso de ffmpeg ausente en el Paso 4 NiceGUI". El archivo tiene exactamente dos tests:
`test_step4_heading_visible` y `test_step4_renders_without_crash`; ninguno afirma que aparece el
mensaje de error de ffmpeg. Del mismo modo, `UI-03` (drill-down) afirma cobertura en
`tests/ui/test_ng_step2.py` para "seleccion por mayor perdida y omision de canales ausentes";
ese archivo solo tiene `test_step2_heading_visible` y `test_step2_guard_without_data`. Las
citaciones de verificacion son falsas: el gate las marca como presentes, pero el comportamiento
critico de cada capacidad no esta testeado.

---

## Hallazgos completos

### GRAVE-1: backlog.md — tres entregables vigentes listados como diferidos

**Archivo:** `product/requerimientos/backlog.md`

El documento dice al inicio "bandeja de entrada de lo diferido: requerimientos que se retomaran
despues de declarar estable la v1.0". Pero lista tres items que ya estan entregados en v2.0:

| Item del backlog | Estado real | Evidencia en codigo |
|------------------|-------------|---------------------|
| Front de escritorio custom (v2.0) | Implementado — NiceGUI principal | `fantasma/ui/ng_app.py`, `ng_step0-4.py`, modulo `UI - Interfaz NiceGUI.md` vigente |
| Coaching de voz — CrewChief Pace Notes | Implementado | `fantasma/viz/pacenotes.py`, capacidades PAC-01 y PAC-02 vigentes |
| Drill-down por curva | Implementado | `fantasma/ui/ng_step2.py` `_render_corner_detail`, capacidad UI-03 vigente |

El backlog tambien lista "Historico entre sesiones", "Nuevos importadores" y "fantasma-live" que
siguen sin implementar — esos son correctos. Solo los tres primeros son falsos positivos.

**Impacto:** Un agente que lea el backlog para planificar trabajo pensara que estos tres modulos
no existen. Riesgo de implementacion duplicada o colision de nombres.

**Correccion recomendada:** Eliminar los tres items ya entregados del backlog o moverlos a una
seccion "Entregado en v2.0" con un puntero al modulo correspondiente.

---

### GRAVE-2: engineering/ — storage backend de AppState incorrecto en dos documentos

**Archivos:**
- `engineering/arquitectura.md` — linea 56: `ng_state.py    AppState proxy sobre app.storage.client`
- `engineering/componentes/nicegui.md` — lineas 17, 22, 23: `app.storage.client` (x3)

**Realidad en codigo** (`fantasma/ui/ng_state.py`, verficado):
```python
# Cada propiedad lee/escribe en app.storage.user
return _ng_app.storage.user.get(key, default)
_ng_app.storage.user[key] = value
```

Los documentos de producto (correcto): `product/modulos/UI - Interfaz NiceGUI.md` y
`product/capacidades/UI-01` dicen correctamente `app.storage.user`. La incoherencia es solo
en engineering/.

**Impacto:** Un agente de infraestructura o un desarrollador que lea `engineering/` para extender
el estado de sesion usara el backend incorrecto. `storage.client` esta disponible en NiceGUI pero
tiene semantica diferente (per-WebSocket/tab vs per-user-session).

---

### GRAVE-3: UI-02 y UI-03 — citaciones de tests NiceGUI que no cubren los criterios

**Archivo UI-02:** `product/capacidades/UI-02 - Avisos del motor visibles en la UI.md`

Criterio declarado: "Dado que el usuario usa la interfaz NiceGUI y ffmpeg no esta instalado,
cuando navega al Paso 4, entonces aparece un mensaje de error que menciona 'ffmpeg' con el
comando de instalacion de su plataforma."

Verificacion declarada: "`tests/ui/test_ng_step4.py` — aviso de ffmpeg ausente en el Paso 4
NiceGUI."

Tests reales en `tests/ui/test_ng_step4.py`:
- `test_step4_heading_visible` — afirma `await user.should_see("Paso 4")`
- `test_step4_renders_without_crash` — afirma `await user.should_see("Componer")`

Ninguno afirma que aparece el aviso de ffmpeg. El archivo menciona ffmpeg solo en comentarios.

**Archivo UI-03:** `product/capacidades/UI-03 - Drill-down por curva.md`

Criterio declarado: "Dado que el usuario usa la interfaz NiceGUI y hay varias curvas con perdidas
distintas, cuando se renderiza el drill-down del Paso 2, entonces el selector ordena por
`time_lost` descendente y muestra por defecto la de mayor perdida."

Verificacion declarada: "`tests/ui/test_ng_step2.py` — drill-down por curva NiceGUI: seleccion
por mayor perdida y omision de canales ausentes."

Tests reales en `tests/ui/test_ng_step2.py`:
- `test_step2_heading_visible` — afirma `await user.should_see("Paso 2")`
- `test_step2_guard_without_data` — afirma `await user.should_see("Primero carga")`

El drill-down no se ejercita en ningun test dedicado. El `test_e2e_wizard.py` si corre el paso 2
con datos y verifica el summary, pero no verifica orden de curvas ni omision de canales.

**Nota positiva:** La cobertura de los criterios Streamlit de UI-02 y UI-03 si existe y es
correcta (test_step2_avisos.py, test_step4_ffmpeg.py, test_coaching.py).

---

### MEDIO-1: Tres capacidades vigente Must Have sin test (CHT-01, REP-01, REP-02)

**Archivos:**
- `product/capacidades/CHT-01 - Generar graficas de analisis.md`
- `product/capacidades/REP-01 - Generar reporte Markdown.md`
- `product/capacidades/REP-02 - Exportar CSVs (delta, corners_compare).md`

Todas declaran explicitamente: "No existe test unitario dedicado a esta capacidad." Esto es
disclosure honesto (el gate no bloqueara). Pero son tres capacidades vigente con prioridad
Must Have de la solucion principal (Analisis Post-Tanda) que no tienen tests automatizados.
Los criterios de aceptacion descritos son verificables (crear archivos, encabezados, top-5).

El pipeline de comparacion CLI si es ejercitado de extremo a extremo por `tests/test_cli.py`
(si existe) y tests de humo, pero sin asercion sobre el contenido de report.md ni los CSVs.

**Riesgo:** Un cambio en `viz/report.py` que rompa el formato del Markdown o los encabezados
del CSV no seria detectado por la suite automatizada.

---

### MEDIO-2: Capacidades UI con modulo ambiguo (SSOT fragmentado)

**Archivos afectados:**
- `product/capacidades/UI-01 - Flujo guiado en pasos.md` — frontmatter `modulo: UI`, wikilink `[[UI - Interfaz Streamlit]]`
- `product/capacidades/UI-02 - Avisos del motor visibles en la UI.md` — idem
- `product/capacidades/UI-03 - Drill-down por curva.md` — idem

Las tres capacidades tienen `modulo: UI` en frontmatter y `## Modulo: [[UI - Interfaz Streamlit]]`
en el cuerpo. Al mismo tiempo, `product/modulos/UI - Interfaz NiceGUI.md` tambien lista estas
tres capacidades como suyas. El comportamiento NiceGUI se describe inline dentro de los archivos
de capacidad con subsecciones "Interfaz NiceGUI (fantasma-ng, v2.0)".

Esto crea ambiguedad en el grafo: el frontmatter asigna cada capacidad solo al modulo Streamlit;
el wikilink entrante desde NiceGUI tambien las reclama. Un agente que filtre capacidades por
`modulo: UI-NG` no encontrara ninguna.

**Opciones de correccion:** (a) Separar capacidades por modulo (UI-01-ST y UI-01-NG), o
(b) declarar `modulo: UI,UI-NG` en frontmatter con el gate adaptado, o
(c) mantener el modelo hibrido pero documentar explicitamente la convencion.

---

### MEDIO-3: hud_preview.py sin nota de capacidad

**Archivo en codigo:** `fantasma/viz/hud_preview.py`

La arquitectura (`engineering/arquitectura.md` linea 53) lista explicitamente:
`hud_preview.py    preview reactiva del HUD para la UI NiceGUI`

No existe capacidad ni especificacion tecnica para este componente. El modulo `OVL` solo cubre
`overlay.py` (OVL-01). La funcionalidad de `compose_preview_frame` (extrae primer frame del
overlay .webm con ffmpeg para mostrar preview en el Paso 3/4 de NiceGUI) no tiene criterios
de aceptacion documentados ni tests.

El componente usa ffmpeg directamente via subprocess, lo que lo hace testeable con monkeypatch
al mismo nivel que `compose.py`.

---

### BAJO-1: UI-01 criterio NiceGUI referencia un bug conocido activo

**Archivo:** `product/capacidades/UI-01 - Flujo guiado en pasos.md`

El ultimo criterio NiceGUI dice: "Dado que ninguna opcion de flujo debe aparecer pre-seleccionada
al cargar la app, cuando el usuario todavia no ha hecho clic, entonces el Paso 0 no debe marcar
ningun flujo como seleccionado (criterio PENDIENTE: hoy el flujo por defecto se muestra
seleccionado — correccion F-01 registrada en `docs/ux-patterns.md`)."

Es disclosure honesto, pero es el unico criterio que documenta un bug activo como criterio
"pendiente". El test `test_step0_no_card_selected_on_load` en `test_ng_step0.py` si existe,
lo que sugiere que el bug pudo haberse corregido — habria que verificar si el test pasa.

---

### BAJO-2: engineering/ panorama de arquitectura — descripcion de la UI legacy como "principal"

**Archivo:** `engineering/arquitectura.md` — tabla de extras opcionales (lineas 25-27)

La tabla lista el extra `ui` (Streamlit) antes que `ui-ng` (NiceGUI). El texto de la seccion
de bloques (linea 54) si dice correctamente "NiceGUI v2.0 (principal) + Streamlit (legacy)".
Es inconsistencia menor de orden, no factual, pero puede confundir en una lectura diagonal.

La descripcion general de la arquitectura (render paralelo, NiceGUI, empaquetado Inno Setup,
hud_preview) es coherente con el codigo actual. El panorama de v2.0 esta correctamente descrito
en el documento de arquitectura — no describe el sistema de v1.

---

## Evaluacion por dimension

### (1) Jerarquia vs producto real v2.0

La jerarquia ecosistema -> solucion -> dominio -> modulo -> capacidad refleja con fidelidad
el sistema implementado en `fantasma/`. El modulo PAC (pace notes), el dominio de coaching de
voz y la interfaz NiceGUI estan todos correctamente modelados como `vigente`. El unico gap es
`hud_preview.py` (sin capacidad) y el backlog stale (GRAVE-1).

### (2) Calidad de criterios de aceptacion

Los criterios del nucleo (NRM-01/02/03, CMP-01/02/03, COR-01, WER-01, SYN-01, CMPO-01,
IMP-MTC-01) son genuinamente Gherkin: tienen "Dado/cuando/entonces" con valores concretos,
son verificables mecanicamente y estan todos cubiertos por tests que existen y tienen los
nombres exactos citados. Calidad: BUENA para el nucleo.

Los criterios de las capacidades UI (NiceGUI sections) son Gherkin formalmente correcto pero
varios no tienen tests que los validen (GRAVE-3). Los criterios de CHT-01, REP-01, REP-02
son verificables pero carecen de tests (MEDIO-1).

Criterios vagos o tautologicos: NO se encontraron. Ningun criterio dice "el sistema funciona
correctamente" sin especificar la condicion observable.

### (3) Capacidades vigente con test citado inexistente o que no prueba el criterio

- UI-02 / NiceGUI Paso 4 ffmpeg: test existe pero no prueba el criterio. (GRAVE-3)
- UI-03 / NiceGUI drill-down: test existe pero no prueba el criterio. (GRAVE-3)
- CHT-01, REP-01, REP-02: no hay test; disclosure honesto. (MEDIO-1)
- Todos los demas (20+ capacidades): tests existen con los nombres exactos citados. VERIFICADO.

### (4) Huerfanos y fragmentacion (DRY/SSOT)

No se encontraron notas chicas que dupliquen contenido de otras en lugar de enlazar. Las
referencias cruzadas usan wikilinks. La unica violacion de SSOT es la fragmentacion del
modulo UI entre dos archivos con la misma lista de capacidades (MEDIO-2).

El backlog SSOT esta roto porque describe el estado deseado de v1.0, no el estado actual de
v2.0 (GRAVE-1). Los items no deberian seguir ahi.

### (5) engineering/ — descripcion del sistema actual vs v1

La arquitectura (`engineering/arquitectura.md`) describe correctamente:
- Nucleo sin dependencias con extras opcionales (sigue igual desde v1)
- NiceGUI como UI principal con Streamlit legacy (correcto para v2.0)
- Render paralelo via `_overlay_worker` (correcto, esta en el codigo)
- Empaquetado con `nicegui-pack` + Inno Setup (descrito en ADR 0018, referenciado)
- `hud_preview.py` nombrado explicitamente (aunque sin capacidad propia)

El panorama de arquitectura NO describe el sistema de v1 — esta actualizado a v2.0.
El unico error factual es el storage backend (GRAVE-2).

Las especificaciones tecnicas (`TEC-OVL-01`, `TEC-CMP-01`, `TEC-SYN-01`, `TEC-COR-01`) son
coherentes con el codigo actual. El componente `engineering/componentes/nicegui.md` tiene el
error de storage pero el resto del contenido (empaquetado, testabilidad) es correcto.

---

## Archivos que requieren intervencion (orden de prioridad)

1. `product/requerimientos/backlog.md` — eliminar 3 items ya entregados (GRAVE-1)
2. `engineering/arquitectura.md` linea 56 — cambiar `storage.client` por `storage.user` (GRAVE-2)
3. `engineering/componentes/nicegui.md` lineas 17, 22, 23 — idem x3 (GRAVE-2)
4. `product/capacidades/UI-02 - Avisos del motor visibles en la UI.md` — corregir seccion de
   Verificacion NiceGUI Paso 4 o agregar el test que falta (GRAVE-3)
5. `product/capacidades/UI-03 - Drill-down por curva.md` — idem para drill-down NiceGUI (GRAVE-3)
6. `product/capacidades/CHT-01`, `REP-01`, `REP-02` — agregar tests o aceptar el disclaimer
   pero registrarlo como deuda tecnica activa (MEDIO-1)
7. `product/capacidades/UI-01/02/03` — resolver ambiguedad de modulo en frontmatter (MEDIO-2)
8. Crear `product/capacidades/OVL-02 - Preview del HUD en la UI.md` o similar para
   `hud_preview.py` (MEDIO-3)

---

## Nota sobre el alcance de esta auditoria

Esta fase no corre los tests ni ejecuta el gate determinista. Las observaciones sobre tests
se basan en leer los archivos de test y comparar nombres de funciones con los citados en las
capacidades. El gate determinista (`tools/auditar.ps1`) corre en paralelo y puede revelar
problemas adicionales de frontmatter o wikilinks rotos no detectados aqui.
