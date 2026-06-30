---
tipo: capacidad
clave: WER-01
modulo: WER
dominio: Desgaste de gomas
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# WER-01 - Medir desgaste acumulable de un stint

## Módulo
- [[WER - Desgaste acumulable]]

## Propósito funcional
Medir el deslizamiento de ruedas en una vuelta y acumular el desgaste a lo largo de un stint, proyectando las vueltas restantes antes del reventón a partir de la tasa reciente.

## Actor principal
Sistema (ejecutado sobre vuelta normalizada; el presupuesto de stint se calcula sobre la lista de tasas de todas las vueltas del stint).

## Entradas funcionales
- Objeto `Lap` con canal `speed` y canales de velocidad de rueda (`ts_fl`, `ts_fr`, `ts_rl`, `ts_rr`).
- Opcionalmente: `brake`, `glong`, `abs`, `tcs`.
- Para el presupuesto de stint: lista de tasas de desgaste por vuelta y diccionario de umbrales (yellow, red, burst).

## Salidas funcionales
- `slip_series`: lista de valores de deslizamiento con signo por punto de distancia.
- `slip_index`: porcentaje medio de deslizamiento por encima de la banda muerta.
- `slip_load`: carga de deslizamiento extensiva acumulada (se puede sumar entre tramos).
- `assist_count`: número de activaciones (flancos de subida) de ABS o TCS.
- `wear_budget`: dict con `cumulative`, `rate_recent`, `laps_done`, `status` (ok/yellow/red/burst) y `laps_to_burst` si aplica.

## Reglas de negocio
- Sin canales de rueda, todas las funciones de deslizamiento devuelven `None` sin lanzar error.
- El slip es negativo en bloqueo de rueda (rueda más lenta que el coche) y positivo en patinaje de tracción (rueda más rápida).
- La carga de deslizamiento es extensiva: `slip_load(tramo1) + slip_load(tramo2) == slip_load(total)`.
- El presupuesto ignora vueltas con tasa `None` (vuelta sin canales de rueda) al calcular acumulado y tasa reciente.
- Si la tasa reciente es 0, no se proyectan vueltas al reventón (se evita la división por cero).

## Criterios de aceptación
- Dado una vuelta de rodadura libre sin deslizamiento real, cuando se calcula el `slip_index`, entonces el resultado es 0.0.
- Dado una vuelta con tramos de bloqueo de rueda y patinaje de tracción, cuando se calcula la `slip_series`, entonces los valores son negativos durante el bloqueo y positivos durante el patinaje.
- Dado una lista de tasas de desgaste por vuelta y umbrales configurados, cuando se calcula el `wear_budget`, entonces el acumulado, el estado y las vueltas estimadas hasta el reventón son correctos según los umbrales.
- Dado que la vuelta no tiene canales de rueda, cuando se intenta calibrar o calcular el deslizamiento, entonces todas las funciones devuelven `None` sin lanzar excepción.

## Dependencias funcionales
- [[NRM-03 - Remuestrear por distancia]]

## Fuera de alcance
- Visualización del GASTO en el HUD del overlay (es [[OVL-01 - Generar overlay HUD con canal alfa]]).

## Relacionado con
- [[Desgaste de gomas]]
