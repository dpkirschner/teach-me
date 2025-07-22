#!/usr/bin/env python3
"""Test runner script for the teach-me project."""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code."""
    print(f"🧪 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    if result.returncode == 0:
        print(f"✅ {description} passed")
    else:
        print(f"❌ {description} failed")

    print("-" * 50)
    return result.returncode


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run tests for teach-me project")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "api", "all"],
        default="unit",
        help="Type of tests to run",
    )
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", help="Run specific test file")

    args = parser.parse_args()

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    if args.file:
        cmd.append(args.file)
    elif args.type == "all":
        cmd.append("tests/")
    else:
        cmd.extend(["-m", args.type])

    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term-missing"])

    if args.verbose:
        cmd.append("-v")

    # Run tests
    exit_code = run_command(cmd, f"Running {args.type} tests")

    if args.coverage and exit_code == 0:
        print("\n📊 Coverage report generated in htmlcov/index.html")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
