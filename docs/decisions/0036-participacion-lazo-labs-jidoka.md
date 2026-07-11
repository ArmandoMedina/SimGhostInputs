# ADR 0036 — SGI participa del lazo de sincronización labs↔Jidoka (primer consumidor)

- **Estado:** Aceptada (2026-07-11)

## Contexto

Los [ADR 0034](0034-convergencia-nucleo-jidoka.md) y [0035](0035-homologacion-personas-asiento-neutral.md)
convergieron la **maquinaria de método** de SGI al núcleo neutral de
[Jidoka](https://github.com/ArmandoMedina/jidoka) **a mano**: dos auditorías de homologación, diff pieza
por pieza, prosa de las personas alineada al asiento neutral. Fue trabajo manual y sin memoria — si Jidoka
mejora el auditor o un hook mañana, nada le avisa a SGI, y nada garantiza que la re-bajada no pise lo que
SGI diverge legítimamente por dominio (su `verificar.ps1` con ruff/pytest) o estética (su casting de
personas).

Jidoka acaba de construir el **lazo de sincronización labs↔Jidoka**: *la lección sube, la máquina baja*.
Cada hijo lleva un **sello** (`tools/jidoka-motor.json`) que registra de qué versión de Jidoka viene su
maquinaria y el hash de cada pieza de motor; un **canal de subida** (`tools/reportar-leccion.ps1`) para
reportar lecciones de campo hacia arriba; y un **aviso de estado** (`tools/estado-motor.ps1`) que compara
el sello contra un checkout de Jidoka y dice si estás al día o atrás. Ya no hay que converger a ciegas y a
mano: hay máquina.

## Decisión

**SGI participa del lazo como su primer consumidor.** En concreto:

1. **Sello retroactivo** — se siembra `tools/jidoka-motor.json` con `version: "0.10.1-beta"` (el punto de
   convergencia real de SGI, ADR 0034/0035) y el SHA256 de las piezas **mecánicas** que SGI tiene hoy
   (`verificar/auditar/auditar-radius/probar-*`, `settings.json`, los cuatro hooks, `pre-push`, los
   workflows). **No** se sellan la ley `blast-radius.json`, `product/`, las skills-persona ni los comandos:
   son **instancia/estética**, no motor. El sello es la **línea base honesta** para futuros `-Actualizar`.
2. **Canal de subida sembrado** — se copian byte-idénticos desde Jidoka `tools/reportar-leccion.ps1` y la
   guía `docs/guias/reportar-leccion-a-jidoka.md`, más `tools/estado-motor.ps1` para consultar la
   divergencia. SGI ya puede subir lecciones y consultar su estado.
3. **El motor de SGI NO se auto-actualiza** — la mecánica que SGI diverge por dominio (`verificar.ps1`
   corre ruff+pytest+cobertura; `auditar.ps1` cubre `product/ + engineering/`; `pre-push` en bash con
   fallback) y por estética (casting de personas, comandos sin namespace `jidoka/`) **se preserva**. La
   convergencia de mecánica común se hará **cuando exista la costura**, corriendo `-Actualizar` en una rama
   y **revisando el diff** (el diff es la revisión), no automáticamente.

Se documenta la evidencia de arranque del lazo en `qa_runs/lazo-sync-20260711/`: reporte de divergencias
pieza por pieza, salida de `estado-motor.ps1`, y lecciones draft pendientes de presentar (excepción de QA
visual con nombre; `probar-gate.ps1` como ítem de bajada; y dos cosechadas del ADR 0019).

## Razones

- La convergencia manual de ADR 0034/0035 **no tiene memoria ni mecanismo**: el sello + el canal + el aviso
  de estado convierten "converger cuando alguien se acuerde" en "el lazo te dice cuándo hay algo que bajar y
  qué es tuyo que no debe pisarse".
- El sello es **honesto por diseño**: registra que el motor de SGI corresponde a Jidoka 0.10.1-beta. Si
  Jidoka avanza, `estado-motor` lo detecta y ofrece la bajada — sin ejecutarla, porque bajar sobre un motor
  divergente exige juicio.
- Sembrar el canal de subida **cuesta casi nada y desbloquea el flujo inverso**: las lecciones que SGI paga
  en campo (ver `qa_runs/lazo-sync-20260711/`) ya tienen ruta para volverse mejoras del método común.

## El camino que NO se toma (y por qué tienta)

- **Auto-`-Actualizar` del motor en cada divergencia detectada:** tienta porque cerraría la brecha sin
  intervención. Pero **clobrearía el `verificar.ps1` de SGI** (perdería ruff/pytest/cobertura), su
  `auditar.ps1` (perdería `engineering/`), su `pre-push` en bash, y potencialmente su casting. La regla del
  cliente es explícita: la mecánica común converge, la divergencia de dominio/estética **se preserva, no se
  pisa**. Por eso el lazo **avisa** (estado-motor no bloquea, exit 0 siempre) y la bajada se decide en rama
  con diff a la vista.
- **No sellar nada hasta la próxima convergencia real:** dejaría a SGI sin línea base — el primer
  `-Actualizar` no tendría contra qué medir qué tocó el humano vs qué re-siembra Jidoka. El sello
  retroactivo es justo esa línea base.

## Consecuencias

- SGI tiene sello, canal de subida y aviso de estado. El motor no cambió de comportamiento: **cero
  regresión** (solo se **añadieron** archivos; el `verificar.ps1`/`auditar.ps1`/hooks de SGI no se tocaron;
  pytest sigue verde).
- **Pendiente (decisión humana):** al correr `estado-motor.ps1` contra el checkout local de Jidoka, este ya
  reporta **0.11.0-beta** (una rama en-vuelo, sin publicar). El aviso dice "atrás" — el lazo funcionando.
  Cuando 0.11.0-beta se libere, evaluar la bajada en rama. Detalle en
  `qa_runs/lazo-sync-20260711/divergencias.md`.
- **Sigue pendiente (de ADR 0035):** portar `probar-gate.ps1` requiere que `verificar.ps1` acepte
  `-Cambiados` — ahora es un ítem de **bajada por el lazo**, no un parche manual (ver
  `qa_runs/lazo-sync-20260711/leccion-probar-gate-convergencia.md`).
