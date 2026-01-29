# Contributing to Travo

All contributions and feedback are welcome!

## Developer workflow

Start contributing forking the Travo repository on gitlab.com
https://gitlab.com/travo-cr/travo, then clone your fork locally
```bash
git clone https://gitlab.com/<your_username>/travo
```
or, using ssh protocol
```bash
git clone git@gitlab.com:<your_username>/travo.git
```

### Isolate your developer environment

Development best practices recommend to isolate your development environment
when developing with python in order to control dependencies (even without admin
rights on the system) and to not break previous installations.
This is possible using python [virtual environments](https://docs.python.org/3/library/venv.html)
or [conda environments](https://conda.io/projects/conda/en/latest/index.html).

We will briefly cover conda environment configuration here as an example.

After [installing conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html),
[create an environment](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#creating-an-environment-with-commands)
dedicated to travo with a specific `pip` installation
```bash
conda create -n travodevenv pip
```
Activate your environment and start contributing
```bash
conda activate travodevenv
```

Alternatively the [Mambaforge installer](https://github.com/conda-forge/miniforge#mambaforge)
can also be used.
It will install `conda` and `mamba` (a package resolver faster than `conda`)

All previous commands can then be run replacing `conda` with `mamba`.

#### Check your contributions

`travo` formats and lints its code with [ruff](https://docs.astral.sh/ruff/).
If you plan to offer a merge request your code should comply with ruff rules.
We strongly suggest to use [pre-commit](https://pre-commit.com/) to manage ruff compliancy.

First of all `ruff` and `pre-commit` should be installed in your environment:
```bash
pip install ruff==0.8.2 pre-commit
```
Then the [pre-commit hook should be installed](https://pre-commit.com/#3-install-the-git-hook-scripts):
```
pre-commit install
```
Now all the necessary format checks will run automatically on `git commit`.

### Build your project

Inside the cloned repository you can build the project in
[editable mode](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs)
```bash
cd travo
pip install -e .
```

### Run the tests

To install all the dependencies needed for running the tests
```bash
pip install -e ".[test]"
```

`Travo` is a library meant to interact with a forge: the majority of the tests
needs to run against an existing forge.
In order to avoid spurious failures, an ephemeral forge is built during the
testing process in a [Docker](https://www.docker.com/) container [^podman].
The Docker daemon should be [installed and running](https://docs.docker.com/engine/)
on the local machine to have Travo tested.

The whole test suite can then be run using [tox](https://tox.wiki/en/4.11.3/),
with the following commands
```bash
pip install tox
tox
```

If you want to run a specific test, say `travo/test/test_assignement.py`,
you can run
```bash
tox -- travo/test/test_assignement.py
```

[^podman]: Note that it should be possible to use [podman](https://podman.io/)
    but the solution has not be tested yet.

#### Advanced testing

The test infrastructure makes use of the tox plugin
[tox-docker](https://tox-docker.readthedocs.io/en/latest/), which removes the
docker container at the end of the test suite.

When developing and testing a specific feature, one may want to reuse the
container rather than rebuilding it at every test run.

This is possible with
```bash
tox --docker-dont-stop=gitlab
```

keeping the docker container at the end of the tox session.

We provide a tool suggesting the commands needed to configure the environment
depending on the container properties:
```bash
python build_tools/run_local_tests.py
```
Once the environment configured as suggested
```bash
pytest travo
```

## Contributing to the documentation

The Travo webpage and documentation are built using [sphinx](https://www.sphinx-doc.org/en/master/)
and the [pydata sphinx theme](https://pydata-sphinx-theme.readthedocs.io/en/stable/).

The sources of the documentation are in the `docs/sources/` repository and they are written in
[MyST markdown](https://mystmd.org/).

To build the documentation the needed dependencies can be installed using
```bash
pip install -e ".[doc]"
```
Then move into the documentation directory
```bash
cd docs
```
the html version can be generated with
```bash
make html
```

The rendered documentation can be browsed in `build/html`.
