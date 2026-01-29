---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.8.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Travo demo: interacting with gitlab

```{code-cell} ipython3
from travo import GitLab
```

```{code-cell} ipython3
gitlab = GitLab("https://gitlab.com")
```

+++

## Accessing a project

For some resources commonly accessed through the API (groups,
projects), travo provides python dataclasses to streamline
read/write access to attributes and add additional methods:

```{code-cell} ipython3
project = gitlab.get_project("travo-cr/travo")
```

```{code-cell} ipython3
project.name_with_namespace
```

```{code-cell} ipython3
project.http_url_to_repo
```

```{code-cell} ipython3
project.forked_from_project
```

```{code-cell} ipython3
group = gitlab.get_group("travo-cr")
```

```{code-cell} ipython3
group.projects
```
