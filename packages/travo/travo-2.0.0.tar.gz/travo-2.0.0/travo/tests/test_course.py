import i18n  # type: ignore
import pytest
import os
from travo.console_scripts import Travo
from travo.course import Course, missing_course
from travo.utils import working_directory, mark_skip_if_gitlab_not_running


def test_missing_course():
    """Test that missing_course() raises the expected ValueError."""
    with pytest.raises(ValueError, match="missing required argument: 'course'"):
        missing_course()


@pytest.mark.parametrize(
    "method_name", ["generate_assignment_content", "generate_assignment"]
)
def test_generate_assignment_no_file(course, method_name):
    """
    Verify that both generate_assignment_content() and generate_assignment()
    raise a FileNotFoundError when the instructor source files are not found.

    The test uses parameterization to avoid duplicate code.
    """
    # Choose an assignment name for which the instructor source directory does not exist.
    assignment_name = "NonExistingAssignment"
    expected_message = "is given as the instructor source files but is not found."

    # Retrieve the method from the course instance.
    method = getattr(course, method_name)

    # Both methods should raise the FileNotFoundError with the expected message.
    with pytest.raises(FileNotFoundError, match=expected_message):
        method(assignment_name)


@mark_skip_if_gitlab_not_running
@pytest.mark.parametrize("embed_option", [False, True])
def test_deploy(gitlab, gitlab_url, tmp_path, embed_option):
    """
    Test the creation and deployment of a new course. This test has no subcourses.
    """

    course_path = f"MyCourse-{embed_option}"
    course_name = f"My Course {embed_option}"

    # Create a dummy course
    course = Course(
        forge=gitlab,
        path=course_path,
        name=course_name,
        url=gitlab_url,
        student_dir=course_path,
        session_path="currentYear",
        expires_at="2030-01-01",
        script="./course.py",
    )

    # Initialise the course directory
    course_dir = os.path.join(tmp_path, course_path)
    Travo.quickstart(course_dir=course_dir, embed=embed_option)

    # Deploy the dummy course
    course.deploy(course_dir=course_dir, embed=embed_option)

    # Check that one of the created groups exists
    assert gitlab.get_group(f"{course_path}/currentYear") is not None

    # Tear down
    gitlab.remove_group(course.path, force=True)


@mark_skip_if_gitlab_not_running
def test_group_submission_true(rich_course):
    rich_course.group_submissions = True
    rich_course.forge.login()
    assert (
        rich_course.assignment("SubCourse/Assignment1").submission_name()
        == "Assignment1"
    )


def test_check_course_parameters(gitlab):
    i18n.set("locale", "en")
    course = Course(
        forge=gitlab,
        path="Info111",
        name="Info 111 Programmation Impérative",
        student_dir="~/ProgImperative",
        student_groups=["MI1", "MI2", "MI3"],
        subcourses=["L1", "L2", "L3"],
    )
    with pytest.raises(RuntimeError, match="Please specify your group among"):
        course.check_student_group("student_group", none_ok=False)
    with pytest.raises(RuntimeError, match="Please specify your subcourse among"):
        course.check_subcourse("subcourse", none_ok=False)

    assert course.check_subcourse("L1") is None
    assert course.check_subcourse(None, none_ok=True) is None


def test_course_release(course):
    i18n.set("locale", "en")

    with pytest.raises(RuntimeError, match="is not the root of a git repository"):
        course.release("Assignment3", path="../")


@mark_skip_if_gitlab_not_running
def test_course_share_with(course):
    i18n.set("locale", "en")

    with pytest.raises(RuntimeError, match="No submission on GitLab"):
        course.share_with(username="student1", assignment_name="Assignment1")


@mark_skip_if_gitlab_not_running
def test_course_collect(
    gitlab, rich_course_deployed, to_be_teared_down, user_name, tmp_path
):
    rich_course = rich_course_deployed
    assignments = rich_course.assignments
    student_groups = rich_course.student_groups
    # Deploy the course assignments ("Assignment1" and "Assignment2")
    with gitlab.logged_as("instructor1"):
        for group in student_groups:
            group_path = rich_course.assignments_group_path + "/" + group
            group_name = group
            rich_course.forge.ensure_group(
                path=group_path, name=group_name, visibility="public"
            )
            for assignment in assignments:
                path = rich_course.assignments_group_path + "/" + assignment
                project = rich_course.forge.ensure_project(
                    path=path, name=assignment, visibility="public"
                )
                project.ensure_file("README.md", branch="master")
                path = group_path + "/" + assignment
                project.ensure_fork(
                    path, assignment, visibility="public", initialized=True
                )

    assignment = rich_course.assignment("Assignment1", student_group="Group1")
    for student_name in ["student1", "student2"]:
        with gitlab.logged_as(student_name):
            to_be_teared_down(assignment.ensure_submission_repo(initialized=True))

    with gitlab.logged_as("instructor1"):
        with working_directory(tmp_path):
            rich_course.collect("Assignment1")
            assert os.path.isdir(os.path.join(tmp_path, "student1"))
            assert os.path.isdir(os.path.join(tmp_path, "student2"))

            rich_course.collect(
                "Assignment1",
                student_group="Group1",
                template="collect-{path}-Group1/{username}",
            )
            assert os.path.isdir("collect-Assignment1-Group1/student1")
            assert os.path.isdir("collect-Assignment1-Group1/student2")

            rich_course.collect(
                "Assignment1",
                student_group="Group2",
                template="collect-{path}-Group2/{username}",
            )
            assert not os.path.isdir("collect-Assignment1-Group2/student1")

            rich_course.collect_in_submitted(
                "Assignment1",
                student_group="Group1",
            )
            assert os.path.isdir("submitted/student1")
            assert os.path.isdir("submitted/student2")


@mark_skip_if_gitlab_not_running
def test_course_generate_and_release(gitlab, rich_course_deployed):
    rich_course = rich_course_deployed
    rich_course.group_submissions = True
    source_dir = "./source"
    release_dir = "./release"
    assignment_name = "Assignment42"

    # create a fake assignment
    os.makedirs(os.path.join(source_dir, assignment_name), exist_ok=True)
    with open(os.path.join(source_dir, assignment_name, "README.md"), "w") as file:
        file.write("Lorem ipsum.")
    assert os.path.isfile(os.path.join(source_dir, assignment_name, "README.md"))

    # set the directories
    rich_course.release_directory = release_dir
    rich_course.source_dir = source_dir
    rich_course.gitlab_ci_yml = "my gitlab-ci.yml file"

    with gitlab.logged_as("instructor1"):
        # generate the assignment before release
        rich_course.generate_assignment(assignment_name)

        assert os.path.isdir(release_dir)
        assert os.path.isdir(os.path.join(release_dir, assignment_name))
        assert os.path.isdir(os.path.join(release_dir, assignment_name, ".git"))
        assert os.path.isfile(
            os.path.join(release_dir, assignment_name, ".gitlab-ci.yml")
        )
        assert os.path.isfile(os.path.join(release_dir, assignment_name, ".gitignore"))

        rich_course.release(
            assignment_name,
            path=os.path.join(release_dir, assignment_name),
        )
