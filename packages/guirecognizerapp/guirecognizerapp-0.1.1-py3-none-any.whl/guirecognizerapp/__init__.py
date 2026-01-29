"""A library to build and preview a set of actions to be executed using guirecognizer."""

import gettext
import locale
from importlib.resources import files

__version__ = "0.1.1"

currentLocale, encoding = locale.getdefaultlocale()
languages = None if currentLocale is None else [currentLocale]
localePath = str(files('guirecognizerapp').joinpath('locale'))
il8nEn = gettext.translation('base', localedir=localePath, languages=languages, fallback=True)
il8nEn.install()
_ = il8nEn.gettext
ngettext = il8nEn.ngettext
