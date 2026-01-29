from typing import Any, Dict, List, Optional, Tuple
from nbgrader.api import Gradebook, MissingEntry, InvalidEntry  # type: ignore
from .utils import getLogger
from sqlalchemy.orm.exc import FlushError  # type: ignore
from sqlalchemy.exc import IntegrityError, StatementError  # type: ignore
from tornado.log import app_log


def to_args(item: Any, positional: List["str"]) -> Tuple[List["str"], Dict["str", Any]]:
    kwargs = dict(item.to_dict())
    args = [kwargs[key] for key in positional]
    for key in positional:
        del kwargs[key]
    return args, kwargs


def merge_assignment_gradebook(source: Gradebook, target: Gradebook) -> None:
    """
    Merge the gradebook's assignment information into the target gradebook

    Grades and submission informations are ignored

    Assumption: there is a single assignment
    """
    (assignment,) = source.assignments
    target.update_or_create_assignment(assignment.name)

    for notebook in assignment.notebooks:
        args, kwargs = to_args(notebook, ["name"])
        # kernelspec must be specified for nbgrader autograde
        if notebook.kernelspec is not None:
            kwargs["kernelspec"] = notebook.kernelspec
        target.update_or_create_notebook(*args, assignment.name, **kwargs)
        for cell in notebook.grade_cells:
            args, kwargs = to_args(cell, ["name", "notebook", "assignment"])
            target.update_or_create_grade_cell(*args, **kwargs)
        for cell in notebook.task_cells:
            args, kwargs = to_args(cell, ["name", "notebook", "assignment"])
            target.update_or_create_task_cell(*args, cell_type=cell.cell_type, **kwargs)
        for cell in notebook.source_cells:
            args, kwargs = to_args(cell, ["name", "notebook", "assignment"])
            target.update_or_create_source_cell(*args, **kwargs)
        for cell in notebook.solution_cells:
            args, kwargs = to_args(cell, ["name", "notebook", "assignment"])
            target.update_or_create_solution_cell(*args, **kwargs)


def merge_submission_gradebook(
    source: Gradebook,
    target: Gradebook,
    back: bool = False,
    on_inconsistency: str = "ERROR",
    # Literal("ERROR", "WARNING")
    new_score_policy: str = "only_empty",
) -> None:
    """
    Merge the students and submissions from the source gradebook into the target
    gradebook

    Assumptions:
    - the target gradebook already contains the assignments
    - new_score_policy: can only be 'only_empty', 'force_new_score', 'only_greater'
    """
    for student in source.students:
        args, kwargs = to_args(student, ["id"])
        target.update_or_create_student(*args, **kwargs)

    for assignment in source.assignments:
        for submission in source.assignment_submissions(assignment.name):
            args, kwargs = to_args(submission, ["student"])
            del kwargs["first_name"]
            del kwargs["last_name"]
            # Don't pass in kwargs, because only the student name is
            # relevant to be able to create a submission, while
            # updating an attribute like the id in the database may
            # wreak havoc
            target.update_or_create_submission(assignment.name, *args)  # , **kwargs)

            for notebook in submission.notebooks:
                for grade in notebook.grades:
                    args, kwargs = to_args(
                        grade, ["name", "notebook", "assignment", "student"]
                    )
                    try:
                        target_grade = target.find_grade(*args)
                    except MissingEntry:
                        if on_inconsistency == "WARNING":
                            log = getLogger()
                            log.warning(
                                "Skipping grade which does not exist in the target:"
                                f" {grade}"
                            )
                            continue
                        else:
                            raise

                    if back:
                        grade, target_grade = target_grade, grade
                        args, kwargs = to_args(
                            grade, ["name", "notebook", "assignment", "student"]
                        )

                    for key, value in kwargs.items():
                        if (
                            (
                                (
                                    new_score_policy == "only_empty"
                                    or new_score_policy == "only_greater"
                                )
                                and getattr(target_grade, key) is None
                            )
                            or new_score_policy == "force_new_score"
                            or (
                                new_score_policy == "only_greater"
                                and type(getattr(target_grade, key)) is float
                                and type(getattr(grade, key)) is float
                                and getattr(grade, key) > getattr(target_grade, key)
                            )
                        ):
                            setattr(target_grade, key, value)

                for comment in notebook.comments:
                    args, kwargs = to_args(
                        comment, ["name", "notebook", "assignment", "student"]
                    )
                    try:
                        target_comment = target.find_comment(*args)
                    except MissingEntry:
                        if on_inconsistency == "WARNING" or (
                            comment.auto_comment is None
                            and comment.manual_comment is None
                        ):
                            log = getLogger()
                            log.warning(
                                "Skipping comment which does not exist in the target:"
                                f" {comment}"
                            )
                            continue
                        else:
                            raise

                    if back:
                        comment, target_comment = target_comment, comment
                        args, kwargs = to_args(
                            comment, ["name", "notebook", "assignment", "student"]
                        )

                    for key, value in kwargs.items():
                        if getattr(target_comment, key) is None:
                            setattr(target_comment, key, value)


def remove_submission_gradebook(
    gb: Gradebook, assignment_name: str, student: str
) -> None:
    log = getLogger()
    try:
        gb.find_submission(assignment_name, student)
        answer = input(
            f"Do you really want to suppress {assignment_name} submission of {student} "
            "from your local .gradebook.db ? [y/N] "
        )
        if answer != "y":
            log.info("Submission not deleted from your local .gradebook.db.")
            return
        gb.remove_submission(assignment_name, student)
    except MissingEntry:
        log.info(
            f"Missing entry for {assignment_name} submission from student {student} in"
            " your local .gradebook.db"
        )


def remove_assignment_gradebook(
    gb: Gradebook, assignment_name: str, force: bool = False
) -> None:
    log = getLogger()
    try:
        gb.find_assignment(assignment_name)
        if not force:
            answer = input(
                "Do you really want to suppress all submissions from"
                f" {assignment_name} from your local .gradebook.db ? [y/N] "
            )
            if answer != "y":
                log.info("Assignment not deleted from your local .gradebook.db.")
                return

        assignment = gb.find_assignment(assignment_name)

        for submission in assignment.submissions:
            gb.remove_submission(assignment_name, submission.student.id)

        try:
            for notebook in assignment.notebooks:
                gb.remove_notebook(notebook.name, assignment_name)
        except Exception:
            pass

        gb.db.delete(assignment)

        try:
            gb.db.commit()
        except (IntegrityError, FlushError, StatementError) as e:
            app_log.exception("Rolling back session due to database error %s" % e)
            gb.db.rollback()
            raise InvalidEntry(*e.args)
        gb.db.close()

    except MissingEntry:
        log.info(
            f"Missing entry for assignment {assignment_name} in your local"
            " .gradebook.db"
        )


class GradebookExporter:
    def record(
        self,
        student: str,
        assignment: str,
        notebook_name: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        pass

    def record_assignment(
        self,
        student: str,
        assignment: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        pass

    def export(self) -> Any:
        pass


class DataFrameGradebookExporter(GradebookExporter):
    def __init__(self) -> None:
        self.data: List[List] = []

    def record(
        self,
        student: str,
        assignment: str,
        notebook_name: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        import pandas as pd  # type: ignore

        if auto_score is None:
            auto_score = pd.NA
        if manual_score is None:
            manual_score = pd.NA
        total_score = auto_score
        if max_manual_score > 0:
            total_score += manual_score
        total_score += extra_credit
        self.data.append(
            [
                student,
                assignment,
                notebook_name,
                auto_score,
                max_auto_score,
                manual_score,
                max_manual_score,
                extra_credit,
                total_score,
                max_auto_score + max_manual_score,
            ]
        )

    def record_assignment(
        self,
        student: str,
        assignment: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        pass

    def export(self) -> Any:
        import pandas as pd  # type: ignore

        df = pd.DataFrame(
            self.data,
            columns=[
                "student",
                "assignment",
                "notebook",
                "auto_score",
                "max_auto_score",
                "manual_score",
                "max_manual_score",
                "extra_credit",
                "total_score",
                "max_total_score",
            ],
        )
        df.set_index(["student", "assignment", "notebook"], inplace=True)
        # df = df.astype('Int64')
        return df


class CSVGradebookExporter(DataFrameGradebookExporter):
    def export(self) -> Any:
        return super().export().to_csv()


class BadgeGradebookExporter(GradebookExporter):
    def record_assignment(
        self,
        student: str,
        assignment: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        import anybadge  # type: ignore

        s = f"auto: {auto_score:g}/{max_auto_score:g}"
        if manual_score is None:
            score = auto_score
            max_score = max_auto_score
        else:
            score = auto_score + manual_score
            max_score = max_auto_score + max_manual_score
            s += f" | manual: {manual_score:g}/{max_manual_score:g}"
            s += f" | total: {score:g}/{max_score:g}"

        if extra_credit > 0:
            s += f" | bonus: {extra_credit:g}"

        score += extra_credit
        if max_score > 0:
            score = score / max_score
            if score <= 0.25:
                color = "red"
            elif score <= 0.5:
                color = "orange"
            elif score <= 0.75:
                color = "yellow"
            else:
                color = "green"
        else:
            color = "green"

        self.badge = anybadge.Badge("score", s, default_color=color)

    def export(self) -> Any:
        return self.badge


class SVGGradebookExporter(BadgeGradebookExporter):
    def export(self) -> Any:
        return super().export().badge_svg_text


class FormatedGradebookExporter(GradebookExporter):
    header_format: str
    notebook_format: str
    score_format: str
    footer_format: str

    def __init__(self) -> None:
        self.report = self.header_format

    def record(
        self,
        student: str,
        assignment_name: str,
        notebook_name: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        self.report += self.notebook_format.format(name=notebook_name)
        if max_auto_score > 0:
            self.report += self.score_format.format(
                type="automatique", score=auto_score, max_score=max_auto_score
            )
        if manual_score is not None:
            self.report += self.score_format.format(
                type="manuel", score=manual_score, max_score=max_manual_score
            )
        if extra_credit > 0:
            self.report += self.score_format.format(
                type="bonus", score=extra_credit, max_score=0
            )

    def record_assignment(
        self,
        student: str,
        assignment_name: str,
        auto_score: float,
        max_auto_score: float,
        manual_score: Optional[float],
        max_manual_score: float,
        extra_credit: float,
    ) -> None:
        self.record(
            student,
            assignment_name,
            "total",
            auto_score,
            max_auto_score,
            manual_score,
            max_manual_score,
            extra_credit,
        )

    def export(self) -> str:
        return self.report + self.footer_format


class HTMLGradebookExporter(FormatedGradebookExporter):
    header_format = "<html>\n<body>\n<title>Scores</title>\n"
    ("<ul>",)
    notebook_format = "    <li><a href='{name}.html'>{name}</a>:\n"
    score_format = "        {type}: {score:g}/{max_score:g}\n"
    footer_format = "</ul>\n</body>\n</html>\n"


class MDGradebookExporter(FormatedGradebookExporter):
    header_format = "Scores:\n"
    notebook_format = "- {name}:\n"
    score_format = "     - {type}: {score:g}/{max_score:g}\n"
    footer_format = ""


gradebook_exporters = {
    "md": MDGradebookExporter,
    "html": HTMLGradebookExporter,
    "df": DataFrameGradebookExporter,
    "csv": CSVGradebookExporter,
    "badge": BadgeGradebookExporter,
    "svg": SVGGradebookExporter,
}


def export_scores(
    gradebook: Gradebook,
    format: str = "html",
    student: Optional[str] = None,
    assignment_name: Optional[str] = None,
) -> Any:
    gradebook_exporter: GradebookExporter = gradebook_exporters[format]()

    if student is None:
        students = [student.id for student in gradebook.students]
    else:
        students = [student]

    for student in students:
        assert student is not None
        for submission in gradebook.find_student(student).submissions:
            if (
                assignment_name is not None
                and submission.assignment.name != assignment_name
            ):
                continue
            assignment_auto_score = 0
            assignment_max_auto_score = 0
            assignment_manual_score = None
            assignment_max_manual_score = 0
            assignment_extra_credit = 0
            for notebook in submission.notebooks:
                auto_score = 0
                max_auto_score = 0
                manual_score = None
                max_manual_score = 0
                extra_credit = 0
                for grade in notebook.grades:
                    # Try to guess whether this is a test cell, whose score can be
                    # computed automatically
                    # At some point, auto_score was None in this case, but this seems
                    # to be gone
                    # For now, assumes that a code cell with a non trivial max_score is
                    # a test cell
                    if grade.cell_type == "code" and grade.auto_score is not None:
                        # Autograded cell
                        max_auto_score += grade.max_score
                        if grade.manual_score is not None:
                            auto_score += grade.manual_score
                        else:
                            auto_score += grade.auto_score
                    else:
                        max_manual_score += grade.max_score
                        if grade.manual_score is not None:
                            if manual_score is None:
                                manual_score = grade.manual_score
                            else:
                                manual_score += grade.manual_score
                    if grade.extra_credit is not None:
                        extra_credit += grade.extra_credit
                gradebook_exporter.record(
                    student,
                    submission.assignment.name,
                    notebook.name,
                    auto_score,
                    max_auto_score,
                    manual_score,
                    max_manual_score,
                    extra_credit,
                )
                assignment_auto_score += auto_score
                assignment_max_auto_score += max_auto_score
                if manual_score is not None:
                    if assignment_manual_score is None:
                        assignment_manual_score = manual_score
                    else:
                        assignment_manual_score += manual_score
                assignment_max_manual_score += max_manual_score
                assignment_extra_credit += extra_credit
            gradebook_exporter.record_assignment(
                student,
                submission.assignment.name,
                assignment_auto_score,
                assignment_max_auto_score,
                assignment_manual_score,
                assignment_max_manual_score,
                assignment_extra_credit,
            )

    return gradebook_exporter.export()
