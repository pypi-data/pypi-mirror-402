import os
import pytest

from travo.assignment import Assignment, Submission
from travo.utils import working_directory, mark_skip_if_gitlab_not_running


@mark_skip_if_gitlab_not_running
def test_collect(
    standalone_assignment: Assignment,
    standalone_assignment_submission: Submission,
    tmp_path: str,
) -> None:
    assignment = standalone_assignment
    student = standalone_assignment_submission.student

    with working_directory(tmp_path):
        assignment.collect()
    assert os.path.isdir(os.path.join(tmp_path, student))
    assert os.path.isfile(os.path.join(tmp_path, student, "README.md"))

    assignment.collect(template="foo/bar-{path}-{username}")
    assert os.path.isdir(f"foo/bar-{assignment.name}-{student}")


@pytest.mark.xfail
# @mark_skip_if_gitlab_not_running
def test_fetch_from_empty_submission_repo(
    standalone_assignment: Assignment, standalone_assignment_dir: str
) -> None:
    assignment = standalone_assignment
    assignment_dir = standalone_assignment_dir
    forge = assignment.forge
    repo = forge.get_project(assignment.repo_path)

    # "Accidently" create an empty submission repository with no fork relation
    my_repo = forge.ensure_project(
        path=assignment.submission_path(), name=assignment.submission_name()
    )
    assert my_repo.forked_from_project is None

    # Fetch + submit should recover smoothly
    assignment.fetch(assignment_dir)

    # Content should be recovered from the original repository
    assert os.path.isfile(os.path.join(assignment_dir, "README.md"))

    assignment.submit(assignment_dir)

    # The submission repository should now have a single branch named
    # master, and be a fork of the assignment repository
    my_repo = forge.get_project(path=assignment.submission_path())
    # There may be a race condition here; on at least one occasion
    # the branch was not yet available when running the tests locally
    (branch,) = my_repo.get_branches()
    assert branch["name"] == "master"
    assert my_repo.forked_from_project is not None
    assert my_repo.forked_from_project.id == repo.id

    # Tear down
    assignment.remove_submission(force=True)
