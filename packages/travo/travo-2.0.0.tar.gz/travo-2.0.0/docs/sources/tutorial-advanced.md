# Travo advanced tutorial

In the [basic tutorial](tutorial.md), we have seen how to use GitLab
and Travo to handle a single assignments. This tutorial suggests some
setups for courses with e.g. several assignments, several groups of
students, or several sessions. These setups emerged from several
iterations of running large courses by the authors, and a few goodies
were added in Travo to support them. Other than this, Travo tries to
be setup agnostic; you are welcome to try others and report!

## Digression: Travo as a Python library

So far, we have been using Travo through the `travo` command line
interface. The core of Travo however is a Python library, and
`travo` is just one of many ways to access it. Instead of running from
the command line:

    travo fetch https://...

you can for example call from Python (e.g. in a Jupyter notebook):

    Travo().fetch("https://...")

Internally, this uses a bridge that automatically maps the command
line interface to Travo's Python API.

## Basic course configuration and usage

Using the generic `travo` script is fine for basic usage. For more
advanced course setups, one may want to configure, customize, or
extend Travo:

* Use simple names for assignment, instead of long URLs
* Provide course-specific documentation
* Enforce conventions
- Customize or add specific functionality (grading, feedback, ...)

This can be achieved through a dedicated Python script for the course.
The script name is arbitrary. We will use `<script>` below to refer to
it.

Here is an example; details will be explained throughout the tutorial.
The core is the course course object which holds some configuration;
it could be used from Python as well.

```
#!/usr/bin/env python

from travo import GitLab
from travo.course import Course
from travo.script import main

forge = GitLab("https://gitlab.example.com")
course = Course(forge=forge,
                path="MyCourse",
                name="My course",
                session_path="2023-2024", # session name (must be a valid path)
                student_dir="./",
                script="<script>",
                # Additional configuration goes here
                )

usage = f"""Help for {course.script}
======================================

Download or update an assignment (here for Assignment1):

    {course.script} fetch Assignment1

Submit your assignment (here for Assignment1)

    {course.script} submit Assignment1

More help:

    {course.script} --help
"""


if __name__ == '__main__':
    main(course, usage)
```

### Setting up the course on GitLab

The teaching material that students work on is typically broken up
into several (e.g. weekly) assignments. In practice, it's handy to
break accordingly the material into git repositories. Thereby, the
forge will hold, for each course, a collection of repositories: one
per assignment, and possibly others. These can conveniently be grouped
together using, well, a group! Using a dedicated group, rather than
one's own namespace also offers more flexibility.

1. From GitLab's web interface, create a new public group for your
   course. In the example, this is `MyCourse`, hosted on the GitLab
   instance `https://gitlab.example.com/`.
2. In the script, set accordingly the `path` and `name` entries.
3. Make the script available to your students and instructors by any
   mean: installing in the computing environment, making it available
   for download, ... An example will be provided below.

Courses with multiple sessions or groups need some more setup before
publishing assignments; please read the corresponding sections.

### Preparing assignments

As in the basic tutorial, an assignment is a normal Git repository
which can published.

Alternatively, on may use Travo:

1. Prepare a directory in your work environment holding the assignment
   files
2. Initialize the assignment directory as a git repository, typically
   by issuing the following commands from within the directory:

        git init
		git add .
		git commit -m "Assignment preparation"

3. Use Travo to publish the assignment from within the assignment
   directory:

	    <script> release Assignment1

For testing purposes, we recommend to first publish the assignment
privately, so that only the instructors can access it:

	    <script> release Assignment1 --visibility=private

and publish it publicly only when students need to access it. Indeed,
it often happens that some students fetch assignments in advance,
leading to potential conflicts should the assignment need to be
amended.

### Student workflow

The student workflow is as in the basic workflow, except that they use
the provided script and can refer to assignments just by their name:

    <script>                      # Displays basic usage
    <script> fetch Assignment1
    <script> submit Assignment1

Unlike in a basic fork, the name and path of the student's submission
will be prefixed with the course name. This avoids conflicts between
courses having assignments with the same name (e.g. `Assignment1`!),
and help grouping assignments by course in the student dashboard.

<div class="alert alert-info">

One would want to group the assignments of a course in a subgroup of
the student's namespace; however such subgroups are not (yet?)
supported by GitLab.

<div>

### Collecting assignments

The following command will clone all the student submissions for the
given assignment in the current directory:

	<script> collect Assignment1

To restrict to submissions from a given student, or from students in a
given student group, or to submissions before a given date, see:

	<script> collect --help

### Summary

Your setup should now look like:

Instructor side:

- https://gitlab.example.com/MyCourse (public)
  - Root group for the course
  - Members: the instructors
- https://gitlab.example.com/MyCourse/Assignment1 (public)
  - Repository holding `Assignment1`
- ...

Student side:

- https://gitlab.example.com/john.doo/MyCourse-Assignment1 (a private
  fork of the assignment `Assignment1`, shared with the instructors in
  `MyCourse`)
  - The student's submission for `Assignment1`

## Advanced course configuration and usage

### Distributing the course script with Git

Most of the authors' courses now use the following setup to distribute
the course script:

1. Create a public repository `ComputerLab` in `MyCourse`.
2. Add the course script, under the name `course.py`
3. Bonus: add any other content required to reproduce the environment
   needed to work on the assignments (hence the name Computer Lab).
   Typically a list of software packages that should be installed
   (e.g. in an `environment.yml` file for Conda or `requirements.txt`
   for pip).
4. Add the following configuration in the course script:

        student_dir="./",
        script="./course.py",

5. Provide the following instructions to the students:

        git clone https://gitlab.example.com/MyCourse/ComputerLab MyCourse
	    cd MyCourse
        ./course.py fetch Assignment1
		./course.py submit Assignment1

Then, in the student's work environment, the course work directory
`MyCourse/` will conveniently hold both the course script and the work
copies of all the assignments all in the same place. Students are free
to create or move this directory anywhere they wish.

Tip for JupyterHub users:
[nbgitpuller](https://jupyterhub.github.io/nbgitpuller/) may be used
to automate the cloning or updating of the `MyCourse` directory when
students open an appropriately crafted URL.

### Complete beginners: enforcing the work directory and preinstalled script (optional)

For courses with complete beginners having blurry notions of file
systems and directory, you may want to enforce a designated course
work directory. This prevents students from inadvertently having
several work copies for the assignments. Also students need not worry
about where they run the course script. Altogether, the student
actions become more reproducible, making it easier to debug for
instructors.

1. Add the following configuration in the course script:

        student_dir="~/MyCourse",
        script="~/MyCourse/course.py",

2. Replace `MyCourse` by `~/MyCourse` in the student instructions.

If you can, you may further rename the script after the course's name
(e.g. `info-111`), and install it in the work environment. Then the
instructions can be simplified to:

        info-111 fetch Assignment1
        info-111 submit Assignment1

### Publishing erratas (optional)

Assume that you discover some issue or potential improvement in an
assignment that some students have already fetched (sounds familiar,
right?). Changing the assignment will let student benefit from your
discovery; but may cause confusion, unequal treatment of students, or
conflicts.

As a small help, Travo offers the option to publish the changes as
erratas, keeping the main branch untouched:

1. From the assignment directory, create a new branch `errata`

        git checkout -b errata

2. Apply the desired changes to the files, and commit:

        git commit -m "Errata: fixed XXX"

3. Publish again:

	    <script> releases Assignment1

Upon the next fetch by a student, Travo will try to merge the erratas
in the student's work copy of the assignment, and fail gracefully if
it can't.

Tip: stick to minor changes which are likely to merge smoothly,
typically touching only read-only parts of the assignment like
instructions. Your mileage will vary for what minor should be.

### Expiring access to student submissions

It's possible to configure the course so that the instructor's access
to student submissions automatically expires after a certain date.

1. Add a line to the configuration such as:

        expires_at="2022-12-31",

The submission are not deleted. However only students can access them.

Use cases:
- Satisfying legal constraints.
- Taming the number of projects in the instructors dashboard.

### Handling non public assignments (optional)

In this tutorial, all repositories and groups holding assignments are
public. This is by design, as we like our course material to be
available publicly under an open license like Creative Commons.
However there is no technical barrier in using private repositories
instead; the only complication is to explicitly grant students access
to them. This can in principle be achieved by modeling the students'
cohorts by mean of groups. This requires some synchronization with the
information system of the institution, typically the students'
Learning Management System (e.g. Moodle).

Contributions to automate this process are welcome.

### Handling multiple instructors (optional)

For the sake of simplicity, we call **instructor** anyone who should
have access to the students' submissions: graders, ...

1. From GitLab's web interface, add the other instructors as member of
   that group (group page -> Members -> Add). If the course has
   multiple sessions or multiple student groups, you may want to read
   the next two sections first.

### Handling multiple sessions (optional)

When the same course is delivered in multiple sessions (e.g. in yearly
sessions like 2020-2021, 2021-2022), one typically want to keep the
student cohorts separate.

1. For each session, create a dedicated public subgroup of the
   course's group. This is where assignments will be hosted, hence we
   call this subgroup the **assignment group**.
2. In the configuration, set `session` accordingly; here is an example:

        session=2021-2022,

   Note: if there are several concurrent sessions, each session will
   need its own script.

3. The submission of a student will be hosted on GitLab in
   `<username>/<course>-<session>-<assignment>` (see also `Grouping
   Submissions` below). This way, a student may
   participate to several sessions, with a clear separation between
   their submissions for each session.

3. If certain instructors only participates to certain sessions, you
   may add them as members of the session's groups, rather than of the
   main course group. This way they will only be granted access to the
   submissions for that session.

### Handling multiple student groups (optional)

When the course is delivered to several student groups simultaneously
(e.g. ) instructors may want to do certain operations -- like
collecting submissions -- only for a given student group instead of
for the whole cohort. In Travo, we model this by having, for each
student group, a dedicated public subgroup of the assignment group.

1. In the script, insert an entry such as:

        student_groups=['Group1', 'Group2', ...],

2. You may create the student groups by hand from GitLab's web
   interface. Alternatively, they will be created automatically the
   first time an assignment is published.
3. If instructors should only be granted access to a given student
   group, you may add them as member of this group, rather than of the
   session, assignment, or course groups.
   Caveat: this has not been tested. Please try and report!

How does it work?

The student group membership is modeled on an assignment basis: for
each assignment hosted in the assignment group, a fork of the
assignment shall be created within each student group. Student
submissions will be created as forks of these rather than forks of the
original assignment.


![A student submission](talks/depot-personnel.png)

Figure: A student submission on GitLab for the course Info111, session
2020-2021, student group MI3, and assignment Semaine4.


On GitLab's web interface, the student submissions for a given group
can be retrieved by navigating to the student group, choosing the fork
of the assignment there and browsing its forks. Or equivalently by
browsing the forks of the forks of the assignment in the assignment
group.


![Overview of submissions per group](talks/vue-soumissions-synthese.png)

Figure: Browsing the forks page of the original assignment provides an
overview of the submissions per student group. For example, for the
course Info111, session 2020-2021, student group MI3, and assignment
Semaine4, there were 24 student submissions.

![Overview of submissions for a group](talks/vue-soumissions-groupe.png)

Figure: Browsing the forks page of the fork of the assignment in a
student group provides an overview of the student submissions for that
group. Here, this is for course Info111, session 2020-2021, and
student group MI3.


Upon submitting, students should specify the name of their group:

    <script> submit Assignment1 Group1

At any point, they may resubmit with a different group (e.g. if they
make a mistake or change group). The fork relation is updated
accordingly, so the new group **replaces** the previous one.

Most instructor's operations can be run on a single student group
rather than the whole cohort; e.g.:

    <script> collect Assignment1 Group1

### Grouping submissions (experimental)

User submissions on the forge are, by default, stored directly in the
user's namespace, with a path such as
`<username>/<course>-<session>-<assignment>`.

Alternatively, with the following setting in the configuration:

    group_submissions=True

user's submissions will be stored in a dedicated group, with
subgroups to group them by course and session, using a path such as:
`<username>_travo/<course>/<session>/<assignment>`.

The use of a dedicated group is required because GitLab does not allow
for creating subgroups in the user's namespace.

<div class="alert alert-warning">

The username in `<username>_travo` is mangled by substituting '.' with
'_'.

**Motivation:** namespaces that contain a `.`, like a user's namespace
of the form `first.last` cause trouble with GitLab Pages (for [SSL
encryption](https://docs.gitlab.com/ee/user/project/pages/introduction.html#subdomains-of-subdomains)
[cookies](https://docs.gitlab.com/ee/user/project/pages/#namespaces-that-contain-));
this is annoying in the context of Travo because GitLab pages are
typically used to publish grading results. Thanks to the mangling,
grouping submissions provides a workaround for this limitation as a
side benefit.

</div>

<div class="alert alert-warning">

**Caveat:** there is a minimal but non zero risk of username
collisions. Either with another user with username `john_travo`.  or
between two users with respective usernames `john_doo` and `john.doo`.

</div>

<div class="alert alert-info">

Grouping submissions may eventually become the default behavior.

</div>

### Anatomy of an elaborate course

We briefly describe the anatomy of one of our elaborate courses with
multiple assignments, instructors, sessions, and groups.

#### On the forge

- https://gitlab.dsi.universite-paris-saclay.fr/Info111 (public)
  - Root group for the course
  - Members: long term instructors for the course
- https://gitlab.dsi.universite-paris-saclay.fr/Info111/Info111 (public or private)
  - Typically named `Instructors` in other courses
  - Contains all the source material for the course, including the
    instructor's versions of the assignments, with solutions
  - Travo currently does not touch it, nor even knows it exists
- https://gitlab.dsi.universite-paris-saclay.fr/Info111/2020-2021/ (public)
  - Group holding all the assignments
  - Members: yearly instructors for the course
  - Description: Équipe pédagogique 2020-2021 et sujets étudiants
- https://gitlab.dsi.universite-paris-saclay.fr/Info111/2020-2021/Semaine1 (public)
  - Repository holding the student version of the assignment
    `Semaine1`. In our setup, it's automatically prepared from the
    instructor's version using nbgrader, and published with the help
    of Travo.
- https://gitlab.dsi.universite-paris-saclay.fr/Info111/2020-2021/MI1 (public)
  - GitLab group holding the assignments for the student group MI1
- https://gitlab.dsi.universite-paris-saclay.fr/Info111/2020-2021/MI1/Semaine1 (public)
  - A plain fork of `2020-2021/Semaine1`
  - Just there to track the student's forks per group

#### In the work environment (laptop, lab, JupyterHub, ...)

For students:
- Course directory: `~/ProgImperative`
- Directory for assignment `Semaine1`: `~/ProgImperative/Semaine1`

Travo config and bookkeeping files (in principle, there is no need to mess with them):
- `~/.travo/`
-` ~/.travo/tokens/gitlab.dsi.universite-paris-saclay.fr`

#### In the travo script

Example script:
- https://gitlab.dsi.universite-paris-saclay.fr/Info111/ComputerLab/-/blob/master/course.py

Configuration:

    from travo import GitLab, Course

    forge = GitLab("https://gitlab.dsi.universite-paris-saclay.fr")
    course = Course(forge=forge,
                    path="Info111",
                    name="Info 111 Programmation Impérative",
                    assignments_group_path="Info111/2020-2021",
                    assignments_group_name="2020-2021",
                    student_dir="~/ProgImperative",
                    script="info-111",
                    expires_at="2022-12-31",
                    student_groups=["MI1", "MI2", "MI3"])

#### In the user interface

Typical operations for students from the command line:

    <script> fetch Semaine1
    <script> submit Semaine1 MI1

Python counterparts:

    course.fetch("Semaine1")
    course.submit("Semaine1", "MI1")

Typical operations for instructors:

    <script> release Semaine1
    <script> collect Semaine1
    <script> collect_feedback Semaine1

These high level operations are built on top of general purpose
operations for interacting with a forge through its API. The important
ones take the form of idempotent operations that ensure the existence
of a given ressource, configured in a given way:

    gitlab.ensure_group(path="Info111", name="Info111")
    gitlab.ensure_project(path="Info111/2020-2021/Instructors", "Instructors", visibility="private")

### Handling collaboration within the instructor team

Git and GitLab are also natural tools for handling collaborations
within the instructor team. The authors typically use:

- A public (?) project `MyCourse/Instructors` holding the instructor
  version of the course material.
- A private project `MyCourse/Private` holding sensitive data
  (e.g. exams subjects). This project is also used for project
  management (team discussions, task tracking ...), using issues.

Whether the `Instructors` project shall be public or private is a
tough decision, because they typically hold solutions. On the one hand
we want to promote findability and reuse of the course material --
including exercise and solutions -- by other instructors; on the other
hand we want to hide solutions for students. Should the project be
private, it could be merged with `Private`.

![A course dashboard](talks/tableau-de-bord.png)

Figure: GitLab issue boards provide the instructor team with a
convenient dashboard to get an overview of ongoing tasks and
discussions.

Tip: do not store personal information about students in the `Private`
project. Indeed, this kind of information needs to be erased after
some time which is not compatible with version control. We
occasionally dedicated session specific based projects (e.g. in
`MyCourse/2021-2022`) to hold such information, like scans of exam
sheets. Then only instructors for that session can access them, and
they can be independently erased when times come.

## Advanced, experimental, or obsolete features

### Experimental web interface

A pure-client-side web interface
[travo-web](https://gitlab.info.uqam.ca/travo/travo-web) is available.

Student can use it to fork (and to correctly setup) their copies.
It also provide a (work in progress) simple overview of their copies with some feedback.


### Workspace-less interface

A feature of the legacy travo script shell was to allow the upload of a single submission file without needing the student to have a local copy of the repository.
The fork, setup and upload was done only with the gitlab API without creating any local directory.
While this approach is very limiting, is could be useful for some courses/students since there is no local directory with frightening files inside.

With this workflow, `travo` behaves just like a tool to send a file.
Under the hood, gitlab, git, commits are still used.
So the instructors get all the history, information, automatic grading, collecting, etc.

Note: the experimental web interfaces have a similar but experimental feature.

### Automatic feedback and grading

`travo info` can collect results of pipelines (CI/CD) for each student, thus enabling some form of automatic feedback or grading for students.
Currenty it collects:

* status of the last pipeline of each ref (branch, etc.).
* status of each job of these pipelines.
* summary of the reports of these job.
* fragile aggregation of TAP results (`ok`, `not ok`) extracted from the trace (log) of these jobs.

Instructors can thus setup a `.gitlab-ci.yml` to run tests that will be collected by Travo.

Custom script can also be developed to selectively choose how to collect and evaluate artefacts produced by CI/DI and present them to the students, instructors and graders.

Note: CI/CD relies on the state of the students copies. Therefore, the ci/cd files can be modified by the student.
Instructor should check (or automatise the check) that the files are not tempered.

TODO: maybe automatise those checks. It seems not easy to do it in a general and light way (see the Principles section).


There is also an undocumented `travo formgrader` command for courses based on Jupyter.
