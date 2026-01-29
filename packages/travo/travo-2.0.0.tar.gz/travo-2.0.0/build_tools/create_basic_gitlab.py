import os
import gitlab
from gitlab.v4.objects import User, Group, Project
import requests
from urllib.parse import urljoin

from typing import Any, Dict, List, cast

from travo.gitlab import GitLabTest


def get_user(username: str) -> User:
    users = cast(List[User], gl.users.list(username=username))
    return users[0]


def create_user(user_data: Dict[str, Any]) -> User:
    try:
        user = gl.users.create(user_data)
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"user {user_data['username']} already defined: {e.error_message}")
        user = get_user(user_data["username"])
    return cast(User, user)


def create_group_or_subgroup(group_data: Dict[str, Any]) -> Group:
    try:
        group = gl.groups.create(group_data)
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"group {group_data['name']} already defined: {e.error_message}")
        group = [gr for gr in gl.groups.list() if gr.name == group_data["name"]][0]
    return cast(Group, group)


def create_user_project(user: User, project_data: Dict[str, Any]) -> Project:
    try:
        user.projects.create(project_data)
    except gitlab.exceptions.GitlabCreateError as e:
        print(f"project {project_data['name']} already defined: {e.error_message}")

    project = [
        pr for pr in gl.projects.list(get_all=True) if pr.name == project_data["name"]
    ][0]
    return cast(Project, project)


if "GITLAB_HOST" in os.environ and "GITLAB_80_TCP_PORT" in os.environ:
    gitlab_url = (
        f"http://{os.environ['GITLAB_HOST']}:{os.environ['GITLAB_80_TCP_PORT']}"
    )
else:
    gitlab_url = "http://gitlab"

# Password authentification is no longer supported by python-gitlab
# https://python-gitlab.readthedocs.io/en/stable/api-usage.html#note-on-password-authentication # noqa: E501
data = {"grant_type": "password", "username": "root", "password": "dr0w554p!&ew=]gdS"}
resp = requests.post(urljoin(gitlab_url, "oauth/token"), data=data)
resp_data = resp.json()
gitlab_oauth_token = resp_data["access_token"]

# login
gl = gitlab.Gitlab(gitlab_url, oauth_token=gitlab_oauth_token, keep_base_url=True)

# create users
users_data = GitLabTest.users

users = {
    user_data["username"]: create_user(user_data)
    for user_data in users_data
    if user_data["username"] != "root"
}
user = users["student1"]


# create user projects and groups
project_data = {"name": "nom-valide", "visibility": "private"}

create_user_project(user, project_data)

project_data = {
    "name": "Fork-de-student1-du-projet-Exemple-projet-CICD",
    "visibility": "private",
}

create_user_project(user, project_data)

group_data = {"name": "group1", "path": "group1"}

group = create_group_or_subgroup(group_data)

try:
    group.members.create(
        {"user_id": user.id, "access_level": gitlab.const.AccessLevel.DEVELOPER}
    )
except gitlab.exceptions.GitlabCreateError as e:
    print(f"member already exists: {e.error_message}")

subgroup_data = {"name": "subgroup", "path": "subgroup", "parent_id": group.id}

subgroup = create_group_or_subgroup(subgroup_data)

grouppublic_data = {
    "name": "Groupe public test",
    "path": "groupe-public-test",
    "visibility": "public",
}

grouppublic = create_group_or_subgroup(grouppublic_data)

admin_user = get_user("root")
project_data = {
    "name": "Projet public",
    "visibility": "public",
    "namespace_id": grouppublic.id,
}

project = create_user_project(admin_user, project_data)

# create commits
# See https://docs.gitlab.com/ce/api/commits.html#create-a-commit-with-multiple-files-and-actions # noqa: E501
# for actions detail
commits_data = {
    "branch": "master",
    "commit_message": "blah blah blah",
    "author_name": user.name,
    "author_email": user.email,
    "actions": [
        {
            "action": "create",
            "file_path": "README.md",
            "content": "This is a README.",
        },
    ],
}

try:
    project.commits.create(commits_data)
except gitlab.exceptions.GitlabCreateError as e:
    print(f"file already committed: {e.error_message}")


# general settings for project export and import
settings = gl.settings.get()
settings.max_import_size = 50
settings.deletion_adjourned_period = 1
settings.import_sources = ["git", "gitlab_project"]
settings.save()
