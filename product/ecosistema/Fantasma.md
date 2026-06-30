---
tipo: ecosistema
nombre: Fantasma
estado: vigente
proyecto_principal: fantasma-inputs
---

# Fantasma

## Propósito del ecosistema
Herramientas para que un sim racer de hobby mejore sus tiempos con **sus propios datos**, sin software profesional de telemetría, sin nube y sin suscripción. El insight: el 80% de la mejora viene del 20% de las curvas donde se pierde más tiempo, y ubicar ese 20% no requiere IA — requiere aritmética sobre datos que ya existen.

## Visión estratégica
Cubrir el ciclo del piloto de hobby con piezas de stack distinto pero filosofía común (datos locales, salidas estándar, sin lock-in):

- **`fantasma-inputs`** (este repo) — análisis **offline** post-tanda: importar → comparar → reporte + overlay de video.
- **`fantasma-live`** (futuro, repo separado) — coaching de voz **en tiempo real** (listener UDP, TTS, latencia <200 ms). Stack radicalmente distinto: mientras el sim corre, la GPU está al límite con VR.

### Oportunidades de expansión
- Importadores nativos (`.ld`, `.ibt`) que eliminen a MoTeC i2 como intermediario.
- Integración con CrewChief vía Pace Notes ([ADR 0002](../../docs/decisions/0002-crewchief-pacenotes.md)).

## Marco / restricciones
- **Sin GPU durante la sesión:** el render corre en CPU; la GPU es del sim. Solo `compose` usa NVENC, post-sesión.
- **Datos locales siempre.** Sin cuentas, sin APIs de terceros en el pipeline.
- **AGPL-3.0-or-later.**

## Soluciones del ecosistema
- [[Análisis Post-Tanda]]
- [[Overlay de Video]]

## Relacionado con
- [Brief de Producto](../../PRODUCT_BRIEF.md)
