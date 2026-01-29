import logging
import sys, os
import platform
from pathlib import Path

os.environ.setdefault("XPCSCORR_LOG_TO_CLI", "0")
os.environ.setdefault("XPCSCORR_LOG_TO_FILE", "1")

logger = logging.getLogger("xpcscorr")
logger.propagate = False           # <--- Set propagate to False immediately after getting the logger
logger.setLevel(logging.INFO)

if logger.hasHandlers():
    logger.handlers.clear()

if os.environ["XPCSCORR_LOG_TO_FILE"].lower() in ("1", "true", "yes", "on"):
    
    platform_system = platform.system()
    if platform_system == "Windows":
        log_dir =  Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "xpcscorr"
    elif platform_system == "Linux":
        log_dir = Path.home() / ".cache" / "xpcscorr"
    elif platform_system == "Darwin":
        log_dir = Path.home() / "Library" / "Logs" / "xpcscorr"
    else:
        log_dir = Path.home() / ".xpcscorr_logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_dir / "xpcscorr.log")
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

if os.environ["XPCSCORR_LOG_TO_CLI"].lower() in ("1", "true", "yes", "on"):
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

# Easy access to main correlator functions
from .correlators.base import _create_correlator_function
from .correlators.dense.reference import CorrelatorDenseReference
from .correlators.dense.chunked import CorrelatorDenseChunked
from .correlators.sparse.chunked_numba import CorrelatorSparseChunkedNumba



correlator_dense_reference = _create_correlator_function(CorrelatorDenseReference)
correlator_dense_chunked = _create_correlator_function(CorrelatorDenseChunked)
correlator_sparse_chunked_numba = _create_correlator_function(CorrelatorSparseChunkedNumba)

# Make these two functions part of the public API so autodoc will include them
__all__ = [
    "correlator_dense_reference",
    "correlator_dense_chunked",
    "correlator_sparse_chunked_numba",
]