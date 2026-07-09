#!/usr/bin/env python3
"""Empaqueta SimGhostInputs con nicegui-pack (--onedir).

Uso:
    python tools/build_installer.py           # solo bundle
    python tools/build_installer.py --inno    # bundle + compilar Inno Setup
"""

import argparse
import os
import re
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inno",
        action="store_true",
        help="Compilar script Inno Setup tras el bundle",
    )
    args = parser.parse_args()

    # Verificar nicegui-pack: es un script que viene DENTRO del paquete nicegui
    # (extra 'ui-ng'), no un paquete de PyPI aparte.
    if not shutil.which("nicegui-pack"):
        print("ERROR: nicegui-pack no encontrado en PATH.")
        print('Instala el extra que lo trae: pip install -e ".[ui-ng]"')
        sys.exit(1)

    # Verificar pyinstaller: nicegui-pack lo invoca como subproceso y, si falta,
    # muere con un WinError 2 opaco. nicegui NO lo declara como dependencia.
    if not shutil.which("pyinstaller"):
        print("ERROR: pyinstaller no encontrado en PATH.")
        print('nicegui-pack lo necesita. Instala: pip install -e ".[pack]"')
        sys.exit(1)

    # Limpiar build anterior
    for d in ["dist", "build"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Limpiado: {d}/")

    # Empaquetar con nicegui-pack
    # Entry point: main_gui.py (wrapper sin relative imports).
    # ng_app.py usa "from . import ..." que falla como __main__ en PyInstaller.
    cmd = [
        "nicegui-pack",
        "--onedir",
        "--name",
        "SimGhostInputs",
        "--windowed",  # sin terminal visible
        "--icon",
        "docs/icon.ico",  # icono (si existe; se quita si no esta)
        "main_gui.py",
    ]
    # Si no hay icono, quitar el flag
    if not os.path.exists("docs/icon.ico"):
        cmd = [c for c in cmd if c not in ("--icon", "docs/icon.ico")]

    print("Ejecutando:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("ERROR: nicegui-pack fallo.")
        sys.exit(1)

    # Medir bundle
    dist_dir = os.path.join("dist", "SimGhostInputs")
    if os.path.exists(dist_dir):
        total = sum(
            os.path.getsize(os.path.join(r, f)) for r, _, files in os.walk(dist_dir) for f in files
        )
        print(f"Bundle size: {total / 1024 / 1024:.1f} MB en {dist_dir}/")
    else:
        print(
            "AVISO: dist/SimGhostInputs/ no encontrado"
            " -- verifica el nombre de salida de nicegui-pack"
        )

    if args.inno:
        _compile_inno()


def _get_version() -> str:
    """Devuelve la version del proyecto.

    Lee fantasma/__init__.py (SSOT de version): el atributo __version__ es un
    literal que setuptools lee por AST en build time. Cae a importlib.metadata
    solo si el archivo no esta a mano (p. ej. ejecutado fuera del repo).
    """
    init_py = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "fantasma",
        "__init__.py",
    )
    if os.path.exists(init_py):
        with open(init_py, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^__version__\s*=\s*["\']([^"\']+)["\']', line)
                if m:
                    return m.group(1)
    try:
        from importlib.metadata import version as pkg_version

        return pkg_version("fantasma-inputs")
    except Exception:
        return "0.0.0"


def _compile_inno():
    _candidates = [
        shutil.which("iscc"),
        shutil.which("ISCC"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    ]
    iscc = next((c for c in _candidates if c and os.path.exists(c)), None)
    if iscc is None:
        # Falla duro: --inno es explicito, y salir en silencio dejaba el build
        # "verde" sin Setup.exe -- el error aparecia despues, en el paso de
        # upload de release.yml, apuntando al sitio equivocado.
        print("ERROR: ISCC.exe no encontrado. Instala Inno Setup 6 para compilar el instalador.")
        print("Descarga: https://jrsoftware.org/isdl.php")
        sys.exit(1)
    script = "tools/installer.iss"
    if not os.path.exists(script):
        print(f"ERROR: {script} no existe.")
        sys.exit(1)
    ver = _get_version()
    print(f"Version detectada: {ver}")
    result = subprocess.run([iscc, f"/DMyAppVersion={ver}", script])
    if result.returncode == 0:
        installer = os.path.join("dist", f"SimGhostInputs-v{ver}-Setup.exe")
        print(f"Instalador generado: {installer}")
    else:
        print("ERROR: ISCC fallo.")
        sys.exit(1)


if __name__ == "__main__":
    main()
