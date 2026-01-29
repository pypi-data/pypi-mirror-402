# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from imio.webspellchecker.testing import IMIO_WEBSPELLCHECKER_INTEGRATION_TESTING
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest


try:
    from Products.CMFPlone.utils import get_installer
except ImportError:
    get_installer = None


def _is_installed(installer, product):
    if hasattr(installer, "is_product_installed"):
        return installer.is_product_installed(product)
    return installer.isProductInstalled(product)


def _uninstall_product(installer, product):
    if hasattr(installer, "uninstall_product"):
        return installer.uninstall_product(product)
    return installer.uninstallProducts([product])


class TestSetup(unittest.TestCase):
    """Test that imio.webspellchecker is properly installed."""

    layer = IMIO_WEBSPELLCHECKER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")

    def test_product_installed(self):
        """Test if imio.webspellchecker is installed."""
        self.assertTrue(_is_installed(self.installer, "imio.webspellchecker"))

    def test_browserlayer(self):
        """Test that IImioWebspellcheckerLayer is registered."""
        from imio.webspellchecker.interfaces import IImioWebspellcheckerLayer
        from plone.browserlayer import utils

        self.assertIn(IImioWebspellcheckerLayer, utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = IMIO_WEBSPELLCHECKER_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        if get_installer:
            self.installer = get_installer(self.portal, self.layer["request"])
        else:
            self.installer = api.portal.get_tool("portal_quickinstaller")
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        _uninstall_product(self.installer, "imio.webspellchecker")
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if imio.webspellchecker is cleanly uninstalled."""
        self.assertFalse(_is_installed(self.installer, "imio.webspellchecker"))

    def test_browserlayer_removed(self):
        """Test that IImioWebspellcheckerLayer is removed."""
        from imio.webspellchecker.interfaces import IImioWebspellcheckerLayer
        from plone.browserlayer import utils

        self.assertNotIn(IImioWebspellcheckerLayer, utils.registered_layers())
