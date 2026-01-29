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

# Travo: Gestion des devoirs étudiants avec GitLab

</div>

[![DOI](https://www.zenodo.org/badge/DOI/10.5281/zenodo.8153991.svg)](https://doi.org/10.5281/zenodo.8153991)

<!--<img src="https://jupyter.org/assets/homepage/main-logo.svg" style="position: absolute; right: 0; width: 20%; border:0px"> -->

<div class="bigskip"/>

[Nicolas M. Thiéry](https://Nicolas.Thiery.name/)

<div class="bigskip"/>

Professeur en Informatique
Laboratoire Interdisciplinaire des Sciences du Numérique  
Université Paris-Saclay

<div class="medskip"/>

<div style="text-align: center;">

Journée autour de GitLab, 29 Juin 2023, CNRS, Paris

</div>

+++ {"slideshow": {"slide_type": "slide"}}

## Le problème

+++ {"slideshow": {"slide_type": "fragment"}}

### Comment gérer les devoirs informatiques dans votre cours?

Typiquement: devoirs «à trous» pour du calcul ou de la programmation

- préparer
- publier
- distribuer
- collecter
- corriger manuellement ou automatiquement
- distribuer les retours

+++ {"slideshow": {"slide_type": "fragment"}}

**Aujourd'hui:** une pièce du puzzle: Travo

+++ {"slideshow": {"slide_type": "slide"}}

## Une idée

***Enseigner les sciences computationnelles est une forme de
collaboration sur du code***

+++ {"slideshow": {"slide_type": "fragment"}}

### Utilise la Forge, Luc!

Par exemple «GitHub ClassRoom».

Modèle:
- l'enseignant prépare et publie un devoir comme un dépôt git
- l'étudiant télécharge le devoir (clone)
- l'étudiant dépose sont travail comme divergence (fork) de ce dépôt git

+++ {"slideshow": {"slide_type": "subslide"}}

### Caveat 1: protection des données personnelles

+++ {"slideshow": {"slide_type": "fragment"}}

### Caveat 2: intégration avec le système d'information de l'institution

+++ {"slideshow": {"slide_type": "fragment"}}

### Solution: utiliser une forge déployée sur site

Par exemple: GitLab

+++ {"slideshow": {"slide_type": "slide"}}

### Caveat 3: la gestion de version et les forges, c'est trop compliqué pour les étudiants!

+++ {"slideshow": {"slide_type": "fragment"}}

### Solution: automatiser l'interaction avec Git et GitLab!

**Travo** à la rescousse!

+++ {"slideshow": {"slide_type": "fragment"}}

### L'interface basique pour les étudiants

Télécharger le devoir :
``` sh
    travo fetch https://gitlab.com/travo-cr/demo-assignment.git
```

Déposer le devoir :
``` sh
    travo submit demo-assignment
```

+++ {"slideshow": {"slide_type": "subslide"}}

### L'interface graphique pour les étudiants

``` python
from course import course
course.student_dashboard()
```

+++

<center><img src="student_dashboard.png" width=60%></center>

+++ {"slideshow": {"slide_type": "slide"}}

## Quel rapport entre Travo, Jupyter, nbgrader?

+++ {"slideshow": {"slide_type": "fragment"}}

- Travo apporte des fonctionnalités supplémentaires pour les devoirs
  basés sur Jupyter (tableau de bords, correction assistée).

+++ {"slideshow": {"slide_type": "fragment"}}

- Travo peut être utilisé comme service d'échange alternatif pour nbgrader.

+++ {"slideshow": {"slide_type": "slide"}}

## Pourquoi utiliser une forge pour l'enseignement?

### Propriétés

- Un espace de stockage collaboratif partagé
- Avec authentification et gestion des droits
- Avec traçabilité forte (gestion de version: git)
- Conçu pour héberger du code
- Conçu pour la collaboration
- Conçu pour gérer des processus
- Très grande souplesse d'utilisation:
    - Interface web riche
    - Automatisation via API

+++ {"slideshow": {"slide_type": "fragment"}}

### Cas d'usage

- Gestion des devoirs
- Édition collaborative du matériel pédagogique
- Édition, production et hébergement site web du cours
- Discussions pédagogiques par tickets
- Interactions étudiants par tickets?

+++ {"slideshow": {"slide_type": "slide"}}

## Travo: Gestion des devoirs étudiants avec GitLab

+++ {"slideshow": {"slide_type": "fragment"}}

https://gitlab.com/travo-cr/travo/

Développé par des enseignants de l'Université du Québec À Montréal et
l'Université Paris-Saclay; et vous?

+++ {"slideshow": {"slide_type": "fragment"}}

### Testé sur le terrain

- Trivial à utiliser pour les étudiants
- Testé sur des cours à toute échelle (10-250 étudiants) à tous les niveaux

+++ {"slideshow": {"slide_type": "fragment"}}

### Fonctionnalités riches

- équipes pédagogiques, groupes étudiants, sessions, travail de
  groupe, gestion des droits, ...
- soutien l'autocorrection par intégration continue, la détection de plagiat
- intégration avec Jupyter et nbgrader
- **toute la puissance de la gestion de version et des forges!!!**

+++ {"slideshow": {"slide_type": "subslide"}}

### Léger, flexible, modulaire, extensible, soutenable, distribué, respectueux des données personnelles

- Juste une petite bibliothèque Python
- API shell, API Python, interface Jupyter
- S'adapte à vos processus
- S'adapte à votre infrastructure
  - toute instance GitLab à laquelle les étudiants ont accès
  - salle de TP, ordinateur personnel, service en ligne, ...

+++ {"slideshow": {"slide_type": "fragment"}}

### Expose progressivement les étudiants à la gestion de version, aux forges
