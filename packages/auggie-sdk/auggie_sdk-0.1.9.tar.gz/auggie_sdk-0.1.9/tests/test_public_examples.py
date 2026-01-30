"""
Integration tests for public examples in the auggie repo.

These tests verify that examples in the public auggie repo work with the current SDK.
This catches breaking SDK changes before they affect the public examples.

Run with: AUGGIE_REPO=/path/to/auggie pytest -m public_examples
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Get the SDK root directory
SDK_ROOT = Path(__file__).parent.parent

# Get the auggie repo path from environment variable
_auggie_repo_env = os.environ.get("AUGGIE_REPO")
AUGGIE_REPO = Path(_auggie_repo_env) if _auggie_repo_env else None


def run_example(script_path: Path, timeout: int = 60) -> tuple[int, str, str]:
    """
    Run an example script and return (returncode, stdout, stderr).

    The script is run with PYTHONPATH set to the SDK root, so it uses
    the local development version of the SDK, not the installed pip package.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SDK_ROOT)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


def discover_example_tests() -> list[Path]:
    """
    Discover all example test scripts in the auggie repo.

    Examples are organized in subdirectories. Each example that is testable
    has a test_example.py file that knows how to exercise and verify the example.
    This allows examples with servers or interactive components to define their
    own test logic (start server, make requests, verify, shutdown).
    """
    if not AUGGIE_REPO or not AUGGIE_REPO.exists():
        return []

    examples_dir = AUGGIE_REPO / "examples" / "python-sdk"
    if not examples_dir.exists():
        return []

    # Find all test_example.py files recursively in the python-sdk directory
    return sorted(examples_dir.rglob("test_example.py"))


# Get example test scripts for parametrization
_example_tests = discover_example_tests()


@pytest.mark.public_examples
@pytest.mark.integration
@pytest.mark.skipif(
    not AUGGIE_REPO or not AUGGIE_REPO.exists(),
    reason="This test requires AUGGIE_REPO point to a checkout of the auggie repo",
)
@pytest.mark.parametrize(
    "example_test",
    _example_tests if _example_tests else [None],
    ids=[s.parent.name for s in _example_tests] if _example_tests else ["no_examples"],
)
def test_public_example(example_test: Path | None):
    """
    Test that a public example works correctly with the current SDK.

    Each example in the public auggie repo has a test_example.py that knows
    how to exercise and verify that example. This test simply runs those
    test files and verifies they exit with code 0.
    """
    if example_test is None:
        pytest.fail(
            "AUGGIE_REPO is set but no test_example.py files found in examples/python-sdk/. "
            "This may indicate the auggie repo structure has changed."
        )

    if not example_test.exists():
        pytest.skip(f"Example test not found: {example_test}")

    returncode, stdout, stderr = run_example(example_test, timeout=120)

    assert returncode == 0, (
        f"\nExample test {example_test.parent.name}/test_example.py failed with exit code {returncode}:\n"
        f"\n--- stdout ---\n{stdout}\n"
        f"\n--- stderr ---\n{stderr}"
    )

