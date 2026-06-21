# ADR 0006 — Jerarquía visual del HUD: grosor uniforme, piloto siempre encima, colores que distinguen quién

- **Estado:** Aceptada (las tres reglas). Para la regla 3 se elige la **opción B** (tonos distintos piloto/referencia), pero su implementación se **difiere** como deuda — ver Consecuencias.
- **Fecha:** 2026-06-21

## Contexto

El ABS/TC de la **vuelta de referencia** casi no se nota en los paneles, porque va por
debajo de las líneas del piloto. Para hacerlo visible tientan dos atajos: **engrosar** esas
líneas, o **dibujarlas encima** del piloto (z-order). Ambos se probaron en esta sesión y se
revirtieron, porque cada uno rompe un principio de cómo el HUD comunica información.

## Decisión

Tres reglas de jerarquía visual del HUD:

1. **Grosor uniforme.** Todas las líneas de los paneles (piloto y referencia) tienen el
   mismo grosor.
2. **El piloto siempre va encima.** La línea del piloto se dibuja por encima de la de la
   referencia; la referencia nunca la tapa.
3. **Colores piloto ≠ referencia, claramente distinguibles.** Los colores de piloto y
   referencia no deben parecerse entre sí.

## Razones

- **Grosor uniforme:** al final son gráficas, y en una gráfica el grosor de una línea es su
  **peso visual**. Las series de piloto y referencia deben pesar igual al leerlas, así que
  engrosar una le da peso a algo que no lo merece más; y si alguna debiera pesar más, sería
  la del **piloto** (el sujeto), nunca la de la referencia. Engrosar la referencia es por eso
  doblemente al revés. El énfasis, si acaso, va por color/capa a favor del piloto — no por
  grosor a favor de la referencia.
- **Piloto encima:** la línea del piloto es el sujeto del análisis: es la que se quiere leer
  y mejorar. La referencia es el contexto contra el que se compara. Si el contexto tapa al
  sujeto, oculta justo el dato que se está analizando, que es lo contrario de lo que el HUD
  debe hacer.
- **Colores distinguibles:** el HUD existe para atribuir de un vistazo *quién hizo qué*. Si
  piloto y referencia comparten colores parecidos, el ojo tiene que detenerse a desambiguar
  y se pierde la lectura a la primera — el único motivo de tener el HUD.

## El camino que NO se toma (y por qué tienta)

- **Engrosar las líneas de la referencia.** Tienta por directo. NO: el grosor es peso
  visual; engrosar la referencia le da más peso que al piloto, exactamente al revés de la
  prioridad correcta (regla 1).
- **Poner la referencia encima del piloto (z-order).** Tienta porque revela el ABS/TC de la
  referencia que queda oculto. NO: taparía al sujeto del análisis con su contexto (regla 2).
  Se probó y se revirtió en esta sesión.
- **Codificar "quién" solo por brillo del mismo tono** (ABS ámbar vivo = piloto, ámbar tenue
  = referencia). Tienta porque "mismo tono = mismo significado (ABS)". NO: mismo tono con
  distinto brillo se confunde a la primera, que es justo lo que la regla 3 evita.

## Consecuencias

- Con grosor uniforme + piloto siempre encima, el ABS/TC de la referencia que queda
  **ocluido** por el piloto no se puede revelar (solo se ve donde las dos líneas divergen).
  Hacerlo más visible **se difiere**: no se engrosa ni se sube de capa.
- **Regla 3 — dirección elegida, implementación diferida:** se opta por la **opción B**
  (tonos distintos para piloto vs referencia, en lugar de compartir el tono de la asistencia
  y separar solo por brillo). No se implementa ahora para no bloquear; se afina después.
  Hasta entonces, los colores de referencia subidos de brillo de la sesión 2026-06-21 quedan
  como **deuda** explícita (son el peor caso para la regla 3).
