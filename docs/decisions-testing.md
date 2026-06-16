# Decisiones de diseño: estrategia de pruebas automatizadas

> **Estado: propuesto — sin implementar.** Este documento fija el enfoque acordado
> para la futura suite de tests. El código de tests se escribirá después; aquí queda
> la decisión razonada para no improvisarla en el momento.

## Problema

El proyecto no tiene ningún test automatizado. Todo el QA es manual con telemetría
real, lo que tiene dos costes concretos ya observados:

- **Regresiones silenciosas.** El refactor 0.6.3 (split de la UI en módulos) dejó
  `app.py` con imports relativos que rompían el arranque de la UI; nadie lo detectó
  hasta ejecutarla a mano sesiones después. Un test que solo importara `app.py`
  lo habría atrapado al instante.
- **Bugs por entorno no cubierto.** El detector de NVENC daba falso positivo en
  equipos sin GPU NVIDIA usable (`Cannot load nvcuda.dll`) y no caía al fallback de
  CPU. Un test del helper habría fijado el contrato.

El ROADMAP lista "sin tests automáticos" como deuda técnica y pide **al menos tests
unitarios de `core/`** como requisito para la 1.0.

---

## Principios que condicionan el enfoque

Heredados de `CONTRIBUTING.md` §4:

1. **Motor sin datos.** El repo nunca incluye telemetría. Los tests usan **datos
   sintéticos** generados en memoria, no CSVs reales versionados.
2. **Determinista.** Mismo input → mismo output. Los tests no dependen de archivos
   externos, red, GPU ni del reloj.
3. **Núcleo sin dependencias.** `core/` e `importers/` son librería estándar pura;
   sus tests no deben necesitar matplotlib, ffmpeg ni streamlit.
4. **Degradación graceful.** Falta de canales opcionales (gear, glat, abs…) es un
   caso de primera clase, no un error — y por tanto algo que **hay que testear**.

---

## Enfoque elegido

### Framework y estructura

- **pytest** — estándar de facto, fixtures simples, sin boilerplate.
- Nuevo extra opcional en `pyproject.toml`: `test = ["pytest>=8,<9"]`, instalable con
  `pip install -e ".[test]"`. Se mantiene fuera de `[full]` (es para desarrollo, no
  para el usuario final).
- Config mínima en `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["tests"]`).
- Carpeta `tests/` como espejo del paquete:

```
tests/
  conftest.py        # fixtures compartidas + el builder make_lap
  core/
    test_normalize.py
    test_compare.py
    test_corners.py
  importers/
    test_motec_csv.py
    fixtures/         # CSVs diminutos (10-20 filas), únicos datos versionados
  viz/
    test_compose.py   # solo helpers puros, sin invocar ffmpeg
  ui/
    test_app_smoke.py # arranque de la UI con streamlit.testing.AppTest
```

### Fixtures sintéticas: `make_lap`

La pieza central es un constructor `make_lap(...)` en `conftest.py` que arma una
`Lap` (el dataclass de `core/lap.py`: `channels` dict + `meta`) con un perfil de
velocidad controlado:

- Valles de velocidad ("curvas") en metros concretos → permite afirmar dónde debe
  detectar curvas el detector y cuánto tiempo se pierde.
- El tiempo se **integra a partir de distancia/velocidad**, así ir más lento cuesta
  más tiempo, igual que en pista real (clave para los tests de `compare`).
- Los canales opcionales se controlan por parámetro: quitar `gear` o `glat` del set
  prueba la degradación graceful sin tocar nada más.

Ventaja sobre versionar CSVs: legible, determinista, y los casos límite se expresan
como parámetros (`make_lap(channels=(...))`) en vez de como archivos opacos.

---

## Estrategia por capas (orden de prioridad = ROI descendente)

### Tier 1 — `core/` puro · **empezar aquí**

Es donde vive el valor del producto y no tiene I/O. Cobertura objetivo:

- `normalize.resample` — paso de rejilla correcto, longitud, interpolación lineal en
  rango, canales discretos (gear) sin fraccionar.
- `compare.delta_trace` — `delta_t` con signo correcto (piloto más lento = positivo),
  alineación por distancia; vueltas idénticas → delta ≈ 0.
- `compare._corner_metrics` y `compare.compare` — vmin, punto de frenada, flags de
  tolerancia; **y el caso sin `gear`/`glat`** (gap #1 del ROADMAP).
- `corners.detect_corners` / `extract_milestones` — nº de curvas e hitos sobre un
  trazado sintético de valles conocidos.
- `wear` — slip/assist con y sin canales de rueda.

### Tier 2 — `importers/` con CSVs fixture diminutos

Únicos datos versionados (10-20 filas, sin datos personales):

- MoTeC i2 CSV estándar, **separador `;`** (gap del ROADMAP), encoding `utf-8-sig`,
  columnas ausentes, `load_laps` de punta a punta.

### Tier 3 — helpers puros de `viz/` (sin invocar ffmpeg)

- `compose._build_filter` — afirmar que el filtro contiene `scale=iw*<f>` y el
  `setpts` solo con offset≠0. **Este test habría atrapado un bug de construcción de
  filtro como el de los asteriscos.**
- `compose._nvenc_available` — monkeypatch de `subprocess.run`: returncode≠0 → `False`,
  0 → `True`. Fija el contrato del fallback.
- `sync` — la aritmética de offset/z-score sobre señales sintéticas.

### Tier 4 — smoke de UI (barato, alto valor)

- `streamlit.testing.AppTest.from_file("fantasma/ui/app.py").run()` y afirmar
  `not at.exception`. **Atrapa el `ImportError` de arranque** que tuvimos, en CI.

---

## Tests de regresión de los bugs ya encontrados

Cada bug corregido se blinda con un test que lo fija (filosofía: un bug que no se
detecta vuelve):

| Bug | Test que lo fija |
| :-- | :-- |
| UI no arrancaba (`ImportError` tras el split) | smoke de `app.py` (Tier 4) |
| NVENC falso positivo sin GPU | `test_nvenc_available_false_on_nonzero` (Tier 3) |
| Construcción de filtro ffmpeg | `test_build_filter_scale_has_operator` (Tier 3) |
| Nombre de archivo / degradación sin canales | casos de `compare` sin gear/glat (Tier 1) |

---

## Integración continua

`.github/workflows/tests.yml` que corra `pytest` en cada push y PR, sobre **Windows**
(plataforma objetivo del proyecto) con Python 3.10–3.12. ffmpeg no es necesario si los
tests de `viz/` se quedan en los helpers puros (Tier 3) — lo cual es parte del diseño.

---

## Plan de arranque realista

Un primer PR de ~1 día que entregue: **Tier 1 + los tests de regresión + el smoke de
UI**. Cubre el núcleo, blinda lo que ya se rompió, y es suficiente para tachar el
requisito de "tests unitarios de `core/`" del camino a 1.0. Tier 2, 3 (resto) y CI
pueden venir en PRs siguientes.

## Alternativas consideradas

- **unittest (stdlib)** — descartado: más verboso, sin fixtures parametrizadas tan
  cómodas. pytest no añade peso porque es solo dependencia de desarrollo.
- **Versionar telemetría real recortada como fixtures** — descartado: viola el
  principio "motor sin datos" y es menos legible que `make_lap`. Se reserva solo para
  los CSVs diminutos de `importers/` (donde el objeto bajo prueba *es* el parseo).
- **Tests E2E que invoquen ffmpeg/matplotlib** — descartado como base: lentos, frágiles
  y dependientes del entorno. La robustez de `compose`/`overlay` se cubre testeando sus
  helpers puros; el render real se sigue validando en el QA manual con video real.
