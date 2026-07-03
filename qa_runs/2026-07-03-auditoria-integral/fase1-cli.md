# Auditoría Fase 1 — CLI y Entry Points de Empaquetado

**Fecha:** 2026-07-03
**Rama:** `codex/sgi-v2-merge`
**Auditor:** QA (claude-sonnet-4-6)
**Archivos cubiertos:**
- `fantasma/cli.py`
- `main_gui.py`
- `main.py`
- `pyproject.toml`
- `SimGhostInputs.spec`
- `tools/build_installer.py`
- `tools/installer.iss`
- `tests/test_cli.py`
- `tests/test_main_gui.py`

**Veredicto del área:** BLOQUEANTE — 3 críticos activos; el más grave hace que el CLI reporte siempre exit-code 0 aunque falle, lo que invalida cualquier uso en CI o scripting.

**Conteo por severidad:** 3 crítico · 4 mayor · 5 menor = 12 hallazgos

---

## CRÍTICOS

### C1 — `main()` descarta el exit code de todos los comandos

**Archivo:** `fantasma/cli.py:679–684`

```python
try:
    args.func(args)          # ← retorno ignorado
except Exception as e:
    print("error: %s" % e, file=sys.stderr)
    return 1
return 0                     # ← siempre 0 si no hubo excepción
```

Las funciones `cmd_ui` (línea 241) y `cmd_compose` (líneas 265, 279, 288, 302, 334)
devuelven `1` ante errores reales (streamlit ausente, scipy faltante, auto-sync sin
correlación suficiente, pace-notes sin driver). El valor de retorno nunca se captura
ni se propaga: `main()` devuelve `0` al caller y `sys.exit(main())` sale con código 0
al OS.

Consecuencia: cualquier script o paso de CI que haga `fantasma compose --auto-sync …`
creerá que tuvo éxito aunque la operación haya fallado silenciosamente. La suite de
tests tampoco valida este comportamiento (ver m3).

**Corrección mínima:** sustituir `args.func(args)` por `return args.func(args) or 0`.

---

### C2 — Versión del paquete 1.0.0 en pyproject.toml contradice v2.0.0 en installer.iss

**Archivos:** `pyproject.toml:7` / `tools/installer.iss:9`

```toml
# pyproject.toml
version = "1.0.0"
```

```iss
; tools/installer.iss
#define MyAppVersion "2.0.0"
```

El instalador generado se llama `SimGhostInputs-v2.0-Setup.exe`, pero si el paquete
Python se instalase en otro entorno, `pip show fantasma-inputs` mostraría `1.0.0`.
El CHANGELOG ya documenta la v2.0 como versión activa (sección `[Unreleased]` apunta
a un release 2.0.0).

Rompe trazabilidad de versión: herramientas de gestión de dependencias, `__version__`
accedido en runtime y la etiqueta del tag de release no son coherentes entre sí.

---

### C3 — SimGhostInputs.spec tiene ruta absoluta hardcodeada de desarrollador

**Archivo:** `SimGhostInputs.spec:8`

```python
datas=[('C:\\Users\\amedina\\AppData\\Local\\Programs\\Python\\Python311\\'
        'Lib\\site-packages\\nicegui', 'nicegui')],
```

El spec está versionado en el repositorio. Ejecutar `pyinstaller SimGhostInputs.spec`
en cualquier otra máquina (CI, PC potente, colega) falla con `OSError: nicegui not found`.
`nicegui-pack` genera su propio spec en tiempo de build, pero el spec comprometido es
el de respaldo documentado y puede ser la única referencia si `nicegui-pack` cambia
su API.

**Corrección mínima:** reemplazar la ruta hardcodeada por código dinámico:

```python
import importlib.util, os
nicegui_root = os.path.dirname(importlib.util.find_spec("nicegui").origin)
datas=[(nicegui_root, 'nicegui')],
```

o eliminar el spec del repo con una nota en el README sobre cómo regenerarlo.

---

## MAYORES

### M1 — --all-laps --format prores produce overlay_all.webm (extensión incorrecta)

**Archivo:** `fantasma/cli.py:188–190`

```python
if args.format != "png" and len(webms) > 1:
    _concat_videos(webms, os.path.join(args.output, "overlay_all.webm"), args.format)
```

La ruta de salida concatenada siempre termina en `.webm` independientemente del
formato elegido. Con `--format prores` se esperaría `overlay_all.mov` (contenedor
QuickTime para ProRes 4444 con canal alfa). Algunos NLE (DaVinci Resolve, Premiere)
rechazan archivos cuya extensión no coincide con el contenedor, o los abren en modo
de compatibilidad con pérdida de canal alfa.

**Corrección:** mapear extensión según formato:
```python
_EXT = {"webm": ".webm", "prores": ".mov", "png": ""}
ext = _EXT.get(args.format, ".webm")
_concat_videos(webms, os.path.join(args.output, "overlay_all" + ext), args.format)
```

---

### M2 — cmd_compose --auto-sync llama input() bloqueando contextos no interactivos

**Archivo:** `fantasma/cli.py:298`

```python
sel = input("¿Cual corresponde a tu vuelta? [1-%d] " % len(cands)).strip()
```

Cuando `--auto-sync` detecta varias vueltas candidatas en el video (`ambiguous=True`),
el CLI pide input del usuario por stdin. Esto bloquea indefinidamente en cualquier
contexto no interactivo: pipe de shell, llamada desde la UI NiceGUI (que ejecuta
procesos en thread/subprocess), runners de CI.

No existe ningún flag para pre-seleccionar el candidato de video (distinto de
`--lap-idx` que selecciona la vuelta de telemetría, no la del video). El ADR 0008
documenta la decisión de preguntar, pero sin escape no interactivo.

**Corrección sugerida:** añadir `--video-lap-idx INT` para seleccionar el candidato
sin interacción, y tratarlo como `required=True` cuando `--no-interactive` esté activo.

---

### M3 — Comando `fantasma ui` oculta la existencia de fantasma-ng al usuario final

**Archivos:** `fantasma/cli.py:592–596` / `pyproject.toml:38`

El subcomando `ui` lanza Streamlit, que no forma parte del exe empaquetado. El
`fantasma --help` no menciona el script `fantasma-ng` (NiceGUI, el reemplazo moderno
documentado en CHANGELOG). Un usuario que instale el exe y ejecute `fantasma ui`
recibirá "error: streamlit no instalado" con instrucciones de pip que no aplican al
exe. Tampoco existe un subcomando `gui` o `ng` dentro de `fantasma` que redirija.

El script `fantasma-ng` existe en `pyproject.toml:38` pero es invisible desde
`fantasma --help`.

**Corrección sugerida:** añadir en `fantasma ui` un bloque que detecte el exe
empaquetado (`getattr(sys, 'frozen', False)`) y redirija con un mensaje como
"en el instalador usa el ejecutable directamente o fantasma-ng".

---

### M4 — build_installer.py asume CWD = raíz del proyecto sin validarlo

**Archivo:** `tools/build_installer.py:48,83`

```python
"--icon", "docs/icon.ico",          # ruta relativa
...
script = "tools/installer.iss"      # ruta relativa
if not os.path.exists(script):
    print(f"ERROR: {script} no existe.")
```

El script usa rutas relativas al directorio de trabajo. Si se invoca desde fuera de
la raíz del proyecto (p. ej. desde un job de CI que hace `python tools/build_installer.py`
después de un `cd tools`), las rutas fallan. `os.path.exists("docs/icon.ico")` en
línea 51 retorna `False`, se elimina el flag `--icon` sin avisar, y luego el ISCC
busca `tools/installer.iss` relativo al CWD incorrecto.

**Corrección:** anclar las rutas al directorio del script:
```python
ROOT = pathlib.Path(__file__).parent.parent
icon_path = ROOT / "docs" / "icon.ico"
```

---

## MENORES

### m1 — import os duplicado dentro de funciones (ya importado a nivel módulo)

**Archivo:** `fantasma/cli.py:7,94,143,208`

`os` se importa en la línea 7 a nivel módulo. Las funciones `cmd_detect` (línea 94),
`cmd_overlay` (línea 143) y `_concat_videos` (línea 208) vuelven a hacer `import os`
dentro de su cuerpo. Son imports redundantes; no causan error pero añaden ruido y
sugieren que el módulo de nivel superior fue modificado sin revisar las funciones.

---

### m2 — Ayuda de --auto-sync no menciona el extra pip necesario

**Archivo:** `fantasma/cli.py:634`

```python
help="detectar offset automaticamente con correlacion audio vs telemetria (requiere scipy)"
```

A diferencia de `cmd_ui` (línea 238) que dice
`"ejecuta: pip install 'fantasma-inputs[ui]'"`, `--auto-sync` solo dice
"requiere scipy" sin indicar el extra `'fantasma-inputs[sync]'`. Inconsistencia
en la guía de instalación que ralentiza al usuario.

---

### m3 — Tests no validan que main() propague el exit code de los comandos

**Archivo:** `tests/test_cli.py`

Todos los tests existentes verifican comportamiento de funciones individuales
(`_overlay_progress`, `cmd_compare`, `cmd_pacenotes`). Ninguno invoca `main()` y
valida que el exit code devuelto por `main()` sea el correcto cuando un subcomando
falla. El bug C1 no sería detectado por la suite en ningún escenario actual.

**Test mínimo a añadir:**
```python
def test_main_propaga_exit_code_cmd_ui_sin_streamlit(monkeypatch):
    monkeypatch.setattr("shutil.which", lambda x: None)
    code = main(["ui"])
    assert code != 0, "main() debe retornar no-cero cuando streamlit falta"
```

---

### m4 — AppId del instalador es un UUID placeholder

**Archivo:** `tools/installer.iss:16`

```iss
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
```

Inno Setup usa el `AppId` para identificar la aplicación en el registro de Windows y
gestionar upgrades. Un UUID genérico tipo "plantilla" puede colisionar con otro
proyecto que use la misma plantilla, provocando que el instalador de SimGhostInputs
pise una instalación ajena (o viceversa). También impide que Add/Remove Programs
muestre correctamente la versión instalada.

**Corrección:** generar un UUID real único para este producto con `python -c "import uuid; print(uuid.uuid4())"` y sustituirlo.

---

### m5 — pyproject.toml version 1.0.0 no está sincronizada con ningún tag git

**Archivo:** `pyproject.toml:7`

(Relacionado con C2, dimensión adicional.) El campo `version` en pyproject.toml
debería mantenerse actualizado junto con el tag del release. Dado que la rama
`codex/sgi-v2-merge` apunta a un pre-release 2.0.0, la versión debería ser al
menos `"2.0.0"` o un pre-release como `"2.0.0rc1"`. Esto afecta también al
`fantasma.__version__` si el paquete lo expone en `fantasma/__init__.py`.

---

## Resumen ejecutivo

| # | Severidad | Hallazgo breve | Archivo:línea |
|---|-----------|----------------|---------------|
| C1 | CRÍTICO | `main()` ignora retorno de cmd_* → exit-code siempre 0 | `cli.py:679` |
| C2 | CRÍTICO | Versión 1.0.0 vs 2.0.0 entre pyproject y installer.iss | `pyproject.toml:7` |
| C3 | CRÍTICO | Spec con ruta absoluta hardcodeada C:\Users\amedina | `spec:8` |
| M1 | MAYOR | --all-laps --format prores genera overlay_all.webm | `cli.py:188` |
| M2 | MAYOR | --auto-sync llama input() en rama ambiguous (bloquea CI) | `cli.py:298` |
| M3 | MAYOR | fantasma ui no menciona fantasma-ng; oculto para usuario exe | `cli.py:592` |
| M4 | MAYOR | build_installer.py asume CWD=raíz sin validarlo | `build_installer.py:48` |
| m1 | MENOR | import os duplicado dentro de funciones | `cli.py:94,143,208` |
| m2 | MENOR | --auto-sync help no menciona extra pip [sync] | `cli.py:634` |
| m3 | MENOR | Tests no cubren exit-code propagado por main() | `test_cli.py` |
| m4 | MENOR | AppId UUID placeholder en installer.iss | `installer.iss:16` |
| m5 | MENOR | pyproject version no sincronizada con tag de release | `pyproject.toml:7` |
