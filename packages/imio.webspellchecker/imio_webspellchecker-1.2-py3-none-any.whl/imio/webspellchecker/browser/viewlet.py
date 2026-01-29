from imio.webspellchecker.browser.controlpanel import IWebspellcheckerControlPanelSchema
from plone import api
from plone.app.layout.viewlets import ViewletBase
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


WSC_SCRIPTS_TEMPLATE = """
<script type="application/javascript" src="{plonesite}/wscinit.js?t={timestamp}" defer></script>
<script type="application/javascript" crossorigin="anonymous" src="{bundle}?t={timestamp}" defer></script>
"""


class WscJsViewlet(ViewletBase):
    def is_allowed_portal_type(self, settings):
        """
        Check if the portal type of the current context is allowed.
        If allowed_portal_types is empty we assume that the context's
        portal type is allowed.
        """
        return not settings.allowed_portal_types or (
            settings.allowed_portal_types and self.context.portal_type in settings.allowed_portal_types
        )

    def is_disallowed_portal_type(self, settings):
        """
        Check if the portal type of the current context is disallowed.
        If disallowed_portal_types is empty we assume that the context's
        portal type is allowed.
        """
        return settings.disallowed_portal_types and self.context.portal_type in settings.disallowed_portal_types

    def index(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IWebspellcheckerControlPanelSchema, check=False)
        if settings.enabled and self.is_allowed_portal_type(settings) and not self.is_disallowed_portal_type(settings):
            return WSC_SCRIPTS_TEMPLATE.format(
                plonesite=api.portal.get().absolute_url(),
                timestamp=api.portal.get_registry_record("imio.webspellchecker.scripts_timestamp"),
                bundle=settings.js_bundle_url,
            )
        return ""
