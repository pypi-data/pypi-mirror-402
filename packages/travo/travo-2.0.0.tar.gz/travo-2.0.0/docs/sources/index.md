# `Travo`: Distributed GitLab ClassRoom

[![PyPI version](https://badge.fury.io/py/travo.svg)](https://badge.fury.io/py/travo)
[![conda version](https://anaconda.org/conda-forge/travo/badges/version.svg)](https://anaconda.org/conda-forge/travo)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://gitlab.com/travo-cr/travo/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://gitlab.com/travo-cr/travo)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

`Travo` (**[t&#641;a&apos;vo]**) is a lightweight open source Python toolkit that turns your
favorite GitLab [forge](https://en.wikipedia.org/wiki/Forge_(software))
into a flexible management solution for computer assignments, à la
[GitHub classroom](https://classroom.github.com/). It does so by
automating steps in the assignment workflow through Git and [GitLab's
REST API](https://docs.gitlab.com/ce/api/).
It takes its name from the practice sessions linked to a course, called in French
*Travaux Pratiques*.

Rationale: *Teaching computer science or computational courses is all
about collaboration on code. It is thus unsurprising that, with a
pinch of salt, software forges like GitLab can provide helpful
infrastructure to support and enhance that collaboration.*

## Features

- **Easy to use for students**: simple workflow with two automated
  operations: `fetch` and `submit`, available from the terminal or a
  widget-based dashboard in Jupyter.
- **Flexible and battlefield tested** on small to large courses (300+
  students at lower undergraduate level) with optional support for
  multiple assignments, student groups, instructors, and sessions, as
  well as (basic) team work.
- **Distributed and personal-data friendly**: Travo can be used with
  any instance of GitLab, including a self-hosted one on premises by
  your institution. No other infrastructure is needed. Students and
  instructors can use any work environment (personal laptop, computer
  labs, JupyterHub, Docker images...) provided that Travo is
  installed.
- **Command Line Interface** (CLI) for most common usages.
- **Graphical User Interface within Jupyter** with student and
  instructor dashboards.
- **Automatic and manual grading of Jupyter assignments** through
  [nbgrader](https://nbgrader.readthedocs.io/) integration.
- **Empowering**: Travo manages assignments according to standard Git
  and GitLab software development workflows, and opens the door for
  your students and instructors to discover at their pace version
  control, forges, collaborative development and devop practices.
- **Lightweight, modular and extensible**: you use whichever part of
  Travo is convenient for you and ignore, extend or replace the
  rest. For example, instructors can setup tailored CLI Python scripts
  for their courses, or bespoke automatic grading using Continuous
  Integration.
- **Internationalized**: French, English (in progress); more languages
  can be added.

## Tutorials

- The [Quickstart](quickstart_tutorial) guides you through the process
  of setting up a simple (Jupyter-based) course using Travo to
  distribute and collect course assignments.
- The [assignment tutorial](tutorial), presents the basic concepts
  behind Travo and explains more in depth how to use it for a single
  assignment.
- The [advanced tutorial](tutorial-advanced) covers Travo’s support
  for courses which may have multiple assignments, instructors,
  sessions, or student groups.

## Screenshots

Fetching and submitting assignments from the terminal:

```shell
./course.py fetch Assignment1
```

```shell
./course.py submit Assignment1
```

The student dashboard for Jupyter users :

![Student dashboard](talks/student_dashboard.png)

Overview of student submissions on GitLab :

![student submissions](talks/vue-soumissions-groupe.png)

## Requirements and installation

Travo requires Python >= 3.10. It can be installed from
[pypi](https://pypi.org/) with:

    pip install travo

or from [conda forge](https://conda-forge.org/) with:

    conda install -c conda-forge travo

The development version can be installed with:

    pip install git+https://gitlab.com/travo-cr/travo.git

For more details check the
[installation instructions](install).

## Authors

Pierre Thomas Froidevaux, Alexandre Blondin-Massé, Chiara Marmo,
Jérémy Neveu, Jean Privat, Nicolas M. Thiéry, with contributions from
Nicolas Grenier, Corentin Morice, Viviane Pons, Marco Pasi, and Brian
Ravenet.

## Contributing

Feedback, e.g. by posting
[issues](https://gitlab.com/travo-cr/travo/-/issues), and
[contributions](https://travo-cr.gitlab.io/travo/contributing.html) are most welcome!

## Brief history and status

Travo started in Spring 2020 at [UQAM](https://uqam.ca/) as a shell
script. See the [Legacy User
Interface](https://gitlab.info.uqam.ca/travo/travo-legacy). The user
interface was completely refactored in Summer and Fall 2020. Travo was
then reimplemented in Python in Winter 2021 and continuously expanded
since. Travo is used in production in a dozen large classes at
[Université Paris-Saclay](https://universite-paris-saclay.fr/) and
[UQAM](https://uqam.ca/), and many other smaller classes.

- **Documentation:** The tutorials could use some more love. On the
  other hand we would be very happy to help you get started as this is
  the most efficient approach to explore new use cases and improve the
  documentation. Get in touch!
- **Better messages:** less verbosity by default; provide tips on what
  to do next.
- **Internationalization:** Basic support for internationalization has
  been set up, and many, but not all, messages are available both in
  French and English. The next steps are to scan the Travo library to
  use internationalization in all messages, and to translate the
  messages. Contributions welcome!
- **Support for collaborative work:** in progress, with experimental
  support for modeling teams of students working collaboratively on an
  assignment, with basic tooling for students. Tooling for instructors
  remains to be implemented.
- **Forge agnosticism:** Currently, only GitLab is supported, but the
  code was designed to be modular to make it easy to support other
  forges (e.g. GitHub).
- **Automatic grading:** Support for a wider range of use cases beyond
  Jupyter assignments; tighter integration with nbgrader for Jupyter
  assignments.

```{toctree}
---
maxdepth: 3
caption: User guide
hidden:
---
changelog
install
authentication
quickstart_tutorial.rst
Assignment Tutorial <tutorial>
Advanced course tutorial <tutorial-advanced>
```
```{toctree}
---
maxdepth: 2
caption: Development
hidden:
---
contributing
API <autoapi/travo/index>
```
