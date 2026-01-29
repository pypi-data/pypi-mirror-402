import torch
from unittest import mock
import pytest

from gmtorch_pse._gaussian_mixture import _check_weights, _check_means, _check_covariance, _check_data_points
from gmtorch_pse._gaussian_mixture import GaussianMixture

N_COMPONENTS = 2
N_DIMENSIONS = 2


class RandomData:
    """
    Minimal helper class for tests.

    Generates random but valid parameters for a Gaussian mixture:
      - weights: (n_components,)
      - means: (n_components, n_dimensions)
      - covariances: (n_components, n_dimensions, n_dimensions)

    ONLY for testing your GaussianMixtureTorch.
    """

    def __init__(
        self,
        seed,
        n_components=N_COMPONENTS,
        n_dimensions=N_DIMENSIONS,
        dtype=torch.float64,
        device=None,
    ):
        # Device and dtype
        if device is None:
            device = torch.device("cpu")
        self.device = device
        self.dtype = dtype

        if seed is not None:
            torch.manual_seed(seed)

        self.n_components = n_components
        self.n_dimensions = n_dimensions

        # weights: random positive numbers normalized to sum to 1
        w = torch.rand(n_components, device=device, dtype=dtype)
        self.weights = w / w.sum()

        self.means = torch.randn(n_components, n_dimensions, device=device, dtype=dtype)

        self.covariances = self._generate_full_covariances()

    def _generate_full_covariances(self):
        K = self.n_components
        D = self.n_dimensions
        covs = torch.empty(K, D, D, device=self.device, dtype=self.dtype)
        eps = 1e-3  # to ensure positive-definiteness (instead of SPD)

        for k in range(K):
            A = torch.randn(D, D, device=self.device, dtype=self.dtype)
            cov = A @ A.T + eps * torch.eye(D, device=self.device, dtype=self.dtype)
            covs[k] = cov

        return covs


# def test__check_parameters():
#     instanz = GaussianMixture()
#     instanz._check_weights = mock.MagicMock()
#     instanz._check_parameters()

#     _check_weights.assert_called


@pytest.mark.parametrize("K", range(1, 6))
def test_check_weights_accept_valid(K):
    # already normalized -> should return identical values
    w_valid = torch.full((K,), 1.0 / K, dtype=torch.float32)
    out = _check_weights(w_valid, K)
    assert torch.allclose(out, w_valid)

    # not normalized -> should normalize
    w = torch.arange(1, K + 1, dtype=torch.float32)
    out = _check_weights(w, K)
    assert torch.isclose(out.sum(), torch.tensor(1.0), atol=1e-6)
    assert (out >= 0).all()


# TODO : Edge cases: if input is 0: error no
@pytest.mark.parametrize(
    "bad, exc",
    [
        ([2.0, 3.0, 4.0], TypeError),  # not tensor
        (torch.tensor([[1, 2, 3], [0.2, 0.3, 0.5]], dtype=torch.float32), ValueError),  # not 1D
        (torch.tensor([1, 2, 3], dtype=torch.int64), TypeError),  # not float
        (torch.tensor([0.2, float("nan"), 0.8], dtype=torch.float32), ValueError),  # NaN
        (torch.tensor([0.2, float("inf"), 0.8], dtype=torch.float32), ValueError),  # Inf
        (torch.tensor([0.2, -0.1, 0.9], dtype=torch.float32), ValueError),  # negative
        (torch.tensor([0.5, 0.5], dtype=torch.float32), ValueError),  # wrong length
        (torch.zeros(3, dtype=torch.float32), ValueError),  # Zeros
    ],
)
def test_check_weights_rejects_invalid(bad, exc):
    with pytest.raises(exc):
        _check_weights(bad, 3)


@pytest.mark.parametrize("K", range(1, 6))
def test_check_weights_rejects_wrong_length_for_K(K):
    w_bad = torch.full((K + 1,), 1.0 / (K + 1), dtype=torch.float32)
    with pytest.raises(ValueError):
        _check_weights(w_bad, K)


def test_check_means_accepts_valid():
    """
    Tests the _check_means(means, n_components, n_dimensions) function.

    Expected behaviour:
    - valid means: no exception
    - non-tensor: TypeError
    - wrong ndim: ValueError
    - wrong n_components: ValueError
    - wrong n_dimensions: ValueError
    - non-float dtype: TypeError
    - NaN/Inf inside: ValueError
    """
    K = 2
    D = 3
    means_valid = torch.zeros(K, D, dtype=torch.float32)
    _check_means(means_valid, K, D)


@pytest.mark.parametrize(
    "bad, K, D, exc",
    [
        ([[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]], 2, 3, TypeError),  # non-tensor
        (torch.zeros(3, dtype=torch.float32), 2, 3, ValueError),  # wrong ndim (1D)
        (torch.zeros(3, 3, dtype=torch.float32), 2, 3, ValueError),  # wrong K
        (torch.zeros(2, 4, dtype=torch.float32), 2, 3, ValueError),  # wrong D
        (torch.zeros(2, 3, dtype=torch.int64), 2, 3, TypeError),  # non-float dtype
        (torch.tensor([[float("nan"), 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float32), 2, 3, ValueError),  # NaN
        (torch.tensor([[float("inf"), 0.0, 0.0], [0.0, 0.0, 0.0]], dtype=torch.float32), 2, 3, ValueError),  # Inf
    ],
)
def test_check_means_rejects_invalid(bad, K, D, exc):
    with pytest.raises(exc):
        _check_means(bad, K, D)


def test_check_covariance_accepts_valid():
    """
    Tests the _check_covariance(covariance) function.

    Expected behaviour:
    - valid covariance (K, D, D), symmetric, PD, float, no NaN/Inf: no exception
    - non-tensor: TypeError
    - wrong ndim: ValueError
    - wrong shape: ValueError
    - non-float dtype: TypeError
    - NaN/Inf: ValueError
    - non-symmetric: ValueError
    - not positive-definite: ValueError
    """
    K = 2
    D = 3
    cov_valid = torch.stack([torch.eye(D) for _ in range(K)], dim=0).to(torch.float32)
    _check_covariance(cov_valid, K, D)


@pytest.mark.parametrize(
    "bad, K, D, exc",
    [
        ([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]] * 2, 2, 3, TypeError),  # non-tensor
        (torch.eye(3, dtype=torch.float32), 2, 3, ValueError),  # wrong ndim (2D)
        (torch.stack([torch.eye(3) for _ in range(3)], dim=0).to(torch.float32), 2, 3, ValueError),  # wrong K
        (torch.zeros(2, 3, 4, dtype=torch.float32), 2, 3, ValueError),  # wrong last dim
        (torch.stack([torch.eye(3) for _ in range(2)], dim=0).to(torch.int64), 2, 3, TypeError),  # non-float dtype
        (
            torch.tensor(
                [
                    [[float("nan"), 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                ],
                dtype=torch.float32,
            ),
            2,
            3,
            ValueError,
        ),  # NaN
        (
            torch.tensor(
                [
                    [[float("inf"), 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                ],
                dtype=torch.float32,
            ),
            2,
            3,
            ValueError,
        ),  # Inf
        # non-symmetric
        (
            torch.tensor(
                [
                    [[1.0, 0.5, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                ],
                dtype=torch.float32,
            ),
            2,
            3,
            ValueError,
        ),
        # not PD (singular)
        (torch.zeros(2, 3, 3, dtype=torch.float32), 2, 3, ValueError),
    ],
)
def test_check_covariance_rejects_invalid(bad, K, D, exc):
    with pytest.raises(exc):
        _check_covariance(bad, K, D)


def test_check_data_points_accepts_valid():
    D = 3
    data_points = torch.randn(10, D, dtype=torch.float32)
    _check_data_points(data_points, D)


@pytest.mark.parametrize(
    "bad, D, exc",
    [
        ([[0.0, 1.0, 2.0]], 3, TypeError),  # non-tensor
        (torch.zeros(3, dtype=torch.float32), 3, ValueError),  # wrong ndim (1D)
        (torch.zeros(2, 4, dtype=torch.float32), 3, ValueError),  # wrong n_dimensions
        (torch.zeros(2, 3, dtype=torch.int64), 3, TypeError),  # non-float dtype
        (torch.tensor([[float("nan"), 0.0, 0.0]], dtype=torch.float32), 3, ValueError),  # NaN
        (torch.tensor([[float("inf"), 0.0, 0.0]], dtype=torch.float32), 3, ValueError),  # Inf
    ],
)
def test_check_data_points_rejects_invalid(bad, D, exc):
    with pytest.raises(exc):
        _check_data_points(bad, D)


def assert_valid_gmm(gmm, K: int, D: int):
    # shapes
    assert gmm.weights.shape == (K,)
    assert gmm.means.shape == (K, D)
    assert gmm.covariance.shape == (K, D, D)

    # basic numeric sanity
    assert torch.is_floating_point(gmm.weights)
    assert torch.is_floating_point(gmm.means)
    assert torch.is_floating_point(gmm.covariance)

    assert torch.isfinite(gmm.weights).all()
    assert torch.isfinite(gmm.means).all()
    assert torch.isfinite(gmm.covariance).all()

    # weights are probabilities
    assert (gmm.weights >= 0).all()
    assert torch.isclose(gmm.weights.sum(), torch.tensor(1.0, dtype=gmm.weights.dtype), atol=1e-6)


def test_from_default_exact_and_valid():
    gmm = GaussianMixture.from_default()
    assert gmm.n_components == 1
    assert gmm.n_dimensions == 1
    assert_valid_gmm(gmm, 1, 1)

    # exact constants (only here!)
    assert torch.allclose(gmm.weights, torch.tensor([1.0], dtype=gmm.weights.dtype))
    assert torch.allclose(gmm.means, torch.tensor([[0.0]], dtype=gmm.means.dtype))
    assert torch.allclose(gmm.covariance, torch.tensor([[[1.0]]], dtype=gmm.covariance.dtype))


@pytest.mark.parametrize("K,D", [(1, 1), (2, 1), (2, 3), (5, 2)])
def test_from_user_valid_invariants(K, D):
    torch.manual_seed(0)

    w = torch.rand(K, dtype=torch.float32)
    w = w / w.sum()

    means = torch.randn(K, D, dtype=torch.float32)

    # guaranteed PD covariances
    covs = torch.empty(K, D, D, dtype=torch.float32)
    eps = 1e-3
    for k in range(K):
        A = torch.randn(D, D, dtype=torch.float32)
        covs[k] = A @ A.T + eps * torch.eye(D, dtype=torch.float32)

    gmm = GaussianMixture.from_user(K, D, w, means, covs)
    assert_valid_gmm(gmm, K, D)


@pytest.mark.parametrize("seed", [0, 1, 2, 123])
def test_from_random_invariants(seed):
    gmm = GaussianMixture.from_random(seed, max_components=10, max_dimensions=6)
    assert_valid_gmm(gmm, gmm.n_components, gmm.n_dimensions)


#  TODO :Check of means and variance if k = 1 (mixture is equivalent to just a gaussian distribution)
# 1. step: generate sample
# 2. step: calculate empiric mean of generated samples
# 3. step: compare with attribute (need tolerance) (e.g. user input in constructor)
# 4. step: repeat 2,3 for covariance
def test_single_component_default():
    """
    Verifies that for K=1, the generated samples statistically match
    the parameters (Mean, Covariance).
    """
    N_SAMPLES = 50_000  # (we can still change this number, but it should be high (because of law of large numbers))
    torch.manual_seed(42)

    # 1. Setup parameters to initialize gmm we want to test
    gmm = GaussianMixture.from_default()

    # 2. Generate samples
    samples = gmm.generate_samples(n_samples=N_SAMPLES)

    # 3. Calculate mean of the generated samples
    sample_mean = torch.mean(samples, dim=0)

    # 4. Calculate empirical covariance
    sample_cov = torch.cov(samples.T)

    # 5. Define Expectations (Standard Normal Distribution)
    expected_mean = torch.zeros(1, dtype=samples.dtype)  # [0.0]
    expected_cov = torch.tensor(1.0, dtype=samples.dtype)  # 1.0 (Scalar because D=1)

    # 6. Compare with tolerance - means
    assert torch.allclose(sample_mean, expected_mean, atol=0.02), f"Default Mean should be ~0.0, got {sample_mean}"

    # 7. Compare with tolerance - covariances
    assert torch.allclose(sample_cov, expected_cov, atol=0.02), f"Default Covariance should be ~1.0, got {sample_cov}"


# TODO it may be useful to implement Random DAta class here
# to get random data not hardcoded
def test_from_user_statistics_hardcoded():
    """
    Tests user constructor by verifying that the generated samples
    statistically match these fixed inputs.
    """
    K = 1
    D = 2
    N_SAMPLES = 100_000
    torch.manual_seed(42)

    w_in = torch.tensor([1.0], dtype=torch.float32)

    # TODO random hardcoded we should change that
    mu_in = torch.tensor([[10.0, -5.0]], dtype=torch.float32)

    cov_in = torch.tensor([[[2.0, 0.0], [0.0, 0.5]]], dtype=torch.float32)

    gmm = GaussianMixture.from_user(K, D, w_in, mu_in, cov_in)

    samples = gmm.generate_samples(n_samples=N_SAMPLES)

    sample_mean = torch.mean(samples, dim=0)
    sample_cov = torch.cov(samples.T)

    assert torch.allclose(
        sample_mean, mu_in[0], atol=0.05
    ), f"Sample Mean {sample_mean} deviates from hardcoded {mu_in[0]}."

    assert torch.allclose(
        sample_cov, cov_in[0], atol=0.05
    ), f"Sample Cov {sample_cov} deviates from hardcoded {cov_in[0]}."
