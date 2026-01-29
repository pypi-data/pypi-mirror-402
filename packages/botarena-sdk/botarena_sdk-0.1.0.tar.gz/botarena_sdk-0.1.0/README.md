# Bot Arena Python SDK

Official Python SDK for the [Bot Arena](https://botmanifold.com) robot policy competition platform.

## Installation

```bash
pip install botarena
```

For local testing with MuJoCo simulation:

```bash
pip install botarena[mujoco]
```

## Quick Start

### 1. Create a Policy

```python
from botarena import Policy
import numpy as np

class MyPolicy(Policy):
    """My awesome robot control policy."""

    def act(self, observation):
        # Your control logic here
        # observation contains robot state and environment info
        robot_pos = observation["robot_state"][:3]
        target_pos = observation["goal"]["target"]

        # Simple proportional control
        error = target_pos - robot_pos
        action = np.clip(error * 0.5, -1, 1)

        return action
```

### 2. Test Locally

```python
from botarena import LocalRunner

runner = LocalRunner("messy-room")
result = runner.evaluate(MyPolicy(), render=True)

print(f"Success: {result.success}")
print(f"Score: {result.score:.2f}")
print(f"Video: {result.video_path}")
```

### 3. Submit to Competition

```python
from botarena import Client

# Set BOTARENA_API_KEY environment variable or pass directly
client = Client(api_key="your-api-key")

# Package and submit
submission = client.submit("my_policy.zip", scenario="messy-room")
print(f"Submitted: {submission.id}")

# Wait for results
result = client.wait_for_result(submission.id)
print(f"Verdict: {result.verdict}")
print(f"Confidence: {result.confidence:.1%}")
```

## CLI Usage

The SDK includes a command-line interface:

```bash
# Submit a policy
botarena submit my_policy.zip -s messy-room --wait

# Check submission status
botarena status abc123

# View leaderboard
botarena leaderboard -s messy-room -n 20

# Test locally
botarena test my_policy.py -s messy-room --render

# List scenarios
botarena scenarios
```

## Policy Guidelines

Your policy must:

1. **Subclass `Policy`** and implement the `act` method
2. **Return actions quickly** - aim for <10ms per call
3. **Be deterministic** - given the same observation, return the same action
4. **Handle edge cases** - don't crash on unexpected observations

### Observation Format

```python
observation = {
    "robot_state": np.array([...]),  # Joint positions, velocities
    "objects": {
        "cube_1": np.array([x, y, z, qw, qx, qy, qz]),
        "cube_2": np.array([...]),
    },
    "goal": {
        "target": np.array([x, y, z]),
        "description": "Move cube_1 to target",
    },
    "time_remaining": 25.3,  # Seconds
}
```

### Action Format

```python
# 3-DOF action: [x_velocity, y_velocity, z_velocity]
action = np.array([0.5, -0.2, 0.1])

# Values should be in range [-1, 1]
# They are scaled to actual velocities by the environment
```

## Packaging Your Policy

Create a zip file with this structure:

```
my_policy.zip
├── policy.py          # Must contain a Policy subclass
├── __init__.py        # Can be empty
├── requirements.txt   # Optional: additional dependencies
└── weights/           # Optional: model weights
    └── model.pt
```

Your `policy.py` must contain exactly one class that subclasses `Policy`:

```python
from botarena import Policy

class MyPolicy(Policy):
    def __init__(self):
        super().__init__()
        # Load your model weights here
        self.model = load_model("weights/model.pt")

    def act(self, observation):
        return self.model.predict(observation)
```

## API Reference

### `Policy`

Base class for all policies.

- `act(observation) -> action`: **Required**. Compute action from observation.
- `reset()`: Optional. Reset episode state.
- `close()`: Optional. Clean up resources.

### `Client`

API client for submissions.

- `submit(path, scenario) -> Submission`: Submit a policy zip file.
- `get_submission(id) -> Submission`: Get submission status.
- `wait_for_result(id, timeout) -> Submission`: Wait for completion.
- `get_leaderboard(scenario, limit) -> List[LeaderboardEntry]`: Get rankings.

### `LocalRunner`

Local testing without submission.

- `evaluate(policy, render, video_path) -> EvaluationResult`: Run one episode.
- `benchmark(policy, num_episodes) -> dict`: Run multiple episodes.

## Environment Variables

- `BOTARENA_API_KEY`: Your API key for submissions
- `BOTARENA_API_URL`: Custom API URL (for development)

## Examples

See the [examples](https://github.com/botmanifold/botarena/tree/main/sdk/examples) directory for:

- `random_policy.py`: Baseline random policy
- `simple_controller.py`: Basic proportional controller
- `neural_policy.py`: PyTorch neural network policy

## Support

- Documentation: https://docs.botmanifold.com
- Discord: https://discord.gg/botarena
- Issues: https://github.com/botmanifold/botarena/issues
