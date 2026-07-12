# Recursos del proyecto — lo que la sesión no debe preguntarte

> Recursos externos que toda sesión necesita y que no se deducen del código (ADR 0019, homologado del starter v0.5.0). **Por qué existe:** la ruta del material de pruebas se dictó 3 veces en 3 sesiones, y la cuenta equivocada de `gh` tumbó un PR. `/jidoka:arranca` lee este archivo al abrir. Si un dato caduca, actualízalo aquí. **Nunca pegues secretos** (va al repo): solo punteros.

## Material de pruebas / datos reales

| Qué | Dónde | Notas |
|---|---|---|
| Material de telemetría real (MoTeC, videos, vueltas) | `C:\Repositorio personal\Paterial para test (no es un repo)` (PC original) · `C:\Users\jose_\Downloads\Pruebas finales` (PC de jose_) | La ruta lleva espacios — va entre comillas. Es **por máquina**: la ruta cambia según la PC. Usarlo para QA con casos reales (no solo sintéticos). |
| Datos sintéticos de la suite | `tests/` (fixtures) | Para tests deterministas; el material real es para QA/validación de Charbel y Mariana. |

## Cuentas e identidades

| Servicio | Cuenta que usa ESTE repo | Notas |
|---|---|---|
| GitHub (`gh`) | **ArmandoMedina** (personal) para PRs/releases/API | Hay 2 cuentas logueadas; la de trabajo (`Armandomedina9705`) suele estar activa y **no es collaborator** aquí → `gh auth switch --user ArmandoMedina` antes, y devolver a `Armandomedina9705` al terminar. Verifica con `gh auth status`. |

## Hooks globales de la cuenta (fuera del repo, gobiernan a Mau)

| Hook | Dónde vive | Qué hace | Por qué es de máquina/cuenta y no del repo |
|---|---|---|---|
| `agent-concurrency-gate.ps1` | `~/.claude/hooks/agent-concurrency-gate.ps1`, cableado en `~/.claude/settings.json` (`hooks.PreToolUse`, `matcher: "Agent"`) | Tope determinista: cuenta lanzamientos con `isolation: "worktree"` (agentes "pesados" — exploran+codean+testean+abren PR) en los últimos 20 min; al 4º dentro de esa ventana, **deniega** el `Agent` con motivo explícito. Agentes livianos (`Explore`, research sin worktree) nunca cuentan. | Vive en `~/.claude/`, no en `.claude/` del repo — gobierna la cuota de la **cuenta API**, no algo del código. Nace del incidente 2026-07-09: 5 subagentes worktree en paralelo agotaron la cuota de sesión de golpe (ver [ADR 0019, enmienda 2026-07-09](decisions/0019-adopcion-homologacion-starter-v0.5.0.md)). |

> Si migrás de máquina o reinstalás `~/.claude/`, este hook **no viaja con el repo** — hay que
> recrearlo (el script y el bloque de `settings.json` están documentados en la enmienda del
> ADR 0019 arriba, con el contenido completo si hace falta reconstruirlo).

## Máquinas y entornos

| Máquina | Para qué | Cómo llegar |
|---|---|---|
| Laptop de desarrollo (esta) | Dev, builds, QA de UI | local. Windows 11, PS 5.1 — ver el recetario `docs/entorno-windows-powershell51.md`. |
| PC potente (host `SERVER`) | Pruebas limpias, cómputo pesado, builds largos | Vía el agente Oscar (infra) o SSH; pedir al PO si está encendida. |
| AMS2 en pista | QA real de pacenotes (tonos en los metros correctos, voz) | Requiere sesión de sim del PO — se agenda, no se automatiza. |

## Relacionado con

- [flujo-de-trabajo](flujo-de-trabajo.md)
- [HANDOFF](../HANDOFF.md)
