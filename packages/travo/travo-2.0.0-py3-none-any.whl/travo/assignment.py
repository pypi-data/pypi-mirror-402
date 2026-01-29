from dataclasses import dataclass, field
import datetime
from logging import Logger
import os
import socket
import subprocess
import time
from typing import Any, Dict, List, Literal, Optional, Tuple, Union, cast
from .gitlab import (
    anonymous_user,
    Forge,
    Job,
    Project,
    Resource,
    ResourceRef,
    ResourceNotFoundError,
    User,
    Unknown,
)
from .i18n import _


@dataclass
class Assignment:
    forge: Forge
    log: Logger
    repo_path: str
    instructors_path: str
    name: str
    username: Optional[str] = None
    leader_name: Optional[str] = None
    assignment_dir: Optional[str] = None
    script: str = field(default="travo")
    jobs_enabled_for_students: bool = field(default=True)
    expires_at: Optional[str] = None
    _repo_cache: Optional[Project] = None

    def __post_init__(self) -> None:
        """
        Post initialisation

        It's a classic to have an accidental trailing '/' in the
        assignment name, typically added by the shell's directory name
        completion. For convenience and safety, this post
        initialisation removes it.

        TESTS:

            >>> forge = getfixture("gitlab")
            >>> assignment = Assignment(forge, forge.log, "", "", "Assignment1/")
            >>> assignment.name
            'Assignment1'
            >>> assignment = Assignment(forge, forge.log, "", "", "Dir/Assignment1/")
            >>> assignment.name
            'Dir/Assignment1'
        """
        self.name = self.name.removesuffix("/")

    @classmethod
    def from_url(
        cls,
        url: str,
    ) -> "Assignment":
        """
        Generate Assignment object from given URL.

        Parameters
        ----------
        url : str
            URL of the repository of the assignment. Can be local or remote
            (over https).

        Returns
        -------
        Assignment
            Assignment object pointing to upstream repository.

        """
        ref = ResourceRef(url=url)
        ref.forge.login()
        username = ref.forge.get_current_user().username

        repo = ref.forge.get_project(ref.path)

        if repo.namespace.full_path == username:
            # The url points to the submission repository. We recover the
            # assigment repository by following the fork relation.
            assert repo.forked_from_project is not None
            repo = ref.forge.get_project(repo.forked_from_project.id)

        instructors_path = os.path.dirname(repo.path_with_namespace)
        name = os.path.basename(repo.path_with_namespace)

        assert username is not None

        return Assignment(
            forge=ref.forge,
            log=ref.forge.log,
            repo_path=repo.path_with_namespace,
            name=name,
            instructors_path=instructors_path,
            _repo_cache=repo,
        )

    def repo(self) -> Project:
        if self._repo_cache is None:
            self._repo_cache = self.forge.get_project(self.repo_path)
        return self._repo_cache

    def get_username(self, username: Optional[str] = None) -> str:
        """
        Return the user name

        `username`, if provided
        Otherwise the assignment username, if defined
        Otherwise, the login of the user on the forge
        """
        if username is not None:
            return username
        if self.username is not None:
            return self.username
        self.forge.login(anonymous_ok=True)
        return cast(str, self.forge.get_current_user().username)

    ##########################################################################
    # Methods meant to be overriden for configuration

    def submission_path(self, username: Optional[str] = None) -> str:
        """
        Return the path on the forge of the student's submission for the
        given assignment

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> assignment = getfixture("standalone_assignment")
            >>> assignment.submission_path()
            'student1/TestAssignment-2...'
        """
        username = self.get_username(username)
        return username + "/" + os.path.basename(self.repo_path)

    def submission_name(self) -> str:
        """
        Return the name of the student's submission for the given assignment

        This method may typically be overriden by the course.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> assignment = getfixture("standalone_assignment")
            >>> assignment.submission_name()
            'Test assignment 2...'
        """
        return self.repo().name

    def submissions_forked_from_path(self) -> Union[str, Unknown]:
        """Return the path of the repository that submissions should be a fork of.

        By default, submissions are direct forks of the assignment
        repository (subclasses may have different rules). If
        leader_name is specified, then submissions are forks of the
        leader's submission which should exist.
        """
        if self.leader_name is not None:
            return self.submission_path(self.leader_name)
        return self.repo_path

    def submissions_forked_from_missing(self) -> None:
        assert False

    def submissions_search_from(self) -> Tuple[Project, int]:
        """Return a project `p` and an int `d` such that the submissions for
        this assignment are all the forks of `p` of depth `d`
        """
        return (self.repo(), 1)

    def get_submission_username(self, project: Project) -> Optional[str]:
        """Return the username for the given submission

        This method is also used in the folloging use case: let S be a
        submission which is a fork of this project. Is this project the
        submission of the leader, or the assignment? To this end, this
        method should return None in the latter case.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> assignment = getfixture("standalone_assignment")
            >>> assignment.get_submission_username(assignment.repo())
            >>> submission = getfixture("standalone_assignment_submission")
            >>> assignment.get_submission_username(submission.repo)
            'student1'
        """
        if project.path_with_namespace == self.repo_path:
            return None
        else:
            return project.get_creator().username

    ##########################################################################

    def submission_repo(self, username: Optional[str] = None) -> Project:
        return self.forge.get_project(self.submission_path(username=username))

    def has_submission(self, username: Optional[str] = None) -> bool:
        """
        Return whether the user already has a submission for this assignment

        Examples::

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> assignment = getfixture("standalone_assignment")
            >>> assignment.has_submission()
            False
            >>> my_repo = assignment.ensure_submission_repo()
            >>> assignment.has_submission()
            True
            >>> assignment.remove_submission(force=True)
            >>> assignment.has_submission()
            False
        """
        try:
            repo = self.submission_repo(username=username)
        except ResourceNotFoundError:
            return False
        # Warning: marked_for_deletion_at is deprecated in favor of
        # marked_for_deletion_on and is indeed not available in Gitlab 17.3.7.
        # see https://docs.gitlab.com/api/projects/#deprecated-attributes
        return (
            repo.extra.get("marked_for_deletion_at") is None
            and repo.extra.get("marked_for_deletion_on") is None
        )

    def ensure_submission_repo(
        self, leader_name: Optional[str] = None, initialized: bool = False
    ) -> Project:
        """
        Return the submission repository for this assignment

        Creating it and configuring it if needed.

        Beware that, by default, this does not initialize the repository content from
        the assignment upon creation.

        Example::

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> assignment = getfixture("standalone_assignment")
            >>> forge = assignment.forge
            >>> repo = assignment.repo()

            >>> my_repo = assignment.ensure_submission_repo()
            >>> my_repo.path
            'TestAssignment-20...'
            >>> my_repo.name
            'Test assignment 20...'
            >>> assert my_repo.forked_from_project.id == repo.id

            >>> my_repo = assignment.ensure_submission_repo()
            >>> share, = my_repo.shared_with_groups
            >>> assert share['group_full_path'] == assignment.instructors_path

        Tear down::

            >>> assignment.remove_submission(force=True)
        """
        # travo_raise_info "- Vérification que le devoir a un dépôt personnel configuré"
        repo = self.repo()
        instructors = self.forge.get_group(self.instructors_path)

        my_repo = repo.ensure_fork(
            path=self.submission_path(),
            name=self.submission_name(),
            forked_from_path=self.submissions_forked_from_path(),
            forked_from_missing=self.submissions_forked_from_missing,
            visibility="private",
            emails_disabled=True,
            default_branch=repo.default_branch,
            jobs_enabled=self.jobs_enabled_for_students,
            initialized=initialized,
        )
        if my_repo.default_branch == "null":
            web_url = my_repo.web_url
            self.log.error(
                f"""Dépôt personnel corrompu: {web_url}
                    Consultez le à l'adresse ci-dessus; s'il est vide, vous
                    pouvez le détruire avec la commande:

                    {self.script} forge_remove_project {my_repo.path_with_namespace}

                    Il sera reconstruit lors du prochain dépôt"""
            )

        if not any(
            share["group_id"] == instructors.id for share in my_repo.shared_with_groups
        ):
            self.log.info(
                f"- Configuration accès enseignants (groupe {instructors.path})"
            )
            try:
                my_repo.share_with(
                    instructors,
                    access=my_repo.AccessLevels.MAINTAINER,
                    expires_at=self.expires_at,
                )
            except KeyError:
                member_ids = [user["id"] for user in my_repo.get_members()]
                for instructor in instructors.get_members():
                    if instructor.id not in member_ids:
                        my_repo.share_with(
                            instructor,
                            access=my_repo.AccessLevels.MAINTAINER,
                            expires_at=self.expires_at,
                        )

        self.log.debug("- Configuration badge:")
        artifacts_url = (
            self.forge.base_url + "/%{project_path}/-/jobs/artifacts/%{default_branch}/"
        )
        link_url = artifacts_url + "file/feedback/scores.html?job=autograde"
        image_url = artifacts_url + "raw/feedback/scores.svg?job=autograde"

        my_repo.ensure_badge(name="Scores", link_url=link_url, image_url=image_url)

        self.log.info(f"- {_('your submission')}:")
        self.log.info(f"  {my_repo.web_url}")
        return my_repo

    def remove_submission(self, force: bool = False) -> None:
        """
        Remove the users' submission for this assignment
        """
        self.forge.remove_project(self.submission_path(), force=force)

    def ensure_clone_configuration(
        self,
        assignment_dir: str,
    ) -> None:
        """
        Ensure that the clone of the assignment is configured

        - 'origin' points to the submission repository for the assignment
        - 'user.name' and 'user.mail' are set

        This assumes that the given clone exists.

        Examples:

        We assume that the student has a clone of the assignment
        in his work directory for the course::

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> import subprocess
            >>> assignment      = getfixture("standalone_assignment")
            >>> assignment_dir  = getfixture("standalone_assignment_dir")
            >>> forge = assignment.forge
            >>> repo = assignment.repo()
            >>> print(forge.git(["clone", repo.http_url_with_base_to_repo(),
            ...                  assignment_dir],
            ...                  stdout=subprocess.PIPE,
            ...                  stderr=subprocess.STDOUT).stdout.decode())
            Clon... ...Assignment-20...

        After running this command::

            >>> assignment.ensure_clone_configuration(assignment_dir)

        the student is guaranteed to have a submission for the assignment::

            >>> path = assignment.submission_path()
            >>> project = forge.get_project(path)
            >>> project.path_with_namespace
            'student1/TestAssignment-20...'
            >>> print(forge.git(["config", "--local", "user.name"],
            ...                 capture_output=True,
            ...                 cwd=assignment_dir).stdout.decode(), end='')
            Étudiant de test pour travo
            >>> print(forge.git(["config", "--local", "user.email"],
            ...                 capture_output=True,
            ...                 cwd=assignment_dir).stdout.decode(), end='')
            travo@gmail.com

        And the remote of the clone will be set appropriately:

            >>> print(forge.git(["remote", "-v"],
            ...           capture_output=True,
            ...           cwd=assignment_dir,
            ...       ).stdout.decode(), end='')
            origin	http://.../student1/TestAssig...git (fetch)
            origin	http://.../student1/TestAssig...git (push)

        This is an idempotent operation:

            >>> assignment.ensure_clone_configuration(assignment_dir)

        Tear down::

            >>> assignment.remove_submission(force=True)
        """
        self.forge.ensure_local_git_configuration(assignment_dir)

        self.log.debug("Ensure that the remote of this repository is configured")
        project = self.ensure_submission_repo()
        result = self.forge.git(
            ["remote", "-v"], cwd=assignment_dir, capture_output=True
        )
        if project.http_url_to_repo in result.stdout.decode():
            self.log.debug("Personal remote already configured")
        else:
            self.log.info(
                "Reconfiguration du dépôt distant de la copie de travail: "
                f"{project.http_url_to_repo}"
            )
            self.forge.git(
                ["remote", "set-url", "origin", project.http_url_to_repo],
                cwd=assignment_dir,
            )

    def assignment_clone(self, assignment_dir: str) -> None:
        """
        Create the student's local clone of the assignment

        - from their submission if it exists
        - from the original repo otherwise

        If the user is logged in as `anonymous`, then the
        original repo is cloned. It needs to be public.
        """
        self.log.info(
            f"Création d'une copie de travail du devoir {self.name}"
            f"dans {assignment_dir}"
        )

        user = self.forge.get_current_user()
        source: Optional[Project] = None
        if user is not anonymous_user:
            try:
                source = self.submission_repo()
            except ResourceNotFoundError:
                pass
            else:
                # Support for accidental empty submission repository
                if not source.get_branches():
                    source = None

        if source is None:
            source = self.repo()
            self.log.info(f"  à partir du dépôt d'origine {source.http_url_to_repo}")
        else:
            self.log.info(
                f"  à partir de votre dépot personnel {source.http_url_to_repo}"
            )

        self.forge.git(
            ["clone", source.http_url_with_base_to_repo(), assignment_dir],
            anonymous_ok=True,
        )

    def check_assignment_dir(self, assignment_dir: str) -> None:
        """
        Check the assignment directory

        Raise an error if it does not exist or is dubious

        Tests:

            >>> import io, i18n
            >>> i18n.set('locale', 'en')
            >>> tmp_path = getfixture("tmp_path")
            >>> os.chdir(tmp_path)
            >>> assignment = getfixture("course").assignment("Assignment")

            >>> assignment.check_assignment_dir("Assignment")
            Traceback (most recent call last):
            ...
            RuntimeError: Missing assignment directory; fetch your assignment?

            >>> io.open("Assignment", 'w').close()
            >>> assignment.check_assignment_dir("Assignment")
            Traceback (most recent call last):
            ...
            RuntimeError: Corrupted assignment directory
            >>> os.remove("Assignment")

            >>> os.mkdir("Assignment")
            >>> assignment.check_assignment_dir("Assignment")
        """
        self.log.info(f"- Vérification de la présence du devoir {assignment_dir}")
        if not os.path.exists(assignment_dir):
            self.log.error(
                f"""Copie de travail {assignment_dir} non trouvée.
                    Vous pouvez la télécharger avec:

                   {self.script} fetch {assignment_dir}
                 """
            )
            raise RuntimeError(_("missing assignment directory"))
        if not os.path.isdir(assignment_dir):
            self.log.error(
                f"""Un fichier ou répertoire {assignment_dir} existe
                    mais n'est pas une copie de travail du devoir.
                    Déplacez ou supprimez le
                 """
            )
            raise RuntimeError(_("corrupted assignment directory"))

    def merge_from(
        self,
        source: Project,
        assignment_dir: str,
        branch: Optional[str] = None,
        content: str = "",
        on_failure: Literal["warning", "error"] = "error",
        anonymous_ok: bool = False,
    ) -> bool:
        """
        Try to merge content in the assignment directory

        Parameters
        ----------
        assignment_dir : str, optional
            Path to directory. The default is None.

        source: Project, optional
            The repository from which to merge content. The default is
            the assignment repository.

        branch: str, optional
            The branch of the source repository from which to merge content.
            The default is the default branch of the source repository.

        If the branch does not exist, report and return False.

        A commit is done before attempting the merge. In case of merge
        conflict, the assignment directory is rolled back to its
        original state, and a warning or error is emmitted depending
        on the value of `on_failure`.

        Return whether the merge was successful (or no merge was needed).

        Assumptions: `assignment_dir` is a clone of the assignment
        repository, with a local git configuration (see
        :ref:`gitlab.ensure_local_git_configuration`).

        Examples:

        We fetch an assignment which already has a submission:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture("gitlab")
            >>> to_be_teared_down = getfixture("to_be_teared_down")
            >>> assignment = getfixture("standalone_assignment")
            >>> submission_repo = assignment.ensure_submission_repo(initialized=True)
            >>> to_be_teared_down(submission_repo)
            >>> assignment_dir = getfixture("standalone_assignment_dir")

            >>> assignment.fetch(assignment_dir=assignment_dir)

            >>> assert os.path.isfile(os.path.join(assignment_dir, "README.md"))
            >>> assert not os.path.isfile(os.path.join(assignment_dir, "newfile"))

        we add a new file in the submission:

            >>> submission_repo.ensure_file("newfile")

        and check that, after merging from the modified submission,
        the new file is present locally:

            >>> assignment.merge_from(submission_repo, assignment_dir=assignment_dir)
            True

            >>> assert os.path.isfile(os.path.join(assignment_dir, "newfile"))

        Now let's create a submission for student2, add there a
        different file, and share it with the current student:

            >>> with gitlab.logged_as("student2"):
            ...    submission2_repo = assignment.ensure_submission_repo(
            ...        initialized=True)
            ...    to_be_teared_down(submission2_repo)
            ...    submission2_repo.ensure_file("newfile-student2")
            ...    assignment.share_with("student1")

        After merging from student2's submission, the new file is present locally:

            >>> assignment.merge_from(submission2_repo, assignment_dir=assignment_dir)
            True

            >>> assert os.path.isfile(os.path.join(assignment_dir, "newfile-student2"))
        """
        msg = _("merging", content=content)
        self.log.info(msg)

        if branch is None:
            branch = source.default_branch
        if not any(b["name"] == branch for b in source.get_branches()):
            self.log.info(_("no content", content=content))
            return True

        # self.check_assignment("$assignment")
        # Share this with fetch
        def git(args: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
            return self.forge.git(
                args, cwd=assignment_dir, anonymous_ok=anonymous_ok, **kwargs
            )

        save_msg = _("save before", what=msg)
        self.log.info("- " + save_msg)
        git(
            ["commit", "--all", "-m", save_msg],
            check=False,
        )
        self.log.info("- " + _("download"))
        git(["fetch", source.http_url_with_base_to_repo(), branch])
        # TODO: nice error message in case of failure
        # - Échec au téléchargement des mises à jour"
        # travo_raise_error f"Échec au téléchargement des {content}"
        self.log.info("- " + _("try to merge"))
        if git(["merge", "-m", msg, "FETCH_HEAD"], check=False).returncode != 0:
            git(["merge", "--abort"])
            message = _("abort conflicting merge", content=content)
            if on_failure == "warning":
                self.log.warning(message)
                return False
            else:
                assert on_failure == "error"
                raise RuntimeError(message)
        return True

    def fetch(
        self,
        assignment_dir: Optional[str] = None,
        username: Optional[str] = None,
        force: bool = False,
    ) -> None:
        """
        Fetch (i.e. download or update) the assignment

        The user must have an account on the forge:
        - to check whether the user has a submission for this assignment
        - to setup the local git configuration

        If logged in as `anonymous`, `fetch` ignores any personnal
        repository the user may have, skips the git configuration and
        won't fetch updates or erratas. We could try harder on this
        last point if there is a use case for it.

        Parameters
        ----------
        assignment_dir : str, optional
            Path to directory. By default, use the assignment
            directory defined in this assignment.

        username : str, optional
            If set, the assignment will be fetched from
            the submission of `username` instead

        force : bool, optional
            If True, create a backup of existing local repo and forces download
            of remote repo. The default is False.

        Returns
        -------
        None
        """
        self.forge.login(anonymous_ok=True)
        user = self.forge.get_current_user()

        def git(args: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
            return self.forge.git(args, cwd=assignment_dir, **kwargs)

        # check_assignment "$assignment"
        if assignment_dir is None:
            assignment_dir = self.assignment_dir
            assert assignment_dir is not None

        if not os.path.exists(assignment_dir):
            self.assignment_clone(assignment_dir)
        elif user is not anonymous_user and self.has_submission(username=username):
            submission_repo = self.submission_repo(username=username)
            self.ensure_clone_configuration(assignment_dir)
            success = self.merge_from(
                source=submission_repo,
                assignment_dir=assignment_dir,
                content=_("updates from submission"),
                on_failure="warning",
            )

            if not success:
                if force:
                    now = datetime.datetime.now().isoformat(sep="_", timespec="minutes")
                    # Something special needs to be done for "."
                    assert assignment_dir != "."
                    backup_dir = f"{assignment_dir}_{now}"
                    self.log.warning(
                        f"""La mise à jour n'a pas pu se faire du fait d'un conflit
                            Votre devoir local va être renommé en {backup_dir}
                            et une copie fraîche du sujet téléchargée à la place
                         """
                    )
                    os.rename(assignment_dir, backup_dir)
                    self.fetch(assignment_dir)
                else:
                    self.log.error(
                        "- La mise à jour n'a pas pu se faire du fait d'un conflit."
                    )
                    self.log.info(
                        f"""  Pour renommer votre devoir local et forcer la mise à jour,
                           utilisez l'option force; en ligne de commande:

                           {self.script} fetch ... --force
                        """
                    )
                    raise RuntimeError(_("fetch failed conflict"))

        # Fetch updates and errata
        self.forge.ensure_local_git_configuration(assignment_dir)
        repo = self.repo()
        self.merge_from(
            source=repo,
            assignment_dir=assignment_dir,
            content=_("updates"),
            anonymous_ok=True,
        )
        self.merge_from(
            source=repo,
            assignment_dir=assignment_dir,
            branch="errata",
            content=_("erratas"),
            on_failure="warning",
            anonymous_ok=True,
        )

    def submit(
        self, assignment_dir: Optional[str] = None, leader_name: Optional[str] = None
    ) -> None:
        """
        submit the given assignment
        """
        self.forge.login()
        if assignment_dir is None:
            assignment_dir = self.assignment_dir
            assert assignment_dir is not None

        self.log.info(f"Soumission de {assignment_dir}:")

        self.check_assignment_dir(assignment_dir)

        # in case of failure, raise: "Échec de la soumission"
        # Must be a failure connecting to gitlab
        user = self.forge.get_current_user()
        assert isinstance(user, User)

        submission_repo = self.ensure_submission_repo(leader_name=leader_name)
        url = submission_repo.http_url_with_base_to_repo()

        self.ensure_clone_configuration(assignment_dir)

        hostname = socket.gethostname()

        def git(args: List[str], **kwargs: Any) -> Any:
            return self.forge.git(args, cwd=assignment_dir, **kwargs)

        self.log.info("- Enregistrement des changements:")
        if (
            git(
                [
                    "commit",
                    "--all",
                    "-m",
                    f"Soumission depuis {hostname} par {user.name}",
                ],
                check=False,
            ).returncode
            != 0
        ):
            self.log.info("  Pas de changement à enregistrer")

        self.log.info("- Envoi des changements:")
        # With a newly created repository, submission_repo.default_branch may
        # still be master even if the assignment repository is using,
        # e.g. main. Force using the assignment repository's default branch.
        branch = self.repo().default_branch
        if git(["push", url, branch], check=False).returncode != 0:
            raise RuntimeError(_("submission failed"))
        # Force an update of origin/master (or whichever the origin default branch is)
        git(["update-ref", f"refs/remotes/origin/{branch}", branch])

        self.log.info(
            f"""- Soumission effectuée. Vous pouvez consulter votre dépôt:
             {url}
            """
        )

    def submission(self) -> "Submission":
        """
        Return the user's submission for this assignment

        Fails if the user has no submission
        """
        if not self.has_submission():
            raise RuntimeError(
                "Dépôt personnel inexistant sur GitLab\n"
                f"Merci de déposer `{self.name}` (avec submit)"
            )
        project = self.submission_repo()
        return Submission(project, assignment=self)

    def submissions(self) -> List["Submission"]:
        """
        Return all the submissions for this assignment

        The submissions are found among the forks or forks of forks.
        To distinguish between actual submissions and,
        e.g. intermediate forks used to model student groups, the
        current criteria is whether the fork resides outside of the
        namespace/group of the assignment.
        """
        # This is an instructor feature; leader_name is a student feature
        assert self.leader_name is None
        repo, fork_depth = self.submissions_search_from()
        forks = repo.get_forks(recursive=fork_depth, simple=True)
        return [
            Submission(fork, assignment=self)
            for fork in forks
            if not fork.namespace.full_path.startswith(repo.namespace.full_path)
        ]

    def is_released(self) -> bool:
        """
        Return whether this assignment has been released.

        (i.e. the assignment repository exists on the forge)

        Examples::

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> assignment = getfixture("standalone_assignment")
            >>> assignment.is_released()
            True

            >>> forge = getfixture("gitlab")
            >>> assignment = Assignment(
            ...     forge=forge,
            ...     log=forge.log,
            ...     repo_path="TestGroup/NotReleasedAssignment",
            ...     name="A not released assignment",
            ...     instructors_path="TestGroup",
            ... )
            >>> assignment.is_released()
            False
        """
        try:
            self.repo()
            return True
        except ResourceNotFoundError:
            return False

    def status(self) -> "SubmissionStatus":
        """
        Return the status of this assignment for its user
        """
        if self.has_submission():
            return self.submission().status()
        else:
            return SubmissionStatus(
                student=self.get_username(),
                status="released" if self.is_released() else "not released",
                autograde_status="none",
            )

    def collect_status(self) -> List["SubmissionStatus"]:
        """
        Return the status of all the submissions for this assignment
        """
        return [submission.status() for submission in self.submissions()]

    def collect(
        self,
        student: Optional[str] = None,
        template: str = "{username}",
        date: Optional[str] = None,
    ) -> None:
        """
        Collect the students' submissions

        Examples:

        Collect all students' submissions in the current directory::

            assignment.collect()

        Collect all students submissions, laying them out according to
        a specific template::

            assignment.collect(template="exchange/Course/submitted/MP2-{username}/{path}")
        """
        self.forge.login()
        bad_projects = []
        for submission in self.submissions():
            self.log.info(
                _(
                    "collect submission",
                    student=submission.student,
                    date=(date or "now"),
                )
            )
            path = template.format(username=submission.student, path=self.name)
            try:
                submission.repo.clone_or_pull(path, date=date)
            except subprocess.CalledProcessError:
                bad_projects.append(submission.repo.http_url_to_repo)
        if len(bad_projects) > 0:
            self.log.warning(_("submissions corrupted", n=len(bad_projects)) + ":")
        for url in bad_projects:
            self.log.warning(url)

    def share_with(
        self,
        username: str,
        access_level: Union[
            int, Resource.AccessLevels
        ] = Resource.AccessLevels.DEVELOPER,
    ) -> None:
        """
        Grant the given user access to the submission repository
        """
        try:
            repo = self.submission_repo()
        except ResourceNotFoundError:
            raise RuntimeError(
                _("no submission; please submit", assignment_name=self.name)
            )
        user = self.forge.get_user(username)
        repo.share_with(user, access=access_level)

    def ensure_main_submission(self, leader_name: str) -> None:
        """
        Ensure that the main submission is set for this submission.

        This is meant for team work on a submission. The principle is
        as follow: among all the submissions for the members of team,
        one is chosen as main submission; its owner is called leader
        of the team. Following a typical collaboration pattern with
        forges, all the others submissions are configured to be forks
        of the main submission.

        Example:

        Let's create an assignment with submissions of student1 and student2:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture("gitlab")
            >>> to_be_teared_down = getfixture("to_be_teared_down")
            >>> assignment = getfixture("standalone_assignment")
            >>> for student_name in ["student1", "student2"]:
            ...     with gitlab.logged_as(student_name):
            ...         to_be_teared_down(
            ...             assignment.ensure_submission_repo(initialized=True))

        student1 and student2 decide together that student2's
        submission will be the main submission (so student2 is called
        the team leader).

        student2 grants student1 access to their submission:

            >>> with gitlab.logged_as("student2"):
            ...     assignment.share_with("student1")

        student1 can now set student2's submission as main submission:

            >>> assignment.ensure_main_submission("student2")
            >>> assignment.submission().get_leader_and_team()
            ('student2', {'student2': ..., 'student1': ...})

        If there are more students in the team, the same needs to be
        done for each of them. They also probably want to grant access
        to their submissions to the other members of the team, but
        that's optional.

        We test that student1's submission is a fork of student2's
        submission, which itself is a fork of the assignment:

            >>> submission_repo = assignment.submission_repo()
            >>> leader_repo = assignment.submission_repo("student2")
            >>> assert (submission_repo.forked_from_project.path_with_namespace ==
            ...         leader_repo.path_with_namespace)
            >>> assert (leader_repo.forked_from_project.path_with_namespace ==
            ...         assignment.repo_path)
        """
        try:
            repo = self.submission_repo()
        except ResourceNotFoundError:
            raise RuntimeError(
                _("no submission; please submit", assignment_name=self.name)
            )
        if leader_name == self.get_username():
            raise RuntimeError(
                _("cannot set self as leader", assignment_name=self.name)
            )

        try:
            main_repo = self.submission_repo(username=leader_name)
        except ResourceNotFoundError:
            raise RuntimeError(
                _(
                    "no main submission",
                    assignment_name=self.name,
                    leader_name=leader_name,
                )
            )
        repo.ensure_is_fork_of(main_repo)


# Only consider running or finished jobs
# this excludes: 'canceled', 'skipped', 'manual',
job_status = ["failed", "created", "pending", "running", "success"]


def job_status_priority(job: dict) -> Tuple[int, str]:
    return job_status.index(job["status"]), job["created_at"]


@dataclass
class SubmissionStatus:
    student: str
    status: str  # Literal['not released', 'released', 'submitted', 'autograded']
    autograde_status: str
    leader_name: Optional[str] = None
    team: Optional[Dict[str, Project]] = None
    autograde_job: Optional[Job] = field(default=None, repr=False)
    submission: Optional["Submission"] = field(default=None, repr=False)

    def is_submitted(self) -> bool:
        return self.status in ["submitted", "autograded"]


@dataclass
class Submission:
    repo: Project
    assignment: Assignment
    student: str = field(default=cast(str, None))

    def __post_init__(self) -> None:
        student = self.repo.get_creator().username
        assert student is not None
        self.student = student

    def get_autograde_job(self) -> Optional[Job]:
        """
        Return autograde job

        This selects the jobs for the latest commit of the default
        branch, which are running or finished. If there is none,
        return None. Otherwise, return that which is the most advanced
        in the following order: "success" > "failure" > "running" >
        "created" > "failed", breaking ties with creation time.
        """
        # TODO remove old feedback
        # TODO deadline management:
        # - lookup appropriate commit instead of the latest as above
        #   https://docs.gitlab.com/ee/api/commits.html avec option "until"

        if not self.assignment.jobs_enabled_for_students:
            return None

        repo = self.repo
        try:
            branch = repo.get_branch(repo.default_branch)
        except Exception:  # would be nicer with a ResourceNotFoundError
            # This can actually fail with an empty repository
            return None

        commit_id = branch["commit"]["id"]
        forge = self.repo.gitlab

        jobs = forge.get_json(
            f"/projects/{repo.id}/jobs", data={"scope": job_status}, depaginate=True
        )
        jobs = [
            job
            for job in jobs
            if job["commit"]["id"] == commit_id
            and job["status"] not in ["canceled", "skipped", "manual"]
        ]

        if jobs:
            job = max(jobs, key=job_status_priority)
            return job

        return None

    def ensure_autograded(self, force_autograde: bool = False) -> Job:
        """
        Ensure that this submission was autograded by CI and feedback is available

        If `force_autograde` is set, a new autograde is forced.

        Return the job that computed the autograde
        """
        repo = self.repo
        forge = repo.gitlab
        if force_autograde:
            job = None
        else:
            status = self.status()
            job = status.autograde_job
            if status.status == "autograded":
                return job
            if job is not None:
                url = job["web_url"]
                if status.autograde_status == "success_no_artifact":
                    raise RuntimeError(
                        f"Correction automatique terminée mais sans artefact: {url}"
                    )
                forge.log.info(f"En attente de la correction automatique: {url}")

        if job is None:
            # Run a new pipeline
            # TODO: could trigger directly a job instead of a pipeline
            pipeline = forge.post(
                f"/projects/{repo.id}/pipeline", data={"ref": repo.default_branch}
            ).json()
            message = pipeline.get("message")
            if message == "403 Forbidden":
                raise RuntimeError(f"Accès «Maintainer» manquant: {self.repo.web_url}")
            if message is not None:
                raise RuntimeError(
                    f"Échec au lancement de la correction automatique ({message}): "
                    f"{repo.web_url}"
                )
            forge.log.info(
                "Lancement d'une nouvelle correction automatique:"
                f" {pipeline['web_url']}"
            )

        # Wait for autograde execution
        import tqdm  # type: ignore

        progress_bar = tqdm.tqdm(
            desc="",
            bar_format="En attente de la correction automatique ({desc}): {elapsed}",
        )
        progress_bar.display()

        if job is None:
            while pipeline["status"] in ["created", "pending", "running"]:
                progress_bar.desc = pipeline["status"]
                progress_bar.update()
                time.sleep(1)
                pipeline = forge.get_json(
                    f"/projects/{repo.id}/pipelines/{pipeline['id']}"
                )

            (job,) = forge.get_json(
                f"/projects/{repo.id}/pipelines/{pipeline['id']}/jobs"
            )

        while job["status"] in ["created", "pending", "running"]:
            progress_bar.desc = job["status"]
            progress_bar.update()
            time.sleep(1)
            job = forge.get_json(f"/projects/{repo.id}/jobs/{job['id']}")

        progress_bar.close()

        # Check job status
        if job["status"] != "success":
            forge.log.warning(f"Failed job: {job['web_url']}")
            raise RuntimeError("Échec de la correction automatique")
        if "artifacts_file" not in job:
            forge.log.warning(f"Job: {job['web_url']}")
            raise RuntimeError("Correction automatique terminée mais sans artefact")
        return job

    def force_autograde(self) -> Job:
        """
        Force the autograde and feedback of the submission by CI.
        Does not wait for the end of the job.

        Return the job that is computing the autograde.
        """
        repo = self.repo
        forge = repo.gitlab
        # Run a new pipeline
        # TODO: could trigger directly a job instead of a pipeline
        pipeline = forge.post(
            f"/projects/{repo.id}/pipeline", data={"ref": repo.default_branch}
        ).json()
        message = pipeline.get("message")
        if message == "403 Forbidden":
            raise RuntimeError(f"Accès «Maintainer» manquant: {self.repo.web_url}")
        if message is not None:
            raise RuntimeError(
                f"Échec au lancement de la correction automatique ({message}): "
                f"{repo.web_url}"
            )
        forge.log.info(
            f"Lancement d'une nouvelle correction automatique: {pipeline['web_url']}"
        )
        (job,) = forge.get_json(f"/projects/{repo.id}/pipelines/{pipeline['id']}/jobs")
        return job

    def get_leader_and_team(self) -> Tuple[str, Dict[str, Project]]:
        """
        Return the leader of the submission and the repositories of the team mates

        Output: a tuple whose first entry is the username of the leader and the
        second entry is a dictionary mapping usernames of team mates to their
        submissions.
        """
        # Fetch the repo and user name of the leader
        forked_from_project = self.repo.forked_from_project
        if forked_from_project is not None:
            leader_repo = forked_from_project
            leader_name = self.assignment.get_submission_username(leader_repo)
        else:
            leader_name = None
        if leader_name is None:
            leader_repo = self.repo
            leader_name = self.assignment.get_submission_username(leader_repo)
            assert leader_name is not None

        # Fetch the team information
        team = {leader_name: leader_repo}
        if leader_repo.forks_count > 0:
            for fork in leader_repo.get_forks(simple=True):
                username = self.assignment.get_submission_username(fork)
                assert username is not None
                team[username] = fork
        return (leader_name, team)

    def status(self) -> SubmissionStatus:
        status = "submitted"

        leader_name, team = self.get_leader_and_team()

        autograde_job = self.get_autograde_job()
        if autograde_job is not None:
            autograde_status = cast(str, autograde_job["status"])
            if not any(
                artifact["filename"] == "artifacts.zip"
                for artifact in autograde_job.get("artifacts", [])
            ):
                autograde_status = "success_no_artifact"
            if autograde_status == "success":
                status = "autograded"
        else:
            autograde_status = "none"

        return SubmissionStatus(
            student=self.student,
            leader_name=leader_name,
            team=team,
            autograde_status=autograde_status,
            autograde_job=autograde_job,
            status=status,
            submission=self,
        )
