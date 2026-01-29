import pytest
import os
import shutil
import i18n

os.environ["LANG"] = "fr_FR.UTF-8"
mdfile_content = (
    "---\n"
    "title: A basic example\n"
    "category: Documentation\n"
    "jupytext:\n"
    "  text_representation:\n"
    "    extension: .md\n"
    "    format_name: myst\n"
    "    format_version: 0.13\n"
    "    jupytext_version: 1.17.2\n"
    "kernelspec:\n"
    "  display_name: Python 3 (ipykernel)\n"
    "  language: python\n"
    "  name: python3\n"
    "---\n"
    "\n"
    "# This is a basic notebook example\n"
    "\n"
    "First we create a numpy random matrix\n"
    "\n"
    "```{code-cell} ipython3\n"
    "---\n"
    "nbgrader:\n"
    "  grade: false\n"
    "  grade_id: cell-5c950002ecf1172f\n"
    "  locked: true\n"
    "  schema_version: 3\n"
    "  solution: false\n"
    "  task: false\n"
    "---\n"
    "import numpy as np\n"
    "\n"
    "matrix = np.random.rand(10,10)\n"
    "matrix\n"
    "```\n"
)


@pytest.mark.parametrize(
    "method_name", ["generate_assignment_content", "generate_assignment"]
)
def test_generate_assignment_no_file(rich_jupyter_course, method_name):
    """
    Verify that both generate_assignment_content() and generate_assignment()
    raise a FileNotFoundError when the instructor source files are not found.

    The test uses parameterization to avoid duplicate code.
    """
    # Choose an assignment name for which the instructor source directory does not exist.
    assignment_name = "NonExistingAssignment"
    expected_message = "is given as the instructor source files but is not found."

    # Retrieve the method from the course instance.
    method = getattr(rich_jupyter_course, method_name)

    # Both methods should raise the FileNotFoundError with the expected message.
    with pytest.raises(FileNotFoundError, match=expected_message):
        method(assignment_name)


def test_pipeline(rich_jupyter_course):
    """
    Verify a standard pipeline with assignment generation and release,
    then, on student side, submission, then, on instructor side
    collection and grading.
    """
    course = rich_jupyter_course
    assignment_name = course.assignments[0]
    student_group = course.student_groups[1]
    source_path = "source/" + assignment_name
    source_name = source_path + "/" + assignment_name + ".md"
    release_path = "release/" + assignment_name

    i18n.set("locale", "fr")

    os.makedirs(source_path, exist_ok=True)
    if not os.path.exists(source_name):
        with open(source_name, "x") as fmd:
            fmd.write(mdfile_content)
    with course.forge.logged_as("instructor1", "aqwzsx(t3"):
        course.log.info(f"after login {course.forge.get_current_user().username=}")
        course.forge.ensure_git(dir=os.getcwd())
        course.forge.ensure_local_git_configuration(dir=os.getcwd())
        course.forge.git(["config", "--global", "init.defaultBranch", "master"])
        course.forge.git(["config", "--global", "pull.rebase", "false"])
        course.forge.ensure_group(
            path=course.path, name=course.name, visibility="public"
        )

        # Create the subgroup for the current session
        if course.session_path is not None:
            assert course.session_name is not None
            course.forge.ensure_group(
                path=course.path + "/" + course.session_path,
                name=course.session_name,
                visibility="public",
            )
        if course.subcourses is not None:
            # Create a subgroup on the forge for each subcourse
            path = course.path
            if course.session_path is not None:
                path += "/" + course.session_path
            for subcourse in course.subcourses:
                course.forge.ensure_group(
                    path=path + "/" + subcourse,
                    name=subcourse,
                    visibility="public",
                )

        course.generate_assignment(assignment_name=assignment_name)
        course.release(
            assignment_name=assignment_name, visibility="public", path=release_path
        )

    # student part
    with course.forge.logged_as("student1"):
        course.forge.login(
            username="student1", password="aqwzsx(t1", anonymous_ok=False
        )
        course.log.info(f"after login {course.forge.get_current_user().username=}")
        work_dir = course.ensure_work_dir()
        course.forge.login(
            username="student1", password="aqwzsx(t1", anonymous_ok=False
        )
        course.log.info(f"after relogin {course.forge.get_current_user().username=}")
        course.fetch(assignment_name=assignment_name)
        course.log.info(f"{work_dir=}")
        assert os.path.isdir(os.path.join(work_dir))
        assert os.path.isdir(os.path.join(work_dir, assignment_name))
        print(os.path.join(work_dir, assignment_name))
        print(os.listdir(os.path.join(work_dir, assignment_name)))
        assert any(
            fname.endswith(".md")
            for fname in os.listdir(os.path.join(work_dir, assignment_name))
        )
        # must run student_autograde to get .gradebook.db correct
        # go into student folder
        course.log.info(f"cwd: {os.getcwd()}")
        cwd = os.getcwd()
        course.log.info(f"os.chdir({os.path.join(work_dir, assignment_name)})")
        os.chdir(os.path.join(work_dir, assignment_name))
        course.log.info(f"cwd: {os.getcwd()}")
        course.student_autograde(
            assignment_name=os.path.basename(assignment_name),
            student="student1.lastname",
        )
        # go back in teacher folder
        os.chdir(cwd)
        course.log.info(f"os.chdir({cwd})")
        course.log.info(f"cwd: {os.getcwd()}")

        course.submit(assignment_name=assignment_name, student_group=student_group)

    with course.forge.logged_as("instructor1"):
        # course.log.info(f"methnum collect_in_submitted {assignment_name} {student_group}")
        course.collect_in_submitted(
            assignment_name=assignment_name, student_group=student_group
        )
        shutil.move(  # adapt to nbgrader format for student names
            f"./submitted/student1/{os.path.basename(assignment_name)}",
            f"./submitted/student1.lastname/{os.path.basename(assignment_name)}",
        )
        assert os.path.isdir("./submitted")
        student_ids = os.listdir("./submitted")
        course.log.info(f"in submitted: {student_ids=}")
        assert len(student_ids) > 0
        # there is no gitlab runners to autograde the tested submission
        # so we mimic the result by copying the autograded and feedback folder
        course.collect_autograded(
            assignment_name=assignment_name, student_group=student_group
        )
        # as they are no CI in the test GitLab we can mimic the effect of collect_autograded
        # doing a copy of the submitted folder
        shutil.copytree(
            "./submitted",
            "./autograded",
            dirs_exist_ok=True,
        )
        shutil.copytree(
            "./submitted",
            "./feedback_generated",
            dirs_exist_ok=True,
        )
        course.merge_autograded_db(
            assignment_name=os.path.basename(assignment_name),
            on_inconsistency="WARNING",
            back=False,
            new_score_policy="greater",
        )
        assert os.path.isdir("./feedback_generated")
        course.release_feedback(
            assignment_name=assignment_name,
            student_group=student_group,
            tag=student_ids[0],
        )
