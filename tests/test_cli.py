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
import sys
from types import SimpleNamespace

import pytest

from fantasma.cli import (
    _force_utf8_console,
    _load_corners_json,
    _overlay_progress,
    cmd_compare,
    cmd_pacenotes,
    main,
)
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
    """Homologa la firma con el callback de la UI (RenderJob.progress_cb en ng_helpers.py):
    def progress_cb(self, n, total, status=None) — mismos tres parametros (sin self)."""
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
        sound_profile="seno",
    )
    cmd_pacenotes(args)
    assert (out / "metadata.json").exists()
    # countdown anclado en la frenada (ADR 0025): tics en 1680 y 1740, "ya" en 1800,
    # gas en 1900; el apex (1847) se descarta por quedar a <50 m del ancla del countdown
    assert len(list(out.glob("*.wav"))) == 4


def test_load_corners_json_extrae_gear_shifts_si_estan():
    """_load_corners_json expone 'gear_shifts' (escrito por cmd_detect) para
    que cmd_pacenotes lo reenvie a build_pack; ausente -> lista vacia, nunca
    KeyError."""
    import json

    data_con = {
        "corners": [],
        "gear_shifts": [{"distance": 500, "gear_from": 2, "gear_to": 3}],
    }
    data_sin = {"corners": []}

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        p_con = Path(tmp) / "con.json"
        p_sin = Path(tmp) / "sin.json"
        p_con.write_text(json.dumps(data_con), encoding="utf-8")
        p_sin.write_text(json.dumps(data_sin), encoding="utf-8")

        assert _load_corners_json(str(p_con))["gear_shifts"] == data_con["gear_shifts"]
        assert _load_corners_json(str(p_sin))["gear_shifts"] == []


def test_pacenotes_cli_reenvia_gear_shifts_a_build_pack(tmp_path, monkeypatch):
    """cmd_pacenotes lee 'gear_shifts' del JSON de corners y lo pasa tal cual
    a build_pack -- wiring end-to-end de la vuelta de referencia."""
    import json

    corners = tmp_path / "corners.json"
    compare = tmp_path / "corners_compare.csv"
    out = tmp_path / "pace_notes"
    corners.write_text(
        json.dumps(
            {
                "corners": [],
                "gear_shifts": [{"distance": 500, "gear_from": 2, "gear_to": 3}],
            }
        ),
        encoding="utf-8",
    )
    compare.write_text("id,name,apex_d,time_lost\n", encoding="utf-8")

    captured = {}

    def _fake_build_pack(rows, corners_arg, outdir, **kwargs):
        captured["gear_shifts"] = kwargs.get("gear_shifts")
        return {"outdir": str(outdir), "files": [], "entries": 0}

    import fantasma.viz.pacenotes as pacenotes_mod

    monkeypatch.setattr(pacenotes_mod, "build_pack", _fake_build_pack)

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
        sound_profile="seno",
    )
    cmd_pacenotes(args)
    assert captured["gear_shifts"] == [{"distance": 500, "gear_from": 2, "gear_to": 3}]


def test_main_propaga_exit_code_del_subcomando(monkeypatch):
    """main() retorna el valor que devuelve el subcomando: cli.py return args.func(args) or 0.

    Monkeypatch de cmd_laps para que devuelva 1; main(["laps", "x.csv"]) debe retornar 1.
    """
    monkeypatch.setattr("fantasma.cli.cmd_laps", lambda args: 1)
    assert main(["laps", "cualquier.csv"]) == 1


def test_main_retorna_1_cuando_subcomando_lanza_excepcion(monkeypatch):
    """main() atrapa Exception y retorna 1: cli.py except Exception → return 1.

    Monkeypatch de cmd_laps para que lance RuntimeError; main no debe reraise y debe retornar 1.
    """

    def _cmd_boom(args):
        raise RuntimeError("error simulado")

    monkeypatch.setattr("fantasma.cli.cmd_laps", _cmd_boom)
    assert main(["laps", "cualquier.csv"]) == 1


def _pacenotes_fixture(tmp_path):
    """Escribe un corners.json + compare.csv minimos y devuelve sus rutas."""
    import json

    corners = tmp_path / "corners.json"
    compare = tmp_path / "corners_compare.csv"
    corners.write_text(
        json.dumps(
            {
                "corners": [
                    {
                        "id": "C01",
                        "name": "Hatzenbach",
                        "milestones": {
                            "brake_start": {"d": 1800, "v": 216},
                            "brake_release": {"d": 1950},
                            "turn_in": {"d": 2050},
                            "throttle_on": {"d": 2200},
                            "full_throttle": {"d": 2400},
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    compare.write_text(
        "id,name,apex_d,time_lost,flags\nC01,Hatzenbach,2000,0.6,vmin+frenada\n",
        encoding="utf-8",
    )
    return corners, compare


def _wavs(directory):
    return {p.name: p.read_bytes() for p in sorted(directory.glob("*.wav"))}


def test_pacenotes_cli_sound_profile_flag_e2e(tmp_path):
    """PROBLEMA 1: --sound-profile fluye por el e2e hasta build_pack.

    Blinda que la feature ya no esta muerta de cara al usuario: el flag existe,
    su default es 'seno' byte-identico, y otra paleta produce WAVs distintos.
    Antes de 759413f+fix la CLI no exponia el perfil (grep solo lo hallaba en
    pacenotes.py) y este e2e no podia pedir una paleta.
    """
    corners, compare = _pacenotes_fixture(tmp_path)
    d_default = tmp_path / "pn_default"
    d_seno = tmp_path / "pn_seno"
    d_timbre = tmp_path / "pn_timbre"

    base = ["pacenotes", "--corners", str(corners), "--compare", str(compare), "--top", "1"]
    assert main([*base, "--output-dir", str(d_default)]) == 0
    assert main([*base, "--output-dir", str(d_seno), "--sound-profile", "seno"]) == 0
    assert main([*base, "--output-dir", str(d_timbre), "--sound-profile", "timbre"]) == 0

    wav_default = _wavs(d_default)
    wav_seno = _wavs(d_seno)
    wav_timbre = _wavs(d_timbre)

    assert wav_default, "el pack default no genero WAVs"
    # Default == 'seno' explicito, byte a byte.
    assert wav_default == wav_seno
    # 'timbre' cambia la forma de onda: mismos nombres de archivo, bytes distintos.
    assert set(wav_default) == set(wav_timbre)
    assert any(wav_default[n] != wav_timbre[n] for n in wav_default)


def test_pacenotes_cli_sound_profile_invalido_falla_con_codigo(tmp_path, capsys):
    """Un --sound-profile invalido corta con SystemExit (exit code != 0) y un
    mensaje accionable que lista las opciones validas (argparse choices)."""
    corners, compare = _pacenotes_fixture(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(
            [
                "pacenotes",
                "--corners",
                str(corners),
                "--compare",
                str(compare),
                "--output-dir",
                str(tmp_path / "out"),
                "--sound-profile",
                "bombo",
            ]
        )
    assert exc.value.code != 0
    err = capsys.readouterr().err
    assert "bombo" in err and "seno" in err and "timbre" in err
