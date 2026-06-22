# ADR 0004 — Desgaste de llanta acumulable (medidor tipo gasolina)

- **Estado:** Aceptada (implementado en `core.wear_budget` + CLI `fantasma wear`; calibración de umbrales pendiente de QA con telemetría real)
- **Fecha:** 2026-06-21

## Contexto

El proyecto ya estima el maltrato de goma **por vuelta** (`slip_index` en `core/wear.py`),
pero es un número aislado: una vuelta no "recuerda" la anterior. El usuario quiere algo
**acumulable, como el medidor de gasolina**: ver cuánto desgaste lleva la goma en el stint
y estimar cuántas vueltas más aguanta antes de cambiar.

Caso de uso concreto (palabras del usuario): *"gasto 7.3 por vuelta, si en 50 revientan,
ya sé que me quedan ~X vueltas. Si bajo a 6.1 por vuelta, me duran un poco más."*

## Decisión

1. Reusar **`slip_index`** como el **rate de desgaste por vuelta** (no inventar otra métrica).
2. **Acumularlo** a lo largo del stint: `acumulado = Σ slip_index_i`.
3. **Umbrales configurables por el usuario** (amarillo / rojo / reventón; ej. 30 / 40 / 50).
4. **Vueltas estimadas a cambio** = `(umbral_reventón − acumulado) / rate_reciente`,
   igual que un medidor de gasolina.
5. Vivir en una **función pura en `core/`** (sin dependencias, testeable con fixtures
   sintéticas como el resto de `core/`).

## Razones

- `slip_index` **ya existe, ya es por vuelta**, y es literalmente "lo que gasta la goma"
  (deslizamiento). Es la medida que el usuario tenía en mente ("la que diseñamos").
- Función pura en `core/` respeta la arquitectura (core sin deps) y se prueba igual que el
  resto de la capa.
- Umbrales **por usuario** porque el número es un **proxy en unidades arbitrarias, no un %
  físico**: solo el piloto sabe a qué valor "revientan" sus gomas en su coche y pista,
  calibrándolo empíricamente vuelta tras vuelta.

## El camino que NO se toma (y por qué tienta)

- **Métrica compuesta (slip + temperatura + ABS/TCS) desde el día 1.** Tienta porque "más
  señales = más preciso". NO: mete pesos arbitrarios que no podemos validar todavía, y el
  usuario pensaba en **una sola medida**. Se puede sumar después si el slip solo no basta.
  v1 = solo `slip_index`.
- **Desgaste físico (% real de goma).** Tienta porque suena "más correcto". NO: no hay canal
  de desgaste real en los exports típicos; pretender un % físico sería **inventar números**.
  El proxy + umbral calibrado por el usuario es lo honesto.
- **Acumulación no-lineal (degradación acelerada).** Tienta porque la goma real se gasta más
  rápido ya gastada. NO en v1: añade parámetros que no podemos calibrar aún. Lineal (como
  gasolina) es simple, predecible y suficiente para empezar; se refina tras validar.
- **Persistencia cross-sesión.** Eso es la feature diferida **"v0.6.0 — Histórico entre
  sesiones"** del ROADMAP. Este ADR cubre solo el **stint en memoria** (una tanda de vueltas
  de una sesión). No mezclar las dos cosas.

## Forma propuesta (para implementar)

Función pura en `core/wear.py`:

```
wear_budget(rates, thresholds, recent_n=1) -> dict
  rates       : lista de slip_index por vuelta del stint (en orden)
  thresholds  : {"yellow": 30, "red": 40, "burst": 50}  (los pone el usuario)
  recent_n    : promediar las últimas N vueltas para el rate de proyección (default 1)
  ->          : {cumulative, status ("ok"/"yellow"/"red"/"burst"),
                 rate_recent, laps_to_burst (estimadas), est_total_laps}
```

CLI/UI consumen esta función; el cálculo no toca ffmpeg ni I/O.

## Consecuencias

- **Se gana:** un "medidor de goma" acumulable + estimación de vueltas a cambio, estilo
  gasolina, sin telemetría nueva (reusa lo que ya se computa).
- **Se limita:** requiere el canal **Tyre Speed** (sin él no hay slip → no hay rate; un
  fallback basado en ABS/TCS+temp queda para después). El número es **relativo, no físico**:
  los umbrales se calibran por prueba.
- **Pendiente para pasar de Propuesta a Aceptada:** confirmar con telemetría real de AMS2
  (stint de varias vueltas) que `slip_index` es **consistente vuelta-a-vuelta** como para que
  la suma tenga sentido. QA manual de Armando.
- **Hallazgo emergente (QA 2026-06-21, Nordschleife, M4 GT3 — sin conclusión cerrada):** en
  una carrera de 9 vueltas el desgaste acumulado llegó a ~17 con umbral amarillo en 30, o
  sea **las gomas no se acercan al amarillo porque el combustible obliga a parar antes**. Si
  esto se repite en la mayoría de los casos, un medidor de **vida total de goma** (umbrales
  absolutos) no es accionable: la decisión real del piloto es *"en mi parada obligada por
  combustible, ¿cambio gomas o no?"*. Eso apunta a otra métrica — **degradación de
  rendimiento dentro del stint**, no vida restante — o a un espectro relativo al stint/tanque.
  Replanteamiento a evaluar con más datos antes de tocar el diseño; ver ROADMAP.

## Enmienda (2026-06-22) — dónde vive cada acumulado

Tras el QA del overlay (Armando vio el campo **DESLIZ** "reiniciarse" curva a curva y
esperaba un acumulado): se aclara que el medidor acumulable de este ADR **nunca estuvo en
el HUD** — solo en `fantasma wear` (CLI, que acumula `slip_index` entre **vueltas** del
stint). El DESLIZ del HUD es instantáneo por diseño (ADR 0005). Decisión de dónde mostrar
cada acumulado:

- **Overlay (HUD): acumulado *de la vuelta*.** Nuevo readout que suma el **exceso de slip**
  desde meta hasta el cursor —cantidad **extensiva**, NO el promedio que es `slip_index`—,
  piloto vs referencia. Crece monótono a lo largo de la vuelta ("gasolina gastada en ESTA
  vuelta"). El overlay es de una sola vuelta, así que no arrastra stint.
- **Stint / sesión completa: gráficas (Producto 1), no el overlay.** La acumulación entre
  vueltas es análisis post-tanda multi-vuelta → su casa son las **gráficas** + el
  `fantasma wear` existente (p. ej. un medidor a lo largo de las vueltas).

**Consideración abierta (consistencia de unidades):** el readout de la vuelta usa una
cantidad **extensiva** (Σ exceso de slip), pero `wear_budget` hoy acumula **promedios**
(`slip_index`) por vuelta. Si se quiere que la gráfica de stint sea consistente con el
overlay (que el acumulado al final de una vuelta = lo que esa vuelta aporta al stint), ambos
deben usar la **misma unidad base**. Decidir al implementar; no resuelto aquí.

**Implica enmendar el ADR 0005** (el HUD pasa a llevar un indicador acumulado *además* de
los instantáneos).
