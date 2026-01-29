"""This module implements a Course class which models a course, i.e. an object
containing all relevant information, such as:

* Course path/name (example: "MethNum")
* Course session (example: "2023-2024")
* List of subcourses (example: ["L1", "L2", "L3"])
* List of assignments (example: ["L2/Homework1", "L2/Homework2", "L2/Exam"])
"""

import logging
import os.path
import io
import shutil
from datetime import datetime
from dataclasses import dataclass, field
import re
import subprocess
from typing import List, Any, Dict, Optional, Tuple, Union, TYPE_CHECKING

from .utils import getLogger, run
from .gitlab import (
    Forge,
    Project,
    Resource,
    ResourceNotFoundError,
    unknown,
    Unknown,
    AnonymousUser,
)
from .assignment import Assignment
from .i18n import _

if TYPE_CHECKING:
    from . import dashboards


def missing_course() -> "Course":
    raise ValueError("missing required argument: 'course'")


"""
Characters that are forbidden in GitLab group names

https://docs.gitlab.com/ee/user/reserved_names.html#limitations-on-project-and-group-names # noqa: E501
https://www.digicert.com/kb/ssl-support/underscores-not-allowed-in-fqdns.htm

Test:

    >>> re.sub(forbidden_chars_in_name, " ", "a-s+d o_98#(*&$'sadf.)")
    'a-s+d o_98      sadf. '
    >>> re.sub(forbidden_chars_in_path, " ", "a-s+d o_98#(*&$'sadf.)")
    'a-s d o 98      sadf  '
"""
# to satisfy both gitlabs' and fqdn constraints
# in project name
forbidden_chars_in_name = re.compile(r"[^-+_. \w0-9]")
# in project path
forbidden_chars_in_path = re.compile("[^-A-Za-z0-9]")


class MissingInformationError(RuntimeError):
    """
    An operation could not be executed due to missing information.

    The missing information can be recovered from the `missing` attribute.
    """

    def __init__(self, message: str, missing: Dict[str, Any]) -> None:
        super().__init__(message)
        self.missing = missing


@dataclass
class CourseAssignment(Assignment):
    # Until Python 3.10 and keyword only fields, a subdataclass
    # can't add mandatory arguments. We fake `course` being
    # mandatory by providing a default factory raising an error.
    # https://medium.com/@aniscampos/python-dataclass-inheritance-finally-686eaf60fbb5

    course: "Course" = field(default_factory=missing_course)
    student_group: Optional[str] = None  # Meant to be mutable

    def submission_path_components(
        self, username: Optional[str] = None
    ) -> Tuple[str, ...]:
        """
        Return the components from which the path of the student's submission is built

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> course = getfixture("rich_course")
            >>> assignment = course.assignment("SubCourse/Assignment1")

            >>> assignment.submission_path_components()
            ('student1', 'TestRichCourse-...', '2020-2021', 'SubCourse', 'Assignment1')

            >>> assignment.submission_path_components(username="john.doo")
            ('john.doo', 'TestRichCourse-...', '2020-2021', 'SubCourse', 'Assignment1')

            >>> course.group_submissions = True
            >>> assignment.submission_path_components(username="john.doo")
            ('john-doo-travo', 'TestRichCourse-...', '2020-2021', 'SubCourse', 'Assignment1')

            >>> course.path='TestModule/TestCourse'
            >>> assignment.submission_path_components()
            ('student1-travo', 'TestModule', 'TestCourse', '2020-2021', 'SubCourse', 'Assignment1')

        Test for #116:

            >>> assignment = course.assignment("SubCourse/Assignment1/")
            >>> assignment.submission_path_components()
            ('student1-travo', 'TestModule', 'TestCourse', '2020-2021', 'SubCourse', 'Assignment1')
        """
        root = self.get_username(username)
        if self.course.group_submissions:
            root = re.sub(forbidden_chars_in_path, "-", root) + "-travo"
        components = [root, *self.course.path.split("/")]
        if self.course.session_path is not None:
            components.append(self.course.session_path)
        components.extend(self.name.split("/"))

        # Assert for #116
        assert components[-1], f"Assignment name {self.name} should not finish with a /"

        return tuple(components)

    def submission_path(self, username: Optional[str] = None) -> str:
        """
        Return the path on the forge of the student's submission for this assignment

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> course = getfixture("course")
            >>> course.assignment("SubCourse/Assignment1").submission_path()
            'student1/TestCourse-SubCourse-Assignment1'

            >>> course = getfixture("rich_course")
            >>> course.assignment("SubCourse/Assignment1").submission_path()
            'student1/TestRichCourse-...-2020-2021-SubCourse-Assignment1'
            >>> course.assignment("SubCourse/Assignment1",
            ...                   student_group="Group1").submission_path()
            'student1/TestRichCourse-...-2020-2021-SubCourse-Assignment1'


        More examples with grouped submissions:

            >>> course.group_submissions = True
            >>> assignment = course.assignment("SubCourse/Assignment1")
            >>> assignment.submission_path()
            'student1-travo/TestRichCourse-.../2020-2021/SubCourse/Assignment1'

            >>> assignment.submission_path(username="john.doo")
            'john-doo-travo/TestRichCourse-.../2020-2021/SubCourse/Assignment1'
        """
        components = self.submission_path_components(username)
        if self.course.group_submissions:
            return "/".join(components)
        else:
            return components[0] + "/" + "-".join(components[1:])

    def submission_name_components(self) -> Tuple[str, ...]:
        """
        Return the components from which the path of the student's submission is built

        Precondition: the user must be logged in, non anymously.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> course = getfixture("rich_course")
            >>> course.forge.login()
            >>> assignment = course.assignment("SubCourse/Assignment1")

            >>> assignment.submission_name_components()
            ('Étudiant de test pour travo',
             'Test rich course ...', '2020-2021', 'SubCourse', 'Assignment1')

            >>> from travo.i18n import _
            >>> import i18n
            >>> i18n.set('locale', 'fr')
            >>> course.group_submissions = True
            >>> assignment.submission_name_components()
            (...Étudiant de test pour travo...,
             'Test rich course ...', '2020-2021', 'SubCourse', 'Assignment1')

        Test:

            >>> name = assignment.submission_name_components()[0]
            >>> from travo.i18n import _
            >>> expected = _('submission group name',
            ...              name='Étudiant de test pour travo')
            >>> assert name == expected
        """
        user = self.forge.get_current_user()
        assert not isinstance(user, AnonymousUser)
        assert user.name is not None
        name = user.name

        # Replace forbidden characters by spaces
        name = re.sub(forbidden_chars_in_name, " ", name)

        if self.course.group_submissions:
            name = _("submission group name", name=name)
        components = [name, self.course.name]
        if self.course.session_name:
            components.append(self.course.session_name)
        components.extend(self.name.split("/"))
        return tuple(components)

    def submission_name(self) -> str:
        """
        Return the name of the student's submission for the given assignment

        Precondition: the user must be logged in, non anymously.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> course = getfixture("course")
            >>> course.forge.login()
            >>> course.assignment("SubCourse/Assignment1").submission_name()
            'Test course - SubCourse - Assignment1'

            >>> course = getfixture("rich_course")
            >>> course.forge.login()
            >>> course.assignment("SubCourse/Assignment1").submission_name()
            'Test rich course ... - 2020-2021 - SubCourse - Assignment1'
        """
        components = self.submission_name_components()
        if self.course.group_submissions:
            return components[-1]
        else:
            return " - ".join(components[1:])

    def submit(
        self,
        assignment_dir: Optional[str] = None,
        leader_name: Optional[str] = None,
        student_group: Optional[str] = None,
    ) -> None:
        # Temporarily set the student group for the time of the submission.
        # In the long run the logic for handling student groups should be
        # reworked to not be stateful anymore, and instead passed down as
        # argument to the repository creation
        old_student_group = self.student_group
        self.student_group = student_group
        try:
            super().submit(assignment_dir=assignment_dir, leader_name=leader_name)
        finally:
            self.student_group = old_student_group

    def ensure_submission_repo(
        self, leader_name: Optional[str] = None, initialized: bool = False
    ) -> Project:
        """
        Return the submission repository for this assignment

        Creating it and configuring it if needed.
        """
        if self.course.group_submissions:

            def ensure_group_recursive(
                path_components: Tuple[str, ...], name_components: Tuple[str, ...]
            ) -> None:
                """
                Ensure the existence of the nested GitLab groups holding the submission

                It is assumed that if the group or its super groups exist,
                they have the correct names and visibility
                """
                assert len(path_components) == len(name_components)
                if not path_components:
                    return
                path = "/".join(path_components)
                try:
                    self.course.forge.get_group(path)
                except ResourceNotFoundError:
                    ensure_group_recursive(path_components[:-1], name_components[:-1])
                    name = name_components[-1]
                    self.forge.ensure_group(path, name=name, visibility="private")

            ensure_group_recursive(
                self.submission_path_components()[:-1],
                self.submission_name_components()[:-1],
            )
        return super().ensure_submission_repo(
            leader_name=leader_name, initialized=initialized
        )

    def submissions_forked_from_path(self) -> Union[str, Unknown]:
        """Return the path of the repository that submissions should be a fork of.

        If the course has student groups and the student group is not
        specified, then the student repo should be a fork of some
        unknown fork of `repo`. We won't have enough information to
        create the student submission, but if it already exists, we
        can still fetch, submit, etc.

            >>> course = getfixture("rich_course")
            >>> course.assignment("SubCourse/Assignment1"
            ...                  ).submissions_forked_from_path()
            unknown
            >>> course.assignment("SubCourse/Assignment1",
            ...                   student_group="Group1").submissions_forked_from_path()
            'TestRichCourse-.../2020-2021/SubCourse/Group1/Assignment1'
        """
        if self.leader_name is not None:
            return super().submissions_forked_from_path()
        if self.course.student_groups is not None and self.student_group is None:
            return unknown
        return self.course.assignment_repo_path(
            self.name, student_group=self.student_group
        )

    def submissions_forked_from_missing(self) -> None:
        """Callback when forked_from must be known but is not"""
        assert self.course.student_groups is not None and self.student_group is None
        self.course.check_student_group(self.student_group)

    def submissions_search_from(self) -> Tuple[Project, int]:
        """Return a project `p` and an int `d` such that the submissions for
        this assignment are all the forks of `p` of depth `d`
        """
        path = self.submissions_forked_from_path()
        if path is unknown:
            return (self.repo(), 2)
        else:
            repo = self.forge.get_project(path)
            return (repo, 1)

    def get_submission_username(self, project: Project) -> Optional[str]:
        """Return the username for the given submission

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> course = getfixture("course")
            >>> assignment_path = getfixture("assignment_path")
            >>> assignment = course.assignment(assignment_path)
            >>> submission_repo = getfixture("submission_repo")

            >>> assignment.get_submission_username(assignment.repo())
            >>> assignment.get_submission_username(submission_repo)
            'student1'

        TODO: test with a rich course and the assignment fork for a student group
        """
        if project.path_with_namespace.startswith(self.course.assignments_group_path):
            return None
        else:
            return project.get_creator().username

    def is_generated(
        self,
    ) -> bool:
        """
        Return whether this assignment has been generated.

        i.e. the assignment directory `<release_dir>/<assignment_name>` exists
        and is a valid git repository.

        Examples:

            >>> tmp_path = getfixture("tmp_path")
            >>> os.chdir(tmp_path)
            >>> course = getfixture("rich_course")
            >>> assignment = course.assignment("Assignment1")
            >>> assignment.is_generated()
            False

        Generate a (fake) assignment and test again:

            >>> release_path = os.path.join("release", assignment.name)
            >>> os.makedirs(release_path)
            >>> assignment.is_generated()
            False

            >>> res = course.forge.git(["init"], cwd=release_path, anonymous=True)
            >>> assignment.is_generated()
            True
        """
        return os.path.exists(os.path.join(self.release_path(), ".git"))

    def source_path(
        self,
    ) -> str:
        """Return the source path for this assignment"""
        # basename() required for nbgrader default path in presence of subcourses
        assignment_basename = os.path.basename(self.name)
        source_dir = self.course.source_directory
        source_path = os.path.join(source_dir, assignment_basename)
        return source_path

    def release_path(
        self,
    ) -> str:
        """Return the release path for this assignment"""
        # basename() required for nbgrader default path in presence of subcourses
        assignment_basename = os.path.basename(self.name)
        release_dir = self.course.release_directory
        release_path = os.path.join(release_dir, assignment_basename)
        return release_path


@dataclass
class Course:
    """Model a course

    Example
    -------

        >>> from travo.gitlab import GitLab
        >>> GitLab.home_dir = getfixture('tmp_path')  # for CI

        >>> forge = GitLab("https://gitlab.dsi.universite-paris-saclay.fr")
        >>> course = Course(forge=forge,
        ...                 path="Info111",
        ...                 name="Info 111 Programmation Impérative",
        ...                 session_path="2022-2023",
        ...                 student_dir="~/ProgImperative",
        ...                 student_groups=["MI1", "MI2", "MI3"],
        ...                 subcourses=["L1", "L2", "L3"],
        ...                 expires_at="2023-12-31",
        ...                 mail_extension="universite-paris-saclay.fr")

    With this example, assignments will be stored in Info111/2022-2023,
    with one fork for each student group in, e.g. Info111/2022-2023/MI3

       >>> course.assignments_group_path
       'Info111...2022-2023'
       >>> course.assignments_group_name
       '2022-2023'
       >>> assignment = course.assignment("Semaine2", student_group="MI3")
       >>> assignment.repo_path
       'Info111...2022-2023/Semaine2'
       >>> assignment.submissions_forked_from_path()
       'Info111...2022-2023/MI3/Semaine2'

    If you wish to use another course layout, you can set the
    above variables directly.
    """

    forge: Forge
    """Git forge on which the course is stored."""
    path: str
    """Main group in Gitlab containing the entire course."""
    name: str
    """Name of the course."""
    student_dir: str = "./"
    """Local working directory for students."""
    assignments_group_path: str = ""
    """Path to the GitLab group containing the assignments.
    Defaults to `<path>/<session_path>` if `session_path` is provided
    and to `<path>` otherwise."""
    assignments_group_name: str = ""
    """Name of the GitLab group containing the assignments."""
    version: Optional[str] = None
    """Version of the course"""
    session_path: Optional[str] = None
    """Path to the group corresponding to the desired session on Gitlab."""
    session_name: Optional[str] = None
    """Will be defined as soon as session_path is."""
    assignments: Optional[List[str]] = None
    """List of assignments (optional); if not provided, the list of assignments
    is recovered from the projects in assignments_group_path."""
    subcourses: Optional[List[str]] = None
    """List of subcourses (optional)."""
    student_groups: Optional[List[str]] = None
    """List of student groups."""
    script: str = "travo"
    """Name of the command which will be executed."""
    url: Optional[str] = None
    """URL for the web page of the cours."""
    jobs_enabled_for_students: bool = False
    """Whether to enable continuous integration for the student submissions.

    Typical use case: automatic grading.
    """
    log: logging.Logger = field(default_factory=getLogger)
    """Logger for warnings, errors, etc."""
    mail_extension: str = ""
    """Domain name common to all students' email addresses."""
    expires_at: Optional[str] = None
    """Date at which instructors will lose access to the student repositories,
    as a YYYY-MM-DD date string."""
    group_submissions: bool = True
    """Enable group submission

    If True -- the default since Travo 1.0 -- the submissions of a student on the
    forge are grouped together by course and, when relevant by subcourse, and
    session. For example, the submission of the student with username `john.doo`
    for Assignment1 for the session 2023-2024 of the course Info101 will be
    stored in:

        john-doo-travo/Info101/2023-2024/Assignment1

    Otherwise, the submissions are stored flat in the student namespace. For
    example, the above submission will be stored in:

        john.doo/Info101-2023-2024-Assignment1

    The use of a bespoke group `john-doo-travo` with the dots in the name replaced
    by `-` is due to technical limitations in GitLab: user's namespace can't
    have subgroups, and GitLab pages have limitations when the path contains dots.
    """

    source_directory: str = "source"
    """
    `source_directory`: the name of the local directory -- relative to
    the course root directory -- holding the sources of the
    assignments. This variable is only meaningful when the assignments
    are generated from sources, not authored directly.

    `source_directory` and `release_directory` are the analogues of
    nbgrader's `CourseDirectory` configuration variables, with the same
    default values. For now this is mostly for documentation purposes
    and is only used by specific features of Travo, like the Jupyter
    based instructor dashboard. If nbgrader is used, then these
    variables must be set as well in nbgrader's configuration.
    """

    release_directory: str = "release"
    """
    `release_directory`: the name of the local directory -- relative
    to the course root directory -- holding the assignments ready to
    be released to the students.
    """
    ignore = [
        "__pycache__",
        ".DS_Store",
        "*~",
        "core*",
    ]
    """Files to be ignored in git repositories."""

    gitlab_ci_yml = None

    def __post_init__(self) -> None:
        # TODO: "Check that: name contains only letters, digits, emojis, '_', '.',
        # dash, space. It must start with letter, digit, emoji or '_'."
        if self.session_path is not None:
            self.assignments_group_path = os.path.join(self.path, self.session_path)
            if self.session_name is None:
                self.session_name = self.session_path

        if self.session_name is not None:
            self.assignments_group_name = self.session_name

        if not self.assignments_group_path:
            self.assignments_group_path = self.path
        if not self.assignments_group_name:
            self.assignments_group_name = os.path.basename(self.assignments_group_path)

        if self.version is None:
            if self.session_name is not None:
                self.version = self.session_name
            else:
                self.version = _("not versioned yet")

    def work_dir(
        self, assignment_name: Optional[str] = None, role: str = "student"
    ) -> str:
        """
        Return the absolute work directory for all (git) commands

        Examples:

        Let's create a dummy course::

            >>> forge = getfixture("gitlab")
            >>> course = Course(forge=forge,
            ...                 path="...", name="...",
            ...                 student_dir="~/ProgImperative")

        The work directory for a student, for example to clone a new
        assignment, is given by the `student_dir` attribute of the
        course, with the home dir ("~/") expanded:

            >>> course.work_dir(role="student")
            '...ProgImperative'

        (where ... is the student's home directory). To work inside a
        given assignment, for example to run `git push` or `git
        pull`, the work directory is::

            >>> course.work_dir(role="student", assignment_name="Week1")
            '...ProgImperative...Week1'

        When `student_dir` is set to ".", the user is in charge of
        being in the appropriate directory for the current operation.
        So this always return "." for the current directory::

            >>> course = Course(forge=forge,
            ...                 path="...", name="...",
            ...                 student_dir=".")
            >>> course.work_dir(role="student")
            '.'
            >>> course.work_dir(role="student", assignment_name="Week1")
            '.'

        .. note::
            This default implementation follows the convention that
            the work directory for an assignment is obtained by
            joining the assignment name to the root work directory.
            Some methods (e.g. assignment_clone) assume that this
            convention is followed and will need to be generalized
            should some course want to use another one.
        """
        assert role == "student"
        dir = self.student_dir
        if dir == ".":
            return "."
        if dir[:2] == "~/":
            dir = os.path.join(self.forge.home_dir, dir[2:])
        if assignment_name is not None:
            dir = os.path.join(dir, assignment_name)
        return dir

    def ensure_work_dir(self) -> str:
        """
        Ensure the existence of the student's work directory

        Return the work directory.

        Examples:

            >>> import os.path
            >>> course = getfixture("course")

            >>> work_dir = course.work_dir(); work_dir
            '...TestCourse'
            >>> assert not os.path.exists(work_dir)

            >>> course.ensure_work_dir()
            '...mp...TestCourse'

            >>> assert os.path.isdir(work_dir)

        This is an idempotent operation:

            >>> course.ensure_work_dir()
            '...mp...TestCourse'
            >>> assert os.path.isdir(work_dir)
        """
        work_dir = self.work_dir()
        if not os.path.isdir(work_dir):
            self.log.info(_("creating work dir", work_dir=work_dir))
            assert os.path.isabs(work_dir)
            os.makedirs(work_dir, exist_ok=True)

        return work_dir

    def check_student_group(
        self, student_group: Optional[str], none_ok: bool = False
    ) -> None:
        """
        Check that the given student group name is valid

        Raise on error; otherwise return nothing.
        """
        if self.student_groups is None or student_group in self.student_groups:
            return
        if none_ok and student_group is None:
            return
        message = ""
        if student_group is not None:
            message += _("unknown group", student_group=student_group) + "\n"
        message += (
            _("specify group", student_groups=", ".join(self.student_groups)) + "\n"
        )
        # message += _('help', script=self.script)
        missing = {"student_group": tuple(self.student_groups)}

        exception = MissingInformationError(message, missing=missing)
        raise exception

    def check_subcourse(self, subcourse: Optional[str], none_ok: bool = False) -> None:
        """
        Check that the given student group name is valid

        Raise on error; otherwise return nothing.
        """
        if self.subcourses is None or subcourse in self.subcourses:
            return
        if none_ok and subcourse is None:
            return
        message = ""
        if subcourse is not None:
            message += _("unknown subcourse", subcourse=subcourse) + "\n"
        message += _("specify subcourse", subcourses=", ".join(self.subcourses)) + "\n"
        # message += _('help', script=self.script)

        raise RuntimeError(message)

    def check_assignment(self, assignment_name: str) -> None:
        """
        Check whether assignment is a valid assignment

        This current default implementation does nothing.
        Alternatively, it could check whether the assignment exists on
        the forge.

        Courses may override it.
        """
        pass

    def assignment_repo_path(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> str:
        """
        Return the path on the forge for the repository holding the
        student version of the given assignment.

        If `group` is provided, then the path of the student_groups' fork
        thereof is returned instead.

        This method may typically be overriden by the course.

        Example:

            >>> course = getfixture("course")
            >>> course.assignment_repo_path("Assignment1")
            'TestCourse/2020-2021/Assignment1'
            >>> course.assignment_repo_path("Subcourse/Assignment1")
            'TestCourse/2020-2021/Subcourse/Assignment1'

            >>> course.assignment_repo_path("Assignment1", student_group="MI1")
            'TestCourse/2020-2021/MI1/Assignment1'
            >>> course.assignment_repo_path("Subcourse/Assignment1",
            ...                             student_group="MI1")
            'TestCourse/2020-2021/Subcourse/MI1/Assignment1'
        """
        result = [self.assignments_group_path]
        dirname = os.path.dirname(assignment_name)
        assignment_name = os.path.basename(assignment_name)
        if dirname:
            result.append(dirname)
        if student_group:
            result.append(student_group)
        result.append(assignment_name)
        return "/".join(result)

    def assignment_repo_name(self, assignment_name: str) -> str:
        """
        Return the name of the student repository for the given assignment

        This method may typically be overriden by the course.

        Example:

            >>> course = getfixture("course")
            >>> course.assignment_repo_name("SubCourse/Assignment1")
            'Assignment1'
        """
        return os.path.basename(assignment_name)

    Assignment = CourseAssignment

    def assignment(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        leader_name: Optional[str] = None,
        username: Optional[str] = None,
    ) -> CourseAssignment:
        """
        Return the assignment `assignment` for the given user

        By default, the user is the current user.
        """
        # The path of the original assignment; not the fork of the student groups
        repo_path = self.assignment_repo_path(assignment_name)
        self.check_student_group(student_group, none_ok=True)
        return self.Assignment(
            forge=self.forge,
            course=self,
            log=self.log,
            name=assignment_name,
            instructors_path=self.assignments_group_path,
            script=self.script,
            expires_at=self.expires_at,
            repo_path=repo_path,
            student_group=student_group,
            leader_name=leader_name,
            username=username,
            assignment_dir=self.work_dir(assignment_name),
            jobs_enabled_for_students=self.jobs_enabled_for_students,
        )

    def remove_submission(self, assignment_name: str, force: bool = False) -> None:
        """
        Remove the users' submission for this assignment
        """
        self.assignment(assignment_name).remove_submission(force=force)

    def fetch(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """
        fetch the given assignment
        """
        self.ensure_work_dir()
        assignment_dir = self.work_dir(assignment_name=assignment_name)
        return self.assignment(assignment_name, student_group=student_group).fetch(
            assignment_dir=assignment_dir, force=force
        )

    def submit(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        leader_name: Optional[str] = None,
    ) -> None:
        """
        submit the given assignment
        """
        self.check_assignment(assignment_name)
        the_assignment = self.assignment(
            assignment_name, student_group=student_group, leader_name=leader_name
        )
        assignment_dir = self.work_dir(assignment_name)
        the_assignment.submit(
            assignment_dir=assignment_dir,
            student_group=student_group,
            leader_name=leader_name,
        )

    def share_with(
        self,
        assignment_name: str,
        username: str,
        access_level: Union[
            int, Resource.AccessLevels
        ] = Resource.AccessLevels.DEVELOPER,
    ) -> None:
        return self.assignment(assignment_name).share_with(
            username=username, access_level=access_level
        )

    def release(
        self, assignment_name: str, visibility: str = "public", path: str = "."
    ) -> None:
        """
        Release the given assignment on the forge

        Parameters
        ----------
        assignment_name : str
             The name of an assignment
        visibility : "public" or "private"
             The visibility of the assignment repository(ies) on the forge
        path: str
             The directory holding the student version of the
             assignment, as a git repository

        This sets up the assignment repository on the forge, if it
        does not yet exist, and pushes all branches to this repository
        (`push --all`).

        In addition, for each student group, it sets up a fork of the
        above repository and pushes there.

        Note
        ----

        The default path may change to the release directory of the
        course. To release the current directory, it is recommended to
        set `path="."` explicitly.
        """

        self.check_assignment(assignment_name)
        self.log.info(
            f"Publish the assignment {assignment_name} with visibility {visibility}."
        )

        # TODO: use self.is_generated instead
        if not os.path.exists(os.path.join(path, ".git")):
            raise RuntimeError(_("not root of git repository", path=path))

        # travo_gitlab_remove_project "${repo}"
        attributes = dict(
            visibility=visibility,
            issues_enabled=False,
            merge_requests_enabled=False,
            container_registry_enabled=False,
            wiki_enabled=False,
            snippets_enabled=False,
            lfs_enabled=False,
        )

        repo_path = self.assignment_repo_path(assignment_name)
        name = self.assignment_repo_name(assignment_name)
        project = self.forge.ensure_project(path=repo_path, name=name, **attributes)
        try:
            project.unprotect_branch(project.default_branch)
        except RuntimeError:
            pass
        self.log.info(f"- Publishing to {repo_path}.")
        self.forge.git(
            ["push", "--all", project.http_url_with_base_to_repo()], cwd=path
        )

        if self.student_groups is None:
            return

        for student_group in self.student_groups:
            repo_path = self.assignment_repo_path(
                assignment_name, student_group=student_group
            )
            name = self.assignment_repo_name(assignment_name)
            self.log.info(
                f"- Publishing to the student group {student_group}' fork {repo_path}."
            )
            self.forge.ensure_group(
                os.path.dirname(repo_path), name=student_group, visibility=visibility
            )

            fork = project.ensure_fork(
                path=repo_path, name=name, jobs_enabled=False, **attributes
            )
            try:
                fork.unprotect_branch(project.default_branch)
            except RuntimeError:
                pass
            self.forge.git(
                ["push", "--all", fork.http_url_with_base_to_repo()], cwd=path
            )

    def remove_assignment(self, assignment_name: str, force: bool = False) -> None:
        """
        Remove the assignment on the forge (DANGEROUS!)

        This is an irreversible operation!
        """
        self.forge.login()
        self.check_assignment(assignment_name)
        self.log.info(f"Unpublish the assignment {assignment_name}.")

        if self.student_groups is not None:
            for student_group in self.student_groups:
                a = self.assignment(assignment_name, student_group=student_group)
                path = a.submissions_forked_from_path()
                assert path is not unknown
                try:  # Don't fail if this fork does not exist (any more)
                    repo = self.forge.get_project(path)
                except ResourceNotFoundError:
                    pass
                else:
                    self.forge.remove_project(path, force=force)

        repo = self.assignment(assignment_name).repo()
        # Only the main repo has pipelines set
        repo.remove_pipelines()
        self.forge.remove_project(repo.path_with_namespace, force=force)

    def collect(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        student: Optional[str] = None,
        template: str = "{username}",
        date: Optional[str] = None,
    ) -> None:
        """
        Collect the student's submissions

        Examples:

        Collect all students submissions in the current directory::

            course.collect("Assignment1")

        Collect all students submissions for a given student group,
        laying them out in nbgrader's format, with the student's group
        appended to the username:

            course.collect("Assignment1",
                           student_group="MP2",
                           template="exchange/Course/submitted/MP2-{username}/{path}")
        """
        self.assignment(assignment_name, student_group=student_group).collect(
            template=template
        )

    def collect_in_submitted(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> None:
        """
        Collect the student's submissions following nbgrader's standard organization.

        This wrapper for `collect`:
        - forces a login;
        - reports more information to the user (at a cost);
        - stores the output in the subdirectory `submitted/`,
          following nbgrader's standard organization.

        This is used by the course dashboard.
        """
        self.forge.login()
        submissions_status = self.assignment(
            assignment_name=assignment_name, student_group=student_group
        ).collect_status()
        self.log.info(f"Downloading submissions for {len(submissions_status)} students")
        template = os.path.join(
            "submitted", "{username}/" + f"{os.path.basename(assignment_name)}"
        )
        self.collect(
            assignment_name=assignment_name,
            student_group=student_group,
            template=template,
        )

    def ensure_instructor_access(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> None:
        """
        Ensure instructor access to the student repositories.

        """
        self.forge.login()
        path = self.assignment_repo_path(assignment_name, student_group)
        project = self.forge.get_project(path)
        forks = project.get_forks(recursive=True)
        for fork in forks:
            self.log.info(_("ensure instructor access", path=fork.path_with_namespace))
            instructors = self.forge.get_group(self.assignments_group_path)
            member_ids = [user["id"] for user in fork.get_members()]
            for instructor in instructors.get_members():
                if instructor.id not in member_ids:
                    fork.share_with(
                        instructor, access=fork.AccessLevels.MAINTAINER, expires_at=None
                    )

    def ensure_autograded(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        force_autograde: bool = False,
    ) -> None:
        """
        Ensure all submissions have been autograded

        The autograde is based on the latest commit from the
        submission's default branch. If that commit has not yet been
        autograded, a new autograde is triggered. With
        `force_autograde`, a new autograde is always triggered.
        """
        raise NotImplementedError

    def collect_autograded(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        prefix: str = "",
    ) -> None:
        """
        Collect the available autograded submissions

        The output is stored in the subdirectories `autograded` and
        `feedback_generated`, following nbgrader's standard
        organization.

        Only files files starting with the given prefix are extracted.
        """
        raise NotImplementedError

    def collect_autograded_post(
        self,
        assignment_name: str,
        tag: str = "*",
        on_inconsistency: str = "ERROR",
        new_score_policy: str = "only_empty",
        autograded: bool = True,
        null_score: bool = True,
    ) -> None:
        """
        After collecting all autograded submissions from an assignment,
        merge the grades in a database
        """
        raise NotImplementedError

    def generate_feedback(
        self, assignment_name: str, tag: str = "*", new_score_policy: str = "only_empty"
    ) -> None:
        """
        Generate the assignment feedback for the given student and propagate the scores
        in the student gradebooks.
        The student name can be given with wildcard.
        """
        raise NotImplementedError

    def release_feedback(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        tag: Optional[str] = "*",
    ) -> None:
        """
        After instructor correction, commit and push student grades of a given assignment
        in the student repos.
        The student group can be given optionally.
        The student name can be given with wildcard.
        """
        raise NotImplementedError

    @staticmethod
    def formgrader(
        assignment_name: Optional[str] = None, in_notebook: bool = False
    ) -> Any:
        """
        Launch grading interface
        """
        raise NotImplementedError

    def run(self, *args: str) -> subprocess.CompletedProcess:
        """Run an arbitrary shell command"""
        return run(args)

    def get_released_assignments(
        self, subcourse: Optional[str] = None, order_by: str = "created_at"
    ) -> List[str]:
        """
        Return the list of released assignments

        These are the projects that reside directly in the assignment
        group and that are visible to the user. They are returned as a
        list of paths, relative to that group.

        If subcourse is not `None`, then assignments are instead
        searched in the given subgroup.

        The assignments are sorted according to `order_by`. By
        default, this is by increasing creation date. See GitLab's
        documentation for the availables sorting orders:

        https://docs.gitlab.com/ee/api/groups.html#list-a-groups-projects
        """
        group_path = self.assignments_group_path
        if subcourse is not None:
            group_path += "/" + subcourse
            prefix = subcourse + "/"
        else:
            prefix = ""
        group = self.forge.get_group(group_path)
        projects = group.get_projects(
            simple=True, with_shared=False, order_by=order_by, sort="asc"
        )
        return [prefix + p.path for p in projects]

    def generate_assignment_reset(
        self,
        assignment_name: str,
    ) -> None:
        """
        Reset the assignment repository.

        Ensures the assignment's release path `<release_dir>/<assignment_name>`
        is the root of an empty git repository.
        """
        release_path = self.assignment(assignment_name).release_path()
        assignment_repo_path = self.assignment_repo_path(
            assignment_name=assignment_name
        )
        if os.path.isdir(release_path):
            # remove existing release folder
            shutil.rmtree(release_path)
        self.forge.login()
        try:
            project = self.forge.get_project(assignment_repo_path)
        except ResourceNotFoundError:
            # no existing repo: initialise empty
            os.makedirs(release_path, exist_ok=True)
            run(["git", "init"], cwd=release_path)
        else:
            # repo exists: clone and reset
            self.log.info(f"{project.http_url_with_base_to_repo()} already created")
            project.clone_or_pull(release_path)
            assert os.path.exists(release_path)
            run(["git", "rm", "-rf", "."], cwd=release_path, check=False)

    def generate_assignment_content(
        self,
        assignment_name: str,
        add_gitignore: bool = True,
        add_gitlab_ci: bool = True,
    ) -> None:
        """
        Generate the content of the assignment from the source.

        Fills the assignment's `release_path` based on the content of its
        `source_path`.
        This default implementation simply copies the content of
        `<assignment.source_path()>` to `<assignment.release_path()>`.
        Subclasses can implement more elaborate behaviour (e.g. removing
        answers).
        """
        assignment = self.assignment(assignment_name)

        source_path = assignment.source_path()
        if not os.path.isdir(source_path):
            raise FileNotFoundError(
                f"{source_path} is given as the instructor source files but is not"
                " found."
            )
        release_path = assignment.release_path()
        shutil.copytree(source_path, release_path, dirs_exist_ok=True)

        assignment_basename = os.path.basename(assignment_name)
        if add_gitlab_ci and self.gitlab_ci_yml is not None:
            io.open(os.path.join(release_path, ".gitlab-ci.yml"), "w").write(
                self.gitlab_ci_yml.format(assignment=assignment_basename)
            )

        if add_gitignore:
            io.open(os.path.join(release_path, ".gitignore"), "w").write(
                "\n".join(self.ignore) + "\n"
            )

    def generate_assignment_commit(
        self,
        assignment_name: str,
    ) -> None:
        """
        Stage and commit the contents of the assignment repository.
        """
        release_path = self.assignment(assignment_name).release_path()
        self.forge.ensure_local_git_configuration(dir=release_path)
        run(["git", "add", "."], cwd=release_path)
        run(
            [
                "git",
                "commit",
                "-n",
                "--allow-empty",
                f"-m '{assignment_name} {datetime.now()}'",
            ],
            cwd=release_path,
        )

    def deploy(
        self,
        course_dir: str = ".",
        share_with_instructors: bool = True,
        embed: bool = True,
    ) -> None:
        """
        Deploy the course structure on the forge

        Also reconfigure local repositories (`ComputerLab`, ...) to
        track their counterparts on the forge.

        Parameters
        ----------
        course_dir : str
            Local directory holding the course
        share_with_instructors : bool
            Publish the source teaching material on the forge as private repos for other instructors. Default: true.
        embed : bool
            Search for the ComputerLab as subdirectory of Instructors directory

        This is an idempotent operation: if some of the course
        structure already exists on the forge, it is updated by adding
        the missing bits.

        To undo, delete the course group on the forge, e.g. through
        the GitLab web interface (irreversible; use with care!).

        The local directory, typically, initialized with `travo
        quickstart` is expected to have the following structure:

        - `<course_dir>/(Instructors)/ComputerLab`: a git repository containing the
          course script `course.py`, typically together with
          documentation and assets on how to use the course as a
          student. Can be inside or outside of Instructors, see option `embed`.
        - (with the share option) `<course_dir>/Instructors`: a git
          repository holding the course material.

        The course structure on the forge is deployed according to the
        following conventions:

        - A public group `<course>`.
        - When relevant, public subgroups `<session>` and `<subcourse>`.
        - A public repository `<course>/ComputerLab`.
        - With the `share` option, a private project
          `<course>/Instructors` to host the source course
          material. It is initialized with the content of the local
          git repository `<course>/Instructors`, and is set as origin
          for this repository. If the course has subcourses, then this
          is instead done for each subcourse, replacing `Instructors`
          by the subcourse name.

        With this structure, the student version of an assignment is
        to be published as a repository:
        `<course>/<session>/<subcourse>/<student_group>/<assignment>`
        This is the role of `Course.release` which also creates the
        subgroups `<student_group>` as needed.
        """

        # Define ComputerLab local directory
        if embed:
            computerlab_dir = os.path.join(course_dir, "Instructors", "ComputerLab")
        else:
            computerlab_dir = os.path.join(course_dir, "ComputerLab")

        # Check if course.py has been modified : to be decommented once decided
        # course_diff = subprocess.run(
        #     ["git", "diff", "--compact-summary", "course.py"],
        #     cwd=computerlab_dir
        # ).stdout
        # if course_diff is None:
        #     raise RuntimeError("Please modify course.py before deploying.")

        # Create the main group for the course
        self.forge.ensure_group(path=self.path, name=self.name, visibility="public")

        # Create the subgroup for the current session
        if self.session_path is not None:
            assert self.session_name is not None
            self.forge.ensure_group(
                path=self.path + "/" + self.session_path,
                name=self.session_name,
                visibility="public",
            )

        if self.subcourses is not None:
            # Create a subgroup on the forge for each subcourse
            path = self.path
            if self.session_path is not None:
                path += "/" + self.session_path
            for subcourse in self.subcourses:
                self.forge.ensure_group(
                    path=path + "/" + subcourse,
                    name=subcourse,
                    visibility="public",
                )

            # Create a private repository for the source course
            # material for each subcourse
            if share_with_instructors:
                for subcourse in self.subcourses:
                    repository = self.forge.ensure_project(
                        path=os.path.join(self.path, subcourse),
                        name=subcourse,
                        visibility="private",
                    )
                    self.forge.git(
                        [
                            "remote",
                            "set-url",
                            "origin",
                            repository.http_url_with_base_to_repo(),
                        ],
                        cwd=os.path.join(course_dir, subcourse),
                    )
                    self.forge.git(["push"], cwd=os.path.join(course_dir, "subcourse"))
        else:
            # If there are no subcourses, create a single private
            # repository `Instructors` for the source course material
            if share_with_instructors:
                repository = self.forge.ensure_project(
                    path=os.path.join(self.path, "Instructors"),
                    name="Instructors",
                    visibility="private",
                )
                self.forge.git(
                    [
                        "remote",
                        "set-url",
                        "origin",
                        repository.http_url_with_base_to_repo(),
                    ],
                    cwd=os.path.join(course_dir, "Instructors"),
                )
                self.forge.git(["push"], cwd=os.path.join(course_dir, "Instructors"))

        # Create project ComputerLab
        repository = self.forge.ensure_project(
            path=os.path.join(self.path, "ComputerLab"),
            name="ComputerLab",
            visibility="public",
        )
        self.forge.git(
            ["remote", "set-url", "origin", repository.http_url_with_base_to_repo()],
            cwd=computerlab_dir,
        )

        # Commit and push edited ComputerLab/course.py
        self.forge.ensure_local_git_configuration(computerlab_dir)
        self.forge.git(
            ["commit", "--allow-empty", "-a", "-m", "first deploy of course.py"],
            cwd=computerlab_dir,
        )
        self.forge.git(["push"], cwd=computerlab_dir)

        # Give the url of the course on the forge to the user
        course_http_url = os.path.join(self.forge.base_url, self.path)
        self.log.info(f"Course successfully deployed at {course_http_url}")

    def generate_assignment(
        self,
        assignment_name: str,
        add_gitignore: bool = True,
        add_gitlab_ci: bool = True,
    ) -> None:
        assignment = self.assignment(assignment_name)
        source_path = assignment.source_path()
        if not os.path.isdir(source_path):
            raise FileNotFoundError(
                f"{source_path} is given as the instructor source files but is not"
                " found."
            )

        release_path = assignment.release_path()
        shutil.copytree(source_path, release_path, dirs_exist_ok=True)
        self.generate_assignment_reset(
            assignment_name=assignment_name,
        )
        self.generate_assignment_content(
            assignment_name=assignment_name,
            add_gitignore=add_gitignore,
            add_gitlab_ci=add_gitlab_ci,
        )
        self.generate_assignment_commit(
            assignment_name=assignment_name,
        )

    def student_dashboard(
        self, subcourse: Optional[str] = None, student_group: Optional[str] = None
    ) -> "dashboards.CourseStudentDashboard":
        """
        Return a student dashboard for the course for use in Jupyter

        This ensures first that the user is logged in (this part is not asynchronous).
        """
        from .dashboards import CourseStudentDashboard

        return CourseStudentDashboard(
            self, student_group=student_group, subcourse=subcourse
        )

    def instructor_dashboard(
        self, student_group: Optional[str] = None
    ) -> "dashboards.CourseInstructorDashboard":
        """
        Return an instructor dashboard for the course for use in Jupyter

        This ensures first that the user is logged in (this part is not asynchronous).
        """
        from .dashboards import CourseInstructorDashboard

        return CourseInstructorDashboard(self, student_group=student_group)
