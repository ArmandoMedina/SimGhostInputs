"""Tier 3 — helper puro de las luces ABS/TC del overlay (sin matplotlib ni ffmpeg).

`_flag_recent_grid` decide si la luz prende: True si el flag (rejilla 1 m) estuvo
activo en los últimos `hold` m hasta el cursor. Es lo que da el comportamiento de
luz instantánea con retención corta en vez del viejo conteo por ventana.
"""

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
