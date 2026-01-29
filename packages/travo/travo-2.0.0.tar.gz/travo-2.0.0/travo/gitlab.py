import base64
import contextlib
from dataclasses import dataclass, field, InitVar, fields
import enum
import fnmatch
import getpass
import io
import logging
import os
import requests
import subprocess
import tempfile
import time
import urllib
import re
import pathlib

import typing
import typing_utils  # type: ignore
from typing import (
    Iterator,
    Optional,
    List,
    Sequence,
    Tuple,
    Dict,
    Union,
    Any,
    Type,
    TypeVar,
    ClassVar,
    cast,
)
import zipfile

from .i18n import _
from .utils import urlencode, run, getLogger

R = TypeVar("R", "Group", "Project", "Namespace", "User")
# JSON = TypeAlias(Any)  # Python 3.10
# Job = TypeAlias(JSON)  # Python 3.10
JSON = Any  # Could be made more specific
Job = JSON  # Could be made more specific
JWT: str = "JWT"  # Json Web Token type
PERSONAL_ACCESS: str = "PERSONAL_ACCESS"  # Personal Access Token type


class ResourceNotFoundError(RuntimeError):
    pass


class AuthenticationError(RuntimeError):
    pass


def request_credentials_basic(
    forge: "GitLab", username: Optional[str] = None, password: Optional[str] = None
) -> Tuple[str, str]:
    """
    Basic interactive UI for requesting credentials to the user
    """
    print(_("please authenticate on", url=forge.base_url))
    if username is None:
        username = input(_("username") + ": ")
    if username == "anonymous":
        password = ""
    if password is None:
        password = getpass.getpass(_("password") + ": ")
    return username, password


class GitLab:
    debug: bool = False
    home_dir: str = str(pathlib.Path.home())
    token: Optional[str] = None
    token_type: Optional[str] = None
    token_expires_at: Optional[float] = None
    _current_user: Optional[Union["User", "AnonymousUser"]] = None
    base_url: str
    api: str
    session: requests.Session
    log: logging.Logger
    # on_missing_credentials should be a callable that either
    # returns the credentials as a tuple (username, password)
    # (typically after requesting them interactively to the user),
    # or raise (typically after setting up a UI to request the
    # credentials)
    on_missing_credentials: Any  # Should be Callable

    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        token_type: Optional[str] = JWT,
        log: logging.Logger = getLogger(),
        home_dir: Optional[str] = None,
    ):
        if base_url[-1] != "/":
            base_url = base_url + "/"
        self.base_url = base_url
        self.api = base_url + "api/v4/"
        self.session = requests.Session()
        self.token = None
        self.token_type = token_type
        self.log = log
        self.on_missing_credentials = request_credentials_basic
        if home_dir is not None:
            self.home_dir = home_dir
        assert self.home_dir

    def __repr__(self) -> str:
        return "GitLab: {}".format(self.base_url)

    def token_file(self) -> str:
        """
        Return the name of the file where the token is stored for this server
        """
        home_dir = self.home_dir
        hostname = typing.cast(str, urllib.parse.urlparse(self.base_url).hostname)
        return os.path.join(home_dir, ".travo", "tokens", hostname)

    def set_token(self, token: str, nosave: bool = False) -> bool:
        """
        Set and check the authentication token

        Unless @nosave is set, the token is saved in the home directory of the user
        for future uses.

        @return whether the token is valid
        """
        if self.token_type == JWT:
            t = time.time()
            response = self.session.get(
                self.base_url + "/oauth/token/info", data=dict(access_token=token)
            )
            try:
                json = response.json()
            except requests.HTTPError:
                response.raise_for_status()
            if "error" in json:
                assert json["error"] == "invalid_token"
                self.log.info(
                    _("invalid token", error_description=json["error_description"])
                )
                return False

            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token_expires_at = t + json["expires_in"]
        elif self.token_type == PERSONAL_ACCESS:
            self.session.headers.update({"PRIVATE-TOKEN": f"{token}"})

        self.token = token
        if not nosave:
            os.makedirs(os.path.dirname(self.token_file()), exist_ok=True)
            with os.fdopen(
                os.open(self.token_file(), os.O_WRONLY | os.O_CREAT, 0o600), "w"
            ) as handle:
                handle.write(token)
        return True

    def logout(self) -> None:
        """
        Logout from the forge

        Remove the token file as side effect
        """
        self.token = None
        self.token_expires_at = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
        if "TRAVO_TOKEN" in os.environ:
            del os.environ["TRAVO_TOKEN"]
        if "PRIVATE-TOKEN" in self.session.headers:
            del self.session.headers["PRIVATE-TOKEN"]
        token_file = self.token_file()
        # Testing whether the file exists before removing it is not
        # atomic; so just try to remove it.
        try:
            os.remove(token_file)
        except FileNotFoundError:
            pass
        self._current_user = None

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        anonymous_ok: bool = False,
    ) -> None:
        r"""
        Ensure that this GitLab session is authenticated

        - If this session is already authenticated, do nothing
        - If a token file exists, load the token from there, and set
          it from now on.
        - Otherwise if the `token_type` is set to "JWT" request a new token
          through login and password authentication, and set it.
        - if the `token_type` is set to "PERSONAL_ACCESS" request to input
          the personal access token.
        - Unless the credentials are passed as arguments, they are requested
          interactively by the user.
          The token is stored in a token file for future reuse.

        In case of failure, for example, because no credentials are
        provided and `self.interactive` is `False`, an
        AuthenticationError is raised.

        Setup: use a temporary directory instead of $HOME::

            >>> GitLab.home_dir = getfixture('tmp_path')

        Create a fresh gitlab session:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab_url = getfixture('gitlab_url')
            >>> gitlab = GitLab(gitlab_url)

        Check that, for now, there is no token and no token file:

            >>> gitlab.token
            >>> gitlab.token_file()
            '/.../.travo/tokens/...'
            >>> assert not os.path.isfile(gitlab.token_file())

        Login. Here the credentials are passed as parameters; they
        typically are instead entered interactively by the user:

            >>> gitlab.login(username="student1",
            ...              password="aqwzsx(")
            Traceback (most recent call last):
            ...
            AuthenticationError: Authentication failed; invalid username or password?

            >>> gitlab.login(username="student1",
            ...              password="aqwzsx(t1")

        Now we may access non-public information like the user status:

            >>> gitlab.get_status()
            {'emoji': None, 'message': None, 'availability': None, 'message_html': ''...

        A token file has been created:

            >>> assert os.path.isfile(gitlab.token_file())

        With a new instance on the same server, we may authenticate
        directly using the token:

            >>> gitlab2 = GitLab(gitlab_url)
            >>> gitlab2.login()
            >>> gitlab.get_status()
            {'emoji': None, 'message': None, 'availability': None, 'message_html': ''...

        If the environment variable `TRAVO_TOKEN` exists, then it is used as the token
        and the rest of the login is bypassed (no interactive, no saved token file).
        This could be used by scripts.

            >>> token = gitlab2.token
            >>> gitlab2.logout()
            >>> os.environ["TRAVO_TOKEN"] = token
            >>> gitlab3 = GitLab(gitlab_url)
            >>> gitlab3.login()
            >>> gitlab.get_status()
            {'emoji': None, 'message': None, 'availability': None, 'message_html': ''...

        """
        if self.token is not None and self.token_type == JWT:
            assert self.token_expires_at is not None
            if time.time() < self.token_expires_at - 60:
                # Assumption: the token is valid; unless the token has
                # been revoked, this should be correct.
                return
            # The token has expired or is about to expire in less than
            # one minute. Clear it. We assume that the token in the
            # persistent cache or in TRAVO_TOKEN, if present, are the
            # same. This is correct unless there is a concurrent travo
            # process.  So clear then as well.
            self.logout()

        # Try to retrieve token from environment variable
        if "TRAVO_TOKEN" in os.environ:
            if self.set_token(os.environ["TRAVO_TOKEN"], nosave=True):
                return
            raise AuthenticationError(
                _("invalid token environment variable", url=self.base_url)
            )

        # Try to retrieve token from persistent cache
        token_file = self.token_file()
        if os.path.exists(token_file):
            if self.set_token(io.open(token_file).read().rstrip()):
                return
            self.logout()

        # No token available
        if self.token_type == JWT:
            if username is None:
                if self._current_user is anonymous_user and anonymous_ok:
                    return
                username, password = self.on_missing_credentials(
                    forge=self, username=username, password=password
                )
            if username is not None and username == "anonymous" and anonymous_ok:
                self._current_user = anonymous_user
                return

            result = self.session.post(
                self.base_url + "/oauth/token",
                params=dict(
                    grant_type="password",
                    username=username,
                    password=password,
                    scope="api",
                ),
            )
            token = result.json().get("access_token")
            # TODO: handle connection failures
            if token is None:
                # TODO: pourrait réessayer
                raise AuthenticationError(_("invalid credentials", url=self.base_url))
            assert self.set_token(token)

        elif self.token_type == PERSONAL_ACCESS:
            print(
                _("personal access token")
                + ".\n"
                + _("no personal access token")
                + "\n"
                + f"`{self.base_url}/-/user_settings/personal_access_tokens`"
            )
            token = getpass.getpass(_("personal access token") + ": ")
            assert self.set_token(token)

    def get(self, path: str, data: dict = {}) -> requests.Response:
        """Issue a GET request to the forge's API"""
        url = self.api + path
        self.log.debug(f"GET {url} {data}")
        return self.session.get(url, data=data)

    def get_json(self, path: str, data: dict = {}, depaginate: bool = False) -> JSON:
        """
        Issue a GET request to the forge's API and return the result as JSON

        Raise if the response status is unsuccessful or if the JSON
        result contains an error message

        If `depaginate` is True, then the result is assumed to be a list,
        and further GET request are issued to recover and concatenate
        all pages.
        """
        res = self.get(path, data)
        res.raise_for_status()

        json = res.json()
        if "message" in json:
            raise RuntimeError(f"API error {json['message']}")

        if depaginate:
            assert isinstance(json, list)
            while "next" in res.links:
                res = self.session.get(res.links["next"]["url"])
                res.raise_for_status()
                newjson = res.json()
                if "message" in newjson:
                    raise RuntimeError(f"API error {newjson['message']}")
                json.extend(newjson)
        return json

    def put(self, path: str, data: dict = {}) -> requests.Response:
        """Issue a PUT request to the forge's API"""
        url = self.api + path
        self.log.debug(f"PUT {url} {data}")
        return self.session.put(url, data=data)

    def put_json(self, path: str, data: dict = {}) -> JSON:
        """
        Issue a POST request to the forge's API and return the result as JSON

        Raise if the response status is unsuccessful or if the JSON
        result contains an error
        """
        res = self.put(path, data)
        res.raise_for_status()

        json = res.json()
        if "message" in json and not json["message"].startswith("20"):
            raise RuntimeError(f"API error {json['message']}")

        return json

    def post(self, path: str, data: dict = {}, files: dict = {}) -> requests.Response:
        """Issue a POST request to the forge's API"""
        url = self.api + path
        self.log.debug(f"POST {url} {data}")
        return self.session.post(url, data=data, files=files)

    def post_json(self, path: str, data: dict = {}, files: dict = {}) -> JSON:
        """
        Issue a POST request to the forge's API and return the result as JSON

        Raise if the response status is unsuccessful or if the JSON
        result contains an error
        """
        res = self.post(path, data, files)
        res.raise_for_status()

        json = res.json()
        if "message" in json and not json["message"].startswith("20"):
            raise RuntimeError(f"API error {json['message']}")

        return json

    def delete(self, path: str) -> requests.Response:
        """Issue a DELETE request to the forge's API"""
        url = self.api + path
        self.log.debug(f"DELETE {url}")
        return self.session.delete(url)

    def get_status(self) -> JSON:
        """Get the user's status"""
        return self.get("user/status").json()

    def namespace_id(self, path: str) -> Optional[str]:
        """
        Return the id of the given namespace

        Recall that, in GitLab's terminology, a namespace is either a
        group or a user's home.

        Limitation: the current implementation requires the user to be
        logged in and to be at least maintainer of the namespace. This
        is ok since this method is currently only used for creating
        projects or subgroups in the namespace). However the error
        message may be misleading if a user tries to create a project
        or group in a namepace they are not maintainer of.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> forge = getfixture("gitlab")
            >>> forge.login()
            >>> forge.namespace_id("")
            >>> forge.namespace_id("student1")
            2
            >>> forge.namespace_id("group1")
            8
            >>> forge.namespace_id("group1/subgroup")
            9

            >>> forge.namespace_id("not_a_group")
            Traceback (most recent call last):
            ...
            travo.gitlab.ResourceNotFoundError: Namespace not_a_group not found

            >>> forge.namespace_id("groupe-public-test/projet-public")
            Traceback (most recent call last):
            ...
            travo.gitlab.ResourceNotFoundError: ... public-test/projet-public not found
        """
        if not path:
            return None
        path_encoded = urlencode(path)
        json = self.get(f"/namespaces/{path_encoded}").json()
        if "id" in json:
            return typing.cast(str, json["id"])
        assert json["message"] == "404 Namespace Not Found"

        # With GitLab 11, the above api requests fails for users; fall back to a search
        json = self.get(f"/namespaces?search={path_encoded}").json()
        if json:
            return typing.cast(str, json[0]["id"])
        raise ResourceNotFoundError(f"Namespace {path} not found")

    def get_resource(self, cls: Type[R], path: Union[R, int, str], **args: Any) -> R:
        """
        Get a resource from its path

        Raise an error if the resource does not exist.

        `path` should be non empty.
        """
        # If already a resource, return as is
        if isinstance(path, cls):
            return path
        path = cast(str, path)
        assert path
        url = cls._resource_type_api_url + "/" + urlencode(path)
        json = self.get(url, data=args).json()
        if "error" in json:
            raise RuntimeError(f"{cls.__name__} {path} not found: {json['error']}")
        message = json.get("message", "")
        if message and message[0] != "2":
            raise ResourceNotFoundError(
                f"{cls.__name__} {path} not found: {json['message']}"
            )
        return cls(gitlab=self, **json)

    def ensure_resource(
        self,
        cls: Type[R],
        path: str,
        name: str,
        get_resource_args: dict = {},
        **attributes: Any,
    ) -> R:
        """
        Ensure that a resource of the given class and attributes exists

        Return the resource, after creating or updating it if needed.

        This will force a login.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> forge = getfixture('gitlab')
            >>> path = getfixture('project_path'); path
            'student1/temporary-test-projet-20...'
            >>> name = getfixture('project_name'); name
            'temporary test projet created at 20...'

            >>> resource = forge.ensure_resource(Project, path, name=name,
            ...                                  build_timeout=645)

        Tear down and test remove_resource:

            >>> forge.remove_resource(Project, path, force=True)
        """
        resource_type = cls.__name__
        self.login()
        try:
            resource = self.get_resource(cls, path, **get_resource_args)
            self.log.info(f"{resource_type} {path} already created")
            resource.setattributes(**attributes)
            return resource
        except ResourceNotFoundError:
            pass
        self.log.info(f"Creating {resource_type} {path}")
        namespace = os.path.dirname(path)
        namespace_id = self.namespace_id(namespace)
        path = os.path.basename(path)
        json = self.post(
            cls._resource_type_api_url,
            {
                "path": path,
                cls._resource_type_namespace_id_attribute: namespace_id,
                "name": name,
                **attributes,
            },
        ).json()
        if "message" in json:
            raise RuntimeError(f"{resource_type} creation failed: {json['message']}")
        assert isinstance(json, dict)
        return cls(gitlab=self, **json)

    def confirm(self, message: str) -> bool:
        """
        Asks the user to confirm a dangerous or irreversible operation.

        @result is True if the user answers yes, false otherwise.
        """
        self.log.warn(message)
        confirm = input("y/N:")
        return confirm.startswith("y")

    def remove_resource(
        self, cls: Type[R], id_or_path: Union[int, str], force: bool = False
    ) -> None:
        """
        Remove resource (IRREVERSIBLE!)

        By default, ask interactively for confirmation. Use
        `force=True` to bypass the confirmation.

        See :meth:`remove_project` for an example
        """
        resource_type = cls.__name__
        if not force:
            if not self.confirm(
                f"Are you sure you want to remove {resource_type} {id_or_path}?"
            ):
                self.log.warn("Removal ignored")
                return

        self.login()
        self.log.info(f"Removing {resource_type} {id_or_path}")
        if isinstance(id_or_path, str):
            id_or_path = urlencode(id_or_path)
        url = f"{cls._resource_type_api_url}/{id_or_path}"
        json = self.delete(url).json()
        if json != {"message": "202 Accepted"}:
            raise RuntimeError(f"{resource_type} removal failed: {json['message']}")

    def get_project(self, path: Union[int, str, "Project"]) -> "Project":
        """
        Get a project from its path

        If path is already a project, return it as is.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture('gitlab')
            >>> project = gitlab.get_project("groupe-public-test/projet-public")
            >>> project.name
            'Projet public'
            >>> project.http_url_to_repo
            'http://.../groupe-public-test/projet-public.git'

            >>> project = gitlab.get_project("student1/nom-valide")
            Traceback (most recent call last):
            ...
            travo.gitlab.ResourceNotFoundError: ...ide not found: 404 Project Not Found

            >>> gitlab.login()
            >>> project = gitlab.get_project("student1/nom-valide")
            >>> project.owner
            User(gitlab=...)
        """
        return self.get_resource(Project, path)

    def ensure_project(self, path: str, name: str, **attributes: Any) -> "Project":
        """
        Ensure that a project with the given attributes exists

        Return the project, after creating or updating it if needed.

        This will force a login.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> forge = getfixture('gitlab')
            >>> project = forge.ensure_project("groupe-public-test/projet-public",
            ...                                name="Projet public")
            >>> project.name
            'Projet public'
            >>> project.http_url_to_repo
            'http://.../groupe-public-test/projet-public.git'

            >>> path = getfixture('project_path'); path
            'student1/temporary-test-projet-20...'
            >>> name = getfixture('project_name'); name
            'temporary test projet created at 20...'

            >>> project = forge.ensure_project(path, name=name, build_timeout=645)
            >>> assert project.path_with_namespace == path
            >>> assert project.path == os.path.basename(path)
            >>> assert project.name == name
            >>> assert project.build_timeout == 645

            >>> project = forge.get_project(path)
            >>> assert project.path_with_namespace == path
            >>> assert project.path == os.path.basename(path)
            >>> assert project.name == name

        Test that ensure_project is idempotent:

            >>> reproject = forge.ensure_project(path, name=name, build_timeout=646)
            >>> assert reproject.id == project.id
            >>> assert reproject.build_timeout == 646

        Test that attributes are updated:


        Tear down and test remove_project:

            >>> forge.remove_project(path, force=True)
            >>> forge.get_project(path).extra['marked_for_deletion_on'] # doctest: +SKIP
            '...'
        """
        return self.ensure_resource(Project, path=path, name=name, **attributes)

    def remove_project(self, id_or_path: Union[str, int], force: bool = False) -> None:
        """
        Remove project (DANGEROUS!)

        """
        self.remove_resource(Project, id_or_path, force=force)

    def get_namespace(self, path: Union[str, "Namespace"]) -> "Namespace":
        return self.get_resource(Namespace, path)

    def get_group(
        self, path: Union[int, str, "Group"], with_projects: bool = False
    ) -> "Group":
        """
        Get a project from its path

        If path is already a group, return it as is.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture("gitlab")

            >>> group = gitlab.get_group("groupe-public-test", with_projects=True)

            >>> group.full_name
            'Groupe public test'
            >>> group.web_url
            'http://.../groups/groupe-public-test'
            >>> group.projects[0].name
            'Projet public'
        """
        return self.get_resource(Group, path, with_projects=with_projects)

    def ensure_group(
        self, path: str, name: str, with_projects: bool = False, **attributes: Any
    ) -> "Group":
        """
        Ensure that a group with the given attributes exists

        Return the group, after creating or updating it if needed.

        This will force a login.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> forge = getfixture('gitlab')
            >>> path =  getfixture('group_path')
            >>> name =  getfixture('group_name')

            >>> group = forge.ensure_group(path=path, name=name)
            >>> assert group.name == name
            >>> assert group.path == path

        Tear down:

            >>> forge.remove_group(path, force=True)
            >>> forge.get_project(path)
            Traceback (most recent call last):
            ...
            travo.gitlab.ResourceNotFoundError: ... not found: 404 Group Not Found
        """
        return self.ensure_resource(
            Group,
            path=path,
            name=name,
            get_resource_args=dict(with_projects=with_projects),
            **attributes,
        )

    def remove_group(self, id_or_path: Union[str, int], force: bool = False) -> None:
        """
        Remove group (DANGEROUS!)

        """
        self.remove_resource(Group, id_or_path, force=force)

    def get_current_user(self) -> Union["User", "AnonymousUser"]:
        """
        Get the currently logged in user (which may be 'anonymous')

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture("gitlab")

            >>> gitlab.login()
            >>> user = gitlab.get_current_user()
            >>> user.username
            'student1'

            >>> gitlab.logout()

            >>> gitlab.login(username="anonymous", anonymous_ok=True)
            >>> user = gitlab.get_current_user()
            >>> user.username
            'anonymous'
        """
        if self._current_user is None:
            self._current_user = User(gitlab=self, **self.get_json("/user"))

        return self._current_user

    def get_user(self, username: Optional[Union[int, str, "User"]] = None) -> "User":
        """
        Get a user from its username or id

        If input is already a user, it is returned as is.

        If no user is specified, raises.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture("gitlab")

            >>> user = gitlab.get_user("student1")
            >>> user.username
            'student1'
            >>> user.web_url
            'http://.../student1'
            >>> user.public_email

            >>> assert gitlab.get_user(user) is user
        """
        if username is None:
            raise (
                ValueError(
                    "forge.get_user() cannot be called without username; please use"
                    " forge.get_current_user()"
                )
            )

        if isinstance(username, str):
            json = self.get_json(f"/users?username={username}")
            assert isinstance(json, list)
            if not json:
                raise ResourceNotFoundError(_("user not found", username=str(username)))
            assert len(json) == 1
            json = json[0]
            return User(gitlab=self, **json)
        else:
            return self.get_resource(User, username)

    def git(
        self,
        args: Sequence[str],
        anonymous: bool = False,
        anonymous_ok: bool = False,
        **kargs: Any,
    ) -> subprocess.CompletedProcess:
        """
        Run git, passing down credentials

        This assumes that https urls are used, and that the git
        command interacts with the same gitlab instance and same
        username.

        Example:

            >>> capfd = getfixture('capfd')

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab_url = getfixture('gitlab_url')

            >>> url = (f"{gitlab_url}/student1/"
            ...        "Fork-de-student1-du-projet-Exemple-projet-CICD.git")
            >>> gitlab = getfixture('gitlab')
            >>> gitlab.login()
            >>> gitlab.git(["clone", url, "repository"], cwd=gitlab.home_dir)

            >>> capture = capfd.readouterr()
            >>> assert 'repository' in capture.err

            >>> gitlab.git(["remote", "-v"],
            ...            cwd=os.path.join(gitlab.home_dir, "repository"))

            >>> capture = capfd.readouterr()
            >>> assert 'origin' in capture.out
            >>> assert f'{url} (fetch)' in capture.out
            >>> assert f'{url} (push)' in capture.out
        """
        env = os.environ.copy()
        git = ["git"]
        if not anonymous:
            self.login(anonymous_ok=anonymous_ok)
            if self.get_current_user() is not anonymous_user:
                env["TRAVO_TOKEN"] = cast(str, self.token)
                env["GIT_ASKPASS"] = "travo-echo-travo-token"
                git = ["git", "-c", "credential.username=oauth2"]
        return run(git + list(args), env=env, **kargs)

    def ensure_git(self, dir: str) -> None:
        """
        Ensure that git is initialized for this local directory

        That is: `git init` has been run.
        """
        self.git(
            ["init"],
            cwd=dir,
            capture_output=True,
            check=False,
            anonymous_ok=True,
        )

    def ensure_local_git_configuration(self, dir: str) -> None:
        """
        Ensure that git is configured for this local directory

        That is: `user.name` and `user.email` are set to enable commits.
        """
        for item in ["name", "email"]:
            res = self.git(
                ["config", "--local", f"user.{item}"],
                cwd=dir,
                capture_output=True,
                check=False,
                anonymous_ok=True,
            )
            if res.returncode != 0 or res.stdout.decode() == "anonymous\n":
                user = self.get_current_user()
                self.git(
                    ["config", "--local", f"user.{item}", getattr(user, item)],
                    cwd=dir,
                    anonymous_ok=True,
                )

    def collect_forks(
        self,
        path: str,
        username: Optional[str] = None,
        template: str = "{username}",
        date: Optional[str] = None,
    ) -> None:
        """
        Collect all forks of this project

        By cloning (or pulling if already cloned there) the master
        branch of each fork in a directory. The name of that directory
        is configured by the parameter 'template' where '{username}'
        is substituted by the username of the owner of the fork. This
        assumes that the fork was created in the owner's namespace.

        If `date` is specified, than the latest commit on the master
        branch before that date is checked out.

        If `username` is specified, then only the fork of the given
        user is collected.
        """
        self.login()
        project = self.get_project(path)
        forks = project.get_forks(recursive=True)
        bad_projects = []
        for fork in forks:
            if fork.owner is not None:
                if username is not None and fork.owner.username != username:
                    continue
                self.log.info(
                    f"Download/update repository for {fork.owner.username} at date"
                    f" {date}:"
                )
                path = template.format(username=fork.owner.username, path=fork.path)
                try:
                    fork.clone_or_pull(path, date=date)
                except subprocess.CalledProcessError:
                    bad_projects.append(fork.http_url_to_repo)
                    if len(bad_projects) > 0:
                        self.log.warning(
                            f"{len(bad_projects)} corrupted or empty project, check the"
                            " links :"
                        )
                        for url in bad_projects:
                            self.log.warning(url)

    def http_url_to_repo(self, path: str) -> str:
        """
        Return the http clone url for the repository with given path.

        Example:

            >>> forge = getfixture('gitlab')
            >>> forge.http_url_to_repo("Foo/Bar")
            'http://.../Foo/Bar.git'
        """
        return f"{self.base_url}{path}.git"


Forge = GitLab


# TODO: Design: should a resource be a resourceref?
@dataclass(frozen=True)
class ResourceRef:
    """
    A reference to a resource on some forge

    Examples:

    The main purpose of this class is to factor out the parsing of
    arguments specifying a resource. It may be specified from a URL:

        >>> ref = ResourceRef(url="https://gitlab.xxx.yy/Foo/Bar")
        >>> ref.forge
        GitLab: https://gitlab.xxx.yy/
        >>> ref.path
        'Foo/Bar'
        >>> ref = ResourceRef(url="https://gitlab.xxx.yy:3456/Foo/Bar")
        >>> ref.forge
        GitLab: https://gitlab.xxx.yy:3456/

    or from an existing :class:`Forge` object and a path. Note that
    this follows GitLab's convention of referencing resources by their
    absolute path, without an initial '/'.

        >>> forge = GitLab("https://gitlab.xxx.yy/")
        >>> ref = ResourceRef(forge=forge, path="Foo/Bar")
        >>> ref.forge
        GitLab: https://gitlab.xxx.yy/
        >>> ref.path
        'Foo/Bar'

        >>> forge = GitLab("https://gitlab.xxx.yy/")
        >>> ref = ResourceRef(forge=forge, path="/Foo/Bar")
        >>> ref.forge
        GitLab: https://gitlab.xxx.yy/
        >>> ref.path
        'Foo/Bar'

    If there is a `.git` suffix (as in a git repo url), it is stripped::

        >>> ref = ResourceRef(url="https://gitlab.xxx.yy/Foo/Bar.git")
        >>> ref.path
        'Foo/Bar'

    The if the url look like a ssh git repository, the forge url is extrapolated

        >>> ref = ResourceRef(url="git@gitlab.xxx.yy:Foo/Bar.git")
        >>> ref.forge
        GitLab: https://gitlab.xxx.yy/
        >>> ref.path
        'Foo/Bar'

    """

    # This is a bit clunky as dataclasses don't yet have good support
    # for:
    # - setting mandatory attributes in __post_init__
    # - setting frozen attributes in __post_init__
    # see e.g. https://groups.google.com/forum/#!topic/dev-python/7vBAZn_jEfQ
    forge: "Forge" = field(default=cast("Forge", None))
    path: str = field(default=cast("str", None))
    url: InitVar[Optional[str]] = None

    def __post_init__(self, url: Optional[str] = None) -> None:
        if (self.forge is None) == (url is None):
            raise ValueError("Exactly one of `forge` or `url` must be specified")
        if (self.path is None) == (url is None):
            raise ValueError("Exactly one of `path` or `url` must be specified")
        if url is not None:
            u = urllib.parse.urlparse(url)
            if u.scheme != "":
                root_url = urllib.parse.urlunparse([u.scheme, u.netloc, "", "", "", ""])
                path = u.path
            else:
                # Assume a ssh
                r = re.search("^(.*@)?([^:]+):(.*?)$", url)
                if r is not None:
                    root_url = "https://" + r.groups()[1]
                    path = r.groups()[2]
            object.__setattr__(self, "forge", GitLab(root_url))
            object.__setattr__(self, "path", path)
        object.__setattr__(self, "path", self.path.lstrip("/"))
        if self.path.endswith(".git"):
            object.__setattr__(self, "path", self.path[:-4])


class ClassCallMetaclass(type):
    def __call__(cls: Type[R], *args: Any, **kwargs: Any) -> R:  # type: ignore
        extra = kwargs  # the collected datafields from the class
        kwargs = {}
        for f in fields(cls):
            if f.name in extra:
                kwargs[f.name] = extra.pop(f.name)
        kwargs["extra"] = extra
        return cast(R, super().__call__(*args, **kwargs))  # type: ignore


get_type_hints_cache: Dict[Type, Dict] = {}


def get_type_hints(cls: Type) -> Dict:
    type_hints = get_type_hints_cache.get(cls, None)
    if type_hints is None:
        type_hints = typing.get_type_hints(cls)
        get_type_hints_cache[cls] = type_hints
    return type_hints


@dataclass
class Resource(metaclass=ClassCallMetaclass):
    class AccessLevels(enum.IntEnum):
        GUEST = 10
        REPORTER = 20
        DEVELOPER = 30
        MAINTAINER = 40
        OWNER = 50

    __initialized: bool = field(default=False, repr=False, init=False)
    _read_only: ClassVar[Tuple[str, ...]] = field(
        default=("gitlab", "id"), repr=False, init=False
    )

    _resource_type_api_url: ClassVar[str]
    _resource_type_namespace_id_attribute: ClassVar[str] = "namespace_id"

    gitlab: GitLab
    id: int

    extra: Dict  # = field(default_factory=dict)

    def get_api_url(self) -> str:
        return f"{self._resource_type_api_url}/{self.id}"

    def __post_init__(self) -> None:
        self.__initialized = True

    def setattributes(self, **attributes: Any) -> None:
        """
        Sets the given attributes

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> project = getfixture('project')
            >>> project.build_timeout
            3600
            >>> project.description

            >>> project.setattributes(build_timeout=642, description="Foo 42")
            >>> project.build_timeout
            642
            >>> project.description
            'Foo 42'

        Test that the changes were indeed applied on the forge:

            >>> forge = project.gitlab
            >>> reproject = forge.get_project(project.path_with_namespace)
            >>> assert reproject.build_timeout == project.build_timeout
            >>> assert reproject.description == project.description
        """
        # Select only the attributes that were changed
        attributes = {
            key: value
            for key, value in attributes.items()
            if key not in self.__dict__ or value != self.__dict__[key]
        }

        if self.__initialized:
            # Check that the attributes are valid
            for key in attributes:
                if key in self._read_only:
                    raise AttributeError(f"Read only attribute: {key}")
                if key not in self.__dict__:
                    raise AttributeError(f"Unknown attribute: {key}")
            # Update the value in GitLab
            self.gitlab.put(self.get_api_url(), attributes)

        type_hints = get_type_hints(self.__class__)

        for key, value in attributes.items():
            # Set the value in `self`, using the type hints to
            # construct Resources from raw dictionaries when
            # relevant; for now are supported types of the form
            # Optional[Resource] or List[Resource]
            type_hint = type_hints[key]
            if typing_utils.issubtype(type_hint, Optional[Resource]):
                if typing_utils.issubtype(type_hint, Resource):
                    resource_type = type_hint
                else:
                    resource_type = typing_utils.get_args(type_hint)[0]
                if value is not None and not isinstance(value, resource_type):
                    assert isinstance(value, dict)
                    value = resource_type(gitlab=self.gitlab, **value)
            elif typing_utils.issubtype(type_hint, List[Resource]):
                resource_type = typing_utils.get_args(type_hint)[0]
                value = [resource_type(gitlab=self.gitlab, **v) for v in value]
            self.__dict__[key] = value

    def __setattr__(self, key: str, value: Any) -> None:
        """
        Sets the given attribute

        If the value has changed, the attribute is also set remotely
        on GitLab.

        This is syntactic sugar for :meth:`setattributes`. If setting
        many attributes at once, calling the latter is preferable as
        it uses a single API call.

        This is also used by dataclass upon the initialization of this
        object to set its attributes.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture('gitlab')
            >>> gitlab.login()
            >>> project = gitlab.get_project("student1/nom-valide")
            >>> import datetime
            >>> description = f"Description: {datetime.datetime.now()}"
            >>> import logging
            >>> gitlab.log.setLevel(logging.DEBUG)
            >>> project.description = description
            >>> project.description
            'Description: 20...'

            >>> assert project.description == description
            >>> project = gitlab.get_project("student1/nom-valide")
            >>> assert project.description == description
        """
        self.setattributes(**{key: value})

    def get_attributes(self) -> Dict:
        res = dict(self.__dict__)
        del res["gitlab"]
        for key, value in res["extra"].items():
            res[key] = value
        return res


@dataclass
class Project(Resource):
    _resource_type_api_url = "projects"
    _read_only = Resource._read_only + ("path", "namespace")

    name: str
    namespace: "Namespace"
    path: str
    name_with_namespace: str
    path_with_namespace: str

    created_at: str
    description: str
    tag_list: list

    default_branch: str

    ssh_url_to_repo: str
    http_url_to_repo: str
    readme_url: str
    avatar_url: str

    star_count: int
    forks_count: int

    last_activity_at: str

    web_url: Optional[str] = None
    shared_with_groups: List[Dict[str, Any]] = field(default_factory=list)
    visibility: Optional[str] = None
    merge_method: Optional[str] = None
    _links: Optional[dict] = None
    archived: Optional[bool] = None
    resolve_outdated_diff_discussions: Optional[bool] = None
    container_registry_enabled: Optional[bool] = None
    container_expiration_policy: Optional[dict] = None
    issues_enabled: Optional[bool] = None
    merge_requests_enabled: Optional[bool] = None
    wiki_enabled: Optional[bool] = None
    jobs_enabled: Optional[bool] = None
    snippets_enabled: Optional[bool] = None
    shared_runners_enabled: Optional[bool] = None
    lfs_enabled: Optional[bool] = None
    packages_enabled: Optional[bool] = None
    service_desk_enabled: Optional[bool] = None
    service_desk_address: Optional[str] = None
    empty_repo: Optional[bool] = None
    public_jobs: Optional[bool] = None
    only_allow_merge_if_pipeline_succeeds: Optional[bool] = None
    request_access_enabled: Optional[bool] = None
    only_allow_merge_if_all_discussions_are_resolved: Optional[bool] = None
    printing_merge_request_link_enabled: Optional[bool] = None
    can_create_merge_request_in: Optional[bool] = None
    issues_access_level: Optional[str] = None
    repository_access_level: Optional[str] = None
    merge_requests_access_level: Optional[str] = None
    forking_access_level: Optional[str] = None
    wiki_access_level: Optional[str] = None
    builds_access_level: Optional[str] = None
    snippets_access_level: Optional[str] = None
    pages_access_level: Optional[str] = None
    operations_access_level: Optional[str] = None
    analytics_access_level: Optional[str] = None
    emails_disabled: Optional[bool] = None
    ci_default_git_depth: Optional[int] = None
    ci_forward_deployment_enabled: Optional[bool] = None
    build_timeout: Optional[int] = None
    auto_cancel_pending_pipelines: Optional[bool] = None
    build_coverage_regex: Optional[str] = None
    allow_merge_on_skipped_pipeline: Optional[bool] = None
    remove_source_branch_after_merge: Optional[bool] = None
    suggestion_commit_message: Optional[str] = None
    auto_devops_enabled: Optional[bool] = None
    auto_devops_deploy_strategy: Optional[str] = None
    autoclose_referenced_issues: Optional[bool] = None

    creator_id: Optional[int] = None
    import_status: Optional[str] = None
    open_issues_count: Optional[int] = None
    ci_config_path: Optional[str] = None

    repository_storage: Optional[str] = None

    permissions: Optional[dict] = None
    forked_from_project: Optional["Project"] = None
    import_error: Optional[str] = None
    runners_token: Optional[str] = None
    owner: Optional["User"] = None

    build_git_strategy: Optional[str] = None
    restrict_user_defined_variables: Optional[bool] = None

    container_registry_image_prefix: Optional[str] = None
    topics: Optional[list] = None
    ci_job_token_scope_enabled: Optional[bool] = None
    squash_option: Optional[str] = None
    keep_latest_artifact: Optional[bool] = None

    def http_url_with_base_to_repo(self) -> str:
        return self.gitlab.base_url + self.path_with_namespace

    def archive(self) -> "Project":
        """Archive current project"""
        json = self.gitlab.post_json(f"/projects/{self.id}/archive")
        return Project(self.gitlab, **json)

    def export(self, forge: GitLab, full_path: Optional[str] = None) -> "Project":
        """
        Export this project to another GitLab instance.

        By default, the path is that of the original project.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> project = getfixture('project')
            >>> newforge = getfixture('gitlab')
            >>> newpath = getfixture('fork_path')
            >>> newproject = project.export(forge=newforge, full_path=newpath)
            >>> assert newproject.gitlab == newforge
            >>> assert newproject.path_with_namespace == newpath
            >>> branches = project.get_branches()
            >>> newbranches = newproject.get_branches()
            >>> for b in branches: del b['web_url']; del b['commit']['web_url']
            >>> for b in newbranches: del b['web_url']; del b['commit']['web_url']
            >>> assert branches == newbranches

        Tear down:

            >>> newforge.remove_project(newproject.path_with_namespace, force=True)
        """
        if full_path is None:
            full_path = self.path_with_namespace

        self.gitlab.log.info(
            f"Exporting project {self.path_with_namespace} to {full_path} on {forge}"
        )

        self.gitlab.post_json(f"/projects/{self.id}/export")
        while (
            self.gitlab.get_json(f"/projects/{self.id}/export")["export_status"]
            != "finished"
        ):
            if (
                self.gitlab.get_json(f"/projects/{self.id}/export")["export_status"]
                == "failed"
            ):
                json = self.gitlab.get_json(f"/projects/{self.id}/export")
                raise RuntimeError(f"export has failed {json}")
            time.sleep(1)
            self.gitlab.log.info("waiting for export to complete")
        res = self.gitlab.get(f"/projects/{self.id}/export/download")
        res.raise_for_status()

        files = {"file": ("file.tar.gz", io.BytesIO(res.content))}
        data = {
            "path": os.path.basename(full_path),
            "namespace": os.path.dirname(full_path),
        }
        json = forge.post_json("projects/import", data=data, files=files)
        id = json["id"]
        while forge.get_json(f"/projects/{id}/import")["import_status"] != "finished":
            time.sleep(1)
        return forge.get_project(id)

    def ensure_is_fork_of(self, forked_from: Union["Project", str]) -> "Project":
        """
        Ensure that this project is a fork of the given project

        Return this project, or an updated copy of it if needed
        """
        forked_from_path = (
            forked_from.path_with_namespace
            if isinstance(forked_from, Project)
            else forked_from
        )

        # Check the fork relationship and update it if needed
        if (
            self.forked_from_project is not None
            and self.forked_from_project.path_with_namespace == forked_from_path
        ):
            return self
        # The fork relationship needs to be set or updated
        self.gitlab.log.info(
            "Setting fork relation "
            f"from {self.path_with_namespace} "
            f"to {forked_from_path}"
        )

        if not isinstance(forked_from, Project):
            # This is both to check the existence of the requested
            # forked from project and recover its id
            forked_from = self.gitlab.get_project(path=forked_from_path)

        # In some cases, fork.forked_from_project may be None even if
        # the project actually has a fork relation set. This happens for
        # exemple with GitLab 15.3.3 in the following scenario
        # - C is a fork of B which is a fork of A
        # - B gets deleted
        # - C still appears as fork of A in the user interface; trying
        #   to set its fork relation to something else fails; C does not
        #   appear in the list of forks of A
        # We therefore systematically try to delete the fork relation; it
        # fails silently if there is none.
        self.gitlab.delete(f"/projects/{self.id}/fork")

        json = self.gitlab.post(f"/projects/{self.id}/fork/{forked_from.id}").json()
        if "message" in json:
            raise RuntimeError(f"failed: {json['message']}")
        self = Project(gitlab=self.gitlab, **json)
        assert self.forked_from_project is not None
        assert self.forked_from_project.path_with_namespace == forked_from_path
        return self

    # Note: the types are set to Any for the optional arguments for
    # compatibility with passing **attributes which are of type Any
    def ensure_fork(
        self,
        path: str,
        name: str,
        forked_from_path: Any = None,  # Optional[Union[str, Unknown]]
        forked_from_missing: Any = None,  # Callable[]
        initialized: Any = False,  # bool
        **attributes: Any,
    ) -> "Project":
        """
        Ensure that `path` is a fork of `self` with given name and attributes

        Creating the fork and configuring it if needed.

        If a project `f` with the given path already exists and
        `check_fork_relationship` is `False`, then the fork relation
        ship between `f` and `self` is not checked.

        Examples::

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> forge = getfixture('gitlab')
            >>> project = getfixture('project')

            >>> fork_path = getfixture('fork_path')
            >>> fork_name = getfixture('fork_name')
            >>> fork = project.ensure_fork(fork_path, fork_name, build_timeout=642)

            >>> assert fork.path_with_namespace == fork_path
            >>> assert fork.name == fork_name
            >>> assert fork.forked_from_project.id == project.id
            >>> assert fork.id == forge.get_project(fork_path).id
            >>> assert fork.build_timeout == 642
            >>> fork_id = fork.id

        Test that the operation is idempotent:

            >>> refork = project.ensure_fork(fork_path, fork_name)
            >>> assert refork.id == fork.id
            >>> assert refork.build_timeout == 642

        Test that attributes are updated:

            >>> refork = project.ensure_fork(fork_path, fork_name, build_timeout=643)
            >>> assert refork.id == fork.id
            >>> assert refork.build_timeout == 643
            >>> refork = forge.get_project(fork_path)
            >>> assert refork.build_timeout == 643

        Tear down:

            >>> forge.remove_project(fork_path, force=True)

        Notes: As of GitLab 11, forking through the API does not
        support choosing the target path and namespace (nor setting
        attributes at once?). As a workaround, the current
        implementation creates the target project independently, and
        then sets the fork relationship.

        Caveats:
        - The operation is not atomic, therefore more fragile

        - By default, the repository of the fork is *not*
          initialized. If `initialized` is set to True, then upon
          creation the default branch of the repository is initialized
          with that of the origin.

        Bonus:
        - Unlike the forking operation in the API, this is a
          synchronous operation: once the operation terminates
          the fork is guaranteed to be created.

        Internal options `forked_from_path` and `forked_from_missing`.
        If `forked_from_path` is set, let `forked_from` be the project
        pointed to by this path. This project should exist and be a
        (direct or indirect) fork of `self`. After calling
        `ensure_fork`, the fork project will be a fork of
        `forked_from`. `forked_from_path` may be `unknown`; in that
        case, the fork project should preexist, and already be a
        direct or indirect fork of `self`; otherwise the callback
        `forked_from_missing` will be called without arguments to
        handle the error reporting.
        """
        # self.gitlab.post(f"projects/{self.id}/fork",
        #                  path=os.path.basename(path),
        #                  namespace=os.path.dirname(path),
        #                  name=name,
        #                  **attributes)
        if forked_from_path is None:
            forked_from_path = self.path_with_namespace
        if forked_from_path is unknown:
            # Won't be able to create the fork or to set the fork relationship
            # Complain if this is required
            try:
                fork = self.gitlab.get_project(path=path)
            except ResourceNotFoundError:
                forked_from_missing()
            if fork.forked_from_project is None:
                forked_from_missing()

        fork = self.gitlab.ensure_project(path=path, name=name, **attributes)

        # If the repository is empty (the default branch does not
        # exist) then initialize the repository with the content
        # of the default branch of the original repository
        def is_initialized(repo: Project) -> bool:
            try:
                fork.get_branch(fork.default_branch)
                return True
            except ResourceNotFoundError:
                return False

        if initialized and not is_initialized(fork):
            if forked_from_path is unknown:
                forked_from_missing()
            self.gitlab.log.info(_("initializing submission"))
            forked_from = self.gitlab.get_project(forked_from_path)
            with tempfile.TemporaryDirectory() as tmpdirname:
                assignment_dir = os.path.join(tmpdirname, self.name)
                branch = forked_from.default_branch
                fork.gitlab.git(
                    [
                        "clone",
                        forked_from.http_url_with_base_to_repo(),
                        assignment_dir,
                    ]
                )
                assert os.path.isdir(assignment_dir)
                fork.gitlab.git(
                    ["push", fork.http_url_with_base_to_repo(), branch],
                    cwd=assignment_dir,
                )
            # Reload project, since the default branch (and other
            # properties?) may have changed
            fork = fork.gitlab.get_project(fork.id)

        if forked_from_path is unknown:
            # Just check that the fork of fork relationship is consistent
            f = fork
            while f.forked_from_project is not None:
                ancestor = self.gitlab.get_project(f.forked_from_project.id)
                if (
                    ancestor.forked_from_project is not None
                    and ancestor.forked_from_project.id == self.id
                ):
                    return fork
                f = ancestor
            raise RuntimeError(
                f"project {fork.path_with_namespace} "
                f"is not a fork of fork of {self.path_with_namespace}"
            )

        assert isinstance(forked_from_path, str)

        return fork.ensure_is_fork_of(forked_from_path)

    def share_with(
        self,
        group_or_user: Union["Group", "User", "Namespace"],
        access: Union[int, Resource.AccessLevels],
        expires_at: Optional[str] = None,
    ) -> None:
        """
        Grant the group `group` access to this repo

        The group maybe be the path or id of a group, or the group
        itself.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> forge   = getfixture("gitlab")
            >>> project = getfixture("project")
            >>> group   = getfixture("group")

            >>> project.share_with(group, project.AccessLevels.DEVELOPER)

            >>> project.shared_with_groups
            []
            >>> project = project.gitlab.get_project(project.path_with_namespace)
            >>> share, = project.shared_with_groups
            >>> assert share['group_id'] == group.id
            >>> assert share['group_access_level'] == project.AccessLevels.DEVELOPER

            >>> user = getfixture("user")
            >>> assert user.id in [u['id'] for u in project.get_members()]
            >>> other_user = getfixture("other_user")
            >>> assert not other_user.id in [u['id'] for u in project.get_members()]

            >>> project.share_with(user, project.AccessLevels.GUEST)
            >>> project.share_with(other_user, project.AccessLevels.GUEST)
            >>> project = project.gitlab.get_project(project.path_with_namespace)

            >>> assert user.id in [u['id'] for u in project.get_members()]
            >>> assert other_user.id in [u['id'] for u in project.get_members()]
        """
        if isinstance(group_or_user, User):
            # user_id = self.gitlab.get_user(group_or_user).id
            user_id = group_or_user.id
            if any(user_id == user["id"] for user in self.get_members()):
                return
            data: dict = dict(user_id=user_id, access_level=int(access))
            if expires_at is not None:
                data["expires_at"] = expires_at
            json = self.gitlab.post(f"/projects/{self.id}/members", data=data).json()
            assert json["id"] == user_id
            assert json["access_level"] == int(access)
        elif isinstance(group_or_user, Group):
            # group_id = self.gitlab.get_group(group_or_user).id
            group_id = group_or_user.id
            data = dict(group_id=group_id, group_access=int(access))
            if expires_at is not None:
                data["expires_at"] = expires_at
            json = self.gitlab.post(f"/projects/{self.id}/share", data=data).json()
            assert json["group_id"] == group_id
            assert json["group_access"] == int(access)
            assert json["project_id"] == self.id
        else:
            raise NotImplementedError()

    def get_forks_ssh_url_to_repo(self) -> List[str]:
        forks = self.gitlab.get(f"/projects/{self.id}/forks").json()
        return [fork["ssh_url_to_repo"] for fork in forks]

    def get_forks(
        self, recursive: Union[int, bool] = False, simple: bool = False
    ) -> List["Project"]:
        """Return the forks of this project

        @return a list of projects

        If `recursive` is True, the forks of these forks are explored
        recursively. Alternatively, one may specify a recursion depth,
        a depth of `1` being equivalent to `recursive=False`.

        If `simple` is True, then less information about each project
        is returned. In particular, `owner` is not set. On the other
        hand, it is about 5 times faster.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture('gitlab')

            >>> project = gitlab.get_project("groupe-public-test/projet-public")
            >>> project.get_forks()
            []

        Setup: use a temporary directory instead of $HOME; this won't
        be needed once the test below will use the test server::

            # >>> GitLab.home_dir = getfixture('tmp_path')

            # >>> gitlab = GitLab("https://gitlab.u-psud.fr")
            # >>> project = gitlab.get_project("Info111/2020-2021/Semaine2")
            # >>> forks = project.get_forks()
            # >>> assert len(forks) >= 9
            # >>> fork_path = 'Info111/2020-2021/CandidatsLibres/Semaine2'
            # >>> assert any(fork.path_with_namespace == fork_path for fork in forks)

            # >>> project = gitlab.get_project("Info111/2020-2021/MI3/Semaine2")
            # >>> forks = project.get_forks()
            # >>> assert len(forks) > 20   ## Beyond the default pagination size

            # >>> project = gitlab.get_project("Info111/2020-2021/Semaine2")
            # >>> forks = project.get_forks(recursive=True)
            # >>> assert len(forks) >= 180

        """
        json = self.gitlab.get_json(
            f"/projects/{self.id}/forks",
            # simple = True would reduce
            # output volume; however at this
            # stage e.g. owner is still needed
            # in some of our use_cases
            data=dict(simple=simple),
            depaginate=True,
        )
        forks = [
            Project(gitlab=self.gitlab, **fork)
            for fork in json
            if "default_branch" in fork  # ignore broken forks with no repositories
        ]
        if simple:
            # Set the forked_from_project information. Motivation: we
            # can set it for free, and this is important information
            # in our context, for example for
            # Submission.get_leader_and_team.
            for fork in forks:
                fork.forked_from_project = self
        if not isinstance(recursive, bool):
            recursive -= 1
        if recursive:
            forks = forks + [
                subfork
                for fork in forks
                for subfork in fork.get_forks(recursive=recursive, simple=simple)
            ]
        return forks

    def get_origin_commit(self) -> JSON:
        """
        Return the first (oldest) commit of the repository for the default branch.

        This is mainly user to check is two repositories are forks unknown from gitlab.
        See `get_possible_forks`.
        """

        # Need to iterate because there is no direct link to the last page nor a
        # ascending order
        page: Optional[str] = "1"
        while page is not None and page != "":
            res = self.gitlab.get(
                f"/projects/{self.id}/repository/commits",
                data={"per_page": 100, "page": page},
            )
            page = res.headers.get("X-Next-Page")
        json = res.json()
        if len(json) == 0:
            return None
        else:
            return json[-1]

    def get_possible_forks(
        self, deep: bool = False, nonfork: bool = False, progress: bool = False
    ) -> List["Project"]:
        """
        Iterate onto newer projects to detect is they are possible forks but not
        identified as such.

        It could happens because the fork relationship was lost (when a children is
        set to private), or if the code for the fork is uploaded into an new project.

        Note: this could be an expensive operation.
        It could be useful to restore the fork-relation ship.

        `deep` do more intrusive searches witing projects with a <40 (maintainer)
        visibility or those that are already a fork of something else.

        `progress` prints '.' on screen while searching (progress-bas feeling).

        `nonfork` returns also project with the same path that share no original
        commits. It can retrieve projects that are rebased for instance.
        """

        sha = self.get_origin_commit().get("id")

        if sha is None:
            return []

        result = []

        # Need to paginate because there could be a lot
        page: Optional[str] = "1"
        while page is not None and page != "":
            if progress:
                print(".", end="", flush=True)
            q = {"id_after": self.id, "page": page}
            if not deep:
                q["min_access_level"] = 40
            res = self.gitlab.get("/projects", data=q)
            page = res.headers.get("X-Next-Page")
            for json in res.json():
                other = Project(self.gitlab, **json)
                if other.forked_from_project is not None and (
                    not deep or other.forked_from_project.id == self.id
                ):
                    continue  # Already registered as a fork of something
                if progress:
                    print(".", end="", flush=True)
                if nonfork and other.path == self.path:
                    result.append(other)
                else:
                    other_sha = other.get_origin_commit()
                    if other_sha is not None:
                        other_sha = other_sha.get("id")
                    if sha == other_sha:
                        result.append(other)
                    if progress:
                        print(".", end="", flush=True)
        if progress:
            print("", flush=True)
        return result

    def add_origin(self, origin: "Project") -> JSON:
        """
        Register `self` as a fork of `origin`.
        """

        json = self.gitlab.post(f"/projects/{self.id}/fork/{origin.id}").json()
        return json

    def get_branches(self) -> List[JSON]:
        """
        Return the branches of this project

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture('gitlab')

            >>> project = gitlab.get_project("groupe-public-test/projet-public")
            >>> branches = project.get_branches()
            >>> from pprint import pprint
            >>> pprint(branches)                   # doctest: +SKIP
            [{'can_push': False,
              ...
              'default': True,
              'developers_can_merge': False,
              'developers_can_push': False,
              'merged': False,
              'name': 'master',
              'protected': True,
              'web_url': 'http://.../groupe-public-test/projet-public/-/tree/master'}]
        """
        return cast(
            list, self.gitlab.get(f"/projects/{self.id}/repository/branches").json()
        )

    def get_branch(self, branch_name: Optional[str] = None) -> JSON:
        """
        Return the given/default branch of the project
        """
        if branch_name is None:
            branch_name = self.default_branch

        res = self.gitlab.get(f"/projects/{self.id}/repository/branches/{branch_name}")
        json = res.json()
        if json.get("message") == "404 Branch Not Found":
            raise ResourceNotFoundError(f"Branch {branch_name} not found")
        return json

    def ensure_branch(
        self, branch_name: Optional[str] = None, ref: Optional[str] = None
    ) -> JSON:
        """
        Ensure the existence of the given/default branch of the project
        """
        if branch_name is None:
            branch_name = self.default_branch
        if ref is None:
            ref = self.default_branch
        try:
            return self.get_branch(branch_name)
        except ResourceNotFoundError:
            pass
        return self.gitlab.post_json(
            f"/projects/{self.id}/repository/branches",
            data=dict(branch=branch_name, ref=ref),
        )

    def get_file(self, file: str, ref: str) -> JSON:
        """Get a file from the repository"""
        file = urlencode(file)
        json = self.gitlab.get(
            f"/projects/{self.id}/repository/files/{file}",
            data=dict(
                ref=ref,
            ),
        ).json()
        error = json.get("error", json.get("message"))
        if error is not None:
            raise RuntimeError(
                f"get file {file} of ref {ref} "
                f"of project {self.path_with_namespace} failed: "
                f"{error}"
            )
        return json

    def ensure_file(
        self,
        file: str,
        branch: Optional[str] = None,
        content: Optional[str] = None,
        encoding: str = "text",  # Literal("base64", "text")
        commit_message: str = "commit",
    ) -> None:
        """Ensure file exists in the repository (with given content)

        If the file does not exist, it is initialized with the given
        content (by default "Lorem ipsum"). If `content` is given and
        the file exists but with a different content, the file content
        is updated accordingly. In either case, a commit is issued,
        with the given commit message.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> project = getfixture("project")
            >>> branch = "mybranch"
            >>> b = project.ensure_branch(branch)
            >>> filename = "myfile"
            >>> project.get_file(filename, branch)
            Traceback (most recent call last):
            ...
            RuntimeError: get file myfile of ref mybranch
            of project student1/temporary-test-projet-20...
            failed: 404 Commit Not Found

            >>> project.ensure_file(filename, branch)

            >>> file = project.get_file(filename, branch)
            >>> import base64
            >>> assert base64.b64decode(file['content']) == b'Lorem ipsum'

            >>> project.ensure_file(filename, branch)

            >>> project.ensure_file(filename, branch,
            ...                     content="foo")

            >>> file = project.get_file(filename, branch)
            >>> import base64
            >>> assert base64.b64decode(file['content']) == b'foo'

            >>> project.ensure_file(filename, branch,
            ...                     content='Zm9v',
            ...                     encoding="base64")

            >>> file = project.get_file(filename, branch)
            >>> assert file['content'] == 'Zm9v'

            >>> project.get_file("foobar", branch)
            Traceback (most recent call last):
            ...
            RuntimeError: get file foobar of ref mybranch
            of project student1/temporary-test-projet-20...
            failed: 404 Commit Not Found

            >>> project.get_file(filename, "foobar")
            Traceback (most recent call last):
            ...
            RuntimeError: get file foobar of ref mybranch
            of project student1/temporary-test-projet-20...
            failed: 404 Commit Not Found
        """
        file = urlencode(file)
        if branch is None:
            branch = self.default_branch
        try:
            oldcontent = self.get_file(file, branch)["content"]
        except RuntimeError:
            oldcontent = None
        #  Compare old and desired content
        if oldcontent is not None:
            if content is None:
                return
            if encoding == "text":
                oldcontent = base64.b64decode(oldcontent)
            if oldcontent == content:
                return
        if content is None:
            content = "Lorem ipsum"
        data = dict(
            content=content,
            branch=branch,
            commit_message=commit_message,
        )
        if encoding != "text":
            data["encoding"] = encoding
        if oldcontent is None:  # file does not yet exist
            json = self.gitlab.post(
                f"/projects/{self.id}/repository/files/{file}", data=data
            ).json()
        else:
            json = self.gitlab.put(
                f"/projects/{self.id}/repository/files/{file}", data=data
            ).json()
        error = json.get("error", json.get("message"))
        if error is not None:
            raise RuntimeError(
                f"ensuring file {file} "
                f"of project {self.path_with_namespace} failed: "
                f"{error}"
            )

    def protect_branch(self, name: str) -> None:
        """
        Protect the project branch with given name

        Examples::

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> project = getfixture("project")
            >>> project.ensure_file("README.md",
            ...                     branch="main")

        Race condition: when running on CI, the protection of the
        branch may appear after a delay::

            >>> import time
            >>> time.sleep(1)

            >>> branch, = project.get_branches()
            >>> branch['name']
            'main'
            >>> branch['protected']                # doctest: +SKIP
            True

            >>> project.unprotect_branch('main')

            >>> branch, = project.get_branches()
            >>> branch['name']
            'main'

        2022-09-29, GitLab 15.4.0: this test fails; yet the branch
        indeed appears unprotected when inspecting branches on the
        GitLab UI. An update bug in the GitLab API?

            >>> branch['protected']                # doctest: +SKIP
            False

            >>> project.protect_branch('main')
            >>> branch, = project.get_branches()
            >>> branch['protected']                # doctest: +SKIP
            True

            >>> project.unprotect_branch('main')
            >>> branch, = project.get_branches()

            >>> branch['protected']                # doctest: +SKIP
            False
        """
        json = self.gitlab.post(
            f"/projects/{self.id}/protected_branches/", data=dict(name=name)
        ).json()
        if "message" in json:
            raise RuntimeError(
                f"protecting branch {name} of project"
                f" {self.path_with_namespace} failed: {json['message']}"
            )

    def unprotect_branch(self, name: str) -> None:
        """
        Unprotect the project branch with given name

        """
        r = self.gitlab.delete(f"/projects/{self.id}/protected_branches/{name}")
        if r.ok:
            return
        json = r.json()
        if "message" in json:
            raise RuntimeError(
                f"unprotecting branch {name} of project"
                f" {self.path_with_namespace} failed: {json['message']}"
            )

    def get_pipelines(self) -> JSON:
        """
        Return the pipelines for this project
        """
        return self.gitlab.get_json(f"/projects/{self.id}/pipelines", depaginate=True)

    def remove_pipelines(self) -> None:
        """
        Remove the pipelines for this project
        """
        for pipeline in self.get_pipelines():
            self.gitlab.delete(f'/projects/{self.id}/pipelines/{pipeline["id"]}')

    def get_reports(self, ref: Optional[str] = None) -> dict:
        """
        Returns pipelines, jobs, reports and logs (traces).

        This could be used to automatically grade (or estimate) the realisation of the
        students.

        Note: the gitlab API is weird thus this method returns a dict of possibly
        combined json object that merge pipelines, jobs and test_reports.

        The log (trace) is also parsed to check for "^ok " and "^not ok" possible tap
        outputs.

        If `ref` is not given, all refs are checked.
        Only the most recent pipeline of each ref is checked.
        """

        suites = {}
        pipelines = self.gitlab.get(f"/projects/{self.id}/pipelines").json()
        for pipeline in pipelines:
            pref = pipeline["ref"]
            if ref is not None and pref != ref:
                continue  # Skip unwanted refs
            if pref in suites:
                continue  # skip older pipeline for this ref

            suites[pref] = pipeline
            prefix = pref + "."

            report = self.gitlab.get(
                f"/projects/{self.id}/pipelines/{pipeline['id']}/test_report"
            ).json()
            for suite in report["test_suites"]:
                suites[prefix + suite["name"]] = suite

            jobs = self.gitlab.get(
                f"/projects/{self.id}/pipelines/{pipeline['id']}/jobs"
            ).json()
            for job in jobs:
                name = prefix + job["name"]
                if name in suites:
                    job.update(suites[name])
                suites[name] = job

                log = self.gitlab.get(
                    f"/projects/{self.id}/jobs/{job['id']}/trace"
                ).text
                job["log"] = log
                if "total_count" not in job:
                    ok = len(re.findall("^ok ", log, re.MULTILINE))
                    nok = len(re.findall("^not ok ", log, re.MULTILINE))
                    if ok != 0 or nok != 0:
                        job["success_count"] = ok
                        job["total_count"] = ok + nok

        return suites

    def fetch_artifact(self, job: Job, artifact_path: str) -> requests.Response:
        """
        fetch a single artifact file for a job and return it as Response

        Use `.text` or `.content` to retrieve content.
        """
        result = self.gitlab.get(
            f"/projects/{self.id}/jobs/{job['id']}/artifacts/{artifact_path}"
        )
        result.raise_for_status()
        return result

    def fetch_artifacts(
        self, job: Job, path: Optional[str] = None, prefix: str = ""
    ) -> None:
        # Variant: fetch the artifact for the branch or tag (not commit)
        result = self.gitlab.get(f"/projects/{self.id}/jobs/{job['id']}/artifacts")
        filebytes = io.BytesIO(result.content)
        myzipfile = zipfile.ZipFile(filebytes)
        for name in myzipfile.namelist():
            if name.startswith(prefix):
                myzipfile.extract(name, path=path)

    _get_creator_cache: Optional["User"] = None

    def get_creator(self) -> "User":
        """
        Return the creator of this project (with cache)

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> project = getfixture('project')
            >>> project.get_creator()
            User(gitlab=...username='student1'...)
        """
        if self._get_creator_cache is None:
            creator_id = self.creator_id
            if creator_id is None:
                # Performance hog: this fetches a lot of information
                # form the GitLab API (everything about the project)
                # only to retrieve one piece of information. Could
                # this be optimized?
                creator_id = self.gitlab.get_project(
                    self.path_with_namespace
                ).creator_id
            self._get_creator_cache = self.gitlab.get_user(creator_id)
        return self._get_creator_cache

    def get_members(self) -> JSON:
        """
        Return the list of all members
        """

        return self.gitlab.get_json(f"/projects/{self.id}/members/all", depaginate=True)

    _get_owner_cache: Optional[JSON] = None

    def get_owners(self) -> JSON:
        """
        Return the owners including all indirect members with an access_level >= 50

        Note: this cache
        """

        res = self._get_owner_cache
        if res is not None:
            return res

        res = []

        owner = self.owner
        if owner is not None:
            res.append(owner)

        # In a group there is no owners, just check in all members to find one
        members = self.get_members()
        for m in members:
            if m["access_level"] < 50:
                continue
            if owner is not None and m["id"] == owner.id:
                continue
            res.append(self.gitlab.get_user(m["username"]))

        self._get_owner_cache = res
        return res

    def get_compare(
        self, from_project: "Project", ref: str = "", from_ref: str = ""
    ) -> JSON:
        """
        Compare `self` to another project.

        If ref of from_ref is empty, the default branches of the projects are used.

        This can be used to get the diff.
        """

        if ref == "":
            ref = self.default_branch

        if from_ref == "":
            from_ref = from_project.default_branch

        res = self.gitlab.get(
            f"/projects/{self.id}/repository/compare",
            data={"from": from_ref, "to": ref, "from_project_id": {from_project.id}},
        ).json()
        return res

    def get_badges(self, name: Optional[str] = None) -> List[JSON]:
        """
        Return the badges of this project

        If `name` is provided, then only badges with that name are
        returned.
        """
        if name is not None:
            data = dict(name=name)
        else:
            data = {}
        return cast(
            list, self.gitlab.get_json(f"/projects/{self.id}/badges", data=data)
        )

    def ensure_badge(self, name: str, link_url: str, image_url: str) -> JSON:
        """
        Ensure the existence of a badge with the given property

        This assumes that there is at most a single page with the given name.

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> project = getfixture('project')

            >>> project.get_badges()
            []
            >>> project.ensure_badge(name='Foo',
            ...                      link_url='https://foo_link',
            ...                      image_url='https://foo_image',
            ... )
            {'name': 'Foo',
             'link_url': 'https://foo_link',
             'image_url': 'https://foo_image',
             'rendered_link_url': 'https://foo_link',
             'rendered_image_url': 'https://foo_image',
             'id': ...,
             'kind': 'project'}
            >>> project.ensure_badge(name='Bar',
            ...                      link_url='https://bar_link',
            ...                      image_url='https://bar_image',
            ... )
            {'name': 'Bar',
             'link_url': 'https://bar_link',
             'image_url': 'https://bar_image',
             'rendered_link_url': 'https://bar_link',
             'rendered_image_url': 'https://bar_image',
             'id': ...,
             'kind': 'project'}
            >>> project.get_badges(name="Bar")
            [{'name': 'Bar',
              'link_url': 'https://bar_link',
              'image_url': 'https://bar_image',
              'rendered_link_url': 'https://bar_link',
              'rendered_image_url': 'https://bar_image',
              'id': ...,
              'kind': 'project'}]
            >>> project.get_badges()
            [{'name': 'Foo',
              'link_url': 'https://foo_link',
              'image_url': 'https://foo_image',
              'rendered_link_url': 'https://foo_link',
              'rendered_image_url': 'https://foo_image',
              'id': ...,
              'kind': 'project'},
             {'name': 'Bar',
              'link_url': 'https://bar_link',
              'image_url': 'https://bar_image',
              'rendered_link_url': 'https://bar_link',
              'rendered_image_url': 'https://bar_image',
              'id': ...,
              'kind': 'project'}]

            >>> project.ensure_badge(name='Bar',
            ...                      link_url='https://bar2_link',
            ...                      image_url='https://bar2_image',
            ... )
            {'name': 'Bar',
             'link_url': 'https://bar2_link',
             'image_url': 'https://bar2_image',
             'rendered_link_url': 'https://bar2_link',
             'rendered_image_url': 'https://bar2_image',
             'id': ...,
             'kind': 'project'}
            >>> project.get_badges(name="Bar")
            [{'name': 'Bar',
              'link_url': 'https://bar2_link',
              'image_url': 'https://bar2_image',
              'rendered_link_url': 'https://bar2_link',
              'rendered_image_url': 'https://bar2_image',
              'id': ...,
              'kind': 'project'}]

        """
        data = dict(name=name, link_url=link_url, image_url=image_url)

        badges = self.get_badges(name=name)

        if len(badges) == 0:
            return self.gitlab.post_json(f"/projects/{self.id}/badges", data=data)
        badge = badges[0]
        if badge["link_url"] == link_url and badge["image_url"] == image_url:
            return badge
        return self.gitlab.put_json(
            f'/projects/{self.id}/badges/{badge["id"]}', data=data
        )

    def clone_or_pull(
        self,
        path: str,
        date: Optional[str] = None,
        pull_can_fail: bool = False,
        force: bool = False,
        anonymous: bool = False,
    ) -> None:
        """
        Clone or pull the project on the file system (with git).

        If date is given, it is used to retrieve the last commit before the date.

        Unless force=True, running on a path which is not a repo or a
        repo with a different origin will fail.

        Examples:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> import shutil
            >>> path = os.path.join(getfixture('tmp_path'), "subpath")
            >>> project = getfixture('project')
            >>> project.clone_or_pull(path)
            >>> capfd = getfixture('capfd')
            >>> project.gitlab.git(["remote", "-v"], cwd=path)

            >>> capture = capfd.readouterr()
            >>> assert 'origin' in capture.out
            >>> assert f'{project.http_url_with_base_to_repo()} (push)' in capture.out

            >>> path = os.path.join(getfixture('tmp_path'), "other_subpath")
            >>> os.makedirs(path)
            >>> io.open(os.path.join(path, "a_file"), "w").close()

            >>> project.clone_or_pull(path)
            Traceback (most recent call last):
            ...
            NotImplementedError: Target directory ... and is not a git repository...
            >>> project.clone_or_pull(path, force=True)
        """
        forge = self.gitlab
        branch = self.default_branch
        if os.path.isdir(path):
            if not os.path.isdir(os.path.join(path, ".git")):
                if force:
                    forge.log.info(f"Cloning into preexisting directory {path}")
                    forge.git(["init"], cwd=path, anonymous=anonymous)
                    forge.git(
                        ["remote", "add", "origin", self.http_url_with_base_to_repo()],
                        cwd=path,
                        anonymous=anonymous,
                    )
                    forge.git(["fetch", "origin"], cwd=path, anonymous=anonymous)
                    forge.git(
                        [
                            "checkout",
                            "-b",
                            self.default_branch,
                            "--track",
                            f"origin/{branch}",
                        ],
                        cwd=path,
                        anonymous=anonymous,
                    )
                else:
                    raise NotImplementedError(
                        f"Target directory {path} already exists "
                        "and is not a git repository\n"
                        "Use force=True to override"
                    )
            # check origin
            remote = self.gitlab.git(
                ["remote", "-v"], cwd=path, anonymous=anonymous, capture_output=True
            ).stdout.decode()
            if "origin" in remote:
                res = self.gitlab.git(
                    ["remote", "get-url", "origin"],
                    cwd=path,
                    anonymous=anonymous,
                    capture_output=True,
                )
                origin = res.stdout.decode().strip()
                if self.http_url_with_base_to_repo() != origin:
                    if force:
                        self.gitlab.log.warning(
                            f"Repository mismatch: got {origin} "
                            f"expected {self.http_url_with_base_to_repo()}"
                        )
                    else:
                        self.gitlab.log.error(
                            f"Repository mismatch: got {origin} "
                            f"expected {self.http_url_with_base_to_repo()}\n"
                            "Use force=True to override"
                        )
                        return
            self.gitlab.git(
                ["pull", "--no-rebase", self.http_url_with_base_to_repo(), branch],
                cwd=path,
                anonymous=anonymous,
                check=not pull_can_fail,
            )
        else:
            self.gitlab.git(
                ["clone", self.http_url_with_base_to_repo(), path], anonymous=anonymous
            )
        if date is not None:
            self.gitlab.git(
                [
                    "-c",
                    "advice.detachedHead=false",
                    "checkout",
                    "origin/HEAD@{'" + date + "'}",
                ],
                cwd=path,
                anonymous=anonymous,
            )


@dataclass
class Namespace(Resource):
    _resource_type_api_url = "namespaces"
    # In the GitLab api, the namespace of a namespace is specified
    # in the attribute `parent_id` rather than `namespace_id`
    _resource_type_namespace_id_attribute = "parent_id"
    _read_only = Resource._read_only + ("path", "full_path", "parent_id")
    name: str
    path: str
    full_path: str
    kind: str = field(repr=False)
    web_url: Optional[str] = None
    parent_id: Optional[int] = None
    avatar_url: Optional[str] = None
    members_count_with_descendants: Optional[int] = None


@dataclass
class Group(Resource):
    _resource_type_api_url = "groups"
    # In the GitLab api, the namespace of a group is specified
    # in the attribute `parent_id` rather than `namespace_id`
    _resource_type_namespace_id_attribute = "parent_id"
    _read_only = Namespace._read_only + (
        "full_name",
        "parent_id",
        "projects",
        "shared_projects",
    )
    name: str
    path: str
    full_name: str
    full_path: str
    description: str
    visibility: str
    avatar_url: str
    lfs_enabled: bool
    request_access_enabled: bool
    web_url: Optional[str] = None
    shared_with_groups: List[Dict[str, Any]] = field(default_factory=list)
    projects: List[Project] = field(repr=False, default_factory=list)
    shared_projects: List[Project] = field(repr=False, default_factory=list)

    parent_id: Optional[int] = None
    created_at: Optional[str] = None
    default_branch_protection: Optional[str] = None
    subgroup_creation_level: Optional[str] = None
    project_creation_level: Optional[str] = None
    auto_devops_enabled: Optional[str] = None
    mentions_disabled: Optional[bool] = None
    emails_disabled: Optional[bool] = None
    two_factor_grace_period: Optional[bool] = None
    require_two_factor_authentication: Optional[bool] = None
    share_with_group_lock: Optional[bool] = None
    runners_token: Optional[str] = None

    def get_projects(
        self,
        owned: bool = False,
        with_shared: bool = True,
        order_by: str = "created_at",
        sort: str = "desc",  # Python >3.6: Literal['asc', 'desc']
        simple: bool = False,
    ) -> List[Project]:
        """Return the projects of this group

        - `with_shared`: include projects shared to this
          group. Default is true.

        - `simple`: return only limited fields for each project. This
          is a no-op without authentication where only simple fields
          are returned. Default is false.

        - `owned`: limit by projects owned by the current
          user. Default is false.

        - `order_by`: return projects ordered by id, name, path,
          created_at, updated_at, similarity (1), or last_activity_at
          fields. Default is created_at.

        https://docs.gitlab.com/ee/api/groups.html#list-a-groups-projects
        """
        json = self.gitlab.get_json(
            f"/groups/{self.id}/projects",
            data=dict(
                simple=simple,
                owned=owned,
                with_shared=with_shared,
                order_by=order_by,
                sort=sort,
            ),
            depaginate=True,
        )
        # Work around with_shared not available in older gitlab
        if not with_shared:
            json = [
                project for project in json if project["namespace"]["id"] == self.id
            ]

        return [Project(gitlab=self.gitlab, **project) for project in json]

    def get_subgroups(self) -> List["Group"]:
        """Return the subgroups of this group"""
        json = self.gitlab.get_json(f"/groups/{self.id}/subgroups", depaginate=True)
        return [Group(gitlab=self.gitlab, **group) for group in json]

    def get_members(self) -> List["User"]:
        """Return the members of this group"""
        json = self.gitlab.get_json(f"/groups/{self.id}/members/all", depaginate=True)
        return [User(gitlab=self.gitlab, **user) for user in json]

    def export(
        self,
        forge: GitLab,
        full_path: Optional[str] = None,
        ignore: List[str] = [],
    ) -> Union["Group", "User"]:
        """
        Export this group or the projects of this user to another GitLab instance.

        `full_path`: the path of the target namespace in `forge`
        (default: the path of the original group or user).

        Subgroups and subprojects are exported recursively. If a group
        or subgroup already exist in the target forge, it is
        updated. If a project already exists in the target forge, it
        is ignored. This should make the export operation reasonably
        idempotent.

        `ignore` is a list of UNIX style globs (e.g. "*/foo*");
        subgroups and projects whose full path matches one of the
        globs are ignored. See Python's `fnmatch` library for the
        matching details.

        Caveats:

        - to protect againsts Denial of Service attacks, GitLab
          imposes a rate limit on the number of project that are
          imported (max 6 per minutes per default). If the group
          contains many projects, you may need to relaunch the export
          a couple times.
        - Fork relationships are not preserved; any project which is a
          fork is ignored.
        - Project and group members are likely not to be preserved.
          For details, see
          https://docs.gitlab.com/ee/user/project/settings/import_export.html
        """
        if isinstance(self, User):
            self_full_path = self.username
        else:
            self_full_path = self.full_path
        if full_path is None:
            full_path = self_full_path
        if isinstance(self, Group):
            self.gitlab.log.info(
                f"Exporting group {self_full_path} to {full_path} on {forge}"
            )
        else:
            self.gitlab.log.info(
                f"Exporting user {self_full_path}'s projects to {full_path} on {forge}"
            )

        # Get the target namespace; if it exists as a group, update
        # it; if it does not exist, create it as a group
        target: Union["Group", "User"]
        try:
            target = forge.get_user(full_path)
        except ResourceNotFoundError:
            attributes = self.get_attributes()
            for key in self._read_only:
                if key in attributes:
                    del attributes[key]
            target = forge.ensure_group(full_path, **attributes)

        if isinstance(self, Group):
            # Recurse in subgroups
            for subgroup in self.get_subgroups():
                matches = [
                    glob for glob in ignore if fnmatch.fnmatch(subgroup.full_path, glob)
                ]
                if matches:
                    self.gitlab.log.info(
                        f"Ignoring group {subgroup.full_path} which matches {matches}"
                    )
                    continue
                assert isinstance(
                    target, Group
                ), "Cannot export subgroup to a user's namespace"
                subgroup.export(
                    forge, os.path.join(full_path, subgroup.path), ignore=ignore
                )

        for project in self.get_projects(with_shared=False, owned=True):
            matches = [
                glob
                for glob in ignore
                if fnmatch.fnmatch(project.path_with_namespace, glob)
            ]
            if matches:
                self.gitlab.log.info(
                    f"Ignoring project {project.path_with_namespace} which matches"
                    f" {matches}"
                )
                continue
            if project.archived:
                self.gitlab.log.info(
                    f"Ignoring archived project {project.path_with_namespace}"
                )
                continue
            if project.forked_from_project is not None:
                self.gitlab.log.info(
                    f"Ignoring project {project.path_with_namespace} which is a fork"
                )
                continue
            project_full_path = os.path.join(full_path, project.path)
            try:
                forge.get_project(project_full_path)
                self.gitlab.log.info(
                    f"Ignoring project {project.path_with_namespace} which already"
                    " exists in the target forge"
                )
                continue

            except ResourceNotFoundError:
                pass
            project.export(forge, project_full_path)
        return target


@dataclass
class User(Resource):
    _resource_type_api_url = "users"
    _read_only = ("id", "path", "namespace")
    web_url: Optional[str] = None
    name: Optional[str] = None
    username: Optional[str] = None
    state: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    bio: Optional[str] = None
    bio_html: Optional[str] = None
    job_title: Optional[str] = None
    work_information: Optional[str] = None
    message: Optional[str] = None
    location: Optional[str] = None
    public_email: Optional[str] = None
    skype: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    website_url: Optional[str] = None
    organization: Optional[str] = None
    last_sign_in_at: Optional[str] = None
    confirmed_at: Optional[str] = None
    last_activity_on: Optional[str] = None
    email: Optional[str] = None
    theme_id: Optional[int] = None
    color_scheme_id: Optional[int] = None
    projects_limit: Optional[int] = None
    current_sign_in_at: Optional[str] = None
    identities: Optional[List[Dict]] = None
    can_create_group: Optional[bool] = None
    can_create_project: Optional[bool] = None
    two_factor_enabled: Optional[bool] = None
    external: Optional[bool] = None
    private_profile: Optional[bool] = None

    bot: Optional[bool] = None
    followers: Optional[int] = None
    following: Optional[int] = None
    commit_email: Optional[str] = None
    is_admin: Optional[bool] = None
    note: Optional[str] = None

    def get_projects(
        self, with_shared: bool = False, owned: bool = True
    ) -> List["Project"]:
        """
        Return the projects of this user

        """
        assert owned
        assert not with_shared
        return [
            Project(gitlab=self.gitlab, **project)
            for project in self.gitlab.get_json(
                f"/users/{self.id}/projects", depaginate=True
            )
        ]

    export = Group.export


@dataclass
class AnonymousUser:
    username: str = "anonymous"
    name: str = "Anonymous"
    email: str = "anonymous mail"


anonymous_user = AnonymousUser()


class Unknown(enum.Enum):
    unknown = enum.auto()

    def __repr__(self) -> str:
        return f"{self.name}"


unknown = Unknown.unknown


class GitLabTest(GitLab):
    """
    A gitlab instance for testing purposes

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

        >>> gitlab = getfixture('gitlab')
        >>> gitlab.login()

    Caveat: due to the token management (stored on file in the home
    directory), there currently should not be two instances of the
    class `GitLabTest` (more generally of `GitLab` for a given forge)
    logged in with different GitLab users. It is therefore recommended
    to construct instances of `GitLabTest` as above via the `gitlab`
    test fixture which guarantees that it is unique (Singleton).

    To enable test scenarios involving several GitLab users, a context
    manager `gitlab.logged_as` is provided to temporarily switch the
    currently logged in user.
    """

    base_url: str = "http://gitlab/"

    # The following data should be shared with build_tools/create_basic_gitlab.py
    users = [
        {
            "username": "root",
            "password": "dr0w554p!&ew=]gdS",
        },
        {
            "username": "student1",
            "email": "travo@gmail.com",
            "name": "Étudiant de test pour travo",
            "password": "aqwzsx(t1",
            "can_create_group": "True",
        },
        {
            "username": "student2",
            "email": "student2@foo.bar",
            "name": "Student 2",
            "password": "aqwzsx(t2",
        },
        {
            "username": "instructor1",
            "email": "instructor1@foo.bar",
            "name": "Instructor 1",
            "password": "aqwzsx(t3",
        },
        {
            "username": "instructor2",
            "email": "instructor2@foo.bar",
            "name": "Instructor 2",
            "password": "aqwzsx(t4",
        },
    ]
    passwords = {user["username"]: user["password"] for user in users}

    def __init__(self, base_url: str = base_url) -> None:
        if "GITLAB_HOST" in os.environ and "GITLAB_80_TCP_PORT" in os.environ:
            base_url = (
                f"http://{os.environ['GITLAB_HOST']}:{os.environ['GITLAB_80_TCP_PORT']}"
            )
        self.tempdir: tempfile.TemporaryDirectory = tempfile.TemporaryDirectory()
        super().__init__(base_url=base_url, home_dir=self.tempdir.name)

    def confirm(self, message: str) -> bool:
        return True

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        anonymous_ok: bool = False,
    ) -> None:
        """
        Ensure that this GitLabTest session is authenticated

        This behaves as GitLab.login, with two additional features:

        - If a username is given from the list of predefined users in
          `self.users`, then the password is filled by default
          automatically.

        - If no username is provided, and not logged in, then the
          session is authenticated as "student1" (mimicking the usual
          behavior of the current user typing the credentials
          interactively).
        """
        if username is None and self.token is None:
            username = "student1"
        if username is not None:
            password = self.passwords.get(username)
        super().login(username=username, password=password, anonymous_ok=anonymous_ok)
        self.log.info(f"LOGIN: {self.get_current_user().username} {username}")
        assert (
            username is None
            or anonymous_ok
            or self.get_current_user().username == username
        )

    @contextlib.contextmanager
    def logged_as(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        anonymous_ok: bool = False,
    ) -> Iterator:
        """
        Defines a context for this gitlab session with temporary
        authentication as another user

        Example:

            >>> from travo.utils import skip_if_gitlab_not_running
            >>> skip_if_gitlab_not_running()

            >>> gitlab = getfixture('gitlab')
            >>> gitlab.login('student1')
            >>> gitlab.get_current_user().username
            'student1'
            >>> with gitlab.logged_as('student2'):
            ...     gitlab.get_current_user().username
            'student2'
            >>> gitlab.get_current_user().username
            'student1'

            >>> gitlab.logout()
            >>> gitlab.get_current_user()
            Traceback (most recent call last):
            ...
            requests.exceptions.HTTPError:...
            >>> with gitlab.logged_as('student2'):
            ...     gitlab.get_current_user().username
            'student2'
            >>> gitlab.get_current_user()
            Traceback (most recent call last):
            ...
            requests.exceptions.HTTPError:...

            >>> gitlab.login('anonymous', anonymous_ok=True)
            >>> gitlab.get_current_user().username
            'anonymous'
            >>> with gitlab.logged_as('student2'):
            ...     gitlab.get_current_user().username
            'student2'
            >>> gitlab.get_current_user().username   # doctest: +SKIP
            'student1'
        """
        save_token = self.token
        try:
            self.logout()
            assert self._current_user is None
            self.login(username=username, password=password, anonymous_ok=anonymous_ok)
            yield self
        finally:
            self.logout()
            if save_token is not None:
                self.set_token(save_token)
            # Maybe something needs to be done to restore anonymous login?
