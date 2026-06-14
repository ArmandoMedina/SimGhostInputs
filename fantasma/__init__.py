"""SimGhostInputs: compara tus inputs contra una vuelta de referencia, por distancia."""
from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("fantasma-inputs")
except PackageNotFoundError:
    __version__ = "unknown"
