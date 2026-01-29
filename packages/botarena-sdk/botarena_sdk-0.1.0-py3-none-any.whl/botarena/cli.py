"""Command-line interface for Bot Arena SDK."""

import argparse
import sys
from pathlib import Path


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="botarena",
        description="Bot Arena CLI - Submit and manage robot policies",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a policy")
    submit_parser.add_argument("policy", type=Path, help="Path to policy zip file")
    submit_parser.add_argument("-s", "--scenario", required=True, help="Scenario ID")
    submit_parser.add_argument(
        "-w", "--wait", action="store_true", help="Wait for result"
    )
    submit_parser.add_argument(
        "--timeout", type=int, default=300, help="Wait timeout in seconds"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Check submission status")
    status_parser.add_argument("submission_id", help="Submission ID")

    # Leaderboard command
    lb_parser = subparsers.add_parser("leaderboard", help="View leaderboard")
    lb_parser.add_argument("-s", "--scenario", help="Filter by scenario")
    lb_parser.add_argument(
        "-n", "--limit", type=int, default=10, help="Number of entries"
    )

    # Test command
    test_parser = subparsers.add_parser("test", help="Test policy locally")
    test_parser.add_argument("policy", type=Path, help="Path to policy module")
    test_parser.add_argument(
        "-s", "--scenario", default="messy-room", help="Scenario ID"
    )
    test_parser.add_argument("--render", action="store_true", help="Render video")
    test_parser.add_argument("-o", "--output", type=Path, help="Video output path")

    # Scenarios command
    subparsers.add_parser("scenarios", help="List available scenarios")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    try:
        if args.command == "submit":
            return cmd_submit(args)
        elif args.command == "status":
            return cmd_status(args)
        elif args.command == "leaderboard":
            return cmd_leaderboard(args)
        elif args.command == "test":
            return cmd_test(args)
        elif args.command == "scenarios":
            return cmd_scenarios(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


def cmd_submit(args):
    """Handle submit command."""
    from botarena import Client

    client = Client()
    print(f"Submitting {args.policy} to {args.scenario}...")

    submission = client.submit(args.policy, args.scenario)
    print(f"Submission ID: {submission.id}")
    print(f"Status: {submission.status.value}")

    if args.wait:
        print("Waiting for result...")
        result = client.wait_for_result(submission.id, timeout=args.timeout)
        print(f"Final status: {result.status.value}")
        if result.verdict:
            print(f"Verdict: {result.verdict.value}")
        if result.confidence:
            print(f"Confidence: {result.confidence:.1%}")
        if result.error_message:
            print(f"Error: {result.error_message}")

    return 0


def cmd_status(args):
    """Handle status command."""
    from botarena import Client

    client = Client()
    submission = client.get_submission(args.submission_id)

    print(f"Submission: {submission.id}")
    print(f"Scenario: {submission.scenario_id}")
    print(f"Status: {submission.status.value}")
    print(f"Created: {submission.created_at}")

    if submission.verdict:
        print(f"Verdict: {submission.verdict.value}")
    if submission.confidence:
        print(f"Confidence: {submission.confidence:.1%}")
    if submission.video_url:
        print(f"Video: {submission.video_url}")
    if submission.error_message:
        print(f"Error: {submission.error_message}")

    return 0


def cmd_leaderboard(args):
    """Handle leaderboard command."""
    from botarena import Client

    client = Client()
    entries = client.get_leaderboard(scenario=args.scenario, limit=args.limit)

    if not entries:
        print("No entries found.")
        return 0

    print(f"{'Rank':<6} {'Score':<10} {'Verdict':<10} {'Submitted':<20}")
    print("-" * 50)

    for entry in entries:
        print(
            f"#{entry.rank:<5} {entry.score:<10.2f} {entry.verdict.value:<10} "
            f"{entry.submitted_at.strftime('%Y-%m-%d %H:%M')}"
        )

    return 0


def cmd_test(args):
    """Handle test command."""
    from botarena import LocalRunner

    print(f"Testing policy on {args.scenario}...")

    runner = LocalRunner(args.scenario)

    # Load the policy module
    import importlib.util

    spec = importlib.util.spec_from_file_location("policy_module", args.policy)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find the policy class or function
    policy = None
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and name != "Policy":
            from botarena import Policy

            if issubclass(obj, Policy):
                policy = obj()
                break
        elif callable(obj) and name == "policy":
            policy = obj
            break

    if policy is None:
        print("Error: No policy found in module", file=sys.stderr)
        return 1

    result = runner.evaluate(
        policy,
        render=args.render,
        video_path=args.output,
    )

    print("\nResult:")
    print(f"  Success: {result.success}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Steps: {result.steps}")
    print(f"  Time: {result.time_elapsed:.2f}s")

    if result.video_path:
        print(f"  Video: {result.video_path}")

    if result.error:
        print(f"  Error: {result.error}")

    return 0 if result.success else 1


def cmd_scenarios(args):
    """Handle scenarios command."""
    from botarena import Client

    client = Client()
    scenarios = client.list_scenarios()

    for s in scenarios:
        print(f"\n{s.name} ({s.id})")
        print(f"  Difficulty: {'★' * s.difficulty}{'☆' * (5 - s.difficulty)}")
        print(f"  Time Limit: {s.time_limit}s")
        print(f"  {s.description}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
