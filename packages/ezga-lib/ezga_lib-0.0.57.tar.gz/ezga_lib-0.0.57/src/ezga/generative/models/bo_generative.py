from __future__ import annotations

import numpy as np
from typing import Optional

from ezga.generative.base import Generative
from ezga.generative.models.BayesianOptimization import BayesianOptimization


class BOGenerative(Generative):
    """
    Bayesian-Optimization-based Generative model.

    This class adapts a BayesianOptimization engine to the Generative interface
    used by EZGA.

    IMPORTANT:
    ----------
    - This class operates strictly in feature space.
    - It NEVER generates atomic structures.
    - It ONLY proposes feature-space target vectors.
    - Physical realizability is handled downstream by Variation.
    """

    def __init__(
        self,
        *,
        size: int,
        start_gen: int,
        every: int,
        fit_frequency: int = 1,
        candidate_multiplier: int = 10,
        selection_mode: str = "pareto",
        min_distance: float = 0.0,
        discrete_design: bool = True,
        avoid_repetitions: bool = True,
        bo_kwargs: Optional[dict] = None,
        **kwargs,
    ):
        """
        Initialize a BO-based Generative model.

        Args:
            size (int):
                Number of feature-space targets to propose when active.

            start_gen (int):
                First generation at which BO is activated.

            every (int):
                Frequency (in generations) at which BO is queried.

            fit_frequency (int):
                Frequency (in generations) at which the BO model is retrained.
                Default is 1 (retrain every time targets are generated).

            candidate_multiplier (int):
                Size of BO candidate pool relative to `size`.

            selection_mode (str):
                Candidate selection strategy ('pareto' or 'all-merged').

            min_distance (float):
                Minimum Euclidean distance between proposed targets.

            discrete_design (bool):
                Whether to sample feature space discretely.

            avoid_repetitions (bool):
                Whether to avoid proposing duplicate targets.

            bo_kwargs (dict, optional):
                Additional keyword arguments passed directly to
                `BayesianOptimization(...)`.
        """
        super().__init__(
            size=size,
            start_gen=start_gen,
            every=every,
        )

        self.candidate_multiplier = candidate_multiplier
        self.selection_mode = selection_mode
        self.min_distance = min_distance
        self.discrete_design = discrete_design
        self.avoid_repetitions = avoid_repetitions

        bo_params = bo_kwargs or {}
        bo_params["fit_frequency"] = fit_frequency
        self.bo = BayesianOptimization(**bo_params)

    # ------------------------------------------------------------------
    # Required implementation of Generative interface
    # ------------------------------------------------------------------

    def _propose_targets(
        self,
        *,
        features: np.ndarray,
        objectives: np.ndarray,
        temperature: float,
        size: int,
    ) -> np.ndarray:
        """
        Propose feature-space targets using Bayesian Optimization.

        Args:
            features (np.ndarray):
                Current population features, shape (n_samples, n_features).

            objectives (np.ndarray):
                Objective values, shape (n_samples, n_objectives).

            temperature (float):
                Current temperature from Thermostat.

            size (int):
                Number of targets to generate.

        Returns:
            np.ndarray:
                Feature-space targets, shape (size, n_features).
        """
        # Fit surrogate models
        self.bo.fit(features, objectives)

        # Use BO to recommend feature-space candidates
        targets = self.bo.recommend_candidates(
            n_candidates=size,
            candidate_multiplier=self.candidate_multiplier,
            T=temperature,
            selection_mode=self.selection_mode,
            min_distance=self.min_distance,
            discrete_design=self.discrete_design,
            avoid_repetitions=self.avoid_repetitions,
        )

        return targets
