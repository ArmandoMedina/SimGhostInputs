# qa_runs/ — la evidencia del Gemba

> Aquí vive lo que la revisión visual **produjo**, no lo que alguien **dijo**. Regla madre: **un archivo que diga "validé y todo bien" no es evidencia** — eso es un acta, y las actas se auto-firman. La evidencia son los artefactos de la corrida.

## La convención

- **Un directorio por corrida:** `<rol|propósito>-<YYYYMMDD[-HHMMSS]>/` (ej. `revisor-visual-20260710-170512/`).
- **Adentro van artefactos reales:** capturas, snapshots renderizados, logs, tablas entrada→salida-obtenida→esperada. Con un `LOG.md` que declare: fecha, rama, **método reproducible**, y los resultados como tabla `# | Caso | Check | Resultado (N/N)`.
- **Datos 100 % sintéticos, siempre** — incluso en repos privados. Ninguna captura carga datos reales (perfil ficticio, montos inventados).
- **El veredicto NO vive aquí.** Va a `HANDOFF.md` o `CHANGELOG.md` **citando** el directorio de la corrida. Artefacto y veredicto se separan a propósito.

## La política de git (lección pagada)

El bulto se ignora (`qa_runs/*/` en `.gitignore`); **solo la evidencia citada desde HANDOFF/CHANGELOG se commitea**, selectivamente:

```
git add -f qa_runs/<corrida>/<archivo-citado>
```

Y es **paso obligatorio del cierre**, no cortesía: en el linaje se descubrió una vez que 0 artefactos habían llegado a git — toda la evidencia era local y se habría perdido con el clon.

## La evidencia sale del producto, no de scripts por fuera

**Todo entregable que el cliente evalúe sale del pipeline real del producto, E2E.** Un script ad-hoc que arma el resultado por otra vía no prueba que el producto lo genere igual — y diverge en silencio. Dos técnicas probadas en el linaje: un harness headless que evalúa los scripts **reales** y emite snapshots abribles como artefacto; y el caso "visitante nuevo" que verifica la ausencia de una fuga buscando una lista de términos conocidos en lo que el visitante vería. Y para refactors de no-regresión: el par **before/after** como artefacto ("bit a bit idéntico" verificado, no declarado).

## El checkpoint final es humano

La evidencia es el insumo para la revisión del cliente, no la revisión misma. El revisor-visual surte capturas y deja la corrida; **"¿se ve bien?" la responde el cliente con sus propios ojos** (Gemba).
