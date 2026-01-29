from DateTime import DateTime
from imio.webspellchecker import _
from imio.webspellchecker.interfaces import IIWebspellcheckerControlPanelSettings
from plone import api
from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from Products.CMFPlone.utils import safe_unicode
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import Invalid

import json


def is_valid_json(value):
    if value:
        try:
            json.loads(value)
        except:  # NOQA: E722
            raise Invalid(_(u"Invalid JSON."))
    return True


class IWebspellcheckerControlPanelSchema(Interface):
    """ """

    enabled = schema.Bool(
        title=_("Enabled"),
        description=_("Enable or disable Webspellchecker, globally."),
        required=False,
        default=False,
    )
    hide_branding = schema.Bool(
        title=_("Hide branding"),
        description=_("Note: only available for server version."),
        required=False,
        default=False,
    )
    enable_grammar = schema.Bool(
        title=_("Enable grammar checking"),
        description=_(""),
        required=False,
        default=True,
    )
    enable_autocorrect = schema.Bool(
        title=_("Enable autocorrect"),
        description=_("Enable or disable autocorrect feature."),
        required=False,
        default=False,
    )
    default_language = schema.Choice(
        title=_("Default language"),
        description=_("Default language for the webspellchecker."),
        required=True,
        vocabulary="imio.webspellchecker.vocabularies.DefaultLanguages",
        default="fr_FR",
    )
    theme = schema.Choice(
        title=_("Theme"),
        description=_(""),
        required=True,
        vocabulary="imio.webspellchecker.vocabularies.Themes",
        default="default",
    )
    js_bundle_url = schema.TextLine(
        title=_("WSC JS bundle URL"),
        description=_(""),
        required=True,
        default=u"",
    )
    service_url = schema.TextLine(
        title=_("WSC service URL"),
        description=_(""),
        required=True,
        default=u"",
    )
    service_id = schema.TextLine(
        title=_("Service ID"),
        description=_(""),
        required=False,
        default=u"",
    )
    allowed_portal_types = schema.List(
        title=_("Allowed portal types"),
        description=_(
            "Define the portal types where the webspellchecker will be active."
            "If this is left blank, the webspellchecker will be available on all portal types."
        ),
        value_type=schema.Choice(vocabulary="plone.app.vocabularies.PortalTypes"),
        required=False,
        missing_value=[],
        default=[],
    )
    disallowed_portal_types = schema.List(
        title=_("Disallowed portal types"),
        description=_(
            "Define the portal types where the webspellchecker should not be active."
            "If this is left blank, this setting will be ignored."
        ),
        value_type=schema.Choice(vocabulary="plone.app.vocabularies.PortalTypes"),
        required=False,
        missing_value=[],
        default=[],
    )

    # see https://webspellchecker.com/docs/api/wscbundle/AutoSearchMechanism.html
    enable_autosearch_in = schema.TextLine(
        title=_("Enable autosearch in"),
        description=_(
            "The parameter allows enabling the autoSearch mechanism only for elements "
            "with provided class, id, data attribute name or HTML elements type. "
            "Possible values are: <br>"
            " - '.class' - enable autoSearch for elements with a specified class. <br>"
            " - '#id' - enable autoSearch for elements with a specified id. <br>"
            " - '[data-attribute]' - enable autoSearch for elements with a specified data attribute name. <br>"
            " - 'textarea' - enable autoSearch for HTML elements (e.g. textarea, input)."
        ),
        required=False,
        default=u"",
        constraint=is_valid_json,
    )
    disable_autosearch_in = schema.TextLine(
        title=_("Disable autosearch in"),
        description=_(
            "The parameter allows disabling the autoSearch mechanism by class, id, "
            "data attribute name and HTML elements."
            "If enable_autosearch_in option is specified than this option will be ignored. Possible values are: <br>"
            " - '.class' - disable autoSearch for elements with a specified class. <br>"
            " - '#id' - disable autoSearch for elements with a specified id. <br>"
            " - '[data-attribute]' - disable autoSearch for elements with a specified data attribute name. <br>"
            " - 'textarea' - disable autoSearch for HTML elements (e.g. textarea, input)."
        ),
        required=False,
        default=u"",
        constraint=is_valid_json,
    )


@implementer(IIWebspellcheckerControlPanelSettings)
class WebspellcheckerControlPanelEditForm(RegistryEditForm):
    schema = IWebspellcheckerControlPanelSchema
    label = _("Webspellchecker settings")
    description = _("Webspellchecker settings control panel")


class WebspellcheckerSettings(ControlPanelFormWrapper):
    form = WebspellcheckerControlPanelEditForm


def handle_configuration_changed(records, event):
    """Event subscriber that is called every time the configuration changed."""
    api.portal.set_registry_record(
        "imio.webspellchecker.scripts_timestamp",
        safe_unicode(str(DateTime().timeTime())),
    )
