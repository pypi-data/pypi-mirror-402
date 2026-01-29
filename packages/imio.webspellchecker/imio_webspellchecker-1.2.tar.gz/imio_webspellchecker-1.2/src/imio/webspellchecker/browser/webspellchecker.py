from imio.webspellchecker.browser.controlpanel import IWebspellcheckerControlPanelSchema
from plone import api
from plone.registry.interfaces import IRegistry
from Products.Five import BrowserView
from six.moves.urllib.parse import urlparse
from zope.component import getUtility
from zope.datetime import rfc1123_date

import json


class WebspellcheckerInitJS(BrowserView):
    JS_SCRIPT_TEMPLATE = "window.WEBSPELLCHECKER_CONFIG = {wsc_config};"

    def __call__(self):
        """
        Get the current webspellchecker settings and create the init script
        """
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IWebspellcheckerControlPanelSchema)
        if settings.enabled:
            language = api.portal.get_current_language()
            scripts_timestamp = api.portal.get_registry_record("imio.webspellchecker.scripts_timestamp")
            response = self.request.response
            response.setHeader("Content-type", "text/javascript; charset=utf-8")
            response.setHeader("Last-Modified", rfc1123_date(float(scripts_timestamp)))
            response.setHeader("Cache-Control", "max-age=31536000, public")
            return self.JS_SCRIPT_TEMPLATE.format(
                js_bundle_url=settings.js_bundle_url,
                wsc_config=self.format_json_settings(settings, language),
            )

    def format_json_settings(self, settings, language):
        service_url = urlparse(settings.service_url)
        service_port = service_url.port
        if not service_port:
            service_port = 443 if service_url.scheme == "https" else 80
        wsc_settings = {
            "autoSearch": True,
            "autoDestroy": True,
            "autocorrect": settings.enable_autocorrect,
            "lang": settings.default_language,
            "localization": language,
            "enableGrammar": settings.enable_grammar,
            "theme": settings.theme,
            "removeBranding": settings.hide_branding,
            "serviceProtocol": service_url.scheme,
            "serviceHost": service_url.hostname,
            "servicePort": service_port,
            "servicePath": service_url.path,
            "disableDictionariesPreferences": True,
        }
        if settings.enable_autosearch_in:
            wsc_settings["enableAutoSearchIn"] = json.loads(settings.enable_autosearch_in)
        if settings.disable_autosearch_in:
            wsc_settings["disableAutoSearchIn"] = json.loads(settings.disable_autosearch_in)
        return json.dumps(wsc_settings)
