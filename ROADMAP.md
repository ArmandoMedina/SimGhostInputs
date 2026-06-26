# Roadmap — SimGhostInputs

> Estado vivo del proyecto: dónde va, qué falta para la **v1.0** y qué queda **diferido** para después. El **porqué** de cada decisión vive en [`docs/decisions/`](docs/decisions/README.md); el historial de cambios, en [`CHANGELOG.md`](CHANGELOG.md); qué documentos tocar al hacer un cambio, en [`CONTRIBUTING.md` §8](CONTRIBUTING.md#8-mantenimiento-de-documentación).
>
> **Para retomar en frío:** lee «Estado actual» y «▶️ Para la próxima sesión». Eso basta para saber qué sigue.

📋 [Brief de Producto](PRODUCT_BRIEF.md) · 📝 [Changelog](CHANGELOG.md) · 🧩 [Decisiones (ADR)](docs/decisions/README.md)

---

## Estado actual — v0.10.0

Último release: **v0.10.0** (2026-06-26) — barreras de calidad: linter/formatter `ruff` + job de CI, `tools/verificar.ps1` (modo aviso), hook `pre-push`, guía `docs/flujo-de-trabajo.md` y el ADR 0010 (UI = Streamlit en v1.0). El pipeline offline completo (importar → comparar → overlay → componer) funciona; la UI es Streamlit ([ADR 0010](docs/decisions/0010-framework-ui-streamlit.md)).

La meta inmediata es **la v1.0**: no es construir features nuevas, sino **estabilizar, testear, documentar y validar en AMS2 el pipeline que ya existe**. Las versiones publicadas están en el CHANGELOG; el siguiente hito es la 1.0.

> **▶️ Para la próxima sesión (Armando):**
> 1. **Revisar overlay + UI** buscando detalles visuales y de usabilidad por pulir (ver gaps de UI abajo — DESLIZ/GASTO se confunden en el HUD).
> 2. **Confirmar el desync de FPS con un video de 60 fps real.** El análisis de código dice que NO debería desincronizar; falta la prueba con video.
> Con eso + el QA de AMS2 (≥3 circuitos) + `setup.ps1` en Windows limpio, se corta la 1.0.

---

## Camino a la v1.0

El criterio para llamarla v1.0 es que el pipeline offline esté **completo, documentado y probado**. Alcance declarado: **AMS2 únicamente**. Importadores adicionales (iRacing, rF2, ACC) y features avanzadas (drill-down, histórico, pace notes) van después.

### Requisitos para la v1.0

- [x] v0.9.0 completada y en producción
- [x] Suite de tests de `core/` + CI en GitHub Actions ([ADR 0003](docs/decisions/0003-testing.md))
- [x] Docs completas y al día: guía de usuario, referencia de HUD (con leyenda visual y campo GASTO), formato de datos, cómo contribuir, **glosario**
- [x] **Los gaps `Alta` no bloquean la 1.0** (decidido 2026-06-21): el único vivo es `--format prores`, ya mitigado con el default `webm`; se difiere a post-1.0
- [ ] **API interna (`core/`) estabilizada** — sin cambios breaking entre parches (es revisión, no código nuevo)
- [ ] 👤 **Probado en AMS2 en ≥3 circuitos distintos** — **1/3: Nordschleife ✓** (M4 GT3, 9 vueltas, 2026-06-21: pipeline completo sin errores). Faltan **Interlagos y México**, elegidos para cubrir clases de auto distintas al GT3 (fórmula y prototipo); falta conseguir esas 2 telemetrías
- [ ] 👤 **`setup.ps1` probado en instalación limpia de Windows 11** — en curso (Armando lo prueba en otra PC). La detección de dependencias y el encoding ASCII ya se corrigieron (v0.7.1 / v0.7.2)
- [x] **Cortar release del `[Unreleased]`** acumulado — hecho en v0.10.0

### Notas vivas (no bloquean, a refinar)

- **Desgaste acumulado en dos vistas** (enmienda [ADR 0004](docs/decisions/0004-desgaste-acumulable.md)/0005; unidad en [ADR 0009](docs/decisions/0009-unidad-desgaste-acumulado.md)):
  - **(1) HUD del overlay** — acumulado *de la vuelta* (campo **GASTO**): **✅ implementado en v0.9.0**.
  - **(2) Gráficas (Producto 1)** — acumulado de *stint* entre vueltas: **⏳ pendiente** (hoy solo en `fantasma wear`, CLI).
- **Umbrales de desgaste a recalibrar:** en el QA real las gomas no llegaron al amarillo porque **el tanque se acaba antes** (vida total de goma vs. degradación dentro del stint). Recopilar más datos antes de rediseñar. Detalle en [ADR 0004 §Consecuencias](docs/decisions/0004-desgaste-acumulable.md).

---

## ⏸️ Diferido — post-v1.0

> Fuera del alcance de la 1.0 (solo AMS2, pipeline offline). Se retoman después de declararla estable. Cada uno conserva su spec en su documento dueño; aquí solo el qué + por qué se difiere.

- **Front de escritorio custom (v2.0)** — *evaluar* migrar la UI de Streamlit a un shell de escritorio, por dos límites reales: personalización topada e instalación no-doble-click. **No está decidida**: es una evaluación con gatillo. Antes de comprometerse, correr el **benchmark de herramientas** (skill `benchmark-opciones`: Streamlit + escape hatches vs Tauri/pywebview/Electron vs web local) y un experimento barato de personalización; luego registrar la arquitectura elegida como ADR nuevo. Restricción heredada: mantener `core/` desacoplado y preferir tests a prueba de migración. Detalle en [ADR 0010](docs/decisions/0010-framework-ui-streamlit.md).
- **Drill-down por curva** — convierte la tabla de tiempo perdido en coaching accionable (Δ frenada, Δ intensidad, V-Min target, síntesis en lenguaje natural), todo aritmética pura sobre `corners_compare.csv`, sin LLM. Los datos ya existen en el `trace` de `compare()`. Spec en [PRODUCT_BRIEF.md §10](PRODUCT_BRIEF.md).
- **Histórico entre sesiones** — comparar el rendimiento en una misma curva a lo largo de varias tandas (`fantasma history add/show`, gráfica de tendencia por curva). Almacenamiento local por decidir (SQLite o JSONs).
- **Nuevos importadores** — `.ld` nativo (MoTeC), `.ibt` (iRacing), ampliar `GUESS`/`MOTEC_MAP` para SimHub/ACC/rF2. Elimina la dependencia de exportar CSV desde MoTeC i2. (v1.0 cubre solo AMS2.)
- **Coaching de voz vía CrewChief Pace Notes** — generar los WAV + `metadata.json` con los metros exactos de `corners.json` para que CrewChief hable en el punto justo. Dos capas: tonos posicionales (sin dependencias) y voz contextual (edge-tts). Investigado y validado; spec completa en [ADR 0002](docs/decisions/0002-crewchief-pacenotes.md).
- **fantasma-live** (repo separado) — coaching adaptativo en tiempo real (listener UDP, delta en vivo, voz <200ms). Solo si Pace Notes no cubre el caso de uso; reacciona a lo que pasa en la vuelta, no al histórico.
- **Lista de vueltas procesadas en la sesión** (UI) — tabla acumulada de vuelta + salida + calidad de sync para quien procesa varias seguidas. Conveniencia, no corrección.

---

## 🔧 Transversal

### Gaps técnicos

Cosas en el código sin cobertura de QA formal ni documentación. Ninguno bloquea la 1.0.

| Gap | Descripción | Prioridad |
| :-- | :-- | :-- |
| `--format prores` cuelga ffmpeg en vueltas largas | En Nordschleife (~394s) arranca, escribe ~4 GB de frames y se congela; el archivo queda corrupto. **Mitigado** con el default `webm`. Diagnóstico (2026-06-21, sin reproducir): `_run_ffmpeg` en `viz/overlay.py` manda `stderr=DEVNULL`, así que el motivo real de ffmpeg se descarta (misma trampa ya corregida en `compose.py` v0.6.5); además la rama `prores_ks` no pasa threading. **Pendiente:** instrumentar (capturar stderr) y reproducir un encode real de vuelta larga. Ojo al límite de 4 GB de FAT32/exFAT si la salida va a disco externo. | Alta (no bloquea: solo afecta a quien pida prores explícito) |
| DESLIZ vs GASTO se confunden en el HUD | Ambos viven en la misma franja; GASTO con etiqueta chica/tenue (fontsize 9). DESLIZ se reinicia por curva (instantáneo, por diseño) y GASTO acumula de la vuelta — visualmente no se distingue cuál es cuál. Mejorar al pulir overlay/UI (separación visual, etiqueta legible, o que GASTO «se llene»). Detectado en QA 2026-06-26. | Baja |
| Overlay con FPS distintos al de la grabación | Investigado (2026-06-17): no reproduce desync — los frames se generan en `t = n/fps`, así que la duración del `overlay.webm` = duración de la vuelta sea cual sea el fps; un fps bajo solo da un HUD «a saltos», no desfase. La guía ya recomienda `--fps 60`. **Pendiente:** confirmarlo con video de 60 fps real (ver «próxima sesión»); si aparece desync real, capturar repro. | Baja |
| Vueltas muy cortas | ¿Qué pasa si el piloto sale de pista y la vuelta tiene solo 500 m? | Media |
| Circuitos con vuelta que cruza meta más de una vez | Circuitos en 8 o con chicane en meta podrían romper la detección de vueltas. | Media |
| Test de degradación por canales ausentes | Falta prueba sistemática de combinaciones de glat/glong/gear/abs/tcs ausentes (parcialmente cubierto por la suite). | Media |
| Auto-sync no detecta un video EQUIVOCADO que sí tiene motor | Un video **sin** señal de motor ya se rechaza (`z < 3.0σ`); pero un video de **otra sesión con motor** puede superar el umbral y, con el multi-vuelta del [ADR 0008](docs/decisions/0008-sync-multivuelta-candidatos.md), ofrecer candidatos espurios. Propuesta: avisar «calidad baja en todos los candidatos, ¿seguro que el video corresponde?». | Baja |
| Aviso si el piloto va más rápido que la referencia | Es fácil invertir `--reference`/`--driver` por error (el GAP sale verde cuando debería ser rojo). Un aviso al renderizar lo atajaría. | Baja |
| Colores ABS/TC de la referencia parecidos a los del piloto | Deuda del [ADR 0006](docs/decisions/0006-grosor-uniforme-lineas-hud.md): el tono codifica «qué» y solo el brillo «quién», lo que confunde piloto vs referencia. Dirección elegida: tonos distintos (opción B), diferida. | Baja |
| `fantasma compose` sin ffmpeg instalado | El error actual puede no ser claro para el usuario — mejorar mensaje. | Baja |
| `setup.ps1` mezcla propósito dev/usuario | Ofrece instalar GitHub CLI «para subir el repositorio» — eso es de contribuidor, no del piloto que instala para analizar. Candidato a un flag `-Dev` o a quitarlo del flujo de usuario. | Baja |

### Deuda técnica

| Item | Descripción |
| :-- | :-- |
| Ampliar cobertura de tests | La suite (48+ tests, Tier 1–4 + smoke de UI) y el CI ya cumplen el requisito de v1.0. Pendiente: ampliar conforme crezca el código. Estrategia en [ADR 0003](docs/decisions/0003-testing.md). |
| `motec_csv.py` codificación | Lee con `utf-8-sig`; CSV de i2 en Windows con setups no-inglés pueden traer otro encoding. |
| Branch protection en `master` | Hoy el CI **avisa** pero no **bloquea el merge** (single-author no lo necesita). Al sumar al primer colaborador: activar en GitHub «requiere PR + checks `lint` y `pytest` en verde». Ya documentado como expectativa en `CONTRIBUTING.md` §6 y `docs/flujo-de-trabajo.md`. |
