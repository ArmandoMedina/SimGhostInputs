# Recursos del proyecto — lo que la sesión no debe preguntarte

> Recursos externos que toda sesión necesita y que no se deducen del código (ADR 0019, homologado del starter v0.5.0). **Por qué existe:** la ruta del material de pruebas se dictó 3 veces en 3 sesiones, y la cuenta equivocada de `gh` tumbó un PR. `/arranca` lee este archivo al abrir. Si un dato caduca, actualízalo aquí. **Nunca pegues secretos** (va al repo): solo punteros.

## Material de pruebas / datos reales

| Qué | Dónde | Notas |
|---|---|---|
| Material de telemetría real (MoTeC, videos, vueltas) | `C:\Repositorio personal\Paterial para test (no es un repo)` | La ruta lleva espacios y el typo "Paterial" es literal — va entre comillas. Usarlo para QA con casos reales (no solo sintéticos). |
| Datos sintéticos de la suite | `tests/` (fixtures) | Para tests deterministas; el material real es para QA/validación de Charbel y Mariana. |

## Cuentas e identidades

| Servicio | Cuenta que usa ESTE repo | Notas |
|---|---|---|
| GitHub (`gh`) | **ArmandoMedina** (personal) para PRs/releases/API | Hay 2 cuentas logueadas; la de trabajo (`Armandomedina9705`) suele estar activa y **no es collaborator** aquí → `gh auth switch --user ArmandoMedina` antes, y devolver a `Armandomedina9705` al terminar. Verifica con `gh auth status`. |

## Máquinas y entornos

| Máquina | Para qué | Cómo llegar |
|---|---|---|
| Laptop de desarrollo (esta) | Dev, builds, QA de UI | local. Windows 11, PS 5.1 — ver el recetario `docs/entorno-windows-powershell51.md`. |
| PC potente (host `SERVER`) | Pruebas limpias, cómputo pesado, builds largos | Vía el agente Oscar (infra) o SSH; pedir al PO si está encendida. |
| AMS2 en pista | QA real de pacenotes (tonos en los metros correctos, voz) | Requiere sesión de sim del PO — se agenda, no se automatiza. |

## Relacionado con

- [flujo-de-trabajo](flujo-de-trabajo.md)
- [HANDOFF](../HANDOFF.md)
