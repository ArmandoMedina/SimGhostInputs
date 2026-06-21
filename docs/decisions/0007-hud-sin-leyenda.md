# ADR 0007 — El HUD no lleva leyenda de colores; se documentan fuera

- **Estado:** Aceptada (leyenda visual ya añadida en `hud-reference.md`, ver `docs/demo/hud-leyenda.png`).
- **Fecha:** 2026-06-21

## Contexto

La franja del overlay tenía dos rótulos de leyenda —`freno+ABS` y `gas+TCS`— que traducen
el color de las líneas de los paneles. Pero son solo **2 de ~10** significados de color del
HUD (gris = referencia, azul/amarillo/naranja del volante por carga lateral, ámbar = ABS,
magenta = TCS, etc.). El overlay se mira **en movimiento**, superpuesto sobre el video.

## Decisión

- El HUD **no** lleva leyenda de colores. Se **quitan** `freno+ABS` y `gas+TCS`.
- Los colores se documentan en `hud-reference.md`, con una **leyenda visual** (imagen
  anotada del HUD), no solo una tabla de texto.
- Para video compartido con terceros, un **frame-leyenda de una sola vez** (no permanente
  en el HUD).

## Razones

- Una leyenda **parcial** (2 de ~10 colores) es peor que ninguna: implica una completitud
  que no tiene y hace preguntar *"¿por qué estos dos y no el resto?"*. Cero leyenda es
  consistente; una leyenda completa ocuparía espacio de pantalla que el HUD no tiene.
- El overlay se lee en movimiento: una leyenda no se consulta a mitad de vuelta, así que
  ocupa espacio sin pagarlo en utilidad. Los colores se aprenden una vez y luego se leen de
  corrido.
- Quitar los dos rótulos **libera espacio** en la franja, que ya estaba apretada.

## El camino que NO se toma (y por qué tienta)

- **Completar la leyenda dentro del HUD** (añadir el resto de colores). Tienta porque haría
  el HUD "autoexplicativo". NO: gasta espacio caro de pantalla en algo que no se consulta en
  movimiento y compite con el dato. La autoexplicación va fuera del HUD.
- **Dejar las dos leyendas parciales como están.** Tienta por inercia (ya estaban ahí). NO:
  2-de-10 es el peor punto entre 0 y todas — implica completitud falsa y confunde.
- **Confiar en que la tabla de texto del doc basta.** Tienta porque "ya está documentado".
  NO: hay evidencia directa de que una tabla de prosa se salta — el propio dueño tenía
  `hud-reference.md` con la tabla completa y aun así no sabía qué significaba `freno+ABS`.
  Por eso la documentación necesita una leyenda **visual**, no solo texto.

## Consecuencias

- HUD más limpio y con más aire en la franja.
- **Costo:** un video exportado es opaco para quien no haya visto la documentación. Se mitiga
  con la leyenda visual en `hud-reference.md` + un frame-leyenda opcional para compartir.
- **Resuelto:** la leyenda visual (frame del HUD, `docs/demo/hud-leyenda.png`) ya está
  incrustada en `hud-reference.md` junto a las tablas de color.
