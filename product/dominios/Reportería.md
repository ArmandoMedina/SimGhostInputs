---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Reportería

## Producto
- Fantasma

## Propósito
Convertir el resultado de la comparación en **salidas accionables y estándar**: un reporte narrativo en Markdown y gráficas ghost, para que el piloto sepa en qué curva enfocar su mejora sin leer números crudos.

## Alcance
- `report.md`: tabla resumen + "Top 5 dónde se va el tiempo" + tabla por curva.
- Gráficas (extra `charts`): mapa de delta, G-G, curvas, zonas de frenada.
- Salidas estándar: Markdown, CSV, PNG (legibles aunque el repo desaparezca).

**Fuera de alcance:** el overlay de video (es [[Overlay y composición de video]]); el cálculo del delta (es [[Normalización y comparación]]).

## Módulos
- REP — Reporte Markdown + CSVs
- CHT — Gráficas

## Relacionado con
- [[Normalización y comparación]]
- [[Interfaz de usuario]]
- [TBL-OUT-01 — Salidas](../../engineering/modelos-de-datos/TBL-OUT-01%20-%20Salidas%20(CSV%20y%20JSON).md)
