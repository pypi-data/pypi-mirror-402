from dataclasses import dataclass

from typing import Optional, List
from travo.utils import git_get_origin
from travo.gitlab import GitLab, ResourceRef, Project, User, Group


@dataclass
class Homework:
    """
    A homework is a simple aggregator of travo information + configuration.

    The basic logic revolve around

    * The instructor's assignment.
    * Some students' copies that are forks.
    """

    gitlab: GitLab
    project: Project  # the original project
    assignment: Project  # the assignment (can be `project` or not)
    directory: str  # The working directory. Usually `.`

    instructor: Optional[User] = None  # The possible instructor
    instructor_level: int = 40  # The access level of the instructor

    group: Optional[Group] = None  # The possible correction group
    group_level: int = 20  # The access level of the group

    def __init__(self, url: str = ".") -> None:
        """
        If url is not given, then the remote of the local git repository is used.
        """

        self.project = self.get_project(url)
        self.gitlab = self.project.gitlab
        self.log = self.gitlab.log

    def get_project(self, url: str) -> Project:
        """
        Connect to the forge and get the project.
        """

        if not url.startswith("https:"):
            self.directory = url
            try:
                url = git_get_origin(url)
            except RuntimeError:
                if url == ".":
                    raise RuntimeError(
                        "The current directory is not a valid travo/git directory."
                        " Specify a valid directory or an project URL."
                    )
                else:
                    raise RuntimeError(
                        f"{url} is not a valid travo/git directory. Specify a valid"
                        " directory or an project URL."
                    )
        else:
            self.directory = "."

        ref = ResourceRef(url=url)
        path = ref.path
        gitlab = ref.forge

        gitlab.login()

        user = gitlab.get_current_user()
        assert isinstance(user, User)
        gitlab.log.info(f"user: {user.username} ({user.name}) {user.web_url}")

        project = gitlab.get_project(path)
        gitlab.log.info(f"project: '{project.name_with_namespace}' {project.web_url}")
        return project

    def get_group(self, path: str) -> None:
        """
        Find the correction group
        """

        self.group = self.gitlab.get_group(path)

    def get_copies(self) -> List[Project]:
        """
        Get copies.

        If the instructor's assignment is given, get all the students' copies.
        IF a student copy is given, just return it.
        """

        project = self.project

        if project.forked_from_project is not None:
            # This is likely an assignment
            assignment = project.forked_from_project
            self.assignment = assignment
            project.gitlab.log.info(
                f"Fork of: '{assignment.name_with_namespace}' {assignment.web_url}"
            )
            forks = [project]
            self.forks = forks
            return forks

        self.assignment = project
        forks = project.get_forks(recursive=False)
        self.copies = forks
        return forks

    def check_student(self, project: "Project", fixup: bool = False) -> bool:
        """
        Check various configuration on a student copy.

        If `fixup` is true then also try to fix them.

        Return `true` if there is issues (after a potential fixup).
        """

        recheck = False
        result = True

        # Detect instructor's assignment if non is given
        assignment = self.assignment
        if assignment is None:
            assignment = project.forked_from_project

        # Check fork
        if assignment is not None:
            if project.forked_from_project is None:
                print("  ❌ not a fork")
                result = False
                if fixup:
                    project.add_origin(assignment)
                    recheck = True
            elif assignment.id != project.forked_from_project.id:
                print(
                    f"  ❌ bad fork of {project.forked_from_project.name_with_namespace}"
                )
                result = False

        # Check visibiliy
        vis = project.visibility
        if vis != "private":
            print(f"  ❌ bad visibility {vis}")
            result = False
            if fixup:
                project.setattributes(visibility="private")
                recheck = True

        # TODO: Check allowed file changes

        # Check correction group (if any)
        if self.group is not None:
            sharedok = False
            for g in project.shared_with_groups:
                if g["group_id"] == self.group.id:
                    if g["group_access_level"] >= self.group_level:
                        sharedok = True
                        continue
            if not sharedok:
                print(f"  ❌ bad group sharing with group {self.group.full_path}")
                result = False
                if fixup:
                    project.share_with(self.group, self.group_level)
                    recheck = True

        instructor = self.instructor
        if instructor is None and assignment is not None:
            owners = assignment.get_owners()
            if len(owners) == 0:
                print("  ❌ no assignment owner")
                result = False
            elif len(owners) > 1:
                print(f"  ❌ multiple assignment owners {owners}")
                result = False
            else:
                instructor = owners[0]

        if instructor is not None:
            instructok = False
            for member in project.get_members():
                if (
                    member["id"] == instructor.id
                    and member["access_level"] >= self.instructor_level
                ):
                    instructok = True
                    continue
            if not instructok:
                print(f"  ❌ bad membership of instructor {instructor.username}")
                result = False
                if fixup:
                    # FIXME share_with do not works on users yet
                    # project.share_with(instructor, self.instructor_level)
                    recheck = True

        if recheck:
            print("     Recheck after fixup!")
            result = self.check_student(project)
        return result

    def print_info(self, project: "Project", fixup: bool = False) -> None:
        """
        Print most information about a student project
        """

        print(f"Student: {project.name_with_namespace} {project.web_url}`")

        # Detect instructor's assignment if non is given
        assignment = self.assignment
        if assignment is None:
            assignment = project.forked_from_project

        self.check_student(project, fixup=fixup)

        if project.default_branch is None:
            print("  ❌ empty repository")
            return

        nocommits = False
        compare = None
        if assignment is not None:
            compare = project.get_compare(assignment)
            if "message" in compare:
                print(f"  ❌ {compare['message']}")
                compare = None
        if compare is not None:
            if len(compare["commits"]) == 0:
                print("  ❌ no commits")
                nocommits = True

            compare_rev = assignment.get_compare(project)
            if len(compare_rev["commits"]) != 0:
                print(
                    "     not up to date with upstream; lags"
                    f" {len(compare_rev['commits'])}"
                )

        if nocommits:
            return

        reports = project.get_reports()
        for k in reports:
            v = reports[k]
            status = v["status"]
            if "total_count" in v:
                if v["success_count"] == v["total_count"] and status == "success":
                    mark = "✅"
                elif v["success_count"] == 0:
                    mark = "❌"
                else:
                    mark = "  "
                print(
                    f"  {mark} {k}:"
                    f" {v['status']} {v['success_count']}/{v['total_count']}"
                )
            else:
                if status == "success":
                    mark = "✅"
                elif status == "failed":
                    mark = "❌"
                else:
                    mark = "  "
                print(f"  {mark} {k}: {v['status']}")
