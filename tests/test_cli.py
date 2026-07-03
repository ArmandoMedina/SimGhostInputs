"""Regresion CLI — contratos de callbacks de progreso.

El test central (test_overlay_progress_acepta_status_kwarg) habria fallado con
el codigo anterior, donde el CLI definia:

    def progress(n, total):   # dentro de cmd_overlay

y overlay.py lo invoca con:

    progress(enc, n_frames, status="Codificando video... frame N / M")

provocando TypeError: progress() got an unexpected keyword argument 'status',
que el except BaseException mataba ffmpeg y re-lanzaba -> webm vacio + exit 1.
"""

import io
import shutil
import sys
from types import SimpleNamespace

import pytest

from fantasma.cli import _force_utf8_console, _overlay_progress, cmd_compare, cmd_pacenotes, main
from fantasma.core.lap import Lap


def test_overlay_progress_acepta_status_kwarg():
    """Habria fallado antes del fix: overlay.py llama progress(n, total, status=...)
    pero el CLI definia def progress(n, total): sin aceptar status."""
    # No debe lanzar TypeError
    _overlay_progress(5, 100, status="Codificando video... frame 5 / 100")


def test_overlay_progress_sin_status_kwarg():
    """Tambien funciona con llamada puramente posicional."""
    _overlay_progress(5, 100)


def test_overlay_progress_total_cero_no_crashea():
    """Division por cero protegida cuando total=0."""
    _overlay_progress(0, 0, status="iniciando")


def test_overlay_progress_firma_compatible_con_ui():
    """Homologa la firma con el callback de la UI (_helpers.py:222):
    def _cb(n, total, status=None) — mismos tres parametros."""
    import inspect

    sig = inspect.signature(_overlay_progress)
    params = list(sig.parameters.keys())
    assert params == ["n", "total", "status"]
    # status debe tener default None
    assert sig.parameters["status"].default is None


def test_force_utf8_console_evita_unicodeerror_con_sigma():
    """Habria fallado antes del fix: imprimir 'σ' (calidad de sincronia) en una
    consola cp1252 —el default de Windows— lanza UnicodeEncodeError ('charmap'
    codec can't encode '\\u03c3'), visto en `fantasma compose`. _force_utf8_console
    reconfigura stdout a utf-8 y el print procede."""
    buf = io.BytesIO()
    stream = io.TextIOWrapper(buf, encoding="cp1252")
    old = sys.stdout
    sys.stdout = stream
    try:
        _force_utf8_console()  # reconfigura el stream a utf-8
        print("  -> offset: 1.234 s  (z=5.5 σ)")  # con cp1252 esto reventaria
        sys.stdout.flush()
    finally:
        sys.stdout = old
    assert "σ".encode("utf-8") in buf.getvalue()


def test_force_utf8_console_no_crashea_si_no_hay_reconfigure():
    """Streams sin .reconfigure (p. ej. ya redirigidos a un objeto simple) no
    deben romper: el fix es silencioso."""
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = object()  # sin metodo reconfigure
    sys.stderr = object()
    try:
        _force_utf8_console()  # no debe lanzar
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def test_compare_avisa_driver_sin_distancia(monkeypatch, tmp_path):
    """Regresion real: un CSV sin distancia no debe escapar como NoneType."""
    ref = Lap(
        channels={
            "time": [0.0, 1.0, 2.0],
            "dist": [0.0, 10.0, 20.0],
            "speed": [100.0, 90.0, 110.0],
        }
    )
    drv = Lap(channels={"time": [0.0, 1.0, 2.0], "speed": [100.0, 90.0, 110.0]})

    def fake_load(path, column_map=None, lap_index=None):
        lap = ref if path == "ref.csv" else drv
        return [lap], lap

    monkeypatch.setattr("fantasma.cli._load_lap", fake_load)

    args = SimpleNamespace(
        reference="ref.csv",
        driver="drv.csv",
        lap=None,
        corners=None,
        step=5.0,
        map=None,
        output=str(tmp_path),
        no_charts=True,
        charts_top=5,
    )
    with pytest.raises(ValueError, match="piloto no tiene canal de distancia"):
        cmd_compare(args)


def test_main_propaga_exit_code_cuando_subcomando_falla(monkeypatch):
    """main() debe retornar no-cero cuando un subcomando devuelve error (C1)."""
    monkeypatch.setattr(shutil, "which", lambda x: None)
    code = main(["ui"])
    assert code != 0, "main() debe propagar el exit-code no-cero de cmd_ui"


def test_pacenotes_cli_genera_pack(tmp_path):
    corners = tmp_path / "corners.json"
    compare = tmp_path / "corners_compare.csv"
    out = tmp_path / "pace_notes"
    corners.write_text(
        """{
  "corners": [
    {
      "id": "C01",
      "name": "Hatzenbach",
      "milestones": {
        "brake": {"d": 1800},
        "apex": {"d": 1847},
        "gas": {"d": 1900}
      }
    }
  ]
}""",
        encoding="utf-8",
    )
    compare.write_text(
        "id,name,apex_d,time_lost\nC01,Hatzenbach,1847,0.4\n",
        encoding="utf-8",
    )
    args = SimpleNamespace(
        corners=str(corners),
        compare=str(compare),
        top=1,
        mode="tones",
        lang="es-MX",
        output_dir=str(out),
        brake_freq=880,
        apex_freq=440,
        gas_freq=220,
        tone_duration=0.05,
        volume=0.8,
        legacy_all_tones=False,
    )
    cmd_pacenotes(args)
    assert (out / "metadata.json").exists()
    assert len(list(out.glob("*.wav"))) == 3
