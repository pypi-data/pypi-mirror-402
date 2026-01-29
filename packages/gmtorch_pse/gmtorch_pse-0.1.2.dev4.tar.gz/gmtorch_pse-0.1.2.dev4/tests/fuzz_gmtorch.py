import torch
import numpy as np
from hypothesis import given, strategies as st, settings, assume
from hypothesis.extra import numpy as nph

from gmtorch_pse._gaussian_mixture import _check_weights, _check_means, _check_covariance
from gmtorch_pse._gaussian_mixture import GaussianMixture


# hypothesis strategy, random matrices
_float_arrays_strategy = nph.arrays(
    dtype=np.float32,
    shape=nph.array_shapes(min_dims=1, max_dims=3, min_side=1, max_side=16),
    elements=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
)


# check weights
@settings(max_examples=500, derandomize=False)
@given(
    weights_arr=_float_arrays_strategy,
    n_components=st.one_of(
        st.integers(min_value=-10, max_value=10),
        st.none(),
        st.lists(st.integers()),
    ),
)
def test_check_weights(weights_arr, n_components):
    tensor = torch.from_numpy(weights_arr).float()
    try:
        _check_weights(tensor, n_components)
    except (TypeError, ValueError):
        pass


# hypothesis strategy, happy weights matrices
_happy_weights_array_strategy = nph.arrays(
    dtype=np.float32,
    shape=nph.array_shapes(min_dims=1, max_dims=1, min_side=1, max_side=100),
    elements=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)


# happy check weights
@settings(max_examples=500, derandomize=False)
@given(weights_arr=_happy_weights_array_strategy)
def test_happy_check_weights(weights_arr):
    assume(np.sum(weights_arr) > 1e-5)

    tensor = torch.from_numpy(weights_arr).float()
    n_components = tensor.size()[0]

    _check_weights(tensor, n_components)


# check means
@settings(max_examples=500, derandomize=False)
@given(
    means_arr=_float_arrays_strategy,
    n_components=st.one_of(st.integers(min_value=-2, max_value=50), st.none(), st.lists(st.integers())),
    n_dimensions=st.one_of(st.integers(min_value=-2, max_value=20), st.none(), st.lists(st.integers())),
)
def test_check_means(means_arr, n_components, n_dimensions):
    means = torch.from_numpy(means_arr).float()

    try:
        _check_means(means, n_components, n_dimensions)
    except (TypeError, ValueError):
        pass


# hypothesis strategy, happy means matrices
_happy_means_array_strategy = nph.arrays(
    dtype=np.float32,
    shape=nph.array_shapes(min_dims=2, max_dims=2, min_side=1, max_side=100),
    elements=st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)


# happy check means
@settings(max_examples=500, derandomize=False)
@given(means_arr=_happy_means_array_strategy)
def test_happy_checks_means(means_arr):
    means = torch.from_numpy(means_arr).float()
    n_components = means.shape[0]
    n_dimensions = means.shape[1]
    _check_means(means, n_components, n_dimensions)


# check covariance
@settings(max_examples=500, derandomize=False)
@given(
    covariance_arr=_float_arrays_strategy,
    n_components=st.one_of(st.integers(min_value=-10, max_value=50), st.none(), st.lists(st.integers())),
    n_dimensions=st.one_of(st.integers(min_value=-10, max_value=10), st.none(), st.lists(st.integers())),
)
def test_check_covariance(covariance_arr, n_components, n_dimensions):
    covariances = torch.from_numpy(covariance_arr).float()

    try:
        _check_covariance(covariances, n_components, n_dimensions)
    except (TypeError, ValueError):
        pass


# happy check covariance
@settings(max_examples=500, derandomize=False)
@given(n_components=st.integers(min_value=1, max_value=50), n_dimensions=st.integers(min_value=1, max_value=50))
def test_happy_check_covariance(n_components, n_dimensions):
    device = _choose_device(n_components, n_dimensions)

    covariance = _random_full_cov_batch(n_components, n_dimensions, eps=1e-5, device=device, dtype=torch.float32)
    _check_covariance(covariance, n_components, n_dimensions)


# test user gm constructor
@given(
    n_components=st.one_of(st.integers(min_value=-10, max_value=50), st.none(), st.lists(st.integers())),
    n_dimensions=st.one_of(st.integers(min_value=-10, max_value=10), st.none(), st.lists(st.integers())),
    weights_arr=_float_arrays_strategy,
    means_arr=_float_arrays_strategy,
    covariances_arr=_float_arrays_strategy,
)
def test_user_gm(n_components, n_dimensions, weights_arr, means_arr, covariances_arr):
    weights = torch.from_numpy(weights_arr).float()
    means = torch.from_numpy(means_arr).float()
    covariances = torch.from_numpy(covariances_arr).float()

    try:
        GaussianMixture.from_user(n_components, n_dimensions, weights, means, covariances)
    except (TypeError, ValueError):
        pass


# happy test user gm constructor
@settings(max_examples=500, derandomize=False)
@given(n_components=st.integers(min_value=1, max_value=50), n_dimensions=st.integers(min_value=1, max_value=50))
def test_happy_user_gm(n_components, n_dimensions):
    device = _choose_device(n_components, n_dimensions)

    # WEIGHTS
    weights = torch.rand(n_components, device=device, dtype=torch.float32)

    # MEANS
    min_value = -10.0
    max_value = 10.0
    means = (max_value - min_value) * torch.rand(
        n_components, n_dimensions, device=device, dtype=torch.float32
    ) + min_value

    # COVARIANCE
    covariances = _random_full_cov_batch(n_components, n_dimensions, eps=1e-5, device=device, dtype=torch.float32)

    GaussianMixture.from_user(n_components, n_dimensions, weights, means, covariances)


# TODO: auf hypothesis umbauen, aktuell nutze ich andere random generator, so nicht rekonstruierbar
# happy test gmm marginalization
@settings(max_examples=500, derandomize=False)
@given(test=st.integers(min_value=3, max_value=1000))
def test_happy_marginalization(test):
    n_components = 5
    n_dimensions = 5
    weights = torch.tensor([0.1, 0.2, 0.3, 0.4, 0.5])

    # GENERATE RANDOM REMAINING DIMENSIONS TENSOR
    # zufällige Länge n_remaining_dimensions in [1, n_dimensions - 1]
    n_remaining_dimensions = torch.randint(1, n_dimensions, (1,)).item()
    # zufällige Permutation von 1 bis n_dimensions - 1, dann die n_remaining_dimensions nehmen
    random_dimension_indices = torch.randperm(4) + 1  # ergibt eine zufällige Reihenfolge, Werte 1..4
    remaining_dimensions = random_dimension_indices[:n_remaining_dimensions]  # 1D-Tensor mit Länge k, ohne Duplikate

    # 5x5 MEANS FROM 00 TO 44
    rows = torch.arange(n_components).unsqueeze(1)  # [K, 1] -> 0..4 als Spaltenvektor
    cols = torch.arange(n_dimensions).unsqueeze(0)  # [1, D] -> 0..4 als Zeilenvektor
    means = (rows * 10 + cols).to(torch.float32)

    device = _choose_device(n_components, n_dimensions)
    # returns sane covariance tensor
    happy_covariance = _random_full_cov_batch(n_components, n_dimensions, eps=1e-5, device=device, dtype=torch.float32)

    # test gmm
    gmm = GaussianMixture.from_user(n_components, n_dimensions, weights, means, happy_covariance)

    # marginalized gmm
    m_gmm = gmm.marginalization(remaining_dimensions)


# best practices: alles auf selben gerät erzeugen, falls später gemeinsam genutzt wird.
def _choose_device(n_components, n_dimensions):
    # Wenn CUDA verfügbar und Problem groß genug, nutze GPU
    if torch.cuda.is_available() and (n_components * n_dimensions**2 > 1e6):
        return torch.device("cuda")
    return torch.device("cpu")


# returns a sane covariance tensor
def _random_full_cov_batch(
    n_components, n_dimensions, eps: float = 1e-5, device=None, dtype=torch.float32
) -> torch.Tensor:
    # covariances: (n_components, n_dimensions, n_dimensions)
    covariances = torch.randn(n_components, n_dimensions, n_dimensions, device=device, dtype=dtype)
    # Gram: (n_components, n_dimensions, n_dimensions)
    covariances = covariances @ covariances.transpose(-1, -2)
    # Symmetrize
    covariances = 0.5 * (covariances + covariances.transpose(-1, -2))
    # Add eps*I to make PD (expand identity to batch)
    covariances = covariances + eps * torch.eye(n_dimensions, device=device, dtype=dtype).expand_as(covariances)
    return covariances
