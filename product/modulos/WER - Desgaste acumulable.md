---
tipo: modulo
clave: WER
dominio: Desgaste de gomas
producto: Fantasma
estado: vigente
prioridad: Must Have
---

# WER - Desgaste acumulable

## Dominio
- [[Desgaste de gomas]]

## Propósito del módulo
Medir el deslizamiento de ruedas vuelta a vuelta y cuantificar el desgaste acumulado de un stint, proyectando las vueltas restantes antes del reventón.

## Alcance
- Calibración del ratio rueda/velocidad en tramos de rodadura libre.
- Series de deslizamiento (`slip_series`) con signo: negativo en bloqueo, positivo en patinaje.
- Índice de deslizamiento (`slip_index`, porcentaje medio) y carga de deslizamiento (`slip_load`, extensiva por distancia).
- Conteo de activaciones de ABS y TCS por flancos de subida.
- Presupuesto de desgaste por stint (`wear_budget`) con acumulado, tasa reciente, estado (ok / yellow / red / burst) y proyección de vueltas.

**No cubre:**
- Presentación visual del desgaste en el HUD del overlay (es [[OVL - Render del overlay]]).
- Temperatura de gomas (canal opcional incluido en el reporte si está disponible).

## Regla funcional
El desgaste es una magnitud extensiva: la carga acumulada de dos tramos contiguos es igual a la suma de sus cargas individuales. Sin canales de rueda (`ts_fl`..`ts_rr`), todas las funciones de desgaste devuelven `None` sin error.

## Secuencia funcional
- **Módulo anterior:** [[NRM - Normalización]]
- **Módulo siguiente:** [[REP - Reporte y CSVs]]

## Capacidades
- [[WER-01 - Medir desgaste acumulable de un stint]]

## Dependencias funcionales
- [[NRM - Normalización]]

## Relacionado con
- [[Desgaste de gomas]]
