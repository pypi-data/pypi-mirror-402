import os.path
import importlib.resources
from contextlib import ExitStack
import atexit
import typing
import yaml  # type: ignore
import i18n  # type: ignore


class MyLoader(i18n.loaders.YamlLoader):
    loader = yaml.FullLoader


i18n.register_loader(MyLoader, ["yml", "yaml"])
i18n.set("enable_memoization", True)
i18n.set("fallback", "en")
file_manager = ExitStack()
atexit.register(file_manager.close)
ref = importlib.resources.files(__package__) / "locale"
i18n.load_path.append(
    file_manager.enter_context(importlib.resources.as_file(ref)).__str__()
)
i18n.set("locale", os.environ.get("LANG", "en")[:2])


def _(key: str, **kwargs: typing.Any) -> str:
    """Return the i18n translation for this key

    Examples:

        >>> from travo.i18n import _

        >>> i18n.set('locale', 'en')
        >>> _('hi')
        'Hello'
        >>> _('help', script='foo')
        "Type 'foo' for help"

        >>> i18n.set('locale', 'fr')
        >>> _('hi')
        'Bonjour'
        >>> _('help', script='foo')
        "Tapez «foo» pour de l'aide"
    """
    return typing.cast(str, i18n.t(f"travo.{key}", **kwargs))
