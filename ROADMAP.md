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

> Fuera del alcance de la 1.0 (solo AMS2, pipeline offline). Se retoman después de declararla estable. El detalle fino de cada uno vive en su documento dueño (ADR o PRODUCT_BRIEF); aquí el qué, el porqué se difiere y el alcance previsto.

### Front de escritorio custom (v2.0)
> Decisión de fondo en [ADR 0010](docs/decisions/0010-framework-ui-streamlit.md).

La UI de v1.0 es Streamlit (ADR 0010). Se difiere a v2.0 **evaluar** migrar a un front custom, por dos límites reales detectados: **(1)** personalización topada y **(2)** fricción de instalación (Streamlit no es doble-click: exige Python + terminal + `setup.ps1`). **No es una migración decidida: es una evaluación con gatillo.**

> **Restricción heredada del ADR 0010:** mantener `core/` **desacoplado** de la UI (mantiene barato migrar) y, durante v1.0, preferir tests **a prueba de migración** (AppTest + snapshot del HUD) sobre Playwright-sobre-Streamlit.

**Qué evaluar antes de comprometerse:**
- [ ] 🔬 **Benchmark de herramientas** (skill `benchmark-opciones`): comparar lo que ya usamos (Streamlit, `AppTest`) y opciones nuevas para un front testeable + personalizable + **instalación doble-click**. Candidatos: shell de escritorio empaquetado (Tauri, pywebview, Electron → `.exe` doble-click); web-en-navegador con servidor local (parte en desventaja: no quita la fricción de instalación); escape hatches de Streamlit (CSS, `st.components.html`, componentes custom → ¿destraban sin migrar?); Playwright para el front nuevo (no para Streamlit).
- [ ] **Experimento barato de personalización:** probar los escape hatches de Streamlit en la pantalla que más duele, para decidir *con evidencia* si migrar siquiera hace falta.
- [ ] Con el benchmark resuelto, **registrar la arquitectura elegida como ADR nuevo** (hoy NO está decidida).

### Coaching de voz — CrewChief Pace Notes
> Investigado y validado; spec completa en [ADR 0002](docs/decisions/0002-crewchief-pacenotes.md).

**Hallazgo clave:** CrewChief tiene un sistema nativo (**Pace Notes**) que reproduce WAV en metros exactos de la pista. SimGhostInputs ya tiene esos metros en `corners.json` — la integración es solo generar los archivos, sin modificar CrewChief ni construir un motor de voz propio.

**Cómo funciona:**
- `fantasma compare` genera el análisis (qué curvas, cuánto tiempo, qué problema).
- `fantasma pacenotes` lee ese análisis y genera las frases (edge-tts → MP3 → WAV 24kHz) + `metadata.json` con el metro exacto de cada curva (del `corners.json`).
- Los archivos se escriben en `Documents\CrewChiefV4\pace_notes\ams2\[pista]\`.
- El piloto activa las pace notes antes de salir del pit; CrewChief habla en el metro exacto.

**Dos capas de audio:**
- **Tonos posicionales** (núcleo, sin dependencias): un tono por hito del `corners.json` — frenada 880 Hz, ápex 440 Hz, gas 220 Hz. El piloto aprende la escala como reflejo; reacción ~100ms vs ~300ms visual.
- **Voz contextual** (opcional, edge-tts): frases 200m antes del punto de frenada, basadas en los flags de `compare`. La voz enseña, el tono actúa.
- **Modos:** `--mode tones` (default) · `--mode voice` · `--mode both`.

**Cambios previstos:**
- [ ] Módulo `fantasma/viz/pacenotes.py` (`generate_tone`, `generate_voice`, `build_pack`).
- [ ] Comando `fantasma pacenotes --corners --compare --mode {tones|voice|both} --top --output-dir`.
- [ ] Frases de voz basadas en los flags de `compare` (`late_brake`, `early_gas`, `d_vmin`).
- [ ] Dependencia opcional `edge-tts` → `pip install 'fantasma-inputs[voice]'`.
- [ ] Resolver el nombre de pista AMS2 (campo `Venue` del CSV o preguntar al usuario).

**QA antes de publicar:**
- [ ] `--mode tones`: genera `metadata.json` + WAV de tonos sin instalar edge-tts.
- [ ] Tonos suenan en los metros correctos en una sesión real en Nordschleife.
- [ ] Escala de frecuencias distinguible: agudo ≠ medio ≠ grave.
- [ ] `--mode voice`: frases coherentes con el problema detectado por curva.
- [ ] `--mode both`: voz 200m antes + tono en el metro exacto, sin solaparse.
- [ ] `--top 3`: solo las 3 curvas con más pérdida generan audio.
- [ ] `--volume 0.3`: tonos audibles pero no intrusivos junto al audio del sim.
- [ ] Sin `edge-tts` con `--mode voice`: error claro con instrucción de instalación.
- [ ] Nombre de pista incorrecto: CrewChief no carga el pack — documentar cómo dar con el nombre correcto.
- [ ] WAV en formato aceptado por CrewChief: 24kHz, mono (verificar con ffprobe).

### Drill-down por curva
> Spec en [PRODUCT_BRIEF.md §10](PRODUCT_BRIEF.md).

Convierte la tabla de tiempo perdido en coaching accionable: el piloto pica una curva y ve qué corregir (Δ frenada, Δ intensidad, V-Min target, Δ gas/G-lat), con síntesis en lenguaje natural — aritmética pura sobre `corners_compare.csv`, sin LLM. Los datos ya existen en el `trace` de `compare()`.

**Cambios previstos:**
- [ ] Tabla de curvas clickeable en UI Paso 2 → panel de detalle por curva.
- [ ] Función `corner_coaching(row, trace)` en `core/` que produce el dict de coaching.
- [ ] Síntesis en lenguaje natural ("frenas 40m antes con 15% menos intensidad → 0.6s perdidos").

**QA antes de publicar:**
- [ ] Click en la curva con mayor pérdida → panel de detalle con todos los campos.
- [ ] Curva sin canal gear → panel omite la marcha sin crashear.
- [ ] Curva sin glat → panel omite G-lat sin crashear.
- [ ] Síntesis en lenguaje natural coherente con los números del panel.
- [ ] Curva donde el piloto es más rápido → mensaje positivo ("ganas X s aquí").

### Histórico entre sesiones
Comparar el rendimiento en una misma curva a lo largo de varias tandas (¿progreso, techo, retroceso?).

**Cambios previstos:**
- [ ] Modelo `SessionHistory` + `fantasma history add/show --corner`.
- [ ] Gráfica de tendencia por curva (X = fechas, Y = tiempo perdido); paso opcional en UI.
- [ ] Almacenamiento local por decidir: SQLite o directorio de JSONs (sin servidor, sin cloud).

**QA antes de publicar:**
- [ ] Registrar 3 sesiones distintas y verificar que el histórico acumula bien.
- [ ] `fantasma history show` sin sesiones previas → mensaje claro, sin crash.
- [ ] Importar sesión antigua (CSV ya procesado) al histórico.
- [ ] Gráfica de tendencia con una sola sesión → no crashea, mensaje informativo.
- [ ] Migración: si el esquema de almacenamiento cambia entre versiones, migrar datos existentes.

### Nuevos importadores
Elimina la dependencia de MoTeC i2 como intermediario. (v1.0 cubre solo AMS2.)

**Cambios previstos:**
- [ ] Importador `.ld` nativo (MoTeC) y `.ibt` (iRacing).
- [ ] Ampliar `GUESS` (SimHub, ACC CSV) y `MOTEC_MAP` (variantes ACC/iRacing/rF2).
- [ ] Docs de compatibilidad por sim (qué canales exporta cada uno, qué queda como None).

**QA antes de publicar:**
- [ ] Importar `.ld` de AMS2 directamente → mismo resultado que vía CSV exportado.
- [ ] Importar `.ibt` de iRacing → detección de vueltas y canales básicos funcionan.
- [ ] CSV de SimHub para AMS2 → auto-detectado sin `--map`.
- [ ] CSV de ACC vía sim-to-motec → degradación graceful en ABS/TCS.
- [ ] Tabla de compatibilidad en README actualizada con estado real probado.

### fantasma-live (repo separado)
Coaching **adaptativo en tiempo real** — reacciona a lo que pasa en esa vuelta (trompo, contacto, pista cambiante), no al histórico. Solo si Pace Notes no cubre el caso de uso.

**Fases tentativas:**
- [ ] Listener UDP para AMS2 — captura telemetría en vivo a 60 Hz.
- [ ] Comparador en vivo — delta continuo por curva vs referencia.
- [ ] Motor de voz adaptativo — TTS con edge-tts, latencia <200ms.
- [ ] Modos de coaching — Aprendizaje · Qualy · Carrera.

### Lista de vueltas procesadas en la sesión (UI)
Tabla acumulada de vuelta + salida + calidad de sync para quien procesa varias seguidas. Conveniencia, no corrección.

---

## 🔧 Transversal

### Gaps técnicos

_Contexto: cosas en el código sin cobertura de QA formal ni documentación. Ninguno bloquea la 1.0. Los pendientes puntuales:_

- [ ] **Instrumentar `_run_ffmpeg` (capturar stderr) y reproducir el encode `--format prores` de una vuelta larga** para diagnosticar por qué cuelga. _Contexto:_ en Nordschleife (~394s) arranca, escribe ~4 GB de frames y se congela; hoy `stderr=DEVNULL` descarta el motivo real (misma trampa ya corregida en `compose.py` v0.6.5) y la rama `prores_ks` no pasa threading. Mitigado con el default `webm`; ojo al límite de 4 GB de FAT32/exFAT. _Prioridad: **Alta** (no bloquea: solo afecta a quien pida prores explícito)._
- [ ] **Distinguir DESLIZ de GASTO en el HUD** (separación visual, etiqueta legible, o que GASTO «se llene»). _Contexto:_ ambos en la misma franja, GASTO con etiqueta chica/tenue (fontsize 9); se confunde el instantáneo (DESLIZ, se reinicia por curva) con el acumulado (GASTO). Detectado en QA 2026-06-26. _Prioridad: Baja._
- [ ] **Confirmar con un video de 60 fps real que el overlay no desincroniza** (ver «próxima sesión»); si aparece desync, capturar repro. _Contexto:_ el código no debería desincronizar (frames en `t = n/fps`); investigado 2026-06-17, sin repro. La guía ya recomienda `--fps 60`. _Prioridad: Baja._
- [ ] **Definir y probar el comportamiento con vueltas muy cortas** (p. ej. salida de pista, vuelta de 500 m). _Prioridad: Media._
- [ ] **Probar circuitos cuya vuelta cruza meta más de una vez** (en 8 o con chicane en meta) — podrían romper la detección de vueltas. _Prioridad: Media._
- [ ] **Agregar test sistemático de degradación por canales ausentes** (combinaciones de glat/glong/gear/abs/tcs). _Contexto:_ parcialmente cubierto por la suite. _Prioridad: Media._
- [ ] **Avisar cuando todos los candidatos de auto-sync tienen calidad baja** ("¿seguro que el video corresponde?"). _Contexto:_ un video sin motor ya se rechaza (`z < 3.0σ`), pero uno de otra sesión con motor puede colar candidatos espurios con el multi-vuelta del [ADR 0008](docs/decisions/0008-sync-multivuelta-candidatos.md). _Prioridad: Baja._
- [ ] **Avisar al renderizar si el piloto va más rápido que la referencia** (atajar el `--reference`/`--driver` invertido, que pinta el GAP verde cuando debería ser rojo). _Prioridad: Baja._
- [ ] **Diferenciar colores ABS/TC de referencia vs piloto** (tonos distintos, opción B del [ADR 0006](docs/decisions/0006-grosor-uniforme-lineas-hud.md)). _Contexto:_ hoy el tono codifica «qué» y solo el brillo «quién», lo que confunde. _Prioridad: Baja._
- [ ] **Mejorar el mensaje de error de `fantasma compose` cuando falta ffmpeg.** _Prioridad: Baja._
- [ ] **Separar el propósito dev del de usuario en `setup.ps1`** (mover la instalación de GitHub CLI detrás de un flag `-Dev` o quitarla del flujo de usuario). _Prioridad: Baja._

### Deuda técnica

_Contexto: lo conocido a saldar cuando toque. Los pendientes puntuales:_

- [ ] **Ampliar la cobertura de tests** conforme crezca el código. _Contexto:_ la suite (48+ tests, Tier 1–4 + smoke de UI) y el CI ya cumplen el requisito de v1.0. Estrategia en [ADR 0003](docs/decisions/0003-testing.md).
- [ ] **Manejar encodings distintos a `utf-8-sig` en `motec_csv.py`** (CSV de i2 en Windows con setups no-inglés pueden traer otro encoding).
- [ ] **Activar branch protection en `master` al sumar al primer colaborador** (requiere PR + checks `lint` y `pytest` en verde). _Contexto:_ hoy el CI avisa pero no bloquea el merge (single-author no lo necesita). Ya documentado en `CONTRIBUTING.md` §6 y `docs/flujo-de-trabajo.md`.
