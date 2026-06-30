---
tipo: dominio
producto: Fantasma
estado: vigente
---

# Importación de telemetría

## Producto
- Fantasma

## Propósito
Convertir cualquier archivo de telemetría de origen al **modelo canónico** [[TBL-LAP-01 - Modelo Lap]], mapeando nombres de canales propios de cada sim/logger a los canónicos. Es la puerta de entrada del pipeline.

## Alcance
- MoTeC i2 CSV/XLSX (separador `;`, `utf-8-sig`, coma decimal europea), incluyendo beacons y metadatos.
- CSV genérico con auto-detección de columnas o mapeo manual (`--map`).

**Fuera de alcance:** importadores nativos `.ld`/`.ibt` (diferidos, ver ROADMAP); datos en vivo (eso es `fantasma-live`). Telemetría que no sea del propio piloto.

## Módulos
- IMP-MTC — Importador MoTeC
- IMP-GEN — Importador CSV genérico

## Relacionado con
- [[Normalización y comparación]]
- [Formato de datos](../../docs/formato-datos.md)
- [[motec-i2]]
