# TODO: Add code to create gmm
# TODO: Add code to create samples from gmm
# mypy: disable-error-code=union-attr

import torch
import math
from torch import softmax
from typing import Optional

# Numerical stability constant
EPSILON = 1e-6


def _check_weights(weights: torch.Tensor, n_components: int) -> torch.Tensor:
    """
    Validate the weights for a GMM.
    Args:
        weights (torch.Tensor): a 1D-Tensor containing the weights as floats.
        n_components (int): the expected number of components.

    Returns:
        weights. If all weights add up to 1 it will return the original weights.
        If not, it will normalize weights and return the new weights.

    """
    # Check if weights are datatype Tensor and NAN, INF:
    _assert_finite(weights, "weights")

    # Check if weights are 1D-Tensor
    if not weights.ndim == 1:
        raise ValueError("weights are not a 1D Tensor!")
    # Check if weights are floats
    if not torch.is_floating_point(weights):
        raise TypeError(f"weights should floats, but weights were : {weights.dtype}")

    # Check amount of weights matches amount of components

    if weights.shape[0] != n_components:
        raise ValueError(
            f"The number of weights ({weights.shape[0]}) \
            does not match the number of components ({n_components})"
        )

    # Check if all weights are positive
    if (weights < 0).any():
        raise ValueError("All weights must be positive values.")

    if torch.all(weights == 0):
        raise ValueError("At least one weight must be positive.")

    weight_sum = weights.sum()
    if not torch.isclose(weight_sum, torch.tensor(1.0), atol=EPSILON):
        new_weights = weights / weight_sum
        return new_weights
    else:
        return weights


def _check_means(mean: torch.Tensor, n_components: int, n_dimensions: int):
    """
    A function to check the means for valid data.
    Args:
        mean: A 2D-Tensor with all the means of the components
        n_components: the number of components
        n_dimensions: the number of dimensions

    Returns:
        None

    """
    # Check if mean is from datatype Tensor and NAN, INF:
    _assert_finite(mean, "mean")

    # Check if mean is a 2D-Tensor
    if not mean.ndim == 2:
        raise ValueError("mean is not a 2D-Tensor!")

    # Check if axis 1 of Tensor has n_components entries
    if not mean.shape[0] == n_components:
        raise ValueError("axis 1 of mean does not have n_component entries!")

    # Check if axis 2 of Tensor has n_dimension entries
    if not mean.shape[1] == n_dimensions:
        raise ValueError("axis 2 of mean does not have n_dimension entries!")

    # Check if all entries of mean are datatype float
    if not mean.is_floating_point():
        raise TypeError("mean is not of datatype float")


def _check_covariance(covariance: torch.Tensor, n_components: int, n_dimensions: int):
    """
    A function to check entries of the covariance matrix.
    Args:
        covariance: the covariance matrix
        n_components: number of gauss
        n_dimensions: dimensional count

    Returns:
        None

    """
    # Check if covariance is from datatype Tensor and NAN, INF:
    _assert_finite(covariance, "covariance")

    # Check if covariance is 3D-Tensor
    if not covariance.ndim == 3:
        raise ValueError("covariance matrix is not 3D!")
    # Check if axis 1 has n_components entries
    if not covariance.shape[0] == n_components:
        raise ValueError("axis 1 of covariance matrix does not have n_components entries!")
    # Check if axis 2 has n_dimensions entries
    if not covariance.shape[1] == n_dimensions:
        raise ValueError("axis 2 of covariance matrix does not have n_dimensions entries!")
    # Check if axis 3 has n_dimensions entries
    if not covariance.shape[2] == n_dimensions:
        raise ValueError("axis 3 of covariance matrix does not have n_dimensions entries!")
    # Check if all values are floats
    if not covariance.is_floating_point():
        raise TypeError("covariance is not of datatype float!")
    # Loop check if covariance is symmetric for number of n_components
    covariance_transposed = covariance.transpose(2, 1)
    if not torch.allclose(covariance, covariance_transposed):
        raise ValueError("covariance matrix is not symmetric!")

    # Check pd with cholesky (torch.linalg.cholesky
    # (see implementation if it really checks pd instead of psd)
    try:
        torch.linalg.cholesky(covariance)
    except RuntimeError as err:
        # Check if error was caused by noice
        # Using the smallest machine error
        eps = torch.finfo(covariance.dtype).eps
        # Checking eigenvalue decomposition
        eigenvalues = torch.linalg.eigh(covariance)[0]

        min_eig = eigenvalues.min()

        # Check against the machine error
        if min_eig < -eps:
            raise ValueError(f"covariance matrix is not PD. Found negative eigenvalue: {min_eig}") from err
        elif min_eig <= eps:
            raise ValueError(f"covariance matrix is singular (eigenvalue near 0): {min_eig}") from err


def _check_data_points(data_points: torch.Tensor, n_dimensions: int):
    """
    A function to check the data_points for valid data.
    Args:
        data_points: A 2D-Tensor with all the means of the components
        n_dimensions: the number of dimensions

    Returns:
        None
    """
    # Check if mean is from datatype Tensor (and not NAN or INF):
    _assert_finite(data_points, "data_points")

    # Check if mean is a 2D-Tensor
    if not data_points.ndim == 2:
        raise ValueError("data_points is not a 2D-Tensor!")

    # Check if axis 2 of Tensor has n_dimension entries
    if not data_points.shape[1] == n_dimensions:
        raise ValueError("axis 2 of data_points does not have n_dimension entries!")

    # Check if all entries of mean are datatype float
    if not data_points.is_floating_point():
        raise TypeError("data_points is not of datatype float")


def _check_datatype(var: int, variable_name: str):
    """
    helper function to check constructor parameters of type int for valid content
    Args:
        var: the variable that will be checked
        variable_name: the name of the variable for the error message.

    Returns:
        None
    """
    # Check if var is of dtype int
    if not isinstance(var, int):
        raise TypeError(f"{variable_name} is not of datatype int!")
    # var cant be inf or NaN now


def _assert_finite(t: torch.Tensor, variable_name: str) -> None:
    """
    Ensure that the given tensor does not contain NaN or infinite values.

    Raises
    ------
    ValueError
        If any element is NaN or +/-inf.
    """
    if not torch.is_tensor(t):
        raise TypeError(f"{variable_name} must be a torch.Tensor, got {type(t)} instead.")

    if torch.isnan(t).any():
        raise ValueError(f"{variable_name} contains NaN values.")
    if torch.isinf(t).any():
        raise ValueError(f"{variable_name} contains infinite values.")


class GaussianMixture:
    """Gaussian Mixture.

    Representation of a Gaussian mixture model probability distribution.
    This class allows to estimate the parameters of a Gaussian mixture
    distribution.

    Parameters
    ----------
    n_components : int, default=1
        The number of mixture components.

    n_dimensions : int, default=1
    The number of dimensions of each gaussian.

    weights_init : (torch.Tensor) a 1D-Tensor containing the weights as floats, default=None
        The user-provided initial weights.
        If it is None, weights are initialized using the `_initialize_parameters` method.

    means_init : 2D-Tensor with all the means of the components, default=None
        The user-provided initial means,
        If it is None, means are initialized using the `_initialize_parameters` method.

    verbose : bool, default=false
        Enable verbose output. If yes then it prints the current
        initialization and each iteration step(also the log probability and the time needed
        for each step). If false no output will be printed

    verbose_interval : int, default=10
        Number of iteration done before the next print.

    Examples
    --------
    #TODO add examples
    """

    def __init__(
        self,
        n_components: int,
        n_dimensions: int,
        covariance_init: torch.Tensor | None,
        weights_init: torch.Tensor | None,
        means_init: torch.Tensor | None,
        random_state: Optional[int],
        verbose: bool,
        verbose_interval: int,
        device: str = "device",
    ) -> None:

        self.device = device
        self.n_components = n_components
        self.n_dimensions = n_dimensions
        self.covariance = covariance_init
        self.weights = weights_init
        self.means = means_init
        self.random_state = random_state

        self.verbose = verbose
        self.verbose_interval = verbose_interval

        # Count for fitting loop
        self.data_points_gpu = None

        self.k_count = 5
        self.em_count = 20
        self.log_likelihood = 0
        self.d_fitting = False
        self.log_fitting = False

        self.copy_stream = None
        self.logged_weights: list[torch.Tensor] = []
        self.logged_means: list[torch.Tensor] = []
        self.logged_covariance: list[torch.Tensor] = []

        self._initialize_parameters()

        # Check variable content
        # check_parameters (at create-time check all parameters)
        self._check_parameters()

    @classmethod
    def from_default(cls):
        # default values for default constructor
        n_comp = 1
        n_dim = 1

        # 1. Covariance: identity matrix (dim 1 simply [[1.0]])
        # We have n_components, in Shape (n_comp, n_dim, n_dim) -> (1, 1, 1)
        covs = torch.eye(n_dim).unsqueeze(0)

        # 2. weights have to be one because there's just one component
        weights = torch.tensor([1.0])

        # 3. put means to 0
        means = torch.zeros(n_comp, n_dim)

        return cls(
            n_components=n_comp,
            n_dimensions=n_dim,
            covariance_init=covs,
            weights_init=weights,
            means_init=means,
            random_state=42,
            verbose=False,
            verbose_interval=10,
        )

    @classmethod
    def from_user(
        cls,
        n_components: int,
        n_dimensions: int,
        weights_init: torch.Tensor,
        means_init: torch.Tensor,
        covariances_init: torch.Tensor,
    ):

        return cls(n_components, n_dimensions, covariances_init, weights_init, means_init, None, False, 0)

    @classmethod
    def from_random(cls, random_state: int, max_components=100, max_dimensions=100):
        """
        random_state : int, RandomState instance or None, default=None
            Controls the random seed given to the method chosen to initialize the
            parameters (see '_initialize_parameters').
            In addition, it controls the generation of random samples from the
            fitted distribution (see the method 'sample').
            Pass an int for reproducible output across multiple function calls.
        """
        if isinstance(random_state, int):
            torch.manual_seed(random_state)

        # random n_components
        n_components = torch.randint(low=1, high=max_components, size=(1,)).item()

        # random n_dimension
        n_dimensions = torch.randint(low=1, high=max_dimensions, size=(1,)).item()

        # random weights amount = n_components
        rand_weights = softmax(torch.randn(n_components), dim=0)

        # Create random matrix
        rand_matrix = torch.randn(n_components, n_dimensions, n_dimensions)

        # Take lower triangle of rand_matrix
        l_triangular = torch.tril(rand_matrix)

        # Make lower_triangular pd
        l_triangular.diagonal(dim1=-2, dim2=-1).exp_()

        rand_covariance = l_triangular @ l_triangular.transpose(-1, -2)

        # random means: 2D Tensor. axe 1 = n_components axe 2 = n_dimensional
        rand_means = torch.randn(n_components, n_dimensions) * 10

        return cls(n_components, n_dimensions, rand_covariance, rand_weights, rand_means, random_state, False, 0)

    def _initialize_parameters(self):
        """
        Initializes missing parameters and device settings.

        This method sets up the initial state of gmm if parameters were not provided by the user:

        weights: defaults to a uniform distribution (1/n_components).
        device: automatically detects the available accelerator (CUDA)
           or defaults to CPU if not specified.
        covariances: defaults to identity matrices for each component.
        means: defaults to zero vectors for each component.
        random state: sets the torch manual seed if an integer is provided.
        """
        if self.weights is None:
            if self.n_components <= 0:
                raise ValueError("n_components must be positive to initialize weights.")
            self.weights = torch.full(
                (self.n_components,),
                1.0 / self.n_components,
                dtype=torch.float32,
            )
        if self.device is None or self.device == "device":
            self.device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"
        else:
            self.device = "cpu"

        if self.device == "cuda":
            self.copy_stream = torch.cuda.Stream()

        # Initialize covariance if missing: identity matrix per component
        if self.covariance is None:
            if self.n_components <= 0 or self.n_dimensions <= 0:
                raise ValueError("n_components and n_dimensions must be positive to initialize covariance.")
            # diag_embed creates a batch of identity matrices:
            # shape: (n_components, n_dimensions, n_dimensions)
            self.covariance = torch.diag_embed(torch.ones(self.n_components, self.n_dimensions, dtype=torch.float32))

        # Initialize means if missing
        if self.means is None:
            if self.n_components <= 0 or self.n_dimensions <= 0:
                raise ValueError("n_components and n_dimensions must be positive to initialize means.")
            self.means = torch.zeros((self.n_components, self.n_dimensions), dtype=torch.float32)

        # Initialize the random seed
        if isinstance(self.random_state, int):
            torch.manual_seed(self.random_state)

    def _check_parameters(self):
        """
        subroutine to check all parameters for GMM
        Returns:
            None
        """
        _check_datatype(self.n_components, "n_components")
        _check_datatype(self.n_dimensions, "n_dimensions")
        self.weights = _check_weights(self.weights, self.n_components)
        _check_covariance(self.covariance, self.n_components, self.n_dimensions)
        _check_means(self.means, self.n_components, self.n_dimensions)

    def fit(self, dynamic_fitting=False, log_fitting=False):
        """
        Creates gaussian distributions for given datapoints.

        Overwrites covariance, means and weights
        """
        self.d_fitting = dynamic_fitting
        self.log_fitting = log_fitting
        # variables on V-RAM:
        # data_points
        # means
        # covariance
        # weights

        # Check data_points
        _check_data_points(self.data_points_gpu, self.n_dimensions)

        # create copy stream to save best gmm

        if not dynamic_fitting:
            self._knn_means()
            self.weights = self.weights.to(self.device)
            self._em()
        else:
            self.n_components = 1
            best_gmm_bic = torch.inf

            while dynamic_fitting:
                self._knn_means()
                self.weights = torch.ones(self.n_components, device=self.device)
                _check_weights(self.weights, self.n_components)
                gmm_bic = self._em()

                if gmm_bic > best_gmm_bic or self.n_components >= 20:
                    break
                else:
                    best_gmm_bic = gmm_bic
                    self.n_components += 1

        self.data_points_gpu = self.data_points_gpu.to("cpu")
        self.means = self.means.to("cpu")
        self.covariance = self.covariance.to("cpu")
        self.weights = self.weights.to("cpu")
        if self.device == "cuda":
            self.copy_stream.synchronize()

    def _knn_means(self):
        """
        Runs the k-Means algorithm to initialize the cluster means.

        This method serves as a heuristic initialization step. It starts with
        randomly initialized centroids and iteratively refines their positions
        by minimizing the Euclidean distance to the data points over a fixed
        number of iterations ('self.k_count').

        The resulting centroids are stored in 'self.means' to be used as
        starting parameters for the Gaussian Mixture Model.
        """
        self.means = torch.randn(self.n_components, self.n_dimensions, device=self.device) * 10

        for _i in range(self.k_count):
            distances = torch.cdist(self.data_points_gpu, self.means)

            # index of the smallest distance as parameter
            # Points have been assigned a cluster
            self._new_means(torch.argmin(distances, dim=1))

    def _new_means(self, assigned_mask: torch.Tensor):
        """
        Updates the cluster centroids based on the assigned data points.

        This performs the 'maximization' step of K-Means. It aggregates all data
        points assigned to a specific cluster and calculates their new mean center.

        It utilizes vectorized operations ('index_add_') for efficiency on the GPU
        and includes a safeguard against division-by-zero errors for empty clusters.

        Args:
            assigned_mask (torch.Tensor): A tensor containing the cluster index
                (0 to n_components-1) for each data point.
        """
        # If point had min dist to means[0] then in assigned_mask there will be 0
        new_means = torch.zeros_like(self.means)

        # Add up all coordinates of the assigned data_points
        new_means.index_add_(0, assigned_mask, self.data_points_gpu)

        points_count = torch.bincount(assigned_mask, minlength=self.n_components).float()
        # If component has 0 points we get NaN error. Therefor set it to min 1.0
        safe_count = torch.clamp(points_count, min=1.0)

        new_means /= safe_count.unsqueeze(1)

        self.means = new_means

    def _em(self):
        """
        Docstring for _em
        """
        self.covariance = torch.diag_embed(torch.ones(self.n_components, self.n_dimensions, device=self.device))

        i = 0
        max_iter = 0
        last_bic = torch.inf
        while True:
            self._m_step(self._e_step())
            if self.log_fitting:
                self._save_fitting_log()
            i += 1
            max_iter += 1
            # Escape statement for static fitting
            if not self.d_fitting and i >= self.em_count:
                return 0

            # Dynamic check BIC is it good ? stop | keep on going
            if self.d_fitting:
                this_bic = self._calc_bic()
                if abs(this_bic - last_bic) < 1e-4:
                    return this_bic
                else:
                    if max_iter >= 1000:
                        return this_bic
                    last_bic = this_bic

    def _e_step(self):
        """
        Calculates responsibility of each data point
        """
        log_probs_points = torch.zeros(self.data_points_gpu.shape[0], self.n_components, device=self.device)
        # We work with log because of numeric instability

        # Calc. for all clusters the log_likelihood of each point
        for k in range(self.n_components):
            distribution = torch.distributions.MultivariateNormal(
                loc=self.means[k], covariance_matrix=self.covariance[k]
            )
            # Calc the probabilities for all points for all components
            log_probs_points[:, k] = distribution.log_prob(self.data_points_gpu)
            # Excel style sort of probabilities. Clusters on the horizontal axis
            # and data_points on the vertical

        log_weights = torch.log(self.weights).unsqueeze(0)
        # Normalizing the responsibilities
        weighted_log_prob_points = log_probs_points + log_weights

        # sum weighted_log_prob_points for BIC
        likelihood = torch.logsumexp(weighted_log_prob_points, dim=1, keepdim=True)
        self.log_likelihood = 2 * torch.sum(likelihood)

        log_respo = weighted_log_prob_points - likelihood

        # Responsibilities from log format in normal numbers.
        return torch.exp(log_respo)

    def _m_step(self, responsibilities):
        """
        Calculation of sum of all weights
        """
        clusters_prob_sum = responsibilities.sum(dim=0)
        # Calc. new all the new weights
        self.weights = clusters_prob_sum / self.data_points_gpu.shape[0]

        # Calc. all the new means
        weighted_sums = torch.matmul(responsibilities.T, self.data_points_gpu)
        self.means = weighted_sums / (clusters_prob_sum.unsqueeze(1) + EPSILON)

        # Calc. for all clusters the new covariance matrix
        for k in range(self.n_components):
            diff = self.data_points_gpu - self.means[k]

            # We use a sqrt trick to vectorize the operation, to take full advantage of the parallelism of the gpu
            # We also gain numerical stability with this trick
            sqrt_resp = torch.sqrt(responsibilities[:, k].unsqueeze(1))

            weighted_diffs = diff * sqrt_resp

            cov_matrix = torch.matmul(weighted_diffs.T, weighted_diffs)

            cov_matrix /= clusters_prob_sum[k] + EPSILON

            eps = EPSILON * torch.eye(self.data_points_gpu.shape[1], device=self.device)
            self.covariance[k] = cov_matrix + eps

    def load_data_points(self, data_points):
        self.data_points_gpu = data_points.to(self.device)

    def generate_samples(self, n_samples=1, return_indices: bool = False):
        """
        Generates random samples from the fitted Gaussian Mixture Model.

        The generation process works in two steps:
        1. Determines which component k a sample belongs to, based on the distribution defined by
           the mixture weights.
        2. Generates the actual data point from the multivariate Gaussian distribution of the
           selected component k.

        The resulting samples are shuffled to ensure random ordering, as the generation
        process initially groups samples by component.

        Args:
            n_samples (int): The total number of samples to generate.
                Must be a positive integer. Defaults to 1.
            return_indices (bool): If True, the method returns a tuple
                containing the samples and the component indices that generated them.
                Defaults to False.
        """

        if n_samples < 1:
            raise ValueError("Number of samples must be positive")

        self.weights = self.weights.to(self.device)
        self.means = self.means.to(self.device)
        self.covariance = self.covariance.to(self.device)
        sample_indices = torch.multinomial(self.weights, n_samples, replacement=True)

        # counts the amount of samples per component
        n_samples_comp_list = torch.bincount(sample_indices, minlength=self.n_components).tolist()

        all_samples = []

        if not return_indices:
            # genereates the samples for each component
            for k in range(self.n_components):
                n_k = n_samples_comp_list[k]

                if n_k > 0:
                    mean_k = self.means[k, :]
                    cov_k = self.covariance[k, :, :]

                    l_cholesky = torch.linalg.cholesky(cov_k)

                    # generate random normal distributed vectors
                    random_vectors = torch.randn(n_k, self.n_dimensions, dtype=mean_k.dtype, device=mean_k.device)

                    # transform random vectors to fit the gaussian distribution of the sample
                    transformed_vectors = random_vectors @ l_cholesky.T

                    samples_k = mean_k + transformed_vectors

                    all_samples.append(samples_k)

            samples = torch.cat(all_samples, dim=0)

            perm_indices = torch.randperm(n_samples, device=samples.device)
            samples = samples[perm_indices]
            self.weights = self.weights.to("cpu")
            self.means = self.means.to("cpu")
            self.covariance = self.covariance.to("cpu")
            samples = samples.to("cpu")
            return samples

        all_indices = []

        # generates the samples for each component but also keeps track of the indices
        for k in range(self.n_components):
            n_k = int(n_samples_comp_list[k])
            if n_k == 0:
                continue

            mean_k = self.means[k, :]
            cov_k = self.covariance[k, :, :]

            l_cholesky = torch.linalg.cholesky(cov_k)
            random_vectors = torch.randn(n_k, self.n_dimensions, dtype=mean_k.dtype, device=mean_k.device)
            samples_k = mean_k + (random_vectors @ l_cholesky.T)
            all_samples.append(samples_k)

            all_indices.append(torch.full((n_k,), k, device=samples_k.device, dtype=torch.long))

        samples = torch.cat(all_samples, dim=0)
        indices = torch.cat(all_indices, dim=0)

        perm = torch.randperm(n_samples, device=samples.device)
        samples = samples[perm]
        indices = indices[perm]

        # Move back to CPU
        self.weights = self.weights.to("cpu")
        self.means = self.means.to("cpu")
        self.covariance = self.covariance.to("cpu")

        return samples.to("cpu"), indices.to("cpu")

    def expectation_average_of_means(self):
        """
        Calculates the global expected value (overall mean) of the Gaussian Mixture Model.

        This method computes the weighted sum of the means of all components,
        representing the center of mass of the entire distribution.

        Returns
        -------
        torch.Tensor
            A 1D-Tensor of shape (n_dimensions,) containing the global expected mean.
        """
        return self.weights @ self.means

    def marginalization(self, remaining_dimensions):
        """
        Calculates the marginalized GMM given certain dimensions that shall remain from the current GMM instance.

        In a GMM there is no integration needed to marginalize a dimension, since removing certain rows/columns
        from the means and covariance tensor is mathematically identical to performing the integral.

        Args:
            remaining_dimensions(torch.Tensor): A 1D-Tensor containing the dimensions that should persist

        Returns:
            GaussianMixture: marginalized GMM instance

        """
        # check if remaining_dimensions is a tensor
        if not (torch.is_tensor(remaining_dimensions)):
            raise ValueError("remaining_dimensions should be a torch.Tensor")
        # check if remaining dimensions has sane shape and values
        if not (remaining_dimensions.dim() == 1):
            raise ValueError("remaining_dimensions should be a 1D-Tensor")
        if not (1 <= remaining_dimensions.size(0) < self.n_dimensions):
            raise ValueError("remaining_dimensions should contain at least one dimension and less than n_dimensions")
        # check if entries are Integer
        if remaining_dimensions.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64):
            raise ValueError("remaining_dimensions must be an integer tensor (e.g., torch.int64)")
        # check if indices are sane
        if not torch.all((remaining_dimensions >= 0) & (remaining_dimensions < self.n_dimensions)):
            raise ValueError("remaining_dimensions contains out-of-range indices")
        # check for duplicates to preserve covariance PSD properties
        if torch.unique(remaining_dimensions).numel() != remaining_dimensions.numel():
            raise ValueError("remaining_dimensions must not contain duplicate indices")

        new_n_dimensions = remaining_dimensions.size(0)

        # only keeps remaining_dimensions columns
        new_means = self.means[:, remaining_dimensions]

        # keeps components and only those dimensions that match remaining_dimensions
        new_covariances = self.covariance[:, remaining_dimensions][:, :, remaining_dimensions]

        return GaussianMixture.from_user(
            n_components=self.n_components,
            n_dimensions=new_n_dimensions,
            weights_init=self.weights,
            means_init=new_means,
            covariances_init=new_covariances,
        )

    def conditioning(self, given_dimensions, given_values):
        """
        Calculates the conditional Gaussian Mixture Model (GMM) given specific observed values.

        Mathematical Formulation (see "Pattern Recognition and Machine Learning" by Christopher Bishop (2006),
        pages 85f and "Probabilistic Machine Learning: An Introduction" by Kevin P. Murphy (2022), pages 87f):
            -------------------------
            Let A be the indices of the unknown dimensions and B be the indices of the observed dimensions.

            1. New Means (Conditional Mean):
            mu_{A|B} = mu_A + Sigma_{AB} @ Sigma_{BB}^{-1} @ (x_B - mu_B)

            2. New Covariances (Conditional Covariance):
            Sigma_{A|B} = Sigma_{AA} - Sigma_{AB} @ Sigma_{BB}^{-1} @ Sigma_{BA}

            3. New Weights (Bayesian Update):
            w_{new} = softmax(log(w_{old}) + log(N(x_B | mu_B, Sigma_{BB})))

        Args:
            given_dimensions (torch.Tensor): A 1D-Tensor containing the indices of the fixed dimensions (x_B).
            given_values (torch.Tensor): A 1D-Tensor containing the observed values for these dimensions.

        Returns:
                GaussianMixture: A new instance of GaussianMixture representing the distribution
                                over the remaining dimensions (x_A).
        """
        if not (torch.is_tensor(given_dimensions) and torch.is_tensor(given_values)):
            raise ValueError("given_dimensions and given_values for conditioning must be tensors.")

        idx_b = given_dimensions.to(device=self.device, dtype=torch.long)
        vals_b = given_values.to(device=self.device, dtype=self.means.dtype)

        all_indices = torch.arange(self.n_dimensions, device=self.device)
        # creates mask: True for all indices, that are not in given_indices
        mask_keep = ~torch.isin(all_indices, idx_b)

        idx_a = all_indices[mask_keep]  # dimensions we want to keep

        # new means
        mu_a = self.means[:, idx_a]  # Shape: (K, D_new)
        mu_b = self.means[:, idx_b]  # Shape: (K, D_given)

        # sigma_aa: rows of A, columns of A
        sigma_aa = self.covariance[:, idx_a][:, :, idx_a]
        # sigma_bb: rows of B, columns of B
        sigma_bb = self.covariance[:, idx_b][:, :, idx_b]
        # sigma_ab: rows of A, columns of B
        sigma_ab = self.covariance[:, idx_a][:, :, idx_b]
        # sigma_ba: rows of B, columns of A (transposed of sigma_ab)
        sigma_ba = sigma_ab.transpose(1, 2)

        # difference between observation and mean B
        mean_diff = (vals_b - mu_b).unsqueeze(-1)

        # Sigma_BB * X = Sigma_BA  (which solves Sigma_BB^-1 * Sigma_BA)
        try:
            # calculates Sigma_BB^-1 * Sigma_BA
            bb_inv_ba = torch.linalg.solve(sigma_bb, sigma_ba)
            # calculates Sigma_BB^-1 * (x_b - mu_b)
            bb_inv_diff = torch.linalg.solve(sigma_bb, mean_diff)
        except RuntimeError:
            # fallback if singular
            sigma_bb_pinv = torch.linalg.pinv(sigma_bb)
            bb_inv_ba = sigma_bb_pinv @ sigma_ba
            bb_inv_diff = sigma_bb_pinv @ mean_diff

        means_shift = sigma_ab @ bb_inv_diff
        new_means = mu_a + means_shift.squeeze(-1)

        # Sigma_AA - Sigma_AB * (Sigma_BB^-1 * Sigma_BA)
        subtrahend = sigma_ab @ bb_inv_ba
        new_covs = sigma_aa - subtrahend

        # update weights with bayes rule
        # create normal distribution with new mean and covariance matrix
        dist_b = torch.distributions.MultivariateNormal(loc=mu_b, covariance_matrix=sigma_bb)

        # we calculate the log-likelihood of the given values (for the fixed dimensions)
        log_probs = dist_b.log_prob(vals_b)

        # update log-weights: log(w_new) ~ log(w_old) + log(likelihood) (we us log bc of numeric stability)
        new_log_weights = torch.log(self.weights + EPSILON) + log_probs

        # normalize new weights to 1
        new_weights = torch.softmax(new_log_weights, dim=0)

        new_n_dim = int(idx_a.shape[0])

        return GaussianMixture.from_user(
            n_components=self.n_components,
            n_dimensions=new_n_dim,
            weights_init=new_weights,
            means_init=new_means,
            covariances_init=new_covs,
        )

    def _calc_bic(self):
        """
        Computes the Bayesian Information Criterion (BIC) for the current model.

        The BIC is a criterion for model selection among a finite set of models.
        It introduces a penalty term for the number of parameters in the model
        to prevent overfitting. The model with the lowest BIC is generally preferred.

        Returns:
            torch.Tensor: The calculated BIC score (scalar).
        """
        return self._calc_overfitting() - self.log_likelihood

    def _calc_overfitting(self):
        """
        Calculates the penalty term representing model complexity.

        This method counts the total number of free parameters (k) in the GMM
        and scales it by the natural logarithm of the sample size (n).

        Returns:
            torch.Tensor: The complexity penalty term.
        """
        k_params = (
            self.n_components * self.n_dimensions
            + self.n_components * ((self.n_dimensions * (self.n_dimensions + 1)) / 2)
            + (self.n_components - 1)
        )
        return k_params * math.log(self.data_points_gpu.shape[0])

    def _save_fitting_log(self):
        # change to copy stream

        if self.device == "cuda":
            with torch.cuda.stream(self.copy_stream):
                self.copy_stream.wait_stream(torch.cuda.current_stream())

                self.logged_weights.append(self.weights.detach().to(device="cpu", non_blocking=True))
                self.logged_means.append(self.means.detach().to(device="cpu", non_blocking=True))
                self.logged_covariance.append(self.covariance.detach().to(device="cpu", non_blocking=True))
        else:
            self.logged_weights.append(self.weights.detach().to(device="cpu", non_blocking=True))
            self.logged_means.append(self.means.detach().to(device="cpu", non_blocking=True))
            self.logged_covariance.append(self.covariance.detach().to(device="cpu", non_blocking=True))
