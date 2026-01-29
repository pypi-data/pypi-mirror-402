##############################################################################
# UI and dashboards
#
# Components:
# - AuthenticationWidget
# - LogWidget
# - Grid of AssignmentDashboards
#
# Design notes
#
# - Any call from the UI to the model (in particular any git/gitlab
#   interaction) goes through LogWidget.callback(action) which is in
#   charge of running the actions in subthreads, logging them, and
#   handling failures.
##############################################################################

import io
import glob
import logging
import os
import subprocess
import requests
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
    from ipywidgets import (  # type: ignore
        Button,
        ToggleButton,
        GridBox,
        HBox,
        VBox,
        Dropdown,
        Label,
        Layout,
        Output,
        Password,
        Text,
        Textarea,
        RadioButtons,
    )
    import ipywidgets
except ImportError:
    raise ImportError(
        "Cannot find ipywidgets. "
        "dashboards needs optional dependencies. "
        "Please install travo with 'pip install travo[jupyter]'."
    )

from IPython.display import display, Javascript  # type: ignore

from .assignment import Assignment

from .gitlab import GitLab, AuthenticationError, ResourceNotFoundError
from .utils import run
from travo.i18n import _

from .course import Course, CourseAssignment, MissingInformationError
from .jupyter_course import JupyterCourse

# TODO: should use the current foreground color rather than black
border_layout = {"border": "1px solid black"}


def isimplemented(method: Callable) -> bool:
    """
    Return whether `method`, defined as not implemented in Course,
    has been implemented in a subclass A of Course.

        >>> from travo.course import Course
        >>> class A(Course):
        ...     def ensure_autograded():
        ...         pass
        >>> course = A("","","")
        >>> assert isimplemented(course.ensure_autograded)
        >>> assert not isimplemented(course.collect_autograded)
        >>> assert not isimplemented(course.formgrader)
    """
    # If an instance method, retrieves the underlying function
    method = getattr(method, "__func__", method)
    # Test whether the method is distinct from the eponym method in Course
    return getattr(Course, method.__name__) is not method


def HTML(*args: Any, **kwargs: Any) -> ipywidgets.HTML:
    """
    Make ipywidgets.HTML apply standard styling to its content

    See https://github.com/jupyter-widgets/ipywidgets/issues/2813
    """
    html = ipywidgets.HTML(*args, **kwargs)
    html.add_class("jp-RenderedHTMLCommon")
    return html


class AuthenticationWidget(VBox):
    """
    A widget for interactive input of credentials

    It's meant to be included in the UI; it will display itself upon
    request, send the credentials through forge.login, and hide itself
    if authentication succeeds.

    """

    on_login_hooks: List[Callable]

    def __init__(self, forge: GitLab):
        forge.on_missing_credentials = self.on_missing_credentials
        self.forge = forge
        title = Label(_("authentication widget title", url=forge.base_url))
        self.usernameUI = Text(
            description=_("username"), layout={"width": "fit-content"}
        )
        self.passwordUI = Password(
            description=_("password"), layout={"width": "fit-content"}
        )
        self.button = Button(description=_("sign in"), button_style="primary")
        self.messageUI = Label()
        self.button.on_click(lambda event: self.login())
        # We don't want to call login each time a new character is typed in!
        # Is there a way to only observe the "Return" key press?
        # self.passwordUI.observe(lambda event: self.login(),
        #                         names='value')
        self.on_login_hooks = []
        super(AuthenticationWidget, self).__init__(
            children=(
                title,
                self.usernameUI,
                self.passwordUI,
                self.button,
                self.messageUI,
            ),
            layout={"border": "1px solid black", "display": "none"},
        )

    def show_widget(self, message: str = "") -> None:
        self.messageUI.value = message
        self.layout.display = "block"

    def hide_widget(self) -> None:
        self.layout.display = "none"

    def login(self) -> None:
        self.messageUI.value = ""
        self.button.disabled = True
        username = self.usernameUI.value
        password = self.passwordUI.value
        try:
            self.forge.login(username=username, password=password, anonymous_ok=True)
            self.hide_widget()
            for hook in self.on_login_hooks:
                Thread(target=hook).start()
        except AuthenticationError as e:
            self.messageUI.value = str(e)
        finally:
            self.button.disabled = False

    def on_login(self, hook: Callable) -> None:
        self.on_login_hooks.append(hook)

    def on_missing_credentials(
        self,
        forge: GitLab,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Display the widget and raise to interrupt login
        """
        message = _("authentication required")
        self.show_widget(message)
        raise AuthenticationError(message)


class FormDialog(ipywidgets.HBox):
    """
    A dialog to request information through a form

    Example:

    Let's set english as language:

        >>> import io, i18n
        >>> i18n.set('locale', 'en')

    We create a dialog:

        >>> dialog = FormDialog()

    Originally it's empty:

        >>> dialog.children
        ()

    We now want to request information from the user. To this end, we
    describe the name of the requested items together with their types
    or list of values:

        >>> input = {"clear scores": bool,
        ...          "student group": str,
        ...          "release mode": ("public", "private")}

    We also define a callback function to handle the information upon
    validation by the user; here, we just print the values:

        >>> def on_validate(**kwargs):
        ...     print(kwargs)

    Optionaly, we define a callback function to be called if the user cancels:

        >>> def on_cancel():
        ...     print("Cancelling")

    We request the information from the user:

        >>> dialog.request_information(input=input,
        ...                            on_validate=on_validate,
        ...                            on_cancel=on_cancel)

    This populates the dialog with localized labels and widgets to
    input the requested entries according to their types, and two
    buttons to cancel or validate:

        >>> dialog.children
        (Label(value='clear scores'),
         Checkbox(value=False),
         Label(value='Student group'),
         Text(value=''),
         Label(value='Release mode'),
         Dropdown(options=('public', 'private'), value='public'),
         Button(button_style='danger', description='Cancel', style=ButtonStyle()),
         Button(button_style='success', description='Validate', style=ButtonStyle()))

    Let's emulate the user clicking on the Cancel button:

        >>> dialog.cancel()
        Cancelling
        >>> dialog.children
        ()

    This time, let's rerequest the information, and emulate the user
    setting some of the values and clicking the Validate:

        >>> dialog.request_information(input=input, on_validate=on_validate)
        >>> dialog.children[1].value = True
        >>> dialog.children[3].value = "mygroup"
        >>> dialog.children[5].value = "private"
        >>> dialog.validate()
        {'clear scores': True, 'student group': 'mygroup', 'release mode': 'private'}

    The same, with a confirmation checkbox:

        >>> dialog.request_information(input=input,
        ...                            on_validate=on_validate,
        ...                            confirm=True)
        >>> dialog.children
        (Label(value='Are you sure?'),
         Checkbox(value=False),
         Label(value='clear scores'),
         Checkbox(value=False),
         Label(value='Student group'),
         Text(value=''),
         Label(value='Release mode'),
         Dropdown(options=('public', 'private'), value='public'),
         Button(button_style='danger', description='Cancel', style=ButtonStyle()),
         Button(button_style='success', description='Validate', disabled=True,
                style=ButtonStyle()))

        >>> dialog.children[3].value = True
        >>> dialog.children[5].value = "mygroup"
        >>> dialog.children[7].value = "private"

    Note that the the validate button is disabled. Let's check the
    Confirmation checkbox to enable the validate button:

        >>> dialog.children[1].value = True
        >>> dialog.children[9]
        Button(button_style='success', description='Validate', style=ButtonStyle())

    Now we can validate:

        >>> dialog.validate()
        {'clear scores': True, 'student group': 'mygroup', 'release mode': 'private'}
    """

    def __init__(self) -> None:
        super().__init__([])
        self.on_cancel: Optional[Callable] = None
        self.validate_button = ipywidgets.Button(
            description=_("validate"), button_style="success"
        )
        self.cancel_button = ipywidgets.Button(
            description=_("cancel"), button_style="danger"
        )
        self.validate_button.on_click(self.validate)
        self.cancel_button.on_click(self.cancel)
        self.cancel()

    def open_dialog(
        self,
        input_widgets: List,
        on_validate: Callable,
        on_cancel: Optional[Callable] = None,
    ) -> None:
        self.cancel()  # in case a dialog is currently open, cancel it
        self.children = [*input_widgets, self.cancel_button, self.validate_button]
        self.layout.display = ""
        self.on_cancel = on_cancel
        self.on_validate = on_validate

    def request_information(
        self,
        input: Dict[str, Any],
        on_validate: Callable,
        on_cancel: Optional[Callable] = None,
        confirm: bool = False,
    ) -> None:
        def make_widget(T: Union[type, tuple]) -> ipywidgets.Widget:
            if T is bool:
                return ipywidgets.Checkbox()
            if T is str:
                return ipywidgets.Text()
            if isinstance(T, (tuple, dict)):
                return ipywidgets.Dropdown(options=T)
            raise ValueError(f"Don't know how to produce a widget for type {T}")

        widgets = {key: make_widget(value) for key, value in input.items()}
        input_widgets = []
        if confirm:
            self.validate_button.disabled = True
            confirmUI = ipywidgets.Checkbox()

            def on_confirmed(_: Any) -> None:
                self.validate_button.disabled = not confirmUI.value

            confirmUI.observe(on_confirmed, names="value")
            input_widgets.extend([ipywidgets.Label(_("confirm")), confirmUI])

        for key, widget in widgets.items():
            input_widgets.extend([ipywidgets.Label(_(key)), widget])

        def c() -> None:
            on_validate(**{key: widget.value for key, widget in widgets.items()})

        self.open_dialog(
            input_widgets,
            on_validate=c,
            on_cancel=on_cancel,
        )

    def validate(self, button: Any = None) -> None:
        self.validate_button.disabled = True
        try:
            self.on_validate()
        except Exception:
            pass
        else:
            self.close_dialog()
        finally:
            self.validate_button.disabled = False

    def cancel(self, button: Any = None) -> None:
        if self.on_cancel is not None:
            self.on_cancel()
            self.on_cancel = None
        self.close_dialog()

    def close_dialog(self) -> None:
        self.children = []
        self.layout.display = "none"


class StatusBar(VBox):
    def __init__(
        self,
        authentication_widget: AuthenticationWidget,
        log: logging.Logger,
        form_dialog: Optional[FormDialog] = None,
    ) -> None:
        minimize_layout = {"flex": "0 0 content"}
        self.authentication_widget = authentication_widget
        self.form_dialog = form_dialog
        self.statusUI = Label(_("ready"), layout={"flex": "1 0 content"})
        self.log_show_UI = ToggleButton(
            description=_("show log details"),
            tooltip=_("show command log"),
            value=False,
            icon="eye",
            layout=minimize_layout,
        )
        self.log_level_UI = Dropdown(
            options=["WARNING", "INFO", "DEBUG"],
            tooltip=_("command log level"),
            layout=minimize_layout,
        )
        self.logUI = Output(layout={"width": "fit-content"})
        self.logUI.layout.display = "none"

        def set_log_show(event: Any) -> None:
            if self.log_show_UI.value:
                self.logUI.layout.display = "block"
                self.log_show_UI.icon = "eye-slash"
                self.log_show_UI.description = _("hide log details")
            else:
                self.logUI.layout.display = "none"
                self.log_show_UI.icon = "eye"
                self.log_show_UI.description = _("show log details")

        self.log_show_UI.observe(set_log_show, names="value")

        def set_log_level(event: Any) -> None:
            log.setLevel(self.log_level_UI.value)

        self.log_level_UI.observe(set_log_level, names="value")

        super().__init__(
            [
                HBox(
                    [
                        Label(_("status") + ": ", layout=minimize_layout),
                        self.statusUI,
                        self.log_show_UI,
                        self.log_level_UI,
                    ]
                ),
                self.logUI,
            ],
            layout=border_layout,
        )

    def run(
        self,
        action: str,
        command: Callable,
        kwargs: Dict[str, Any] = {},
        input: Dict[str, Any] = {},
        confirm: bool = False,
        on_finished: Optional[Callable] = None,
        on_success: Optional[Callable] = None,
    ) -> None:
        if self.form_dialog is not None:
            self.form_dialog.cancel()
        self.statusUI.value = action + ": " + _("ongoing")

        def finish(exit_status: str) -> None:
            if on_finished is not None:
                on_finished()
            self.statusUI.value = action + ": " + exit_status

        def request_information(input: Dict[str, Any], confirm: bool = False) -> None:
            assert self.form_dialog is not None
            self.statusUI.value = action + ": " + _("waiting for information")

            def on_validate(**information: Any) -> None:
                self.run(
                    action=action,
                    command=command,
                    kwargs={**kwargs, **information},
                    on_finished=on_finished,
                    on_success=on_success,
                )

            def on_cancel() -> None:
                finish(exit_status=_("canceled"))

            self.form_dialog.request_information(
                input=input,
                confirm=confirm,
                on_validate=on_validate,
                on_cancel=on_cancel,
            )

        if input or confirm:
            request_information(input=input, confirm=confirm)
            return

        with self.logUI:
            try:
                command(**kwargs)
            except MissingInformationError as e:
                request_information(e.missing)
            except (RuntimeError, subprocess.CalledProcessError) as e:
                finish(exit_status=_("failed with error", error=str(e)))
            except Exception as e:  # in case of unexpected exception
                finish(exit_status=f"{_('failed')}: {e}")
                raise
            else:
                if on_success is not None:
                    on_success()
                finish(exit_status=_("finished"))

    def run_in_subthread(
        self,
        action: str,
        command: Callable,
        on_finished: Optional[Callable] = None,
        on_success: Optional[Callable] = None,
    ) -> None:
        Thread(
            target=lambda: self.run(
                action=action,
                command=command,
                on_finished=on_finished,
                on_success=on_success,
            )
        ).start()


class AssignmentStudentDashboard(HBox):
    def __init__(
        self,
        assignment: Assignment,
        status_bar: Optional[StatusBar] = None,
        authentication_widget: Optional[AuthenticationWidget] = None,
    ):
        self.name = assignment.name
        self.assignment = assignment
        if authentication_widget is None:
            authentication_widget = AuthenticationWidget(assignment.forge)
        authentication_widget.on_login(self.update)
        self.authentication_widget = authentication_widget
        if status_bar is None:
            status_bar = StatusBar(
                authentication_widget=authentication_widget, log=assignment.log
            )
        self.status_bar = status_bar

        from ipylab import JupyterFrontEnd  # type: ignore

        self.jupyter_front_end = JupyterFrontEnd()

        layout = Layout(width="initial")
        self.nameUI = HTML(self.name, layout=layout)
        self.fetchUI = Button(
            description=_("fetch"),
            button_style="primary",
            icon="download",
            tooltip=_("fetch assignment", assignment_name=self.name),
            layout=layout,
            disabled=True,
        )
        self.fetchUI.on_click(lambda event: self.fetch())
        self.submitUI = Button(
            description=_("submit"),
            button_style="primary",
            icon="upload",
            tooltip=_("submit assignment", assignment_name=self.name),
            layout=layout,
            disabled=True,
        )
        self.submitUI.on_click(lambda event: self.submit())

        self.work_dir_UI = Button(
            description=_("open"),
            button_style="primary",
            icon="edit",
            tooltip=_("open assignment", assignment_name=self.name),
            layout=layout,
            disabled=True,
        )
        self.work_dir_UI.on_click(self.open_work_dir_callback)
        self.scoreUI = HTML("", tooltip=_("browse feedback"))
        self.updateUI = Button(
            description="",
            # button_style="primary",
            icon="rotate-right",
            tooltip=_("update view"),
            layout=layout,
            disabled=False,
        )
        self.updateUI.on_click(lambda event: self.update())

        self.submissionUI = HTML(layout=Layout(align_self="center"))

        self.other_actionsUI = Dropdown(
            description="",
            options=[
                (_("other actions"), ""),
                # (_("fetch from"), "fetch from"), # not ready yet
                (_("set student group"), "set student group"),
                (_("share with"), "share with"),
                (_("set main submission"), "set main submission"),
                (_("remove submission"), "remove submission"),
            ],
        )
        self.other_actionsUI.observe(lambda change: self.other_action(), names="value")

        HBox.__init__(
            self,
            [
                self.nameUI,
                self.fetchUI,
                self.work_dir_UI,
                self.submitUI,
                self.submissionUI,
                self.scoreUI,
                self.updateUI,
                self.other_actionsUI,
            ],
        )
        Thread(target=self.update).start()

    def update(self) -> None:
        # For now, fetching the assignment status requires the user to
        # be logged in. Fails gracefuly if this is not yet the case.
        try:
            status = self.assignment.status()
        except AuthenticationError:
            return
        if status.status == "not released":
            self.nameUI.value = self.name
            self.fetchUI.disabled = True
        else:
            repo = self.assignment.repo()
            self.nameUI.value = (
                f'<a href="{repo.web_url}" target="_blank">{self.name}</a>'
            )
            self.fetchUI.disabled = False

        if status.is_submitted():
            submission_repo = self.assignment.submission_repo()
            assert status.team is not None

            def annotation(username: str) -> str:
                result = ""
                assert status.team is not None
                if len(status.team) == 1:
                    return result
                if username == status.student:
                    result += f' ({_("me")})'
                if username == status.leader_name:
                    result += " *"
                return result

            self.submissionUI.value = (
                '<div style="line-height: 1.1;">'
                + "<br>".join(
                    f'<a href="{status.team[username].web_url}"'
                    f'  target="_blank">{username}</a>'
                    f"{annotation(username)}"
                    for username in sorted(status.team.keys())
                )
                + "</div>"
            )
        else:
            self.submissionUI.value = ""

        self.submitUI.tooltip = _("submit assignment", assignment_name=self.name)
        self.submitUI.disabled = True
        self.work_dir_UI.disabled = True
        if self.assignment.assignment_dir is not None and os.path.exists(
            self.assignment.assignment_dir
        ):
            self.work_dir_UI.disabled = False
            self.submitUI.disabled = False

        if status.autograde_status == "success":
            # these two s/could be provided by autograde_status
            try:
                badge = submission_repo.fetch_artifact(
                    status.autograde_job, artifact_path="feedback/scores.svg"
                ).text
            except requests.HTTPError:
                badge = _("browse")
            assert status.autograde_job is not None
            path_components = self.assignment.submission_path().split("/")
            feedback_url = (
                f"https://{path_components[0]}."
                f"{self.assignment.forge.base_url[8:]}-/"
                f"{'/'.join(path_components[1:])}/-/jobs/"
                f"{status.autograde_job['id']}/artifacts/"
                "feedback/scores.html"
            )
            self.scoreUI.value = f"<a href='{feedback_url}' target='_blank'>{badge}</a>"
        else:
            self.scoreUI.value = ""

        # repo = HTML('<a href="#" class="btn btn-primary btn-lg disabled"
        #        role="button" aria-disabled="true">Primary link</a>')
        # need to update repo_path

    def fetch(self) -> None:
        self.fetchUI.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("fetching assignment", assignment_name=self.name),
            command=self.assignment.fetch,
            on_finished=lambda: setattr(self.fetchUI, "disabled", False),
            on_success=self.update,
        )

    def submit(self) -> None:
        self.submitUI.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("submitting assignment", assignment_name=self.name),
            command=self.assignment.submit,
            on_finished=lambda: setattr(self.submitUI, "disabled", False),
            on_success=self.update,
        )

    def open_work_dir_callback(self, event: Any) -> None:
        self.work_dir_UI.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("open work dir", assignment_name=self.name),
            command=self.open_work_dir,
            on_finished=lambda: setattr(self.work_dir_UI, "disabled", False),
        )

    def open_work_dir(self) -> None:
        if self.assignment.assignment_dir is None:
            raise ValueError(_("cannot open work dir unset"))
        if os.path.isabs(self.assignment.assignment_dir):
            raise NotImplementedError(
                _(
                    _("cannot open work dir absolute"),
                    work_dir=self.assignment.assignment_dir,
                )
            )
        path = os.path.dirname(self.jupyter_front_end.sessions.current_session["path"])
        # TODO : if README.md does not exist neither, try to open gitlab file browser
        index_files = ["index.md", "index.ipynb", "README.md", "README.ipynb"]
        for x in index_files:
            file = os.path.join(self.assignment.assignment_dir, x)
            if os.path.isfile(file):
                self.jupyter_front_end.commands.execute(
                    "docmanager:open",
                    {
                        "path": path + "/" + file,  # Generalize if there is no index.md
                        "factory": "Notebook",
                        # 'options': {
                        #     'mode': 'split-right'
                        # },
                        "kernelPreference": {
                            "shutdownOnClose": True,
                        },
                    },
                )
                return
        raise FileNotFoundError(
            _(
                "no index file",
                assignment_dir=self.assignment.assignment_dir,
                index_files=" ".join(index_files),
            )
        )

    def other_action(self) -> None:
        action = self.other_actionsUI.value
        if not action:
            return
        input: Dict[str, Any]

        self.other_actionsUI.disabled = True

        def on_finished() -> None:
            self.other_actionsUI.index = 0

        self.other_actionsUI.disabled = False

        assert action in [
            "set student group",
            "share with",
            "set main submission",
            "fetch from",
            "remove submission",
        ]

        confirm = False
        command: Callable

        if action == "remove submission":
            confirm = True
            input = {}

            def command() -> None:
                self.assignment.remove_submission(force=True)

        elif action == "fetch from":
            # TODO this is not quite yet ready
            sources = {"assignment": self.assignment.repo()}
            status = self.assignment.status()
            assert status.team is not None
            for username in status.team.keys():
                sources[username] = status.team[username]
            command = self.assignment.merge_from
            input = {
                "source": sources,
                "on_conflict": (
                    "abort",
                    "backup and fetch",
                    "merge anyway",
                ),
            }

        elif action == "share with":
            command = self.assignment.share_with
            input = {"username": str}

        elif action == "set main submission":
            input = {"username": str}

            def command(username: str) -> None:
                # TODO: simplify and generalize:
                # - once leader_name can be passed down to submit without being ignored
                # - once there are dedicated method to set the leader or student group
                #   without submitting
                self.assignment.ensure_main_submission(leader_name=username)

        elif action == "set student group":
            command = self.assignment.submit
            assert isinstance(self.assignment, CourseAssignment)
            assert self.assignment.course.student_groups is not None
            input = {"student_group": tuple(self.assignment.course.student_groups)}

        self.status_bar.run(
            action=_(action),
            command=command,
            confirm=confirm,
            input=input,
            on_success=self.update,
            on_finished=on_finished,
        )


class CourseStudentDashboard(VBox):
    """
    A Jupyter-widget based course dashboard for students

    This class currently assumes that the user is logged in.
    """

    assignments: Tuple[str, ...] = ()
    assignment_dashboards: Dict[str, AssignmentStudentDashboard]

    def __init__(
        self,
        course: Course,
        subcourse: Optional[str] = None,
        student_group: Optional[str] = None,
    ):
        self.course = course

        if course.url:
            header_label = f'<a href="{course.url}" target="_blank">{course.name}</a>'
        else:
            header_label = course.name
        self.header = HBox(
            [
                HTML(
                    header_label,
                    layout={"flex": "1 0 content"},
                )
            ],
            layout=border_layout,
        )
        if self.course.subcourses is not None:
            self.subcourse_UI = Dropdown(
                description=_("subcourse"),
                value=subcourse,
                options=course.subcourses,
            )
            self.course.assignments = self.course.get_released_assignments()
            self.header.children += (self.subcourse_UI,)
            self.subcourse_UI.observe(
                lambda change: self.update_subcourse(), names="value"
            )
        else:
            self.subcourse_UI = Dropdown()

        self.authentication_widget = AuthenticationWidget(forge=self.course.forge)
        self.form_dialog = FormDialog()

        self.grid = GridBox(
            layout=Layout(
                grid_template_columns="repeat(8, max-content)",
                grid_gap="5px 5px",
                border=border_layout["border"],
            )
        )
        self.assignment_dashboards = {}

        self.status_bar = StatusBar(
            authentication_widget=self.authentication_widget,
            form_dialog=self.form_dialog,
            log=self.course.log,
        )

        self.updateUI = Button(
            description="",
            # button_style="primary",
            icon="rotate-right",
            tooltip=_("update view"),
            layout=Layout(width="initial"),
            disabled=False,
        )
        self.updateUI.on_click(lambda event: self.update(update_assignment_list=True))

        super().__init__(
            [
                self.authentication_widget,
                self.header,
                self.grid,
                self.form_dialog,
                self.status_bar,
            ],
            layout={"width": "fit-content"},
        )
        self.update(update_assignment_list=True)
        try:
            self.course.forge.login()
        except AuthenticationError:
            pass

    def update_subcourse(self) -> None:
        subcourse = self.subcourse_UI.value
        self.course.assignments = self.course.get_released_assignments(
            subcourse=subcourse
        )
        self.update(update_assignment_list=True)

    def update(self, update_assignment_list: bool = False) -> None:
        subcourse = self.subcourse_UI.value
        # if student_group is None:
        #    self.center = None
        if update_assignment_list:
            if self.course.assignments is not None:
                assignments = self.course.assignments
            else:
                assignments = self.course.get_released_assignments(subcourse=subcourse)
            if tuple(assignments) != self.assignments:
                self.assignments = tuple(assignments)
            else:
                update_assignment_list = False

        for assignment in self.assignments:
            if assignment not in self.assignment_dashboards:
                self.assignment_dashboards[assignment] = AssignmentStudentDashboard(
                    self.course.assignment(assignment),
                    status_bar=self.status_bar,
                    authentication_widget=self.authentication_widget,
                )

        if update_assignment_list:
            self.grid.children = [
                Label(_("assignment")),
                Label(""),
                Label(_("work directory")),
                Label(""),
                Label(_("submission")),
                Label(_("score")),
                self.updateUI,
                Label(""),
            ] + [
                widget
                for assignment in self.assignments
                for widget in self.assignment_dashboards[assignment].children
            ]


class AssignmentInstructorDashboard(HBox):
    def __init__(
        self,
        course: Course,
        assignment: CourseAssignment,
        force_autograding: bool,
        new_score_policy: str,
        student_group: Optional[Any] = None,
        release_mode: Optional[Any] = None,
        status_bar: Optional[StatusBar] = None,
        authentication_widget: Optional[AuthenticationWidget] = None,
    ):
        self.course = course
        self.student_group = student_group
        self.release_mode = release_mode
        # TODO: find better way to recover the assignment name
        self.name = assignment.name
        self.assignment = assignment
        if authentication_widget is None:
            authentication_widget = AuthenticationWidget(assignment.forge)
        self.authentication_widget = authentication_widget
        self.authentication_widget.on_login(self.update)
        if status_bar is None:
            status_bar = StatusBar(
                authentication_widget=authentication_widget, log=assignment.log
            )
        self.status_bar = status_bar

        from ipylab import JupyterFrontEnd  # type: ignore

        self.jupyter_front_end = JupyterFrontEnd()

        layout = Layout(width="initial")

        self.nameUI = Label(self.name)
        self.assignmentUI = HTML()  # layout=layout)
        self.generateButton = Button(
            description=_("generate"),
            button_style="primary",
            icon="cog",
            tooltip=_("generate assignment", assignment_name=self.name),
            layout=layout,
            disabled=False,
        )
        self.generateButton.on_click(lambda event: self.generate())
        self.generateStatus = Textarea(self.generate_status_cmd(), layout=layout)
        self.generateUI = VBox([self.generateButton, self.generateStatus])

        self.releaseButton = Button(
            description=_("release"),
            button_style="primary",
            icon="angle-double-up",
            tooltip=_("release assignment", assignment_name=self.name),
            layout=layout,
            disabled=False,
        )
        self.releaseButton.on_click(lambda event: self.release(self.release_mode))
        self.releaseStatus = Textarea(self.release_status_cmd(), layout=layout)
        self.releaseUI = VBox([self.releaseButton, self.releaseStatus])

        self.collectButton = Button(
            description=_("collect"),
            button_style="primary",
            icon="angle-double-down",
            tooltip=_("collect assignment", assignment_name=self.name),
            layout=layout,
            disabled=False,
        )
        self.collectButton.on_click(lambda event: self.collect())
        self.collectStatus = Textarea(
            self.count_submissions_cmd(submitted_directory="submitted"), layout=layout
        )
        self.collectUI = VBox([self.collectButton, self.collectStatus])

        self.force_autograding = force_autograding
        self.new_score_policy = new_score_policy

        # This widget is used to send javascript commands to the frontend
        self.open_url_widget = Output()

        # Formgrader zone
        self.formgraderButton = Button(
            description=_("formgrader"),
            button_style="primary",
            icon="book",
            tooltip=_("formgrader assignment", assignment_name=self.name),
            layout=layout,
            disabled=False,
        )
        self.formgraderButton.on_click(lambda event: self.open_formgrader_cmd(event))
        self.formgraderStatus = Textarea(
            self.count_submissions_need_manual_grade_cmd(), layout=layout
        )
        self.formgraderUI = VBox(
            [self.formgraderButton, self.formgraderStatus, self.open_url_widget]
        )

        self.feedbackButton = Button(
            description=_("feedback"),
            button_style="primary",
            icon="paper-plane",
            tooltip=_("feedback assignment", assignment_name=self.name),
            layout=layout,
            disabled=False,
        )
        self.feedbackButton.on_click(lambda event: self.feedback())
        self.feedbackStatus = Textarea(
            self.release_feedback_status_cmd(self.student_group), layout=layout
        )
        self.feedbackUI = VBox([self.feedbackButton, self.feedbackStatus])

        HBox.__init__(
            self,
            [
                self.nameUI,
                self.assignmentUI,
                self.generateUI,
                self.releaseUI,
                self.collectUI,
                self.formgraderUI,
                self.feedbackUI,
            ],
        )

        # Squash to zero width elements that are not relevant if the
        # underlying methods are not implemented in the course
        if not isimplemented(self.course.formgrader):
            self.formgraderUI.layout.display = "none"
        if not isimplemented(self.course.generate_feedback) or not isimplemented(
            self.course.release_feedback
        ):
            self.feedbackUI.layout.display = "none"

        Thread(target=self.update).start()

    def update(self) -> None:
        self.generateStatus.value = self.generate_status_cmd()
        self.releaseButton.disabled = True
        if self.release_mode is None:
            self.releaseButton.tooltip += _("needs release mode")
        elif self.assignment.is_generated():
            self.releaseButton.disabled = False
        # For now, fetching the assignment status requires the user to
        # be logged in. Fails gracefuly if this is not yet the case.
        try:
            is_released = self.assignment.is_released()
        except AuthenticationError:
            return
        if not is_released:
            self.assignmentUI.value = ""
            self.collectButton.disabled = True
        else:
            repo = self.assignment.repo()
            self.assignmentUI.value = (
                f'<a href="{repo.web_url}" target="_blank">{_("browse")}</a>'
            )
            self.releaseStatus.value = self.release_status_cmd()
            if self.course.student_groups is not None and self.student_group is None:
                self.collectButton.disabled = True
                self.feedbackButton.disabled = True
            else:
                self.collectButton.disabled = False
                self.feedbackButton.disabled = False
                self.formgraderButton.disabled = False

        self.collectStatus.value = self.count_submissions_cmd(
            submitted_directory="submitted"
        )
        self.formgraderStatus.value = self.count_submissions_need_manual_grade_cmd()
        self.feedbackStatus.value = self.release_feedback_status_cmd(self.student_group)

    def generate(self) -> None:
        self.generateButton.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("generating assignment", assignment_name=self.name),
            command=self.course.generate_assignment,
            kwargs={"assignment_name": self.name},
            on_finished=lambda: setattr(self.generateButton, "disabled", False),
            on_success=self.update,
        )

    def release(self, release_mode: Optional[Any] = None) -> None:
        if release_mode not in ["public", "private"]:
            self.course.log.error("Please set release mode: public or private.")
            return
        self.releaseButton.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("releasing assignment", assignment_name=self.name),
            command=self.course.release,
            kwargs={
                "assignment_name": self.name,
                "visibility": release_mode,
                "path": os.path.join(
                    self.course.release_directory, os.path.basename(self.name)
                ),
            },
            on_finished=lambda: setattr(self.releaseButton, "disabled", False),
            on_success=self.update,
        )

    def collect(self) -> None:
        self.collectButton.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("collect assignment", assignment_name=self.name),
            command=self.collect_cmd,
            on_finished=lambda: setattr(self.collectButton, "disabled", False),
            on_success=self.update,
        )

    def formgrader(self) -> None:
        self.status_bar.run(  # run_in_subthread(
            action=_("open formgrader", assignment_name=self.name),
            command=self.open_formgrader_cmd,
            kwargs={},
            on_finished=lambda: setattr(self.formgraderButton, "disabled", False),
            on_success=self.update,
        )

    def feedback(self) -> None:
        self.feedbackButton.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("feedbacking assignment", assignment_name=self.name),
            command=self.feedback_cmd,
            kwargs={"tag": "*"},
            on_finished=lambda: setattr(self.feedbackButton, "disabled", False),
            on_success=self.update,
        )

    def collect_cmd(self) -> None:
        if self.course.student_groups is not None and self.student_group is None:
            self.course.log.error(_("Must choose a student_group value"))
            return
        self.course.collect_in_submitted(
            assignment_name=self.name, student_group=self.student_group
        )
        self.course.ensure_autograded(
            assignment_name=self.name,
            student_group=self.student_group,
            force_autograde=self.force_autograding,
        )
        self.course.collect_autograded(
            assignment_name=self.name, student_group=self.student_group
        )
        self.course.collect_autograded_post(
            assignment_name=os.path.basename(self.name),
            on_inconsistency="WARNING",
            new_score_policy=self.new_score_policy,
        )

    def feedback_cmd(self, tag: str = "*") -> None:
        if self.course.student_groups is not None and self.student_group is None:
            self.course.log.error(_("Must choose a student_group value"))
            return
        self.course.generate_feedback(
            os.path.basename(self.name), tag=tag, new_score_policy=self.new_score_policy
        )
        self.course.release_feedback(self.name, student_group=self.student_group)

    def open_url(self, url: str) -> None:
        """
        Open a URL in a separate tab
        """
        # https://discourse.jupyter.org/t/widget-button-to-open-url/11634/2?u=nthiery
        with self.open_url_widget:
            display(Javascript(f'window.open("{url}");'))  # type: ignore

    def open_formgrader_cmd(self, event: Any) -> None:
        """
        Open nbgrader's formgrader in a separate tab

        Caveat: currently, the browser must allow popups for this to
        work. To avoid this, it would be best to use a link
        instead. However building this link requires the path to the
        directory holding the current notebook; at this stage we
        request this path to the frontend through a ipylab, which is
        an asynchronous operation. So we can't get the result at once
        when time the dashboard is built, but instead need to wait for
        a user interaction.
        """
        # Request the path to the directory holding the current
        # notebook from the root of Jupyter's server
        path = os.path.dirname(self.jupyter_front_end.sessions.current_session["path"])
        # Build the URL to the formgrader relative to this notebook
        # Uses https://github.com/jupyter/nbgrader/pull/1859 to open
        # the formgrader using the nbgrader_config.py file from that
        # path
        url = (
            "../" * (len(path.split("/")) + 2) + "formgrader"
            f"?path={path}"  # /gradebook/{os.path.basename(self.assignment.name)}
        )
        self.open_url(url)

    def generate_status_cmd(self) -> str:
        try:
            path = os.path.join(
                self.course.release_directory, os.path.basename(self.assignment.name)
            )
            date = subprocess.run(
                ["git", "log", "-1", "--format=%ai"],
                check=True,
                text=True,
                capture_output=True,
                cwd=path,
            ).stdout
            status = _("last generation", assignment_date=date)
        except (RuntimeError, subprocess.CalledProcessError, FileNotFoundError):
            status = _("not generated")
        return status

    def count_submissions_cmd(self, submitted_directory: str = "submitted") -> str:
        status = ""
        number_of_copies = len(
            glob.glob(
                f"{submitted_directory}/*/{os.path.basename(self.assignment.name)}",
                recursive=True,
            )
        )
        if number_of_copies > 0:
            status += _("Number of submissions", number_of_submissions=number_of_copies)
        return status

    def count_submissions_need_manual_grade_cmd(self) -> str:
        status = ""
        try:
            import numpy as np  # type: ignore

            # Create the connection to the database
            from nbgrader.api import Gradebook, MissingEntry  # type: ignore

            with Gradebook("sqlite:///.gradebook.db") as gb:
                grades = []
                counts = 0
                total = 0
                # Loop over each assignment in the database
                for student in gb.students:
                    # Try to find the submission in the database. If it doesn't exist,
                    # the `MissingEntry` exception will be raised, which means the
                    # student didn't submit anything, so we assign them a score of zero.
                    try:
                        submission = gb.find_submission(
                            os.path.basename(self.assignment.name), student.id
                        )
                    except MissingEntry:
                        pass
                    else:
                        total += 1
                        score = submission.score
                        grades.append(score)
                        if submission.needs_manual_grade:
                            counts += 1
                if len(grades) > 0:
                    status += _(
                        "Needs manual grading",
                        counts=counts,
                        mean=np.mean(grades),
                        dev=np.std(grades),
                    )
                else:
                    status = _("No grades")
        except ImportError:
            pass
        return status

    def release_status_cmd(self) -> str:
        try:
            p = self.course.forge.get_project(self.assignment.repo_path)
            status = _("last release", visibility=p.visibility, date=p.last_activity_at)
        except ResourceNotFoundError:
            status = _("not released")
        return status

    def release_feedback_status_cmd(self, student_group: Optional[Any]) -> str:
        try:
            url = self.course.forge.get_project(
                self.course.assignment(
                    self.assignment.name, student_group=student_group
                ).repo_path
            ).http_url_to_repo
            url = _("go to") + url.replace(".git", "/-/forks")
        except ResourceNotFoundError:
            url = _("not released")
        return url


class CourseInstructorDashboard(VBox):
    """
    A Jupyter-widget based course dashboard for instructors

    This class currently assumes that the user is logged in.
    """

    student_group_UI: Dropdown

    def __init__(
        self,
        course: Course,
        student_group: Optional[str] = None,
    ):
        self.course = course
        self.course.forge.login()

        self.release_mode = RadioButtons(
            description="",
            value=None,
            options=[(_("public"), "public"), (_("private"), "private")],
            layout={"width": "fit-content"},
        )

        if course.url:
            header_label = f'<a href="{course.url}" target="_blank">{course.name}</a>'
        else:
            header_label = course.name
        self.header = HBox(
            [
                HTML(
                    header_label,
                    layout={"flex": "flex-start"},
                ),
                VBox([Label(_("release mode")), self.release_mode], width="10px"),
            ],
            layout=Layout(border="1px solid black", grid_gap="5px 40px"),
        )

        if self.course.student_groups is not None:
            self.student_group_UI = Dropdown(
                description="",
                value=student_group,
                options=course.student_groups,
            )
            self.header.children += (
                VBox([Label(_("student group")), self.student_group_UI]),
            )
            self.student_group_UI.observe(lambda change: self.update(), names="value")
        else:
            self.student_group_UI = Dropdown()

        self.force_autograding = RadioButtons(
            description="",
            value=False,
            options=[False, True],
            layout={"width": "fit-content"},
        )
        self.new_score_policy = RadioButtons(
            description="",
            value="only_greater",
            options=[
                (_("only_empty"), "only_empty"),
                (_("only_greater"), "only_greater"),
                (_("force_new_score"), "force_new_score"),
            ],
            layout={"width": "fit-content"},
        )

        if isinstance(course, JupyterCourse):
            self.header.children += (
                VBox([Label(_("collect force new autograde")), self.force_autograding]),
                VBox([Label(_("new score policy")), self.new_score_policy]),
            )

        self.release_mode.observe(lambda change: self.update(), names="value")
        self.authentication_widget = AuthenticationWidget(forge=self.course.forge)

        self.n_grid = 5
        if isimplemented(self.course.formgrader):
            self.n_grid += 1
        if isimplemented(self.course.generate_feedback) and isimplemented(
            self.course.release_feedback
        ):
            self.n_grid += 1

        self.grid = GridBox(
            layout=Layout(
                grid_template_columns=f"repeat({self.n_grid}, max-content)",
                grid_gap="5px 5px",
                border=border_layout["border"],
            )
        )

        self.status_bar = StatusBar(
            authentication_widget=self.authentication_widget, log=self.course.log
        )

        super().__init__(
            [self.authentication_widget, self.header, self.grid, self.status_bar],
            layout={"width": "fit-content"},
        )
        self.make_grid()
        try:
            self.course.forge.login()
        except AuthenticationError:
            pass

        if isinstance(course, JupyterCourse):
            self.new_score_policy.observe(lambda change: self.update(), names="value")

    def update(self) -> None:
        self.make_grid()
        # Once it will be possible to update on the fly the student group of a course
        # assignment (which means updating the assignment repo and the fork_of_fork
        # field, it will be posible to simply update the assignment dashboards:
        # for assignment_dashboard in self.assignment_dashboards:
        #     Thread(target=assignment_dashboard.update).start()

    def make_grid(self) -> None:
        if self.student_group_UI.value is None:
            self.center = None
        if self.course.assignments is None:
            self.course.assignments = self.course.get_released_assignments()
            local_assignments = sorted(
                file
                for file in os.listdir(self.course.source_directory)
                if os.path.isdir(os.path.join(self.course.source_directory, file))
            )
            self.course.assignments += [
                assignment
                for assignment in local_assignments
                if assignment not in self.course.assignments
            ]

        self.assignment_dashboards = [
            AssignmentInstructorDashboard(
                self.course,
                self.course.assignment(
                    assignment_name, student_group=self.student_group_UI.value
                ),
                student_group=self.student_group_UI.value,
                release_mode=self.release_mode.value,
                force_autograding=self.force_autograding.value,
                new_score_policy=self.new_score_policy.value,
                status_bar=self.status_bar,
                authentication_widget=self.authentication_widget,
            )
            for assignment_name in self.course.assignments
        ]

        titles = [
            _("assignment"),
            _("assignment repository"),
            _("instructor workflow"),
            "",
            "Evaluations",
        ]
        titles = titles + [""] * (self.n_grid - 5)
        self.grid.children = [Label(label) for label in titles] + [
            widget
            for assignment_dashboard in self.assignment_dashboards
            for widget in assignment_dashboard.children
        ]


class CourseGradeDashboard(VBox):
    """
    A Jupyter-widget based course dashboard for grade managing.

    This class currently assumes that the user is logged in.
    """

    import numpy as np  # type: ignore
    import pandas as pd  # type: ignore

    def __init__(self, course: JupyterCourse) -> None:
        self.course = course
        self.course.forge.login()

        layout = Layout(width="initial")
        self.dashboard_grade_filename = "dashboard-grades.csv"
        if self.course.assignments is None:
            self.course.assignments = self.course.get_released_assignments()
        self.assignments_UI = Dropdown(
            description=_("assignments"),
            value=None,
            options=["all"] + [a for a in self.course.assignments],
            width="350px",
        )

        self.get_scores_UI = Button(
            description=_("update scores"),
            button_style="primary",
            icon="book",
            layout=layout,
        )
        self.get_scores_UI.on_click(lambda event: self.get_scores())

        self.clear_csv_UI = Button(
            description=_("clear scores"),
            button_style="primary",
            icon="trash",
            layout=layout,
        )
        self.clear_csv_UI.on_click(lambda event: self.clear_csv())

        self.copy_UI = Button(
            description=_("copy"),
            button_style="primary",
            icon="clipboard",
            layout=layout,
        )
        self.copy_UI.on_click(lambda event: self.copy_dataframe())

        self.header = HBox(
            [self.assignments_UI, self.get_scores_UI, self.clear_csv_UI, self.copy_UI],
            layout=border_layout,
        )
        if self.course.student_groups is not None:
            self.student_group_UI = Dropdown(
                description=_("student group"),
                value=None,
                options=["all"] + list(self.course.student_groups),
            )
            self.header.children = (self.student_group_UI,) + self.header.children

        self.authentication_widget = AuthenticationWidget(forge=self.course.forge)
        self.make_grid()
        self.status_bar = StatusBar(
            authentication_widget=self.authentication_widget, log=self.course.log
        )

        super().__init__(
            [self.authentication_widget, self.header, self.grid, self.status_bar],
            layout={"width": "fit-content"},
        )

        try:
            self.course.forge.login()
        except AuthenticationError:
            pass

    def update(self) -> None:
        self.refresh_scores()
        self.grid.data = self.df

    def make_grid(self) -> None:
        from ipydatagrid import DataGrid, TextRenderer, Expr  # type: ignore

        self.df = self.refresh_scores()

        renderers = {}
        for col in self.df.columns:
            if "note" in col and "/0" not in col:
                renderers[col] = TextRenderer(
                    text_color="black", background_color=Expr(_format_note)
                )
            elif "status" in col:
                renderers[col] = TextRenderer(
                    text_color="black", background_color=Expr(_format_status)
                )

        grid_layout = {"height": "300px"}
        self.grid = DataGrid(
            self.df,
            base_column_size=200,
            base_header_size=200,
            layout=grid_layout,
            editable=True,
            renderers=renderers,
        )
        self.grid.auto_fit_params = {"area": "all", "padding": 100}
        self.grid.auto_fit_columns = True

    def refresh_scores(self) -> Any:  # pandas.DataFrame
        import pandas as pd  # type: ignore

        if os.path.isfile(self.dashboard_grade_filename):
            df = pd.read_csv(self.dashboard_grade_filename, index_col=0)
        else:
            df = pd.DataFrame()
        col_students = ["group", "email"]
        col_assignments = [col for col in df.columns if "-" in col]
        self.df = df.reindex(col_students + sorted(col_assignments), axis=1)
        return self.df

    def get_scores(self) -> None:
        self.get_scores_UI.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("get scores"),
            command=self.get_scores_cmd,
            on_finished=lambda: setattr(self.get_scores_UI, "disabled", False),
            on_success=self.update,
        )

    def clear_csv(self) -> None:
        self.clear_csv_UI.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("clear grades"),
            command=self.clear_csv_cmd,
            on_finished=lambda: setattr(self.clear_csv_UI, "disabled", False),
            on_success=self.update,
        )

    def copy_dataframe(self) -> None:
        self.copy_UI.disabled = True
        self.status_bar.run(  # run_in_subthread(
            action=_("clear grades"),
            command=self.copy_cmd,
            on_finished=lambda: setattr(self.copy_UI, "disabled", False),
            on_success=None,
        )

    def get_scores_cmd(self) -> None:
        """Load all the grades for an assignment and student group.

        Grades are always exported in file dashboard-grades.csv.

        """

        import numpy as np  # type: ignore
        import pandas as pd  # type: ignore

        # load the requested assignments
        if self.assignments_UI.value is None or self.assignments_UI.value == "all":
            assignment_names = [
                assignment_name for assignment_name in self.assignments_UI.options[1:]
            ]
        else:
            assignment_names = [self.assignments_UI.value]
        # load the requested groupes
        if self.student_group_UI.value is None or self.student_group_UI.value == "all":
            student_groups = [
                student_group for student_group in self.student_group_UI.options[1:]
            ]
        else:
            student_groups = [self.student_group_UI.value]

        # load previous scores from dashboard-grades.csv
        d = {}
        if os.path.isfile(self.dashboard_grade_filename):
            df2 = pd.read_csv(self.dashboard_grade_filename, index_col=0)
            d = df2.to_dict("index")

        self.course.forge.login()
        for assignment_name in assignment_names:
            total = 0
            total_bad = 0
            for student_group in student_groups:
                # path = course.assignment_repo_path(assignment, student_group)
                try:
                    # project = course.forge.get_project(path)
                    # forks = project.get_forks(recursive=True)
                    submissions_status = self.course.assignment(
                        assignment_name=assignment_name, student_group=student_group
                    ).collect_status()
                    # course.log.info(f"Collecting autograded for
                    # {len(submissions_status)} students")
                    bad_projects = []
                    if len(submissions_status) == 0:
                        continue
                    for status in submissions_status:
                        student = status.student
                        if student is not None:
                            if student not in d.keys():
                                d[student] = {"group": student_group}
                                # for assignment in assignments:
                            d[student]["email"] = (
                                student + "@" + self.course.mail_extension
                            )
                            d[student][assignment_name + "-status"] = (
                                "as "
                                + student_group
                                + " with autograding="
                                + status.autograde_status
                            )
                            if status.autograde_status != "success":
                                self.course.log.info(
                                    f"missing successful autograde for {student}"
                                )
                                bad_projects.append(student)
                                continue
                            self.course.log.info(f"fetching scores for {student}")
                            if status.submission is not None:
                                repo = status.submission.repo
                                job = status.autograde_job
                                path = "feedback/scores.csv"
                                scores_txt = repo.fetch_artifact(
                                    job, artifact_path=path
                                ).text
                                scores = pd.read_csv(io.StringIO(scores_txt))
                                # TODO: add type check for scores to help mypy
                                total_score = np.sum(scores["total_score"].values)
                                max_manual_score = np.sum(
                                    scores["max_manual_score"].values
                                )
                                if (
                                    np.all(np.isnan(scores["manual_score"].values))
                                    and ~np.isnan(max_manual_score)
                                    and max_manual_score > 0
                                ):
                                    d[student][
                                        assignment_name + "-note "
                                        f"(/{int(scores['max_total_score'].values[0])})"
                                    ] = "attente notation manuelle"
                                else:
                                    d[student][
                                        assignment_name + "-note "
                                        f"(/{int(scores['max_total_score'].values[0])})"
                                    ] = total_score
                            else:
                                self.course.log.info(
                                    f"missing submission for {student}"
                                )
                                bad_projects.append(student)
                                continue
                    if len(bad_projects) > 0:
                        self.course.log.warning(
                            f"{len(bad_projects)} dépôt(s) avec"
                            " autograde_status!=success:"
                        )
                        for student in bad_projects:
                            self.course.log.warning(
                                f"student={student},"
                                f" status={d[student][assignment_name + '-status']}"
                            )
                    total += len(submissions_status)
                    total_bad += len(bad_projects)
                    self.course.log.warning(
                        f"{len(submissions_status)} projets soumis pour"
                        f" {assignment_name}, groupe {student_group},"
                        f" {len(bad_projects)} dépôt(s) corrompu(s)."
                    )
                except ResourceNotFoundError:
                    pass
            self.course.log.info(
                f"{total} projects submitted for {assignment_name}, {total_bad} repo(s)"
                " corrupted."
            )
        self.df = pd.DataFrame.from_dict(d, orient="index")
        self.df.index.name = "student_id"
        self.df.to_csv(self.dashboard_grade_filename)
        self.df = self.refresh_scores()
        self.update()

    def clear_csv_cmd(self) -> None:
        run(["rm", "-rf", self.dashboard_grade_filename])
        self.update()

    def copy_cmd(self) -> None:
        import numpy as np  # type: ignore

        df2 = self.df.replace("attente notation manuelle", np.nan)
        df2.to_clipboard(excel=True)


def _format_note(cell: Any) -> str:
    return "yellow" if cell.value == "attente notation manuelle" else "white"


def _format_status(cell: Any) -> str:
    if "autograding=success" in cell.value:
        return "lightgreen"
    elif "autograding=none" in cell.value:
        return "red"
    else:
        return "white"
