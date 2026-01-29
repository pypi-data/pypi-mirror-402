import builtins
import getpass
import requests
import pytest
from travo import gitlab


def test_request_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    forge = gitlab.GitLab(base_url="https://gitlab.example.com")
    inputs = iter(["travo-test-etu", "aqwzsx(t1"])
    with pytest.raises(OSError, match="reading from stdin while output is captured"):
        monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
        user, passwd = gitlab.request_credentials_basic(forge)
        assert user == "travo-test-etu"
        assert passwd == "aqwzsx(t1"

    monkeypatch.setattr(getpass, "getpass", lambda _: "aqwzsx(t1")
    user, passwd = gitlab.request_credentials_basic(forge, username="travo-test-etu")
    assert user == "travo-test-etu"
    assert passwd == "aqwzsx(t1"

    username, password = gitlab.request_credentials_basic(forge, username="anonymous")
    assert username == "anonymous"
    assert password == ""


def test_login_with_personal_access(monkeypatch: pytest.MonkeyPatch) -> None:
    forge = gitlab.GitLab(
        base_url="https://gitlab.example.com", token_type="PERSONAL_ACCESS"
    )
    forge.logout()
    inputs = iter(["personal_token"])
    monkeypatch.setattr(getpass, "getpass", lambda _: next(inputs))
    forge.login()
    assert forge.token == "personal_token"
    forge.logout()


def test_set_token() -> None:
    forge = gitlab.GitLab(
        base_url="https://gitlab.example.com", token_type="PERSONAL_ACCESS"
    )
    personal_token = "personal_token"
    forge.set_token(personal_token)
    assert forge.session.headers["PRIVATE-TOKEN"] == personal_token
    forge.logout()
    assert "PRIVATE-TOKEN" not in forge.session.headers.keys()


def test_token_requests(gitlab_url: str) -> None:
    forge = gitlab.GitLab(base_url=gitlab_url)
    assert not forge.set_token("*Ae", nosave=True)

    forge = gitlab.GitLab(base_url="http://gitlab.example.com")
    with pytest.raises(requests.exceptions.ConnectionError):
        forge.set_token("very_secret_token", nosave=True)


def test_login_username_none(gitlab_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    forge = gitlab.GitLab(base_url=gitlab_url)
    forge.logout()

    inputs = iter(["travo-test-etu", "aqwzsx(t1"])
    with pytest.raises(OSError, match="reading from stdin while output is captured"):
        monkeypatch.setattr(builtins, "input", lambda _: next(inputs))
        forge.login()
        token = forge.token
        assert token is not None
        forge.logout()


def test_login_anonymous(gitlab_url: str) -> None:
    forge = gitlab.GitLab(base_url=gitlab_url)
    forge.login(username="anonymous", anonymous_ok=True)
    token = forge.token
    assert token is None
    forge.login(anonymous_ok=True)
    token = forge.token
    assert token is None


def test_get_user_nousername(gitlab):
    with pytest.raises(ValueError, match="cannot be called without username;"):
        gitlab.get_user()
