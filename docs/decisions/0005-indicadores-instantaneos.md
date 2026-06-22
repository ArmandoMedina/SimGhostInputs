# ADR 0005 — Los indicadores de estado del HUD se leen en el cursor, no por ventana

- **Estado:** Aceptada
- **Fecha:** 2026-06-21

## Contexto

El overlay tiene indicadores en la franja de datos (ABS, TC, DESLIZ…). Originalmente
varios se calculaban como un agregado sobre **toda la ventana visible** (~520 m: 320 m
atrás + 200 m **adelante** del cursor): las luces ABS/TC eran un conteo de activaciones
en esa ventana, y DESLIZ un promedio de slip de esa ventana. Resultado: no reaccionaban
al momento real — el "ABS" no prendía/apagaba con la frenada, y DESLIZ promediaba incluso
200 m que el piloto aún no había recorrido.

## Decisión

Los **indicadores de estado** reflejan el momento del cursor, no la ventana:

- **Luces ABS/TC**: leen el flag del piloto en el cursor y encienden con **retención corta**
  (`HOLD_M`, 8 m) para no parpadear a 30/60 fps. Apagadas = gris; encendidas = su color
  (ABS ámbar, TC violeta).
- **DESLIZ**: promedio de slip sobre una **ventana corta detrás** del cursor (`SLIP_WIN_M`,
  40 m) — el deslizamiento que la goma acaba de sufrir.

Las **líneas** de los paneles (gas/freno/volante) sí siguen dibujando toda la ventana
visible: ahí el contexto adelante/atrás aporta.

## Razones

- Un indicador de estado debe responder *"¿qué pasa AHORA?"*, no *"¿qué pasó en promedio
  en 520 m?"*. El agregado por ventana mete lag y desconecta el dato del video.
- Incluir 200 m **por delante** del cursor en DESLIZ era directamente engañoso (slip futuro).
- La retención / ventana corta da estabilidad sin reintroducir lag perceptible.

## El camino que NO se toma (y por qué tienta)

- **Volver a un agregado por ventana grande "para que se vea más estable".** Tienta porque
  una ventana grande suaviza el número. NO: suaviza a costa de lag y de mostrar slip que el
  piloto no ha tomado. La estabilidad se logra con retención/ventana corta, no con los 520 m.
- **Instantáneo puro (1 muestra) sin retención.** Tienta por "máxima precisión". NO: a
  30/60 fps las activaciones de 1-2 muestras parpadean. La retención corta es el punto medio.

## Consecuencias

- Las luces ABS/TC y DESLIZ ahora siguen el video. Este ADR cubre tanto el arreglo de las
  luces como el ajuste de DESLIZ.
- Pendiente: validar en video real que los tiempos (`HOLD_M` / `SLIP_WIN_M`) se sienten
  bien — son ajustables sin cambiar el principio.

## Enmienda (2026-06-22) — excepción acumulada en el HUD

El principio de este ADR (los **indicadores de estado** se leen en el cursor) **se mantiene**
para ABS/TC y DESLIZ. Se añade una **excepción deliberada**: el HUD llevará **un** indicador
**acumulado** — el desgaste de goma acumulado *de la vuelta* (suma corrida del exceso de slip
desde meta hasta el cursor; ver enmienda del ADR 0004). Ese readout **no es instantáneo a
propósito**: su valor es justamente el total corrido.

⚠️ **Para la siguiente sesión/IA:** no "corregir" ese acumulado a una ventana corta creyendo
que viola este ADR. DESLIZ (instantáneo) y el acumulado de la vuelta son **dos cosas distintas
que coexisten**: DESLIZ responde *"¿dónde castigo la goma ahora?"*; el acumulado, *"¿cuánto
llevo gastado en la vuelta?"*.
