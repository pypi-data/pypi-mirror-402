---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.12
    jupytext_version: 1.9.1
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

```{code-cell} ipython3
from travo.travo import GitLab
```

```{code-cell} ipython3
gitlab = GitLab("https://gitlab.dsi.universite-paris-saclay.fr")
```

```{code-cell} ipython3
project = gitlab.get_project('Info111/2022-2023/MI3/Semaine2')
```

```{code-cell} ipython3
project.get_forks_ssh_url_to_repo()
```

```{code-cell} ipython3
gitlab.login()
```

```{code-cell} ipython3
project = gitlab.get_project('Info111/2022-2023/MI3/Semaine6')
```

```{code-cell} ipython3
project
```

```{code-cell} ipython3
project.get_forks()
```

```{code-cell} ipython3
forks = _
```

```{code-cell} ipython3
len(forks)
```

```{code-cell} ipython3
project.id
```

```{code-cell} ipython3
res = gitlab.get("projects/2028/forks")
```

```{code-cell} ipython3
import pprint
pprint.pprint(res.headers)
```

```{code-cell} ipython3
res.headers['Link']
```

```{code-cell} ipython3
res.links
```

```{code-cell} ipython3
res.headers['X-Total']
```

```{code-cell} ipython3
project = gitlab.get_project("Info111/2022-2023/MI3/Semaine2")
```

```{code-cell} ipython3
l = project.get_forks()
```

```{code-cell} ipython3
sorted([p.path_with_namespace for p in l])
```

```{code-cell} ipython3
len(l)
```

```{code-cell} ipython3

```
