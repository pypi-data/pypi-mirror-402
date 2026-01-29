from imio.webspellchecker import config
from imio.webspellchecker.browser.controlpanel import is_valid_json
from imio.webspellchecker.tests import WSCIntegrationTest
from plone import api
from plone.testing._z2_testbrowser import Browser
from Products.CMFPlone.utils import safe_unicode
from six.moves.urllib.error import HTTPError
from zope.interface import Invalid

import transaction


class TestView(WSCIntegrationTest):
    def setUp(self):
        super(TestView, self).setUp()
        app = self.layer["app"]
        self.browser = Browser(app)
        self.INIT_SCRIPT_URL = "{}/wscinit.js".format(self.portal.absolute_url())

    def test_js_view_doesnt_fail(self):
        self.browser.open(self.INIT_SCRIPT_URL)

    def test_js_view_include_all_info(self):
        self.browser.open(self.INIT_SCRIPT_URL)

        self.assertIn("window.WEBSPELLCHECKER_CONFIG", self.browser.contents)
        self.assertIn("enableGrammar", self.browser.contents)
        self.assertIn("serviceHost", self.browser.contents)
        self.assertIn("autocorrect", self.browser.contents)
        self.assertIn("wsc.fake", self.browser.contents)
        self.assertIn("servicePath", self.browser.contents)
        self.assertIn("/wscservice/api/scripts/ssrv.cgi", self.browser.contents)
        self.assertIn("theme", self.browser.contents)
        self.assertIn("default", self.browser.contents)

    def test_js_view_is_disabled(self):
        config.set_enabled(False)
        transaction.commit()
        self.browser.open(self.INIT_SCRIPT_URL)
        self.assertEqual(
            b"",
            self.browser.contents,
        )

    def test_js_view_headers(self):
        self.browser.open(self.INIT_SCRIPT_URL)

    def test_scripts_viewlet(self):
        self.browser.open(self.portal.absolute_url())
        self.assertIn("wscinit.js", self.browser.contents)
        self.assertIn("wscbundle", self.browser.contents)

    def test_scripts_viewlet_disabled(self):
        config.set_enabled(False)
        transaction.commit()
        self.browser.open(self.portal.absolute_url())
        self.assertNotIn("wscinit.js", self.browser.contents)
        self.assertNotIn("wscbundle", self.browser.contents)

    def test_scripts_viewlet_timestamps(self):
        before_scripts_timestamp = api.portal.get_registry_record("imio.webspellchecker.scripts_timestamp")
        config.set_enable_grammar(False)
        transaction.commit()
        after_scripts_timestamp = api.portal.get_registry_record("imio.webspellchecker.scripts_timestamp")
        self.assertNotEqual(after_scripts_timestamp, before_scripts_timestamp)
        self.browser.open(self.portal.absolute_url())
        self.assertIn("wscinit.js?t=" + after_scripts_timestamp, self.browser.contents)

    def test_allowed_content_types(self):
        config.set_allowed_portal_types(["Document"])
        transaction.commit()

        doc = api.content.create(type="Document", title="My Document", container=self.portal)
        event = api.content.create(type="Event", title="My Event", container=self.portal)
        transaction.commit()

        self.browser.open(doc.absolute_url())
        self.assertIn("wscinit.js", self.browser.contents)
        self.assertIn("wscbundle", self.browser.contents)
        self.browser.open(event.absolute_url())
        self.assertNotIn("wscinit.js", self.browser.contents)
        self.assertNotIn("wscbundle", self.browser.contents)

    def test_disallowed_content_types(self):
        config.set_disallowed_portal_types(["Document", "Image"])
        transaction.commit()

        doc = api.content.create(type="Document", title="My Document", container=self.portal)
        event = api.content.create(type="Event", title="My Event", container=self.portal)
        transaction.commit()

        self.browser.open(doc.absolute_url())
        self.assertNotIn("wscinit.js", self.browser.contents)
        self.assertNotIn("wscbundle", self.browser.contents)
        self.browser.open(event.absolute_url())
        self.assertIn("wscinit.js", self.browser.contents)
        self.assertIn("wscbundle", self.browser.contents)

    def test_enable_autosearch_for(self):
        self.browser.open(self.INIT_SCRIPT_URL)
        self.assertNotIn("enableAutoSearchIn", self.browser.contents)
        config.set_enable_autosearch_in(safe_unicode('["#id, .class"]'))
        transaction.commit()
        self.browser.open(self.INIT_SCRIPT_URL)
        self.assertIn(
            '"enableAutoSearchIn": ["#id, .class"]',
            self.browser.contents,
        )

    def test_disable_autosearch_for(self):
        self.browser.open(self.INIT_SCRIPT_URL)
        self.assertNotIn(
            "disableAutoSearchIn",
            self.browser.contents,
        )
        config.set_disable_autosearch_in(safe_unicode('[".textarea-widget"]'))
        transaction.commit()
        self.browser.open(self.INIT_SCRIPT_URL)
        self.assertIn(
            '"disableAutoSearchIn": [".textarea-widget"]',
            self.browser.contents,
        )

    def test_js_injection(self):
        malicious_input = safe_unicode(""" ""};<script>alert('I'm malicious')</script> """)
        good_input = '[".my-class"]'
        with self.assertRaises(Invalid):
            is_valid_json(malicious_input)
        self.assertTrue(is_valid_json(good_input))

        config.set_enable_autosearch_in(malicious_input)
        transaction.commit()
        with self.assertRaises(HTTPError):
            self.browser.open(self.INIT_SCRIPT_URL)
            self.assertIn("JSONDecodeError", self.browser.contents)
