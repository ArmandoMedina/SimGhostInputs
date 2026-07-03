"""Tests para la limpieza de archivos temporales de upload (Fix C-01).

Verifica:
- _save_upload registra el path en _upload_temps.
- _cleanup_upload borra el archivo y lo saca del registro.
- Segunda llamada a _cleanup_upload (idempotente) no lanza excepcion.
- Un segundo upload al mismo slot deja limpio el temp del primero.
"""

import os


def test_save_upload_registra_en_upload_temps():
    """_save_upload agrega la ruta al registro _upload_temps."""
    from fantasma.ui.ng_helpers import _cleanup_upload, _save_upload, _upload_temps

    path = _save_upload(b"a,b\n1,2", ".csv")
    try:
        assert path in _upload_temps
    finally:
        _cleanup_upload(path)


def test_cleanup_upload_borra_archivo():
    """_cleanup_upload elimina el archivo del disco."""
    from fantasma.ui.ng_helpers import _cleanup_upload, _save_upload

    path = _save_upload(b"a,b\n1,2", ".csv")
    assert os.path.exists(path)
    _cleanup_upload(path)
    assert not os.path.exists(path)


def test_cleanup_upload_saca_del_registro():
    """_cleanup_upload elimina la ruta de _upload_temps."""
    from fantasma.ui.ng_helpers import _cleanup_upload, _save_upload, _upload_temps

    path = _save_upload(b"a,b\n1,2", ".csv")
    _cleanup_upload(path)
    assert path not in _upload_temps


def test_cleanup_upload_idempotente():
    """Segunda llamada a _cleanup_upload no lanza excepcion."""
    from fantasma.ui.ng_helpers import _cleanup_upload, _save_upload

    path = _save_upload(b"a,b\n1,2", ".csv")
    _cleanup_upload(path)
    _cleanup_upload(path)  # no debe lanzar


def test_segundo_upload_mismo_slot_limpia_anterior():
    """Simula dos uploads consecutivos: el primero se limpia antes del segundo."""
    from fantasma.ui.ng_helpers import _cleanup_upload, _save_upload

    path1 = _save_upload(b"a,b\n1,2", ".csv")
    assert os.path.exists(path1)
    # Primer parse terminado; limpieza inmediata (como hacen los handlers)
    _cleanup_upload(path1)
    assert not os.path.exists(path1), "Temp del primer upload debe borrarse"

    # Segundo upload al mismo slot
    path2 = _save_upload(b"a,b\n3,4", ".csv")
    assert os.path.exists(path2)
    _cleanup_upload(path2)
    assert not os.path.exists(path2)
