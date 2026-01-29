import contextlib
import importlib
import io
import glob
import os.path
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import time
import base64
from typing import Any, Iterator, Optional, List, Tuple, Union, TYPE_CHECKING

if importlib.util.find_spec("nbgrader") is None:
    raise ImportError(
        "Cannot find nbgrader. "
        "jupyter_course needs optional dependencies. "
        "Please install travo with 'pip install travo[jupyter]'."
    )

from .assignment import SubmissionStatus
from .course import Course
from travo.i18n import _
from .utils import run

if TYPE_CHECKING:
    from . import dashboards


@contextlib.contextmanager
def TrivialContextManager() -> Iterator[Any]:
    yield


# Currently just a dummy grade report, just for making some tests
grade_report = """
<?xml version="1.0" encoding="UTF-8" ?>
   <testsuites id="20140612_170519" name="New_configuration (14/06/12 17:05:19)"
               tests="225" failures="1262" time="0.001">
      <testsuite id="codereview.cobol.analysisProvider" name="COBOL Code Review"
                 tests="45" failures="17" time="0.001">
         <testcase id="codereview.cobol.rules.ProgramIdRule"
              name="Use a program name that matches the source file name" time="0.001">
            <failure
            message="PROGRAM.cbl:2 Use a program name that matches the source file name"
            type="WARNING">
WARNING: Use a program name that matches the source file name
Category: COBOL Code Review – Naming Conventions
File: /project/PROGRAM.cbl
Line: 2
      </failure>
    </testcase>
  </testsuite>
</testsuites>
"""

# Not used at this stage; for the record should we eventually use
# GitLab's quality reports for reporting grades
quality_report = """
            [
              {
                "description": "'unused' is assigned a value but never used.",
                "fingerprint": "7815696ecbf1c96e6894b779456d330e",
                "severity": "minor",
                "location": {
                  "path": "lib/index.js",
                  "lines": {
                    "begin": 42
                  }
                }
              }
            ]
"""

jupyterhub_host = "https://jupyterhub.ijclab.in2p3.fr"


def jupyter_lab_in_hub(
    path: str, debug: bool = False, background: bool = False
) -> Optional[str]:
    """
    Launch a sub-notebook server within the current notebook server on JupyterHub

    The host jupyter server should have jupyter_server_proxy installed.

    Caveat:
    - The hub URL is currently hardcoded ... sorry
      It's only used to provide the user with the url to follow
    - On our hub, websockets are non functional. So that's ok for e.g.
      formgrading with nbgrader, but not for running notebooks
    """
    token = "".join(chr(random.randint(97, 122)) for i in range(48))
    os.environ["JUPYTER_TOKEN"] = token

    prefix = os.environ["JUPYTERHUB_SERVICE_PREFIX"]
    port = 8000
    log_level = "ERROR"  # Ignored by jupyter notebook ????

    url = f"{jupyterhub_host}{prefix}proxy/absolute/{port}/{path}?token={token}"
    if not background:
        print("======================================================================")
        print("Launching formgrader; please open this URL to access it:")
        print(url)
        print("Close the server with 'Control-C' and 'y' when done")
        print("======================================================================")

    command = [
        "jupyter",
        "lab",
        "--no-browser",
        f"--LabApp.base_url={prefix}proxy/absolute/{port}/",
        f"--port={port}",
        f"--log-level={log_level}",
        "--LabApp.allow_remote_access=True",
    ]
    if background:
        subprocess.Popen(command)
        return url
    else:
        subprocess.run(command, capture_output=not debug)
        return None


def jupyter_notebook(path: str) -> None:
    """
    Launch a new Jupyter notebook server

    This works both in the command line or within a JupyterHub
    """
    if "JUPYTERHUB_SERVICE_PREFIX" in os.environ:
        jupyter_lab_in_hub(path)
    else:
        subprocess.run(
            [
                "jupyter",
                "notebook",
                "--ip=127.0.0.1",
                f"--NotebookApp.default_url={path}",
            ]
        )


class JupyterCourse(Course):
    ignore = Course.ignore + [
        "feedback",
        ".ipynb_checkpoints*.pyc",
    ]

    def __post_init__(self) -> None:
        super().__post_init__()
        self.ignore_nbgrader = self.ignore + [".*"]

    @staticmethod
    def validate(*files: str) -> None:
        """
        Validates the given notebook files with nbgrader
        """
        errors = 0
        failures = 0
        for file in files:
            if file.endswith(".md"):
                testfile = f".test.{file}.ipynb"
                run(["jupytext", file, "-o", testfile])
                file = testfile
            else:
                testfile = ""
            assert file.endswith(".ipynb")
            command = ["nbgrader", "validate"]
            process = subprocess.Popen(
                [*command, file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                if "ERROR" in line:
                    errors += 1
                if "FAILED" in line:
                    failures += 1
                print(line, end="")
            if testfile:
                os.remove(testfile)
        if failures + errors:
            print(_("validation failed", errors=str(errors), failures=str(failures)))
            exit(failures + errors)

    def convert_from_md_to_ipynb(self, path: str) -> list[str]:
        """
        Convert all markdown notebooks with nbgrader metadata into ipynb notebooks

        Return the list of produced ipynb notebooks
        """
        import jupytext  # type: ignore

        ipynbs = []

        for mdname in glob.glob(os.path.join(path, "*.md")):
            with io.open(mdname, encoding="utf-8") as fd:
                if "nbgrader" not in fd.read():
                    self.log.debug(
                        "Skip markdown file/notebook with no nbgrader metadata:"
                        f" {mdname}"
                    )
                    continue
            ipynbname = mdname[:-3] + ".ipynb"
            ipynbs.append(ipynbname)
            self.log.info(f"Converting {mdname} to {ipynbname}")
            notebook = jupytext.read(mdname)
            jupytext.write(notebook, ipynbname)
            # run(["jupytext", mdname, "--to ipynb"])
            self.log.info("Updating cross-links to other notebooks (.md->.ipynb)")
            with open(ipynbname, "r") as file:
                filedata = file.read()
            filedata = filedata.replace(".md)", ".ipynb)")
            # Write the file out again
            with open(ipynbname, "w") as file:
                file.write(filedata)
            # run(["jupytext", "--sync", ipynbname])
        return ipynbs

    def convert_from_ipynb_to_md(
        self, path: str, ipynbs: list[str] | None = None
    ) -> None:
        import jupytext  # type: ignore

        if ipynbs is None:
            ipynbs = glob.glob(os.path.join(path, "*.ipynb"))

        for ipynbname in ipynbs:
            mdname = ipynbname[:-6] + ".md"
            self.log.info(f"Converting {ipynbname} to {mdname}")
            notebook = jupytext.read(ipynbname)
            jupytext.write(notebook, mdname, fmt="md:myst")
            self.log.info("Updating cross-links to other notebooks (.ipynb->.md)")
            with open(mdname, "r") as file:
                filedata = file.read()
            filedata = filedata.replace(".ipynb)", ".md)")
            # Write the file out again
            with open(mdname, "w") as file:
                file.write(filedata)
            # run(["jupytext", "--sync", ipynbname])

    def generate_assignment_content(
        self,
        assignment_name: str,
        add_gitignore: bool = True,
        add_gitlab_ci: bool = True,
    ) -> None:
        """
        Generate the student version of the given assignment
        """
        assignment = self.assignment(assignment_name)
        source_path = assignment.source_path()
        if not os.path.isdir(source_path):
            raise FileNotFoundError(
                f"{source_path} is given as the instructor source files but is not"
                " found."
            )
        ipynbs = self.convert_from_md_to_ipynb(path=source_path)
        release_path = assignment.release_path()
        with tempfile.TemporaryDirectory() as tmpdirname:
            db = os.path.join(release_path, ".gradebook.db")
            # If assignment comes from a git repo, save the .git directory
            gitdir = os.path.join(release_path, ".git")
            is_git = os.path.exists(gitdir)
            if is_git:
                tmpgitdir = os.path.join(tmpdirname, ".git")
                self.log.info("Sauvegarde de l'historique git")
                shutil.move(gitdir, tmpgitdir)
            assignment_basename = os.path.basename(assignment_name)
            try:
                run(
                    [
                        "nbgrader",
                        "generate_assignment",
                        "--force",
                        f"--CourseDirectory.source_directory={self.source_directory}",
                        f"--CourseDirectory.release_directory={self.release_directory}",
                        assignment_basename,
                        f"--db='sqlite:///{db}'",
                    ]
                )
                # Convert back temporary ipynb notebooks to markdown
                released_ipynbs = [
                    ipynb.replace(source_path, release_path) for ipynb in ipynbs
                ]
                self.convert_from_ipynb_to_md(path=release_path, ipynbs=released_ipynbs)
                for ipynb in released_ipynbs:
                    Path(ipynb).unlink()

            except subprocess.CalledProcessError:
                pass
            finally:
                self.log.info("Restauration de l'historique git")
                # In case the target_path has been destroyed and not recreated
                os.makedirs(release_path, exist_ok=True)
                shutil.move(tmpgitdir, gitdir)
        # Remove temporary ipynb notebooks
        for ipynb in ipynbs:
            Path(ipynb).unlink()
        if add_gitlab_ci and self.gitlab_ci_yml is not None:
            io.open(os.path.join(release_path, ".gitlab-ci.yml"), "w").write(
                self.gitlab_ci_yml.format(assignment=assignment_basename)
            )
        if add_gitignore:
            io.open(os.path.join(release_path, ".gitignore"), "w").write(
                "\n".join(self.ignore) + "\n"
            )

    def format_studentid(self, student_id: str) -> Tuple[str, str, str]:
        """Format student id to nbgrader format if needed"""
        if student_id.count(".") == 1:
            firstname, lastname = student_id.split(".")
        elif student_id.count(".") == 2:
            group, firstname, lastname = student_id.split(".")
        elif student_id.count(".") == 0:  # assuming short login
            firstname = student_id[0]
            lastname = student_id[1:]
        else:
            raise ValueError(
                f"Unknown student format {student_id}. "
                "Must be group.firstname.lastname or firstname.lastname or flastname (short login)."
            )
        firstname = firstname.lower()
        lastname = lastname.lower()
        if student_id.count(".") >= 1:
            email_login = f"{firstname}.{lastname}"
        else:
            email_login = student_id
        if self.mail_extension is None:
            email = ""
        else:
            email = f"{email_login}@{self.mail_extension}"
        return firstname, lastname, email

    def nbgrader_update_student_list(
        self, tag: str = "", submitted_directory: str = "submitted"
    ) -> None:
        """Piece of code specific to methnum, to be more developed and generalized..."""
        student_list = run(
            ["nbgrader", "db", "student", "list"], capture_output=True
        ).stdout.decode("utf-8")
        for student_id in os.listdir(submitted_directory):
            if tag.replace("*", "") not in student_id:
                continue
            if student_id in student_list:
                continue
            firstname, lastname, email = self.format_studentid(student_id)
            run(
                [
                    "nbgrader",
                    "db",
                    "student",
                    "add",
                    f"{student_id}",
                    f"--first-name={firstname}",
                    f"--last-name={lastname}",
                    f"--email={email}",
                ]
            )

    def get_nbgrader_config(self) -> List[str]:
        nbgrader_config = [
            "--CourseDirectory.ignore=" + str(self.ignore_nbgrader),
        ]
        if not os.path.isfile("nbgrader_config.py"):
            nbgrader_config.append("--db=sqlite:///.gradebook.db")
            nbgrader_config.append("--CourseDirectory.submitted_directory=submitted")
        return nbgrader_config

    def autograde(
        self, assignment_name: str, tag: str = "*", force: bool = False
    ) -> None:
        """
        Run nbgrader autograde for the assignment of the given student.
        Student submissions must follow nbgrader convention and be in `submitted` directory.
        Student notebooks can be either md or ipynb files.

        The student name can be given with wildcard.

        Examples:

        Autograde all students submissions in the submitted directory::

            course.autograde("Assignment1")

        Autograde submissions for a given student:

            course.autograde("Assignment1", tag="firstname.lastname")
        """
        run(["nbgrader", "--version"])
        assignment = os.path.basename(assignment_name)
        nbgrader_config = self.get_nbgrader_config()
        self.nbgrader_update_student_list(tag=tag)
        self.convert_from_md_to_ipynb(assignment)
        run(
            [
                "nbgrader",
                "autograde",
                *nbgrader_config,
                os.path.basename(assignment_name),
                f"--student={tag}",
                "--db=sqlite:///.gradebook.db",
            ]
            + (["--force"] if force else [])
        )

    def local_autograde(self, assignment_name: str, tag: str = "*") -> None:
        """
        Run student_autograde for an assignment of a given student locally in the corresponding
        submitted folders. Autograded folders are created in the `autograded` folder.

        Student submissions must follow nbgrader convention and be in `submitted` directory.
        Student submissions may be a mix of md or ipynb files, with local .gradebook.db files.
        Gradebooks are directly merged into the instructor .gradebook.db file.

        Already present marks in the instructor gradebook are NOT overwritten.

        The student name can be given with wildcard.

        Examples:

        Autograde all students submissions in the submitted directory::

            course.local_autograde("Assignment1")

        Autograde submissions for a given student:

            course.local_autograde("Assignment1",
                                    tag="firstname.lastname")
        """
        from .nbgrader_utils import Gradebook

        run(["nbgrader", "--version"])

        assignment = os.path.basename(assignment_name)
        self.nbgrader_update_student_list(tag=tag)
        for student_id in os.listdir("submitted"):
            if tag.replace("*", "") not in student_id:
                continue
            self.convert_from_md_to_ipynb(
                os.path.join("submitted", student_id, assignment)
            )
        self.convert_from_md_to_ipynb(
            os.path.join(self.source_directory, os.path.basename(assignment))
        )

        # First, must include the assignment in the instructor gradebook
        if not os.path.exists(".gradebook.db"):
            run(
                [
                    "nbgrader",
                    "db",
                    "init",
                    "--db='sqlite:///.gradebook.db'",
                ]
            )
        gb = Gradebook("sqlite:///.gradebook.db")
        if assignment not in [a.name for a in gb.assignments]:
            self.log.info(f"Adding assignment {assignment} to the gradebook")
            run(
                [
                    "nbgrader",
                    "generate_assignment",
                    f"--CourseDirectory.source_directory={self.source_directory}",
                    f"--CourseDirectory.release_directory={self.release_directory}",
                    os.path.basename(assignment),
                    "--db='sqlite:///.gradebook.db'",
                    "--force",
                ]
            )
            run(
                [
                    "nbgrader",
                    "db",
                    "assignment",
                    "add",
                    assignment,
                    "--db='sqlite:///.gradebook.db'",
                ]
            )
        gb = Gradebook("sqlite:///.gradebook.db")
        submissions = gb.assignment_submissions(assignment)
        self.log.warning(
            f"Already have submisisons for {[s.student.id for s in submissions]}. "
            f"Use force=True to re-autograde them."
        )

        # cwd = os.getcwd()
        # os.makedirs("autograded", exist_ok=True)
        for submitted_dir in sorted(
            glob.glob(f"submitted/{tag}/{os.path.basename(assignment_name)}")
        ):
            student = submitted_dir.split("/")[1]
            autograded_dir = os.path.join(
                "autograded", student, os.path.basename(assignment_name)
            )
            # Instructor may be in a state with a mix of student repos and
            # manually downloaded submitted folders in case of misfunctionning
            # of the forge integration.
            is_autograded = False
            # Check already have submission
            if student in [s.student.id for s in submissions]:
                is_autograded = True
            # Check if .gradebook.db in submitted folder
            if os.path.exists(os.path.join(submitted_dir, ".gradebook.db")):
                if not os.path.exists(autograded_dir):
                    shutil.copytree(
                        submitted_dir,
                        autograded_dir,
                        dirs_exist_ok=True,
                        symlinks=False,
                    )
            # Check if autograded .gradebook.db is not empty (original instructor state)
            if os.path.exists(os.path.join(autograded_dir, ".gradebook.db")):
                source = Gradebook(
                    f"sqlite:///{os.path.join(autograded_dir, '.gradebook.db')}"
                )
                if len(source.assignment_submissions(assignment)) > 0:
                    is_autograded = True

            if not is_autograded:
                self.autograde(
                    assignment_name=os.path.basename(assignment_name),
                    tag=student,
                    force=True,
                )
            else:
                self.collect_autograded_post(
                    assignment_name=os.path.basename(assignment_name),
                    tag=student,
                    on_inconsistency="ERROR",
                    new_score_policy="only_empty",
                )

    def forge_autograde(
        self,
        assignment_name: str,
        tag: str = "*",
        new_score_policy: str = "only_empty",
    ) -> None:
        """
        Autograde the student's assignments directly on the forge. Useful when a submission was
        modified by the teacher directly in the local `submitted` folder to solve and bug
        or to add manual corrections. The corrected submission is then committed and pushed to the forge.
        This method waits for the student_autograde and collect the new student gradebook.

        Examples:

        Autograde all students submissions in the current directory::

            course.forge_autograde("Assignment1")

        Autograde all students submissions for a given student:

            course.forge_autograde("Assignment1",
                                      tag="firstname.lastname")
        """
        from .nbgrader_utils import Gradebook, remove_submission_gradebook

        failed = []
        self.forge.login()
        for assignment_dir in glob.glob(
            f"submitted/{tag}/{os.path.basename(assignment_name)}"
        ):
            student = assignment_dir.split("/")[1]
            # get student group
            project = self.assignment(assignment_name, username=student)
            submission = project.submission()
            assert (
                submission.repo.forked_from_project is not None
            ), "a student assignment should be a fork"
            student_group = submission.repo.forked_from_project.namespace.name
            self.log.info(f"Student: {student} (group {student_group})")
            remove_submission_gradebook(
                Gradebook("sqlite:///.gradebook.db"),
                os.path.basename(assignment_name),
                student,
            )
            # re-submit the submitted
            self.log.info("- Enregistrement des changements:")
            self.forge.ensure_local_git_configuration(dir=os.getcwd())
            if (
                self.forge.git(
                    [
                        "commit",
                        "--all",
                        "-m",
                        f"Correction par {self.forge.get_current_user().username}",
                    ],
                    check=False,
                    cwd=assignment_dir,
                ).returncode
                != 0
            ):
                self.log.info("  Pas de changement à enregistrer")

            self.log.info("- Envoi des changements:")
            branch = submission.repo.default_branch
            url = str(submission.repo.web_url)
            self.forge.git(["push", url, branch], cwd=assignment_dir)
            # Force an update of origin/master (or whichever the origin default branch)
            # self.forge.git(["update-ref", f"refs/remotes/origin/{branch}", branch])
            self.log.info(
                f"- Nouvelle soumission effectuée. "
                f"Vous pouvez consulter le dépôt: {url}"
            )
            # autograde
            try:
                job = submission.ensure_autograded(force_autograde=True)
            except RuntimeError as e:
                self.log.warning(e)
                failed.append(assignment_dir)
                continue
            # collect gradebooks
            self.log.info(f"fetch autograded for {assignment_dir}")
            submission.repo.fetch_artifacts(job, path=".", prefix="")
            self.merge_autograded_db(
                assignment_name=os.path.basename(assignment_name),
                tag=tag,
                on_inconsistency="WARNING",
                new_score_policy=new_score_policy,
            )
        if failed:
            self.log.warning(f"Failed autograde: {' '.join(failed)}")

    def collect_in_submitted(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> None:
        """
        Collect the student's submissions following nbgrader's standard organization
        and convert markdown into ipynb notebooks.

        This wrapper for `collect`:
        - forces a login;
        - reports more information to the user (at a cost);
        - stores the output in the subdirectory `submitted/`,
          following nbgrader's standard organization,
        - converts markdown notebooks into ipynb notebooks.

        This is used by the course dashboard.
        """
        super().collect_in_submitted(assignment_name, student_group)
        self.convert_from_md_to_ipynb(
            path=f"submitted/*/{os.path.basename(assignment_name)}"
        )

    def generate_feedback(
        self, assignment_name: str, tag: str = "*", new_score_policy: str = "only_empty"
    ) -> None:
        """
        Generate the assignment feedback for the given student and propagate the scores
        in the student gradebooks.
        The student name can be given with wildcard.
        """
        nbgrader_config = self.get_nbgrader_config()
        self.convert_from_md_to_ipynb(
            path=f"autograded/{tag}/{os.path.basename(assignment_name)}/"
        )
        run(
            [
                "nbgrader",
                "generate_feedback",
                "--force",
                "--CourseDirectory.feedback_directory=feedback_generated",
                *nbgrader_config,
                os.path.basename(assignment_name),
                f"--student={tag}",
            ]
        )
        if os.path.exists("feedback"):
            shutil.rmtree("feedback")
            shutil.copytree("feedback_generated", "feedback")
        self.merge_autograded_db(
            os.path.basename(assignment_name),
            back=True,
            on_inconsistency="WARNING",
            tag=tag,
            new_score_policy=new_score_policy,
        )

    def student_autograde(self, assignment_name: str, student: str) -> None:
        """
        Autograde the assignment for the given student

        This is mostly meant for usage in Continuous Integration
        """
        namespace = os.environ.get("CI_PROJECT_NAMESPACE")
        if student == "student" and namespace is not None and "/" not in namespace:
            student = namespace

        # add student firstname, lastname and email in database
        firstname, lastname, email = self.format_studentid(student)
        run(
            [
                "nbgrader",
                "db",
                "student",
                "add",
                f"{student}",
                f"--first-name={firstname}",
                f"--last-name={lastname}",
                f"--email={email}",
                "--db=sqlite:///.gradebook.db",
            ]
        )

        nbgrader_config = [
            "--db=sqlite:///.gradebook.db",
            "--force",
            "--CourseDirectory.submitted_directory=submitted",
            "--CourseDirectory.autograded_directory=autograded",
            "--CourseDirectory.feedback_directory=feedback_generated",
            "--CourseDirectory.ignore=" + str(self.ignore_nbgrader),
            "--ExecutePreprocessor.allow_errors=True",
            "--ExecutePreprocessor.interrupt_on_timeout=True",
        ]
        submitted_student = os.path.join("submitted", student)
        submitted_assignment = os.path.join(submitted_student, assignment_name)
        os.makedirs(submitted_student, exist_ok=True)
        if not os.path.exists(submitted_assignment):
            os.symlink("../..", submitted_assignment)
        notebooks_md = glob.glob("*.md")
        is_nbgrader = False
        for nb_md in notebooks_md:
            with io.open(nb_md) as fd:
                if "nbgrader" not in fd.read():
                    self.log.info(
                        "Skip markdown file/notebook with no nbgrader metadata:"
                        f" {nb_md}"
                    )
                    continue
            run(["jupytext", "--to", "ipynb", nb_md])
            is_nbgrader = True
        if not is_nbgrader:
            self.log.error("No markdown notebooks with nbgrader metadata found.")
            return
        run(["nbgrader", "autograde", *nbgrader_config, assignment_name])
        run(["nbgrader", "generate_feedback", *nbgrader_config, assignment_name])
        autograded = os.path.join("autograded", student, assignment_name)
        shutil.copy(".gradebook.db", autograded)
        feedback_generated = os.path.join(
            "feedback_generated", student, assignment_name
        )
        for format in ["csv", "md", "html", "svg"]:
            io.open(os.path.join(feedback_generated, f"scores.{format}"), "w").write(
                self.export_scores(
                    format, student=student, assignment_name=assignment_name
                )
            )

        if os.path.exists("feedback"):
            shutil.rmtree("feedback")
        shutil.copytree(feedback_generated, "feedback")

    # For backward compatibility
    ci_autograde = student_autograde

    def export_scores(
        self,
        format: str = "html",
        student: Optional[str] = None,
        assignment_name: Optional[str] = None,
    ) -> Union[str, Any]:
        """
        Export the notebook scores from nbgrader's database
        """
        import nbgrader.api  # type: ignore
        from .nbgrader_utils import export_scores

        db = nbgrader.api.Gradebook("sqlite:///.gradebook.db")
        return export_scores(
            db, format=format, student=student, assignment_name=assignment_name
        )

    def fetch_feedback(
        self, assignment_name: str, force_autograde: bool = False
    ) -> None:
        """
        Télécharge les retours (correction automatique et manuelle)
        """
        self.forge.login()
        assignment = self.assignment(assignment_name)
        assignment_dir = self.work_dir(assignment_name)
        assignment.check_assignment_dir(assignment_dir)

        if not assignment.has_submission():
            raise RuntimeError(
                _("no submission please submit", assignment_name=assignment_name)
            )

        submission = assignment.submission()

        job = submission.ensure_autograded(force_autograde=force_autograde)
        self.log.info(
            "Téléchargement des retours dans"
            f" {self.student_dir}/{assignment_name}/feedback/"
        )
        submission.repo.fetch_artifacts(job, path=assignment_dir, prefix="feedback")
        student = self.forge.get_current_user().username
        assert student is not None
        feedback_generated = os.path.join(
            assignment_dir, "feedback_generated", student, assignment_name
        )
        feedback = os.path.join(assignment_dir, "feedback")
        if os.path.exists(feedback_generated):
            if os.path.exists(feedback):
                os.remove(feedback)
            os.rename(feedback_generated, feedback)
        scorefile = os.path.join(assignment_dir, "feedback", "scores.md")
        self.log.info(io.open(scorefile).read())

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
        assignment = self.assignment(assignment_name, student_group=student_group)
        failed = []
        for submission in assignment.submissions():
            try:
                self.log.info(
                    f"Ensuring {submission.student}'s submission has been autograded"
                )
                submission.ensure_autograded(force_autograde=force_autograde)
            except RuntimeError as e:
                self.log.warning(e)
                failed.append(submission.student)
                continue
        if failed:
            self.log.warning(f"Failed autograde: {' '.join(failed)}")

    def force_autograde(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
    ) -> None:
        """
        Force the autograding of all submissions.
        """
        self.forge.login()
        assignment = self.assignment(
            assignment_name=assignment_name, student_group=student_group
        )
        failed = []
        for submission in assignment.submissions():
            try:
                self.log.info(
                    f"Ensuring {submission.student}'s submission has been autograded"
                )
                submission.force_autograde()
            except RuntimeError as e:
                self.log.warning(e)
                failed.append(submission.student)
                continue
            time.sleep(0.2)
        if failed:
            self.log.warning(f"Failed force autograde: {' '.join(failed)}")

    def collect_status(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> List[SubmissionStatus]:
        assignment = self.assignment(assignment_name, student_group=student_group)
        return assignment.collect_status()

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

        Submissions for which an autograde has already been collected
        are skipped by default. If you wish to collect a fresh
        feedback for one or more student, wipe the corresponding
        directories in "autograded/*" and "feedback_generated/*".

        The autograde is based on the latest commit from the
        submission's default branch. If that commit has not yet been
        autograded, a new autograde is triggered. With
        `force_autograde`, a new autograde is always triggered.

        Only files files starting with the given prefix are extracted.
        """
        self.forge.login()
        submissions_status = self.assignment(
            assignment_name=assignment_name, student_group=student_group
        ).collect_status()
        self.log.info(f"Collecting autograded for {len(submissions_status)} students")
        for status in submissions_status:
            student = status.student
            if os.path.isdir(os.path.join("autograded", student, assignment_name)):
                self.log.info(f"autograded already collected for {student}; skipping")
                continue
            if status.autograde_status != "success":
                self.log.info(
                    f"autograded not available for {student} "
                    f"(status: {status.autograde_status}); skipping"
                )
                continue
            self.log.info(f"collect autograded for {student}")
            assert status.submission is not None and status.autograde_job is not None
            repo = status.submission.repo
            job = status.autograde_job
            repo.fetch_artifacts(job, path=".", prefix=prefix)
            # autograded_anonymous = os.path.join("autograded", "student")
            # if os.path.isdir(autograded_anonymous):
            #     shutil.copytree(autograded_anonymous,
            #                     os.path.join("autograded", student),
            #                     dirs_exist_ok=True)
            #     shutil.rmtree(autograded_anonymous)
            feedback_path = os.path.join(
                "feedback_generated", student, os.path.basename(assignment_name)
            )
            if os.path.isdir("feedback"):
                shutil.copytree("feedback", feedback_path, dirs_exist_ok=True)
                shutil.rmtree("feedback")

    def collect_scores(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> Any:  # pandas.DataFrame
        """
        Collect available nbgrader's scores for all submissions

        Run `ensure_autograded` first to ensure they are available.
        """
        import pandas as pd  # type: ignore

        submissions_status = self.assignment(
            assignment_name=assignment_name, student_group=student_group
        ).collect_status()
        self.log.info(f"Collecting scores for {len(submissions_status)} students")
        all_scores = []
        for status in submissions_status:
            student = status.student
            if status.autograde_status != "success":
                self.log.info(f"missing successful autograde for {student}")
                all_scores.append(
                    pd.DataFrame(
                        {"student": [student], "assignment": [assignment_name]}
                    )
                )
                continue
            assert status.submission is not None and status.autograde_job is not None
            self.log.info(f"fetching scores for {student}")
            repo = status.submission.repo
            job = status.autograde_job
            path = "feedback/scores.csv"
            scores_txt = repo.fetch_artifact(job, artifact_path=path).text
            scores = pd.read_csv(io.StringIO(scores_txt))
            all_scores.append(scores)
        return pd.concat(all_scores, axis=0)

    def collect_gradebooks(
        self, assignment_name: str, student_group: Optional[str] = None
    ) -> None:
        """
        Collect the gradebooks for all submissions

        Run `ensure_autograded` first to ensure they are available.
        """
        submissions_status = self.assignment(
            assignment_name=assignment_name, student_group=student_group
        ).collect_status()
        self.log.info(f"Collecting scores for {len(submissions_status)} students")
        for status in submissions_status:
            student = status.student
            if os.path.isdir(os.path.join("autograded", student, assignment_name)):
                self.log.info(f"autograded already available for {student}; skipping")
                continue
            self.log.info(f"collect autograded for {student}")
            if status.autograde_status != "success":
                continue
            assert status.submission is not None and status.autograde_job is not None
            job = status.autograde_job
            repo = status.submission.repo
            file = f"autograded/{student}/{assignment_name}/.gradebook.db"
            content = repo.fetch_artifact(job, artifact_path=file).content
            os.makedirs(os.path.dirname(file), exist_ok=True)
            with io.open(file, "wb") as f:
                f.write(content)

    def merge_autograded_db(
        self,
        assignment_name: str,
        tag: str = "*",
        on_inconsistency: str = "ERROR",
        new_score_policy: str = "only_empty",
        back: bool = False,
    ) -> None:
        """Propagate the student scores to the global teacher gradebook from the
        student's gradebooks.
        If back is True, do the reverse process.

        Args:
            assignment_name:
            tag:
            back:
            on_inconsistency:
            new_score_policy: can only be 'only_empty', 'force_new_score',
                              'only_greater'

        Returns:

        """
        from nbgrader.api import Gradebook, MissingEntry
        from .nbgrader_utils import merge_submission_gradebook

        target = Gradebook("sqlite:///.gradebook.db")
        if back:
            self.log.info(
                "Syncing students' gradebook from the global gradebook `.gradebook.db`"
            )
        else:
            self.log.info(
                "Syncing students' gradebook to the global gradebook `.gradebook.db`"
            )
        for file in sorted(
            glob.glob(
                f"autograded/{tag}/{os.path.basename(assignment_name)}/.gradebook.db"
            )
        ):
            self.log.info(f"Student gradebook `{file}`")
            source = Gradebook(f"sqlite:///{file}")
            try:
                target.find_assignment(os.path.basename(assignment_name))
            except MissingEntry:
                from .nbgrader_utils import merge_assignment_gradebook

                merge_assignment_gradebook(source, target)
            merge_submission_gradebook(
                source,
                target,
                back=back,
                on_inconsistency=on_inconsistency,
                new_score_policy=new_score_policy,
            )
            if back:
                source.db.commit()
            source.close()
        if not back:
            target.db.commit()
        target.close()

    def clear_needs_manual_grade(
        self,
        assignment_name: str,
        autograded: bool = True,
        null_score: bool = True,
    ) -> None:
        """
        Clear the «needs manual grade» flag in simple cases

        - with `autograded` set: the flag is cleared for all autograded answer cells
        - with `null_score` set: the flag is cleared for all cells with max_score=0
        """
        from nbgrader.api import Gradebook

        gradebook = Gradebook("sqlite:///.gradebook.db")
        for submission in gradebook.assignment_submissions(assignment_name):
            for notebook in submission.notebooks:
                for grade in notebook.grades:
                    if autograded and grade.auto_score is not None:
                        grade.needs_manual_grade = False
                    if null_score and grade.max_score == 0:
                        grade.needs_manual_grade = False
        gradebook.db.commit()
        gradebook.close()

    def collect_autograded_post(
        self,
        assignment_name: str,
        tag: str = "*",
        on_inconsistency: str = "ERROR",
        new_score_policy: str = "only_empty",
        autograded: bool = True,
        null_score: bool = True,
    ) -> None:
        """Propagate the student scores to the global teacher gradebook from the
        student's gradebooks and clear
        the nbgrader «needs manual grade» flag in simple cases.

        See also:
            merge_autograded_db
            clear_needs_manual_grade
        """
        self.merge_autograded_db(
            assignment_name=os.path.basename(assignment_name),
            tag=tag,
            on_inconsistency=on_inconsistency,
            back=False,
            new_score_policy=new_score_policy,
        )
        self.clear_needs_manual_grade(
            os.path.basename(assignment_name),
            autograded=autograded,
            null_score=null_score,
        )

    def release_feedback(
        self,
        assignment_name: str,
        student_group: Optional[str] = None,
        tag: Optional[str] = "*",
    ) -> None:
        """
        After instructor correction, commit and push student grades
        of a given assignment in the student repos.
        The student group can be given optionally.
        The student name can be given with wildcard.
        """
        self.forge.login()
        for file in sorted(
            glob.glob(
                f"autograded/{tag}/{os.path.basename(assignment_name)}/.gradebook.db"
            )
        ):
            content = base64.b64encode(io.open(file, "rb").read()).decode("ascii")
            username = file.split("/")[1]
            project = self.assignment(
                assignment_name, username=username
            ).submission_repo()
            if student_group is not None:
                assert (
                    project.forked_from_project is not None
                ), "a student assignment should be a fork"
                group = project.forked_from_project.namespace.name
                if group != student_group:
                    continue
            self.log.info(f"Release feedback for student gradebook `{file}`")
            project.ensure_file(
                ".gradebook.db",
                content=content,
                encoding="base64",
                commit_message="Release feedback",
            )

    def jupyter(self, *args: str, **kwargs: None) -> None:
        """Lance le notebook jupyter (inutile sur le service JupyterHub)"""
        if args and args[0] == "notebook":
            if "JUPYTERHUB_USER" in os.environ:
                self.log.info(_("No need to launch Jupyter on JupyterHub"))
                return
            args = ("notebook", "--ip=127.0.0.1", *args[1:])
        self.run("jupyter", *args)

    @staticmethod
    def formgrader(
        assignment_name: Optional[str] = None, in_notebook: bool = False
    ) -> Any:
        """
        Launch nbgrader's formgrader
        """
        if assignment_name is None:
            url = "/formgrader/gradebook"
        else:
            url = f"/formgrader/gradebook/{assignment_name}"
        if in_notebook:
            from IPython.display import HTML  # type: ignore

            if "JUPYTERHUB_SERVICE_PREFIX" in os.environ:
                print("Launching formgrader in the background")
                jurl = jupyter_lab_in_hub(path=url, background=True)
                assert (
                    jurl is not None
                )  # TODO check if jurl can be None and what it means
                url = jurl

            return HTML(
                f"Follow this link to <a target='_blank' rel='noopener noreferrer' href='{url}'>start grading {assignment_name}</a>"
            )  # type: ignore # noqa: E501
        jupyter_notebook(url)

    def grade_dashboard(
        self, student_group: Optional[str] = None
    ) -> "dashboards.CourseGradeDashboard":
        """
        Return a dashboard for the course for use in Jupyter

        This ensures first that the user is logged in (this part is not asynchronous).
        """
        from .dashboards import CourseGradeDashboard

        return CourseGradeDashboard(self)
