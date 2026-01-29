import numpy as np

def mask_to_3d_bool_stack(mask: np.ndarray) -> np.ndarray:
    """
    Converts various mask formats to a 3D boolean stack.
    
    Parameters
    ----------
    mask : np.ndarray
        Input mask in one of the supported formats:
        - 2D mask with 0/1 or False/True
        - 2D mask with integer labels (each label is a mask index)
        - 3D mask with 0/1 or False/True
        - 3D mask with integer values (nonzero = True)
    
    Returns
    -------
    np.ndarray
        3D boolean array of shape (n_masks, height, width)
    """
    mask = np.asarray(mask)
    if mask.ndim == 2:
        if mask.dtype == bool or np.array_equal(np.unique(mask), [0, 1]) or np.array_equal(np.unique(mask), [0]):
            # 2D binary mask: single mask
            return mask[None, ...].astype(bool)
        else:
            # 2D integer mask: each unique nonzero value is a mask index
            labels = np.unique(mask)
            labels = labels[labels != 0]  # Exclude zero label
            if len(labels) == 0:
                # Only zeros: return a single all-False mask
                return np.zeros((1,) + mask.shape, dtype=bool)
            stack = np.zeros((len(labels),) + mask.shape, dtype=bool)
            for i, label in enumerate(labels):
                stack[i] = (mask == label)
            return stack
    elif mask.ndim == 3:
        # 3D mask: treat each slice as a mask
        return mask.astype(bool)
    else:
        raise ValueError("Mask must be 2D or 3D numpy array")

def lin_log_bin(x, N, n_log_bins) -> tuple[np.ndarray, np.ndarray]:
    """
    Create hybrid linear-logarithmic binning for the linear x input data \
    with a linear part from 0 to N and a logarithmic part from N to the maximum.
    The logarithmic part is divided into n_log_bins bins.
    The linear part is divided into 10**N bins.

    Parameters
    ----------
    x : np.ndarray
        Input of x coordinates.
    N : int
        The log10 decade from which logarithmic binning should start.
    n_log_bins : int
        Number of logarithmic equally distributed bins.

    Returns
    -------
    bin_edges : np.ndarray
        The edges of the bins.
    binned_indices : np.ndarray
        The indices of the bins for each element in x.
    """

    N_max = np.log10(np.max(x))
    if N_max < N:
        N_max = N

    bin_edges = np.concatenate((
        #Here -0.5 was requested by Yuri.
        np.arange(0,10**N)-0.5,  # the linear part, bins are centered around integers
        np.logspace(N, N_max, num=n_log_bins) # the logarithmic part
    ))

    bin_edges[-1] = np.max(x) # ensure the last bin edge is exactly the max of x

    #binned_indices = np.digitize(x, bin_edges, right=True) 
    #binned_indices = binned_indices[(binned_indices > 0) &
    #                                (binned_indices < len(bin_edges))]
    
    binned_indices = np.searchsorted(bin_edges, x, side='right') - 1
    binned_indices = np.clip(binned_indices, 0, len(bin_edges) - 2)

    return bin_edges, binned_indices

def calculate_lin_log_bin_counts(N, age_edges, lag_edges):
    """
    Calculates the number of matrix elements in bins defined by:
      Age = (t1 + t2) / 2
      Lag = t2 - t1
    
    Matches numpy.histogram2d behavior:
    - Bins are [a, b) (half-open)
    - The LAST bin in each dimension is [a, b] (inclusive)

    Parameters
    ----------
    N : int
        The number of frames (matrix size is NxN).
    age_edges : np.ndarray
        The edges of the Age bins.
    lag_edges : np.ndarray
        The edges of the Lag bins.
    Returns
    -------
    counts : np.ndarray
        2D array of counts for each (lag, age) bin.
    """
    age_edges = np.asarray(age_edges)
    lag_edges = np.asarray(lag_edges)
    
    n_age_bins = len(age_edges) - 1
    n_lag_bins = len(lag_edges) - 1
    
    counts = np.zeros((n_lag_bins, n_age_bins), dtype=np.int64)
    
    # Transform Age edges to Sum space (S = t1 + t2 = 2 * Age)
    s_edges = age_edges * 2
    
    max_s_val = 2 * N - 2
    
    for i in range(n_age_bins):
        s_min_float = s_edges[i]
        s_max_float = s_edges[i+1]
        
        # --- FIX 1: Handle Age (Sum) Last Bin Inclusive ---
        is_last_age_bin = (i == n_age_bins - 1)
        
        # Start is always ceil (inclusive left)
        s_start = int(np.ceil(s_min_float))
        
        if is_last_age_bin:
            # Last bin includes the right edge: floor(max)
            s_end = int(np.floor(s_max_float))
        else:
            # Standard bin excludes right edge: ceil(max) - 1
            s_end = int(np.ceil(s_max_float)) - 1
        
        if s_start > s_end:
            continue
            
        # Vector of all valid S integers in this Age bin
        s_vec = np.arange(s_start, s_end + 1, dtype=np.int64)
        
        # Geometric limits of Diff (D) imposed by NxN matrix
        limit_lower = np.maximum(-s_vec, s_vec - 2 * (N - 1))
        limit_upper = np.minimum(s_vec, 2 * (N - 1) - s_vec)
        
        s_parity = s_vec % 2

        for j in range(n_lag_bins):
            d_min_bin = lag_edges[j]
            d_max_bin = lag_edges[j+1]
            
            # --- FIX 2: Handle Lag (Diff) Last Bin Inclusive ---
            is_last_lag_bin = (j == n_lag_bins - 1)
            
            # D start
            d_start_int = int(np.ceil(d_min_bin))
            
            # D end
            if is_last_lag_bin:
                d_end_int = int(np.floor(d_max_bin))
            else:
                d_end_int = int(np.ceil(d_max_bin)) - 1
            
            # Intersect matrix geometric limits with Bin limits
            actual_start = np.maximum(limit_lower, d_start_int)
            actual_end = np.minimum(limit_upper, d_end_int)
            
            valid_mask = actual_end >= actual_start
            
            if not np.any(valid_mask):
                continue
                
            a_start = actual_start[valid_mask]
            a_end = actual_end[valid_mask]
            p = s_parity[valid_mask]
            
            # Count integers in [a_start, a_end] with parity p
            # Formula: floor((B - P) / 2) - floor((A - P - 1) / 2)
            count_upper = np.floor((a_end - p) / 2.0).astype(np.int64)
            count_lower = np.floor((a_start - 1 - p) / 2.0).astype(np.int64)
            
            bin_count = np.sum(count_upper - count_lower)
            
            counts[j, i] = bin_count

    return counts

import numpy as np

def calculate_lin_lin_bin_counts(N, bins_edges):
    """
    Calculates the number of matrix elements in bins defined by:
    t1 and t2 linear bins.
    Restricted to the LOWER TRIANGLE (including diagonal), i.e., t2 <= t1.

    Matches numpy.histogram2d behavior:
    - Bins are [a, b) (half-open)
    - The LAST bin in each dimension is [a, b] (inclusive)

    Parameters
    ----------
    N : int
        The number of frames (matrix size is NxN).
    bins_edges : np.ndarray
        The edges of the t1 and t2 bins.

    Returns
    -------
    counts : np.ndarray
        2D array of counts for each (t1, t2) bin.
    """

    bins_edges = np.asarray(bins_edges)
    
    n_bins = len(bins_edges) - 1
    
    counts = np.zeros((n_bins, n_bins), dtype=np.int64)
    
    for i in range(n_bins): # t1 loop (columns in the counts histogram usually correspond to x-axis)
        t1_min_float = bins_edges[i]
        t1_max_float = bins_edges[i+1]
        
        # --- Handle t1 Last Bin Inclusive ---
        is_last_t1_bin = (i == n_bins - 1)
        
        # Range for integer t1: [t1_start, t1_end]
        t1_start = int(np.ceil(t1_min_float))
        if is_last_t1_bin:
            t1_end = int(np.floor(t1_max_float))
        else:
            t1_end = int(np.ceil(t1_max_float)) - 1
        
        if t1_start > t1_end:
            continue
            
        for j in range(n_bins): # t2 loop (rows in the counts histogram usually correspond to y-axis)
            t2_min_float = bins_edges[j]
            t2_max_float = bins_edges[j+1]
            
            # --- Handle t2 Last Bin Inclusive ---
            is_last_t2_bin = (j == n_bins - 1)
            
            # Range for integer t2: [t2_start, t2_end]
            t2_start = int(np.ceil(t2_min_float))
            if is_last_t2_bin:
                t2_end = int(np.floor(t2_max_float))
            else:
                t2_end = int(np.ceil(t2_max_float)) - 1
            
            if t2_start > t2_end:
                continue

            # We need to count pairs (t1, t2) in the rectangle defined by
            # t1 in [t1_start, t1_end] AND t2 in [t2_start, t2_end]
            # SUCH THAT t2 <= t1.
            
            # If the entire rectangle is in the upper triangle (t2_start > t1_end), count is 0.
            if t2_start > t1_end:
                counts[j, i] = 0
                continue

            # If the entire rectangle is in the lower triangle (t2_end <= t1_start),
            # then the condition t2 <= t1 is always met for valid t1, t2.
            # Note: t2 <= t1_start implies t2 <= any t1 inside [t1_start, t1_end].
            if t2_end <= t1_start:
                count_t1 = (t1_end - t1_start + 1)
                count_t2 = (t2_end - t2_start + 1)
                counts[j, i] = count_t1 * count_t2
                continue
            
            # Intersection Case: The diagonal passes through this bin.
            # We iterate the shorter range to sum up valid points.
            # It's usually efficient to iterate over t2 rows.
            # For a specific row t2, valid t1s are max(t1_start, t2) to t1_end.
            
            bin_count = 0
            # Iterate through every integer t2 in the bin range
            for t2_val in range(t2_start, t2_end + 1):
                # The condition is t1 >= t2.
                # Also t1 must be >= t1_start.
                # So effective start for t1 is max(t1_start, t2_val).
                current_t1_start = max(t1_start, t2_val)
                
                if current_t1_start <= t1_end:
                    bin_count += (t1_end - current_t1_start + 1)
            
            counts[j, i] = bin_count

    return counts


def bin_centers_mixed(bins_lag, N):
    """
    Compute bin centers for hybrid linear-logarithmic bins.
    The linear part is from 0 to 10**N and the logarithmic part is
    from 10**N to the maximum.
    
    Parameters
    ----------
    bins_lag : np.ndarray
        The edges of the bins.
    N : int
        The log10 decade from which logarithmic binning starts.
    
    Returns
    -------
    centers : np.ndarray
        The centers of the bins.
    """

    split_idx = np.searchsorted(bins_lag, 10**N)
    centers = np.empty(len(bins_lag) - 1)
    # Linear part
    centers[:split_idx] = 0.5 * (bins_lag[1:split_idx+1] + bins_lag[:split_idx])
    # Log part
    centers[split_idx:] = np.sqrt(bins_lag[split_idx+1:] * bins_lag[split_idx:-1])
    return centers


def lin_bin(x, N, halfs=False) -> tuple[np.ndarray, np.ndarray]:
    """
    Create linear binning for the linear x input data.
    The linear part is divided into N bins.

    Parameters
    ----------
    x : np.ndarray
        Input of x coordinates.
    N : int
        The number of bins.
    halfs : bool
        If True, bin indices are created for x values at every 0.5 step.

    Returns
    -------
    bin_edges : np.ndarray
        The edges of the bins.
    binned_indices : np.ndarray
        The indices of the bins for each element in x.
    """
    
    bin_edges = np.linspace(0, np.max(x), N+1)
   
    if halfs:
        x2=np.arange(0,np.max(x)+0.5,0.5)
        binned_indices = np.searchsorted(bin_edges, x2, side='right') - 1
        binned_indices = np.clip(binned_indices, 0, N-1)
        
    else:
        binned_indices = np.searchsorted(bin_edges, x, side='right') - 1
        binned_indices = np.clip(binned_indices, 0, N-1)

    return bin_edges, binned_indices

def bin_centers(bins):
    """
    Compute bin centers from bin edges.
    
    Parameters
    ----------
    bins : np.ndarray
        The edges of the bins.
    
    Returns
    -------
    centers : np.ndarray
        The centers of the bins.
    """
    return 0.5 * (bins[1:] + bins[:-1])


def bins_calc_tccf_t1_t2_chunk(t1_t2_binning, global_ttcf_size, rows_start, rows_end, cols_start, cols_end):
        """
        Bin the chunk ttcf matrix according to the provided t1_t2_binning.
        
        Parameters
        ----------
        ttcf : np.ndarray
            The chunk ttcf matrix to be binned.
        global_ttcf_size : int
            The axis size of the full ttcf matrix - equal to the number of frames.
        t1_t2_binning : int
            The number of linear bins for each axis (t1 and t2).
        
        Returns
        -------
        local_bin_t1 : np.ndarray
            The bin edges for t1 in the chunk.
        local_bin_t2 : np.ndarray
            The bin edges for t2 in the chunk.
        bin_t1_start : int
            The starting index of the t1 bins in the global bin array.
        bin_t1_end : int
            The ending index of the t1 bins in the global bin array.
        bin_t2_start : int
            The starting index of the t2 bins in the global bin array.
        bin_t2_end : int
            The ending index of the t2 bins in the global bin array.
        """

        global_bin_t1, _ = lin_bin(np.arange(global_ttcf_size), t1_t2_binning)
        global_bin_t2 = global_bin_t1


        # Row bins
        bin_t2_start = np.searchsorted(global_bin_t2, rows_start, side='right') - 1
        bin_t2_end   = np.searchsorted(global_bin_t2, rows_end-1, side='right')
        # Column bins
        bin_t1_start = np.searchsorted(global_bin_t1, cols_start, side='right') - 1
        bin_t1_end   = np.searchsorted(global_bin_t1, cols_end-1, side='right')

        # Clamp indices
        bin_t1_start = max(bin_t1_start, 0)
        bin_t1_end = min(bin_t1_end, len(global_bin_t1)-1)
        bin_t2_start = max(bin_t2_start, 0)
        bin_t2_end = min(bin_t2_end, len(global_bin_t2)-1)

        # Local bins for the chunk
        local_bin_t1 = global_bin_t1[bin_t1_start:bin_t1_end+1]
        local_bin_t2 = global_bin_t2[bin_t2_start:bin_t2_end+1]
        
        return local_bin_t1, local_bin_t2, bin_t1_start, bin_t1_end, bin_t2_start, bin_t2_end


def bins_calc_tccf_age_lag_chunk(age_binning, lag_binning, global_ttcf_size, rows_start, rows_end, cols_start, cols_end):
    """
    Calculate bin edges for age and lag values for a chunk.
    The age is (t1 + t2)/2 and lag is (t2 - t1).
    
    For lag values, we need to consider the actual range of lag values in the chunk,
    including negative lags for the lower triangle.

    Parameters
    ----------
    age_binning : int
        Number of linear bins for age.
    lag_binning : tuple(int, int)
        Tuple specifying (linear part end decade, number of log bins) for lag.
    global_ttcf_size : int
        The axis size of the full ttcf matrix - equal to the number of frames.
    rows_start : int
        Starting index of the chunk rows (t2).
    rows_end : int
        Ending index of the chunk rows (t2).
    cols_start : int
        Starting index of the chunk columns (t1).
    cols_end : int
        Ending index of the chunk columns (t1).

    Returns
    -------
    local_bin_lag : np.ndarray
        The bin edges for lag in the chunk.
    local_bin_age : np.ndarray
        The bin edges for age in the chunk.
    bin_lag_start : int
        The starting index of the lag bins in the global bin array.
    bin_lag_end : int
        The ending index of the lag bins in the global bin array.
    bin_age_start : int
        The starting index of the age bins in the global bin array.
    bin_age_end : int
        The ending index of the age bins in the global bin array.
    """
    # For age binning, we can continue with linear binning
    global_age_bins, _ = lin_bin(np.arange(global_ttcf_size), age_binning)
    
    # For lag binning, we need to consider the actual range of lag values
    # Maximum lag value would be the difference between max and min frame indices
    max_lag_value = global_ttcf_size - 1
    
    # Create lag bins using lin_log_bin (linear from 0 to 10**lag_binning[0], 
    # then log-spaced with lag_binning[1] bins)
    global_lag_bins, _ = lin_log_bin(np.arange(max_lag_value + 1), lag_binning[0], lag_binning[1])
    
    # Check if this chunk spans the diagonal
    is_diagonal_chunk = rows_start <= cols_end and cols_start <= rows_end
    
    if is_diagonal_chunk:
        # This chunk includes both positive and negative lags
        min_lag = 0  # Include the diagonal (zero lag)
        max_lag = max(rows_end - cols_start - 1, cols_end - rows_start - 1)
    else:
        # Handle purely upper or lower triangle
        if rows_start > cols_end:
            # Upper triangle (positive lags)
            min_lag = rows_start - cols_end
            max_lag = rows_end - cols_start - 1
        else:
            # Lower triangle (negative lags)
            min_lag = 0  # We'll convert to positive later
            max_lag = cols_end - rows_start
    
    # Find bin indices that cover this range
    bin_lag_start = np.searchsorted(global_lag_bins, min_lag, side='right') - 1
    bin_lag_end = np.searchsorted(global_lag_bins, max_lag, side='right')
    
    # For age bins, use the original approach
    bin_age_start = np.searchsorted(global_age_bins, (cols_start + rows_start)/2, side='right') - 1
    bin_age_end = np.searchsorted(global_age_bins, (cols_end + rows_end)/2, side='right')
    
    # Clamp indices
    bin_age_start = max(bin_age_start, 0)
    bin_age_end = min(bin_age_end, len(global_age_bins)-1)
    bin_lag_start = max(bin_lag_start, 0)
    bin_lag_end = min(bin_lag_end, len(global_lag_bins)-1)
    
    # Local bins for the chunk
    local_bin_lag = global_lag_bins[bin_lag_start:bin_lag_end+1]
    local_bin_age = global_age_bins[bin_age_start:bin_age_end+1]
    
    # Ensure we always have at least 2 bin edges
    if len(local_bin_lag) < 2:
        local_bin_lag = np.array([0, max_lag + 1])
        bin_lag_start = 0
        bin_lag_end = 1
        
    if len(local_bin_age) < 2:
        local_bin_age = np.array([cols_start, rows_end])
        bin_age_start = 0
        bin_age_end = 1
    
    return local_bin_lag, local_bin_age, bin_lag_start, bin_lag_end, bin_age_start, bin_age_end
   
@staticmethod
def calculate_g2_from_ttcf_t1t2(ttcf : np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculates g2 and g2 error from the ttcf matrix in t1-t2 format.
    
    Parameters
    ----------
    ttcf : np.ndarray
        The ttcf matrix in t1-t2 format.
    Returns
    -------
    g2 : np.ndarray
        The calculated g2 values.
    g2_err : np.ndarray
        The calculated g2 error values.
    """
    g2_len=ttcf.shape[0]

    g2=np.zeros(g2_len)
    g2_err=np.zeros(g2_len)

    for i in range(g2_len):
        diag_values = np.diagonal(ttcf, offset=i)
        g2[i] = np.mean(diag_values)
        g2_err[i] = np.std(diag_values) / np.sqrt(len(diag_values))

    return g2, g2_err

@staticmethod
def calculate_g2_from_ttcf_lag_age(ttcf : np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculates g2 and g2 error from the ttcf matrix in lag-age format.
    
    Parameters
    ----------
    ttcf : np.ndarray
        The ttcf matrix in lag-age format.
    Returns
    -------
    g2 : np.ndarray
        The calculated g2 values.
    g2_err : np.ndarray
        The calculated g2 error values.
    """
    g2_len=ttcf.shape[1]
    g2=np.zeros(g2_len)
    g2_err=np.zeros(g2_len)

    for i in range(g2_len):
        lag_column = ttcf[:, i]
        g2[i] = np.nanmean(lag_column)
        g2_err[i] = np.nanstd(lag_column) / np.sqrt(np.sum(~np.isnan(lag_column)))
    return g2, g2_err

def simulate_decorrelating_frames(n_frames, X, Y, noise_level=1.0):
    """
    Simulate a stack of frames that decorrelate over time.
    Each frame is generated by adding random noise to the previous frame.

    Parameters
    ----------
    n_frames : int
        Number of frames to simulate.
    X : int
        Width of each frame.
    Y : int
        Height of each frame.
    noise_level : float
        The level of noise to add to each frame.

    Returns
    -------
    frames : np.ndarray
        The simulated stack of frames.
    """
    # Start with a random initial frame
    frames = np.zeros((n_frames, X, Y), dtype=np.float32)
    frames[0] = np.random.poisson(40, (X, Y))
    for i in range(1, n_frames):
        # Each frame is the previous frame plus random noise (decorrelation)
        frames[i] = frames[i-1] + np.random.normal(0, noise_level * i, (X, Y))
    return frames


class SharedMemoryArray():
    @staticmethod
    def initialize(shape, dtype):
        """
        Create an empty shared memory numpy array.

        Returns a tuple (array_view, shm_handle). Caller must keep shm_handle alive
        and call shm_handle.close() and shm_handle.unlink() when done.
        """
        import multiprocessing.shared_memory as shm

        # Calculate the size in bytes
        n_bytes = np.prod(shape) * np.dtype(dtype).itemsize

        # Create shared memory block (keep handle alive)
        shared_mem = shm.SharedMemory(create=True, size=n_bytes)

        # Create a numpy array backed by shared memory
        array = np.ndarray(shape, dtype=dtype, buffer=shared_mem.buf)

        # Return both the view and the SharedMemory handle
        return array, shared_mem

    @staticmethod
    def get_metadata(array, shm_handle):
        """
        Get metadata for a shared memory numpy array.
        Requires the SharedMemory handle returned by initialize to be passed in.
        """
        if shm_handle is None:
            raise ValueError("get_metadata requires the SharedMemory handle returned by initialize()")

        metadata = {
            'name': shm_handle.name,
            'shape': array.shape,
            'dtype': array.dtype.str
        }

        return metadata

    @staticmethod
    def create_view_from_metadata(metadata):
        """
        Reconstruct a shared memory numpy array from metadata.
        Returns (array_view, shm_handle). Caller must call shm_handle.close() when done.
        """
        import multiprocessing.shared_memory as shm
        import numpy as np

        # Access the shared memory block by name
        shared_mem = shm.SharedMemory(name=metadata['name'])

        # Create a numpy array backed by shared memory
        array = np.ndarray(metadata['shape'], dtype=np.dtype(metadata['dtype']), buffer=shared_mem.buf)

        return array, shared_mem

   