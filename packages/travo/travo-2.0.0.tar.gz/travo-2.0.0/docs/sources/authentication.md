# Access your forge

`Travo` goal is to easily interact with a forge, for that, before starting using
`Travo`, it is essential to verify that the forge is accessible and the user can
successfully authenticate into it.

`Travo` communicates with the forge via securized http transactions.
It supports two types of authentication:
- [basic authentication](https://en.wikipedia.org/wiki/Basic_access_authentication) via user and password credentials;
- [personal access token](https://en.wikipedia.org/wiki/Personal_access_token)
authentication.

### Password authentication
`Travo` asks for user and password in order to authenticate.

Please note that the user should have authenticate into the forge at least once for `Travo`
to log in successfully.

### Personal access token authentication
Personal access token (PAT) authentication is required when two-factor authentication (2FA)
or SAML Single Sign-On (SSO) are enabled on the forge: users authenticate with a personal
access token in place of the password.
Username is not evaluated as part of the authentication process.

The user needs to create a Personal Access Token, first, as described, for example,
in the [related gitlab documentation](https://docs.gitlab.com/user/profile/personal_access_tokens/#create-a-personal-access-token).
For `Travo` to be able to interact with the forge the [scope](https://docs.gitlab.com/user/profile/personal_access_tokens/#personal-access-token-scopes)
of the token should be set to `api`.