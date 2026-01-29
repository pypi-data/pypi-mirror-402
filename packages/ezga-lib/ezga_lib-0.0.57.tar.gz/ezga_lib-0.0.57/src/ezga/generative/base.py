from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class Generative(ABC):
    """
    Abstract base class for generative guidance models in EZGA.

    A Generative model proposes *targets in feature space* that guide the
    evolutionary search toward promising or diverse regions.

    IMPORTANT DESIGN PRINCIPLE
    --------------------------
    A Generative model:
      - operates ONLY in feature space
      - NEVER generates atomic structures
      - NEVER applies mutations directly
      - NEVER enforces constraints

    The conversion from feature targets to physically valid structures is
    handled exclusively by the `Variation` module via guided mutations.

    This abstraction allows multiple backends (Bayesian Optimization,
    diffusion models, heuristics, user-defined strategies) to plug into the
    same evolutionary workflow without breaking physical validity.
    """

    def __init__(
        self,
        *,
        size: int,
        start_gen: int,
        every: int,
    ):
        """
        Initialize the generative controller.

        Args:
            size (int):
                Number of feature-space targets proposed when activated.

            start_gen (int):
                First generation at which the generative model is allowed
                to propose targets.

            every (int):
                Frequency (in generations) at which the model is queried.
                For example, `every=5` means the model is used every 5 generations.
        """
        self.size = size
        self.start_gen = start_gen
        self.every = every

    # ------------------------------------------------------------------
    # Public API (called by the GA engine)
    # ------------------------------------------------------------------

    def is_active(self, generation: int) -> bool:
        """
        Check whether the generative model should be active at a given generation.

        Args:
            generation (int): Current generation index.

        Returns:
            bool: True if the model should propose targets, False otherwise.
        """
        if self.size <= 0:
            return False

        if generation < self.start_gen:
            return False

        if generation % self.every != 0:
            return False

        return True

    def generate_targets(
        self,
        *,
        generation: int,
        features: np.ndarray,
        objectives: np.ndarray,
        temperature: float,
    ) -> Optional[np.ndarray]:
        """
        Generate feature-space targets for guided variation.

        This is the ONLY method the GA engine should call.

        Args:
            generation (int):
                Current generation index.

            features (np.ndarray):
                Feature matrix of the current population,
                shape (n_samples, n_features).

            objectives (np.ndarray):
                Objective values corresponding to `features`,
                shape (n_samples, n_objectives).

            temperature (float):
                Current temperature provided by the Thermostat.
                Used to modulate exploration vs exploitation.

        Returns:
            Optional[np.ndarray]:
                Array of target feature vectors with shape
                (n_targets, n_features), or None if inactive.
        """
        if not self.is_active(generation):
            return None

        return self._propose_targets(
            features=features,
            objectives=objectives,
            temperature=temperature,
            size=self.size,
        )

    # ------------------------------------------------------------------
    # Backend-specific logic (to be implemented by subclasses)
    # ------------------------------------------------------------------

    @abstractmethod
    def _propose_targets(
        self,
        *,
        features: np.ndarray,
        objectives: np.ndarray,
        temperature: float,
        size: int,
    ) -> np.ndarray:
        """
        Propose feature-space targets.

        This method must be implemented by concrete subclasses
        (e.g. Bayesian Optimization, diffusion, heuristics).

        Args:
            features (np.ndarray):
                Current population features,
                shape (n_samples, n_features).

            objectives (np.ndarray):
                Corresponding objective values,
                shape (n_samples, n_objectives).

            temperature (float):
                Current temperature from the Thermostat.

            size (int):
                Number of feature-space targets to generate.

        Returns:
            np.ndarray:
                Feature-space target vectors,
                shape (size, n_features).
        """
        raise NotImplementedError
