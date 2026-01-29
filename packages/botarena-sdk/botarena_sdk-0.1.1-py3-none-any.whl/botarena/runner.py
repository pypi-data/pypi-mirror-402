"""Local runner for testing policies before submission."""

import time
from pathlib import Path
from typing import Any, Callable, Optional, Union

import numpy as np

from botarena.policy import Policy
from botarena.types import EvaluationResult


class LocalRunner:
    """Run and evaluate policies locally before submitting.

    The LocalRunner allows you to test your policy against a local
    simulation environment. This requires MuJoCo to be installed.

    Example:
        >>> from botarena import LocalRunner, Policy
        >>>
        >>> class MyPolicy(Policy):
        ...     def act(self, obs):
        ...         return np.zeros(3)
        >>>
        >>> runner = LocalRunner("messy-room")
        >>> result = runner.evaluate(MyPolicy(), render=True)
        >>> print(f"Success: {result.success}, Score: {result.score:.2f}")

    Args:
        scenario: Scenario ID to run (e.g., "messy-room").
        scenarios_path: Path to scenarios directory. If None, uses
            the installed scenarios or downloads them.
    """

    # Scenario configurations
    SCENARIOS = {
        "messy-room": {
            "module": "scenarios.messy_room.task",
            "class": "MessyRoom",
            "time_limit": 30.0,
            "max_steps": 300,
            "action_dim": 3,
        },
    }

    def __init__(
        self,
        scenario: str,
        scenarios_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize the runner."""
        if scenario not in self.SCENARIOS:
            available = ", ".join(self.SCENARIOS.keys())
            raise ValueError(f"Unknown scenario: {scenario}. Available: {available}")

        self.scenario = scenario
        self.config = self.SCENARIOS[scenario]
        self.scenarios_path = Path(scenarios_path) if scenarios_path else None

        self._task = None
        self._runner = None

    def _load_scenario(self):
        """Lazily load the scenario module."""
        if self._task is not None:
            return

        try:
            # Try to import the scenario
            import importlib

            if self.scenarios_path:
                import sys

                sys.path.insert(0, str(self.scenarios_path.parent))

            module = importlib.import_module(self.config["module"])
            task_class = getattr(module, self.config["class"])
            self._task = task_class()

            # Try to import the runner
            from scenarios.runner import SimRunner

            self._runner = SimRunner(self._task)

        except ImportError as e:
            raise RuntimeError(
                f"Failed to load scenario '{self.scenario}'. "
                f"Make sure MuJoCo and the scenarios package are installed. "
                f"Error: {e}"
            ) from e

    def evaluate(
        self,
        policy: Union[Policy, Callable[[Any], np.ndarray]],
        max_steps: Optional[int] = None,
        render: bool = False,
        video_path: Optional[Union[str, Path]] = None,
        seed: Optional[int] = None,
    ) -> EvaluationResult:
        """Evaluate a policy on the scenario.

        Args:
            policy: Policy instance or callable that takes observation
                and returns action.
            max_steps: Maximum simulation steps. Defaults to scenario limit.
            render: Whether to render video frames.
            video_path: Path to save video. If None and render=True,
                generates a path automatically.
            seed: Random seed for reproducibility.

        Returns:
            EvaluationResult with success, score, and metrics.

        Example:
            >>> result = runner.evaluate(my_policy, render=True)
            >>> if result.success:
            ...     print(f"Task completed! Score: {result.score:.2f}")
            >>> if result.video_path:
            ...     print(f"Video saved to: {result.video_path}")
        """
        self._load_scenario()
        assert self._runner is not None  # guaranteed by _load_scenario

        max_steps = max_steps or int(self.config["max_steps"])

        # Set up the policy
        if isinstance(policy, Policy):
            policy.action_space = {
                "shape": (self.config["action_dim"],),
                "low": -1.0,
                "high": 1.0,
            }
            policy.reset()
            policy_fn = policy.act
        else:
            policy_fn = policy

        # Determine video path
        actual_video_path = None
        if render or video_path:
            if video_path:
                actual_video_path = str(video_path)
            else:
                actual_video_path = f"eval_{self.scenario}_{int(time.time())}.mp4"

        # Run evaluation
        start_time = time.time()
        try:
            result = self._runner.run_policy(
                policy_fn,
                max_steps=max_steps,
                render=render,
                video_path=actual_video_path,
            )

            elapsed = time.time() - start_time

            # Extract metrics
            success = result.get("success", False)
            score = result.get("score", 0.0)
            steps = result.get("sim_steps", 0)
            metrics = {
                k: v
                for k, v in result.items()
                if k not in ("success", "score", "sim_steps", "frames")
            }

            return EvaluationResult(
                success=success,
                score=score,
                steps=steps,
                time_elapsed=elapsed,
                metrics=metrics,
                video_path=actual_video_path if render else None,
                error=None,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            return EvaluationResult(
                success=False,
                score=0.0,
                steps=0,
                time_elapsed=elapsed,
                error=str(e),
            )

        finally:
            if isinstance(policy, Policy):
                policy.close()

    def benchmark(
        self,
        policy: Union[Policy, Callable[[Any], np.ndarray]],
        num_episodes: int = 10,
        seed: Optional[int] = None,
    ) -> dict[str, Any]:
        """Run multiple evaluation episodes and compute statistics.

        Args:
            policy: Policy to evaluate.
            num_episodes: Number of episodes to run.
            seed: Base random seed for reproducibility.

        Returns:
            Dictionary with aggregated statistics.

        Example:
            >>> stats = runner.benchmark(my_policy, num_episodes=100)
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
            >>> print(f"Mean score: {stats['mean_score']:.2f}")
        """
        results = []
        for i in range(num_episodes):
            episode_seed = seed + i if seed is not None else None
            result = self.evaluate(policy, seed=episode_seed)
            results.append(result)

        successes = [r.success for r in results]
        scores = [r.score for r in results]
        steps = [r.steps for r in results]
        times = [r.time_elapsed for r in results]

        return {
            "num_episodes": num_episodes,
            "success_rate": sum(successes) / len(successes),
            "mean_score": np.mean(scores),
            "std_score": np.std(scores),
            "min_score": np.min(scores),
            "max_score": np.max(scores),
            "mean_steps": np.mean(steps),
            "mean_time": np.mean(times),
            "results": results,
        }
