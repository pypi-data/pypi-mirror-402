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
from travo.travo import GitLab
```

```{code-cell} ipython3
gitlab = GitLab("https://gitlab.dsi.universite-paris-saclay.fr")
```

## Authentication

```{code-cell} ipython3
gitlab.login()
```

Note: login again is idempotent:

```{code-cell} ipython3
gitlab.login()
```

Note: the token is cached in `~/.travo/tokens/gitlab.dsi.universite-paris-saclay.fr` so
we need not authenticate again, even in a separate session.

+++

We may now access personal info:

```{code-cell} ipython3
gitlab.get_status()
```

And make requests to the API. Here we fetch information
on the current user, which we recover in json format:

```{code-cell} ipython3
gitlab.get("/user").json()
```

## Accessing a project

For some resources commonly accessed through the API (groups,
projects), travo provides python dataclasses to streamline
read/write access to attributes and add additional methods:

```{code-cell} ipython3
project = gitlab.get_project("Info111/2022-2023/MI3/Semaine4")
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
group = gitlab.get_group("Info111")
```

```{code-cell} ipython3
group.projects
```

## Testing zone

```{code-cell} ipython3
from travo.travo import GitLab, Project
gitlab = GitLab("https://gitlab.dsi.universite-paris-saclay.fr/")
gitlab.login()
project = gitlab.get_project("Info111/2022-2023/MI3/Semaine4")
```

```{code-cell} ipython3
project.forked_from_project
```
