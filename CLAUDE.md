# SimGhostInputs — Guía para Claude

## Qué es este proyecto

Motor open-source (AGPL-3.0) para comparar inputs de simracing contra una vuelta de referencia, por distancia. CLI en Python, sin infraestructura de servidor ni dependencias de nube.

**Propósito único:** convertir telemetrías exportadas de distintos loggers en un formato interno común, compararlas metro a metro contra una referencia, y generar reportes y visualizaciones accionables para el piloto.

---

## Lo que ESTÁ dentro del scope

- Importadores de telemetría: MoTeC CSV/XLSX, CSV genérico con `--map`
- Normalización: metro 0 en meta, remuestreo configurable por distancia
- Detector de curvas e hitos (V-Min, kinks de alta G, segmentación anti-contaminación)
- Comparador piloto vs referencia: delta continuo por metro + tabla por curva con tolerancias
- Reportes: `report.md`, `delta.csv`, `corners_compare.csv`
- Gráficas ghost: mapa de delta + velocidad/gas/freno por curva (matplotlib, opcional)
- Overlay HUD con canal alfa para superponer sobre grabaciones (matplotlib + ffmpeg, opcional)
- `fantasma compose`: compositor ffmpeg que superpone el overlay sobre el video final
- UI local (`fantasma ui`): interfaz Streamlit en localhost — sin hosting, datos siempre locales
- CLI: `fantasma laps | detect | compare | overlay | compose | ui`
- Nuevos **importadores** para otros formatos (iRacing .ibt, `.ld` directo, SimHub CSV...)
- Mejoras al detector de curvas, al comparador o al sistema de tolerancias

---

## Lo que está FUERA del scope de este repo

| Fuera de scope | Por qué |
| :-- | :-- |
| Listener de telemetría en vivo (Fase 3) | Es un proyecto separado; este repo es offline/post-tanda |
| Motor TTS / voz en tiempo real | Idem — live coaching es otro repo |
| Vueltas de referencia, telemetrías o setups incluidos en el repo | Cada usuario trae sus propios datos (principio AGPL) |
| API REST o servicio cloud | Requiere hosting externo ajeno al scope |
| UI web hospedada (SaaS, servidor público) | Idem — los datos del usuario no deben salir de su máquina |
| Base de datos propia o backend de almacenamiento | Los datos son CSV/JSON estándar; sin lock-in |
| Machine learning o inferencia de IA en el pipeline de comparación | El comparador es aritmética pura — un LLM solo añade latencia |
| Duplicar funcionalidad de CrewChief (spotter, combustible, daños) | CrewChief ya lo resuelve; este proyecto es solo coaching por datos |
| Hacks específicos de un sim dentro de `core/` | Van en `importers/`, no en el núcleo |

---

## Invariantes de arquitectura — nunca romper

1. **`core/` no importa desde `viz/` ni desde `importers/`** — dependencia unidireccional hacia arriba.
2. **El pipeline de comparación no usa LLM ni red** — es aritmética sobre arrays en RAM.
3. **Sin dependencias de GPU** — todo corre en CPU (la GPU va a AMS2 VR + Virtual Desktop).
4. **Sin estado global ni base de datos** — cada ejecución es idempotente con sus archivos de entrada.
5. **Los datos del usuario nunca entran al repo** — `reference_trace.csv`, `corners.json`, `hotlap.csv` y cualquier telemetría son privados por diseño.
6. **Nuevos importadores se añaden en `fantasma/importers/`** y devuelven un `Lap` con canales canónicos — no modifican `core/`.
7. **Las dependencias opcionales siguen siendo opcionales** — `core/` funciona sin Pillow, matplotlib ni openpyxl.

---

## Restricciones de rendimiento (hardware objetivo)

Xeon E5-2680 v4 (14c/28t) · 48 GB DDR4 · RTX 2060 (ocupada con AMS2 VR + Virtual Desktop).

- Nada que consuma GPU durante la sesión de conducción.
- Nada que requiera red en tiempo real.
- El overlay puede ser lento (post-tanda, sin restricción de tiempo).
- La comparación debe ser rápida (<5s para una vuelta completa del Nordschleife).

---

## Filosofía del proyecto

> Si una herramienta ayuda a la comunidad a mejorar, las mejoras de esa herramienta también deben volver a la comunidad.

- **Trae tus propios datos** — el motor es libre, los datos son tuyos.
- **CLI primero** — sin lock-in, sin UI obligatoria, scriptable.
- **Salidas estándar** — CSV, Markdown, PNG, WebM; nada propietario.
- **AGPL-3.0** — quien distribuye mejoras las devuelve a la comunidad.

---

## Buenas prácticas en este repo

- Actualiza `CHANGELOG.md` (`[Unreleased]`) con cada cambio significativo. Usa `/changelog` para asistencia.
- Los commits siguen el formato `tipo: descripción corta` + detalle si aplica. Usa `/commit` para asistencia.
- Antes de proponer un cambio grande, usa `/guardia` para verificar que está dentro del scope.
- Los datos privados (telemetrías, referencias, salidas generadas) **nunca** se añaden al repo.
