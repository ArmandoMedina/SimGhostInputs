"""Entry point para nicegui-pack / PyInstaller.

ng_app.py usa relative imports que fallan cuando PyInstaller lo ejecuta como
__main__. Este wrapper importa run() de forma absoluta, lo que funciona tanto
en modo paquete como en el exe empaquetado.
"""

import multiprocessing

from fantasma.ui.ng_app import run

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
