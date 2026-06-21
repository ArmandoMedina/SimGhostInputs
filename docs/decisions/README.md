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
| [0002](0002-crewchief-pacenotes.md) | Integración con CrewChief vía Pace Notes | Propuesta (v0.8.0) | 2026-06-14 |
| [0003](0003-testing.md) | Estrategia de pruebas automatizadas | Aceptada | 2026-06-17 |
| [0004](0004-desgaste-acumulable.md) | Desgaste de llanta acumulable (medidor tipo gasolina) | Aceptada | 2026-06-21 |
| [0005](0005-indicadores-instantaneos.md) | Indicadores de estado del HUD se leen en el cursor, no por ventana | Aceptada | 2026-06-21 |
| [0006](0006-grosor-uniforme-lineas-hud.md) | Jerarquía visual del HUD: grosor uniforme, piloto siempre encima, colores que distinguen quién | Aceptada (color difer.) | 2026-06-21 |
