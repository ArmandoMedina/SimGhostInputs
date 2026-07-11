# 02 — Linaje: software y organizaciones (cómo se sacó la correctitud de la disciplina personal)

Cada práctica toma una garantía que vivía en la buena voluntad, memoria o competencia de un
individuo falible, y la reifica en un **artefacto o proceso verificable por un tercero distinto
del actor**. Eso es exactamente un hook.

| Práctica | Origen | Qué externaliza | Gate equivalente |
|---|---|---|---|
| Four-eyes / maker-checker | contabilidad → banca (Basilea) | "confío en que el autor no erra/defrauda" | required review: `approver ≠ author` |
| Two-person rule | doctrina nuclear EE.UU. (AFI 91-104) | "confío en el juicio de un solo operador" | doble confirmación para acciones irreversibles |
| Code review (Fagan) | M. Fagan, IBM, 1976 | "confío en que el autor no dejó defectos" | PR gate: revisor independiente antes de integrar |
| Continuous Integration | Booch 1994 → Beck/XP 1997 | "el dev dice que compila" | required check: el build es el árbitro, no la palabra |
| Design by Contract / tipos | Meyer (Eiffel) años 80; Minsky; King 2019 | "el programador recordará validar" | schema/typecheck: estados ilegales inexpresables ("parse, don't validate") |
| Definition of Done | Schwaber/Sutherland, Scrum, 1995 | "el individuo decide si está listo" | criterios explícitos y testeables del gate |
| Runbooks / ITIL / ISO 9001 / CMMI | CCTA 1989; ISO 1987; SEI/Humphrey 1987-91 | "el actor recuerda el procedimiento" | el estado vive en artefactos, no en la memoria del actor |

## Notas clave

- **Maker-checker**: el fraude/error exitoso pasa a requerir colusión de dos, no la falla de uno.
  Es literalmente el "required reviewer que no puede ser el autor" de GitHub.
- **Fagan (IBM, 1976)**: las inspecciones detectaban hasta 93% de defectos; el punto era hacer la
  calidad *reproducible y medible*, no dependiente del cuidado individual.
- **CI**: el gated check-in rechaza el código que rompe el build *antes* de que entre. "La máquina
  es el árbitro" — el ancestro directo del required check.
- **CMM nivel 1 → niveles superiores**: sacar el proceso de "ad hoc, dependiente de individuos
  heroicos" hacia definido y repetible. **Un agente de IA es, por defecto, un actor nivel 1**
  (sin memoria persistente, propenso a olvidar): estos marcos son exactamente la disciplina que
  externaliza estado y procedimiento fuera del actor.
- **Distribución del estado por caducidad** (patrón del laboratorio de campo, transferible): lo permanente (el porqué)
  → ADR; lo enviado → CHANGELOG; el camino → ROADMAP; lo efímero (dónde voy) → HANDOFF que se
  limpia al abrir; los datos externos que no se deducen del código → doc de recursos. La amnesia
  deja de importar porque nada importante vive en la cabeza del actor.

## El sustrato (decisión de arquitectura, benchmark 2026)

No existe, a 2026, un sustrato multi-persona con gate inmutable que la IA domine mejor que
**git/GitHub** — ni para trabajo no-código. Stack ganador, todo de fábrica:

- **Sustrato**: docs-as-code (Markdown versionado); el merge ES la publicación (choke point).
- **Muro local**: Claude Code hooks (`PreToolUse` ask/deny sobre la tool de "enviar"; `Stop`).
  El hook local es UX (saltable con `--no-verify`); **CI es la garantía**.
- **Muro server-side**: branch protection + required checks + required reviews + CODEOWNERS
  (bien configurado: sin repartir admin; el bypass de Actions para aprobar PRs es un toggle de
  administrador que debe estar desactivado — data de 2022, sigue siendo configurable).
- **Validadores**: Vale (prosa: frases prohibidas, terminología, disclaimers), JSON Schema /
  Pydantic (completitud estructural), markdownlint (higiene). Todos gatean **forma, no verdad**.
- Ticketing propietario (Jira/ServiceNow/Zendesk): la IA los conoce mucho peor que git; meterla
  ahí obliga a construir el MCP que se quería evitar. MCP solo como **puente delgado** hacia
  artefactos cautivos, nunca como el muro: el puente transporta, el muro decide, y el muro vive
  fuera del modelo.

Fuentes y URLs: reporte íntegro en el corpus interno del linaje (no publicado; ver la nota en
`decisiones/README.md`). Verificación: `citas-verificadas.md`.
