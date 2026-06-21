# ADR 0004 — Desgaste de llanta acumulable (medidor tipo gasolina)

- **Estado:** Propuesta (falta validar con telemetría real de AMS2 en un stint de varias vueltas)
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
