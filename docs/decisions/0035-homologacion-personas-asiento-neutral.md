# ADR 0035 — Homologación de las personas al asiento neutral (segunda pasada)

- **Estado:** Aceptada (2026-07-11)

## Contexto

El [ADR 0034](0034-convergencia-nucleo-jidoka.md) convergió la **maquinaria** de SGI al núcleo neutral
de [Jidoka](https://github.com/ArmandoMedina/jidoka): hooks, `settings.json`, comandos y los tokens de
rol de la ley quedaron idénticos. Una auditoría de homologación "full join" (dos auditores + diff de la
maquinaria, 2026-07-11) confirmó que **la máquina que juzga es neutral y byte-idéntica** —incluido
`gemba-stop.ps1`— pero encontró que el **drift sobrevivió en la prosa** de los `SKILL.md` de las
personas y en un comando:

1. Ninguna persona **declaraba su asiento neutral** (Jidoka `kanban/roles.md` lo exige: "soy Mariana,
   el asiento revisor-visual"); el mapeo quedaba implícito por dominio.
2. El `SKILL.md` de **Mariana** nombraba maquinaria que **no existe** (`mariana-stop`,
   `.claude/.mariana-marker`, "rol `Mariana` del manifiesto"), cuando la real es `gemba-stop.ps1`,
   `.claude/.gemba-marker` y el token `revisor-visual`. Drift documental, no de máquina.
3. **Charbel** había perdido dos límites neutrales del asiento `validador`: "entrada hostil con
   presupuesto anti-ReDoS" y "verificar terceros contra su código fuente, no su documentación".
4. El **Escribano** enrutaba los ADR a un skill `adr-helper` **inexistente** y contradecía a Armando
   sobre quién los redacta.
5. El comando `/arranca` era una reescritura comprimida que **omitía** dos reglas duras del canónico de
   Jidoka: "una sola sesión escritora por working tree" y la convención 🎭 de anuncio de asiento.

## Decisión

Se homologa la **prosa** de las personas al asiento neutral, sin tocar la maquinaria (que ya es
neutral):

1. **Declaración de asiento** — cada `SKILL.md` de persona (ahiram→desarrollador, armando→arquitecto-doc,
   charbel→validador, mariana→revisor-visual, escribano→escribano) declara explícitamente qué asiento
   neutral ocupa. El nombre es cosmético; los límites son los del asiento.
2. **Mariana** — su prosa se corrige a los nombres reales de la maquinaria neutral (`gemba-stop`,
   `.gemba-marker`, `revisor-visual`).
3. **Charbel** — recupera los dos límites neutrales del `validador`, aterrizados en `importers/` (que
   parsean archivos externos, caso hostil esperado).
4. **Autoría de ADR (matiz de casting):** en SGI, **Armando** (el asiento arquitecto-doc) actúa de
   **redactor/escribiente** del ADR, pero la **decisión sigue siendo del PO**. El asiento neutral de
   Jidoka no redacta ADRs; esta es una **persona-ficación local**, no un cambio de la ley. Se corrige la
   referencia rota del Escribano (`adr-helper` → Armando) y la de `docs/flujo-de-trabajo.md`.
5. **`/arranca`** se re-homologa a la estructura canónica de Jidoka, recuperando las dos reglas omitidas
   y conservando lo propio de SGI (ciclo del HANDOFF, personas Mau/Mariana, rutas del repo).
6. **Excepción de datos de QA visual (con nombre):** la regla neutral del asiento revisor-visual es
   "evidencia 100% sintética". SGI usa **telemetría real** para la QA visual del HUD porque lo sintético
   no ejercita el render realista. Lo que la regla protege —que ningún dato real entre al repo— se
   cumple: el material vive **fuera del repo** (ruta gitignoreada) y en `qa_runs/` solo se commitean
   **capturas**, nunca telemetría cruda. Se documenta como excepción de dominio (patrón Jidoka
   `doctrina/07`), no se fuerza a sintético.

## Razones

- La homologación de Jidoka es "una sola metodología": la maquinaria neutral + una capa cosmética de
  persona. Si la prosa de la persona describe maquinaria que no existe o contradice sus límites, reintroduce
  la "metodología paralela" que el 0034 cerró — aunque la máquina esté sana.
- Todo el drift restante era **prosa barata de arreglar y sin riesgo para la máquina**; los cambios no
  tocan `fantasma/`, ni los hooks, ni la ley.

## El camino que NO se toma (y por qué tienta)

- **Renombrar los hooks/marcadores a la persona** (`gemba-stop` → `mariana-stop`) para que la prosa
  original de Mariana fuera cierta: sería exactamente la regresión que el 0034 evitó — la máquina debe
  quedarse neutral; se corrige la prosa, no la máquina.
- **Forzar la QA visual a datos sintéticos** para cumplir la regla al pie: rompería la práctica real
  (el HUD necesita telemetría realista) sin ganar nada — la regla se satisface documentando la excepción
  con nombre, que es el mecanismo que el propio método prescribe.
- **Quitarle a Armando la redacción de ADR** para igualar al asiento neutral: pierde una división de
  trabajo útil; el asiento neutral prohíbe *decidir*, no *escribir el archivo* — y Armando no decide.

## Consecuencias

- Las personas y el comando `/arranca` quedan homologados al método; el mapeo persona↔asiento es
  explícito y auditable.
- La maquinaria no cambia: cero riesgo de regresión (no se tocó `fantasma/`, hooks, ni la ley).
- **Pendiente (diferido a sesión humana):** portar `probar-gate.ps1` (self-test del gate) desde Jidoka
  exige que `verificar.ps1` acepte inyección de archivos (`-Cambiados`), lo que implica **editar el
  propio gate** — la regla del método reserva eso a una sesión humana, no a un pase autónomo. Queda
  anotado en el ROADMAP.
