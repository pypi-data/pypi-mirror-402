import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from scipy.stats import norm
import random
import warnings
from typing import List, Callable, Optional, Dict

def non_dominated_indices(acq_matrix: np.ndarray) -> List[int]:
    r"""
    Identify Pareto-optimal (non-dominated) candidates in a multi-objective acquisition matrix.

    Given an acquisition matrix \(A \in \mathbb{R}^{N \times M}\), where each row corresponds to 
    a candidate and each column to an objective to be maximized, this function returns the indices 
    of non-dominated candidates (the Pareto front).

    A row \(j\) dominates row \(i\) if

    .. math::
       A_{j,:} \ge A_{i,:} \quad \text{(elementwise)}\\
       \text{and}\\
       A_{j,:} > A_{i,:} \quad \text{in at least one component.}

    Parameters
    ----------
    acq_matrix : np.ndarray, shape (N, M)
        Multi-objective acquisition values for N candidates and M objectives.

    Returns
    -------
    List[int]
        Indices of Pareto-optimal candidates.
    """
    n_points = acq_matrix.shape[0]
    dominated = np.zeros(n_points, dtype=bool)

    for i in range(n_points):
        if dominated[i]:
            continue
        for j in range(n_points):
            if i == j or dominated[i]:
                continue
            # Check if candidate j dominates candidate i
            # For maximization: j >= i in all dims, and j > i in at least one
            better_equal = np.all(acq_matrix[j] >= acq_matrix[i])
            strictly_better = np.any(acq_matrix[j] > acq_matrix[i])
            if better_equal and strictly_better:
                dominated[i] = True
                break

    return [idx for idx in range(n_points) if not dominated[idx]]

# ------------------------------------------------------------------
# Modified BayesianOptimization Class with Constraints
# ------------------------------------------------------------------
class BayesianOptimization:
    r"""
    Bayesian Optimization framework supporting multi-objective acquisition,
    constraints, discrete sampling, and Boltzmann-based strategies.

    The optimizer maintains one Gaussian Process surrogate per objective and uses
    acquisition functions to propose new candidate points.

    Attributes
    ----------
    surrogate_models : List[GaussianProcessRegressor]
        One GP model per objective.
    bounds : np.ndarray, shape (n_features, 2)
        Search space bounds for each feature.
    discrete_levels : Optional[List[np.ndarray]]
        Allowed discrete values for features (if any).
    constraints : List[Callable[[np.ndarray], bool]]
        Feature constraint functions.
    logic : str
        Constraint logic: 'all' or 'any'.
    n_objectives : int
        Number of optimization objectives.
    n_candidates : int
        Number of candidates to recommend.
    temperature : Optional[float]
        Temperature parameter for Boltzmann acquisition.
    stall_threshold : int
        Number of generations without improvement to declare convergence.
    information_driven : bool
        Whether to track information-driven novelty for convergence.
    """
    def __init__(self,
                 surrogate_models=None,
                 active_model_key='gp',
                 gp_alpha=1e-1,
                 weights=None,
                 bounds=None,
                 n_candidates:int=1,
                 n_objectives: int=1,
                 constraints: Optional[List] = None,
                 discrete_levels: Optional[List[np.ndarray]] = None, 
                 logic: str = "all",
                 temperature:float = None,
                 n_restarts_optimizer: int = 0,
                 fit_frequency: int = 1,
                 training_subsample: Optional[int] = 100,
                 random_state: int = 42):
        r"""
        Initialize BayesianOptimization instance.

        Builds default Gaussian Process surrogates if none are provided.

        Parameters
        ----------
        surrogate_models : dict, optional
            Predefined surrogate models keyed by name.
        active_model_key : str
            Key of the active surrogate in surrogate_models.
        gp_alpha : float
            Regularization parameter for GP noise level.
        weights : np.ndarray, optional
            Weights for scalarization in multi-objective to single-objective.
        bounds : np.ndarray, shape (n_features, 2)
            Search space bounds.
        n_candidates : int
            Number of candidates to propose per iteration.
        n_objectives : int
            Number of objectives to optimize.
        constraints : List[Callable], optional
            List of functions `f(x)->bool` to enforce feasible region.
        discrete_levels : List[np.ndarray], optional
            Discrete allowable values per feature.
        logic : {'all','any'}
            Constraint aggregation logic.
        temperature : float, optional
            Temperature for Boltzmann acquisition.
        n_restarts_optimizer : int, default=0
            Number of restarts of the optimizer for finding the kernel's parameters.
        fit_frequency : int, default=1
            Frequency of fitting the GP models (every k generations).
        training_subsample : int, optional
            Maximum number of training points to use. If exceeded, a subset (best + diverse) is used.
        random_state : int
            Seed for reproducibility.
        """
        np.random.seed(random_state)
        random.seed(random_state)

        valid_modes = ["all", "any"]
        if logic not in valid_modes:
            raise ValueError(
                f"Invalid logic='{logic}'. Must be one of {valid_modes}."
            )
        self.logic = logic
        self.n_objectives = n_objectives
        self.bounds = bounds
        self.discrete_levels = discrete_levels
        self.constraints = constraints if constraints else []

        self.active_model_key = active_model_key
        self.weights = weights
        self._trained_objective_values = None
        self.n_candidates = n_candidates
        self.n_candidates = n_candidates
        self.temperature = temperature
        self.n_restarts_optimizer = n_restarts_optimizer
        self.fit_frequency = fit_frequency
        self.training_subsample = training_subsample
        self.fit_count = 0

        # 1. If no surrogate models are provided, create a default Gaussian Process.
        # Build a dictionary of GPs, one per objective: "obj0", "obj1", ...
        self.surrogate_models: list[str, GaussianProcessRegressor] = []
        for i in range(n_objectives):
            kernel = (ConstantKernel(1.0, (1e-3, 1e3)) *
                      Matern(nu=2.5, length_scale=10.0, length_scale_bounds=(1e-2, 1e3)) +
                      WhiteKernel(noise_level=1e-6, noise_level_bounds=(1e-8, 1e-1)))
            gp = GaussianProcessRegressor(kernel=kernel,
                                          alpha=gp_alpha,
                                          normalize_y=True,
                                          n_restarts_optimizer=self.n_restarts_optimizer,
                                          random_state=random_state)
            self.surrogate_models.append(gp)



    def _aggregate_objectives(self, objectives: np.ndarray) -> np.ndarray:
        r"""
        Aggregate multi-objective outputs into a scalar score.

        Uses weighted sum or arithmetic mean:
        .. math::
           s = \begin{cases}
             \sum_i w_i \; o_i, & \text{if } w\text{ provided},\\
             \frac{1}{M} \sum_i o_i, & \text{otherwise.}
           \end{cases}

        Parameters
        ----------
        objectives : np.ndarray, shape (N, M) or (N,)
            Multi-objective values per sample.

        Returns
        -------
        np.ndarray
            Scalarized objective of shape (N,).
        """
        # same as your original code
        if objectives.ndim == 1:
            return objectives
        n_obj = objectives.shape[1]
        if self.weights is None:
            return np.mean(objectives, axis=1)
        else:
            if len(self.weights) != n_obj:
                raise ValueError(f"Mismatch: 'weights' length {len(self.weights)} != # of objectives {n_obj}.")
            return objectives @ self.weights

    def _subsample_training_data(self, X: np.ndarray, Y: np.ndarray, pool_limit: int = 10000):
        """
        Subsample the training data to keep:
         - Top 50% points with the lowest objective values (promising).
         - Remaining 50% points that are most diverse (farthest from the promising set).
        
        Optimized for large datasets:
         - If remaining diversity pool > pool_limit, we randomly downsample it first.
         - Uses incremental distance updates to avoid O(N*K) full matrix re-computation.
        """
        if self.training_subsample is None or len(X) <= self.training_subsample:
            return X, Y

        n_keep = self.training_subsample
        n_promising = n_keep // 2
        n_diverse = n_keep - n_promising

        # 1. Select Promising (lowest aggregated objective)
        if self.n_objectives > 1:
            scores = self._aggregate_objectives(Y)
        else:
            scores = Y.flatten()

        sorted_indices = np.argsort(scores)
        promising_indices = sorted_indices[:n_promising]

        # 2. Select Diverse from the remainder
        remaining_indices = sorted_indices[n_promising:]
        
        # Optimization: If pool is too large, randomly sample a subset
        if len(remaining_indices) > pool_limit:
            # We shuffle to pick random 'pool_limit' candidates
            rng = np.random.default_rng() 
            # Note: keeping stable indices map
            # We pick indices relative to 'remaining_indices' array
            subset_local_indices = rng.choice(len(remaining_indices), size=pool_limit, replace=False)
            pool_indices = remaining_indices[subset_local_indices]
        else:
            pool_indices = remaining_indices

        if n_diverse > 0 and len(pool_indices) > 0:
            selected_diverse = []
            
            # Diversity works by finding points in 'pool_indices' that are far from 'current_selected'
            # current_selected starts as promising_indices
            
            # Coordinates
            pool_coords = X[pool_indices]
            selected_coords = X[promising_indices]
            
            # Initialize min_dists: distance from each pool point to the NEAREST point in the promising set
            from scipy.spatial.distance import cdist
            
            # Chunking cdist if selected_coords is huge could be needed, but usually n_promising is small (e.g. <1000)
            # If n_promising is large, this step is still expensive O(Pool * Promising)
            # But usually training_subsample is small (e.g. 500-1000?)
            
            dists_initial = cdist(pool_coords, selected_coords)
            
            # Minimal distance to ANY promising point
            if dists_initial.shape[1] > 0:
                min_dists = np.min(dists_initial, axis=1)
            else:
                # If no promising points (edge case), dist is infinite
                min_dists = np.full(len(pool_indices), np.inf)

            # Greedy Selection Loop
            for _ in range(n_diverse):
                # Find point with largest minimum distance (MaxMin)
                best_local_idx = np.argmax(min_dists)
                best_global_idx = pool_indices[best_local_idx]
                
                selected_diverse.append(best_global_idx)
                
                # New point added to selection
                new_pt = pool_coords[best_local_idx:best_local_idx+1]
                
                # Update min_dists: compare current min_dists with dists to the NEW point
                new_dists = cdist(pool_coords, new_pt).flatten()
                min_dists = np.minimum(min_dists, new_dists)
                
                # We effectively "remove" the selected point by making its distance -1 (or just ignore it)
                # Setting it to -1 ensures it won't be max again (since dists >= 0)
                min_dists[best_local_idx] = -1.0

            final_indices = np.concatenate([promising_indices, np.array(selected_diverse)]).astype(int)
        else:
            final_indices = promising_indices

        return X[final_indices], Y[final_indices]

    def fit(self, X: np.ndarray, Y: np.ndarray):
        """
        Fit each GP to its respective objective column.
        
        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
        Y : np.ndarray, shape (n_samples, n_objectives)

        Raises
        ------
        ValueError
            If features or objectives have incompatible shapes or dimensions.
        """
        if X.ndim!=2:
            raise ValueError("X must be 2D: (n_samples, n_features).")
        if Y.ndim==1:
            # e.g. single objective as (n_samples,)
            Y = Y.reshape(-1,1)
        if Y.shape[1]!= self.n_objectives:
            raise ValueError(f"Y has {Y.shape[1]} objectives, but n_objectives={self.n_objectives}.")
        
        # Check fit frequency
        self.fit_count += 1
        
        # We should only skip fit if we have fitted at least once!
        # Assuming if self.X_train exists, we have fitted before.
        # But wait, User might want to enforce fit on first call (fit_count=1).
        if (self.fit_count - 1) % self.fit_frequency != 0:
            # We skip fitting, BUT we must ensure the model has been fitted at least once.
            # If the user supplies models pre-fitted, good.
            # If not, and this is fit_count > 1, we are fine assuming fit_count 1 did it.
            # If fit_count == 1, (1-1)%k == 0, so we always fit on first call.
            return

        # Subsample if needed
        X_train_final, Y_train_final = self._subsample_training_data(X, Y)

        self.X_train = X_train_final
        self.Y_train = Y_train_final

        for i, model in enumerate(self.surrogate_models):
            model.fit(X_train_final, Y_train_final[:, i])

    def _predict(self, X: np.ndarray, objective_idx: int ):
        """
        Predict mean and standard deviation of the objective at the given features.
        
        Parameters
        ----------
        X : np.ndarray
            Shape (n_points, n_features).
        objective_idx

        Returns
        -------
        tuple of np.ndarray
            (mean, std) each of shape (n_points,).
        
        Raises
        ------
        NotImplementedError
            If the active surrogate model does not support uncertainty estimation.
        """
        model = self.surrogate_models[objective_idx]
        try:
            mean, std = model.predict(X, return_std=True)
        except TypeError:
            # e.g. for RandomForestRegressor
            if hasattr(model, "estimators_"):
                predictions = np.array([est.predict(X) for est in model.estimators_])
                mean = np.mean(predictions, axis=0)
                std = np.std(predictions, axis=0)
            else:
                raise NotImplementedError(
                    "The active surrogate model does not support uncertainty estimation."
                )
        return mean, std
    
    def validate(self, features: np.ndarray) -> bool:
        """
        Checks whether the provided feature vector satisfies
        the constraints according to the specified logic.
        
        Returns
        -------
        bool
            True if constraints pass, False otherwise.
        """
        if self.logic == "all":
            return all(constraint(features) for constraint in self.constraints)
        elif self.logic == "any":
            return any(constraint(features) for constraint in self.constraints)
        return False

    # ----------------------------------------------------------------
    # Modified multi_objective_acquisition_matrix
    # ----------------------------------------------------------------
    def multi_objective_acquisition_matrix(self,
                                           X: np.ndarray,
                                           T: float=1.0,
                                           T0: float=0.5,
                                           k: float=10.0) -> np.ndarray:
        """
        Compute an M-dimensional "Boltzmann-like" acquisition for each candidate in X,
        where M = number of objectives. We treat each objective separately,
        then store them in columns.

        For each objective:
          - Predict mean, std
          - min-max normalize them
          - combine (1-mean_norm) + (std_norm) with logistic weighting
          - fill into the corresponding column

        Returns
        -------
        acq_matrix : np.ndarray of shape (X.shape[0], self.n_objectives)
        """
        n_candidates = X.shape[0]
        M = self.n_objectives
        acq_matrix = np.zeros((n_candidates, M), dtype=float)

        for obj_idx in range(M):
            mean, std = self._predict(X, obj_idx)
            min_m, max_m = mean.min(), mean.max()
            min_s, max_s = std.min(), std.max()

            rng_m = max_m - min_m if max_m>min_m else 1e-9
            rng_s = max_s - min_s if max_s>min_s else 1e-9

            mean_norm = (mean - min_m)/rng_m
            std_norm  = (std  - min_s)/rng_s

            # logistic factor
            sig_T = 1.0/(1.0 + np.exp(-k*(T-T0)))
            C_T = 1.0 - sig_T
            B_T = sig_T

            # Minimizing mean => exploitation = (1-mean_norm)
            exploitation = 1.0 - mean_norm
            exploration  = std_norm

            acq = C_T*exploitation + B_T*exploration
            acq_matrix[:, obj_idx] = acq

        return acq_matrix

    def generate(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        *,
        n_candidates: int = 1,
        candidate_multiplier: int = 10,
        T: float = 1.0,
        T0: float = 0.5,
        k: float = 10.0,
        selection_mode: str = "pareto",
        min_distance: float = 0.0,
        discrete_design: bool = True,
        avoid_repetitions: bool = True
        ) -> np.ndarray:
        """
        Fit the surrogate models on (X, Y) and propose new candidate points.

        This method performs two steps in sequence:
          1. Fit each Gaussian Process on the provided training data.
          2. Use the acquisition and selection machinery to recommend new points.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            Training feature matrix.
        Y : np.ndarray, shape (n_samples, n_objectives) or (n_samples,)
            Training objective values.
        n_candidates : int, optional (default=1)
            Number of final points to return.
        candidate_multiplier : int, optional (default=10)
            Multiplier for initial candidate pool size.
        T : float, optional (default=1.0)
            Temperature for Boltzmann acquisition.
        T0 : float, optional (default=0.5)
            Temperature offset for Boltzmann acquisition.
        k : float, optional (default=10.0)
            Steepness parameter for logistic weighting.
        selection_mode : {'pareto','all-merged'}, optional
            Strategy for selecting among candidates.
        min_distance : float, optional (default=0.0)
            Minimum pairwise Euclidean distance among returned points.
        discrete_design : bool, optional (default=True)
            Whether to sample features discretely.
        avoid_repetitions : bool, optional (default=True)
            Whether to remove duplicate candidates.

        Returns
        -------
        np.ndarray, shape (<= n_candidates, n_features)
            Array of proposed candidate points.

        Raises
        ------
        ValueError
            If any of the parameters are out of range or of incorrect type.
        RuntimeError
            If fitting or candidate recommendation fails.
        """
        # Validate modes and parameters
        valid_modes = {"pareto", "all-merged"}
        if selection_mode not in valid_modes:
            raise ValueError(f"selection_mode must be one of {valid_modes}, got '{selection_mode}'")
        if n_candidates <= 0:
            raise ValueError(f"n_candidates must be positive, got {n_candidates}")
        if candidate_multiplier <= 0:
            raise ValueError(f"candidate_multiplier must be positive, got {candidate_multiplier}")
        if min_distance < 0:
            raise ValueError(f"min_distance must be non-negative, got {min_distance}")

        # Step 1: Fit surrogate models
        try:
            self.fit(X, Y)
        except Exception as e:
            raise RuntimeError("Failed to fit surrogate models") from e
        # Step 2: Recommend new candidates

        try:
            return self.recommend_candidates(
                n_candidates=n_candidates,
                candidate_multiplier=candidate_multiplier,
                T=T,
                T0=T0,
                k=k,
                selection_mode=selection_mode,
                min_distance=min_distance,
                discrete_design=discrete_design,
                avoid_repetitions=avoid_repetitions
            )
        except (ValueError, RuntimeError) as e:
            # propagate known errors
            raise
        except Exception as e:
            # wrap any unexpected failures
            raise RuntimeError("Error during candidate recommendation") from e

    # ----------------------------------------------------------------
    # Modified recommend_candidates to handle constraints & discrete
    # ----------------------------------------------------------------
    def recommend_candidates(
        self,
        n_candidates: int = 1,
        candidate_multiplier: int = 10,
        T: float = 1.0,
        T0: float = 0.5,
        k: float = 10.0,
        selection_mode: str = "pareto",
        min_distance: float = 0.0,
        discrete_design: bool = True,
        avoid_repetitions: bool = True
        ) -> np.ndarray:
        r"""
        Generate and select new candidate points using multi‐objective acquisition,
        constraints, and optional discrete sampling.

        This routine proceeds in five stages:

        1. **Candidate Pool Generation**  
           Create a pool of :math:`N=\text{candidate_multiplier}\times\text{n_candidates}` points
           in the search space, obeying `bounds`, optional `discrete_levels`, etc.

           points in the search space, obeying `bounds`, optional `discrete_levels`, 
           and the user‐supplied constraint functions.

           - If `discrete_design=True` and `discrete_levels` are provided, each feature 
             is sampled from its allowed set via uniform random choice.  
           - If `discrete_design=True` but no `discrete_levels`, integer values are drawn 
             uniformly between each feature’s lower and upper bound.  
           - If `discrete_design=False`, real‐valued features are sampled uniformly.  
           - Invalid points (failing `validate`) are discarded and re-sampled up to a maximum 
             of :math:`100N` attempts.

        2. **Acquisition Evaluation**  
           For each of the :math:`N` candidates 
           :math:`X_{\text{cand}} = \{\,x_i\in\mathbb{R}^d\}_{i=1}^N`, compute an 
           :math:`M`-dimensional acquisition matrix 
           :math:`A\in\mathbb{R}^{N\times M}` via
           ``multi_objective_acquisition_matrix``.  

           Each entry 
           :math:`A_{i,j}` balances exploitation (low predicted mean) and exploration (high predicted uncertainty) using a Boltzmann‐like weighting:
           .. math::

              \sigma_T = \frac{1}{1 + e^{-k\,(T - T_0)}}, 
              \quad
              A_{i,j} = (1-\sigma_T)\,\bigl(1 - \widehat\mu_{i,j}\bigr)
                        + \sigma_T\,\widehat\sigma_{i,j},

           where 
           :math:`\widehat\mu_{i,j}` and :math:`\widehat\sigma_{i,j}` 
           are min–max normalized mean and standard deviation for objective :math:`j`.

        3. **Pareto‐Front Selection**  
           If `selection_mode=="pareto"`, identify the Pareto front of the 
           rows of :math:`A` via `non_dominated_indices(A)`.  Denote the front indices 
           by :math:`\mathcal{P}` and points by :math:`\{\,x_p\}_{p\in\mathcal{P}}`.  

           - **Case A**:  
             If 
             :math:`|\mathcal{P}| = 0` (all points dominated), fall back to “all‐merged” mode.  
           - **Case B**:  
             If 
             :math:`0 < |\mathcal{P}| < n_{\rm candidates}`,  
             include all Pareto points, then fill the remaining slots by ranking the 
             dominated points by their aggregated score
             .. math::
                s_i = \sum_{j=1}^M A_{i,j},
             subject to a minimum pairwise distance constraint 
             :math:`\min_{q\in\mathcal{S}} \|x_i - x_q\| \ge \text{min_distance}.`  
           - **Case C**:  
             If 
             :math:`|\mathcal{P}|\ge n_{\rm candidates}`,  
             greedily select :math:`n_{\rm candidates}` points from 
             :math:`\mathcal{P}` by iteratively adding the next farthest‐apart point to 
             maximize diversity.

        4. **All‐Merged Fallback**  
           If `selection_mode=="all-merged"`, compute the scalarized score
           .. math::
              s_i = \max_{1\le j\le M} A_{i,j},
           sort candidates by :math:`s_i` descending, and select the top 
           :math:`n_{\rm candidates}`, again enforcing the minimum distance constraint 
           between chosen points.

        5. **Return**  
           Returns an array of up to :math:`n_{\rm candidates}` points 
           :math:`\{x^*\}`.  If too few valid points remain after enforcing 
           `min_distance` and `constraints`, a `RuntimeError` is raised.

        Parameters
        ----------
        n_candidates : int
            Number of final points to return.
        candidate_multiplier : int
            Factor multiplying `n_candidates` to form the initial pool size.
        T : float
            Current temperature parameter for the Boltzmann acquisition.
        T0 : float
            Temperature offset in the logistic factor.
        k : float
            Steepness parameter for the Boltzmann weighting.
        selection_mode : {'pareto','all-merged'}
            Selection strategy: Pareto‐front vs. scalarized.
        min_distance : float
            Minimum Euclidean distance between any two returned points.
        discrete_design : bool
            If True, sample features discretely per `discrete_levels` or integer bounds.
        avoid_repetitions : bool
            If True, deduplicate identical candidate vectors in the pool.

        Returns
        -------
        np.ndarray, shape (<=n_candidates, n_features)
            The selected candidate points.

        Raises
        ------
        RuntimeError
            If the pool generation fails to produce at least `n_candidates` valid points.
        ValueError
            If `selection_mode` is unrecognized.
        """
        
        # 0) Infer bounds if none were provided at construction
        if self.bounds is None:
            if not hasattr(self, 'X_train'):
                raise RuntimeError("Cannot infer bounds: no self.bounds and no self.X_train available.")
            mins = self.X_train.min(axis=0)
            maxs = self.X_train.max(axis=0)
            bounds_ = np.stack([mins, maxs], axis=1)
        else:
            bounds_ = self.bounds

        # 1) Candidate pool
        candidate_count = candidate_multiplier*n_candidates
        candidates = []
        used = set()
        max_attempts = candidate_count*100
        attempts=0
        n_features = bounds_.shape[0]

        while len(candidates)<candidate_count and attempts<max_attempts:
            if discrete_design and self.discrete_levels is not None:
                cand = []
                for dim_idx, (low, high) in enumerate(bounds_):
                    possible_vals = self.discrete_levels[dim_idx]
                    valid_vals = possible_vals[(possible_vals>=low)&(possible_vals<=high)]
                    if len(valid_vals)==0:
                        break
                    cand.append(np.random.choice(valid_vals))
                if len(cand)<n_features:
                    attempts+=1
                    continue
                cand = np.array(cand, dtype=float)
            elif discrete_design:
                # integer
                cand = np.array([
                    random.randint(int(low), int(high)) for (low, high) in bounds_
                ], dtype=float)
            else:
                # continuous
                cand = np.array([
                    random.uniform(low, high) for (low, high) in bounds_
                ], dtype=float)

            if self.validate(cand):
                c_tuple = tuple(cand)
                if avoid_repetitions:
                    if c_tuple not in used:
                        used.add(c_tuple)
                        candidates.append(cand)
                else:
                    candidates.append(cand)
            attempts+=1

        if len(candidates)<n_candidates:
            warnings.warn(f"Not enough valid candidates found. Requested {n_candidates}, found {len(candidates)}. Returning available candidates.")
            # raise RuntimeError("Not enough valid candidates found.")

        X_cand = np.array(candidates)

        # 2) Evaluate multi-objective acquisitions => shape (N, M)
        acq_matrix = self.multi_objective_acquisition_matrix(X_cand, T, T0, k)

        # 3) Depending on selection_mode, pick final set
        if selection_mode=="pareto":
            # 3a) get Pareto front
            pareto_idx = non_dominated_indices(acq_matrix)
            pareto_points = X_cand[pareto_idx]
            # if the front is exactly or bigger than n_candidates => pick subset
            if len(pareto_points)==0:
                # corner case: no non-dominated => all are dominated
                # fallback => do aggregator
                selection_mode="all-merged"
            elif len(pareto_points)<n_candidates:
                # pick all from front, then fill remainder from dominated
                chosen = list(pareto_points)

                # 3b) aggregator: sum across M dims for each candidate
                sums = np.sum(acq_matrix, axis=1)
                # remove those in front
                front_set = set(pareto_idx)
                dominated_idx = [i for i in range(len(X_cand)) if i not in front_set]
                # sort dominated by sum descending
                dominated_sorted = sorted(dominated_idx, key=lambda i: sums[i], reverse=True)

                def distance(a,b):
                    return np.linalg.norm(a-b)

                # fill the remainder
                for idx in dominated_sorted:
                    if len(chosen)>=n_candidates:
                        break
                    pt = X_cand[idx]
                    # distance check
                    if min_distance>0:
                        too_close = any(distance(pt, c0)<min_distance for c0 in chosen)
                        if too_close:
                            continue
                    chosen.append(pt)

                return np.array(chosen[:n_candidates])
            else:
                # front >= n_candidates => pick subset via distance
                chosen = []
                def distance(a,b):
                    return np.linalg.norm(a-b)
                chosen.append(pareto_points[0])
                for i in range(1, len(pareto_points)):
                    pt = pareto_points[i]
                    if min_distance>0:
                        too_close = any(distance(pt, c0)<min_distance for c0 in chosen)
                        if too_close:
                            continue
                    chosen.append(pt)
                    if len(chosen)>=n_candidates:
                        break
                return np.array(chosen)
        
        # Fallback or alternative approach
        if selection_mode=="all-merged":
            # For each candidate i, define merged_acq_i = max across M dims
            merged_acq = np.max(acq_matrix, axis=1)
            # sort descending
            sorted_idx = np.argsort(-merged_acq)
            chosen = []
            def distance(a,b):
                return np.linalg.norm(a-b)

            for idx in sorted_idx:
                pt = X_cand[idx]
                if len(chosen)==0:
                    chosen.append(pt)
                else:
                    if min_distance>0:
                        too_close = any(distance(pt,c0)<min_distance for c0 in chosen)
                        if too_close:
                            continue
                    chosen.append(pt)
                if len(chosen)>=n_candidates:
                    break
            return np.array(chosen)

        # If we got here with an unexpected selection_mode, fallback
        raise ValueError(f"Unknown selection_mode='{selection_mode}'")

    def evaluate_BO_over_generations(self, temperature: list = None, max_generations: int = 1000) -> None:
        """
        This function simulates the evolution of candidate points over several generations
        using Bayesian Optimization. It plots several figures to help diagnose and understand:
          - The background objective landscape.
          - How candidate points evolve over generations under different temperature settings.
          - The evolution of the predicted mean responses and errors for each objective.
          - The predicted mean surfaces of the final surrogate models.
        
        Parameters
        ----------
        temperature : list
            A list or array of temperature values (one per generation). The temperature influences
            the exploration/exploitation balance in the acquisition function.
        max_generations : int, optional
            Number of generations to simulate. (This function uses the length of `temperature`.)
        
        Returns
        -------
        None
        """
        import matplotlib.pyplot as plt
        import numpy as np

        # Determine the number of generations from the temperature array length.
        max_generations = len(temperature)

        # Define two synthetic objective functions.
        # Y: a sinusoidal function with noise.
        def Y(X1, X2, noise=0.0):
            # Returns a sinusoidal pattern over the domain.
            return np.sin(X1 / 3) + np.sin(X2 / 3) + np.random.rand(X1.shape[0]) * noise

        # Y2: a quadratic function with noise.
        def Y2(X1, X2, noise=0.0):
            return (X1 - 50)**2 / 2500 + (X2 - 50)**2 / 2500 + np.random.rand(X1.shape[0]) * noise

        # Generate synthetic training data.
        X_train = np.random.rand(5, 2) * 100  # 5 samples in a 100x100 domain.
        # Generate training responses for two objectives (each column corresponds to one objective).
        Y_train = np.array([Y(X_train[:, 0], X_train[:, 1], noise=0.5),
                            Y2(X_train[:, 0], X_train[:, 1], noise=1.0)]).T

        # Create a grid over the domain for background visualization.
        x_grid = np.linspace(0, 100, 200)
        y_grid = np.linspace(0, 100, 200)
        XX, YY = np.meshgrid(x_grid, y_grid)
        Z = Y(XX, YY)    # Background objective function for objective 1.
        Z2 = Y2(XX, YY)  # Background objective function for objective 2.

        # Plot the background gradient (for objective 1) as a contour plot.
        plt.figure(figsize=(8, 6))
        bg = plt.contourf(XX, YY, Z, levels=100, cmap='viridis')
        plt.colorbar(bg, label='Objective Value (Background)')
        plt.xlabel('X1')
        plt.ylabel('X2')
        plt.title('Background Objective Landscape (Objective 1)')
        plt.tight_layout()
        plt.show()

        # Initialize arrays to store mean responses and errors over generations.
        n_objectives = 2
        mean_response_array = np.zeros((max_generations, n_objectives))
        error_array = np.zeros((max_generations, n_objectives))

        # Instantiate the Bayesian Optimization model (multi-objective version).
        bo = BayesianOptimization(bounds=np.array([[0, 100], [0, 100]]), n_objectives=n_objectives)
        bo.fit(X_train, Y_train)
        plt.figure(figsize=(8, 6))
        plt.contourf(XX, YY, Z, levels=100, cmap='viridis')
        
        # Loop over generations.
        for i, (gen, T_val) in enumerate(zip(range(1, max_generations + 1), temperature)):
            # Obtain candidate points using a Boltzmann sampling strategy with current temperature T_val.
            new_candidates = bo.recommend_candidates(n_candidates=10, T=T_val)
            # Compute responses for each candidate for both objectives.
            responses = np.array([Y(new_candidates[:, 0], new_candidates[:, 1], noise=0.5),
                                  Y2(new_candidates[:, 0], new_candidates[:, 1], noise=1.0)]).T

            # Scale marker size relative to temperature (for visualization purposes).
            marker_size = 400 * (T_val / max(temperature))

            # Plot candidate points on the background plot.

            # Note: No legend is added as requested.
            plt.scatter(new_candidates[:, 0],
                        new_candidates[:, 1],
                        c=responses[:, 0],
                        cmap='viridis',
                        s=marker_size,
                        edgecolor='k',
                        alpha=0.8)
            plt.xlabel('X1')
            plt.ylabel('X2')
            plt.title(f'Generation {gen} Candidate Points (T = {T_val:.2f})')
            plt.tight_layout()

            # Optionally annotate each candidate with its generation number.
            # (Comment out if not desired.)
            # for (x, y) in new_candidates:
            #     plt.text(x, y, f'{gen}', fontsize=8, color='white', ha='center', va='center')

            # Augment training data with new candidates and their responses.
            X_train = np.concatenate((X_train, new_candidates), axis=0)
            Y_train = np.concatenate((Y_train, responses), axis=0)
            mean_response_array[i, :] = np.mean(responses, axis=0)
            bo.fit(X_train, Y_train)

            # Compute prediction errors over the grid for both objectives.
            points = np.column_stack((XX.ravel(), YY.ravel()))
            mean_obj1, _ = bo._predict(points, 0)
            mean_grid_obj1 = mean_obj1.reshape(XX.shape)
            error_array[i, 0] = np.sum(np.abs(Z - mean_grid_obj1))

            mean_obj2, _ = bo._predict(points, 1)
            mean_grid_obj2 = mean_obj2.reshape(XX.shape)
            error_array[i, 1] = np.sum(np.abs(Z2 - mean_grid_obj2))

        # Plot evolution of mean response for Objective 1.
        plt.figure(figsize=(8, 6))
        plt.plot(temperature, mean_response_array[:, 0], 'o', markersize=6, color='blue')
        plt.xlabel('Temperature')
        plt.ylabel('Mean Response (Objective 1)')
        plt.title('Evolution of Mean Response for Objective 1')
        plt.tight_layout()
        plt.show()

        # Plot evolution of mean response for Objective 2.
        plt.figure(figsize=(8, 6))
        plt.plot(temperature, mean_response_array[:, 1], 'o', markersize=6, color='red')
        plt.xlabel('Temperature')
        plt.ylabel('Mean Response (Objective 2)')
        plt.title('Evolution of Mean Response for Objective 2')
        plt.tight_layout()
        plt.show()

        # Plot evolution of prediction error for Objective 1.
        plt.figure(figsize=(8, 6))
        plt.plot(error_array[:, 0], 'o', markersize=6, color='blue')
        plt.xlabel('Generation')
        plt.ylabel('Error (Objective 1)')
        plt.title('Prediction Error Evolution for Objective 1')
        plt.tight_layout()
        plt.show()

        # Plot evolution of prediction error for Objective 2.
        plt.figure(figsize=(8, 6))
        plt.plot(error_array[:, 1], 'o', markersize=6, color='red')
        plt.xlabel('Generation')
        plt.ylabel('Error (Objective 2)')
        plt.title('Prediction Error Evolution for Objective 2')
        plt.tight_layout()
        plt.show()

        # Plot final predicted mean surface for Objective 1.
        points = np.column_stack((XX.ravel(), YY.ravel()))
        mean_obj1, _ = bo._predict(points, 0)
        mean_grid_obj1 = mean_obj1.reshape(XX.shape)
        plt.figure(figsize=(8, 6))
        bg = plt.contourf(XX, YY, mean_grid_obj1, levels=100, cmap='viridis')
        plt.colorbar(bg, label='Predicted Mean (Objective 1)')
        plt.xlabel('X1')
        plt.ylabel('X2')
        plt.title('Predicted Mean Surface for Objective 1')
        plt.tight_layout()
        plt.show()

        # Plot final predicted mean surface for Objective 2.
        mean_obj2, _ = bo._predict(points, 1)
        mean_grid_obj2 = mean_obj2.reshape(XX.shape)
        plt.figure(figsize=(8, 6))
        bg = plt.contourf(XX, YY, mean_grid_obj2, levels=100, cmap='viridis')
        plt.colorbar(bg, label='Predicted Mean (Objective 2)')
        plt.xlabel('X1')
        plt.ylabel('X2')
        plt.title('Predicted Mean Surface for Objective 2')
        plt.tight_layout()
        plt.show()

        # This function currently does not return values (generations_array and mutation_rate_array
        # are undefined), so we return None.
        return None

    def plot_model(self, objective_idx: int = 0, filename: Optional[str] = None, show: bool = True):
        """
        Visualize the trained surrogate model (mean prediction and uncertainty) along with training data.
        
        Supported dimensions:
        - 1D: Plot mean curve, fill_between for uncertainty (mean +/- 1.96 std), and scatter training points.
        - 2D: Plot contour map of the mean prediction and scatter training points.
        - >2D: Not supported (logs a warning).

        Parameters
        ----------
        objective_idx : int
            Index of the objective to visualize.
        filename : str, optional
            If provided, saves the figure to this path.
        show : bool
            If True, calls plt.show().
        """
        import matplotlib.pyplot as plt

        if not hasattr(self, 'X_train') or self.X_train is None:
            print("Model has not been trained yet used.")
            return

        n_features = self.X_train.shape[1]
        
        # Determine bounds for plotting
        if self.bounds is not None:
            # Use defined bounds
            plot_bounds = self.bounds
        else:
            # Infer from data with some padding
            mins = self.X_train.min(axis=0)
            maxs = self.X_train.max(axis=0)
            span = maxs - mins
            if np.any(span == 0): span = 1.0 # handle single point or constant dim
            plot_bounds = np.stack([mins - 0.1 * span, maxs + 0.1 * span], axis=1)

        if n_features == 1:
            # --- 1D Plotting ---
            lb, ub = plot_bounds[0]
            resolution = 200
            x_grid = np.linspace(lb, ub, resolution).reshape(-1, 1)
            
            mean, std = self._predict(x_grid, objective_idx)
            
            plt.figure(figsize=(10, 6))
            
            # Plot uncertainty
            plt.fill_between(x_grid.ravel(), 
                             mean - 1.96 * std, 
                             mean + 1.96 * std, 
                             alpha=0.2, color='blue', label='95% Confidence')
            
            # Plot mean prediction
            plt.plot(x_grid, mean, 'b-', label='Predicted Mean')
            
            # Plot training data
            y_train = self.Y_train[:, objective_idx]
            plt.scatter(self.X_train, y_train, c='red', marker='x', label='Training Data')
            
            plt.xlabel('Feature 1')
            plt.ylabel(f'Objective {objective_idx}')
            plt.title(f'Bayesian Optimization Model (Objective {objective_idx})')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
        elif n_features == 2:
            # --- 2D Plotting ---
            resolution = 100
            x1_lb, x1_ub = plot_bounds[0]
            x2_lb, x2_ub = plot_bounds[1]
            
            x1 = np.linspace(x1_lb, x1_ub, resolution)
            x2 = np.linspace(x2_lb, x2_ub, resolution)
            X1, X2 = np.meshgrid(x1, x2)
            
            # Flatten for prediction
            grid_points = np.column_stack([X1.ravel(), X2.ravel()])
            mean, std = self._predict(grid_points, objective_idx)
            
            mean_grid = mean.reshape(X1.shape)
            # std_grid = std.reshape(X1.shape) # Could plot uncertainty in another subplot if needed
            
            plt.figure(figsize=(12, 5))
            
            # Subplot 1: Mean Prediction
            plt.subplot(1, 2, 1)
            cp = plt.contourf(X1, X2, mean_grid, levels=50, cmap='viridis')
            plt.colorbar(cp, label='Predicted Mean')
            plt.scatter(self.X_train[:, 0], self.X_train[:, 1], c='red', marker='x', s=50, label='Data')
            plt.xlabel('Feature 1')
            plt.ylabel('Feature 2')
            plt.title(f'Predicted Mean (Obj {objective_idx})')
            plt.legend()

            # Subplot 2: Uncertainty (Std Dev)
            std_grid = std.reshape(X1.shape)
            plt.subplot(1, 2, 2)
            cp_std = plt.contourf(X1, X2, std_grid, levels=50, cmap='plasma')
            plt.colorbar(cp_std, label='Uncertainty (Std)')
            plt.scatter(self.X_train[:, 0], self.X_train[:, 1], c='white', marker='.', s=20, alpha=0.5)
            plt.xlabel('Feature 1')
            plt.ylabel('Feature 2')
            plt.title(f'Uncertainty (Obj {objective_idx})')
            
            plt.tight_layout()
            
        else:
            # --- >2D ---
            print(f"[WARN] plot_model only supports 1D and 2D feature spaces. Current dim: {n_features}")
            return

        if filename:
            plt.savefig(filename, dpi=300)
            print(f"Plot saved to {filename}")
        
        if show:
            plt.show()
