---
description: Corre el demo del incremento y produce la evidencia real en qa_runs/ para que el cliente lo verifique con sus ojos
argument-hint: "[qué incremento/rebanada se va a demostrar]"
allowed-tools: Read, Bash
---

**Gemba: ir a donde el trabajo ocurre.** El cliente no revisa el código ni el PR — revisa el **demo corriendo**. Este comando produce la evidencia de que el incremento funciona, saliendo del pipeline real del producto, no de un script por fuera.

Incremento a demostrar: **$ARGUMENTS**

## La regla madre

> **Un archivo que diga "validé y todo bien" NO es evidencia** — eso es un acta, y las actas se auto-firman. La evidencia son los **artefactos de la corrida** (disparo `evidencia-no-palabra`). El gate y el cliente leen el artefacto, no tu palabra.

## Qué hacer

1. **Corre el demo desde el producto real, E2E.** No armes el resultado por otra vía: un script ad-hoc que fabrica la salida no prueba que el producto la genere igual, y diverge en silencio. Usa el pipeline real (los tests reales, el comando real, la app real).
2. **Deja los artefactos en `qa_runs/<rol|propósito>-<YYYYMMDD-HHMMSS>/`** (ej. `qa_runs/revisor-visual-20260710-170512/`):
   - Los artefactos reales: capturas, snapshots renderizados, logs, tablas `entrada → salida-obtenida → esperada`.
   - Un `LOG.md` que declare: **fecha, rama, método reproducible**, y los resultados como tabla `# | Caso | Check | Resultado (N/N)`.
   - **Datos 100 % sintéticos por defecto** — perfiles ficticios, montos inventados; ninguna captura carga datos reales, ni en repos privados. *Excepción de dominio con nombre* (disparo `excepciones-cableadas`): si lo sintético no ejercita el artefacto —un render/HUD sobre telemetría real—, corre con dato real **fuera del repo** y commitea solo capturas; **nómbrala**, no la toleres en silencio.
3. **El veredicto NO vive en `qa_runs/`.** Va a `HANDOFF.md` o `CHANGELOG.md` **citando** el directorio de la corrida. Artefacto y veredicto se separan a propósito.

## El checkpoint es del cliente

La evidencia es el **insumo** de la revisión, no la revisión. Para lo visual/subjetivo, **"¿se ve bien?" la responde el cliente con sus propios ojos** — tú surtes las capturas y dejas la corrida lista. Para lo objetivo, el veredicto lo da el artefacto (test verde, tabla N/N).

Recuerda: el bulto de `qa_runs/` está gitignored; **commitear la evidencia citada es paso obligatorio del cierre** (`/jidoka:cierra` lo hace con `git add -f`), no cortesía — en el linaje se descubrió una vez que 0 artefactos habían llegado a git.
