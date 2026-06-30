---
tipo: componente
tecnologia: MoTeC i2 (externo)
administrador: el piloto (exporta desde i2)
estado: vigente
---

# MoTeC i2

## Propósito
Software de análisis de telemetría del que SimGhostInputs **toma su entrada principal**: el piloto exporta un CSV desde MoTeC i2 y este repo lo importa. No es una dependencia de código — es el formato de origen que el repo evita tener que aprender (ese es el problema que resuelve, ver [PRODUCT_BRIEF](../../PRODUCT_BRIEF.md)).

## Funciones clave (lo que el repo consume)
- **CSV de i2** (separador `;`, encoding `utf-8-sig`, coma decimal europea): lo lee `fantasma/importers/motec_csv.py`.
- **Beacons**: marcadores de vuelta en los metadatos del log; el importador los usa como primera estrategia de separación de vueltas.
- Canales: i2 exporta nombres propios que el importador mapea a los [canales canónicos](../../docs/formato-datos.md).

## Conectividad y protocolos
- Archivo. El repo nunca habla con i2 en vivo; consume su export estático. (Un futuro importador `.ld` nativo eliminaría a i2 como intermediario — ver ROADMAP.)

## Relacionado con
- [[arquitectura]]
- [Formato de datos (mapeo de canales)](../../docs/formato-datos.md)
