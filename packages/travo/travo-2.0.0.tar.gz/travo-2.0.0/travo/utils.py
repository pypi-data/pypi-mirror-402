import subprocess
import urllib
import urllib.parse
from typing import cast, Any, Iterator, Sequence, Optional
import logging
import colorlog  # type: ignore
import os
from contextlib import contextmanager
import pytest

_logger: Optional[logging.Logger] = None

mark_skip_if_gitlab_not_running = pytest.mark.skipif(
    "GITLAB_HOST" not in os.environ and "GITLAB_ROOT_PASSWORD" not in os.environ,
    reason="the gitlab instance is not running or not configured",
)


def skip_if_gitlab_not_running() -> None:
    if "GITLAB_HOST" not in os.environ and "GITLAB_ROOT_PASSWORD" not in os.environ:
        pytest.skip("the gitlab instance is not running or not configured")


def getLogger() -> logging.Logger:
    global _logger
    if _logger is None:
        handler = colorlog.StreamHandler()
        handler.setFormatter(
            colorlog.ColoredFormatter("%(log_color)s%(levelname)s:%(name)s:%(message)s")
        )
        _logger = cast(logging.Logger, colorlog.getLogger("travo"))
        _logger.addHandler(handler)
    return _logger


def urlencode(s: str) -> str:
    """
    Encode a string `s` for inclusion in a URL

    Parameters
    ----------
    s : str
        Input string to encode.

    Returns
    -------
    str
        Encoded string.

    Examples
    --------
        >>> urlencode("foo/bar!")
        'foo%2Fbar%21'
    """
    return urllib.parse.urlencode({"": s})[1:]


def run(
    args: Sequence[str], check: bool = True, **kwargs: Any
) -> subprocess.CompletedProcess:
    """
    A wrapper around subprocess.run

    - logs command with pretty printing
    - set check=True by default
    """
    # Backport capture_output from Python 3.6
    if kwargs.get("capture_output"):
        del kwargs["capture_output"]
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.STDOUT
    getLogger().info("Running: " + " ".join(args))
    return subprocess.run(args, check=check, **kwargs)


def git_get_origin(cwd: str = ".") -> str:
    """
    Return the origin of the current repository

    Parameters
    ----------
    cwd : str, optional
        Path to current working repository. The default is ".".

    Raises
    ------
    RuntimeError
        Raises if `git remote get-url origin` yields return code other than zero.

    Returns
    -------
    str
        URL of the repository at origin.

    Examples
    --------
        >>> import os
        >>> tmp_path = getfixture('tmp_path')
        >>> result = subprocess.run(["git", "init"], cwd=tmp_path)
        >>> result = subprocess.run(["git", "remote", "add", "origin",
        ...                          "https://xxx.yy/truc.git"], cwd=tmp_path)
        >>> git_get_origin(tmp_path)
        'https://xxx.yy/truc.git'
        >>> os.chdir(tmp_path)
        >>> git_get_origin()
        'https://xxx.yy/truc.git'
    """
    result = run(
        ["git", "remote", "get-url", "origin"],
        check=False,
        capture_output=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.decode().strip())
    lines = result.stdout.decode().splitlines()
    assert lines
    return cast(str, lines[0])


@contextmanager
def working_directory(path: str) -> Iterator:
    """
    A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.

    Example:

        >>> tmp_path = getfixture("tmp_path")
        >>> dirname = "this-is-a-long-directory-name"

    This creates a directory in `tmp_path`, instead of in the current
    working directory:

        >>> with working_directory(tmp_path):
        ...     os.mkdir(dirname)

        >>> assert os.path.exists(os.path.join(tmp_path, dirname))
        >>> assert not os.path.exists(dirname)
    """
    prev_cwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
