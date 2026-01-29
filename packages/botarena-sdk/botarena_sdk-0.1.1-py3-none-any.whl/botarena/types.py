"""Type definitions for the Bot Arena SDK."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np


class SubmissionStatus(str, Enum):
    """Status of a submission in the pipeline."""

    PENDING = "pending"
    UPLOADED = "uploaded"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JudgeVerdict(str, Enum):
    """Verdict from the AI judge."""

    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"
    ERROR = "error"


@dataclass
class Observation:
    """Observation from the simulation environment.

    Attributes:
        robot_state: Joint positions and velocities of the robot.
        objects: Dictionary of object states (position, orientation).
        goal: Goal specification for the current task.
        time_remaining: Seconds remaining in the episode.
        raw: Raw observation dictionary from MuJoCo.
    """

    robot_state: np.ndarray
    objects: dict[str, np.ndarray]
    goal: dict[str, Any]
    time_remaining: float
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Action:
    """Action to send to the robot.

    Attributes:
        control: Control signal array (joint torques or positions).
        gripper: Optional gripper command (0.0 = open, 1.0 = closed).
    """

    control: np.ndarray
    gripper: Optional[float] = None

    def to_array(self) -> np.ndarray:
        """Convert action to a flat numpy array."""
        if self.gripper is not None:
            return np.concatenate([self.control, [self.gripper]])
        return self.control


@dataclass
class EvaluationResult:
    """Result of a local policy evaluation.

    Attributes:
        success: Whether the task was completed successfully.
        score: Numerical score (0.0 to 1.0).
        steps: Number of simulation steps executed.
        time_elapsed: Wall-clock time for evaluation.
        metrics: Additional metrics from the scenario.
        video_path: Path to recorded video (if render=True).
        error: Error message if evaluation failed.
    """

    success: bool
    score: float
    steps: int
    time_elapsed: float
    metrics: dict[str, Any] = field(default_factory=dict)
    video_path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class Submission:
    """A submission to the Bot Arena competition.

    Attributes:
        id: Unique submission identifier.
        scenario_id: The scenario this submission is for.
        status: Current status in the pipeline.
        created_at: When the submission was created.
        verdict: Judge verdict (if judged).
        confidence: Judge confidence score (if judged).
        video_url: URL to the replay video (if available).
        error_message: Error message (if failed).
    """

    id: str
    scenario_id: str
    status: SubmissionStatus
    created_at: datetime
    verdict: Optional[JudgeVerdict] = None
    confidence: Optional[float] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class LeaderboardEntry:
    """An entry on the leaderboard.

    Attributes:
        rank: Position on the leaderboard.
        submission_id: ID of the submission.
        user_id: ID of the user (anonymized in public view).
        scenario_id: The scenario.
        score: Numerical score.
        verdict: Judge verdict.
        submitted_at: When the submission was made.
    """

    rank: int
    submission_id: str
    user_id: str
    scenario_id: str
    score: float
    verdict: JudgeVerdict
    submitted_at: datetime


@dataclass
class Scenario:
    """Information about an available scenario.

    Attributes:
        id: Unique scenario identifier.
        name: Human-readable name.
        description: Detailed description of the task.
        difficulty: Difficulty rating (1-5).
        time_limit: Maximum episode time in seconds.
        observation_space: Description of observation structure.
        action_space: Description of action structure.
    """

    id: str
    name: str
    description: str
    difficulty: int
    time_limit: float
    observation_space: dict[str, Any]
    action_space: dict[str, Any]
