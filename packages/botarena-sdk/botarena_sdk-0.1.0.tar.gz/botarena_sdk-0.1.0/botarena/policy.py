"""Base policy class for Bot Arena submissions."""

from abc import ABC, abstractmethod
from typing import Any, Optional, Union

import numpy as np

from botarena.types import Action, Observation


class Policy(ABC):
    """Abstract base class for robot control policies.

    Subclass this to create your own policy for the Bot Arena competition.
    Your policy must implement the `act` method, which takes an observation
    and returns an action.

    Example:
        >>> class MyPolicy(Policy):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.step_count = 0
        ...
        ...     def act(self, observation):
        ...         self.step_count += 1
        ...         # Your control logic here
        ...         return np.zeros(3)  # 3-DOF action
        ...
        ...     def reset(self):
        ...         self.step_count = 0

    Note:
        - The `act` method is called at each simulation step (~50Hz).
        - Keep computation light to avoid timing issues.
        - Use `reset` to clear any episode-specific state.
    """

    def __init__(self) -> None:
        """Initialize the policy."""
        self._action_space: Optional[dict[str, Any]] = None
        self._observation_space: Optional[dict[str, Any]] = None

    @property
    def action_space(self) -> Optional[dict[str, Any]]:
        """Action space specification (set by runner)."""
        return self._action_space

    @action_space.setter
    def action_space(self, value: dict[str, Any]) -> None:
        self._action_space = value

    @property
    def observation_space(self) -> Optional[dict[str, Any]]:
        """Observation space specification (set by runner)."""
        return self._observation_space

    @observation_space.setter
    def observation_space(self, value: dict[str, Any]) -> None:
        self._observation_space = value

    @abstractmethod
    def act(
        self, observation: Union[Observation, dict[str, Any], np.ndarray]
    ) -> Union[Action, np.ndarray]:
        """Compute action given an observation.

        Args:
            observation: Current observation from the environment.
                Can be an Observation object, raw dictionary, or numpy array
                depending on the scenario configuration.

        Returns:
            Action to execute. Can be an Action object or numpy array
            of control values.

        Note:
            This method is called at each simulation step. Keep it fast!
        """
        pass

    def reset(self) -> None:
        """Reset any episode-specific state.

        Called at the start of each evaluation episode. Override this
        to reset any internal state your policy maintains.
        """
        pass

    def close(self) -> None:
        """Clean up any resources.

        Called when the evaluation is complete. Override this to
        release any resources (e.g., GPU memory, file handles).
        """
        pass


class RandomPolicy(Policy):
    """A simple random policy for testing.

    Samples random actions from the action space bounds.
    Useful as a baseline or for testing the submission pipeline.

    Example:
        >>> from botarena import RandomPolicy, LocalRunner
        >>> runner = LocalRunner("messy-room")
        >>> result = runner.evaluate(RandomPolicy())
    """

    def __init__(self, seed: Optional[int] = None) -> None:
        """Initialize with optional random seed.

        Args:
            seed: Random seed for reproducibility.
        """
        super().__init__()
        self._rng = np.random.default_rng(seed)

    def act(
        self, observation: Union[Observation, dict[str, Any], np.ndarray]
    ) -> np.ndarray:
        """Return a random action.

        Args:
            observation: Ignored for random policy.

        Returns:
            Random action array sampled uniformly from [-1, 1].
        """
        # Default to 3-DOF if action space not set
        action_dim = 3
        if self._action_space and "shape" in self._action_space:
            action_dim = self._action_space["shape"][0]

        return self._rng.uniform(-1, 1, size=action_dim).astype(np.float32)


class ZeroPolicy(Policy):
    """A policy that always returns zero action.

    Useful for testing that the robot stays in place.
    """

    def act(
        self, observation: Union[Observation, dict[str, Any], np.ndarray]
    ) -> np.ndarray:
        """Return zero action.

        Args:
            observation: Ignored for zero policy.

        Returns:
            Zero action array.
        """
        action_dim = 3
        if self._action_space and "shape" in self._action_space:
            action_dim = self._action_space["shape"][0]

        return np.zeros(action_dim, dtype=np.float32)
