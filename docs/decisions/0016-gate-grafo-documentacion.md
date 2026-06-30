# ADR 0016 — Gate determinista del grafo de documentación (auditar.ps1), sin auto-firma

- **Estado:** Aceptada
- **Fecha:** 2026-06-30

## Contexto

El [ADR 0015](0015-estructura-product-engineering.md) reclasificó el repo a mixto y creó
`product/` + `engineering/`: una jerarquía de notas con frontmatter, claves `FAM-MOD-NN`, wikilinks
entre capacidades/módulos/dominios/specs y criterios de aceptación Gherkin. Ese grafo es ahora un
**artefacto de primera clase** — el contrato que un subagente lee antes de implementar — y, como
todo artefacto, se degrada: un subagente puede dejar una nota sin frontmatter, romper un wikilink
(el caso real ya visto: `[[Normalizacion...]]` sin acento no resuelve), o declarar una capacidad
`vigente` sin sus criterios de aceptación.

El objetivo rector del trabajo (ADR 0015) es que **ningún doc/flujo obligatorio se le pase a un
subagente**. El doc-gate §8 (`verificar.ps1` + `escribano-stop`) ya cubre la sincronía
**código→doc dueño** (core/→`formato-datos`, viz/→`hud-reference`, barreras→`flujo-de-trabajo`).
Falta cubrir la **integridad estructural del grafo** del QUÉ/CÓMO, que el §8 no mira.

El thread de diseño proponía, entre otras cosas, archivos `.gate/` donde cada rol escribiera que
"ya validó". Hay que decidir cómo se hace cumplir la integridad **sin romper el principio
"determinismo bloquea; juicio aconseja"**.

## Decisión

Se crea **`tools/auditar.ps1`**, un auditor determinista del grafo de `product/`+`engineering/`,
y se cablea en las barreras existentes. No se introducen archivos de auto-firma.

- **Reglas (path/content-match, deterministas):**
  - **BLOQUEA** — frontmatter ausente o sin claves requeridas (`tipo`/`estado`; las capacidades
    además `clave`/`modulo`/`dominio`); **wikilink roto** `[[X]]` sin nota destino; capacidad
    `estado: vigente` sin `## Criterios de aceptación` con Gherkin (`Dado…`).
  - **AVISA** — capacidad `vigente` sin test citado **ni** disclaimer "no existe test" (cruzar
    capacidad↔test es juicio de Armando); nota huérfana (sin enlace entrante), salvo raíces
    (ecosistema, backlog, proceso).
- **Modulación por estado:** una capacidad nace `estado: en_definicion` y solo se le exige
  frontmatter + enlaces; al pasar a `vigente` se le exigen los criterios. El gate **no estorba la
  exploración**.
- **Tres capas, autoridad creciente** (igual que el resto del sistema): el grafo se evalúa sobre el
  **artefacto** (`git diff`/árbol), no sobre confiar en el agente. `verificar.ps1` lo corre local
  (los BLOQUEA detienen el push, como el doc-drift §8); el CI lo corre con `-Bloquea` en el job
  `docs-graph` (infranqueable). El §8 de `CONTRIBUTING.md` es la **fuente única** que describe las
  reglas; el script las implementa.
- **Sin `.gate/`.** No hay archivos donde un rol firme "validé". Que pytest esté verde = Charbel
  corrió; que el grafo esté íntegro = lo dice `auditar.ps1` leyendo los `.md`. El checkpoint visual
  de Mariana sigue siendo el marcador efímero `.claude/.mariana-marker` (atestación de hook, no
  evidencia commiteada).

## Razones

- **Determinismo bloquea; juicio aconseja.** Lo verificable por máquina (frontmatter, wikilinks,
  presencia de criterios) bloquea; lo que es juicio (¿qué test cubre esto?, ¿esta nota debería
  estar enlazada?) avisa. Un agente que escribe "ya validé" en un `.gate/` es justo lo contrario:
  no es verificación, es confianza disfrazada de barrera — y la rompería.
- **El gate sobre el artefacto es lo que cumple el objetivo rector.** Si el auditor leyera "quién
  tocó qué" confiaría en el proceso; al leer los `.md` resultantes, da igual si lo escribió un
  humano, el orquestador o un subagente despistado: **lo que se cuela, se atrapa**.
- **Mata una deuda recurrente para siempre.** Los wikilinks rotos por acento y los huérfanos eran
  deuda manual que se revisaba "a ojo". Ahora son un check que corre solo en cada push y PR.

## El camino que NO se toma (y por qué tienta)

- **Archivos `.gate/` de auto-firma** (un `.md`/`.json` por rol diciendo "validé"). Tienta porque
  da una pista de auditoría legible y "se siente" riguroso. Se descarta: un agente que firma su
  propio trabajo no es una verificación determinista; rompe "determinismo bloquea" y crea una
  barrera que se puede satisfacer sin hacer el trabajo. La evidencia real es el estado del repo.
- **Meter estas reglas en el stop hook `escribano-stop`.** Tienta por reutilizar la maquinaria de
  hooks ya cableada. Se descarta: el stop hook mira **drift código→doc sobre cambios sin commitear**
  (su asiento); la integridad del grafo es una propiedad **estructural** que se audita mejor sobre
  un rango/árbol (modo CI), no sobre el working tree de una sesión. Mezclarlas sobrecargaría el hook
  y difuminaría responsabilidades. `escribano-stop` se queda como está.
- **Hacer todo BLOQUEA** (también "sin test citado" y "huérfana"). Se descarta: cruzar
  capacidad↔test y decidir si una nota debe estar enlazada es **juicio de Armando**, no una regla
  mecánica dura; forzarlo generaría referencias inventadas o enlaces de relleno. Avisan.
- **No gatear el grafo** (dejar la integridad al QA manual). Se descarta: es exactamente el dolor
  que el método combate — lo manual se olvida, y un subagente no "se acuerda" de revisar wikilinks.

## Consecuencias

- **Se gana:** la integridad del grafo del QUÉ/CÓMO es ahora una barrera determinista; los wikilinks
  rotos, el frontmatter incompleto y las capacidades vigentes sin criterios no se cuelan; la
  modulación por estado deja explorar sin fricción.
- **Se pierde / costo:** una barrera más que mantener; `auditar.ps1` debe seguir a la jerarquía si
  esta cambia (nuevos `tipo`, nuevas claves). El costo es bajo: ~un script de lectura, sin deps.
- **Asiento dueño:** **Armando** (arquitecto) es quien atiende los hallazgos del auditor, igual que
  Charbel atiende un rojo de pytest.
- Al tocar las barreras (`verificar.ps1`, CI) este cambio actualiza `docs/flujo-de-trabajo.md` en el
  mismo commit (doc-gate §8: barreras → su doc dueño).
- **Pendiente:** granularidad `-PorCommit` (auditar commit por commit en un rango) si el flujo lo
  pide; hoy basta el modo árbol y el modo `-Range`. Backport a `project-starter` en la Fase 4.
