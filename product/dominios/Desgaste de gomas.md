---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Desgaste de gomas

## Producto
- Fantasma

## Propósito
Estimar el **desgaste de goma acumulable** de un stint a partir de la carga de deslizamiento, para que el piloto vea cómo se degrada el agarre a lo largo de las vueltas. Medidor tipo gasolina (se llena), no instantáneo.

## Alcance
- Cálculo de slip/carga de deslizamiento con y sin canales de rueda (degradación graceful).
- Acumulado de la vuelta (campo GASTO del HUD) y de stint (`fantasma wear`).

**Fuera de alcance:** modelo físico de neumático; predicción de vida total de goma (los umbrales se recalibran con datos reales, ver ROADMAP). Combustible.

## Módulos
- WER — Desgaste acumulable

## Relacionado con
- [[Reportería]]
- [ADR 0004 — Desgaste acumulable](../../docs/decisions/0004-desgaste-acumulable.md)
- [ADR 0009 — Unidad del desgaste](../../docs/decisions/0009-unidad-desgaste-acumulado.md)
