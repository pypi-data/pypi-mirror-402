# Travo tutorial

In this tutorial, you will explore how Travo can help for a basic
GitLab based workflow for students (fetch, submit) and instructor(s)
(publish, review, collect) for a single assignment. Some familiarity
with Git and GitLab is assumed (creating Git repositories, GitLab
projects, GitLab groups, ...).

The [advanced tutorial](tutorial-advanced.md) will cover Travo's support
for **courses** which may have multiple assignments, instructors,
sessions, or student groups.

<!--

TODO:
- [ ] Explain the Python API -> Command-Line bridge that lets one call
      all the operations from the command line
- [ ] Generalize git to version control system below

!-->

(Basic_workflow)=
## Basic workflow and concepts

* The **instructor** **publishes** (or **releases**) an
  **assignment**, as a collection of files and directories, hosted in
  Git repository on a (GitLab) forge. Travo imposes no constraint on
  the repository, as long as students have read-access it, and an
  account on the forge (to be able to submit).

  The owner of the repository is assumed to be the instructor. In case
  the repository is stored in a GitLab group, any member of the group
  is considered as instructor.

* To work on the assignment, a **student** makes a **work copy** of
  the repository (a **clone** in Git parlance) in his work environment
  (computer lab, personal laptop, computing infrastructure). Travo
  automates the process with a single **fetch** command. The same
  command can be used later to update this copy.

* When done, the student **submits** their work on the forge for
  review by the instructors and/or peers and/or automated testing
  (CI).  The **submission** takes the form of a repository which is a
  **fork** (in **Git** parlance) of the assignment repository,
  appropriately configured (read-write access for all instructors,
  ...).  Travo automates the process with a single **submit** command.
  The same command can be used later to update the submission.

* If configured, **Continuous Integration** (CI) can run arbitrary
  commands on the submission: executing the student's code in a safe
  environment, running tests, computing automatic grades, preparing
  reports. This provides immediate **feedback** to the student and
  paves the way for manual review by the instructors.

* The instructors can then review the submissions directly on the
  forge, **collect** them, with the full power of version control and
  forges (history, issues) to scrutinize the progress and interact
  with the submission and the student.


The following picture (in French) illustrates the data flow for one of
the courses at Paris-Saclay; there, students work alternatively in two
environment: in the computer lab or remotely using a Jupyter service:

[![](https://gitlab.dsi.universite-paris-saclay.fr/MethNum/scripts/-/blob/master/figures/methnum_structure.png)](https://gitlab.dsi.universite-paris-saclay.fr/MethNum/scripts/-/blob/master/figures/methnum_structure.pdf)

## Using Travo from the command line: the basic student workflow

Travo provides a command line interface (CLI) with the `travo`
script. Let's see its usage for students. Here we assume that the
assignment is hosted in some repository
`https://gitlab.example.com/cs101/assignment1`, where `gitlab.example.com`
is a GitLab forge the student has an account on.

The student **fetches** the assignment with:

    travo fetch https://gitlab.example.com/cs101/assignment1

When done, they **submit** their work on the forge, for review by the
instructors and/or peers and/or automated testing (CI):

    travo submit <work copy>

The submission is stored on the forge as a fork of the original
repository, in the student's namespace:
`https://gitlab.example.com/<student login>/assignment1`.

<div class="alert alert-info>

Behind the scene, Travo automates the interaction with the forge
(creating a fork, ...) and with the version control system (`git
pull`, `git push`, `git merge`, ...).

</div>

### Tips and tricks

- The student typically needs to sign in once to GitLab to activate
  their account.
- `fetch` and `submit` can be used at any intermediate point to backup
  the work, transfer it to other work environments, get feedback (from
  instructors, peers, automated testing, ...), etc.
- The student should not already have a repository in their namespace
  with the same path as the assignment; for example, if several
  courses use the same path `assignment1`, there will be trouble! See
  the advanced tutorial for how to resolve this.

<!--
From within the work copy, the student can get information about the
current state of the submission (in particular feedback from automated
testing) with:

    travo info
!-->

### Exercise

In the exercises, we assume that you have an account on some GitLab
forge (e.g. GitLab.com). We will refer to it as *the forge*.

1. Choose as assignment some repository on the forge.

   <div class="alert alert-warning">

   Caveats:
   - that repository should reside in a group, not in your namespace,
   - there should be no repository in your namespace with the same
     path.

   </div>

   You may for example use, if you have an account on the given
   forges:
   - https://gitlab.dsi.universite-paris-saclay.fr/Info111/2022-2023/Semaine1
   - ...

2. Try the above commands

3. Explore your submission on GitLab.

## Using Travo from the command line: the simple instructor workflow

* Create the assignment like a normal GitLab project, as you wish.
  Caveat: for now, this project should reside in a group.
* Provide the students with the url of the project and instructions
* To retrieve or update (clone/pull) the submissions of all the
  students (for manual inspection or whatever), use:

	    travo collect <url>

  If run from your copy of the assignment, you may omit the <url> part.

<!--
* Periodically, you can use the subcommand `travo info` from the
  directory of your local copy of the assignment to see the status of
  the students
!-->

* If you rely on the manual student workflow (see below), you can run
  `travo search_forks` to collect missing forks (and `--fixup` them)

### Exercise

1. Prepare an assignment.
2. Fetch and submit that assignment
3. Have colleagues or students fetch the assignment and submit them
4. Open GitLab's web interface for your assignment repository, and
   click on the number of forks to browse the submissions.
5. Use `collect` to collect all the submissions in your work environment.

## Manual student workflow

Students need not use Travo: they can do all the operations by hand
with Git and GitLab's user interface, should they wish to do so (or
not have Travo installed in their work environment). It's easy however
to forget some of the step, and then break the instructor's
workflow. So they should make sure to stick precisely to the following
instructions:

* Create a repository for their submission, as a fork of the
  assignment repository.
* Make the submission repository private: beware that by default, a
  fork of a public repository is public!
* Make sure to add all instructors (or best the instructor group) as
  members, with Maintainer role.

## Conflict resolution

It is not unusual for a student to have two or more work copies for a
given assignment -- for example because they work in several
environments. Then there is a risk of these copies diverging with
changes on both sides. Travo -- in fact Git -- will try hard to
automatically merge the changes upon fetching, but these may
**conflict**. Conflict resolution is an inherently difficult task for
beginners. A simple and reliable practice to prevent conflicts is to
systematically fetch at the beginning of any work session and
systematically submit after.

Every now and then, a student will not follow that practice and run
into a conflict. Then `fetch` will abort with a message and leave the
work copy unchanged. The student may `fetch` again with the `--force`
option; this will rename the work copy with a timestamp, and fetch a
fresh work copy from the forge. Then the student may resolve the
conflict by hand by copying over files or chunks thereof into the
fresh work copy, and submit again from there. This is low-tech, but
requires no Git knowledge. For details, see
[there](https://nicolas.thiery.name/Enseignement/Info111/devoirs.html#en-cas-de-divergence-ou-conflit) (in French)

## Collaborative work with Travo

In the case of collaborative work, conflict resolution is an intrinsic
part of the process. At some point students will have to learn to
resolve them. Exploring best practices to ease collaborations for
beginners is a work in progress. Feedback welcome!

## Conclusion

In this tutorial, you have seen how to use the `travo` command line
interface to facilitate the workflow between instructors and students
around a single assignment: publish, fetch, submit, collect.

In the [advanced tutorial](tutorial-advanced.md) you will learn how to
handle courses with, e.g. several assignments, several groups of
students, or several sessions.
