---
jupytext:
  notebook_metadata_filter: rise
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
rise:
  auto_select: first
  autolaunch: false
  centered: false
  controls: false
  enable_chalkboard: true
  height: 100%
  margin: 0
  maxScale: 1
  minScale: 1
  scroll: true
  slideNumber: true
  start_slideshow_at: selected
  transition: none
  width: 90%
---

+++ {"slideshow": {"slide_type": "slide"}}

<div class="alert alert-info"> 

# Travo: distributed GitLab ClassRoom

</div>

<img src="https://jupyter.org/assets/homepage/main-logo.svg" style="position: absolute; right: 0; width: 20%; border:0px">

<div class="bigskip"/>

[Nicolas M. Thiéry](https://Nicolas.Thiery.name/)

<div class="bigskip"/>

Professor in Computer Science  
Laboratoire Interdisciplinaire des Sciences du Numérique  
Université Paris-Saclay

<div class="medskip"/>

<div style="text-align: center;">

JupyterCon, May 10th of of 2023

</div>

+++ {"slideshow": {"slide_type": "slide"}}

## The problem

+++ {"slideshow": {"slide_type": "fragment"}}

### How to manage computational assignments in your course?

- prepare
- publish
- distribute
- collect
- grade manually or automatically
- release feedback

+++ {"slideshow": {"slide_type": "fragment"}}

**Today:** a piece in the puzzle: Travo

+++ {"slideshow": {"slide_type": "slide"}}

## An idea

***Teaching computationnal sciences is a form of collaboration on code***

+++ {"slideshow": {"slide_type": "fragment"}}

### Use the Forge!

E.g. GitHub ClassRoom

+++ {"slideshow": {"slide_type": "fragment"}}

### Caveat 1: personal data protection

+++ {"slideshow": {"slide_type": "fragment"}}

### Caveat 2: integration with the school information system

+++ {"slideshow": {"slide_type": "fragment"}}

### Use a forge hosted on premisses

E.g. GitLab

+++ {"slideshow": {"slide_type": "slide"}}

### Caveat 3: Version control and forges are too complicated for students

+++ {"slideshow": {"slide_type": "fragment"}}

### Automate the interaction with Git and GitLab!

**Travo** to the rescue!

+++ {"slideshow": {"slide_type": "slide"}}

### The student interface

```{code-cell} ipython3
from course import course
course.student_dashboard()
```

+++ {"slideshow": {"slide_type": "slide"}}

## How does Travo relate to nbgrader?

+++ {"slideshow": {"slide_type": "fragment"}}

- Travo can be used as alternative exchange service for nbgrader

+++ {"slideshow": {"slide_type": "fragment"}}

- Travo can be used with non Jupyter assignments

+++ {"slideshow": {"slide_type": "slide"}}

## Travo: Distributed GitLab ClassRoom

+++ {"slideshow": {"slide_type": "fragment"}}

https://gitlab.com/travo-cr/travo/

By a handful of devs at Université du Québec À Montréal and Université Paris-Saclay; and you?

+++ {"slideshow": {"slide_type": "fragment"}}

### Ready for the battlefield
- Trivial to use for students
- Tested on small to large courses (200+ students) at all levels
- Use existing infrastructure as is:
  - any GitLab instance that students can access
  - any JupyterHub, local installation, even binder; soon JupyterLite!

+++ {"slideshow": {"slide_type": "fragment"}}

### Feature rich
- multiple instructors, multiple student groups, multiple sessions, group work, autograding by CI
- integration with Jupyter and nbgrader
- **all the power of version control and forges!!!**

+++ {"slideshow": {"slide_type": "fragment"}}

### Lightweight, flexible, modular, extensible, sustainable, distributed, personal-data friendly
- Just a small Python library
- Shell API, Python API, Jupyter UI
- Adapts to your workflow

+++ {"slideshow": {"slide_type": "fragment"}}

### Progressively exposes students to version control and forges
