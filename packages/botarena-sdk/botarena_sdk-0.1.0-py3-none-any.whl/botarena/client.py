"""Bot Arena API client for submitting policies and checking results."""

import os
from datetime import datetime
from pathlib import Path
from typing import IO, Any, Optional, Union

import requests

from botarena.types import (
    JudgeVerdict,
    LeaderboardEntry,
    Scenario,
    Submission,
    SubmissionStatus,
)


class BotArenaError(Exception):
    """Base exception for Bot Arena API errors."""

    pass


class AuthenticationError(BotArenaError):
    """Raised when API authentication fails."""

    pass


class SubmissionError(BotArenaError):
    """Raised when a submission fails."""

    pass


class Client:
    """Client for interacting with the Bot Arena API.

    Use this client to submit policies, check submission status,
    and view leaderboard standings.

    Example:
        >>> client = Client(api_key="your-api-key")
        >>>
        >>> # Submit a policy
        >>> submission = client.submit("my_policy.zip", scenario="messy-room")
        >>> print(f"Submitted: {submission.id}")
        >>>
        >>> # Check status
        >>> status = client.get_submission(submission.id)
        >>> print(f"Status: {status.status}")
        >>>
        >>> # View leaderboard
        >>> leaderboard = client.get_leaderboard("messy-room", limit=10)
        >>> for entry in leaderboard:
        ...     print(f"#{entry.rank}: {entry.score:.2f}")

    Args:
        api_key: Your Bot Arena API key. If not provided, reads from
            BOTARENA_API_KEY environment variable.
        base_url: API base URL. Defaults to production API.
        timeout: Request timeout in seconds.
    """

    DEFAULT_BASE_URL = "https://api.botmanifold.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the client."""
        self.api_key = api_key or os.environ.get("BOTARENA_API_KEY")
        self.base_url = (
            base_url or os.environ.get("BOTARENA_API_URL", self.DEFAULT_BASE_URL)
        ).rstrip("/")
        self.timeout = timeout

        self._session = requests.Session()
        if self.api_key:
            self._session.headers["Authorization"] = f"Bearer {self.api_key}"
        self._session.headers["User-Agent"] = "botarena-sdk/0.1.0"

    def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict:
        """Make an API request."""
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        try:
            response = self._session.request(method, url, **kwargs)
        except requests.RequestException as e:
            raise BotArenaError(f"Request failed: {e}") from e

        if response.status_code == 401:
            raise AuthenticationError("Invalid API key")
        if response.status_code == 403:
            raise AuthenticationError("Access denied")

        if not response.ok:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise BotArenaError(f"API error ({response.status_code}): {detail}")

        return response.json()

    def submit(
        self,
        policy_path: Union[str, Path, IO[bytes]],
        scenario: str,
        description: Optional[str] = None,
    ) -> Submission:
        """Submit a policy to the competition.

        Args:
            policy_path: Path to a zip file containing your policy,
                or a file-like object.
            scenario: Scenario ID to submit to (e.g., "messy-room").
            description: Optional description for this submission.

        Returns:
            Submission object with ID and initial status.

        Raises:
            SubmissionError: If the submission fails validation.
            BotArenaError: If the API request fails.

        Example:
            >>> submission = client.submit("my_policy.zip", "messy-room")
            >>> print(f"Submission ID: {submission.id}")
        """
        if isinstance(policy_path, (str, Path)):
            path = Path(policy_path)
            if not path.exists():
                raise SubmissionError(f"File not found: {path}")
            if not path.suffix == ".zip":
                raise SubmissionError("Policy must be a .zip file")
            if path.stat().st_size > 10 * 1024 * 1024:  # 10MB
                raise SubmissionError("Policy file exceeds 10MB limit")

            with open(path, "rb") as f:
                return self._submit_file(f, path.name, scenario, description)
        else:
            return self._submit_file(policy_path, "policy.zip", scenario, description)

    def _submit_file(
        self,
        file: IO[bytes],
        filename: str,
        scenario: str,
        description: Optional[str],
    ) -> Submission:
        """Submit a file object."""
        files = {"file": (filename, file, "application/zip")}
        params = {"scenario": scenario}
        if description:
            params["description"] = description

        data = self._request("POST", "/submissions", files=files, params=params)

        return Submission(
            id=data["submission_id"],
            scenario_id=data["scenario_id"],
            status=SubmissionStatus(data["status"]),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
        )

    def get_submission(self, submission_id: str) -> Submission:
        """Get the status of a submission.

        Args:
            submission_id: The submission ID returned from submit().

        Returns:
            Submission object with current status and results.

        Example:
            >>> status = client.get_submission("abc123")
            >>> if status.status == SubmissionStatus.COMPLETED:
            ...     print(f"Verdict: {status.verdict}")
        """
        data = self._request("GET", f"/submissions/{submission_id}")

        # Try to get judge result
        verdict = None
        confidence = None
        try:
            judge_data = self._request("GET", f"/submissions/{submission_id}/judge")
            verdict = JudgeVerdict(judge_data["verdict"])
            confidence = judge_data.get("confidence")
        except BotArenaError:
            pass  # Judge result not available yet

        return Submission(
            id=data["id"],
            scenario_id=data["scenario_id"],
            status=SubmissionStatus(data["status"]),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            verdict=verdict,
            confidence=confidence,
            video_url=data.get("video_url"),
            error_message=data.get("error_message"),
        )

    def wait_for_result(
        self,
        submission_id: str,
        timeout: int = 300,
        poll_interval: int = 5,
    ) -> Submission:
        """Wait for a submission to complete.

        Args:
            submission_id: The submission ID to wait for.
            timeout: Maximum time to wait in seconds.
            poll_interval: Time between status checks in seconds.

        Returns:
            Submission object with final status.

        Raises:
            TimeoutError: If the submission doesn't complete in time.
        """
        import time

        start_time = time.time()
        while time.time() - start_time < timeout:
            submission = self.get_submission(submission_id)
            if submission.status in (
                SubmissionStatus.COMPLETED,
                SubmissionStatus.FAILED,
            ):
                return submission
            time.sleep(poll_interval)

        raise TimeoutError(
            f"Submission {submission_id} did not complete within {timeout}s"
        )

    def get_leaderboard(
        self,
        scenario: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[LeaderboardEntry]:
        """Get the leaderboard for a scenario.

        Args:
            scenario: Scenario ID to filter by, or None for all.
            limit: Maximum number of entries to return.
            offset: Number of entries to skip (for pagination).

        Returns:
            List of LeaderboardEntry objects.

        Example:
            >>> leaderboard = client.get_leaderboard("messy-room", limit=10)
            >>> for entry in leaderboard:
            ...     print(f"#{entry.rank}: Score {entry.score:.2f}")
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if scenario:
            params["scenario"] = scenario

        data = self._request("GET", "/submissions", params=params)

        entries = []
        for i, sub in enumerate(data["submissions"], start=offset + 1):
            entries.append(
                LeaderboardEntry(
                    rank=i,
                    submission_id=sub["id"],
                    user_id=sub.get("user_id", "anonymous"),
                    scenario_id=sub["scenario_id"],
                    score=sub.get("score", 0.0),
                    verdict=(
                        JudgeVerdict(sub["verdict"])
                        if sub.get("verdict")
                        else JudgeVerdict.PASS
                    ),
                    submitted_at=datetime.fromisoformat(
                        sub["created_at"].replace("Z", "+00:00")
                    ),
                )
            )

        return entries

    def list_scenarios(self) -> list[Scenario]:
        """List all available scenarios.

        Returns:
            List of Scenario objects.
        """
        # For now, return hardcoded scenarios
        # TODO: Implement /scenarios endpoint
        return [
            Scenario(
                id="messy-room",
                name="Messy Room Challenge",
                description="Clean up a messy room by moving objects to targets.",
                difficulty=2,
                time_limit=30.0,
                observation_space={
                    "type": "dict",
                    "robot_state": "array(7,)",
                    "objects": "dict",
                },
                action_space={"type": "array", "shape": (3,), "low": -1.0, "high": 1.0},
            ),
        ]

    def health_check(self) -> bool:
        """Check if the API is healthy.

        Returns:
            True if API is reachable and healthy.
        """
        try:
            data = self._request("GET", "/")
            return data.get("status") == "healthy"
        except BotArenaError:
            return False
