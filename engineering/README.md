---
tipo: indice
estado: en_definicion
---

# Ingeniería — el CÓMO

Esta capa describe **la implementación**: arquitectura, algoritmos, modelo de datos, componentes externos. Sombrero de **Dev** (Ahiram). Aquí va lo que en [`../product/`](../product/) quedó deliberadamente abierto. Las decisiones técnicas no obvias se registran como ADR en [`../docs/decisions/`](../docs/decisions/).

> Si una definición es de negocio (qué/por qué), no va aquí — va en [`../product/`](../product/).

## Qué vive aquí

- **[`arquitectura.md`](arquitectura.md)** — vista general del paquete `fantasma/` (core, importers, viz, ui, cli) y el principio "core sin dependencias". (Esqueleto arc42 / C4.)
- **[`pruebas.md`](pruebas.md)** — la estrategia de pruebas: qué se automatiza vs qué es QA manual (consolida [ADR 0003](../docs/decisions/0003-testing.md)). Es la verificación viva.
- **`componentes/`** — sistemas/servicios reales (propios o externos) que sostienen las capacidades: ffmpeg, NiceGUI, MoTeC i2, CrewChief-MQTT (futuro); Streamlit (obsoleto, referencia histórica).
- **`especificaciones/`** — la implementación concreta de una capacidad: comparación por distancia, detección de curvas, auto-sync por audio, NVENC.
- **`modelos-de-datos/`** — las estructuras: el modelo `Lap`, `corners.json`, `delta.csv`, `corners_compare.csv`.

## Relación con docs/ existente (SSOT)

Hay docs técnicos vivos que ya son **dueños** de su hecho y el doc-gate §8 los vigila:
`docs/formato-datos.md` (modelo de datos canónico, algoritmo de detección), `docs/hud-reference.md`
(anatomía del HUD). Las notas de `engineering/` **enlazan** a esos dueños o reciben su autoridad de
forma explícita — **nunca duplican** un hecho. La migración es gradual (ver [ADR 0015](../docs/decisions/0015-estructura-product-engineering.md)).

## Dónde vive el código

El código se escribe en `fantasma/` (VS Code); la documentación se edita en Obsidian. Conviven en el mismo git (docs-as-code). La estructura interna de `fantasma/` es una decisión de ingeniería descrita en [`arquitectura.md`](arquitectura.md). Las pruebas espejan el paquete en [`../tests/`](../tests/): el criterio de aceptación de una capacidad se materializa como test.

## Relacionado con
- [[pruebas]]
- [Registro de decisiones (ADRs)](../docs/decisions/README.md)
