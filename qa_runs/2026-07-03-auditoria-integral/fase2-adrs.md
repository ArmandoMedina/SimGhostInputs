# Auditoría de ADRs — SimGhostInputs

**Fecha:** 2026-07-03
**Rama:** codex/sgi-v2-merge
**Auditor:** Claude Sonnet 4.6 (agente, modo lectura)
**Alcance:** docs/decisions/ (ADR 0000–0019), código fuente, CI, product/

---

## Veredicto

El corpus de ADRs está estructuralmente sano (índice completo, sin huecos ni duplicados), pero la migración a NiceGUI dejó tres heridas documentales: una condición de seguridad sin evidencia de cumplimiento (ADR 0018), un ADR con scope que ya no describe la realidad (ADR 0012) y un header de estado internamente inconsistente (ADR 0010). Ningún fallo de runtime; el riesgo es de confusión para agentes y sesiones futuras.

---

## Conteo por severidad

| Severidad | Cantidad |
|-----------|---------- |
| CRÍTICO   | 1         |
| MAYOR     | 2         |
| MENOR     | 3         |
| **Total** | **6**     |

---

## Los 3 hallazgos más graves

1. **[CRÍTICO] ADR 0018 — Spike obligatorio no documentado como cumplido.** El ADR declara 4 condiciones previas ("spike obligatorio antes de escribir código de producción": bundle size, bug --onefile en Win 11 24H2, latencia PIL per-tick, AV false positives). El código NiceGUI está completamente implementado en producción (ng_app.py, ng_step0–4.py) pero no existe ninguna enmienda al ADR 0018, nota de spike ni qa_run que acredite que los 4 puntos fueron verificados. El comentario del CI build-installer confirma que al menos el bundle size spike no cerró ("El paso Inno Setup (--inno) se agrega cuando se confirme el bundle size en el spike de validacion"). Una sesión futura leyendo ADR 0018 no puede saber si los riesgos fueron validados.

2. **[MAYOR] ADR 0012 — Scope desactualizado; sin enmienda que registre el cambio de baseline.** El ADR 0012 titula "Playwright para smoke visual acotado de la UI Streamlit en v1.0". ADR 0018 nota que el baseline pasa a NiceGUI pero no genera enmienda en ADR 0012. Los tests Playwright reales (tests/ui/visual/) ya apuntan a NiceGUI (conftest levanta fantasma.ui.ng_app en SGI_HEADLESS=1, no Streamlit). El CI visual-smoke es únicamente import smoke ("Reemplaza el smoke visual de Streamlit (ADR 0012)"). Lectura directa de ADR 0012 lleva a creer que hay un baseline Playwright activo contra Streamlit en CI: no existe.

3. **[MAYOR] ADR 0010 — Inconsistencia interna en el campo Estado.** El encabezado del archivo dice `Estado: Aceptada`. Las propias Enmiendas al final del mismo documento dicen explícitamente: "El estado de este ADR pasa a Parcialmente reemplazada por ADR 0018". El encabezado nunca fue actualizado. Cualquier lectura del índice README o del header del archivo presenta un estado incorrecto.

---

## Auditoría completa

### Sección 1 — Integridad del índice

| Verificación | Resultado |
|---|---|
| Archivos en disco vs listados en README | LIMPIO |
| Numeración sin huecos (0001–0019) | SIN HUECOS |
| Duplicados | NINGUNO |
| Listados que no existen en disco | NINGUNO |
| Archivos en disco no listados | ADR 0000 (plantilla, correcto que no se liste) |

**Conclusión:** El índice es íntegro. Los 19 ADRs listados (0001–0019) tienen su archivo; la plantilla (0000) existe en disco pero no se lista, lo cual es correcto según las instrucciones del README.

---

### Sección 2 — Contradicciones código vs ADR

#### H-1 [CRÍTICO] ADR 0018: Spike no documentado antes de iniciar migración

**ADR dice:**
> "Condición previa a iniciar la migración — spike obligatorio: Antes de escribir código de producción, verificar las 4 incertidumbres del benchmark."
>
> | Incertidumbre | Cómo verificar |
> |---|---|
> | Bundle size real con stack completo | nicegui-pack --onedir en venv limpio; medir |
> | Bug --onefile en Windows 11 24H2 | Probar en VM limpia |
> | Latencia PIL per-tick en la preview del HUD | Prototipo: slider → PIL → image.set_source() → medir |
> | AV false positives del .exe | Subir a VirusTotal |

**Código/CI real:**
- `fantasma/ui/ng_app.py`, `ng_step0.py`–`ng_step4.py`, `ng_state.py`, `ng_helpers.py` existen y son código de producción completo.
- El job `build-installer` en CI contiene el comentario: "El paso Inno Setup (--inno) se agrega cuando se confirme el bundle size en el spike de validacion" — indica que el bundle size spike no cerró antes de escribir código.
- No hay qa_run, enmienda de ADR ni nota de sesión que documente resultados de los 4 spikes.

**Acción recomendada:** Enmienda al ADR 0018 con resultado de cada spike (aunque sea retrospectiva). Si algún spike no se hizo, declararlo pendiente. La condición "antes de escribir código" ya no aplica (el código existe), pero la evidencia es necesaria para que el CI pueda habilitar Inno Setup.

---

#### H-2 [MAYOR] ADR 0012: Scope dice Streamlit; la implementación real es NiceGUI

**ADR dice (título y texto):**
> "Playwright para smoke visual acotado de la UI Streamlit en v1.0"
> "...una dependencia extra [dev] (no toca al usuario final). Genera un snapshot de imagen de las pantallas clave (el Paso 0 primero) y el CI truena si el layout se mueve."

**Código/CI real:**
- `tests/ui/visual/conftest.py` levanta `fantasma.ui.ng_app` con `SGI_HEADLESS=1` (NiceGUI, no Streamlit).
- `tests/ui/visual/test_step0_visual.py` y `test_e2e_playwright_wizard.py` ejecutan contra el servidor NiceGUI.
- El job CI `visual-smoke` no corre Playwright: es solo import smoke Python (`python -c "from fantasma.ui import ng_app ..."`).
- Comentario del CI: "Reemplaza el smoke visual de Streamlit (ADR 0012) ahora que la UI migra a NiceGUI (ADR 0018). Playwright completo contra NiceGUI se agrega en un PR posterior al merge."

**Lo que ADR 0018 dice sobre ADR 0012:**
> "El ADR 0012 (Playwright para smoke visual) sigue siendo válido en espíritu; el baseline cambia de Streamlit a NiceGUI."

Esto está escrito solo en ADR 0018. El ADR 0012 no tiene ninguna enmienda que registre este cambio. Estado de cabecera del ADR 0012: `Aceptada` (sin mención a NiceGUI).

**Acción recomendada:** Añadir enmienda al ADR 0012 indicando que el baseline migró a NiceGUI (ADR 0018) y que el smoke visual de CI pasó a import smoke provisional mientras se agrega Playwright contra NiceGUI en PR subsiguiente.

---

#### H-3 [MAYOR] ADR 0010: Estado interno inconsistente

**Header del archivo:**
```
- **Estado:** Aceptada
```

**Sección Enmiendas del mismo archivo (2026-06-30):**
> "El estado de este ADR pasa a Parcialmente reemplazada por ADR 0018 en lo que respecta a la arquitectura del front de v2.0"

**README (índice):**
> `| [0010]... | Aceptada | 2026-06-26 |`

El header y el índice presentan un estado que el propio documento invalida. Un agente que lea solo el header (o el índice) llega a conclusiones incorrectas sobre la vigencia de ADR 0010.

**Acción recomendada:** Actualizar el campo `Estado:` del header de ADR 0010 a `Parcialmente reemplazada por ADR 0018` y sincronizar la columna Estado en el README.

---

#### H-4 [MENOR] ADR 0003 — product/modulos/UI - Interfaz Streamlit.md marcada vigente

El módulo product `UI - Interfaz Streamlit.md` tiene `estado: vigente` en su frontmatter. El código Streamlit (`fantasma/ui/app.py`, `step0–4.py`) sigue en el repo y se incluye en el extra `[ui]` del CI. Sin embargo, la dirección estratégica del producto es NiceGUI (v2.0, ADR 0018). Coexistir dos módulos vigentes sin relación de prioridad entre ellos puede confundir a un agente que lea el grafo de producto.

**Nota:** El auditor `auditar.ps1` del ADR 0016 puede detectar esta inconsistencia si el grafo de `product/` define reglas de estado excluyente. Sin ver las reglas exactas del script, este punto es aviso no bloqueo.

**Acción recomendada:** Añadir una nota en `UI - Interfaz Streamlit.md` indicando que es módulo de compatibilidad/v1.0 y que el sucesor estratégico es `UI - Interfaz NiceGUI`. O cambiar `estado` a `legacy` si la jerarquía admite ese valor.

---

#### H-5 [MENOR] Required checks en ruleset de master no aplicados

**ADR 0019 declara acción pendiente del PO:**
> "marcar audit, docs-graph, lint y pytest como required checks en el ruleset de master — sin eso, el punto 2 es cosmético (la regla anti-bypass lo dice: un rojo no-requerido deja pasar el merge)."

El CI define los 4 jobs pero no puede verificarse desde el código si el ruleset de GitHub los marca como required. Esta condición es externa al repo.

**Severidad:** MENOR — el riesgo es conocido, está documentado y es acción humana. No es contradicción código-ADR.

---

### Sección 3 — Decisiones enterradas sin ADR

#### D-1 Patrón d_offset en _render_chunk / _render_parallel (overlay.py)

**Descripción:**
El render paralelo del overlay slice los arrays de canales por chunk de distancia para reducir el pkl de ~4–5 MB a ~1 MB por worker (documentado en el docstring de `_render_parallel`). El parámetro `d_offset` se pasa al worker como el índice de inicio del slice (= distancia en metros del inicio del slice, dado que ds tiene paso de 1 m).

Dentro de `_render_chunk` se usa en dos sitios:
- `_flag_recent_grid(drv_ch.get("abs"), cur_d - d_offset, HOLD_M)` — convierte distancia absoluta a índice en el array recortado para buscar la retención de la luz ABS/TC.
- `j = max(0, min(int(cur_d) - d_offset, len(cum) - 1))` — mismo ajuste para `drv_load_cum` / `ref_load_cum`.

El invariante: `d_offset = d_lo = max(0, int(d_min) - W_BEFORE - HOLD_M)`, donde `d_lo` incluye padding suficiente para que `cur_d - d_offset` nunca sea negativo dentro de la ventana del chunk. Para el caso serial, `d_offset = 0` (arrays completos, sin slice).

**¿Amerita ADR?** No. No hay elección entre alternativas de arquitectura; es un invariante de implementación del optimizador de pickle. Commit 73f5ac1 lo introdujo como corrección de bug (índices incorrectos en chunks no iniciales).

**¿Qué sí falta?** Un docstring en `_render_chunk` que explique el invariante. Sin él, un refactor que iguale `d_offset` a cero o que cambie el step de ds rompe silenciosamente la retención ABS/TC en todos los chunks no-iniciales — exactamente el bug original. El docstring es la documentación adecuada; un ADR sería sobredocumentación.

**Acción recomendada:** Añadir docstring a `_render_chunk` explicando: "d_offset = índice de inicio del slice en ds (metros). Todos los arrays de canales fueron recortados en [d_offset, d_hi). Se resta de cur_d para convertir distancia absoluta a índice relativo en los arrays recortados. Para el caso serial (arrays completos) d_offset=0."

---

#### D-2 Empaquetado PyInstaller/nicegui-pack + Inno Setup (cubierto)

El ADR 0018 registra la decisión de usar nicegui-pack (PyInstaller oficial de NiceGUI) + Inno Setup. El job CI `build-installer` implementa nicegui-pack; el paso Inno Setup está pendiente del spike de bundle size. No falta ADR; el ADR 0018 es suficiente. El CI comenta explícitamente el pendiente.

---

#### D-3 NiceGUI con `native=True` en producción vs `native=False` en Playwright (cubierto)

La variable de entorno `SGI_HEADLESS=1` que desactiva `native=True` para los tests de Playwright está documentada en el docstring de `ng_app.py::run()` y en `tests/ui/visual/conftest.py`. No requiere ADR; es un detalle de infraestructura de testing.

---

### Sección 4 — Estados desactualizados

| ADR | Estado actual en header | Estado real | Acción |
|-----|------------------------|-------------|--------|
| 0010 | Aceptada | Parcialmente reemplazada por ADR 0018 | Actualizar header y README (ver H-3) |
| 0012 | Aceptada | Aceptada con enmienda pendiente (NiceGUI) | Añadir enmienda (ver H-2) |
| 0001 | Aceptada (en README) | Enmendada por ADR 0008 | README lo indica; ADR 0001 no tiene header estructurado — aceptable por formato antiguo |

**Nota sobre ADR 0001:** No tiene el bloque `Estado: / Fecha:` que los ADRs posteriores adoptaron. El README lo declara "Aceptada" y el ADR 0008 lo enmienda. No hay inconsistencia de fondo, solo de formato. No se clasifica como hallazgo porque el formato del header no es un requisito del índice.

---

## Apéndice — Referencias de archivos clave

- `docs/decisions/README.md` — índice
- `docs/decisions/0010-framework-ui-streamlit.md` — Estado header vs enmiendas (H-3)
- `docs/decisions/0012-playwright-smoke-visual-ui.md` — Scope desactualizado (H-2)
- `docs/decisions/0018-framework-ui-nicegui.md` — Spike conditions (H-1)
- `fantasma/ui/ng_app.py` — evidencia de migración completa
- `tests/ui/visual/conftest.py` — Playwright apuntando a NiceGUI (H-2)
- `.github/workflows/tests.yml` — visual-smoke como import smoke (H-2)
- `product/modulos/UI - Interfaz Streamlit.md` — estado vigente cuestionable (H-4)
- `fantasma/viz/overlay.py` líneas 405-406 y 415-419 — patrón d_offset (D-1)
