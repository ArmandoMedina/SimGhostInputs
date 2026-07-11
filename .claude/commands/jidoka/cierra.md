---
description: Cierra el sprint o la sesión — registra el estado, poda lo muerto, commitea la evidencia y prepara el release
argument-hint: "[sprint/sesión que se cierra]"
allowed-tools: Read, Bash
---

Estás **cerrando**. El cierre es donde el conocimiento se vuelve durable para la próxima sesión (tú en 6 meses, o una IA sin memoria). Lo que no quede en un artefacto se pierde.

Qué se cierra: **$ARGUMENTS**

## 1. Registra (el Registro se reparte por caducidad)

Cada cosa a su doc dueño (`kanban/lazo.md`):

- **`HANDOFF.md`** (efímero) — se **llena** al cerrar con el estado en vuelo y los pendientes; **se limpia** de lo ya atendido (una nota vieja que ya no es verdad es peor que no tenerla). Las decisiones de juicio del cliente van a su cola propia (`[PENDIENTE]` / `[DECIDIDA-REVISABLE]`).
- **`CHANGELOG.md`** — qué cambió, versión a versión. Si tocaste el ritual o los gates, aquí se registra (lo pide la ley: áreas `metodo` y `ritual`).
- **Un ADR** (`docs/decisions/`) por cada decisión no obvia — y **listada en su índice en el mismo commit** (único bloqueo duro). Si una regla gobierna decisiones futuras, asciende a un ADR: no la dejes enterrada en un checkbox.
- Si hubo sprint: llena la entrega con `@kit/.jidoka/templates/sprint-entrega.md` en `docs/sprints/` — su Kaizen (1-5 lecciones) es lo único que el siguiente `planea` lee completo.

## 2. Poda (la otra mitad de registrar)

Cierra con trazabilidad lo que ya no vive; borra solo el andamiaje que nunca fue contenido. **Si dudas entre borrar y marcar → marca.** El plan de trabajo del día (`/.jidoka/plan-actual.md`) se poda aquí.

## 3. Commitea la evidencia del Gemba (paso obligatorio, no cortesía)

El bulto de `qa_runs/` está gitignored. La evidencia **citada** desde HANDOFF/CHANGELOG se commitea selectivamente:

```
git add -f qa_runs/<corrida>/<archivo-citado>
```

En el linaje se descubrió una vez que 0 artefactos habían llegado a git — toda la evidencia era local y se habría perdido con el clon.

## 4. Verifica antes de subir

- Corre `./tools/probar-gate.ps1` (el motor sano) y `./tools/verificar.ps1` (sin drift de docs).
- **No uses `--no-verify` ni manipules el estado staged para pasar un hook** (disparo `no-verify-es-teatro`): el muro real es el required check server-side; saltar el hook local solo pospone y agranda el fallo.

## 5. Release (si el sprint entrega una versión)

El ritual, en 6 pasos (`CONTRIBUTING.md`): working tree limpio → cerrar la sección del CHANGELOG → commit `chore(release)` → tag anotado → push **con OK del dueño** → GitHub release. La versión vive en **un** solo lugar; todo lo demás deriva. La pregunta del salto: ¿rompe? MAJOR · ¿agrega? MINOR · ¿arregla? PATCH — en un repo de método, una reorganización que obliga a migrar notas es MAJOR.

> Autorizaciones vigentes (revisa el HANDOFF): publicar tag+release puede estar ya autorizado; **merges de PR y cambios de config/permisos requieren orden nombrada del cliente cada vez**. No los asumas.
