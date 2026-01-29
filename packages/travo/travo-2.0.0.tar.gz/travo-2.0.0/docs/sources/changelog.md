# What's new?

## Version 2.0.0

### Maintenance

- The minimal supported Python version is now 3.10.
- [Remove now unneeded `dataclasses` package from the dependencies](https://gitlab.com/travo-cr/travo/-/merge_requests/219)

### New features

- New autograding functions:
  - possibility to run local_autograde to grade local submissions from the submitted directory and merge the gradebooks
  - run forge_autograde to repost a submission that an instructor has modified
- Authentification via personal access token is now possible.
  This is mandatory when double authentication or Single-Sign-On
  is enabled on the forge

### Bug fixes

- Fix generation of assignments for Jupyter courses with markdown notebooks ([!211]https://gitlab.com/travo-cr/travo/-/merge_requests/211)
- Quick fix to manage long and short username on upsaclay gitlab forge([!213](https://gitlab.com/travo-cr/travo/-/merge_requests/213))
- `generate_assignment_content` produces a student version even if source is not a git repo

### Test infrastructure

- Add a `rich_jupyter_course` fixture for `jupyter_course` module testing ([!216](https://gitlab.com/travo-cr/travo/-/merge_requests/216))
- Omit `tests` directory from coverage ([!216](https://gitlab.com/travo-cr/travo/-/merge_requests/216))

## Version 1.1.3

Fix missing `pytest` dependency.

## Version 1.1.2

### Test infrastructure

- Tests needing to connect to a gitlab instance are skipped when the instance
  is not running (issue [#119](https://gitlab.com/travo-cr/travo/-/issues/119))
- Improve coverage

### Instructor dashboard
- When `course.assignments` is not specified, include local assignments in
`course.source_dir` in addition to assignments already published on the
forge [#207](https://gitlab.com/travo-cr/travo/-/merge_requests/207).

## Version 1.1.1

- Handle gracefully assignment names given with a trailing /
  (issue [#74](https://gitlab.com/travo-cr/travo/-/issues/74))
- Fix optional arguments parsing on the command line (issues
  [#31](https://gitlab.com/travo-cr/travo/-/issues/31),
  [#117](https://gitlab.com/travo-cr/travo/-/issues/117),
  [#109](https://gitlab.com/travo-cr/travo/-/issues/109))

## Version 1.1

- The minimal supported Python version is now 3.9.
- Improved Windows compatibility.
- New argument `initialized` for `Project.ensure_fork` and `Assignment.ensure_submission_repo` to ensure that the project should be initialized with the content of the origin repository upon creation.
- `GitLab.get_branch` now raises `ResourceNotFound` if the branch is missing.
- Manage jupyter courses with jupyter lab options rather than jupyter notebook.
- Apply `ruff` linting and formatting.
- move build process from `flit` to `hatch` so development versions can be
identified.

### Student dashboard

- New student actions available through a dropdown menu
  - share with (team work)
  - set main submission (team work)
  - remove submission
  - merge from another submission
- Smoother User Experience through form dialogs that appear only when
  information is required from the user (e.g. to choose the student group)

### Test infrastructure

- Improved test robustness with test (rich) course paths and names parametrised by test run id.
- New fixtures: `to_be_teared_down`, `rich_course_deployed`.
- New context managers: `travo.util.working_directory`, `Gitlab.logged_as`.
- Refactor user creation in basic gitlab infrastructure.

### Misc

- Refactored `Assignment.merge`

## Version 1.0

The 1.0 release has focused on:
- simplicity of use, especially for simple courses: tutorial, more automation and dashboards,
- backward incompatible changes to better support the best practices,
- backward incompatible changes that helped improve the code quality,
- quality of the code.

In particular:
- the minimal supported Python version is now 3.8,
- black formatting has been applied.

Users are strongly advised not to upgrade to version 1.0 during teaching sessions.

### New features

- Add `quickstart` and `deploy` utilities to ease course creation and deployment (see the
  [quickstart tutorial](quickstart_tutorial)).
- Fix and generalize the instructor dashboard to make it work with any course, including
  courses not using Jupyter notebooks and nbgrader.
- Generalize assignment generation to simple courses.

### Documentation

- Add installation instructions.
- Update tutorials, in particular about [creating and deploying a course](quickstart_tutorial).
- Update and improve docstrings.
- Add developer's guide.

### Backward incompatibilities

- Change default values in `course.py`:

  - `group_submission` is now set to `True`, submissions are grouped by course and session,
    in `https://<forge>//<student>-travo/<course>/<session>/<assignment>` rather than
    `https://<forge>/<student>/<course>-<session>-<assignment>`;
  - `student_dir` is now set to `./`.
- Rename `assignment` attributes and parameters to `assignment_name`.
- Rename `personal_repo` attributes and parameters to `submission`.
- `GitLab.get_user()` throws an exception is called without the `username` parameter.
- Refactor `Course.collect()` collecting student submissions.

### Bug fixes

- Fix name incompatibilities with gitlab and FQDN standards.
- Better interactions with Instructor and student dashboards.
- Fix `Projet.get_creator()` where the current user was returned, rather than the
  student having submitted.

### Command line

- Add `--version` option to the command line.
- Fix boolean options in command line.

### Test infrastructure

- Improve the usability of the test gitlab instance.
- Improve test coverage.
- Allow all the tests to be run locally.

### Translations

- Switch to `i18nice` for localization.
- Improve dashboard translations.
