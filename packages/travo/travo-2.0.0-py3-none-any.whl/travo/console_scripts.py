"""
Implementation of the console scripts for travo

- travo
- travo_echo_travo_token
"""

import os
from typing import Any, Optional
from travo import Assignment, GitLab
from travo.script import CLI
from travo.utils import git_get_origin, mark_skip_if_gitlab_not_running
from travo import Homework
from . import __version__


class Travo:
    """
    This class defines the command line interface for the travo script
    """

    version = __version__
    name = "travo"

    def info(
        self,
        url: str = ".",
        group: Optional[str] = None,
        copy: Optional[str] = None,
        fixup: bool = False,
    ) -> None:
        """
        Get, check and print information on the repository.

        The repository can be either the instructor's assignment or a student
        submission.
        If the former case, the information is iterated on all student copies.

        A homework.Homework object is created to get all forks corresponding to
        students' submissions (gitlab.Project objects).

        Command-line options:
            --group indicates the correction group to check (if any)
            --fixup tries to fix configuration mismatch (visibility, etc.)
            --copy indicate to work on the given copy (and not all)

        Parameters
        ----------
        url : str, optional
            Path to gitlab project containing homework. The default is ".".
        group : str, optional
            Indicates the correction group to check (if any). The default is None.
        copy : str, optional
            Indicate to work on the given copy (and not all). The default is None.
        fixup : bool, optional
            Tries to fix configuration mismatch (visibility, etc.). The default is
            False.

        Returns
        -------
        None
        """

        homework = Homework(url)
        if group is not None:
            homework.get_group(group)
        if copy is None:
            forks = homework.get_copies()
        else:
            homework.assignment = homework.project  # assume assigment
            forks = [homework.get_project(copy)]

        for fork in forks:
            homework.print_info(fork, fixup=fixup)

    def search_forks(
        self,
        url: str = ".",
        group: Optional[str] = None,
        fixup: bool = False,
        deep: bool = False,
    ) -> None:
        """
        Search for possible missing forks [instructor]

        For some reason, the fork relationship can be lost with gitlab, for instance
        the `fork` button was not used or fork was made private.

        Note: the search of forks can be slow.

        Command-line options:
            --group indicates the correction group to check (if any)
            --fixup tries to fix configuration mismatch (visibility, etc.)
            --deep indicates to search among more potential projects.

        Parameters
        ----------
        url : str, optional
            Path to gitlab project containing homework. The default is ".".
        deep : bool, optional
            Search among more potential projects. The default is False.
        group : str, optional
            Correction group to check (if any). The default is None.
        fixup : bool, optional
            Tries to fix configuration mismatch (visibility, etc.). The default is
            False.

        Returns
        -------
        None
        """

        homework = Homework(url)
        homework.assignment = homework.project  # assume assigment
        if group is not None:
            homework.get_group(group)

        forks = homework.project.get_possible_forks(deep=deep, progress=True)
        for fork in forks:
            homework.print_info(fork, fixup=fixup)

    def collect(self, url: str = ".", dir: str = "forks") -> None:
        """
        Collect the student repositories [instructor]

        Either a single copy, or all the students' copies if the instructor's
        assignment is used.

        Command-line options:
            --dir is the target directory.

        Parameters
        ----------
        url : str, optional
            Path to gitlab project containing homework. The default is ".".
        dir : str, optional
            Target directory. The default is "forks".

        Returns
        -------
        None
        """
        # TODO: merge with Assignment.collect_forks
        homework = Homework(url)
        forks = homework.get_copies()
        template = "{user}-{id}"

        for fork in forks:
            if fork.owner is None:
                continue
            path = os.path.join(
                dir, template.format(user=fork.owner.username, id=fork.id)
            )
            homework.print_info(fork)
            fork.clone_or_pull(path)

    def fetch(self, url: str = ".", assignment_dir: Optional[str] = None) -> None:
        """
        Fetch the assignment [student]

        Fetch assignment from URL, optionally specifying an assignment_dir:

            Travo.fetch(url)
            Travo.fetch(url, assignment_dir)

        Update an already fetched assignment:

            Travo.fetch(assignment_dir)

        Parameters
        ----------
        url : str, optional
            Path to gitlab project containing homework. The default is ".".
        assignment_dir : str, optional
            Local path to repository. The default is None.

        Returns
        -------
        None
        """
        if not url.startswith("http"):
            assert assignment_dir is None
            assignment_dir = url
            url = git_get_origin(assignment_dir)

        assignment = Assignment.from_url(url)

        if assignment_dir is None:
            assignment_dir = os.path.basename(assignment.repo_path)

        assignment.fetch(assignment_dir)

    def submit(self, assignment_dir: str = ".") -> None:
        """
        Submit the copy [student]

        Parameters
        ----------
        assignment_dir : str, optional
            Local path to repository. The default is ".".

        Returns
        -------
        None
        """

        url = git_get_origin(assignment_dir)
        assignment = Assignment.from_url(url)
        assignment.submit(assignment_dir)

    @staticmethod
    def formgrader(assignment: Optional[str] = None, in_notebook: bool = False) -> Any:
        """
        Launch nbgrader's formgrader
        """
        from travo.jupyter_course import JupyterCourse

        return JupyterCourse.formgrader(assignment, in_notebook)

    @staticmethod
    def validate(*files: str) -> None:
        """
        Launch nbgrader's validate
        """
        from travo.jupyter_course import JupyterCourse

        return JupyterCourse.validate(*files)

    @staticmethod
    def student_autograde(assignment_name: str, student: str) -> None:
        """
        Autograde the assignment for the given student

        This is mostly meant for usage in Continuous Integration

        This is currently only for Jupyter courses that use nbgrader.
        """
        from travo.jupyter_course import JupyterCourse

        course = JupyterCourse(GitLab("https://foo.bar"), "", "", "")
        course.student_autograde(assignment_name, student)

    @staticmethod
    def quickstart(
        course_dir: str,
        template: str = "simple-jupyter-course",
        embed: bool = True,
    ) -> None:
        """
        Help quick start a new course

        Parameters
        ----------
        course_dir : str
            Local directory holding the course
        template : str
            remote repository hosting the template demo for the course
        embed : bool
            Initialize ComputerLab as subdirectory of Instructors, default is `True`

        Examples:

            travo quickstart MyCourse template="simple-jupyter-course"
        """
        forge = GitLab("https://gitlab.com")
        instructors_dir = os.path.join(course_dir, "Instructors")
        if embed:
            computerlab_dir = os.path.join(instructors_dir, "ComputerLab")
        else:
            computerlab_dir = os.path.join(course_dir, "ComputerLab")
        course = os.path.join(computerlab_dir, "course.py")
        forge.git(
            [
                "clone",
                "https://gitlab.com/travo-cr/demos/" + template + "/Instructors",
                instructors_dir,
            ],
            anonymous=True,
        )
        forge.git(
            [
                "clone",
                "https://gitlab.com/travo-cr/demos/" + template + "/ComputerLab",
                computerlab_dir,
            ],
            anonymous=True,
        )
        source_dir = os.path.join(instructors_dir, "source")
        forge.log.info(
            f"Initialized `{source_dir}` for holding the sources of your course"
            " material"
        )
        forge.log.info(
            f"and `{computerlab_dir}` to make the course available for your students."
        )
        forge.log.info(f"Now edit {course} to configure your course,")
        forge.log.info(f"then run `cd {course_dir}`,")
        running_dir = os.path.join(".", "/".join(course.split("/")[1:]))
        forge.log.info(f"and run `{running_dir} deploy`.")


@mark_skip_if_gitlab_not_running
def test_travo(standalone_assignment: Assignment, tmp_path: str) -> None:
    url = standalone_assignment.repo().http_url_with_base_to_repo()
    assignment_dir = os.path.join(tmp_path, "Assignment")

    travo = Travo()
    travo.fetch(url, assignment_dir)

    travo.fetch(assignment_dir)
    travo.submit(assignment_dir)

    # Tear down
    standalone_assignment.remove_submission()


usage = """travo [fetch|submit] ...

For students

Fetch the latest version of the assignment:

    travo fetch <url> <dir>
    travo fetch <url>
    travo fetch <dir>

Submit the assignment:

    travo submit <dir>

where `<url>` is the url of the Git repository holding the
assignment, and <dir> is the (to be created) local working copy
for the assignment. By default, the working copy is created in a
subdirectory of current working directory with basename matching
that of the assignment.

More help:

    travo --help
"""


def travo() -> None:
    """
    Entrypoint for the main `travo` console script
    """
    CLI(Travo(), usage=usage)


def travo_echo_travo_token() -> None:
    """
    Entrypoint for the `travo-echo-travo-token console script

    This script is used as GIT_ASKPASS callback to provide the gitlab
    authentication token to git
    """
    print(os.environ["TRAVO_TOKEN"])
