from typing import Optional, Tuple
import numpy as np
from xpcscorr.core.base import Results

def correlator_sparse_chunked_numba(
    intensity: "np.ndarray",
    time_index: "np.ndarray",
    pixel_pointer: "np.ndarray",
    frames_shape: Tuple[int, ...],
    roimask: "np.ndarray",
    ttcf_format: Optional[str] = ...,
    t1_t2_binning: Optional[int] = ...,
    age_binning: Optional[int] = ...,
    lag_binning: Optional[tuple] = ...,
    extra_options: Optional[dict] = ...,
) -> Results: ...