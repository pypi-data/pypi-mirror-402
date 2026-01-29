import os
import subprocess
import pytest

from travo.utils import git_get_origin


def test_get_origin_error(tmp_path: str) -> None:
    # Forces english locale for testing. See:
    # https://www.gnu.org/software/gettext/manual/html_node/Locale-Environment-Variables.html
    os.environ["LC_ALL"] = "C"

    os.chdir(tmp_path)
    with pytest.raises(RuntimeError, match="fatal: not a git repository"):
        # The directory is not a git repository
        git_get_origin()

    subprocess.run(["git", "init", "--quiet"], cwd=tmp_path)
    with pytest.raises(RuntimeError, match="error: No such remote 'origin'"):
        # The remote origin is not defined
        git_get_origin()
