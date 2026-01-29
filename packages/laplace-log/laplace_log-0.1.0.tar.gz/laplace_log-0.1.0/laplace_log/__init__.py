'''
laplace_log – unified logging utilities for Laplace applications.
'''
# libraries
from importlib.metadata import version, PackageNotFoundError

# project
from .log_lhc import LoggerLHC, log

try:
    __version__ = version("laplace-log")
except PackageNotFoundError:
    __version__ = "0.0.0"


__all__ = ["LoggerLHC", "log", "__version__"]
