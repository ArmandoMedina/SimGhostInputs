# Registro de decisiones (ADR)

Una decisión = un archivo. Cada ADR fija **qué se decidió, por qué, y qué se descartó**,
para que una sesión futura (o una IA con el mismo contexto) no vuelva a tomar la
bifurcación equivocada.

- Plantilla para nuevos ADR: [`0000-plantilla.md`](0000-plantilla.md).
- Numeración correlativa (`NNNN-titulo-kebab.md`). Nunca se borra un ADR: si queda
  superado, se marca `Reemplazada por ADR-XXXX` u `Obsoleta` y se enlaza el nuevo.

| # | Título | Estado | Fecha |
|---|---|---|---|
| [0001](0001-sync-offset.md) | Auto-detección del offset de sincronía | Aceptada | 2026-06 |
| [0002](0002-crewchief-pacenotes.md) | Integración con CrewChief vía Pace Notes | Propuesta (diferida post-v1.0) | 2026-06-14 |
| [0003](0003-testing.md) | Estrategia de pruebas automatizadas | Aceptada | 2026-06-17 |
| [0004](0004-desgaste-acumulable.md) | Desgaste de llanta acumulable (medidor tipo gasolina) | Aceptada · enmend. 2026-06-22 | 2026-06-21 |
| [0005](0005-indicadores-instantaneos.md) | Indicadores de estado del HUD se leen en el cursor, no por ventana | Aceptada · enmend. 2026-06-22 | 2026-06-21 |
| [0006](0006-grosor-uniforme-lineas-hud.md) | Jerarquía visual del HUD: grosor uniforme, piloto siempre encima, colores que distinguen quién | Aceptada (color difer.) | 2026-06-21 |
| [0007](0007-hud-sin-leyenda.md) | El HUD no lleva leyenda de colores; se documentan fuera | Aceptada | 2026-06-21 |
| [0008](0008-sync-multivuelta-candidatos.md) | Auto-sync multi-vuelta: candidatos + selección obligatoria del usuario (enmienda 0001) | Aceptada | 2026-06-21 |
| [0009](0009-unidad-desgaste-acumulado.md) | Unidad del desgaste acumulado: carga de deslizamiento (integral), no el promedio | Aceptada (implementada) | 2026-06-22 |
| [0010](0010-framework-ui-streamlit.md) | Framework de UI: Streamlit en v1.0; front de escritorio custom diferido a v2.0 | Aceptada | 2026-06-26 |
| [0011](0011-cablear-mariana-no-charbel.md) | Cablear el rol Mariana (UX visual); Charbel se queda en los tests | Aceptada | 2026-06-27 |
| [0012](0012-playwright-smoke-visual-ui.md) | Playwright para smoke visual acotado de la UI Streamlit en v1.0 (enmienda testing del 0010) | Aceptada | 2026-06-28 |
| [0013](0013-setup-modo-desatendido.md) | Modo desatendido (`-Yes`) en `setup.ps1` para pruebas reproducibles | Aceptada | 2026-06-28 |
| [0014](0014-gate-ux-ui.md) | Gate de UX/UI: lo medible bloquea, lo subjetivo es checkpoint de Mariana | Aceptada | 2026-06-28 |
| [0015](0015-estructura-product-engineering.md) | Adoptar estructura product/ + engineering/ (reclasificar el repo a mixto) | Aceptada | 2026-06-29 |
| [0016](0016-gate-grafo-documentacion.md) | Gate determinista del grafo de docs (`auditar.ps1`), sin auto-firma | Aceptada | 2026-06-30 |
| [0017](0017-distancia-canal-requerido.md) | La distancia es un canal requerido; no se sintetiza desde la velocidad | Aceptada | 2026-06-30 |
| [0018](0018-framework-ui-nicegui.md) | Framework de UI v2.0: NiceGUI + nicegui-pack + Inno Setup (enmienda ADR 0010) | Aceptada · enmend. 2026-07-03 | 2026-06-30 |
| [0019](0019-adopcion-homologacion-starter-v0.5.0.md) | Adopción de la homologación con project-starter v0.5.0: audit en CI, evidencia de QA, no-memorias, recursos (cierra la Fase 4 del 0016) | Aceptada · enmend. 2026-07-03 | 2026-07-01 |
| [0020](0020-blast-radius-viz-hud-reference-avisa.md) | Blast-radius de `viz`: `hud-reference` AVISA (no BLOQUEA); el gate pregunta si el cambio es visual | Aceptada | 2026-07-03 |
| [0021](0021-flujo-solo-pacenotes.md) | Flujo "Solo Pace Notes": ruta directa Importar→Análisis→Pace Notes (Paso 0 nuevo flujo) | Aceptada | 2026-07-05 |
| [0022](0022-ci-release-installer.md) | CI que genera y adjunta el instalador Windows en cada release (versión parametrizada, job muerto eliminado) | Aceptada | 2026-07-05 |
| [0023](0023-fuente-unica-de-version.md) | Fuente única de verdad de la versión: literal `__version__` en `fantasma/__init__.py` | Aceptada | 2026-07-05 |
| [0024](0024-sincronia-pace-notes.md) | Sincronía de pace notes: anticipación por tiempo, gap global y sidecar video↔vuelta | Aceptada · enmend. 2026-07-06 | 2026-07-05 |
| [0025](0025-countdown-ancla-en-la-frenada.md) | El último tono del countdown ES el punto de frenada (enmienda ADR 0024) | Aceptada · enmend. 2026-07-06 | 2026-07-06 |
| [0026](0026-cues-frenada-universal-countdown-oportunista.md) | Cues de frenada universales: tono protegido, countdown oportunista y fuera el tono de apex (enmienda ADR 0024 y 0025) | Aceptada | 2026-07-06 |
