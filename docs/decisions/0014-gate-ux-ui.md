# ADR 0014 — Gate de UX/UI: lo medible bloquea, lo subjetivo es checkpoint de Mariana

- **Estado:** Aceptada
- **Fecha:** 2026-06-28

## Contexto

El repo ya exige que pasen barreras deterministas (lint, formato, tests) para subir código, y un
doc-gate para los docs. Falta el equivalente para la **interfaz**: hoy un cambio de UI o de HUD
puede subir sin que nada verifique su calidad más allá del smoke visual del Paso 0 (ADR 0012). Se
pidió "que las pruebas de UX/UI pasen por algo similar a los tests para subir cambios".

La tentación es montar un "gate de UX" que apruebe/rechace la interfaz por máquina. Pero la calidad
de UX tiene dos naturalezas distintas y mezclarlas rompe el gate:
- **Medible:** ¿se movió el layout?, ¿hay contraste suficiente?, ¿existen los elementos esperados?,
  ¿se ve el estado de carga? Esto es determinista.
- **Subjetiva:** ¿se ve profesional?, ¿el flujo se siente claro?, ¿el HUD es legible sobre *este*
  video? Esto es juicio humano (el límite semántico que ya reconoce el ADR 0003).

## Decisión

Se adopta un **gate de UX/UI en tres capas** que respeta el principio del repo *determinismo
bloquea, juicio aconseja* (documentado en [`docs/ux-patterns.md`](../ux-patterns.md)):

1. **Determinista → BLOQUEA en CI** (como los tests): smoke visual de layout por pantalla
   (Playwright, baseline Ubuntu), aserciones estructurales (Streamlit AppTest) y contraste WCAG de
   los colores propios.
2. **Juicio → ACONSEJA** (checkpoint del rol **Mariana**, vía el hook `mariana-stop`): una checklist
   de heurísticas que **frena el cierre y obliga a mirar**, pero cuyo resultado vuelve al PO; no es
   auto-pase ni portero de lo irreversible.
3. **Local → AVISA** temprano (`verificar.ps1`, skipea limpio sin Chromium); el CI es el que bloquea.

La rúbrica (10 heurísticas) y el detalle del gate viven en `docs/ux-patterns.md`.

## Razones

- **Coherencia con el resto del repo:** misma filosofía que código y docs — lo automatizable se
  automatiza y bloquea; lo que depende de juicio se enruta a un rol, no se finge determinista.
- **Un gate subjetivo automático se ignora:** si la máquina rechaza por "no se ve bien", produce
  falsos rojos, el equipo aprende a saltárselo y el gate pierde autoridad. Peor que no tenerlo.
- **No medir lo medible deja pasar regresiones reales:** el bug de botones desalineados (ADR 0011)
  era detectable por máquina — por eso el smoke visual existe. Extenderlo es barato y atrapa esa clase.

## El camino que NO se toma (y por qué tienta)

- **Un "score de UX" automático que bloquee todo (incl. lo subjetivo).** Tienta porque suena a
  "calidad garantizada por CI", pero convierte juicio en portero: falsos rojos, frustración y
  evasión del gate. La calidad subjetiva **no** es determinista; tratarla así la degrada.
- **Dejar la UX 100% a revisión humana sin nada automático.** Tienta por simplicidad, pero repite
  el dolor #1 del repo (lo que depende de que alguien se acuerde, se cuela): las regresiones de
  layout y contraste son medibles y deben atraparse solas.
- **Validar el smoke visual en Windows como verdad canónica.** Se descartó: el render difiere por OS;
  la verdad canónica es Ubuntu (CI), como ya fija el ADR 0012. Windows sirve como señal local con
  tolerancia generosa, no como árbitro.

## Consecuencias

- **Se gana:** un estándar de interfaz explícito y un gate que mezcla lo automático (bloquea) con el
  checkpoint humano (aconseja), sin pretender que la máquina juzgue el gusto.
- **Se pierde / costo:** hay que construir las piezas que aún no existen (smoke visual de Pasos 1-4,
  aserciones AppTest ampliadas, test de contraste) y formalizar la checklist en `mariana-stop`.
- **Pendiente de validar:** implementar esas piezas e integrarlas en `verificar.ps1` y
  `.github/workflows/tests.yml`. Cuando se toquen esas barreras, el doc-gate §8 obliga a actualizar
  `flujo-de-trabajo.md` (barreras → su doc dueño).
- Enmienda implícita del alcance de testing: extiende la línea del ADR 0012 (smoke visual) hacia un
  gate de UX completo; no lo reemplaza.
