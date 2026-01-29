"""Bot Arena SDK - Official Python client for the Bot Arena platform.

This SDK provides tools for:
- Developing robot control policies locally
- Testing policies against simulation environments
- Submitting policies to the Bot Arena competition
- Retrieving results and leaderboard standings

Example:
    >>> from botarena import Policy, LocalRunner, Client
    >>>
    >>> # Define your policy
    >>> class MyPolicy(Policy):
    ...     def act(self, observation):
    ...         return self.action_space.sample()
    >>>
    >>> # Test locally
    >>> runner = LocalRunner("messy-room")
    >>> result = runner.evaluate(MyPolicy())
    >>> print(f"Score: {result.score}")
    >>>
    >>> # Submit to competition
    >>> client = Client(api_key="your-api-key")
    >>> submission = client.submit("my_policy.zip", scenario="messy-room")
    >>> print(f"Submission ID: {submission.id}")
"""

from botarena.client import Client
from botarena.policy import Policy
from botarena.runner import LocalRunner
from botarena.types import (
    Action,
    EvaluationResult,
    JudgeVerdict,
    Observation,
    Submission,
    SubmissionStatus,
)

__version__ = "0.1.0"
__all__ = [
    "Policy",
    "Client",
    "LocalRunner",
    "Observation",
    "Action",
    "EvaluationResult",
    "Submission",
    "SubmissionStatus",
    "JudgeVerdict",
    "__version__",
]
