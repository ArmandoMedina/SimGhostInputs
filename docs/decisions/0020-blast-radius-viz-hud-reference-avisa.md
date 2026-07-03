# ADR 0020 — Blast-radius de `viz`: `hud-reference` AVISA, no BLOQUEA

- **Estado:** Aceptada
- **Fecha:** 2026-07-03
- **Relacionada con:** [ADR 0016](0016-gate-grafo-documentacion.md), [ADR 0019](0019-adopcion-homologacion-starter-v0.5.0.md)

## Contexto

El gate del blast-radius (§8 de `CONTRIBUTING.md`, espejo ejecutable en
`tools/blast-radius.json`) tenía a `docs/hud-reference.md` como **`doc_bloquea`** del
área `viz` (`fantasma/viz/*`). Es decir: **todo** cambio en `fantasma/viz/` exigía tocar
`docs/hud-reference.md`, sin distinguir si el cambio era visual o no.

`fantasma/viz/` no es solo el HUD: también aloja gráficas, composición de video, sincronía
de audio y pacenotes. Buena parte de su churn es **no-visual** — rendimiento del render,
refactors, manejo de encoding. Para esos cambios, `hud-reference.md` (anatomía y código de
colores del HUD) es un doc **irrelevante**, y el gate lo exigía igual.

Caso vivido hoy (2026-07-03): el commit `73f5ac1` optimizó el rendimiento del render del
overlay (salida pixel-idéntica pretendida, +85 líneas de test) y el gate local frenó el
push por no tocar un doc que ese cambio no afectaba
(auditoría integral, `qa_runs/2026-07-03-auditoria-integral/` — decisión PO-3;
`fase3-skills-blast-radius.md`).

## Decisión

En `tools/blast-radius.json`, área `viz`: mover `docs/hud-reference.md` de `doc_bloquea`
a `doc_avisa`, y anexar un `mensaje` al área que **pregunte por la naturaleza del cambio**:

> ¿el cambio es visual (color, panel, franja, layout del HUD)? entonces toca
> `docs/hud-reference.md` + `README` (tabla de colores) + `docs/ux-patterns.md` + **ADR
> nuevo**. Si es no-visual (perf, refactor, encoding), ninguno aplica.

`viz` queda **sin `doc_bloquea`**: el gate ahora **AVISA** (no bloquea) sobre los docs
visuales, dejando el juicio "¿esto era visual?" al autor y a Mariana. El muro duro sigue
siendo el CI (`audit` sobre el rango del PR, ADR 0019) para lo que sí deba bloquear.

## Razones

- **El bloqueo indiscriminado producía falsos positivos.** Exigir un doc visual a un cambio
  de rendimiento es fricción sin señal: entrena a saltarse el gate (`--no-verify`), que es
  peor que no tenerlo.
- **La verdadera pregunta es "¿el cambio es visual?", y esa es de juicio, no mecánica.** El
  `mensaje` la hace explícita en el aviso, que es donde el autor decide — en vez de fingir
  que un patrón de ruta puede contestarla.
- **No abre un hueco de gobernanza.** Un cambio visual real sigue teniendo su router (la
  fila §8, el rol Mariana con su hook de evidencia) y el CI `audit` como muro. Lo que se
  quita es un *bloqueo local* que disparaba en el caso equivocado.

## El camino que NO se toma (y por qué tienta)

- **Partir el área `viz` en `viz-visual` / `viz-no-visual` con matchers finos.** Tienta
  porque "resuelve el falso positivo en la máquina, sin depender del juicio". Se descarta:
  no hay una frontera de ruta limpia entre lo visual y lo no-visual dentro de `overlay.py`
  (el mismo archivo hace layout del HUD y encoding); el matcher tendría que adivinar por
  contenido del diff, no por path. Es sobre-ingeniería para un repo personal — el `mensaje`
  que pregunta logra el 90% del valor con cero complejidad de matcher.
- **Dejarlo como `doc_bloquea` y "aguantar" el falso positivo.** Tienta por no tocar la ley.
  Se descarta: ya causó un bloqueo real hoy y el costo de un gate que llora en falso es que
  se ignora.

## Consecuencias

- **Se gana:** los cambios no-visuales de `viz` (perf, refactor, encoding) dejan de chocar
  contra `hud-reference.md`; el aviso educa sobre qué tocar **si** el cambio es visual.
- **Se pierde / costo:** el `mensaje` es de área, así que se anexa a **todos** los avisos de
  `viz` (también a `ux-patterns.md` y a los `product_avisa`), no solo al de `hud-reference`.
  Es ruido tolerable — el matcher (starter v0.5.0) solo soporta `mensaje` por área, no por
  doc; afinar eso sería la sobre-ingeniería que este ADR descarta.
- **Se apoya en:** que el CI `audit` sea *required check* (acción de PO pendiente del ADR
  0019) para que el muro duro exista donde ya no bloquea el gate local.
