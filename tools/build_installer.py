#!/usr/bin/env python3
"""Empaqueta SimGhostInputs con nicegui-pack (--onedir).

Uso:
    python tools/build_installer.py           # solo bundle
    python tools/build_installer.py --inno    # bundle + compilar Inno Setup
"""

import argparse
import os
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

    # Verificar nicegui-pack
    result = subprocess.run(["pip", "show", "nicegui-pack"], capture_output=True)
    if result.returncode != 0:
        print("ERROR: nicegui-pack no instalado. Ejecuta: pip install nicegui-pack")
        sys.exit(1)

    # Limpiar build anterior
    for d in ["dist", "build"]:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Limpiado: {d}/")

    # Empaquetar con nicegui-pack
    cmd = [
        "nicegui-pack",
        "--onedir",
        "--name",
        "SimGhostInputs",
        "--windowed",  # sin terminal visible
        "--icon",
        "docs/icon.ico",  # icono (si existe; se quita si no esta)
        "fantasma/ui/ng_app.py",
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


def _compile_inno():
    iscc = shutil.which("iscc") or r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if not os.path.exists(iscc):
        print("AVISO: ISCC.exe no encontrado. Instala Inno Setup 6 para compilar el instalador.")
        print("Descarga: https://jrsoftware.org/isdl.php")
        return
    script = "tools/installer.iss"
    if not os.path.exists(script):
        print(f"ERROR: {script} no existe.")
        sys.exit(1)
    result = subprocess.run([iscc, script])
    if result.returncode == 0:
        print("Instalador generado en dist/")
    else:
        print("ERROR: ISCC fallo.")
        sys.exit(1)


if __name__ == "__main__":
    main()
