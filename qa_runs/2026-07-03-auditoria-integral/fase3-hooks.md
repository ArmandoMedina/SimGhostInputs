# Fase 3 — Auditoría integral de hooks de sesión

**Fecha:** 2026-07-03  
**Alcance:** `.claude/settings.json`, `.claude/hooks/review-stop.ps1`, `escribano-stop.ps1`,
`mariana-stop.ps1`, `no-memorias-pretooluse.ps1`; contraste con `docs/flujo-de-trabajo.md`
y `tools/blast-radius.json`.  
**Auditor:** Claude Sonnet 4.6 (agente)  
**Rama:** `codex/sgi-v2-merge`

---

## Veredicto

Los hooks de sesión son funcionalmente correctos para el escenario que vigilan (cerrar una sesión
con working tree sucio), pero comparten una falla arquitectónica crítica: todos usan
`git status --porcelain` como fuente de verdad, lo que los deja ciegos ante código commiteado
durante la sesión. Ese punto ciego ya causó el incidente 73f5ac1 (hoy). A eso se suman dos fallas
secundarias graves: la evidencia de Mariana no valida relevancia (cualquier archivo qa_runs/ pasa) y
el marcador de review puede setearse sin hacer la revisión. El mecanismo de bloqueo local
(`verificar.ps1`) es saltable con `--no-verify`. El CI es la única barrera que nadie puede saltar.

---

## Conteo de hallazgos por severidad

| Severidad | Cantidad |
|-----------|----------|
| CRITICO   | 2        |
| ALTO      | 4        |
| MEDIO     | 5        |
| BAJO / INFO | 4      |
| **Total** | **15**   |

---

## Sección 1 — Conformidad con la documentación

### 1.1 review-stop.ps1

**Documentado (flujo-de-trabajo.md §La capa en sesión):**
> "si hay código nuevo en `fantasma/` sin revisar, frena el cierre y dispara `/code-review`.
> Marca el diff revisado (`.claude/.review-marker`) para no re-revisar lo mismo."

**Implementado:** El script lee `git status --porcelain -- fantasma`, computa SHA1 de
`git diff HEAD -- fantasma` concatenado con la lista de cambios, compara contra el marker, y
bloquea si difiere. Instruye al agente a correr `/code-review` y provee el comando exacto para
marcar el diff como revisado.

**Diferencias encontradas:**

- **[CRITICO-01]** El scope de la comprobación es el working tree, no la sesión. La línea 17
  (`if (-not $codeChanged) { exit 0 }`) causa que el hook pase inmediatamente si todo el código
  de la sesión fue commiteado antes del cierre, sin importar si hubo revisión. El incidente
  73f5ac1 (commit de código de otra IA que entró sin que el Reviewer de la sesión pasara) ocurrió
  exactamente por esta razón: al momento del Stop, el working tree estaba limpio.

- **[ALTO-01]** La documentación promete que el hook "dispara `/code-review`" pero en realidad
  solo instruye al agente en el mensaje `additionalContext`. No hay verificación de que `/code-review`
  se haya ejecutado; el agente puede escribir el marker sin haberlo hecho.

- **[BAJO-01]** El payload SHA1 mezcla `git diff HEAD -- fantasma` (cambios rastreados vs HEAD)
  con `git status --porcelain -- fantasma` (que incluye archivos no rastreados como líneas XY).
  Si hay archivos nuevos sin `git add`, el SHA incluye su nombre pero no su contenido. Un archivo
  nuevo que cambia de contenido sin `git add` no cambia el SHA y no re-dispara el gate.

### 1.2 escribano-stop.ps1

**Documentado:**
> "si tocaste código y su doc dueño quedó desfasado (§8), frena el cierre y dispara el Escribano,
> que lo actualiza. Cuando ya está sincronizado, deja cerrar."

**Implementado:** El script lee blast-radius.json, evalúa git status --porcelain, y bloquea si
algún `doc_bloquea` falta. Solo `doc_bloquea` bloquea; `doc_avisa` y `product_avisa` aparecen
en el mensaje de contexto pero no bloquean el cierre.

**Diferencias encontradas:**

- **[CRITICO-02]** Misma falla arquitectónica que review-stop: la línea 27
  (`if (-not $changed) { exit 0 }`) hace que cualquier sesión que commitee código sin sus docs
  antes del Stop tenga working tree limpio y el hook pase sin detectar el drift. Esta ventana está
  mencionada en el comentario del script (líneas 7-9) y en la doc (nota sobre las dos ventanas),
  pero la doc lo presenta como comportamiento esperado cuando en realidad es la ventana de bypass
  más ancha del sistema.

- **[INFO-01]** Las áreas `importers`, `cli`, `setup` y `orquestacion` no tienen `doc_bloquea`
  en blast-radius.json (solo `doc_avisa`). Cambios en `fantasma/importers/`, `fantasma/cli.py`,
  `.claude/skills/` o `setup.ps1` nunca disparan el bloqueo del Escribano en sesión. El doc dice
  que el escribano bloquea por "§8" pero blast-radius clasifica estas áreas como avisos, no bloqueos.
  Esto no es contradicción — es diseño — pero vale documentarlo como cobertura incompleta del gate.

- **[BAJO-02]** El script no tiene mecanismo de marcador (a diferencia de review-stop y mariana-stop).
  Cada Stop donde haya `doc_bloquea` pendiente bloqueará sin importar si el Escribano ya lo atendió.
  El único mecanismo de desbloqueo es que los docs aparezcan en el working tree. Esto es correcto
  por diseño (el marcador aquí sería incorrecto), pero significa que si el Escribano actualiza un
  doc y lo commitea antes del Stop, el hook pasa por la ventana CRITICO-02 sin haber validado nada.

### 1.3 mariana-stop.ps1

**Documentado:**
> "exige evidencia verificable en `qa_runs/` posterior al cambio (screenshots, logs de la corrida)
> antes de dejar cerrar — un veredicto de QA sin artefacto no vale (ADR 0019)"

**Implementado:** El script busca en `qa_runs/` cualquier archivo cuyo `LastWriteTime` sea mayor
que el `LastWriteTime` del archivo visual más reciente. Si encuentra alguno, sale 0.

**Diferencias encontradas:**

- **[ALTO-02]** La evidencia es temporalmente relativa pero no temáticamente relevante. El check
  es `Get-ChildItem $qaDir -Recurse -File | Where-Object { $_.LastWriteTime -gt $lastVis }`.
  Cualquier archivo en `qa_runs/` — incluyendo runs de Charbel (`charbel-20260630/laps/*.txt`,
  `local-matrix-*/detect/*.json`) — satisface el gate si su timestamp es posterior al cambio
  visual. En la sesión que produjo 73f5ac1, los archivos Charbel de `qa_runs/charbel-20260630/`
  son del 2026-06-30; cualquier cambio visual posterior a esa fecha que tenga en la misma sesión
  un nuevo archivo qa_runs/ (de cualquier tipo) pasaría el gate de Mariana. La doc promete
  "evidencia verificable"; el script acepta cualquier dato de cualquier disciplina.

- **[ALTO-03]** El timestamp usado para el cambio visual es `LastWriteTime` del archivo en disco,
  no la fecha del commit. Un archivo que existía antes del cambio pero fue tocado (p.ej. por el
  propio script de QA al leerlo) puede mover el timestamp y alterar la comparación. En repos
  con `git checkout` recientes, todos los archivos tienen timestamp del checkout, lo que puede
  hacer que archivos "viejos" pasen como recientes.

- **[MEDIO-01]** El marker `.mariana-marker` tiene la misma vulnerabilidad que `.review-marker`:
  el hook mismo provee el comando exacto para setearlo sin haber hecho QA:
  `Set-Content -Encoding ASCII '.claude/.mariana-marker' '$sha'`.
  No hay audit trail. El doc llama a esto "caso raro (el PO aprueba sin artefacto)" pero no hay
  ningún mecanismo que fuerce la intervención del PO antes de setear el marker.

### 1.4 no-memorias-pretooluse.ps1

**Documentado (ADR 0019):** Bloquea escrituras a la memoria persistente de Claude.

**Implementado:** Normaliza separadores de ruta y evalúa regex `/\.claude/projects/[^/]+/memory/`.
Bloquea con `permissionDecision: 'deny'`.

**Diferencias:** Ninguna. La implementación es fiel a la intención documentada. El script corre
via `PreToolUse` con matcher `Write|Edit` y solo afecta escrituras a rutas de memoria de Claude.
No es un Stop hook, por lo que no comparte la falla arquitectónica de los otros tres.

---

## Sección 2 — Ventanas de bypass

### 2a. Bypass por commit durante la sesión [CRITICO-01 y CRITICO-02]

**Mecanismo:** Todos los Stop hooks (review-stop, escribano-stop, mariana-stop) evalúan
`git status --porcelain` como primera acción. Si el resultado está vacío, salen con `exit 0`.
Esto sucede cuando:
- El código fue commiteado durante la misma sesión (por el agente o por el usuario)
- Otro agente o proceso externo hizo un commit en paralelo
- El usuario ejecutó `git commit` desde otra terminal

En el incidente 73f5ac1, la sesión parallel de otra IA commiteó `fantasma/viz/overlay.py` con 149
líneas cambiadas. Al momento del Stop, `git status --porcelain -- fantasma` devolvió vacío, y
review-stop, escribano-stop y mariana-stop pasaron sin intervenir.

**Afecta:** Los tres Stop hooks. review-stop: línea 17. escribano-stop: línea 27. mariana-stop: línea 54.

**Gravedad:** CRITICO. Es la ventana principal y la que ya causó un incidente real.

**No hay mitigación en el flujo actual para el caso de código commiteado antes del Stop.** La doc
auto-documenta la ventana como conocida ("commitea código y docs juntos") pero no ofrece cierre.

### 2b. Manipulación de marcadores [MEDIO-01]

**Mecanismo:** Ambos marcadores (`.review-marker`, `.mariana-marker`) son archivos de texto plano
gitignoreados, escritos por el propio agente con un comando que el hook enseña explícitamente en
el mensaje de bloqueo. El SHA1 es determinista y reproducible desde el diff. Un agente puede:
1. Calcular el SHA desde `git diff HEAD -- fantasma` + `git status --porcelain`
2. Escribir el marker sin ejecutar `/code-review` ni guardar evidencia en `qa_runs/`
3. El hook pasa en el próximo Stop

Los marcadores sobreviven solo si el diff es exactamente el mismo. Un nuevo cambio en `fantasma/`
invalida `.review-marker` y un nuevo cambio visual invalida `.mariana-marker`, por lo que la
manipulación requiere re-computar. No sobreviven automáticamente a nuevos cambios: esto es correcto.

**Gravedad:** MEDIO. Requiere intención del agente de bypassear el control.

### 2c. `git commit --no-verify` y `git push --no-verify`

**`git commit --no-verify`:** No tiene efecto sobre los Stop hooks de sesión de Claude Code porque
estos no son hooks de git. El flag `--no-verify` solo omite hooks de git (pre-commit, commit-msg).
No hay hooks pre-commit ni commit-msg definidos en `.githooks/`. Por lo tanto, `--no-verify` en
commit es un no-op para el sistema de sesión. Sin embargo, dado que el commit limpia el working
tree, desencadena el bypass CRITICO-01/02 de forma indirecta.

**`git push --no-verify`:** Salta el `.githooks/pre-push`, que es el único mecanismo que corre
`tools/verificar.ps1`. Esto bypasea:
- Lint (ruff check)
- Formato (ruff format --check)
- Tests (pytest)
- Doc-gate CHANGELOG
- Doc-gate blast-radius (el bloqueo local de §8)
- Auditor del grafo de docs (auditar.ps1)

La doc documenta esto explícitamente ("Saltar a propósito: `git push --no-verify`") y asume que
el CI es la barrera de respaldo. Los jobs de CI (`lint`, `pytest`, `docs-graph`, `audit`) son la
última línea de defensa real. Sin embargo, si `audit` (blast-radius sobre el rango del PR) no está
marcado como *required check* en el ruleset de master (ADR 0019 menciona que un job no-requerido
deja pasar el merge), el bypass es total en todo el pipeline.

**Gravedad (--no-verify en push):** ALTO. Salta todo el pipeline local.

### 2d. `stop_hook_active` anti-loop [MEDIO-02]

**Mecanismo:** Los tres Stop hooks verifican `$inp.stop_hook_active` y salen con `exit 0` si es
verdadero. Esto previene bucles infinitos cuando Claude Code dispara un Stop desde dentro de un
Stop. Sin embargo, crea un bypass automático para cualquier cierre que ocurra desde dentro de un
contexto de Stop hook activo: si el agente cierra su sesión desde una sub-invocación durante la
resolución de un hook, los tres gates pasan sin comprobación.

**Gravedad:** MEDIO. Caso raro pero sistémico.

---

## Sección 3 — Robustez PS 5.1

### 3.1 Errores silenciosos [ALTO-04]

Los cuatro scripts configuran `$ErrorActionPreference = 'SilentlyContinue'` en la primera línea.
Esto es la opción de "falla silenciosa" de PowerShell 5.1. Consecuencias específicas:

- **review-stop:** Si `git diff HEAD -- fantasma` falla (git no disponible, repo corrupto),
  `$payload` será vacío o parcial. El SHA1 de un string vacío difiere del marker, así que el hook
  bloqueará. Comportamiento safe-fail en este caso. Sin embargo, si `git status --porcelain`
  falla, `$codeChanged` será `$null` y el hook saldrá con `exit 0` en línea 17 (falso negativo).

- **escribano-stop:** Si `git rev-parse --show-toplevel` falla, el script sale en línea 25
  (`if (-not $repo) { exit 0 }`). Safe-fail. Si el blast-radius.json es ilegible, el script pasa
  sin detectar drift (línea 32 falta un try/catch equivalente al de mariana-stop).

- **mariana-stop:** Tiene `try { ... } catch { exit 0 }` para la lectura del manifest (línea 32).
  Safe-fail si el JSON está malformado. Pero si `Get-ChildItem $qaDir` falla por permisos, el
  script bloquea (porque `$fresh` queda null), lo cual es correcto.

- **En general:** Errores en `ConvertTo-Json` o en la escritura de stdout silencian la salida JSON.
  Claude Code recibiría respuesta vacía del hook, lo que puede interpretarse como no-bloqueo.

### 3.2 Rutas con espacios [MEDIO-03]

La ruta del repo es `C:\Repositorio personal\SimGhostInputs` (espacio en "Repositorio personal").

- `settings.json` usa `${CLAUDE_PROJECT_DIR}` y el comando está entre comillas dobles en la cadena
  JSON. Correcto.
- Los scripts usan `Join-Path` para construir rutas (correcto en PS 5.1).
- `mariana-stop.ps1` usa `-LiteralPath` en `Get-Item` y `Test-Path`, que maneja espacios
  correctamente.
- `escribano-stop.ps1` usa `Join-Path $repo` pero no siempre usa `-LiteralPath` en subcalls.
  En la práctica PS 5.1 maneja espacios en rutas calculadas por Join-Path, pero si una ruta
  llegara como string interpolado a un comando externo (git) sin quoting, fallaría. Los calls a
  git en los scripts usan `-- $visChanged` donde `$visChanged` puede contener rutas con espacios;
  `git diff HEAD -- "ruta con espacio"` funciona en bash pero en PS 5.1 pasado como array puede
  ser problemático.

**Riesgo efectivo:** Bajo a medio. El repo no tiene rutas de archivo (dentro de `fantasma/`) con
espacios, solo el directorio raíz. Los calls a git con `-- fantasma` no tienen el problema.

### 3.3 Exit codes [INFO-02]

Todos los scripts terminan con `exit 0` en todos los paths, incluyendo el path de bloqueo. El
bloqueo se comunica via JSON con `decision: 'block'`, no via exit code. Este es el comportamiento
correcto para hooks de Claude Code: la plataforma interpreta el JSON, no el exit code.

Sin embargo, si el JSON está malformado o vacío por error silencioso (ver 3.1), Claude Code puede
interpretar la ausencia de `decision: 'block'` como permiso de cerrar, pasando todos los gates.
No hay test de sanidad del output JSON.

---

## Sección 4 — Validez de la evidencia en mariana-stop [ALTO-02 extendido]

El gate de Mariana promete "evidencia verificable". En la implementación actual:

**Qué valida:**
- Que existe al menos un archivo en `qa_runs/` (cualquier subcarpeta, cualquier nombre)
  cuyo `LastWriteTime` sea mayor que el `LastWriteTime` del archivo visual modificado más reciente.

**Qué NO valida:**
- Que el archivo pertenezca a una carpeta Mariana (p.ej. `qa_runs/mariana-*/`)
- Que el archivo sea un screenshot, log de UI, o cualquier tipo de evidencia visual
- Que el archivo referencie los archivos visuales cambiados
- Que el archivo fue creado en la sesión actual (no en una sesión anterior)
- Que el archivo fue commiteado (qa_runs/* está en .gitignore, solo `qa_runs/README.md` se trackea)

**Caso de bypass real dado el estado actual del repo:**
Los archivos `qa_runs/charbel-20260630/` y `qa_runs/local-matrix-20260630-082708/` contienen
decenas de archivos de telemetría (`.txt`, `.json`, `.csv`) con timestamp 2026-06-30. Cualquier
cambio visual en `fantasma/viz/` o `fantasma/ui/` con `LastWriteTime` anterior al 2026-06-30
en disco haría que el gate de Mariana pasara automáticamente usando evidencia de Charbel, sin
que se haya hecho QA visual alguno.

En el escenario más probable (commit 73f5ac1 y archivos actuales del working tree), el commit
ocurrió el 2026-07-03 06:22 y los archivos Charbel son del 2026-06-30, así que los archivos
visuales en el working tree modificados por el commit tendrían timestamp mayor que los Charbel
y el gate de Mariana sí bloquearía. Sin embargo, si el usuario hace `git checkout` o un agente
reescribe el archivo visual con contenido idéntico, el timestamp se actualiza y la comparación
puede invertirse.

**El diseño documentado describe "evidencia verificable" pero el código implementa "cualquier
archivo qa_runs/ más nuevo que el cambio visual". La brecha entre ambos es significativa.**

---

## Sección 5 — Huecos de cobertura

### 5.1 Áreas sin gate de sesión [MEDIO-04]

| Área del repo | Tiene Stop hook? | Nota |
|---------------|-----------------|------|
| `fantasma/core/` | Sí (review-stop para code, escribano-stop para doc_bloquea) | Solo working tree |
| `fantasma/viz/` | Sí (los tres hooks) | Solo working tree |
| `fantasma/ui/` | Sí (los tres hooks) | Solo working tree |
| `fantasma/importers/` | Solo review-stop (no bloquea por doc) | No hay `doc_bloquea` en blast-radius |
| `fantasma/cli.py` | Solo review-stop (no bloquea por doc) | No hay `doc_bloquea` en blast-radius |
| `tests/` | Ninguno | Cambios en tests no disparan ningún hook |
| `docs/` | Ninguno (como fuente) | Solo como destino en blast-radius |
| `product/` | Ninguno | Solo el CI corre auditar.ps1 |
| `engineering/` | Ninguno | Solo el CI corre auditar.ps1 |
| `.claude/skills/` | Ninguno de bloqueo | Área "orquestacion" sin doc_bloquea |
| `tools/blast-radius.json` | Área "barreras" → bloquea por `docs/flujo-de-trabajo.md` | Correcto |
| `.github/workflows/` | Área "barreras" → mismo bloqueo | Correcto |
| `CHANGELOG.md`, `ROADMAP.md` | Ninguno como fuente | Solo el verificar.ps1 los chequea |

**Huecos más relevantes:**

- **`tests/`**: Si se eliminan tests, no hay ningún hook que lo detecte en sesión. El CI
  (`pytest`) lo detectaría si los tests que se eliminaron antes pasaban; si se eliminan tests de
  funciones también eliminadas, no se detecta.

- **`fantasma/importers/`**: Sin `doc_bloquea`, un cambio en los importadores (p.ej. cambio de
  formato CSV que rompa compatibilidad) puede commitearse sin que ningún hook bloquee por
  documentación. El CONTRIBUTING dice que Charbel valida importers, pero Charbel no tiene hook.

- **Código commiteado y pusheado con `--no-verify`**: Ningún hook de sesión vigila esto. El CI
  es la única barrera, y solo si los checks son *required* en el ruleset.

### 5.2 Brecha entre sesión y push [MEDIO-05]

El diagrama de capas en la doc:
```
EXPLORAS → CONSOLIDAS → hook pre-push (verificar.ps1) → CI en GitHub Actions
```

Hay una brecha entre "CONSOLIDAS" (commit en sesión) y "hook pre-push": en esa brecha, el código
commiteado no está cubierto por ningún Stop hook (ya pasó) ni por pre-push (aún no se ejecuta).
Si el usuario hace `git push` en una sesión diferente a la que generó el commit, el pre-push de
esa sesión sí corre. Pero si la misma sesión que commiteó también pushea sin cerrar y volver a
abrir, los Stop hooks no intervienen entre commit y push.

### 5.3 No hay hook para cierre de sesión sin commits [INFO-03]

Si una sesión genera trabajo pero el agente no commitea nada y cierra, los Stop hooks detectan
el working tree sucio y bloquean. Esto funciona bien. El problema es el caso inverso: una sesión
que commitea todo su trabajo y luego el Stop no ve nada — que es exactamente el incidente 73f5ac1.

---

## Sección 6 — Resumen de hallazgos

| ID | Severidad | Descripción breve |
|----|-----------|-------------------|
| CRITICO-01 | CRITICO | review-stop y mariana-stop ciegos ante código commiteado durante la sesión (líneas 17 y 54 respectivamente) — causa raíz del incidente 73f5ac1 |
| CRITICO-02 | CRITICO | escribano-stop ciego ante doc-drift de código ya commiteado (línea 27) — misma falla arquitectónica |
| ALTO-01 | ALTO | review-stop no verifica que `/code-review` se ejecutó; solo instruye al agente, que puede setear el marker directamente |
| ALTO-02 | ALTO | mariana-stop acepta cualquier archivo qa_runs/ como evidencia de QA visual, sin filtro de relevancia, tipo ni directorio |
| ALTO-03 | ALTO | mariana-stop usa LastWriteTime del archivo en disco, no del commit; un checkout o reescritura puede alterar la comparación |
| ALTO-04 | ALTO | `$ErrorActionPreference = 'SilentlyContinue'` en todos los scripts silencia fallos de git/JSON; si `git status` falla, los hooks pasan (exit 0 falso negativo) |
| MEDIO-01 | MEDIO | Markers (.review-marker, .mariana-marker) seteables sin hacer el trabajo; el hook enseña el comando exacto sin requerir intervención del PO |
| MEDIO-02 | MEDIO | stop_hook_active bypass: cualquier Stop desde dentro de un Stop activo omite los tres gates |
| MEDIO-03 | MEDIO | Call `git diff HEAD -- $visChanged` en mariana-stop con array de rutas puede fallar silenciosamente en PS 5.1 si los paths contienen caracteres especiales |
| MEDIO-04 | MEDIO | `fantasma/importers/` y `fantasma/cli.py` sin `doc_bloquea` en blast-radius; escribano-stop nunca bloquea por esas áreas |
| MEDIO-05 | MEDIO | Brecha de cobertura entre commit y push: si la sesión commitea y pushea sin cerrar, los Stop hooks no intervienen |
| BAJO-01 | BAJO | SHA1 de review-stop incluye nombre pero no contenido de archivos sin `git add`; cambio de contenido sin staging no re-invalida el marker |
| BAJO-02 | BAJO | escribano-stop sin marker: re-bloquea cada Stop si hay doc pendiente, incluso si el Escribano actualizó el doc pero lo commiteó (CRITICO-02 lo hace pasar silenciosamente) |
| INFO-01 | INFO | Areas `importers`, `cli`, `setup`, `orquestacion` documentadas como "§8" pero sin `doc_bloquea`; su gate es solo aviso, no bloqueo de sesión |
| INFO-02 | INFO | Todos los hooks salen con exit 0; output JSON vacío o malformado puede ser interpretado como no-bloqueo por Claude Code |
| INFO-03 | INFO | No hay hook para detectar "sesión que commitea todo y cierra" — diseño actual solo cubre working tree sucio |

---

## Sección 7 — Los 3 hallazgos más graves (con propuesta de mitigación)

### CRITICO-01 / CRITICO-02 — Hooks ciegos ante código commiteado durante la sesión

**Ruta afectada:** `.claude/hooks/review-stop.ps1` línea 17; `escribano-stop.ps1` línea 27;
`mariana-stop.ps1` línea 54.

**Mecánica exacta:** Los tres hooks salen con `exit 0` si `git status --porcelain` (total o por
área) devuelve vacío. Cuando el agente commitea código durante la sesión antes del Stop, el working
tree queda limpio y los tres gates pasan sin intervenir, independientemente de si el código fue
revisado, si los docs están actualizados, o si hay evidencia de QA visual.

**Incidente real:** Commit 73f5ac1 (2026-07-03 06:22), `fantasma/viz/overlay.py` 149 líneas,
entrada de otra IA, review-stop y mariana-stop ciegos.

**Mitigación posible:** Complementar el check de working tree con un check de commits recientes
vs la última referencia conocida. Por ejemplo, comparar `git log --oneline @{upstream}..HEAD`
y si hay commits de `fantasma/` en HEAD que aún no han pasado por review, disparar el gate.
Alternativamente, almacenar en un marker el SHA del commit HEAD al momento en que el hook pasó,
y re-validar en el próximo Stop si HEAD cambió. Esto requiere rediseño del approach de detección.

### ALTO-02 — Evidencia de Mariana no filtra por relevancia

**Ruta afectada:** `.claude/hooks/mariana-stop.ps1` líneas 66-68.

**Mecánica exacta:**
```powershell
$fresh = Get-ChildItem $qaDir -Recurse -File |
         Where-Object { $_.LastWriteTime -gt $lastVis } |
         Select-Object -First 1
if ($fresh) { exit 0 }
```
Cualquier archivo en `qa_runs/` — incluyendo telemetría de Charbel, reportes de auditoría,
archivos CSV de comparación de vueltas — satisface el gate si su timestamp es posterior al cambio
visual. La doc promete "evidencia verificable"; el código acepta cualquier dato de cualquier disciplina.

**Mitigación posible:** Restringir el check a subdirectorios que sigan la convención de Mariana
(`qa_runs/mariana-*/`) o a extensiones de evidencia visual (`.png`, `.jpg`, `.webp`, `.html`).
Alternativamente, requerir un archivo de manifiesto con nombre fijo (`qa_runs/mariana-*/EVIDENCE.md`)
que el agente cree explícitamente.

### ALTO-01 — review-stop no verifica que `/code-review` fue ejecutado

**Ruta afectada:** `.claude/hooks/review-stop.ps1` líneas 28-36 (contexto del bloqueo).

**Mecánica exacta:** El hook bloquea el cierre y en `additionalContext` dice al agente que ejecute
`/code-review` y luego use `Set-Content` para setear el marker. Pero el hook no tiene forma de
verificar que el agente realmente corrió `/code-review` antes de setear el marker; el agente puede
ignorar la instrucción de code-review, escribir el marker directamente, y el próximo Stop pasa.
No hay audit trail, no hay artefacto verificable de que el review ocurrió.

**Mitigación posible:** Requerir que el agente deposite un artefacto de review en una ubicación
predefinida (p.ej. `qa_runs/review-<sha>.md` con el output del review) y que el hook verifique
la existencia de ese archivo antes de aceptar el marker. Esto convertiría el gate en verificable
por artefacto, igual que Mariana (aunque Mariana también tiene la debilidad ALTO-02).

---

## Sección 8 — Estado de los marcadores al momento de la auditoría

- `.claude/.review-marker` existe: `8C104624E9E9B8976985C0CA393B7DE0D3BC1916`
- `.claude/.mariana-marker` existe: `5BE439F7929D3FE5D75BA5FE2A00350AE223FD9B`
- Ambos corresponden a diffs anteriores al estado actual del working tree (hay cambios sin
  commitear en `fantasma/viz/overlay.py` y `tests/viz/test_overlay.py` según `git status`).
  Los markers quedarán inválidos en el próximo Stop porque el SHA del diff actual diferirá.

---

*Fin del reporte. Ruta: `qa_runs/2026-07-03-auditoria-integral/fase3-hooks.md`*
