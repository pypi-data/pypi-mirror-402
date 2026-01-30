from contextvars import ContextVar
from gettext import NullTranslations
from typing import Any, Union

_current_translations: ContextVar[NullTranslations] = ContextVar("_current_translations", default=None)


class Translator:
    _translations_cache: dict[str, NullTranslations] = {}
    _translations_dir: str = "locale"

    @classmethod
    def set_translations_dir(cls, translations_dir: str):
        cls._translations_dir = translations_dir

    @classmethod
    def _get_translations(cls, locale: str) -> NullTranslations:
        """Get translations for the given locale."""
        from babel.support import Translations

        if locale not in cls._translations_cache:
            try:
                translations = Translations.load(dirname=cls._translations_dir, locales=[locale])
                cls._translations_cache[locale] = translations
            except FileNotFoundError:
                return None
        return cls._translations_cache[locale]

    @classmethod
    def set_locale(cls, locale: str):
        """Set locale for the current context."""
        translations = cls._get_translations(locale)
        if translations:
            translations.install()
            _current_translations.set(translations)

    @classmethod
    def gettext(cls, message: str) -> str:
        """Translate a message based on the current locale."""
        translations = _current_translations.get()
        if translations:
            return translations.gettext(message)
        return message


class LazyString:
    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return Translator.gettext(self.message)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other: Union["LazyString", str]):
        if isinstance(other, LazyString):
            return str(self) == str(other)
        return str(self) == other

    def format(self, *args, **kwargs):
        return str(self).format(*args, **kwargs)


def convert_lazy_string(v: Any) -> Any:
    """Recursively convert LazyString instances to str in nested data structures.

    This function traverses dictionaries, lists and other data structures recursively,
    converting any LazyString instances to regular strings. This is needed because
    JsonSchema and Pydantic (see Pydantic issue #8439) do not support LazyString.

    Args:
        v: The value to convert. Can be a LazyString, dict, list, or any other type.

    Returns:
        The input value with all LazyString instances converted to str. The structure
        of the input (dict/list/etc) is preserved.
    """
    if isinstance(v, dict):
        return {k: convert_lazy_string(v) for k, v in v.items()}
    if isinstance(v, list):
        return [convert_lazy_string(v) for v in v]
    if isinstance(v, LazyString):
        return str(v)
    return v


gettext = Translator.gettext
lazy_gettext = LazyString
_ = Translator.gettext
_l = LazyString
