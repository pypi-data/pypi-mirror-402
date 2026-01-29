from imio.webspellchecker import _
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


@provider(IVocabularyFactory)
class WebspellcheckerThemesVocabulary(object):
    """Vocabulary factory for http protocols"""

    def __call__(self, context):
        return SimpleVocabulary(
            [
                SimpleTerm("default", "Default"),
                SimpleTerm("gray", "Gray"),
                SimpleTerm("ckeditor5", "CKEditor 5"),
                SimpleTerm("dark", "Dark"),
                SimpleTerm("custom", "Custom"),
            ]
        )


WebspellcheckerThemesVocabularyFactory = WebspellcheckerThemesVocabulary()


@provider(IVocabularyFactory)
class WebspellcheckerDefaultLanguagesVocabulary(object):
    """Vocabulary factory for default languages"""

    def __call__(self, context):
        return SimpleVocabulary(
            [
                SimpleTerm("auto", _("Auto-detect")),
                SimpleTerm("fr_FR", _("French")),
                SimpleTerm("nl_NL", _("Dutch")),
                SimpleTerm("en_US", _("English")),
                SimpleTerm("de_DE", _("German")),
            ]
        )


WebspellcheckerDefaultLanguagesVocabularyFactory = WebspellcheckerDefaultLanguagesVocabulary()
