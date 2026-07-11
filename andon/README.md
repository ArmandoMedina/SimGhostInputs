# Andon — los gates deterministas

> El cordón que para la línea. En Toyota, cualquier operario que ve un defecto jala el Andon y detiene la producción. Aquí, el Andon es el conjunto de gates que **atrapan el error en la fuente, fuera del LLM** — no le piden al agente que se porte bien; hacen el error imposible o lo bloquean.

## La ley: una sola fuente

Toda regla de gate vive en **un solo lugar** — el `blast-radius.json` (el "radio de explosión": qué área, al tocarse, obliga a tocar qué doc dueño). El hook, el verificador local y el CI **leen esa ley**; la prosa solo la explica. Cambiar la regla en un lugar la cambia en todos.

> **Dónde vive:** en un proyecto instalado, la ley es `.jidoka/blast-radius.json`. Jidoka corre su propio Andon (dogfooding), así que en **este** repo el motor vive en [`../tools/`](../tools/) y la ley es [`../tools/blast-radius.json`](../tools/blast-radius.json).

## Autoridad creciente (el modelo de amenaza)

No todos los gates son muros. Se ordenan por autoridad, y solo el último es infranqueable:

```
Stop hooks (avisan / frenan el cierre)   →  saltables
  pre-push  (UX local)                   →  saltable con --no-verify
    check `andon` en CI + branch protection  →  EL MURO REAL (server-side)
```

Se asume que **todo aviso local será bypaseado**. Por eso el muro real es el check `andon` corriendo en CI con *required checks* activados — lo único que `--no-verify` no salta.

## deny vs ask — heredado de la aviación

Este eje no lo inventamos: sale de cómo la aviación resolvió la automatización peligrosa (ver [`../doctrina/03-aviacion.md`](../doctrina/03-aviacion.md)).

- **`deny`** (bloqueo duro, **estilo Airbus**: límites que no puedes cruzar) para lo **irreversible y peligroso**.
- **`ask`** con override (**estilo Boeing**: avisa y frena, pero puedes anular) para lo que requiere **juicio humano**.

Se mezclan por tipo de acción; no se elige una sola filosofía. Y cuando la situación se degrada, la regla es **`click-it-down`** ("Children of the Magenta"): baja el nivel de automatización, no pelees dentro del modo automático.

## Los disparos: doctrina en el momento del gate

La IA no lee la doctrina. La doctrina le llega **compilada a disparos** — mensajes cortos (regla + porqué, autocontenidos) que se inyectan en el `permissionDecisionReason` de un hook, en un mensaje de CI o en la plantilla de un PR. Los 12 disparos viven en [`../kit/.jidoka/disparos/`](../kit/.jidoka/disparos/). Algunos clave:

- **`no-verify-es-teatro`** — saltarte el hook local solo pospone y agranda el fallo; el muro real es el required check.
- **`evidencia-no-palabra`** — el gate lee el artefacto (archivo, timestamp, diff, log), no la palabra del agente.
- **`prueba-de-vida-del-gate`** — ¿cuándo rechazó este gate algo real por última vez? Silencio = podrido.

## Prueba de vida

Un gate que nunca rechaza nada está podrido aunque el tablero esté verde. Por eso el motor Andon incluye un **self-test** (`probar-gate`): corre casos de resultado conocido —incluido uno que DEBE bloquear— para que la rama que bloquea no se pudra sin que nadie lo note. Quien valida, también se valida.

## Cuatro reglas de campo (pagadas en el linaje)

- **El gate gobierna hacia adelante; la historia tiene baseline.** Al estrenar un gate en un repo existente, el modo forense surfacea commits previos a la regla — eso no es deuda accionable: se limpia en un PR dedicado o se acepta como baseline. La autoridad del gate empieza el día que se enciende.
- **Hay una segunda familia de barreras: las que protegen el proceso, no el repo.** Corren donde el artefacto vive (el envío, el despliegue), no en CI. Mismas leyes: choke point, deny/ask, ledger de lo realmente enviado ("el registro se hace SOLO tras enviar de verdad"), y sin historial el check **se degrada a lo verificable hoy y lo dice** — no truena. Un `ask` que grita en falso seguido se recalibra o se poda: un gate ruidoso entrena el reflejo de click-para-pasar.
- **Un principio sin mecanismo es una promesa.** En el linaje, "nada sale del dispositivo" fue disciplina de código hasta que se volvió regla de plataforma (una CSP que lo hace imposible) — con la consecuencia deliberada de que violar el principio en el futuro exija revisitar el ADR a propósito. El costo de salida como diseño: poka-yoke aplicado a los propios ADRs.
- **Sin descartes silenciosos.** Cuando un motor decide omitir o callar algo, el descarte queda en el artefacto de auditoría con su razón. Caso real: unos `continue` tiraban datos sin registrarlos y el reporte *mentía por omisión*. El silencio también es auditable.

## El motor, en concreto (Sprint 1)

En este repo el motor son varias piezas en [`../tools/`](../tools/) más los hooks y el CI:

| Pieza | Qué hace |
|---|---|
| [`tools/blast-radius.json`](../tools/blast-radius.json) | La ley. 8 áreas (incluida `raiz`, la tierra de nadie; `ritual`, los comandos `/jidoka:*` y las skills; y `kit`, el instalador y el kit sembrable — Sprint 3). Dimensiones por área: `doc_bloquea` (**un** solo real: un ADR nuevo debe listarse en su índice), `doc_avisa`, **`product_avisa`** (el grafo de `product/`), **`revisa`** (marca el código que pide `/code-review`) y `rol` (`revisor-visual` enciende `gemba-stop`). Los mensajes enseñan cuándo **no** aplican (anti-fatiga). |
| [`tools/verificar.ps1`](../tools/verificar.ps1) | El verificador. Corre local (pre-push) y en CI. **Avisa** los `doc_avisa`, **bloquea** los `doc_bloquea`, y **falla cerrado** (exit 2) si no puede medir. |
| [`tools/probar-gate.ps1`](../tools/probar-gate.ps1) · [`probar-hooks.ps1`](../tools/probar-hooks.ps1) · [`probar-auditor.ps1`](../tools/probar-auditor.ps1) | Los self-tests (prueba de vida). Casos de resultado conocido, cada uno con al menos uno que DEBE bloquear. Corren en CI sobre el motor del PR. `probar-gate` incluye además un **fixture del quickstart del README** (flujo real commit→verificar por git), para que la demo copy-paste no se rompa en silencio. |
| [`tools/auditar.ps1`](../tools/auditar.ps1) | El **auditor del grafo** de docs (`product/`): frontmatter, wikilinks, Gherkin de las capacidades `vigente`, huérfanas — modulado por estado (`kanban/estados.md`). Cosechado de los casos de éxito (ADR 0007). Corre en CI `-Range base...HEAD -Bloquea`. |
| [`tools/instalar.ps1`](../tools/instalar.ps1) + [`probar-instalador.ps1`](../tools/probar-instalador.ps1) | El **instalador** (Sprint 3, MVP Windows-first, ADR 0008/0009): siembra el método en un repo destino leyendo el motor genérico del árbol (sin duplicar la ley), regla **no-clobber**. **Pregunta el arquetipo** (`docs-as-code`/`code-first`) y siembra distinto — la matriz vive como manifiesto ejecutable (`kit/.jidoka/instalar/manifiesto.json`) con las leyes-plantilla (`kit/.jidoka/leyes/`). Su smoke instala en un repo temporal y corre los self-tests sembrados — un instalador que siembra un motor roto se caza ahí. |
| **El lazo labs↔Jidoka** (Fase 3.C, ADR 0012): [`tools/version.txt`](../tools/version.txt) + [`probar-version.ps1`](../tools/probar-version.ps1) · sello `tools/jidoka-motor.json` · `instalar.ps1 -Actualizar` · [`estado-motor.ps1`](../tools/estado-motor.ps1) · [`reportar-leccion.ps1`](../tools/reportar-leccion.ps1) | *La lección sube, la máquina baja.* `version.txt` es el **SSOT** (atado al CHANGELOG por `probar-version`); el instalador siembra el **sello** (versión + hash por pieza); **`-Actualizar`** re-siembra solo la mecánica con conciencia de tres vías (no pisa lo que el hijo customizó); **`estado-motor`** avisa si el hijo está atrás (aviso, no muro); **`reportar-leccion`** abre el canal de subida. La costura `verificar.local.ps1` deja al hijo extender la mecánica sin bifurcarla. |
| `.claude/hooks/` + `.github/workflows/andon.yml` | Stop hooks locales: `andon-stop` (doc-drift), **`review-stop`** (código sin `/code-review` frena; marcador humano `.review-marker`) y **`gemba-stop`** (cambio visual sin evidencia fresca en `qa_runs/` frena — dormido si no hay áreas `rol: revisor-visual`); + `no-memorias` (PreToolUse). Si git falla de verdad, **avisan** en vez de callar (ALTO-04). El check `andon` en cada PR — **con la ley y el verificador leídos desde la base** (ADR 0003) — y **sube los avisos al summary del PR** (cierra la grieta 1). |

### Encenderlo

1. **Hooks locales** (una vez por clon): `git config core.hooksPath .githooks` — así el `pre-push` corre el verificador antes de cada push. Los hooks de Claude (`no-memorias`, `andon-stop`) se cablean solos vía `.claude/settings.json`.
2. **El muro real** (paso humano, una vez): en GitHub → *Settings → Branches → Branch protection rule* de `main`, con **tres** cosas — sin las tres no hay muro:
   - **Require a pull request before merging** (si se puede pushear directo, el check nunca corre);
   - el check del workflow Andon como *required status check* (en el selector de GitHub aparece con su nombre de job: **`andon blast-radius (la ley)`**);
   - **Do not allow bypassing the above settings** (si el admin puede saltárselo, para el admin —y para el agente usando sus credenciales— sigue siendo una sugerencia).
3. **Probarlo**: corre `./tools/probar-gate.ps1` (debe salir verde). Para verlo bloquear de verdad: agrega un ADR en `docs/decisions/` sin listarlo en el índice y corre `./tools/verificar.ps1`.

## Fronteras del muro (honestidad)

Ningún muro es infinito; estos son los límites conocidos de este motor, dichos de frente (la doctrina exige fronteras explícitas, `doctrina/06`):

- **La ley que juzga un PR es la de la base, no la del PR** — eso cierra el hueco auto-referencial (un PR ya no puede vaciar la ley que lo juzga). El costo: un cambio legítimo a la ley rige a partir del *siguiente* PR.
- **El primer push de una rama nueva no se verifica localmente** (sin upstream, el pre-push solo ve el working tree). Lo cubre el CI en cuanto abres el PR.
- **"Tocar" el doc dueño incluye borrarlo** — el matching mide presencia en el diff, no que el doc siga existiendo. Borrar el índice de ADRs junto con un ADR nuevo pasaría el gate (y lo cazaría el humano en el PR).
- **Sin branch protection completa (paso 2), todo lo anterior es teatro.** El gate local se salta con `--no-verify` a propósito y por diseño; el muro es el check requerido server-side, y solo si el admin tampoco puede saltárselo.
- **El marcador de revisión es válvula humana, no auto-firma.** `review-stop` y `gemba-stop` se despejan con un marcador SHA (`.claude/.review-marker`, `.claude/.gemba-marker`, gitignored) que **pone el humano** tras revisar; el hook verifica que el SHA sea el del diff real (lo que se cuela, se atrapa). Un agente no puede escribirse su propio pase sin que corresponda al artefacto.
- **`gemba-stop` mide frescura por mtime **y exige que la evidencia esté rastreada por git**, y por eso corre local.** "Evidencia válida" = artefacto en `qa_runs/` que `git ls-files` rastrea (forzado al índice con `git add -f`, porque `qa_runs/` está gitignoreado) **y** con mtime posterior al cambio visual. Lo segundo pide `Stop` local (un `git checkout`/clone reescribe mtimes); lo primero cierra un Goodhart cosechado por el lazo (ADR 0013): un archivo que nunca se commitea satisfacía el mtime pero git no lo veía — evidencia-no-palabra exige que exista *en git*, no solo en disco. En Jidoka nace **dormido** (no hay áreas `rol: revisor-visual`); su prueba de vida está en el self-test, no en el repo.
- **`no-memorias` solo intercepta `Write|Edit`, no Bash** (grieta 2 de la auditoría externa): una escritura vía `Set-Content` por Bash lo rodea. Sigue abierta — ampliar el matcher a Bash o confesarlo aquí es trabajo pendiente (ROADMAP). Es un aviso disfrazado de deny mientras tanto.
