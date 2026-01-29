# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from Products.CMFQuickInstallerTool import interfaces as QuickInstaller
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):
    def getNonInstallableProfiles(self):
        """Hide uninstall profile from site-creation and quickinstaller."""
        return [
            "imio.webspellchecker:base",
            "imio.webspellchecker:uninstall",
        ]


@implementer(QuickInstaller.INonInstallable)
class HiddenProducts(object):
    def getNonInstallableProducts(self):
        """Do not show on QuickInstaller's list of installable products."""
        return [
            "imio.webspellchecker:base",
            "imio.webspellchecker:uninstall",
        ]


def post_install(context):
    """Post install script"""
    # Do something at the end of the installation of this package.


def uninstall(context):
    """Uninstall script"""
    # Do something at the end of the uninstallation of this package.
