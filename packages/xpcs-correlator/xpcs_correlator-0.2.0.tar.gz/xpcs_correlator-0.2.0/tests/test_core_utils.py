import numpy as np
from xpcscorr.core.utils import (mask_to_3d_bool_stack,
                                 lin_bin,
                                 lin_log_bin,
                                 calculate_lin_log_bin_counts,
                                 calculate_lin_lin_bin_counts
                                 )


def ref_count_bin_age_lag(frames_n, lag_binning, age_binning):
    """
    Thi method computes number of elemnts per age-lag bin, for given binning parameters.
    Used as reference to test binning utilities.
    """

    bins_lag, bins_lag_indices = lin_log_bin(np.arange(frames_n),
                                        lag_binning[0], 
                                        lag_binning[1])
    bins_age, bins_age_indices = lin_bin(np.arange(frames_n), age_binning)
    
    t2, t1 = np.indices((frames_n, frames_n))
    lag = t2 - t1
    age = (t1+t2)/2
    
    ind = lag >=0
    lag_selected = lag[ind]
    age_selected = age[ind]
    bins = (bins_age, bins_lag)
    counts, _, _,  = np.histogram2d(age_selected, lag_selected, bins=bins)

    return counts, bins_age, bins_lag

def ref_count_bin_lin_lin(frames_n, bins_n):
    
    bins_edges , bins_ind = lin_bin(np.arange(frames_n), bins_n)
                
   

    counts = np.zeros((bins_n, bins_n), dtype=int)
    ix, iy = np.meshgrid(bins_ind, bins_ind, indexing='ij')
    rows, cols = np.tril_indices_from(ix)
    
    ix_lower = ix[rows, cols]
    iy_lower = iy[rows, cols]
    np.add.at(counts, (ix_lower.ravel(), iy_lower.ravel()), 1)

    return counts, bins_edges



def test_mask_to_3d_bool_stack():
    # 2D binary mask (0/1)
    mask_2d_bin = np.array([[0, 1, 0],
                            [1, 0, 1],
                            [0, 1, 0]])
    out = mask_to_3d_bool_stack(mask_2d_bin)
    assert out.shape == (1, 3, 3)
    assert np.array_equal(out[0], mask_2d_bin.astype(bool))

    # 2D binary mask (all zeros)
    mask_2d_zero = np.zeros((3, 3), dtype=int)
    out = mask_to_3d_bool_stack(mask_2d_zero)
    assert out.shape == (1, 3, 3)
    assert np.all(out == False)

    # 2D boolean mask
    mask_2d_bool = np.array([[True, False, True],
                             [False, True, False],
                             [True, False, True]])
    out = mask_to_3d_bool_stack(mask_2d_bool)
    assert out.shape == (1, 3, 3)
    assert np.array_equal(out[0], mask_2d_bool)

    # 2D integer mask (labels)
    mask_2d_labels = np.array([[0, 2, 1],
                               [1, 2, 0],
                               [2, 1, 0]])
    out = mask_to_3d_bool_stack(mask_2d_labels)
    assert out.shape == (2, 3, 3)  # labels 1 and 2
    assert np.array_equal(out[0], mask_2d_labels == 1)
    assert np.array_equal(out[1], mask_2d_labels == 2)

    # 3D binary mask
    mask_3d_bin = np.zeros((3, 3, 3), dtype=int)
    mask_3d_bin[0, 0, 0] = 1
    mask_3d_bin[1, 1, 1] = 1
    mask_3d_bin[2, 2, 2] = 1
    out = mask_to_3d_bool_stack(mask_3d_bin)
    assert out.shape == (3, 3, 3)
    assert out[0, 0, 0] == True
    assert out[1, 1, 1] == True
    assert out[2, 2, 2] == True
    assert np.sum(out) == 3

    # 3D boolean mask
    mask_3d_bool = np.zeros((3, 3, 3), dtype=bool)
    mask_3d_bool[0, 1, 2] = True
    mask_3d_bool[1, 2, 0] = True
    mask_3d_bool[2, 0, 1] = True
    out = mask_to_3d_bool_stack(mask_3d_bool)
    assert out.shape == (3, 3, 3)
    assert out[0, 1, 2] == True
    assert out[1, 2, 0] == True
    assert out[2, 0, 1] == True
    assert np.sum(out) == 3

    print("All mask_to_3d_bool_stack tests passed.")


def test_lin_bin_vs_histogram():

    
    x = np.arange(0, 100, 5)
    bin_edges, indices = lin_bin(x, 10)

    # Count occurrences per bin using indices
    hist_from_indices = np.bincount(indices, minlength=len(bin_edges)-1)
    hist_np, _ = np.histogram(x, bin_edges)
    assert np.array_equal(hist_from_indices, hist_np), f"Got {hist_from_indices}, expected {hist_np}"


def test_lin_log_bin_indices_vs_histogram():
    x = np.arange(0, 1001)
    bin_edges, indices = lin_log_bin(x, 1, 10)

    # build histogram from returned per-element indices (0-based, one index per element)
    hist_from_indices = np.bincount(indices, minlength=len(bin_edges) - 1)

    # numpy histogram using the same edges
    hist_np, _ = np.histogram(x, bin_edges)

    assert np.array_equal(hist_from_indices, hist_np)

def test_calculate_lin_log_bin_counts():
    frames_n = 1000
    lag_binning = (1, 13)
    age_binning = 24

    counts_ref, bins_age, bins_lag = ref_count_bin_age_lag(frames_n, lag_binning, age_binning)
    counts_test = calculate_lin_log_bin_counts(frames_n, bins_age, bins_lag).T

    assert np.array_equal(counts_ref, counts_test), "Age-Lag Bin counts do not match reference implementation."

def test_calculate_lin_lin_bin_counts():
    frames_n = 117
    bins_n = 13

    counts_ref, bins_edges = ref_count_bin_lin_lin(frames_n, bins_n)
    counts_test = calculate_lin_lin_bin_counts(frames_n, bins_edges).T

    assert np.array_equal(counts_ref, counts_test), "Lin-Lin Bin counts do not match reference implementation."