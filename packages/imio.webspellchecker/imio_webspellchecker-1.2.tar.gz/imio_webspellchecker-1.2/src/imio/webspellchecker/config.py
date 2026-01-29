from copy import deepcopy
from imio.webspellchecker.browser.controlpanel import IWebspellcheckerControlPanelSchema
from plone import api


def get_enabled():
    return api.portal.get_registry_record(name="enabled", interface=IWebspellcheckerControlPanelSchema)


def get_hide_branding():
    return api.portal.get_registry_record(name="hide_branding", interface=IWebspellcheckerControlPanelSchema)


def get_enable_grammar():
    return api.portal.get_registry_record(name="enable_grammar", interface=IWebspellcheckerControlPanelSchema)


def get_theme():
    return api.portal.get_registry_record(name="theme", interface=IWebspellcheckerControlPanelSchema)


def get_enable_autocorrect():
    return api.portal.get_registry_record(name="enable_autocorrect", interface=IWebspellcheckerControlPanelSchema)


def get_default_language():
    return api.portal.get_registry_record(name="default_language", interface=IWebspellcheckerControlPanelSchema)


def get_js_bundle_url():
    return api.portal.get_registry_record(name="js_bundle_url", interface=IWebspellcheckerControlPanelSchema)


def get_service_url():
    return api.portal.get_registry_record(name="service_url", interface=IWebspellcheckerControlPanelSchema)


def get_service_id():
    return api.portal.get_registry_record(name="service_id", interface=IWebspellcheckerControlPanelSchema)


def get_allowed_portal_types(as_copy=True):
    return deepcopy(
        api.portal.get_registry_record(name="allowed_portal_types", interface=IWebspellcheckerControlPanelSchema)
    )


def get_disallowed_portal_types(as_copy=True):
    return api.portal.get_registry_record(name="disallowed_portal_types", interface=IWebspellcheckerControlPanelSchema)


def get_enable_autosearch_in():
    return api.portal.get_registry_record(name="enable_autosearch_in", interface=IWebspellcheckerControlPanelSchema)


def get_disable_autosearch_in():
    return api.portal.get_registry_record(name="disable_autosearch_in", interface=IWebspellcheckerControlPanelSchema)


def set_enabled(value):
    api.portal.set_registry_record(name="enabled", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_hide_branding(value):
    api.portal.set_registry_record(name="hide_branding", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_enable_grammar(value):
    api.portal.set_registry_record(name="enable_grammar", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_theme(value):
    api.portal.set_registry_record(name="theme", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_enable_autocorrect(value):
    api.portal.set_registry_record(name="enable_autocorrect", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_default_language(value):
    api.portal.set_registry_record(name="default_language", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_js_bundle_url(value):
    api.portal.set_registry_record(name="js_bundle_url", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_service_url(value):
    api.portal.set_registry_record(name="service_url", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_service_id(value):
    api.portal.set_registry_record(name="service_id", value=value, interface=IWebspellcheckerControlPanelSchema)


def set_allowed_portal_types(value):
    api.portal.set_registry_record(
        name="allowed_portal_types",
        value=value,
        interface=IWebspellcheckerControlPanelSchema,
    )


def set_disallowed_portal_types(value):
    api.portal.set_registry_record(
        name="disallowed_portal_types",
        value=value,
        interface=IWebspellcheckerControlPanelSchema,
    )


def set_enable_autosearch_in(value):
    api.portal.set_registry_record(
        name="enable_autosearch_in",
        value=value,
        interface=IWebspellcheckerControlPanelSchema,
    )


def set_disable_autosearch_in(value):
    api.portal.set_registry_record(
        name="disable_autosearch_in",
        value=value,
        interface=IWebspellcheckerControlPanelSchema,
    )
