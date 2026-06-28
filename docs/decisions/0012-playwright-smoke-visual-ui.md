# ADR 0012 — Playwright para smoke visual acotado de la UI Streamlit en v1.0 (enmienda el testing del 0010)

- **Estado:** Aceptada
- **Fecha:** 2026-06-28

## Contexto

El [ADR 0010](0010-framework-ui-streamlit.md) fijó Streamlit como UI de v1.0 y, en
sus Consecuencias ("Testing a prueba de migración"), **desaconsejó usar Playwright
sobre Streamlit**: los selectores contra el DOM de Streamlit se tirarían al migrar el
front, así que reservó Playwright para el front nuevo y dejó como base AppTest (lógica
de los flujos 0→4) + snapshot de imagen del HUD.

Esa restricción descansaba en un supuesto: que **la migración del front estaba cerca**,
así que cualquier prueba atada al DOM de Streamlit sería trabajo desechable casi de
inmediato. Dos hechos nuevos cambian el cálculo:

- **El timeline real es de meses, no de semanas.** Información del PO: la UI custom va
  *después* del trabajo de CrewChief, y a ~1 hora/día de dedicación eso son meses. El
  trabajo "desechable" se amortiza sobre meses de cobertura → el cálculo se invierte.
- **AppTest no atrapa bugs de renderizado.** El bug de los botones desalineados del
  Paso 0 (ADR 0011) era de **layout en el DOM**, no de lógica. AppTest mira el árbol de
  widgets, no los píxeles, así que no lo ve. Mariana (ojo humano, ADR 0011) tampoco lo
  *asegura*: depende de que alguien se acuerde de mirar. El hueco es real y demostrado.

## Decisión

Adoptamos **Playwright** para un **smoke visual acotado** de la UI Streamlit durante
v1.0, como dependencia **extra `[dev]`** (no toca al usuario final). Genera un snapshot
de imagen de las pantallas clave (el Paso 0 primero) y el CI truena si el layout se
mueve. Dueño del rol: **Mariana** (UX visual). Charbel mantiene AppTest (flujo 0→4),
los snapshots del HUD y correr el pipeline.

Con esto, la restricción "no-Playwright-sobre-Streamlit" del ADR 0010 queda **acotada,
no vigente tal cual**: sigue valiendo para la *lógica* de flujo, pero no para el smoke
visual que AppTest no puede cubrir.

## Razones

- **Solo un snapshot visual en CI convierte "ojalá lo notemos" en una barrera.** El bug
  del Paso 0 demostró que ni AppTest (no ve píxeles) ni el checkpoint humano de Mariana
  (depende de que alguien mire) atrapan un layout roto de forma confiable. Un snapshot
  en CI sí: si el layout se mueve, el build falla, sin depender de la memoria de nadie.
- **El supuesto que justificaba prohibirlo ya no se sostiene.** El 0010 lo desaconsejaba
  porque la prueba moriría pronto al migrar. Con la migración a meses de distancia, la
  prueba paga meses de cobertura antes de tirarse: el costo desechable se amortiza.
- **No le cuesta nada al usuario final.** Va en el extra `[dev]`, igual que ruff o
  pytest; quien instala la app para usarla no arrastra Playwright.
- **El flake de los snapshots visuales se mitiga, no se sufre.** Los snapshots de
  imagen son quisquillosos entre máquinas (fuente, antialiasing). Por eso: (1) la
  *verdad* del snapshot se genera en un entorno consistente — el contenedor del CI —
  como fuente única; (2) tolerancia **generosa**, para detectar "el layout se movió", no
  "un pixel cambió"; (3) acotado a las pantallas clave (el Paso 0 primero), no toda la UI.

## El camino que NO se toma (y por qué tienta)

- **Snapshots pixel-perfect / estrictos.** Tientan por "máxima detección": si comparas
  pixel a pixel atrapas el cambio más mínimo. Se descarta porque el rendering difiere
  entre máquinas (fuente, antialiasing), así que daría **falsos positivos** constantes y
  el equipo aprendería a ignorar el CER rojo — peor que no tenerlo. Tolerancia generosa.
- **Usar Playwright también para la LÓGICA del flujo 0→4.** Tienta por "ya que está
  Playwright, úsalo para todo". Se descarta porque ese flujo ya lo cubre **AppTest**, que
  es Python (no DOM) y por tanto *sobrevive a la migración* del front; reescribirlo en
  Playwright lo ataría al DOM de Streamlit y lo volvería desechable sin ganar nada.
  Playwright se reserva a lo **visual** que AppTest no ve.
- **Arrancar Playwright más tarde citando la restricción vieja del 0010.** Una sesión
  futura podría leer el 0010, ver "no Playwright sobre Streamlit" y bloquear esto. Este
  ADR existe justo para evitarlo: deja explícito que aquella restricción queda **acotada**
  (vale para la lógica, no para el smoke visual) porque su supuesto de timeline cambió.

## Consecuencias

- **Se gana** una barrera automática contra regresiones de layout en las pantallas clave:
  el CI falla si el render se mueve, sin depender de que alguien mire.
- **Sigue valiendo la base a prueba de migración del 0010:** mantener `core/` desacoplado
  de la UI, y AppTest (lógica) + snapshot del HUD (output) como cobertura que sobrevive a
  la migración. El smoke visual de Playwright se **suma**, no reemplaza.
- **Se asume que los snapshots de Playwright SÍ se tiran al migrar el front** (están
  atados al DOM de Streamlit). Es el costo aceptado: lo amortiza la lejanía de la
  migración (meses de cobertura antes de descartarlos).
- **Nueva dependencia en el extra `[dev]`** (Playwright). No afecta al usuario final ni a
  los extras de runtime.
- **Pendiente de implementar (paso aparte):** el andamiaje — añadir Playwright a `[dev]`
  en `pyproject.toml`, escribir el smoke del Paso 0, fijar la tolerancia y generar la
  verdad del snapshot en el contenedor del CI. Este ADR fija *que* se adopta y *con qué
  restricciones*, no el cableado.
