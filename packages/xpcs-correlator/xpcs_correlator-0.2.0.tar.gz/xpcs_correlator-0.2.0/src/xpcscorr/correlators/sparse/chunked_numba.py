import sys
import gc
from time import time

import numpy as np

from dask.distributed import LocalCluster, Client
from distributed import as_completed

import h5py

from xpcscorr.correlators.base import SparseCorrelator
from xpcscorr.core.base import Results

from xpcscorr.core.utils import (mask_to_3d_bool_stack, 
                                lin_bin, lin_log_bin,
                                bin_centers, bin_centers_mixed, 
                                SharedMemoryArray, 
                                calculate_lin_log_bin_counts,
                                calculate_lin_lin_bin_counts,
                                calculate_g2_from_ttcf_lag_age,
                                calculate_g2_from_ttcf_t1t2)

from xpcscorr.correlators.sparse.base import  (_calculate_correlation_g2_only,
                                               _calculate_correlation, 
                                               _calculate_correlation_t1_t2_binning,
                                               _calculate_correlation_age_lag,
                                               _calculate_row_sum_roimask,
                                               _calculate_denom_diag,
                                               set_enable_g2
                                               )
from xpcscorr import logger

python_executable = sys.executable

class ChunkWorker:
    """
    Worker class to calculate correlation matrix from CSC-like sparse data in chunked mode.
    """
    def __init__(self,
               roimask: np.ndarray,
               frames_shape: tuple,
               ttcf_format = None,
               t1_t2_binning = None,
               age_binning = None,
               lag_binning = None,
               row_mean = None,
               dask_cluster_type = None,
               calculate_full_g2 = True,
               ):
        
        self.roimask = roimask
        self.frames_shape = frames_shape
        self.ttcf_format = ttcf_format
        self.t1_t2_binning = t1_t2_binning
        self.age_binning = age_binning
        self.lag_binning = lag_binning
        self.row_mean = row_mean
        self.dask_cluster_type = dask_cluster_type
        self.calculate_full_g2 = calculate_full_g2
        
        # Operations during initialization

        # reshape roimask from 3D to 2D (mask_num, pixels)
        self.roimask = self.roimask.reshape(roimask.shape[0], -1).copy()
    
    def __call__(self, data_type, data, pixel_indices,chunk_ID, mask_id):
        """
        Calculate the correlation matrix of the data
        """
        start_time = time()
        # --- Process the chunk ---
        logger.info(f"Processing by worker chunk ID {chunk_ID}...")
        
        self.chunk_ID = chunk_ID
        self.mask_id = mask_id
        self.data_shm= {}
        self.data_chunk= {}
        
        # --- set g2 calculation mode  ---
        # This need to be obligatorily called here to set the correct g2 calculation mode
        set_enable_g2(self.calculate_full_g2)

        # _load chunk data
        logger.info(f"Loading data for chunk ID {self.chunk_ID}...")
        self._load_chunk_data(data_type, data, pixel_indices)

        # _calculate_chunk
        logger.info(f"Calculating correlation for chunk ID {self.chunk_ID}...")
        res_chunk, numerator, sum_intensity= self._calculate_chunk()

        #close shared memory handles - problematic in dask workers
        #if data_type == 'shared_memory' and self.dask_cluster_type is not None:
        #    logger.info(f"Closing shared memory for chunk ID {self.chunk_ID}...")
            # self.shm_close()
            
        logger.info(f"Returning data {self.chunk_ID}..., total worker time {time()-start_time:.2f}s")
        return res_chunk, numerator, sum_intensity

    def _load_chunk_data(self, data_type, data, pixel_indices):

        #Shared memory data loading for local cluster worker
        if data_type == 'shared_memory':

            for key in ('intensity', 'time_index', 'pixel_pointer'):
                self.data_shm[key] = {}
                self.data_shm[key]['shm_view'], self.data_shm[key]['shm_handle'] = SharedMemoryArray.create_view_from_metadata(data[key])

            self.data_chunk['intensity'], self.data_chunk['time_index'], self.data_chunk['pixel_pointer'] = \
                self._get_data_chunk(
                    self.data_shm['intensity']['shm_view'],
                    self.data_shm['time_index']['shm_view'],
                    self.data_shm['pixel_pointer']['shm_view'],
                    pixel_indices,
                )

        elif data_type == 'hdf5':
            # open hdf5 datasets
            with h5py.File(data['intensity'][0], "r") as f:
                intensity_ds = f[data['intensity'][1]]
                time_index_ds = f[data['time_index'][1]]
                pixel_pointer_ds = f[data['pixel_pointer'][1]]

                self.data_chunk['intensity'], self.data_chunk['time_index'], self.data_chunk['pixel_pointer'] = \
                    self._get_data_chunk(
                        intensity_ds,
                        time_index_ds,
                        pixel_pointer_ds,
                        pixel_indices,
                    )

            logger.info(f"Data loaded from memory for chunk ID {self.chunk_ID}.")
        else:
            raise ValueError("Data must be a tuple of 3 elements of np.ndarray "
                               "for one chunk.")

    def _calculate_chunk(self):

        # Calculate only g2 function
        if self.ttcf_format is None:
            g2_sum_nom_diagonal = np.zeros(self.frames_shape[0])

            _calculate_correlation_g2_only(
                self.data_chunk['intensity'],
                self.data_chunk['time_index'],
                self.data_chunk['pixel_pointer'],
                g2_sum_nom_diagonal,
                )
            
            res_chunk= [g2_sum_nom_diagonal,]

            return res_chunk, None, None

        # Calculate t1,t2 correlation without binning    
        if self.ttcf_format=='t1,t2' and self.t1_t2_binning is None:
            numerator = np.zeros((self.frames_shape[0] , self.frames_shape[0]), dtype=np.int64)
            sum_intensity = np.zeros((self.frames_shape[0]), dtype=np.int64)
            g2_sum_nom_diagonal = np.zeros(self.frames_shape[0])
            
            res_chunk = None
            
            #TODO verify datatypes for all calculations
            _calculate_correlation(
                self.data_chunk['intensity'],
                self.data_chunk['time_index'],
                self.data_chunk['pixel_pointer'],
                numerator,
                sum_intensity,
                g2_sum_nom_diagonal,
                )
            
            res_chunk= [g2_sum_nom_diagonal,]
            return res_chunk, numerator, sum_intensity
        
        #Calculate t1,t2 correlation with binning
        if self.ttcf_format == 't1,t2' and self.t1_t2_binning is not None:
            numerator = np.zeros((self.t1_t2_binning , self.t1_t2_binning), dtype=np.float64)
            sum_intensity = np.zeros((self.t1_t2_binning), dtype=np.int64)
            _ , bins = lin_bin(np.arange(self.frames_shape[0]), self.t1_t2_binning)
            g2_sum_nom_diagonal = np.zeros(self.frames_shape[0])
            
            res_chunk = None
            #TODO verify datatypes for all calculations
            _calculate_correlation_t1_t2_binning(
                self.data_chunk['intensity'],
                self.data_chunk['time_index'],
                self.data_chunk['pixel_pointer'],
                numerator,
                sum_intensity,
                bins,
                self.row_mean[self.mask_id],
                g2_sum_nom_diagonal,
                )
            res_chunk= [g2_sum_nom_diagonal,]
            return res_chunk, numerator, sum_intensity
        
        # Calculate age,lag correlation with binning
        if self.ttcf_format == 'age,lag' and self.age_binning is not None and self.lag_binning is not None:

            logger.info(f"Calculating age,lag correlation for chunk ID {self.chunk_ID}...")
            
            numerator = np.zeros((self.age_binning , 
                                  10**self.lag_binning[0]-1+self.lag_binning[1]), 
                                  dtype=np.float64)
            
            lag_bins, _ = lin_log_bin(np.arange(self.frames_shape[0]),
                                        self.lag_binning[0], 
                                        self.lag_binning[1])
            age_bins, _ = lin_bin(np.arange(self.frames_shape[0]), 
                                        self.age_binning,
                                        halfs=True)
            
            lag_bins[-1] += 1  # to include the last bin for searchsorted in numba methods
            age_bins[-1] += 1  # to include the last bin for searchsorted in numba methods
    
            res_chunk = None

            g2_sum_nom_diagonal=np.zeros(self.frames_shape[0])

            logger.info(f"Calling Numba age,lag calculation for chunk ID {self.chunk_ID}...")

            _calculate_correlation_age_lag(
                self.data_chunk['intensity'],
                self.data_chunk['time_index'],
                self.data_chunk['pixel_pointer'],
                numerator, #in reality this is not nrmalized ttcf
                age_bins,
                lag_bins,
                self.row_mean[self.mask_id],
                g2_sum_nom_diagonal,
                )
            

            res_chunk= [g2_sum_nom_diagonal,]
            logger.info(f"Finished age,lag calculation for chunk ID {self.chunk_ID}.")
            return res_chunk, numerator, None

    def _get_data_chunk(self, intensity, time_index, pixel_pointer, pixel_indices):
        """
        Extract data chunk for given pixel indices from the global sparse data.
        Memory-efficient version using numpy arrays for ranges.
        """
        logger.info(f"Extracting data for {len(pixel_indices)} masked pixels.")
        
        # Pre-compute all starts and ends
        starts = pixel_pointer[pixel_indices]
        ends = pixel_pointer[pixel_indices + 1]
        lengths = (ends - starts)
        total = int(lengths.sum())
        
        # Vectorized detection of contiguous ranges
        is_break = np.concatenate([[True], starts[1:] != ends[:-1], [True]])
        break_indices = np.where(is_break)[0]
        
        # Store ranges as numpy arrays (much more memory efficient)
        range_starts = starts[break_indices[:-1]]
        range_ends = ends[break_indices[1:] - 1]
        n_ranges = len(range_starts)
        
        logger.info(f"Reduced to {n_ranges} contiguous range(s) from {len(pixel_indices)} pixels. "
                    f"Compression ratio: {len(pixel_indices)/n_ranges:.1f}x")
        
        # Allocate output arrays
        intensity_masked = np.empty(total, dtype=intensity.dtype)
        time_index_masked = np.empty(total, dtype=time_index.dtype)
        
        # Read data in contiguous chunks
        out_pos = 0
        for i in range(n_ranges):
            start_idx = int(range_starts[i]) #int here for promotion rules - diffrence betwee nnumpy 1.23 and 2.0
            end_idx = int(range_ends[i])
            chunk_size = end_idx - start_idx
            intensity_masked[out_pos:out_pos + chunk_size] = intensity[start_idx:end_idx]
            time_index_masked[out_pos:out_pos + chunk_size] = time_index[start_idx:end_idx]
            out_pos += chunk_size
        
        # Build pixel_pointer_masked
        pixel_pointer_masked = np.zeros(len(pixel_indices) + 1, dtype=pixel_pointer.dtype)
        pixel_pointer_masked[1:] = np.cumsum(lengths)
        
        logger.info(f"Extracted total of {total} non-zero elements for chunk ID {self.chunk_ID}.")
        return intensity_masked, time_index_masked, pixel_pointer_masked
    
    
    def shm_close(self):
        # Just delete views and clear the dict
        for key in list(self.data_shm.keys()):
            if 'shm_view' in self.data_shm[key]:
                del self.data_shm[key]['shm_view']
        
        self.data_shm.clear()
        gc.collect()
            

class CorrelatorSparseChunkedNumba(SparseCorrelator):
    """
    Implementation of the correlator of the sparse data in chunked mode
    using Numba. The data format is assumed to be CSC-like format with three vectors and
    data shape but in the future expected to be extended to CSR.

    Parameters
    ----------
    extra_options : dict, optional
        Extra options for the correlator.

        Example for the local dask cluster with 4 workers and chunk size of 1000 pixels::
            
            extra_options= {
                'chunks_N': 1000,
                'dask_cluster_type': 'local',
                'dask_local_n_workers': 4,
            }
        
        The following options are avalible:

        **General options**:

        * chunks_N: int, optional
            Number of pixels per chunk. If 0, all pixels in mask are processed in one chunk. Default is 0.
        * calculate_full_g2: bool, optional
            Whether to calculate full g2 function from the data or form the ttcf. Default is True.
        * dask_cluster_type: str, optional
            Type of dask cluster to use. Options are 'local' or 'slurm'. If None, no dask cluster is used. Default is 'local'.
        
        **Local dask cluster options**:

        * dask_local_n_workers: int, optional
            Number of local dask workers. Default is 2.

        **Slurm dask cluster options**:

        * dask_slurm_queue: str, optional
            Partition name for the slurm dask cluster. Default is 'low'.
        * dask_slurm_walltime: str, optional
            Walltime for the slurm dask cluster. Default is '12:00:00'.
        * dask_slurm_workers: int, optional
            Number of slurm dask workers. Default is 2.
        * dask_slurm_processes_per_worker: int, optional
            Number of processes per slurm dask worker. Default is 1.
        * dask_slurm_cores_per_worker: int, optional
            Number of CPU cores per worker for the slurm dask cluster. Default is 1.
        * dask_slurm_memory_per_worker: str, optional
            Memory per worker for the slurm dask cluster. Default is '4GB'.
    """

    def __init__(self, intensity, time_index, pixel_pointer, frames_shape, roimask, **kwargs):
        super().__init__(intensity, time_index, pixel_pointer, frames_shape, roimask, **kwargs)

        # Frames shape is the original shape of the data before converting to sparse format
        # The CSC format represent 2D array where columans are pixels and rows are values of frames
        # at given time index.
        # The CSC matrix (pixel pointer, time index) can be reshaped back to (frames, height, width)
        # using frames_shape
        
        self.frames_shape = frames_shape

        self.ttcf_format = kwargs.get('ttcf_format', None)
        self.t1_t2_binning = kwargs.get('t1_t2_binning', None)
        self.age_binning = kwargs.get('age_binning', None)
        self.lag_binning = kwargs.get('lag_binning', None)
        self.extra_options = kwargs.get('extra_options', None)
        
        # --- load extrea options ---

        # chunks_N name is like this, it means number of pixels per chunk
        # if it is one than load all pixels in mask at once, else split into chunks where
        # the number of pixels pers chunk is equal to chunks_N, the last chunk can have less pixels
        defaults= dict(
            chunks_N = 0,  # 0 means all pixels in mask in one chunk

            calculate_full_g2 = True, # whether to calculate full g2 

            dask_cluster_type = 'local', # 'local' or 'slurm' - if None no dask cluster is used
            
            dask_local_n_workers = 2, # number of local dask workers

            dask_slurm_queue = 'low' , # slurm queue name
            dask_slurm_walltime = '12:00:00', # slurm cluster walltime
            dask_slurm_workers = 2, # number of slurm dask workers
            dask_slurm_processes_per_worker = 1, # number of processes per slurm dask worker
            dask_slurm_cores_per_worker = 1, # number of cores per slurm dask worker
            dask_slurm_memory_per_worker = '4GB', # memory per slurm dask worker
        )

        opts= defaults.copy()
        if isinstance(self.extra_options, dict):
            opts.update(self.extra_options)

        # assigning attributes from merged options
        self.chunks_N = int(opts['chunks_N'])
        self.calculate_full_g2 = bool(opts['calculate_full_g2'])
        
        ## Dask settings
        self.dask_cluster_type = opts['dask_cluster_type']
        #local
        self.dask_local_n_workers = int(opts['dask_local_n_workers'])
        #slurm
        self.dask_slurm_queue = opts['dask_slurm_queue']
        self.dask_slurm_walltime = opts['dask_slurm_walltime']
        self.dask_slurm_workers = int(opts['dask_slurm_workers'])
        self.dask_slurm_processes_per_worker = int(opts['dask_slurm_processes_per_worker'])
        self.dask_slurm_cores_per_worker = int(opts['dask_slurm_cores_per_worker'])
        self.dask_slurm_memory_per_worker = opts['dask_slurm_memory_per_worker']
        
        # --- Prepare the data ---
        logger.info("Preparing data...")
        self._prepare_data(intensity, time_index, pixel_pointer)
        
        # ---Mask processing---
        logger.info("Processing ROI mask...")
        self.roimask = mask_to_3d_bool_stack(self.roimask)

        if self.roimask.ndim == 2:
            self.roimask = self.roimask[np.newaxis, ...]

        self.mask_num = self.roimask.shape[0]

         # --- Results initialization ---
        self.results=Results(
                             roimask= self.roimask, 
                             ttcf_format=self.ttcf_format,
                            )
        
        # --- Computation ---
        self._compute()

        # --- Clean up shared memory  ---
        if self._data['type'] == 'shared_memory':
            for key in ['intensity', 'time_index', 'pixel_pointer']:
                del self._data[key]['shm_view']
                #gc.collect()
                self._data[key]['shm_handle'].close()
                self._data[key]['shm_handle'].unlink()
  
    def _compute(self):
        start_time = time() 
        logger.info(f"Starting computation... {time()-start_time:.2f}s")
        logger.info(f"Data shape: {self.frames_shape}, mask shape: {self.roimask.shape}")

        # --- setting all variables and conditions ---
        calculate_ttcf = bool(self.ttcf_format)
        
        # --- initialize results ttcf and ttcf counts (binning) ---
        if self.ttcf_format is None:
            self.results.ttcf = None
        
        if self.ttcf_format == 't1,t2':
            if self.t1_t2_binning is None:
                self.results.ttcf = np.zeros((self.roimask.shape[0], 
                                        self.frames_shape[0],
                                        self.frames_shape[0],), 
                                        dtype=np.float64)
            if self.t1_t2_binning is not None:
                self.results.ttcf = np.zeros((self.roimask.shape[0], 
                                        self.t1_t2_binning,
                                        self.t1_t2_binning,), 
                                        dtype=np.float64)
        if self.ttcf_format == 'age,lag':

            assert self.age_binning is not None, "age_binning must be specified for age,lag ttcf_format"
            assert self.lag_binning is not None, "lag_binning must be specified for age,lag ttcf_format"
            
            self.results.ttcf  = np.zeros((self.roimask.shape[0], 
                                           self.age_binning, 
                                           10**self.lag_binning[0]-1+self.lag_binning[1]), 
                                           dtype=np.float64)
       
        # --- initialize chunks and data collection variables---
        self.chunks = self._calculate_chunks()
        sum_intensity_global = None
        numerator_global = None

        # --- initialize g2 numerator diagonal storage - full g2 calculation ---
        g2_num_diagonal_global = np.zeros((self.roimask.shape[0],self.frames_shape[0]))
        
        #TODO order better if conditions for similar cases sharing this same True values
        # initialize global numerator and sum intensity arrays
        if self.ttcf_format == 't1,t2' and self.t1_t2_binning is None:
            numerator_global = np.zeros((self.roimask.shape[0],
                                        self.frames_shape[0], 
                                        self.frames_shape[0]), 
                                        dtype=np.float64)
            sum_intensity_global = np.zeros((self.roimask.shape[0],
                                            self.frames_shape[0]),
                                            dtype=np.float64)
        
        if self.ttcf_format =='t1,t2' and self.t1_t2_binning is not None:
            numerator_global = np.zeros((self.roimask.shape[0],
                                        self.t1_t2_binning, 
                                        self.t1_t2_binning), 
                                        dtype=np.float64)
            sum_intensity_global = np.zeros((self.roimask.shape[0],
                                            self.t1_t2_binning),
                                            dtype=np.float64)
        if self.ttcf_format== 'age,lag':
            numerator_global = np.zeros_like(self.results.ttcf)

         # --- Calculate mean row sum for normalization of ttcf---
        logger.info(f"Calculating frame means for normalization {time()-start_time:.2f} s")
        self.row_mean = self._calculate_row_sum(self._data['type'],self.roimask)
       
        # normalize by number of pixels in frame
        mask_sums = np.sum(self.roimask, axis=(1,2)) 
        self.row_mean /= mask_sums[:, np.newaxis]  # shape (n_rois, n_frames)
           
        # --- calculations  ---
        logger.info(f"Worker initialization {time()-start_time:.2f} s")
        worker = ChunkWorker(self.roimask, 
                             self.frames_shape,
                             self.ttcf_format,
                             self.t1_t2_binning,
                             self.age_binning,
                             self.lag_binning,
                             self.row_mean,
                             self.dask_cluster_type,
                             self.calculate_full_g2
                            )
        
        # --- Dask cluster setup ---
        if self.dask_cluster_type is not None:
            self._dask_cluster_setup()
            logger.info(f"Dask SLURM cluster started and scaled {time()-start_time:.2f} s")
        else:
            logger.info(f"Processing locally without Dask {time()-start_time:.2f} s")
        
        all_futures = {}
        future_to_key = {}

        # --- Main loop over chunks ---
        for i in self.chunks:

            mask_id = self.chunks[i]['mask_id']
            pixel_indices = self.chunks[i]['pixel_indices']

            logger.info(f"Processing chunk {i+1}/{len(self.chunks)} for mask ID {mask_id} at {time()-start_time:.2f}s")
            logger.info(f"Chunk details: mask ID {mask_id}, "
                        f"number of pixels {len(pixel_indices)}.")
            
            # Prepare data metadata for worker
            metadata = {}
            if self._data['type'] == 'shared_memory':
                
                for key in ['intensity', 'time_index', 'pixel_pointer']:
                    metadata[key] = self._data[key]['shm_metadata']
                
            if self._data['type'] == 'hdf5':
                for key in ['intensity', 'time_index', 'pixel_pointer']:
                    metadata[key] = self._data[key]   

            if self.dask_cluster_type is None:
                #Synchronous processing (for debugging), no Dask!!!!
                
                logger.info(f"Calculating chunk ID {i} locally {time()-start_time:.2f}s...")
                
                res_chunk, numerator, sum_intensity = worker(
                    self._data['type'],
                    metadata,
                    pixel_indices,
                    i,
                    mask_id
                )
                if numerator is not None:
                    numerator_global[mask_id] += numerator
                
                if sum_intensity_global is not None:
                    sum_intensity_global[mask_id] += sum_intensity
                
                if res_chunk is not None:
                    g2_num_diagonal_global[mask_id] += res_chunk[0]
                
                logger.info(f"Finished chunk {i+1}/{len(self.chunks)} in {time()-start_time:.2f}s ")
            
            # --- Dask processing ---
            elif self.dask_cluster_type is not None:
                logger.info(f"Submitting chunk ID {i} to Dask cluster {time()-start_time:.2f}s...")
                
                future = self._dask_client.submit(worker, 
                                       self._data['type'], 
                                       metadata, 
                                       pixel_indices, 
                                       i,
                                       mask_id)
                
                all_futures[(mask_id, i)] = future
                future_to_key[future] = (mask_id, i)
        
        #Collect results from futures
        if self.dask_cluster_type is not None:
            logger.info(f"Collecting results from Dask cluster {time()-start_time:.2f}s...")
            for future_finished, results in as_completed(all_futures.values(), with_results=True):
                logger.info(f"Collecting results for  chunk ID {future_to_key[future_finished][1]} {time()-start_time:.2f}s...")
                mask_num, chunk_n = future_to_key[future_finished]
                res_chunk, numerator, sum_intensity = results

                if numerator is not None:
                    numerator_global[mask_num] += numerator
                
                if sum_intensity_global is not None:
                    sum_intensity_global[mask_num] += sum_intensity
                       
                if res_chunk is not None:
                    g2_num_diagonal_global[mask_num] += res_chunk[0]

                # remove from pending futures to free memory
                all_futures.pop((mask_num, chunk_n), None)

        #Callculate  final results for each ROI mask
        logger.info(f"Normalizing collected results and calculating g2 {time()-start_time:.2f}s...")
        for i in range(self.roimask.shape[0]):
            
            # number of pixels in this masked chunk
            n_masked_pixels = np.sum(self.roimask[i])
            
            # --- Normalizing results for t1,t2 ttcf ---
            if self.ttcf_format== 't1,t2' and self.t1_t2_binning is None and self.age_binning is  None:
            
                # compute mean intensity per time over masked pixels (include zeros for pixels absent in sparse storage)
                mean_I = sum_intensity_global[i] / n_masked_pixels

                # denominator is outer product of per-time means
                denominator = np.outer(mean_I, mean_I)
                
                # normalize numerator by number of pixels 
                numerator_global[i] = numerator_global[i] / n_masked_pixels
 
                # compute ttcf (guard against divide-by-zero)
                with np.errstate(divide='ignore', invalid='ignore'):
                    ttcf = (numerator_global[i] / denominator)

                self.results.t1= self.results.t2 = np.arange(self.frames_shape[0])
                
            #--- Normalizing results for t1,t2 ttcf with binning ---
            if self.ttcf_format == 't1,t2' and self.t1_t2_binning is not None:
                
                # Calculating bin counts for normalization
                bins_edges , _ = lin_bin(np.arange(self.frames_shape[0]), self.t1_t2_binning)
                counts = calculate_lin_lin_bin_counts(self.frames_shape[0], bins_edges).T
                
                with np.errstate(divide='ignore', invalid='ignore'):
                    ttcf=  (numerator_global[i] / n_masked_pixels /counts.T).T
                
                self.results.t1= self.results.t2 = bin_centers(bins_edges)
                    
            #--- Normalizing results for age,lag ttcf with binning ---
            if self.ttcf_format  == 'age,lag':
               
                bins_lag, _ = lin_log_bin(np.arange(self.frames_shape[0]),
                                            self.lag_binning[0], 
                                            self.lag_binning[1])
                bins_age, _ = lin_bin(np.arange(self.frames_shape[0]), self.age_binning)
                
                # Calculating bin counts for normalization
                counts = calculate_lin_log_bin_counts(self.frames_shape[0], bins_age, bins_lag).T
                
                # normalize numerator (ttcf) by number of pixels  and counts
                with np.errstate(divide='ignore', invalid='ignore'):
                    ttcf = numerator_global[i] / n_masked_pixels/counts

                self.results.age = bin_centers(bins_age)
                self.results.lag = bin_centers_mixed(bins_lag,self.lag_binning[0])
            logger.info(f"Finished normalization for mask ID {i} {time()-start_time:.2f}s...")
            
            # --- G2 calculations ---
            if self.calculate_full_g2:
                logger.info(f"Calculating denominator diagonal for g2 normalization for mask ID {i} {time()-start_time:.2f}s...")
                
                # Initialize g2 results storage
                if self.results.g2 is None:
                    self.results.g2=np.zeros((self.roimask.shape[0],self.frames_shape[0]-1)) #we skip firs diagonal (zero lag)
                    self.results.g2_err=np.zeros_like(self.results.g2)

                # Calculate denominator for full g2 calculations 
                denom_diag= _calculate_denom_diag(self.row_mean[i])
                
                # g2 calculation 
                logger.info(f"Calculating full g2 for mask ID {i} {time()-start_time:.2f}s...")
                g2= g2_num_diagonal_global[i] / denom_diag / n_masked_pixels
                self.results.g2[i]=g2[1:] #skipping first lag (zero lag)
            
            elif not self.calculate_full_g2 and self.t1_t2_binning is not None:
                logger.info(f"Calculating g2 and g2_err from t1,t2 ttcf for mask ID {i} {time()-start_time:.2f}s...")
                
                # Intialize g2 results storage
                if self.results.g2 is None:
                    self.results.g2=np.zeros((self.roimask.shape[0],ttcf.shape[1]-1)) #we skip firs diagonal (zero lag)
                    self.results.g2_err=np.zeros_like(self.results.g2)

                # g2 calculation
                g2, g2_err= calculate_g2_from_ttcf_t1t2(ttcf.T)
                self.results.g2[i]=g2[1:] #skipping first lag (zero lag)
                self.results.g2_err[i]=g2_err[1:] #skipping first lag (zero lag)
            
            elif not self.calculate_full_g2 and self.ttcf_format  == 'age,lag':
                logger.info(f"Calculating g2 and g2_err from age,lag ttcf for mask ID {i} {time()-start_time:.2f}s...")
               
                #Initialize g2 results storage
                if self.results.g2 is None:
                    self.results.g2=np.zeros((self.roimask.shape[0],ttcf.shape[1]-1)) #we skip firs diagonal (zero lag)
                    self.results.g2_err=np.zeros_like(self.results.g2)

                # g2 calculation
                g2,g2_err= calculate_g2_from_ttcf_lag_age(ttcf)
               
                self.results.g2[i]=g2[1:] #skipping first lag (zero lag)
                self.results.g2_err[i]=g2_err[1:] #skipping first lag (zero lag)
            else:
                logger.warning(f"No g2 calculation performed for mask ID {i} {time()-start_time:.2f}s...")
            # Final assignment to results 
            
            if self.ttcf_format is not None:
                self.results.ttcf[i] = ttcf
         
        #Close dask client and cluster
        if self.dask_cluster_type is not None:
            self._dask_client.close()
            self._dask_cluster.close()    
        
        logger.info(f"Computation finished in {time()-start_time:.2f}s")

    def _prepare_data(self, intensity, time_index, pixel_pointer):

        # Initialize storage for data
        data = {}
        data['intensity'] = {}  
        data['time_index'] = {}  
        data['pixel_pointer'] = {}

        # Load data into shared memory if they are numpy arrays
        if all(isinstance(x, np.ndarray) for x in (intensity, time_index, pixel_pointer)):

            data['type'] = 'shared_memory'
            
            for key, arr in (('intensity', intensity),
                                ('time_index', time_index),
                                ('pixel_pointer', pixel_pointer)):
                view, handle = SharedMemoryArray.initialize(arr.shape, arr.dtype)
                data[key]['shm_view'] = view
                data[key]['shm_handle'] = handle
                data[key]['shm_metadata'] = SharedMemoryArray.get_metadata(view, handle)
                
                # copy data to shared memory and delete original array to save memory
                np.copyto(view, arr)
                del arr
                gc.collect()
            
            self._data = data
            self.intensity = data['intensity']['shm_view']
            self.time_index = data['time_index']['shm_view']
            self.pixel_pointer = data['pixel_pointer']['shm_view']
        
        elif all(isinstance(x, h5py.Dataset) for x in (intensity, time_index, pixel_pointer)):
            data['type'] = 'hdf5'
            data['intensity'] = (intensity.file.filename, intensity.name)
            data['time_index'] = (time_index.file.filename, time_index.name)
            data['pixel_pointer'] = (pixel_pointer.file.filename, pixel_pointer.name)
            
            self._data = data
            self.intensity = data['intensity']
            self.time_index = data['time_index']
            self.pixel_pointer = data['pixel_pointer']
            
            #enough to close just file handle of one dataset as they share the same file
            intensity.file.close()

        else:
            raise ValueError("intensity, time_index, and pixel_pointer must be numpy arrays or h5py Datasets.")

    def _calculate_chunks(self):
        """
        Build global chunk index for all ROI masks.

        Returns a dict mapping global_chunk_id -> {
            'mask_id': int,                  # ROI index
            'pixel_indices': ndarray[int],   # global 1D (ravelled) pixel indices in this chunk
            'pixel_range_in_mask': (s, e)    # start/end indices in the mask-local list (s inclusive, e exclusive)
        }

        self.chunks_N defines maximum number of pixels per chunk.
        If self.chunks_N == 0 then all pixels for a given mask are taken in a single chunk.
        """
        chunks = {}
        flat_masks = self.roimask.reshape(self.roimask.shape[0], -1)
        global_chunk_id = 0

        for mask_id, mask in enumerate(flat_masks):
            masked_idx = np.flatnonzero(mask)
            n_pixels = masked_idx.size

            if n_pixels == 0:
                logger.info(f"ROI mask {mask_id+1}/{self.roimask.shape[0]}: 0 pixels, 0 chunks created.")
                continue

            # Determine chunk size: all pixels if chunks_N==0, else self.chunks_N
            chunk_size = n_pixels if self.chunks_N == 0 else self.chunks_N
            n_chunks = int(np.ceil(n_pixels / chunk_size))

            for local_chunk in range(n_chunks):
                s = local_chunk * chunk_size
                e = min(s + chunk_size, n_pixels)
                
                chunks[global_chunk_id] = {
                    'mask_id': mask_id,
                    'pixel_indices': masked_idx[s:e].copy(),
                    'pixel_range_in_mask': (s, e),
                }
                logger.info(f"Created chunk {global_chunk_id} for ROI {mask_id}: pixels {s}:{e} ({e-s} pixels).")
                global_chunk_id += 1

        logger.info(f"Total chunks created: {global_chunk_id}")
        return chunks

    def _calculate_row_sum(self, data_type, roimask=None):
        """
        Calculates the sum of intensities per time frame (row sum) for the sparse data in CSC format.
        The columns represent pixels and rows represent time frames.
        The pixels can be masked using the roimask attribute.
        Uses a Numba-compiled helper for the core accumulation and returns the summed row vector.
        """
        n_frames = self.frames_shape[0]
        
        if data_type == 'shared_memory':
            intensity = self.intensity
            time_index = self.time_index
            pixel_pointer = self.pixel_pointer
            # call numba routine directly on numpy/shared-memory arrays
            return _calculate_row_sum_roimask(intensity, time_index, pixel_pointer, n_frames,roimask=roimask)

        elif data_type == 'hdf5':
            # load datasets into numpy arrays then call numba routine
            with h5py.File(self.intensity[0], "r") as f:
                intensity_ds = f[self.intensity[1]][:]
                time_index_ds = f[self.time_index[1]][:]
                pixel_pointer_ds = f[self.pixel_pointer[1]][:]
            
            return _calculate_row_sum_roimask(intensity_ds, time_index_ds, pixel_pointer_ds, n_frames, roimask=roimask)

        else:
            raise ValueError("Data type must be 'shared_memory' or 'hdf5'.")

    def _dask_cluster_setup(self):
        """
        Setup Dask cluster, slurm or local, based on the provided configuration.
        """
        logger.info(f"Setting up Dask cluster : {self.dask_cluster_type}")
        cluster_type = self.dask_cluster_type  # 'local' or 'slurm' 
        
        if cluster_type == 'local':
            from dask.distributed import LocalCluster
            self._dask_cluster=LocalCluster(n_workers=self.dask_local_n_workers,
                                            threads_per_worker=1,
                                            processes=True,
                                            )
            logger.info(f"Local Dask cluster with {self.dask_local_n_workers} workers started.")

        if cluster_type == 'slurm':
            from dask_jobqueue import SLURMCluster
            self._dask_cluster = SLURMCluster(
                queue=self.dask_slurm_queue,  # Specify SLURM partition/queue
                cores=self.dask_slurm_cores_per_worker,  # CPU cores per job - match your OMP_NUM_THREADS
                memory=self.dask_slurm_memory_per_worker,    # Memory per job
                processes=self.dask_slurm_processes_per_worker, # One Dask worker per SLURM job
                walltime=self.dask_slurm_walltime,  # Job time limit
                log_directory="./dask-worker-logs",
                python=python_executable,  # Use your current Python interpreter from env
                worker_extra_args=['--nthreads', '1']  # Ensure each worker uses a single thread!!! Important for BLAS
            )                                
            self._dask_cluster.scale(self.dask_slurm_workers)  # Adjust number of workers as needed
            logger.info(f"SLURM Dask cluster with {self.dask_slurm_workers} workers, CPUs per worker {self.dask_slurm_cores_per_worker} started.")
        self._dask_client = Client(self._dask_cluster)
        print("Dashboard:", self._dask_client.dashboard_link)
        logger.info("Dashboard: %s", self._dask_client.dashboard_link)