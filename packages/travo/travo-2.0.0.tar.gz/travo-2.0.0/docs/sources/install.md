# Installing Travo

Travo is available for installation from the [Python Package Index](https://pypi.org/).

If you don't have administrator access to your machine it is recommended to install
`travo` via `pip` or `conda` in an isolated environment
([venv](https://docs.python.org/3/library/venv.html),
[conda](https://conda.io/projects/conda/en/latest/user-guide/concepts/environments.html)
or [mamba](https://mamba.readthedocs.io/en/latest/user_guide/concepts.html) environments):
```
pip install travo
```
or
```
conda install travo
```

To benefit from the Jupyter integration (dashboards), please use
instead:
```
pip install 'travo[jupyter]'
```
or
```
conda install -c conda-forge travo-jupyter
```

To install the development version via pip
```
pip install git+https://gitlab.com/travo-cr/travo.git
```

## Troubleshooting

- Without creating an isolated environment you may need to use `pip3` instead of `pip`
  to force the use of Python 3.
- If using `pip` as provided by your operating system, you may need to
  add `~/.local/bin` to your path.
- Use `sudo` to install `travo` system wide (this is **not recommended**, but sometimes
  unavoidable when installing in a multi-user environment).
