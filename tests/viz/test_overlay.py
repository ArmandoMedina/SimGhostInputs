"""Tier 3 — helper puro de las luces ABS/TC del overlay (sin matplotlib ni ffmpeg).

`_flag_recent_grid` decide si la luz prende: True si el flag (rejilla 1 m) estuvo
activo en los últimos `hold` m hasta el cursor. Es lo que da el comportamiento de
luz instantánea con retención corta en vez del viejo conteo por ventana.
"""

import io
from unittest.mock import MagicMock, patch

import pytest

np = pytest.importorskip("numpy")
from fantasma.viz import overlay  # noqa: E402


def test_flag_recent_grid_none_is_off():
    assert overlay._flag_recent_grid(None, 10, 8) is False


def test_flag_recent_grid_on_at_cursor():
    g = np.zeros(20)
    g[10] = 1.0
    assert overlay._flag_recent_grid(g, 10, 8) is True


def test_flag_recent_grid_holds_within_window():
    g = np.zeros(20)
    g[5] = 1.0
    # cursor 6 m después de la activación, dentro de la retención de 8 m
    assert overlay._flag_recent_grid(g, 11, 8) is True


def test_flag_recent_grid_off_beyond_hold():
    g = np.zeros(30)
    g[5] = 1.0
    # cursor 20 m después: fuera de la retención de 8 m
    assert overlay._flag_recent_grid(g, 25, 8) is False


def test_flag_recent_grid_off_when_never_active():
    assert overlay._flag_recent_grid(np.zeros(20), 10, 8) is False


def test_flag_recent_grid_clamps_index_past_end():
    g = np.zeros(10)
    g[9] = 1.0
    # cursor más allá del final: se acota al último índice y sigue detectando
    assert overlay._flag_recent_grid(g, 50, 8) is True


# ── _run_ffmpeg: captura de stderr ───────────────────────────────────────────


def test_run_ffmpeg_raises_runtime_error_with_stderr_tail():
    """_run_ffmpeg: returncode != 0 → RuntimeError con tail de stderr de ffmpeg."""
    fake_proc = MagicMock()
    fake_proc.returncode = 1
    fake_proc.stdout = iter([])

    # Pre-populamos el "stderr" como bytes (modo w+b) como si ffmpeg lo hubiera escrito.
    # El código hará seek(0) antes de leer, por lo que el contenido es visible.
    fake_err = io.BytesIO(b"Error: codec libvpx-vp9 not found\nInvalid encoder.\n")

    with patch("fantasma.viz.overlay.tempfile.TemporaryFile", return_value=fake_err):
        with patch("subprocess.Popen", return_value=fake_proc):
            with pytest.raises(RuntimeError, match="libvpx-vp9"):
                overlay._run_ffmpeg(["ffmpeg", "-y", "dummy.webm"], 100, None)


def test_run_ffmpeg_non_utf8_stderr_does_not_raise_unicode_error():
    """_run_ffmpeg: bytes no-UTF8 en stderr son reemplazados, no lanzan UnicodeDecodeError."""
    fake_proc = MagicMock()
    fake_proc.returncode = 1
    fake_proc.stdout = iter([])

    # b"\xf3" no es UTF-8 válido; errors="replace" lo convierte a U+FFFD (u"�")
    fake_err = io.BytesIO(b"c\xf3dec error")

    with patch("fantasma.viz.overlay.tempfile.TemporaryFile", return_value=fake_err):
        with patch("subprocess.Popen", return_value=fake_proc):
            with pytest.raises(RuntimeError) as exc_info:
                overlay._run_ffmpeg(["ffmpeg", "-y", "dummy.webm"], 100, None)

    msg = str(exc_info.value)
    assert "c" in msg and "dec error" in msg, "El texto alrededor del byte inválido debe aparecer"
    assert "�" in msg, "El byte inválido debe sustituirse por el carácter de reemplazo U+FFFD"


# ── render paralelo: collect round-robin ─────────────────────────────────────


def test_render_parallel_collect_round_robin(tmp_path):
    """Workers que terminan en orden inverso son recolectados por orden de finalización.

    Tres chunks de tamaños distintos: worker 2 (5 frames) termina primero,
    luego worker 1 (10 frames), luego worker 0 (15 frames, el más lento).
    La aserción discriminante: collected_done[0] == 5, es decir los frames del
    worker rápido se cuentan antes de que worker 0 haya terminado.
    Un código secuencial que bloquee en worker 0 daría collected_done[0] == 15.
    """
    rounds = [0]

    def make_proc(finish_round):
        m = MagicMock()
        m.returncode = 0

        def poll():
            return 0 if rounds[0] >= finish_round else None

        m.poll = poll
        return m

    # worker 0 → chunk (0,15),  15 frames, finish_round=4 (el más lento)
    # worker 1 → chunk (15,25), 10 frames, finish_round=2
    # worker 2 → chunk (25,30),  5 frames, finish_round=0 (inmediato)
    procs_queue = [make_proc(4), make_proc(2), make_proc(0)]
    proc_iter = iter(procs_queue)

    fake_file = MagicMock()
    fake_file.name = str(tmp_path / "fake.pkl")

    collected_done = []

    def fake_progress(done, total):
        collected_done.append(done)

    ds = np.arange(0.0, 200.0, 1.0)
    ch = {
        "throttle": np.zeros(200),
        "brake": np.zeros(200),
        "steering": np.zeros(200),
        "speed": np.zeros(200),
    }
    t_arr = np.linspace(0.0, 3.0, 300)
    d_arr = np.linspace(0.0, 199.0, 300)
    base = (
        ds,
        ch,
        ch,
        0.0,
        0.0,
        None,
        None,
        [{"delta_t": 0.0}] * 40,
        40,
        5.0,
        t_arr,
        d_arr,
        [],
        str(tmp_path),
        30,
        0.0,
        None,
        None,
        0,
    )

    n_frames = 30
    chunks = [(0, 15), (15, 25), (25, 30)]

    with patch("subprocess.Popen", side_effect=lambda *a, **k: next(proc_iter)):
        with patch("tempfile.NamedTemporaryFile", return_value=fake_file):
            with patch("pickle.dump"):
                with patch("os.unlink"):
                    with patch(
                        "time.sleep",
                        side_effect=lambda t: rounds.__setitem__(0, rounds[0] + 1),
                    ):
                        overlay._render_parallel(chunks, base, n_frames, fake_progress)

    assert collected_done, "progress nunca fue llamado"
    # Aserción discriminante: el worker rápido (25-30, 5 frames) se recolecta
    # en la primera pasada del poll, antes de que worker 0 termine.
    # Código secuencial daría collected_done[0] == 15 (worker 0 primero).
    assert collected_done[0] == 5, (
        "round-robin debe reportar al worker rapido (5 frames) antes que al lento"
    )
    assert collected_done[-1] == n_frames
