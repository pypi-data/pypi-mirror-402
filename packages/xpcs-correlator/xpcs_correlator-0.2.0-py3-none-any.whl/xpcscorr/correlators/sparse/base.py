import os
import functools
import numpy as np
import numba as nb
from numba import prange, get_num_threads



# --- Numba decorator ---
USE_NUMBA = os.environ.get("XPCSCORR_USE_NUMBA", "1") == "1" # Default to use numba unless env var is set to "0"
def optional_njit(_func=None, *, cond=USE_NUMBA, **njit_kwargs):
    """
    Optional numba njit decorator that accepts custom nb.njit kwargs.

    Usage:
      @optional_njit                # works (uses default cond)
      def f(...): ...

      @optional_njit(cond=False)    # force no-jit
      def f(...): ...

      @optional_njit(parallel=True, fastmath=True)
      def f(...): ...
    """
    def _decorator(func):
        if cond:
            return nb.njit(**njit_kwargs)(func)
        else:
            # preserve metadata
            @functools.wraps(func)
            def wrapper(*a, **k):
                return func(*a, **k)
            return wrapper

    if _func is None:
        return _decorator
    else:
        return _decorator(_func)

# --- Numba methods ---
################################
# Correlation - only g2        #
################################
@optional_njit(nogil=True)
def _calculate_correlation_g2_only(intensity, 
                          time_index, 
                          pixel_pointer,
                          g2_sum_nom_diagonal,
                          ):
    """
    Calculate only g2 function only, no ttcf matrix and no binning.
    """
    # Compute correlation by calculating each pixel's auto-correlation
    pixels_number = nb.int32(pixel_pointer.shape[0]-1)

    for i in range(pixels_number):

        start_idx = pixel_pointer[i]
        end_idx = pixel_pointer[i+1]
        _dot_product_g2_only(intensity[start_idx:end_idx], 
                     time_index[start_idx:end_idx], 
                     g2_sum_nom_diagonal,
    )

@optional_njit(nogil=True, inline='always')
def _dot_product_g2_only(intensity, 
                         time_index, 
                        g2_sum_nom_diagonal
                         ):
    """
    Correlation of sparse pixel time series in CSC format. This correspond to 
    the data of a single pixel over all frames.
    """
    total_length = nb.int32(time_index.shape[0])
    num_tmp = nb.int64(0)

    for i in range(total_length):
        for j in range(i, total_length):
            
            num_tmp = nb.int64(intensity[i]) * nb.int64(intensity[j])

            _calculate_g2_parameters(num_tmp,
                    time_index[i],
                    time_index[j],
                    g2_sum_nom_diagonal,
                    )
################################
# Correlation t1-t2 no binning #
################################
@optional_njit(nogil=True)
def _calculate_correlation(intensity, 
                          time_index, 
                          pixel_pointer,
                          numerator,
                          sum_I,
                          g2_sum_nom_diagonal,
                          ):
    """
    Calculate the correlation matrix for sparse dataset in CSC format.
    """
    # Compute correlation by calculating each pixel's auto-correlation
    pixels_number = pixel_pointer.shape[0]-1

    for i in range(pixels_number):

        start_idx = pixel_pointer[i]
        end_idx = pixel_pointer[i+1]
        _dot_product(intensity[start_idx:end_idx], 
                     time_index[start_idx:end_idx], 
                     numerator,
                     sum_I,
                     g2_sum_nom_diagonal,
    )

@optional_njit(nogil=True, inline='always')
def _dot_product(intensity, time_index, numerator, sum_I, g2_sum_nom_diagonal):                 
    """
    Correlation of sparse pixel time series in CSC format. This correspond to 
    the data of a single pixel over all frames.
    """
    total_length = nb.int32(time_index.shape[0])
    num_tmp = nb.int64(0)

    for i in range(total_length):
        sum_I[time_index[i]] += intensity[i]
        
        for j in range(i, total_length):
            
            num_tmp = nb.int64(intensity[i]) * nb.int64(intensity[j])
            numerator[time_index[i], time_index[j]] += num_tmp

            _calculate_g2_parameters(num_tmp,
                    time_index[i],
                    time_index[j],
                    g2_sum_nom_diagonal,
                    )
###############################
# Correlation t1-t2 binning  #
###############################
@optional_njit(nogil=True)
def _calculate_correlation_t1_t2_binning(intensity, 
                          time_index, 
                          pixel_pointer,
                          numerator, 
                          sum_I,
                          bins,
                          row_mean,
                          g2_sum_nom_diagonal,
                          ):
    """
    Calculate the correlation matrix for sparse dataset in CSC format.
    """
    # Compute correlation by calculating each pixel's auto-correlation
    pixels_number = pixel_pointer.shape[0]-1

    for i in range(pixels_number):

        start_idx = pixel_pointer[i]
        end_idx = pixel_pointer[i+1]

        # preload local time_index, row_mean and bins
        # insted of passing full arrays to numba function
        # to reduce cache misses
        time_index_local = time_index[start_idx:end_idx]
        row_mean_local = row_mean[time_index_local]
        bins_local = bins[time_index_local]  

        _dot_product_t1_t2_binning(intensity[start_idx:end_idx], 
                                time_index_local, 
                                numerator, 
                                sum_I,
                                bins_local,
                                row_mean_local,
                                g2_sum_nom_diagonal,
                                )

@optional_njit(nogil=True, inline='always')
def _dot_product_t1_t2_binning(intensity,
                               time_index, 
                               numerator,  
                               sum_I, 
                               bins_local,
                               row_mean_local,
                               g2_sum_nom_diagonal,
                               ):  

    """
    Correlation of sparse pixel time series in CSC format. This correspond to 
    the data of a single pixel over all frames.
    """
    total_length = nb.int32(time_index.shape[0])
    num_tmp=nb.float64(0.0)
    bin_i=nb.int32(0)
    bin_j=nb.int32(0)
    
    for i in range(total_length):

        bin_i = bins_local[i]

        sum_I[bin_i] += intensity[i]
        
        for j in range(i, total_length):
           
            bin_j= bins_local[j]
          
            num_tmp =(nb.float64(intensity[i]) * nb.float64(intensity[j])) 
            
            numerator[bin_i, bin_j] += num_tmp /(nb.float64(row_mean_local[i]) * nb.float64(row_mean_local[j]))
            
            _calculate_g2_parameters(num_tmp,
                                    time_index[i],
                                    time_index[j],
                                    g2_sum_nom_diagonal,
                                    )

###############################
# Correlation age-lag binning #
###############################
@optional_njit(nogil=True)
def _calculate_correlation_age_lag(intensity, 
                          time_index, 
                          pixel_pointer,
                          numerator,
                          age_bins,
                          lag_bins,
                          row_mean,                
                          g2_sum_num_diagonal,
                          ):
    
    """
    Calculate the correlation matrix for sparse dataset in CSC format using
    lin-log, lin binning in age-lag format.
    """
    # Compute correlation by calculating each pixel's auto-correlation
    pixels_number = nb.int32(pixel_pointer.shape[0]-1)

    for i in range(pixels_number):
        
        start_idx = pixel_pointer[i]
        end_idx = pixel_pointer[i+1]

        # preload local time_index and row_mean
        # insted of passing full arrays to numba function
        time_index_local = time_index[start_idx:end_idx]
        row_mean_local = row_mean[time_index_local]  

        _dot_product_age_lag_binning(intensity[start_idx:end_idx], 
                                time_index_local, 
                                numerator,
                                age_bins,
                                lag_bins,
                                row_mean_local,
                                g2_sum_num_diagonal,
                                )   

@optional_njit(nogil=True, inline='always')
def _dot_product_age_lag_binning(intensity,
                               time_index, 
                               numerator, 
                               age_bins, 
                               lag_bins,
                               row_mean,
                               g2_sum_num_diagonal,
                               ):
    
    total_length = nb.int32(time_index.shape[0])
    n_lag_bins = nb.int32(len(lag_bins))
    n_age_bins = nb.int32(len(age_bins))

    lag=nb.int32(0)
    age=nb.float32(0)
    bin_lag=nb.int32(0)
    bin_age=nb.int32(0)

    for i in range(total_length):
        # Reset bin indices for each new i (lag and age start from small values)
        bin_lag = nb.int32(0)
        bin_age = nb.int32(0)
        
        for j in range(i, total_length):
            
            time_i = nb.int32(time_index[i])
            time_j = nb.int32(time_index[j])
            
            lag=  time_j - time_i
            age = (time_i + time_j) / 2 
            if lag < 0:
                continue

            # Exploit monotonicity: lag and age increase as j increases
            # So bins can only increase, never decrease - just increment when needed
            while bin_lag < n_lag_bins - 1 and lag >= lag_bins[bin_lag + 1]:
                bin_lag += 1
            while bin_age < n_age_bins - 1 and age >= age_bins[bin_age + 1]:
                bin_age += 1

            num=(nb.float64(intensity[i]) * nb.float64(intensity[j]))
            denom= (nb.float64(row_mean[i]) * nb.float64(row_mean[j]))
            
            numerator[bin_age, bin_lag] += num / denom

            _calculate_g2_parameters(num,
                                    time_i,
                                    time_j,
                                    g2_sum_num_diagonal,
                                    )
####################
# G2 helper method #       
####################
@optional_njit(nogil=True, inline='always')
def _calculate_g2_parameters_full(numerator,
                           time_i,
                           time_j,
                           g2_sum_num_diagonal,
                           ):
    """
    Calculate g2 parameters  for later calculation of g2 function.
    Is sum of ttcf matrix digabonal elements, sum of squared diagonal elements, and counts.
    Parameters
    ----------
    numerator : int value
        ij numerator elemtn of global ttcf matrix.
    time_i : int value
        time index i of global ttcf matrix.
    time_j : int value
        time index j of global ttcf matrix.
    g2_sum_num_diagonal : 1D array
        Initilized array to accumulate sum of numerator per diagonal.
    """
    nth_diagonal = time_j - time_i # calculate which diagonal we are at

    g2_sum_num_diagonal[nth_diagonal] += numerator
    
@optional_njit(nogil=True, inline='always')
def _calculate_g2_parameters_noop(numerator,
                           time_i,
                           time_j,
                           g2_sum_num_diagonal,):
    """
    This is a dummy noop function for skipping g2 calculation.
    """
    return


def set_enable_g2(flag: bool):
    """
    Set whether to enable full g2 calculation or skip it.
    Parameters
    ----------
    flag : bool
        If True, enable full g2 calculation, else skip it.
    """
    global _calculate_g2_parameters
    if flag:
        _calculate_g2_parameters = _calculate_g2_parameters_full
        #print("Using full g2 calculation")
    else:
        _calculate_g2_parameters = _calculate_g2_parameters_noop
        #print("Skipping g2 calculation")


##############################
# Other helper numba methods #
##############################
@optional_njit()
def _calculate_row_sum(intensity, time_index, pixel_pointer, n_frames, roimask=None):
    """
    Numba implementation that accumulates row sums (no division) for CSC-like sparse arrays.
    Parameters:
      intensity     : 1D array of non-zero values
      time_index    : 1D array of frame indices (same length as intensity)
      pixel_pointer : 1D pointer array of length n_pixels+1
      n_frames      : number of frames (rows)
      roimask       : Optional 3D boolean array (n_rois, n_x, n_y) to mask pixels
    Returns:
      row_mean : 1D array of length n_frames with summed intensities per frame
    """
    row_sum = np.zeros(n_frames, dtype=np.float64)

    n_pixels = pixel_pointer.shape[0] - 1
    for pix in range(n_pixels):
        start = pixel_pointer[pix]
        end = pixel_pointer[pix + 1]
        # iterate over non-zero entries of this pixel
        for idx in range(start, end):
            frm = time_index[idx]
            row_sum[frm] += intensity[idx]

    return row_sum

@optional_njit()
def _calculate_row_sum_roimask(intensity, time_index, pixel_pointer, n_frames, roimask):
    """
    Numba implementation that accumulates row sums per ROI mask for CSC-like sparse arrays.
    
    Parameters:
      intensity     : 1D array of non-zero values
      time_index    : 1D array of frame indices (same length as intensity)
      pixel_pointer : 1D pointer array of length n_pixels+1
      n_frames      : number of frames (rows)
      roimask       : 3D boolean array (n_rois, x_pixels, y_pixels) to mask pixels
    
    Returns:
      row_sum : 2D array of shape (n_rois, n_frames) with summed intensities per frame per mask
    """
    
    n_rois = roimask.shape[0]
    row_sum = np.zeros((n_rois, n_frames), dtype=np.float64)
    
    n_pixels = pixel_pointer.shape[0] - 1
    
    for pix in range(n_pixels):
        start = pixel_pointer[pix]
        end = pixel_pointer[pix + 1]
        
        # Check which ROIs include this pixel
        for roi in range(n_rois):
            # Flatten the 2D mask: roimask[roi] is (x_pixels, y_pixels)
            # pix is 1D index, so we use ravel to match it
            mask_flat = roimask[roi].ravel()
            if mask_flat[pix]:  # This pixel belongs to this ROI
                # Accumulate intensities for all frames where this pixel is non-zero
                for idx in range(start, end):
                    frm = time_index[idx]
                    row_sum[roi, frm] += intensity[idx]
    
    return row_sum


@optional_njit(parallel=True)
def _calculate_denom_diag(vec):
    """
    Calculates the sum of diagonals for the outer product of a vector with itself.
    Equivalent to computing autocorrelation for all positive lags.
    Threaded version that parallelizes over available threads in a cyclic manner.
    Parameters:
        vec: 1D numpy array (self.row_mean[i])
    Returns:
        denom_diag: 1D numpy array where index l contains the sum of the l-th
    """
    #Cyclick version of _calculate_denom_diag to better utilize multithreading
    n = len(vec)
    denom_diag = np.zeros(n, dtype=vec.dtype)
    
    # We ask Numba how many threads are available
    n_threads = get_num_threads()
    
    # We parallelize over the *threads*, not the array indices directly
    for t in prange(n_threads):
        # Each thread takes every nth item (stride = n_threads)
        # e.g. Thread 0 doing 4 threads: 0, 4, 8, 12...
        # e.g. Thread 3 doing 4 threads: 3, 7, 11, 15...
        for l in range(t, n, n_threads):
            sum_val = 0.0
            for j in range(n - l):
                sum_val += vec[j] * vec[j + l]
            denom_diag[l] = sum_val
            
    return denom_diag

###########################   
# Other non-numba methods #
###########################
class FrameToTimeFormatConverter:
    """
    Convert frame compacted sparse data to pixel compacted sparse data.
    Basically it converts CSR to CSC format where each row is a flattened frame.
    It is 2 pass algorithm. First pass is to calculate the number of non-zero elements
    in each time frame, second pass is to fill the data in the correct position.
    """

    def __init__(self, intensity, pixel_index, frame_pointer, frames_shape, frame_sums=False):
        
        self.intensity = intensity
        self.pixel_index = pixel_index
        self.frame_pointer = frame_pointer
        self.frames_shape = frames_shape

        if frame_sums:
            self.frame_sums = np.zeros((frames_shape[0],), dtype=np.int64)

        time_index_counts = self._calculate_pixel_index(frames_shape[0], pixel_index)
        
        self.intensity_pc, self.time_index_pc, self.pixel_pointer_pc = \
            self._initialize_pixel_compacted(time_index_counts)
        

        self.convert(intensity, pixel_index, frame_pointer,
                     self.intensity_pc, self.time_index_pc, self.pixel_pointer_pc)
        
    
    def get_converted(self):
        return self.intensity_pc, self.time_index_pc, self.pixel_pointer_pc

    
    @staticmethod
    def _calculate_pixel_index(frames_n, pixel_index):
        """
        First pass to calculate the number of non-zero elements in each time frame.
        Uses bincount for making hisotgram of frame indices.
        """

        bins = np.arange(frames_n+1, dtype=np.int32)
        time_index_counts = np.bincount(pixel_index, minlength=frames_n)

        return time_index_counts
    
    @staticmethod
    def _initialize_pixel_compacted(time_index_counts):
        """
        Initialize intensity, time_index and pixel_pointer arrays for pixel 
        compacted sparse data.

        Parameters
        ----------
        time_index_counts : np.ndarray
            Number of non-zero elements in each  frame.

        """

        elements_nnz = np.sum(time_index_counts)

        pixel_pointer = np.zeros((time_index_counts.shape[0]+1,), dtype=np.int32)
        for i in range(time_index_counts.shape[0]):
            pixel_pointer[i+1] = pixel_pointer[i] + time_index_counts[i]

        intensity = np.zeros((elements_nnz,), dtype=np.int32)
        time_index = np.zeros((elements_nnz,), dtype=np.int32)

        return intensity, time_index, pixel_pointer
    
    @staticmethod
    def convert(intensity, pixel_index, frame_pointer,
                intensity_pc, time_index, pixel_pointer):
        
        """
        Second pass to fill the pixel compacted sparse data arrays.

        Parameters
        ----------
        intensity : np.ndarray
            Intensity values in frame compacted format.
        pixel_index : np.ndarray
            Pixel indices in frame compacted format.
        frame_pointer : np.ndarray
            Frame pointer array in frame compacted format.
        intensity_pc : np.ndarray
            Empty intensity array in pixel compacted format to be filled.
        time_index : np.ndarray
            Empty time index array in pixel compacted format to be filled.
        pixel_pointer : np.ndarray
            Pixel pointer array in pixel compacted format.
        """

        # number of pixels
        pixels_number = pixel_pointer.shape[0] - 1

        # working write positions per pixel (start positions)
        write_pos = pixel_pointer.copy()

        # number of frames
        frames_n = frame_pointer.shape[0] - 1

        for frame in range(frames_n):
            start = frame_pointer[frame]
            end = frame_pointer[frame + 1]
            for idx in range(start, end):
                pix = pixel_index[idx]
                pos = write_pos[pix]
                intensity_pc[pos] = intensity[idx]
                time_index[pos] = frame
                write_pos[pix] = pos + 1





