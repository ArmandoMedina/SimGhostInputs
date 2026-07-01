---
tipo: plan-de-trabajo
estado: en_curso
---

# Plan — <tarea, en una frase>

> **Para qué es esta plantilla (ADR 0019):** una tarea larga con IA muere a media ejecución (tokens, contexto compactado, subagente caído) — y lo no escrito se pierde (pasó aquí: "me quedé sin tokens" a media migración NiceGUI). El plan vive en el repo **antes** de ejecutar; cada paso commiteable se commitea al terminar. Al retomar: **verifica contra el código real**, no contra el resumen de la sesión anterior (los resúmenes de compactación pueden mentir — caso `storage.user` vs `storage.client`). Al cerrar la tarea completa: el resultado va a CHANGELOG/HANDOFF y este plan **se borra** (es efímero; si dejó una decisión, esa va a un ADR).
>
> Dónde va: `docs/planes/<fecha>-<slug>.md`.

## Objetivo

<Qué queda funcionando al terminar, verificable. No "mejorar X": "X hace Y y lo prueba Z".>

## Pasos (cada uno commiteable y verde)

- [ ] <Paso 1 — con su verificación: qué comando/test lo confirma>
- [ ] <Paso 2>

## Decisiones tomadas en el camino

<Si al ejecutar apareció una DECISIÓN (elegiste un camino sobre otro), anótala aquí con una línea… y conviértela en ADR antes de cerrar. No la dejes enterrada en el plan.>

## Para retomar en frío

<Lo que una sesión nueva necesita: rama, último paso completado, qué comando corre el estado actual, qué NO tocar. Verificable contra el repo, no contra memoria.>
