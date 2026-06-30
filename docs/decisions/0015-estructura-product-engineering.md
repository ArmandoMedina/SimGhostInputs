# ADR 0015 — Adoptar la estructura product/ + engineering/ (reclasificar el repo a mixto)

- **Estado:** Aceptada
- **Fecha:** 2026-06-29

## Contexto

El repo nació code-first: una herramienta Python de un autor, con el QUÉ (alcance, nicho,
principios) en `PRODUCT_BRIEF.md` plano y el CÓMO (algoritmos, formato de datos, HUD) disperso en
`docs/` (`formato-datos.md`, `hud-reference.md`, `guia-usuario.md`, `ux-patterns.md`,
`casos-de-uso.md`). Esa forma plana funcionó mientras el producto fue una idea acotada.

Ya no lo es. Hay **dos productos** (análisis post-tanda y overlay de video) sobre un motor común,
varias áreas funcionales con reglas propias (importación, normalización/comparación, detección de
curvas, visualización/HUD, sincronía, composición, UI, desgaste), un backlog vivo con specs por
diseñar (drill-down, histórico, pace notes, importadores) y la intención de orquestar el trabajo
con varios subagentes. Cuando el QUÉ crece, mantenerlo plano hace que: (1) las reglas de negocio y
los criterios de aceptación queden implícitos en el código y los tests, no declarados; (2) un
subagente que implementa no tenga un "contrato" navegable de qué debe cumplir; (3) el grafo de
"qué capacidad soporta qué módulo de qué dominio" no exista para razonar el blast-radius.

La metodología de `project-starter` ya está adoptada en su **capa de automatización** (barreras,
doc-gate §8, hooks de sesión, casting). Falta su **estructura física del QUÉ/CÓMO**.

## Decisión

Se **reclasifica el repo de code-first a mixto** y se adopta la estructura completa de
`project-starter`:

- **`product/`** — la jerarquía funcional (ecosistema → solución → dominio → módulo → capacidad),
  más `requerimientos/` (bandeja de entrada + backlog) y `procesos/`. Poblada con el **contenido
  real** del repo, no con notas de ejemplo. Las capacidades llevan criterios de aceptación Gherkin,
  derivados de los tests que ya existen.
- **`engineering/`** — `arquitectura.md`, `pruebas.md`, `componentes/`, `especificaciones/`,
  `modelos-de-datos/`. Absorbe, **respetando SSOT**, lo técnico hoy disperso en `docs/`.
- **`templates/`** — los formatos canónicos para copiar.
- **`HANDOFF.md`** — relevo de sesión (continuidad efímera: dónde voy, qué falta).

## Razones

- **Un mixto sí llena la jerarquía.** La guía del método (`empezar-de-cero`, Paso 1) reserva la
  jerarquía completa para repos mixtos/regulados; un code-first puro se quedaría en el brief. El
  repo cruzó ese umbral: dos productos, varias áreas con reglas, backlog con specs, trabajo
  multiagente. La estructura deja de ser ceremonia y pasa a ser el contrato que los subagentes leen.
- **Separar el QUÉ del CÓMO es la regla #1.** Hoy están mezclados en `docs/`; el grafo product/
  ↔ engineering/ los separa y vuelve auditable el blast-radius del doc-gate §8.
- **Habilita el objetivo rector:** que ningún doc/flujo obligatorio se le pase a un subagente. Eso
  exige que cada área tenga un doc dueño explícito y enlazado — justo lo que la estructura crea.

## El camino que NO se toma (y por qué tienta)

- **Quedarse code-first y no crear `product/`/`engineering/`.** Tienta por simplicidad y porque
  "el código ya lo dice todo". Se descarta: con dos productos y trabajo delegado, lo implícito se
  bifurca (una sesión/IA reconstruye distinto). El método es honesto en que para un code-first puro
  esto **sería de más** — pero el repo ya no lo es. Esta es la bifurcación que el ADR fija: no
  volver a tratar un repo mixto como si fuera un script de una vez.
- **Crear el árbol con notas de ejemplo (como la plantilla) y llenarlas "después".** Se descarta:
  notas de ejemplo que hay que borrar son ruido; la estructura nace poblada con lo real o no nace.
- **Mover todo `docs/` técnico dentro de `engineering/` de golpe.** Se descarta: rompería los
  dueños SSOT que el doc-gate §8 ya vigila (`formato-datos.md`, `hud-reference.md`). La migración es
  gradual y cada doc conserva o cede su autoridad de forma explícita, no por mudanza ciega.

## Consecuencias

- **Se gana:** el QUÉ y el CÓMO separados y navegables; capacidades con criterios de aceptación
  declarados; un grafo que vuelve auditable el blast-radius; un contrato que los subagentes leen
  antes de implementar.
- **Se pierde / costo:** trabajo de migración real (redistribuir `docs/` técnico a `engineering/`
  cuidando SSOT, derivar capacidades de los tests). Se hace por fases, cada una verde.
- **Pendiente de validar:** el **gate determinista** se extiende para cubrir la estructura nueva
  (`product/capacidades`, `engineering/`), con la matriz §8 como fuente única que leen hook,
  `verificar.ps1`, un nuevo `tools/auditar.ps1` y el CI — **sin** archivos de auto-firma. Eso es una
  decisión propia que se registrará en su ADR al implementar la Fase 3.
- Al tocar las barreras (gate, hooks, CI) en esa fase, el doc-gate §8 obliga a actualizar
  `docs/flujo-de-trabajo.md` (barreras → su doc dueño).
