"""Worker subprocess para render paralelo de frames del overlay.

Se invoca como: python -m fantasma.viz._overlay_worker <pkl_path>
Tener __main__ propio evita que spawn reimporte el servidor de Streamlit.
"""
import pickle
import sys

if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")

    with open(sys.argv[1], "rb") as _f:
        _args = pickle.load(_f)

    from fantasma.viz.overlay import _render_chunk
    _render_chunk(_args)
