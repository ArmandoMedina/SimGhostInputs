# ADR 0011 — Cablear el rol Mariana (UX visual); Charbel se queda en los tests

- **Estado:** Aceptada
- **Fecha:** 2026-06-27

## Contexto

En v0.11.0 se construyó el sistema de roles ([CONTRIBUTING §8](../../CONTRIBUTING.md#8-mantenimiento-de-documentación)). Quedaron **declarados cuatro roles validadores** (Reviewer, Escribano, Charbel, Mariana) pero **solo dos auto-cableados** como hooks de sesión: `review-stop` (código sin revisar → `/code-review`) y `escribano-stop` (doc-drift §8 → skill Escribano). La regla escrita fue deliberada: *"Charbel y Mariana se construyen cuando un cambio real los pida"* — no se adelanta maquinaria antes de necesitarla.

Llegó el primer cambio que lo pide: un bug visual en la UI (los botones «Elegir este / Seleccionado» de `step0.py` quedan desalineados entre tarjetas porque cada uno se ancla al final de su columna, no a una línea base común). **Se coló sin que nada lo atrapara**, por dos huecos concretos:

1. **No hay checkpoint visual.** `review-stop` ve bugs de código y `escribano-stop` ve docs, pero **ninguno pregunta "¿la UI se ve bien?"**. Ese es el asiento de Mariana, y no está cableado.
2. **`escribano-stop` ni siquiera vigila `fantasma/ui/`** — solo `core/`, `viz/` y las barreras. La §8 dice que un cambio de UX en `fantasma/ui/` es dueño de `guia-usuario.md`, pero el hook no lo enfila.

## Decisión

**Cablear Mariana** como hook de sesión `mariana-stop`: al detectar cambios sin commitear en `fantasma/viz/` o `fantasma/ui/`, frena el cierre y devuelve el control al PO con un **checkpoint visual** (abrir `fantasma ui` / revisar el HUD a ojo antes de dar por terminado). Auto-terminante con marcador, igual que `review-stop`. De paso, **extender `escribano-stop` a `fantasma/ui/` → `guia-usuario.md`** para cerrar el hueco de doc.

**NO cablear Charbel.** Su validación (correctitud de telemetría) ya vive en `pytest` + el doc-gate `core/` → `formato-datos.md`. Se queda declarado en la §8, sin hook.

## Razones

- **Mariana ataca un hueco demostrado, no hipotético.** El bug es la prueba: cambios visuales en `viz/`/`ui/` no tenían ninguna barrera. Es lo que la regla de v0.11.0 anticipó ("cuando un cambio real lo pida").
- **El checkpoint respeta el límite semántico del flujo.** Ningún chequeo determinista garantiza que algo "se vea bien" (ver [flujo-de-trabajo.md §4](../flujo-de-trabajo.md) y [ADR 0003](0003-testing.md)). Por eso Mariana **no intenta detectar** el desalineado: solo **recuerda** hacer el QA visual que sí lo cacha. Recordatorio, no portero — coherente con "determinismo bloquea; juicio aconseja".
- **Charbel sería redundante y caro.** La §8 ya advierte: *"ese asiento es de los tests; no pongas la IA a validar la telemetría en bloque"*. Un hook de Charbel duplicaría lo que `pytest` ya hace y caería en el "sobre-orquestar" que el propio playbook marca como el error caro.

## El camino que NO se toma (y por qué tienta)

- **Cablear también a Charbel "para completar los cuatro".** Tienta por simetría (si cableamos uno, cableemos los dos). Se descarta porque su asiento ya está ocupado por los tests deterministas; un hook de IA encima no añade señal, añade ruido y latencia, y contradice la §8.
- **Hot-wirear el hook sin registrar la decisión.** Tienta por velocidad (el bug urge, "solo es un hook"). Se descarta porque cambiar las barreras/gobernanza **es** una decisión (§8 la enruta a Architect): saltársela es justo el patrón que dejó a Mariana sin cablear sin que quedara asentado el porqué. Sin este ADR, una sesión futura no sabría por qué Charbel quedó fuera y reintentaría cablearlo.
- **Hacer que Mariana intente detectar problemas visuales sola** (heurísticas sobre el layout). Tienta porque "automatizar todo" suena mejor. Se descarta: lo visual es juicio humano; una heurística daría falsos positivos/negativos y falsa confianza.

## Consecuencias

- **Se gana** una barrera (recordatorio) para todo cambio en `viz/`/`ui/`, y se cierra el hueco doc `ui/` → `guia-usuario.md` en `escribano-stop`.
- **Se gana** un precedente claro: los roles se cablean *cuando un cambio real lo pide*, y cablear barreras pasa por ADR.
- **Se pierde/asume** una fricción extra al cerrar sesiones que tocan UI (un checkpoint más). Es el costo buscado: el QA visual deja de depender de que alguien se acuerde.
- **Queda como límite conocido:** Mariana **no** valida que la UI esté bien, solo obliga a mirarla. La aceptación visual sigue siendo del PO.
- **Pendiente de validar:** que `mariana-stop` no entre en bucle (usa el mismo patrón de marcador/`stop_hook_active` ya probado en `review-stop`).
