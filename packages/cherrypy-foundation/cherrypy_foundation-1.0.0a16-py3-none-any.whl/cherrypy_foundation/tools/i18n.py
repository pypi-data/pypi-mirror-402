# Internationalisation tool for cherrypy
# Copyright (C) 2012-2025 Patrik Dufresne
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Internationalization (i18n) and Localization (l10n) support for CherryPy.

This module provides a CherryPy tool that integrates GNU gettext and Babel
to handle language selection, translations, locale-aware formatting, and
timezone handling on a per-request basis.

The active language is resolved in the following order (highest priority first):

1. Language explicitly set with ``with i18n.preferred_lang():``
2. User-defined callback (``tools.i18n.func``)
3. HTTP ``Accept-Language`` request header
4. Default language configured via ``tools.i18n.default``

Translations are loaded using Babel and gettext, and the resolved locale is
available through ``i18n.get_translation()`` during request handling.

---------------------------------------------------------------------------
Basic usage
---------------------------------------------------------------------------

Within Python code, mark translatable strings using ``ugettext`` or
``ungettext``:

    from i18n import gettext as _, ngettext

    class MyController:
        @cherrypy.expose
        def index(self):
            locale = cherrypy.response.i18n.locale
            s1 = _(u"Translatable string")
            s2 = ngettext(
                u"There is one item.",
                u"There are multiple items.",
                2
            )
            return "<br />".join([s1, s2, locale.display_name])

---------------------------------------------------------------------------
Lazy translations
---------------------------------------------------------------------------

If code is executed before a CherryPy response object is available
(e.g. model definitions or module-level constants), use the ``*_lazy``
helpers. These defer translation until the value is actually rendered:

    from i18n_tool import gettext_lazy

    class Model:
        name = gettext_lazy(u"Model name")

---------------------------------------------------------------------------
Templates
---------------------------------------------------------------------------

For template rendering, i18n integrate with jinja2.

    {% trans %}Text to translate{% endtrans %}
    {{ _('Text to translate') }}
    {{ get_translation().gettext('Text to translate') }}
    {{ get_translation().locale }}
    {{ var | format_datetime(format='full') }}
    {{ var | format_date(format='full') }}

---------------------------------------------------------------------------
Configuration
---------------------------------------------------------------------------

Example CherryPy configuration:

    [/]
    tools.i18n.on = True
    tools.i18n.default = "en_US"
    tools.i18n.mo_dir = "/path/to/i18n"
    tools.i18n.domain = "myapp"

The ``mo_dir`` directory must contain subdirectories named after language
codes (e.g. ``en``, ``fr_CA``), each containing an ``LC_MESSAGES`` directory
with the compiled ``.mo`` file:

    <mo_dir>/<language>/LC_MESSAGES/<domain>.mo

"""

import logging
import os
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from gettext import NullTranslations, translation

import cherrypy
import pytz
from babel import dates
from babel.core import Locale, get_global
from babel.support import LazyProxy, Translations

_preferred_lang = ContextVar('preferred_lang', default=())
_preferred_timezone = ContextVar('preferred_timezone', default=())
_translation = ContextVar('translation', default=None)
_tzinfo = ContextVar('tzinfo', default=None)


def _get_config(key, default=None):
    """
    Lookup configuration from request, if available. Fallback to global config.
    """
    if getattr(cherrypy, 'request') and getattr(cherrypy.request, 'config') and key in cherrypy.request.config:
        return cherrypy.request.config[key]
    return cherrypy.config.get(key, default)


@contextmanager
def preferred_lang(lang):
    """
    Re-define the preferred language to be used for translation within a given context.

    with i18n.preferred_lang('fr'):
        i18n.gettext('some string')
    """
    if not (lang is None or isinstance(lang, str)):
        raise ValueError(lang)
    try:
        # Update preferred lang and clear translation.
        if lang:
            token_l = _preferred_lang.set((lang,))
        else:
            token_l = _preferred_lang.set(tuple())
        token_t = _translation.set(None)
        yield
    finally:
        # Restore previous value
        _preferred_lang.reset(token_l)
        _translation.reset(token_t)


@contextmanager
def preferred_timezone(timezone):
    """
    Re-define the preferred timezone to be used for date format within a given context.

    with i18n.preferred_lang('America/Montreal'):
        i18n.format_datetime(...)
    """
    if not (timezone is None or isinstance(timezone, str)):
        raise ValueError(timezone)
    try:
        # Update preferred timezone and clear tzinfo.
        if timezone:
            token_t = _preferred_timezone.set((timezone,))
        else:
            token_t = _preferred_timezone.set(tuple())
        token_z = _tzinfo.set(None)
        yield
    finally:
        # Restore previous value
        _preferred_timezone.reset(token_t)
        _tzinfo.reset(token_z)


@lru_cache(maxsize=32)
def _search_translation(dirname, domain, *locales, sourcecode_lang='en'):
    """
    Loads the first existing translations for known locale.

    :parameters:
        langs : List
            List of languages as returned by `parse_accept_language_header`.
        dirname : String
            A single directory of the translations (`tools.i18n.mo_dir`).
        domain : String
            Gettext domain of the catalog (`tools.i18n.domain`).

    :returns: Translations, the corresponding Locale object.
    """
    if not isinstance(locales, (list, tuple)):
        locales = tuple(locales)

    # Loop on each locales to find the best matching translation.
    for locale in locales:
        try:
            # Use `gettext.translation()` instead of `gettext.find()` to chain translation fr_CA -> fr -> src.
            t = translation(domain=domain, localedir=dirname, languages=[locale], fallback=True, class_=Translations)
        except Exception:
            # If exception occur while loading the translation file. The file is probably corrupted.
            cherrypy.log(
                f'failed to load gettext catalog domain={domain} localedir={dirname} locale={locale}',
                context='I18N',
                severity=logging.WARNING,
                traceback=True,
            )
            continue
        if t.__class__ is NullTranslations and not locale.startswith(sourcecode_lang):
            # Continue searching if translation is not found.
            continue
        t.locale = Locale.parse(locale)
        return t
    # If translation file not found, return default
    t = NullTranslations()
    t.locale = Locale(sourcecode_lang)
    return t


def get_language_name(lang_code):
    """
    Translate the language code into it's language display name.
    """
    try:
        locale = Locale.parse(lang_code)
    except Exception:
        return lang_code
    translation = get_translation()
    return locale.get_language_name(translation.locale)


def get_timezone():
    """
    Get the best timezone information for the current context.

    The timezone returned is determined with the following priorities:

    * value of preferred_timezone()
    * tools.i18n.default_timezone
    * default server time.

    """
    # When tzinfo is defined, use it
    tzinfo = _tzinfo.get()
    if tzinfo is not None:
        return tzinfo
    # Otherwise search for a valid timezone.
    default = _get_config('tools.i18n.default_timezone')
    preferred_timezone = _preferred_timezone.get()
    if default and default not in preferred_timezone:
        preferred_timezone = (
            *preferred_timezone,
            default,
        )
    for timezone in preferred_timezone:
        try:
            tzinfo = dates.get_timezone(timezone)
            break
        except Exception:
            pass
    # If we can't find a valid timezone using the default and preferred value, fall back to server timezone.
    if tzinfo is None:
        tzinfo = dates.get_timezone(None)
    _tzinfo.set(tzinfo)
    return tzinfo


def get_translation():
    """
    Get the best translation for the current context.
    """
    # When translation is defined, use it
    translation = _translation.get()
    if translation is not None:
        return translation

    # Otherwise, we need to search the translation.
    # `preferred_lang` should always has a sane value within a cherrypy request because of hooks
    # But we also need to support calls outside cherrypy.
    sourcecode_lang = _get_config('tools.i18n.sourcecode_lang', 'en')
    default = _get_config('tools.i18n.default')
    preferred_lang = _preferred_lang.get()
    if default and default not in preferred_lang:
        preferred_lang = (
            *preferred_lang,
            default,
        )
    mo_dir = _get_config('tools.i18n.mo_dir')
    domain = _get_config('tools.i18n.domain', 'messages')
    translation = _search_translation(mo_dir, domain, *preferred_lang, sourcecode_lang=sourcecode_lang)
    _translation.set(translation)
    return translation


def list_available_locales():
    """
    Return a list of available translations.
    """
    return_value = []
    # Always return the source code locale.
    sourcecode_lang = _get_config('tools.i18n.sourcecode_lang', 'en')
    return_value.append(Locale.parse(sourcecode_lang))
    # Then scan language directory for more translation.
    mo_dir = _get_config('tools.i18n.mo_dir')
    domain = _get_config('tools.i18n.domain', 'messages')
    if not mo_dir:
        return
    for lang in os.listdir(mo_dir):
        if os.path.exists(os.path.join(mo_dir, lang, 'LC_MESSAGES', f'{domain}.mo')):
            try:
                return_value.append(Locale.parse(lang))
            except Exception:
                continue
    return return_value


def list_available_timezones():
    """
    Return list of available timezone.
    """
    # Babel only support a narrow list of timezone.
    babel_timezone = get_global('zone_territories').keys()
    return [t for t in pytz.all_timezones if t in babel_timezone]


# Public translation functions
def gettext(message):
    """Standard translation function. You can use it in all your exposed
    methods and everywhere where the response object is available.

    :parameters:
        message : Unicode
            The message to translate.

    :returns: The translated message.
    :rtype: Unicode
    """
    return get_translation().gettext(message)


ugettext = gettext


def ngettext(singular, plural, num):
    """Like ugettext, but considers plural forms.

    :parameters:
        singular : Unicode
            The message to translate in singular form.
        plural : Unicode
            The message to translate in plural form.
        num : Integer
            Number to apply the plural formula on. If num is 1 or no
            translation is found, singular is returned.

    :returns: The translated message as singular or plural.
    :rtype: Unicode
    """
    return get_translation().ngettext(singular, plural, num)


ungettext = ngettext


def gettext_lazy(message):
    """Like gettext, but lazy.

    :returns: A proxy for the translation object.
    :rtype: LazyProxy
    """

    def func():
        return get_translation().gettext(message)

    return LazyProxy(func, enable_cache=False)


def format_datetime(datetime=None, format='medium', tzinfo=None):
    """
    Wrapper around babel format_datetime to use current locale and current timezone.
    """
    return dates.format_datetime(
        datetime=datetime,
        format=format,
        locale=get_translation().locale,
        tzinfo=tzinfo or get_timezone(),
    )


def format_date(datetime=None, format='medium', tzinfo=None):
    """
    Wrapper around babel format_date to provide a default locale.
    """
    # To enforce the timezone and locale, make use of format_datetime for dates.
    return dates.format_datetime(
        datetime=datetime,
        format=dates.get_date_format(format),
        locale=get_translation().locale,
        tzinfo=tzinfo or get_timezone(),
    )


def get_timezone_name(tzinfo, width='long'):
    return dates.get_timezone_name(tzinfo, width=width, locale=get_translation().locale)


def _load_default(mo_dir, domain, default, **kwargs):
    """
    Initialize the language using the default value from the configuration.
    """
    # Clear current translation
    _preferred_lang.set(tuple())
    _preferred_timezone.set(tuple())
    # Clear current translation
    _translation.set(None)
    # Clear current timezone
    _tzinfo.set(None)


def _load_accept_language(**kwargs):
    """
    When running within a request, load the preferred language from Accept-Language header.
    """
    if cherrypy.request.headers.elements('Accept-Language'):
        # Sort language by quality
        languages = sorted(cherrypy.request.headers.elements('Accept-Language'), key=lambda x: x.qvalue, reverse=True)
        _preferred_lang.set(tuple(lang.value.replace('-', '_') for lang in languages))
        # Clear current translation
        _translation.set(None)


def _load_cookie_language(**kwargs):
    """
    Load preferred language from a request cookie.

    Expected cookie value formats:
    - en
    - en_US
    - en-US
    """
    # Skip this step if cookie name is not defined.
    cookie_name = _get_config('tools.i18n.cookie_name')
    if not cookie_name:
        return

    # Check if value defined in cookie.
    cookie = cherrypy.request.cookie
    if cookie_name not in cookie:
        return

    try:
        value = cookie[cookie_name].value.replace('-', '_')
    except Exception:
        return

    # Set preferred language and clear cached translation
    _preferred_lang.set((value,))
    _translation.set(None)


def _load_func_language(**kwargs):
    """
    When running a request where a current user is found, load preferred language from user preferences.
    """
    func = _get_config('tools.i18n.lang', default=_get_config('tools.i18n.func'))
    if not func:
        return
    try:
        lang = func()
    except Exception:
        return
    if not lang:
        return
    # Add custom lang to preferred_lang
    _preferred_lang.set((lang,))
    # Clear current translation
    _translation.set(None)


def _load_func_tzinfo(**kwargs):
    """
    When running a request, load the preferred timezone information from user preferences.
    """
    func = _get_config('tools.i18n.tzinfo')
    if not func:
        return
    try:
        tzinfo = func()
    except Exception:
        return
    if not tzinfo:
        return
    # Add custom lang to preferred_lang
    _preferred_timezone.set((tzinfo,))
    # Clear current translation
    _tzinfo.set(None)


def _set_content_language(**kwargs):
    """
    Sets the Content-Language response header (if not already set) to the
    language of `cherrypy.response.i18n.locale`.
    """
    if 'Content-Language' not in cherrypy.response.headers:
        # Only define the content language if the handler uses i18n module.
        translation = _translation.get()
        if translation:
            locale = translation.locale
            language_tag = f"{locale.language}-{locale.territory}" if locale.territory else locale.language
            cherrypy.response.headers['Content-Language'] = language_tag


class I18nTool(cherrypy.Tool):
    """Tool to integrate babel translations in CherryPy."""

    def __init__(self):
        super().__init__('before_handler', _load_default, 'i18n')

    def _setup(self):
        cherrypy.Tool._setup(self)
        # Attach additional hooks as different priority to update preferred lang with more accurate preferences.
        cherrypy.request.hooks.attach('before_handler', _load_accept_language, priority=60)
        cherrypy.request.hooks.attach('before_handler', _load_cookie_language, priority=70)
        cherrypy.request.hooks.attach('before_handler', _load_func_language, priority=75)
        cherrypy.request.hooks.attach('before_handler', _load_func_tzinfo, priority=75)
        cherrypy.request.hooks.attach('before_finalize', _set_content_language)


cherrypy.tools.i18n = I18nTool()
