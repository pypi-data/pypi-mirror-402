import datetime
import os.path
import pytest  # type: ignore
import random
import string
from typing import Callable, Iterator, List

from travo.gitlab import GitLab, GitLabTest, Group, Project, User, Resource
from travo.course import Course
from travo.jupyter_course import JupyterCourse
from travo.assignment import Assignment, Submission


@pytest.fixture
def gitlab_url() -> str:
    if "GITLAB_HOST" in os.environ and "GITLAB_80_TCP_PORT" in os.environ:
        gitlab_url = (
            f"http://{os.environ['GITLAB_HOST']}:{os.environ['GITLAB_80_TCP_PORT']}"
        )
    else:
        gitlab_url = "http://gitlab"
    return gitlab_url


@pytest.fixture
def gitlab() -> GitLab:
    forge = GitLabTest()
    forge.log.setLevel("DEBUG")
    return forge


@pytest.fixture
def test_run_id() -> str:
    """
    A (statistically) unique id for this test run
    """
    now = datetime.datetime.now().isoformat().replace(":", "_").replace("-", "_")
    return (
        now + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
    )


@pytest.fixture
def project_path(test_run_id: str) -> str:
    return f"student1/temporary-test-projet-{test_run_id}"


@pytest.fixture
def project_name(test_run_id: str) -> str:
    return f"temporary test projet created at {test_run_id}"


@pytest.fixture
def project(gitlab: GitLab, project_path: str, project_name: str) -> Iterator[Project]:
    project = gitlab.ensure_project(project_path, project_name)
    # TODO: factor out duplication with assignment_repo
    project.ensure_file("README.md")
    yield project
    gitlab.remove_project(project_path, force=True)


@pytest.fixture
def group_path(test_run_id: str) -> str:
    return f"temporary-test-group-{test_run_id}"


@pytest.fixture
def group_name(test_run_id: str) -> str:
    return f"temporary test group created at {test_run_id}"


@pytest.fixture
def group(gitlab: GitLab, group_path: str, group_name: str) -> Iterator[Group]:
    yield gitlab.ensure_group(group_path, group_name)
    gitlab.remove_group(group_path, force=True)


@pytest.fixture
def user_name() -> str:
    return "student1"


@pytest.fixture
def user(gitlab: GitLab, user_name: str) -> User:
    return gitlab.get_user(user_name)


@pytest.fixture
def other_user(gitlab: GitLab) -> User:
    return gitlab.get_user("student2")


@pytest.fixture
def fork_path(user_name: str, test_run_id: str) -> str:
    return f"{user_name}/temporary-forked-project-{test_run_id}"


@pytest.fixture
def fork_name(test_run_id: str) -> str:
    return f"temporary forked project created at {test_run_id}"


@pytest.fixture
def standalone_assignment_namespace(gitlab: GitLab) -> Group:
    return gitlab.ensure_group(
        path="TestGroup",
        name="Test Group",
        with_projects=False,
        visibility="public",
    )


@pytest.fixture
def standalone_assignment(
    gitlab: GitLabTest,
    user_name: str,
    standalone_assignment_namespace: Group,
    test_run_id: str,
) -> Iterator[Assignment]:
    repo = gitlab.ensure_project(
        path=f"TestGroup/TestAssignment-{test_run_id}",
        name=f"Test assignment {test_run_id}",
        visibility="public",
    )
    repo.ensure_file("README.md", branch="master")
    yield Assignment(
        forge=gitlab,
        log=gitlab.log,
        repo_path=repo.path_with_namespace,
        name=repo.path,
        instructors_path="TestGroup",
    )
    gitlab.remove_project(repo.path_with_namespace, force=True)


@pytest.fixture
def standalone_assignment_dir(tmp_path: str, test_run_id: str) -> str:
    return os.path.join(tmp_path, f"Assignment-{test_run_id}")


@pytest.fixture
def to_be_teared_down() -> Iterator[Callable[[Resource], None]]:
    """
    A factory fixture for planning the removal of resources upon tear down

    Currently projects and groups are supported.

    Example:

        >>> forge = get_fixture("gitlab")
        >>> to_be_teared_down = get_fixture("to_be_teared_down")
        >>> group = forge.ensure_group("MyTemporaryGroup")
        >>> to_be_teared_down(group)

    Reference: https://docs.pytest.org/en/6.2.x/fixture.html#factories-as-fixtures
    """
    resources: List[Resource] = []

    def _to_be_teared_down(resource: Resource) -> None:
        resources.append(resource)

    yield _to_be_teared_down

    # Tear down resources

    for resource in reversed(resources):
        forge = resource.gitlab
        assert isinstance(forge, GitLabTest)
        with forge.logged_as("root"):
            if isinstance(resource, Group):
                forge.remove_group(resource.id)
            else:
                assert isinstance(resource, Project)
                forge.remove_project(resource.id)


@pytest.fixture
def standalone_assignment_submission(
    standalone_assignment: Assignment,
) -> Iterator[Submission]:
    standalone_assignment.ensure_submission_repo(initialized=True)
    yield standalone_assignment.submission()
    standalone_assignment.forge.remove_project(standalone_assignment.submission_path())


@pytest.fixture
def course(gitlab: GitLabTest) -> Course:
    return Course(
        forge=gitlab,
        path="TestCourse",
        name="Test course",
        assignments_group_path="TestCourse/2020-2021",
        student_dir="~/TestCourse",
        group_submissions=False,
    )
    # course.log.setLevel("DEBUG")


@pytest.fixture
def rich_course(gitlab: GitLabTest, test_run_id: str) -> Course:
    # The course path and name could be randomized to enable parallel tests
    return Course(
        forge=gitlab,
        path=f"TestRichCourse-{test_run_id}",
        name=f"Test rich course {test_run_id}",
        session_path="2020-2021",
        assignments=["Assignment1", "Assignment2"],
        student_groups=["Group1", "Group2"],
        student_dir="~/RichCourse",
        group_submissions=False,
    )


@pytest.fixture
def rich_course_deployed(gitlab: GitLabTest, rich_course: Course) -> Iterator[Course]:
    with gitlab.logged_as("instructor1"):
        rich_course.forge.ensure_group(
            path=rich_course.path,
            name=rich_course.name,
            visibility="public",
        )

        assert rich_course.session_name is not None
        rich_course.forge.ensure_group(
            path=rich_course.assignments_group_path,
            name=rich_course.session_name,
            visibility="public",
        )

    yield rich_course

    with gitlab.logged_as("instructor1"):
        rich_course.forge.remove_group(rich_course.path)


@pytest.fixture
def rich_jupyter_course(gitlab: GitLabTest, test_run_id: str) -> JupyterCourse:
    pytest.importorskip("jupytext", reason="jupytext needs to be installed.")
    # The course path and name could be randomized to enable parallel tests
    return JupyterCourse(
        forge=gitlab,
        path=f"TestRichJupyterCourse-{test_run_id}",
        name=f"Test rich jupyter course {test_run_id}",
        session_path="2020-2021",
        assignments=["Assignment1", "Assignment2"],
        student_groups=["Group1", "Group2"],
        student_dir="~/RichJupyterCourse",
        group_submissions=False,
    )


@pytest.fixture
def course_assignment_group(course: Course) -> Group:
    course.forge.ensure_group(path=course.path, name=course.name, visibility="public")
    return course.forge.ensure_group(
        path=course.assignments_group_path,
        name=course.assignments_group_name,
        visibility="public",
    )


@pytest.fixture
def assignment_path(test_run_id: str) -> str:
    return f"temporary-assignment-{test_run_id}"


@pytest.fixture
def assignment_name(test_run_id: str) -> str:
    return f"temporary assignment created at {test_run_id}"


@pytest.fixture
def assignment_repo(
    course: Course,
    course_assignment_group: Group,
    assignment_path: str,
    assignment_name: str,
) -> Iterator[Project]:
    path = course.assignment_repo_path(assignment_path)
    project = course.forge.ensure_project(path, assignment_name)
    project.ensure_file("README.md", branch="master")
    yield project
    course.forge.remove_project(path, force=True)


@pytest.fixture
def submission_repo(
    course: Course, assignment_path: str, assignment_repo: Project
) -> Iterator[Project]:
    project = course.assignment(assignment_path).ensure_submission_repo()
    yield project
    course.forge.remove_project(project.path_with_namespace, force=True)


@pytest.fixture
def student_work_dir(course: Course) -> str:
    return course.ensure_work_dir()
