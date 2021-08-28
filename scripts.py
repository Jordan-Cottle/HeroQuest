#! /usr/bin/env python
""" Scripts for development """

import os
import re
from argparse import ArgumentParser
from subprocess import PIPE, STDOUT, CalledProcessError, run
from typing import Callable, Iterable, Mapping

from hero_quest import __version__

SOURCE_CODE_LOCATIONS = " ".join(["hero_quest", "tests", __file__])
PYPI = os.getenv("PYPI", "pypi")

assert (
    os.getenv("VIRTUAL_ENV") is not None
), "You really should be using a virtual environment"


def _run(command, quiet=False):

    if not quiet:
        print(command)

    try:
        output = run(
            command, check=True, shell=True, text=True, stdout=PIPE, stderr=STDOUT
        ).stdout
    except CalledProcessError as error:
        if not quiet:
            print(error.stdout)
        raise

    if not quiet:
        print(output)
    return output.strip()


PROJECT_NAME = _run("poetry version").split()[0]


def run_black(options: Iterable[str] = ("--check", "--diff")) -> None:
    """Execute black on all source code in project."""

    _run(f"black {' '.join(options)} {SOURCE_CODE_LOCATIONS}")


def run_pylint(options: Iterable[str] = ()) -> None:
    """Execute pylint on all source code in project."""

    _run(f"pylint {' '.join(options)} {SOURCE_CODE_LOCATIONS}")


def run_mypy(options: Iterable[str] = ()) -> None:
    """Execute mypy for all source code in project."""

    _run(f"mypy {' '.join(options)} {SOURCE_CODE_LOCATIONS}")


def check(tools: Iterable[str] = ("black", "mypy", "pylint")) -> None:
    """Check source code using static analysis"""

    static_analysis_tools = {
        "black": run_black,
        "pylint": run_pylint,
        "mypy": run_mypy,
    }

    for tool in tools:
        static_analysis_tools[tool]()


def test(options: Iterable[str] = ()) -> None:
    """Run all pytest."""

    _run(f"pytest {' '.join(options)}")


def get_git_tag():
    """Get the git tag for this commit.

    It's a bit of a mess with all of the possible different ways actions can check out the project.
    """

    git_ref = os.getenv("GITHUB_REF")

    # Use passed in git reference
    if git_ref is not None:
        git_tag = git_ref.split("/")[-1]
        if re.match(r"v\d+.\d+.\d+", git_tag):
            return git_tag

    # This enables the git describe command below to work since by default the information
    # required by `git describe` is not checkout out within the actions environment
    try:
        _run("git fetch --prune --unshallow", quiet=True)
    except CalledProcessError as error:
        # If we didn't need this, then ignore the error
        if error.returncode != 128:
            print(error.stdout)
            raise

    return _run("git describe --abbrev=0")


def check_version() -> None:
    """Assert that the latest git tag matches the poetry version."""

    current_version = _run("poetry version -s")
    print(f"Latest version: {current_version}")

    git_tag = get_git_tag()
    if git_tag != f"v{current_version}":
        raise ValueError(
            f"Git tag ({git_tag}) does not match poetry version ({current_version})"
        )

    if __version__ != current_version:
        raise ValueError(
            "Project version in __init__.py does not match pyproject.toml version: "
            f"{__version__} != {current_version}"
        )


def publish() -> None:
    """Publish project."""

    check_version()

    raise NotImplementedError("Publishing hasn't been implemented yet.")


COMMANDS: Mapping[str, Callable] = {
    "check": check,
    "black": run_black,
    "pylint": run_pylint,
    "mypy": run_mypy,
    "test": test,
    "check_version": check_version,
}

if __name__ == "__main__":
    parser = ArgumentParser(description="Local development scripts")

    parser.add_argument("command", help="command to check", choices=COMMANDS)

    args = parser.parse_args()

    print(args.command)

    COMMANDS[args.command]()
