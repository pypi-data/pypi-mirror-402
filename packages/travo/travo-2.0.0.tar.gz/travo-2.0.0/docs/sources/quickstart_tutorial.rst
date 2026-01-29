##################################
Quickstart a simple Jupyter Course
##################################

This tutorial will guide you through the process of setting up a simple Jupyter-based course using Travo to distribute and collect course material.
If you are new to Travo, we suggest you read the "Basic workflow and concepts" section of the Travo Tutorial before you start (see :ref:`Basic_workflow`).

In particular, during this tutorial, you will set up a simple course and then use Travo (via the Instructor Dashboard Jupyter Notebook) to publish the material related to 2 assignments to your students.
Then you will use the Student Dashboard to see how students interact with your course: you will retrieve the course material, work on the assignments and submit them.
Finally, back to being a course instructor, again via the Instructor Dashboard Jupyter Notebook, you will collect the submitted assignments.

The tutorial uses a bare-bones course template (Simple Jupyter Course) created specifically to allow exploring Travo functionalities.

Some steps of the tutorial have been fully automated ("Auto" tab), but you can execute them manually ("Manual" tab) to discover how Travo works under the hood or for finer grain control.

.. admonition:: Prerequisite

   To follow this tutorial, you will need to have an account on some GitLab instance (referred to later on as "the forge"), with permissions to create groups and projects.


.. admonition:: Tutorial replay
   :class: dropdown

   If you want to replay this tutorial again, you **must** first discard the course on the forge and recreate it from scratch.

   .. caution:: The following actions are irreversible!!!

   If you have tested the course by submitting assignments as a student, you need to remove them first:

    .. code-block:: bash

       cd <MyCourse>/Instructors
       ./ComputerLab/course.py remove_submission Assignment1

    Then remove the course's group on GitLab:

    .. code-block:: bash

       cd <MyCourse>/Instructors
       ./ComputerLab/course.py forge remove_group <SimpleJupyterCourse>

    replacing `<SimpleJupyterCourse>` with the value of `course.path`.


**************************
1. Set-up as an instructor
**************************

Install Travo
=============

.. tabs::

   .. group-tab:: pip

      .. code-block:: bash

         pip install travo[jupyter]

   .. group-tab:: conda/mamba

      .. code-block:: bash

         conda install -c conda-forge travo-jupyter

Download the course template on your machine
============================================

The course template will be downloaded in a new subdirectory `MyCourse`. You may use any other name, and it does not need to match with any name on the forge. Below we will refer to this subdirectory as `<MyCourse>`.

.. tabs::

   .. group-tab:: Auto

      Simply use this shell command :

      .. code-block:: bash

         travo quickstart <MyCourse>

   .. group-tab:: Manual

      1. Clone `Instructors` as `<MyCourse>/Instructors`

      .. code-block:: bash

         git clone https://gitlab.com/travo-cr/demos/simple-jupyter-course/Instructors <MyCourse>/Instructors

      2. Clone `ComputerLab` as `<MyCourse>/ComputerLab`

      .. code-block:: bash

         git clone https://gitlab.com/travo-cr/demos/simple-jupyter-course/ComputerLab <MyCourse>/Instructors/ComputerLab


Configure your course
=====================

Edit `<MyCourse>/Instructors/ComputerLab/course.py`. In order for the tutorial to work, you **must** change the course `path` and `name` to something unique:

.. code-block:: python

   [...]
   path="SimpleJupyterCourse",
   [...]
   name="SimpleJupyterCourse",

You also **must** set the forge used by Travo to one where you have an account:

.. code-block:: python

   [...]
   # The URL of the forge that will host the course
   forge=GitLab("https://gitlab.com"),

If you are using `https://gitlab.com`, please see the warning at the beginning of the next section.

If your course uses continuous integration (e.g. for automated grading), set:

.. code-block:: python

   [...]
   jobs_enabled_for_students=True,


Create the course structure on the forge
===========================================

After these local steps, the remote forge must be configured and then the course material to share is sent online.

.. tabs::

   .. group-tab:: Auto

      .. Warning:: On some instance (like `gitlab.com`), the base group of the course can't be created automatically. In that case, that group needs to be created manually first (follow step 1 of this "Manual" tab).

      Upload the course on the forge using:

      .. code-block:: bash

         cd <MyCourse>
         ./Instructors/ComputerLab/course.py deploy

   .. group-tab:: Manual

      .. warning:: The GitLab UI tends to suggest paths that are lowercase. It is nevertheless case sensitive. Double check that the paths given in GitLab match exactly these given in `course.py`. Also mind that there are some restrictions on characters that can appear in paths and names.

      1. Create a **public** group with path as given in `course.path` and name in `course.name`.
      2. Create a public subgroup with path `course.session_path` and name `course.session_name` (typically `2024-2025` for both).
      3. Create in the course group a **blank** public project (make sure to uncheck the initialisation of the README) with path and name `ComputerLab`.

      4. If changes have been made to `course.py` you need to share it (with students). Configure your `ComputerLab` repo with remote server, commit your modification and push to the server:

       .. code-block:: bash

         cd <MyCourse>/Instructors/ComputerLab
         git remote set-url origin <...>/ComputerLab.git
         git add course.py
         git commit -m "Modification of course.py"
         git push

      5. Optionally create in the course group an empty (without README) (private or public) project `Instructors`; this is typically useful if you want to use such a project for collaborating with other instructors on the course material. And set remote for this repo:

      .. code-block:: bash

         cd <MyCourse>/Instructors
         git remote set-url origin <...>/Instructors.git
         git push


Create your first assignment
============================

In the template course, we provide two fake Assignments, 1 & 2, as Jupyter notebooks. If you are using the `nb_grader` extension, you may want to remove solutions from the notebooks before sharing them to students. This is the purpose of this `generate` step.

Even if you are not using `nb_grader`, the `generate` step is still required, and will simply copy the material from the assignment's `source` folder to the `release` folder.

.. tabs::

   .. group-tab:: From Jupyter

      Open `<MyCourse>/Instructors/instructor_dashboard.ipynb` and click on the `generate` button.

   .. group-tab:: From the shell

      1. Create a directory for the student version of the assignment:

      .. code-block:: bash

         cd <MyCourse>/Instructors
         mkdir -p source/Assignment1
         cd source/Assignment1

      2. Populate the directory with the material for the assignment.
         Recommendation: include a file named `index.md` or `index.ipynb` or `README.md` or `README.ipynb`.

      .. Warning:: It is not recommanded to initialize Git repo inside `source` folders. If so, you need to configure `nbgrader_config.py` in `Instructors` to exclude `.git` folder. Instead use Git repo in `Instructors` to version your `source` folders.

      3. Generate the student version:

      .. code-block:: bash

          cd <MyCourse>/Instructors
          ./ComputerLab/course.py generate_assignment Assignment1


Release (publish) the assignment on the forge
=============================================

Now it's time to share your material with students!

.. tabs::

   .. group-tab:: From Jupyter

      Open `<MyCourse>/instructor_dashboard.ipynb`, select a `Release mode` (either `Public` or `Private`, top left of the dashboard) and then click on the `Release lesson` button. Note that the `Release lesson` button is disabled until you select a `Release mode`.

   .. group-tab:: From the shell

      .. code-block:: bash

         cd <MyCourse>/Instructors/release/Assignment1
         ../../ComputerLab/course.py release Assignment1


*************************
2. Discover as a student
*************************

Test the assignment as a student
================================

Now discover the interaction with Travo as a student!

We denote by `<MyCourseStudent>` the directory where the students will be working. It can be anything.
You can also use your existing `ComputerLab` folder located at `<MyCourse>/ComputerLab`; if you do, you can skip to the next section.

First, download the computer lab:

.. code-block:: bash

   git clone <url of ComputerLab> <MyCourseStudent>
   cd <MyCourseStudent>

You are now ready to fetch your first assignment.

Fetch your first assignment
===========================

As a student, download the material of a specific Assignment.

.. tabs::

   .. group-tab:: From Jupyter

      Open `<MyCourseStudent>/ComputerLab/dashboard.ipynb` then use the button `fetch`: the assignment appears in your local folder.

   .. group-tab:: From the shell

      .. code-block:: bash

         cd <MyCourseStudent>
        ./course.py fetch Assignment1

Submit an assignment
====================

Edit the assignment files at will in `Assignment1`. Your modification will be submitted to the teacher in the upcoming submission step.

.. tabs::

   .. group-tab:: From Jupyter

      Open `<MyCourseStudent>/ComputerLab/dashboard.ipynb` then use the button `submit`.

   .. group-tab:: From the shell

      .. code-block:: bash

         cd <MyCourseStudent>
        ./course.py submit Assignment1


***************************
3. Collect as an instructor
***************************

As an instructor you want to gather the submissions of your students to correct their contributions.

Back to teacher: collect the submissions
========================================

This collect step is managed by Travo:

.. tabs::

   .. group-tab:: From Jupyter

      Open `<MyCourse>/instructor_dashboard.ipynb` and click on the `collect` button. The submissions appear in the `submitted` folder.

   .. group-tab:: From the shell

      .. code-block:: bash

         cd <MyCourse>/Instructors
        ./ComputerLab/course.py collect Assignment1

Next, the grading action depends on your workflow. If you want to grade Jupyter notebooks, you could use `nb_grader` (out of scope of this tutorial).

.. admonition:: The end!

   That's it! You succeeded to create your first course with Travo! Congratulations!
