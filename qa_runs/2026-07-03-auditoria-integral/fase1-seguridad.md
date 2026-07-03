# Auditoria de Seguridad — SimGhostInputs v2.0.0-pre
**Fecha:** 2026-07-03  
**Rama:** codex/sgi-v2-merge  
**Tipo:** Auditoria defensiva pre-release (app de escritorio local, AGPL publico)  
**Metodologia:** Descubrimiento por agente + filtrado paralelo de falsos positivos por agentes independientes  

---

## Veredicto

Un hallazgo MEDIO confirmado; cero hallazgos ALTOS. El codigo Python es seguro en sus superficies criticas (subprocess, pickle, parseo de archivos). El unico riesgo concreto es la interfaz NiceGUI/Streamlit que escucha en 0.0.0.0 sin autenticacion, con un campo de path de salida sin sanear que un atacante LAN podria explotar para escribir archivos a paths arbitrarios del sistema.

---

## Conteo por severidad

| Severidad | Confirmados | Descartados como FP |
|-----------|-------------|---------------------|
| ALTO      | 0           | —                   |
| MEDIO     | 1           | —                   |
| BAJO / Informativo | 2  | —                   |
| Falsos positivos descartados | — | 3           |

---

## Superficie 1: Parseo de archivos CSV / XLSX no confiables

### Resultado: LIMPIO

**XLSX** — `fantasma/importers/motec_csv.py`: cargado con `openpyxl.load_workbook(path, read_only=True)`. El modo `read_only=True` activa la lectura en streaming y deshabilita la evaluacion de formulas y macros. openpyxl 3.x no procesa entidades externas (XXE). No hay riesgo de inyeccion de formulas ni de entidades.

**CSV** — `csv.reader` estandar de Python. Sin evaluacion de formulas. Sin ejecucion de codigo.

**Conclusiones:**
- No hay path traversal en nombres de archivo: los paths provienen de dialogos del SO.
- No hay formula injection: openpyxl no evalua formulas.
- No hay XXE: openpyxl no expande entidades externas.
- El unico riesgo es la carga en memoria de un archivo gigante (DOS, excluido por criterio).

---

## Superficie 2: Invocacion de ffmpeg y subprocess

### Resultado: LIMPIO

| Verificacion | Resultado |
|---|---|
| `shell=True` | Cero ocurrencias en todo el codebase |
| Comandos construidos con strings del usuario | No encontrados |
| `subprocess.Popen` con string en vez de lista | No encontrado |
| Argumentos de filtro de ffmpeg con datos del usuario | Valores float formateados `%.6f` — no inyectables |

Todos los calls a ffmpeg (`compose.py`, `overlay.py`, `sync.py`, `pacenotes.py`, `hud_preview.py`) usan la forma de lista de argumentos. Los valores de `scale` y `offset` provienen de sliders UI (float), formateados como `%.6f`. Las posiciones vienen de diccionarios hardcodeados. El concat list de `cli.py` usa paths generados internamente, no del usuario.

---

## Superficie 3: pickle / multiprocessing entre procesos propios

### Resultado: RIESGO BAJO CONFIRMADO — sin accion requerida

`fantasma/viz/overlay.py` + `fantasma/viz/_overlay_worker.py`: el proceso principal serializa arrays numpy calculados internamente a un archivo `.pkl` en el temp del SO. El worker subprocess lo deserializa.

- Los datos pickeados son arrays numpy del pipeline interno, no contenido raw del archivo del usuario.
- Un atacante local ya tiene los mismos privilegios; la race en el tempfile es teorica y de ventana de milisegundos.
- Veredicto: riesgo negligible en el modelo de amenaza de app de escritorio local.

---

## Superficie 4: UI local — interfaz de red y archivos servidos

### HALLAZGO MEDIO — M-01: NiceGUI/Streamlit escucha en 0.0.0.0 sin autenticacion

**Severidad:** MEDIO  
**Confianza:** 7/10  
**Archivos:**
- `fantasma/ui/ng_app.py`, lineas 284-292
- `main.py`, linea 5
- `fantasma/cli.py`, linea 243 (Streamlit)

**Descripcion:**

`ui.run()` no especifica el parametro `host`. El valor por defecto de NiceGUI es `host='0.0.0.0'`, haciendo que el servidor FastAPI/uvicorn escuche en todas las interfaces. Ninguna ruta tiene middleware de autenticacion, login, ni restriccion de IP. Confirmado por inspeccion directa de los archivos.

```python
# ng_app.py lineas 284-292
ui.run(
    title="SimGhostInputs",
    native=not headless,
    storage_secret="sgi-v2-secret",
    port=8765,
    # host= NO esta presente — defaultea a 0.0.0.0
)
```

**Camino de ataque (atacante en la misma LAN):**

1. Navegar a `http://<IP>:8765/` — la ruta raiz no tiene guard de acceso.
2. Usar `ui.upload` en `ng_step1.py` / `ng_step4.py` para subir archivos a disco via `_save_upload()` en `ng_helpers.py`.
3. Ingresar un path arbitrario en `out_folder_input` (texto libre, sin sanear); el codigo ejecuta `os.makedirs(_out_folder_val, exist_ok=True)` y escribe la salida de ffmpeg al path elegido por el atacante.

**Primitivas habilitadas:** escritura de archivo (MP4) a path arbitrario del usuario, creacion de directorios arbitrarios. No es RCE directo.

**Mitigacion — una linea por callsite:**
```python
# ng_app.py y main.py
ui.run(..., host="127.0.0.1", ...)

# cli.py — agregar al comando streamlit
["streamlit", "run", app, "--server.address", "127.0.0.1", "--server.port", str(args.port)]
```

### Archivos servidos arbitrariamente

**Resultado: LIMPIO** — no hay `ui.add_static_files()` ni rutas que expongan paths del filesystem. Las graficas se sirven como bytes en memoria.

---

## Superficie 5: Secretos y rutas personales en el repositorio

### HALLAZGO INFORMATIVO — I-01: Path absoluto del desarrollador en SimGhostInputs.spec

**Severidad:** INFORMATIVO (no es vulnerabilidad de seguridad)  
**Archivo:** `SimGhostInputs.spec`, linea 8

```
'C:\\Users\\amedina\\AppData\\Local\\Programs\\Python\\Python311\\Lib\\site-packages\\nicegui'
```

**Analisis:** El username `amedina` ya es publico en los commits. El path no habilita ningun ataque. El problema es de mantenibilidad: el spec no funciona en ninguna otra maquina. Filtrado como falso positivo de seguridad; es un issue de build hygiene.

### HALLAZGO INFORMATIVO — I-02: Paths de datos de prueba hardcodeados en tests

**Severidad:** INFORMATIVO  
**Archivos:** `tests/ui/test_e2e_wizard.py` (linea 37), `tests/ui/visual/test_e2e_playwright_wizard.py` (lineas 28-32)

```python
r"C:\Repositorio personal\Paterial para test (no es un repo)"
```

Tests decorados con `pytest.mark.skip` cuando el path no existe; no afectan CI. Excluidos por criterio (archivos de test). Issue de portabilidad, no de seguridad.

### API keys, passwords, tokens

**Resultado: LIMPIO** — No se encontraron API keys, tokens OAuth, ni credenciales de servicios externos en ningun archivo del repositorio.

`storage_secret="sgi-v2-secret"`: revisado y descartado como falso positivo. En una app de escritorio de usuario unico sin datos sensibles en el storage del browser, un secret predecible no habilita ningun ataque concreto. Si se aplica el fix M-01, el servidor queda inaccesible desde la red y este punto se vuelve irrelevante.

---

## Superficie 6: Dependencias con CVEs conocidos

### Resultado: NO AUDITABLE — sin lockfile

`pyproject.toml` especifica rangos de version (`openpyxl>=3,<4`, `nicegui>=3.14,<4`, etc.). Sin `poetry.lock`, `requirements.txt` fijado, ni `uv.lock`. No es posible verificar versiones exactas contra CVE databases.

Los rangos cubren versiones mayores modernas sin CVEs criticos conocidos en el rango actual.

**Recomendacion:** Generar lockfile (`uv lock` o `pip freeze > requirements-lock.txt`) como parte del proceso de release.

---

## Resumen de hallazgos

| ID | Severidad | Descripcion breve | Accion |
|----|-----------|-------------------|--------|
| M-01 | MEDIO | NiceGUI/Streamlit en 0.0.0.0 sin auth; path de salida controlable por atacante LAN | `host="127.0.0.1"` en ambos `ui.run()` y Streamlit |
| I-01 | INFORMATIVO | Path absoluto del dev en SimGhostInputs.spec | Build hygiene; sin urgencia de seguridad |
| I-02 | INFORMATIVO | Paths de datos de prueba hardcodeados | Portabilidad; excluido como test file |

---

## Que esta limpio

- `shell=True`: cero ocurrencias en todo el codebase
- Command injection en subprocess: todos los calls usan lista de argumentos
- Formula injection en XLSX: openpyxl con `read_only=True`, sin evaluacion
- XXE en XLSX: openpyxl no procesa entidades externas
- pickle en datos externos: `pickle.load` solo sobre datos generados internamente
- SQL injection: no hay base de datos ni queries SQL en el proyecto
- Template injection: no se usan motores de plantillas que evaluen expresiones
- Inyeccion en filtros de ffmpeg: valores float-formateados o de diccionarios hardcodeados
- Archivos arbitrarios via HTTP: NiceGUI no expone rutas de filesystem
- XSS en WebView local: vector tecnico existe (corner names en `ui.html()`) pero impacto nulo — sin datos sensibles, sin sesion que hijackear, sin path a RCE desde el WebView

---

## Metodologia

1. **Descubrimiento:** Agente leyo todos los archivos fuente clave, trazo flujos de datos desde entradas del usuario hasta operaciones sensibles, identifico 9 candidatos iniciales.
2. **Filtrado paralelo:** Tres agentes independientes revisaron los candidatos de mayor confianza aplicando criterios de exclusion y leyendo el codigo real.
3. **Resultado:** 3 falsos positivos descartados, 1 hallazgo MEDIO confirmado, 2 hallazgos informativos.

---

*Auditoria defensiva pre-release v2.0.0 — SimGhostInputs*  
*Herramienta: Claude Code security-review + agentes de filtrado paralelo*
