import numpy as np
import scipy.sparse as sp
import h5py 
import pytest

from xpcscorr import correlator_sparse_chunked_numba as correlator_sparse
from xpcscorr import correlator_dense_reference as correlator_reference
from xpcscorr import correlator_dense_chunked as correlator_dense_chunked
from xpcscorr.correlators.sparse.base import _calculate_denom_diag
from xpcscorr.core.utils import calculate_g2_from_ttcf_lag_age, calculate_g2_from_ttcf_t1t2

np.set_printoptions(linewidth=300, threshold=np.inf)

def make_data():
    density = 0.1
    shape = (100, 80, 50)
    mask = np.random.rand(*shape) < density
    
    frames = np.where(mask, np.random.randint(1, 100, size=shape), 0).astype(np.uint8)
    #------
    #frames = frames*0+2
    #------

    # N = 20  # or whatever size you want
    # A = np.zeros((N, N, N), dtype=int)

    # idx = np.arange(N)
    # A[idx, idx, idx] = 1
    # frames = A
    #------
    frames_sparse = sp.csc_matrix(frames.reshape(shape[0], -1))

    leading = 2
    roimask = np.ones((leading,) + shape[1:], dtype=bool)
    roimask = ~roimask 
    
    roimask[0,:,:] = True #
    roimask[1,0:shape[1]//3,0:shape[2]//3] = True 
    

    return frames ,frames_sparse.data, frames_sparse.indices, frames_sparse.indptr, roimask, shape

@pytest.fixture
def data_np_array():
    return make_data()
    

@pytest.fixture
def data_hdf5(tmp_path):

    frames, intensity, time_index, pixel_pointer, roimask, shape = make_data()
    # write to temporary h5 file
    h5_path = tmp_path / "matrix_sparse.h5"
    with h5py.File(h5_path, "w") as f:
        f.create_dataset("intensity", data=intensity, compression=None)
        f.create_dataset("time_index", data=time_index, compression=None)
        f.create_dataset("pixel_pointer", data=pixel_pointer, compression=None)
        f.attrs['shape'] = shape
        f.create_dataset("roimask", data=roimask, compression=None)

    # read dataset back 
    f=h5py.File(h5_path, "r")
    roimask = f["roimask"][:]
    frames_shape = f.attrs['shape']

    return frames, f["intensity"], f["time_index"], f["pixel_pointer"], roimask, frames_shape

@pytest.fixture(params=["data_np_array", "data_hdf5"])
def data_type(request):
    return request.getfixturevalue(request.param)

@pytest.fixture(params=[None,'local']) # None, local, slurm - as params
def dask_cluster_type(request):
    return request.param


@pytest.mark.parametrize("data_type", ["data_np_array", "data_hdf5"],indirect=True)
#@pytest.mark.parametrize("dask_cluster_type", ['local'],indirect=True)
def test_g2_only(data_type, dask_cluster_type):
    """
    Test calculation of only g2 function without ttcf calculation.
    Compare with g2 calculated from reference correlator.
    """
    frames, intensity, time_index, pixel_pointer, roimask, frames_shape = data_type
    # fraction of non-zero pixels (e.g. 0.05 => 5% non-zero, 95% zeros)

    print("Frames shape:", frames_shape)
    print("Sparse representation shape:", frames_shape)
    print("Number of non-zero elements:", len(intensity))

    extra_options = {
        'chunks_N': 1000,
        'dask_cluster_type': dask_cluster_type
    }
    result=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format=None,
        extra_options=extra_options
    )

    result_ref = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="t1,t2",
    )

    for i in range(roimask.shape[0]):
        assert np.allclose(result_ref.g2[i], 
                           result.g2[i], 
                           atol=1e-8, equal_nan=True)



@pytest.mark.parametrize("data_type", ["data_np_array", "data_hdf5"],indirect=True)
#@pytest.mark.parametrize("dask_cluster_type", ['local'],indirect=True)
def test_t1_t2(data_type, dask_cluster_type):
    
    frames, intensity, time_index, pixel_pointer, roimask, frames_shape = data_type
    # fraction of non-zero pixels (e.g. 0.05 => 5% non-zero, 95% zeros)

    print("Frames shape:", frames_shape)
    print("Sparse representation shape:", frames_shape)
    print("Number of non-zero elements:", len(intensity))

    extra_options = {
        'chunks_N': 1000,
        'dask_cluster_type': dask_cluster_type
    }
    result=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format="t1,t2",
        extra_options=extra_options
    )

    result_ref = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="t1,t2",
    )

    

    for i in range(roimask.shape[0]):
        
        result.ttcf[i] = np.nan_to_num(result.ttcf[i], nan=0.0)

        assert np.allclose(np.triu(result.ttcf[i]), 
                           np.triu(result_ref.ttcf[i]), 
                           atol=1e-8, equal_nan=True)
        assert np.allclose(result_ref.g2[i], 
                           result.g2[i], 
                           atol=1e-8, equal_nan=True)


@pytest.mark.parametrize("data_type", ["data_np_array", "data_hdf5"],indirect=True)
#@pytest.mark.parametrize("data_type", ["data_np_array"],indirect=True)
def test_t1_t2_binning(data_type, dask_cluster_type):
    
    frames, intensity, time_index, pixel_pointer, roimask, frames_shape = data_type
    # fraction of non-zero pixels (e.g. 0.05 => 5% non-zero, 95% zeros)

    print("Frames shape:", frames_shape)
    print("Number of non-zero elements:", len(intensity))

    bins=17

    extra_options = {
        'chunks_N': 1000,
        'dask_cluster_type': dask_cluster_type
    }
    result=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format="t1,t2",
        t1_t2_binning = bins,
        extra_options = extra_options
    )

    result_ref = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="t1,t2",
        t1_t2_binning = bins,
    )


    for i in range(roimask.shape[0]):
        assert np.allclose(np.tril(result.ttcf[i]), 
                           np.tril(result_ref.ttcf[i]), 
                           atol=1e-8, equal_nan=True)
        assert np.allclose(result_ref.g2[i], 
                           result.g2[i], 
                           atol=1e-8, equal_nan=True)
    
    print("Finished correlator_sparse")

@pytest.mark.parametrize("data_type", ["data_np_array", "data_hdf5"],indirect=True)
#@pytest.mark.parametrize("data_type", ["data_np_array"],indirect=True)
def test_age_lag_binning(data_type,dask_cluster_type):

    frames, intensity, time_index, pixel_pointer, roimask, frames_shape = data_type

    age_binning=20
    lag_binning=(1,10)

    extra_options = {
       'chunks_N': 1000,
       'dask_cluster_type': dask_cluster_type,
    }

    result_ref = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="age,lag",
        age_binning = age_binning,
        lag_binning = lag_binning
    )

    result=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format="age,lag",
        age_binning = age_binning,
        lag_binning = lag_binning,
        extra_options = extra_options
    )

    for i in range(roimask.shape[0]):
        assert np.allclose(result.ttcf[i], 
                           result_ref.ttcf[i], 
                           atol=1e-8, equal_nan=True)
    for i in range(roimask.shape[0]):
        assert np.allclose(result.g2[i], 
                           result_ref.g2[i], 
                           atol=1e-8, equal_nan=True)

@pytest.mark.parametrize("data_type", ["data_np_array"],indirect=True)
def test_g2_from_ttcf(data_type):
    """
    Test calculation of g2 and g2_err from ttcf for both t1,t2 and age,lag formats.
    Compare with g2 and g2_err calculated from ttcf of reference correlator.
    """
    frames, intensity, time_index, pixel_pointer, roimask, frames_shape = data_type

    age_binning=20
    lag_binning=(1,10)
    t1_t2_binning=10

    extra_options = {
       'chunks_N': 1000,
       'dask_cluster_type': None,
       'calculate_full_g2': False
    }

    result_ref_t1_t2 = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="t1,t2",
        t1_t2_binning = t1_t2_binning,
        
    )

    result_ref_age_lag = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="age,lag",
        age_binning = age_binning,
        lag_binning = lag_binning
    )

    result_t1_t2_binned=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format="t1,t2",
        t1_t2_binning = t1_t2_binning,
        extra_options = extra_options
    )

    result_age_lag=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format="age,lag",
        age_binning = age_binning,
        lag_binning = lag_binning,
        extra_options = extra_options
    )

    for i in range(roimask.shape[0]):
        # calculations from the reference results
        g2_t1t2_binned, g2_t1t2_binned_err = calculate_g2_from_ttcf_t1t2(result_ref_t1_t2.ttcf[i].T)
        g2_age_lag, g2_age_lag_err = calculate_g2_from_ttcf_lag_age(result_ref_age_lag.ttcf[i])
        
        assert np.allclose(result_t1_t2_binned.g2[i], 
                           g2_t1t2_binned[1:], 
                           atol=1e-8, equal_nan=True)
        assert np.allclose(result_t1_t2_binned.g2_err[i],
                           g2_t1t2_binned_err[1:], 
                           atol=1e-8, equal_nan=True)

        assert np.allclose(result_age_lag.g2[i], 
                           g2_age_lag[1:], 
                           atol=1e-8, equal_nan=True)
        assert np.allclose(result_age_lag.g2_err[i],
                           g2_age_lag_err[1:], 
                           atol=1e-8, equal_nan=True)
        
#@pytest.mark.parametrize("data_type", ["data_np_array", "data_hdf5"],indirect=True)
@pytest.mark.parametrize("data_type", ["data_np_array"],indirect=True)
def test_temp(data_type):

    frames, intensity, time_index, pixel_pointer, roimask, frames_shape = data_type

    age_binning=20
    lag_binning=(1,10)

    extra_options = {
       'chunks_N': 1000,
       'dask_cluster_type': None,
       'calculate_full_g2': True
    }

    result_ref = correlator_reference(
        frames,
        roimask=roimask,
        ttcf_format="t1,t2",
        t1_t2_binning =20
    )

    result=correlator_sparse(
        intensity = intensity,
        time_index = time_index,
        pixel_pointer = pixel_pointer,
        frames_shape = frames_shape,
        roimask = roimask,
        ttcf_format="t1,t2",
        t1_t2_binning =20,
        extra_options = extra_options
    )

    for i in range(roimask.shape[0]):
        assert np.allclose(result.ttcf[i], 
                           result_ref.ttcf[i], 
                           atol=1e-8, equal_nan=True)
    for i in range(roimask.shape[0]):
        assert np.allclose(result.g2[i], 
                           result_ref.g2[i], 
                           atol=1e-8, equal_nan=True)

def test_denom_diag_calculation():
    """
    This test checks the correctness of the _calculate_denom_diag function.
    It compares the output of the function with a reference calculation using
    the outer product method.
    """
 
    frames_n=20
    row_mean=np.random.rand(frames_n)
    # outer product -> full (frames_n x frames_n) matrix
    denom_tmp = np.outer(row_mean, row_mean)  # shape (frames_n, frames_n)
    denom_diag_ref = np.zeros(frames_n)
    for l in range(frames_n):
        denom_diag_ref[l] = np.sum(np.diagonal(denom_tmp, l))
        
    denom_diag= _calculate_denom_diag(row_mean)
    assert np.allclose(denom_diag, denom_diag_ref, atol=1e-8, equal_nan=True)