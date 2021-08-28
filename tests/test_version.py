""" Tests for top level package behavior and meta data. """
from subprocess import run, PIPE

from hero_quest import __version__


def test_version():
    """Check version of package matched project meta data."""
    poetry_version = run(
        "poetry version -s", stdout=PIPE, check=True, shell=True, text=True
    ).stdout.strip()
    assert __version__ == poetry_version
