---
tipo: plan-de-trabajo
estado: en_curso
---

# Plan — <tarea, en una frase>

> **Para qué es esta plantilla (ADR 0019, enmienda 2026-07-03):** una tarea larga con IA muere a media ejecución (tokens, contexto compactado, subagente caído) — y lo no escrito se pierde (pasó aquí: "me quedé sin tokens" a media migración NiceGUI). El plan te da un guion para no perder el hilo. Al retomar: **verifica contra el código real**, no contra el resumen de la sesión anterior (los resúmenes de compactación pueden mentir — caso `storage.user` vs `storage.client`).
>
> **El plan es EFÍMERO y NO se versiona** (decisión del PO, 2026-07-03; ADR 0019 §Enmienda). Vive en la **sesión / el task-tracker** mientras la tarea corre — **no** se commitea, ni siquiera a `docs/planes/`. Al morir la tarea, lo durable se reparte:
>
> - dejó una **decisión** (elegiste un camino sobre otro) → va a un **ADR**;
> - dejó **estado en vuelo** al morir la sesión (rama, último paso, qué NO tocar) → va al **HANDOFF**;
> - resultado liberable → **CHANGELOG**.
>
> Cuando la tarea cierra, el plan simplemente se descarta: su valor ya migró a ADR/HANDOFF/CHANGELOG.

## Objetivo

<Qué queda funcionando al terminar, verificable. No "mejorar X": "X hace Y y lo prueba Z".>

## Pasos (cada uno commiteable y verde)

- [ ] <Paso 1 — con su verificación: qué comando/test lo confirma>
- [ ] <Paso 2>

## Decisiones tomadas en el camino

<Si al ejecutar apareció una DECISIÓN (elegiste un camino sobre otro), anótala aquí con una línea… y conviértela en ADR antes de cerrar. No la dejes enterrada en el plan.>

## Para retomar en frío

<Lo que una sesión nueva necesita: rama, último paso completado, qué comando corre el estado actual, qué NO tocar. Verificable contra el repo, no contra memoria.>
