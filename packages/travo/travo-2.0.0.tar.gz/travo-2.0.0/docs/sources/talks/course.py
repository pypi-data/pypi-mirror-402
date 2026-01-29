#!/usr/bin/env python3

import os.path
import subprocess
import sys

##############################################################################
# Vérifie que l'environnement intro-science-donnees est actif. Si non:
# - En salle de TP du PGIP: active l'environnement dans /public
# - Autrement: produit une erreur

# conda_root_pgip = "/opt/mambaforge/"
conda_root_pgip = "/public/info-111/mambaforge/"

if __name__ == "__main__":
    try:
        import intro_science_donnees   # type: ignore
        ok = True
    except ImportError:
        ok = False

    if not ok:
        if os.path.isdir(conda_root_pgip + "/envs/intro-science-donnees/"): # En salle TP du PGIP/SIF
            command = [conda_root_pgip + "bin/conda", "run", "--no-capture-output", "-n", "intro-science-donnees",
                       "python", *sys.argv]
            subprocess.run(command)
            exit(0)
        else:
            sys.tracebacklimit = 0
            raise RuntimeError("Environnement intro-science-donnees non actif\n"
                               "Veuillez l'installer, puis l'activer avec: \n"
                               "   conda activate intro-science-donnees")

##############################################################################
# Configuration du cours

import textwrap
from travo import GitLab
from travo.jupyter_course import JupyterCourse
from travo.script import main
from travo.utils import run

forge = GitLab("https://gitlab.dsi.universite-paris-saclay.fr/")
course = JupyterCourse(
    forge=forge,
    path="L1InfoInitiationScienceDonnees",
    name="Introduction à la Science des Données",
    url="https://Nicolas.thiery.name/Enseignement/IntroScienceDonnees/",
    student_dir="./",
    session_path="2022-2023",
    expires_at="2024-07-31",
    jobs_enabled_for_students=True,
#    assignments=[f"Semaine{i}" for i in range(1, 10)],
    student_groups=[
        "MI1",
        "MI2",
        "MI3",
        "MI4",
        "LDDIM1",
        "LDDIM2",
        "AuditeursLibres",
    ],
)

assert course.student_groups is not None
course.script = "./course.py"

usage = f"""Aide pour l'utilisation de la commande {course.script}
===============================================

Télécharger ou mettre à jour un TP ou projet (remplacer «Semaine1» par
le nom du TP):

    cd ~/IntroScienceDonnees
    {course.script} fetch Semaine1

Déposer un TP ou projet (remplacer «Semaine1» par le nom du TP ou
projet et remplacer «Groupe» par le nom de votre groupe) :

    cd ~/IntroScienceDonnees
    {course.script} submit Semaine1 Groupe

{textwrap.fill('Groupes: '+', '.join(course.student_groups))}

Lancer le carnet Jupyter (inutile sur le service JupyterHub) :

    cd ~/IntroScienceDonnees
    {course.script} jupyter lab

Valider un carnet Jupyter (remplacer «Semaine1» et «1_jupyter.md» par
le nom du devoir et du carnet respectivement) :

    cd ~/IntroScienceDonnees
    cd Semaine1
    ../course.py validate 1_jupyter.md 

Plus d'aide:

    {course.script} --help
"""

##############################################################################
# Execution du script

if __name__ == "__main__":
    main(course, usage)
