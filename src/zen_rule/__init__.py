
import importlib.metadata
from .engine import ZenRule
from .register import udf, udf_manager

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0"


__all__ = [
    __version__,
    ZenRule,
    udf,
    udf_manager
]