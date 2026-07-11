# Verificación — la doctrina de pruebas del linaje

> El tercer tiempo del [lazo](lazo.md), en detalle. Todo lo de aquí se pagó en producción en el linaje (ADRs [0004](../docs/decisions/0004-centralizacion-del-conocimiento.md) y [0005](../docs/decisions/0005-exprimido-final-del-linaje.md)). La maquinaria (barreras de lint/tests/cobertura, smoke visual en CI) llega en el Sprint 3; las reglas no esperan a la máquina.

## Las reglas madre

- **El test ES el criterio, ejecutable.** No repitas en prosa lo que el test afirma: la prosa se pudre, el test truena.
- **Una prueba que nadie ejecuta es documentación que miente.** Por eso las suites van al muro (CI required), no a la memoria.
- **Un rojo se diagnostica, no se silencia.** Ajustar el test sin entender el rojo es apagar la alarma de humo.
- **Cada bug corregido se blinda con su test de regresión** (tabla bug → test). Un bug sin test es un bug en pausa.
- **No persigas 100 % de cobertura**: comportamiento crítico, reglas de negocio, bordes.

## Dos capas cuando hay UI (a prueba de migración)

La **lógica de flujo se prueba sin tocar el DOM** — así sobrevive a un rediseño; la **aceptación visual** va aparte. No valides la lógica a través del tool visual: la ata al DOM y la vuelve desechable al migrar.

Lo visual, a su vez, se parte en dos:

- **Lo medible bloquea en CI** como cualquier test: regresión de layout, aserciones estructurales, contraste WCAG ("aritmética sobre colores").
- **Lo subjetivo es checkpoint humano.** *Un gate subjetivo automático produce falsos rojos, se aprende a saltarlo y pierde autoridad — peor que no tenerlo.*

Política de snapshots: la verdad del baseline **se genera en el CI** (fuente única, no tu PC); **tolerancia generosa** — detecta "el layout se movió", no "un píxel cambió" (los falsos positivos por fuentes/antialiasing pudren el gate); acotado a pantallas clave; **opt-in**, nunca default (flaky y caro).

## E2E nombrado por clave de capacidad

El e2e se nombra con la clave estable de la [jerarquía](jerarquia.md) (`FAM-MOD-NN.spec`): en un contexto regulado, ese e2e **es evidencia de auditoría** — la capacidad y su prueba se encuentran una a la otra sin buscador.

## El contrato de robustez ante entrada hostil

Cuando el input primario viene de afuera, lo hostil es caso **esperado**, y el contrato del parser tiene cuatro cláusulas:

1. **Jamás lanza** — cualquier tipo de entrada devuelve resultado con forma.
2. **Jamás se cuelga** — presupuesto de tiempo explícito en la suite: si un cambio degrada un regex (ReDoS), el presupuesto lo delata.
3. **Jamás calla** — lo ilegible va a errores con `ok=false`, nunca a un `NaN` silencioso.
4. **La basura no contamina lo bueno.**

Y la política de datos: **fixtures sintéticos por defecto** (un builder parametrizable, nunca datos reales versionados — "motor sin datos"); la data real valida **fuera del repo** y el `.gitignore` excluye el formato crudo a propósito. La válvula cuando lo sintético *no ejercita el artefacto* (un render/HUD sobre telemetría real) es la **excepción de dominio cableada con nombre** (disparo `excepciones-cableadas`), no aflojar el mandato para todos: dato real fuera del repo, solo el resultado entra, y la excepción nombrada. La lección hermana ya es célebre en el linaje: la data real rompe el parser varias veces antes de estabilizar — se valida contra **toda** la data, no contra una muestra bonita.

## La verificación también mira hacia afuera

- **El contrato con un tercero se verifica contra su código fuente, no contra su documentación.** En el linaje, una spec escrita "desde la docs" traía 3 falsedades; trazar el fuente real (repo/branch/commit citados) las corrigió y descubrió un crash alcanzable. La tesis se confirma *"por evidencia externa, no por autorreferencia al propio repositorio"*.
- **La infraestructura se verifica conductualmente**, no por lectura: el fix de un mecanismo de actualización se probó observando que el contenido nuevo llega y que offline sirve la última copia — no leyendo el código y asintiendo.

## Cerrar con medición

- Un refactor de no-regresión deja el par **before/after** como artefacto ("bit a bit idéntico" verificado, no declarado).
- Una deuda puede cerrarse **por medición** ("MEDIDO: mantener, sin acción") — siempre con su **condición de reapertura** escrita.

## QA desde el producto, no desde scripts por fuera

Regla del linaje: **todo entregable que el cliente evalúe sale del pipeline real del producto, E2E.** Un script ad-hoc que arma el resultado por otra vía no prueba que el producto lo genere igual — y diverge en silencio.
