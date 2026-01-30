from importlib.metadata import version, PackageNotFoundError

from . import helper
from . import modelbase

from .pytrate import CombinedSiteAaModel, CrossedSiteAaModel
from .foldchange import FoldChangeModel
from .helper import make_ax_a_map
from .natural_experiments import MapCoordModel
from .seqdf import SeqDf, Substitution

try:
    __version__ = version("pytrate")
except PackageNotFoundError:
    __version__ = "unknown"


__all__ = [
    "__version__",
    "CombinedSiteAaModel",
    "CrossedSiteAaModel",
    "FoldChangeModel",
    "helper",
    "make_ax_a_map",
    "MapCoordModel",
    "modelbase",
    "natural_experiments",
    "seqdf",
    "SeqDf",
    "Substitution",
]
