# Plan de trabajo — [tarea]

> Para una tarea larga que puede morir a media ejecución (compactación, cierre de sesión). **Efímero, con hogar persistente (ADR 0006):** vive en `/.jidoka/plan-actual.md` — fuera de git (no se versiona, historial limpio) pero en disco, así que **sobrevive la compactación**. `/jidoka:arranca` lo lee al abrir; `/jidoka:cierra` lo poda al terminar. Al retomar, verifica contra el código real, no contra el resumen de la sesión anterior (los resúmenes de compactación mienten — disparo `desconfia-de-la-compactacion`). No lo confundas con el plan de SPRINT (`docs/sprints/`), que **sí** se versiona: aquel es el contrato aprobado; este es tu andamiaje del día.

## Objetivo

[Una frase.]

## Pasos (cada uno commiteable y verde)

- [ ] Paso 1
- [ ] Paso 2

## Decisiones tomadas en el camino

[Registro corto. Si alguna es permanente, se convierte en ADR antes de borrar este plan.]

## Para retomar en frío

[Lo que la próxima sesión necesita saber que no está en el repo: en qué paso vas, qué está a medias, qué NO tocar.]
