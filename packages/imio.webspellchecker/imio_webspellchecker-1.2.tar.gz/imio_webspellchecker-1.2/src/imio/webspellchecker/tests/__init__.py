from imio.webspellchecker.testing import IMIO_WEBSPELLCHECKER_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing.helpers import login
from plone.app.testing.interfaces import TEST_USER_ID
from plone.app.testing.interfaces import TEST_USER_NAME
from zope.globalrequest import setLocal

import unittest


class WSCIntegrationTest(unittest.TestCase):
    """Base class for integration browser tests."""

    layer = IMIO_WEBSPELLCHECKER_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        setLocal("request", self.portal.REQUEST)
        login(self.portal, TEST_USER_NAME)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        super(WSCIntegrationTest, self).setUp()
