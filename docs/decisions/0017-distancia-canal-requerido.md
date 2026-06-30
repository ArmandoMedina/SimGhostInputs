# ADR 0017 — La distancia es un canal requerido; no se sintetiza desde la velocidad

- **Estado:** Aceptada
- **Fecha:** 2026-06-30

## Contexto

SimGhostInputs compara vueltas **por distancia**: el metro de pista es el índice maestro,
no el tiempo (principio de diseño #2, [`docs/formato-datos.md`](../formato-datos.md)). El canal
`dist` ya está marcado como obligatorio en el modelo de datos.

Durante el QA de cierre de v1.0 (telemetría real de AMS2, varios circuitos y clases) apareció
un export del ORECA 07 **sin el canal `Distance`**: en MoTeC i2 el export CSV tiene una casilla
**«Include Distance Data»** fácil de no marcar. El síntoma era doble: `laps` reportaba longitud
0 m (parecía "funcionar") y `detect`/`compare`/`overlay` reventaban con un `KeyError('dist')`
desnudo. Es un error que **se le va a pasar a muchos usuarios**, no un caso de borde raro.

Al corregirlo surge la bifurcación: ¿exigir el canal (detener con un aviso claro) o **derivar**
la distancia integrando `speed × dt` cuando falte, para que la herramienta "funcione igual"?

## Decisión

La distancia es un **canal requerido**. Si falta, el motor se **detiene con un aviso accionable**
(en CLI, UI y núcleo) que indica re-exportar marcando «Include Distance Data». **No se sintetiza**
un eje de distancia desde la velocidad.

## Razones

- **La comparación por distancia exige consistencia entre las dos vueltas.** Un eje integrado de
  `speed × dt` acumula error de deriva y, peor, **dos vueltas distintas derivarían ejes distintos**
  (dependientes de la calibración y el ruido de su propia señal de velocidad): el alineado por metro
  —que es la base de todo el análisis— quedaría comparando manzanas con peras. Un número plausible
  pero sutilmente inconsistente es más peligroso que un error claro.
- **Falla fuerte, temprano y accionable** es mejor que un resultado silenciosamente sesgado. El
  usuario tiene el dato correcto a un re-export de distancia; pedírselo cuesta segundos y elimina la
  ambigüedad.
- El canal existe en el origen; el problema es de **export**, no de disponibilidad. La solución
  correcta es guiar el export, no inventar el dato.

## El camino que NO se toma (y por qué tienta)

**Derivar la distancia integrando la velocidad** (`dist[i] = Σ speed·dt`) cuando el canal falta.
Tienta porque "la herramienta seguiría funcionando sin pedirle nada al usuario" y técnicamente la
integral es trivial. Se descarta: introduce **inconsistencia entre vueltas** (cada una con su propio
eje derivado), deriva acumulada y una falsa sensación de exactitud sobre el eje maestro del que
depende **todo** el pipeline. Si una sesión futura lo reconsidera, que sea con evidencia de que la
inconsistencia entre ejes derivados es tolerable para la comparación —no por conveniencia de UX.

## Consecuencias

- **Se gana:** robustez y honestidad — sin distancia, mensaje claro en vez de crash o resultado
  sesgado; guía de export reforzada (UI Paso 1 bloquea, `laps` avisa, guía de usuario y
  `formato-datos` lo dejan explícito).
- **Se pierde:** la herramienta no procesa exports sin distancia (decisión deliberada).
- **Pendiente de validar:** si con más datos reales se confirma que muchos usuarios exportan sin
  el canal pese al aviso, reconsiderar la guía de export (no la síntesis).
