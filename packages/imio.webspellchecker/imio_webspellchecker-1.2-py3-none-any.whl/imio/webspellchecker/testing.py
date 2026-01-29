# -*- coding: utf-8 -*-
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PloneWithPackageLayer
from plone.testing import z2

import imio.webspellchecker


class ImioWebspellcheckerLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load any other ZCML that is required for your tests.
        # The z3c.autoinclude feature is disabled in the Plone fixture base
        # layer.
        import plone.app.dexterity

        self.loadZCML(package=plone.app.dexterity)
        self.loadZCML(package=imio.webspellchecker, name="testing.zcml")

    def setUpPloneSite(self, portal):
        applyProfile(portal, "imio.webspellchecker:default")
        applyProfile(portal, "imio.webspellchecker:testing")


IMIO_WEBSPELLCHECKER_FIXTURE = ImioWebspellcheckerLayer()


IMIO_WEBSPELLCHECKER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(IMIO_WEBSPELLCHECKER_FIXTURE,),
    name="ImioWebspellcheckerLayer:IntegrationTesting",
)


IMIO_WEBSPELLCHECKER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(IMIO_WEBSPELLCHECKER_FIXTURE,),
    name="ImioWebspellcheckerLayer:FunctionalTesting",
)

WEBSPELLCHECKER_ROBOT_BASE = PloneWithPackageLayer(
    bases=(REMOTE_LIBRARY_BUNDLE_FIXTURE,),
    zcml_package=imio.webspellchecker,
    zcml_filename="testing.zcml",
    gs_profile_id="imio.webspellchecker:testing",
    name="WEBSPELLCHECKER_ROBOT_BASE",
)

IMIO_WEBSPELLCHECKER_ACCEPTANCE_TESTING = FunctionalTesting(
    bases=(
        WEBSPELLCHECKER_ROBOT_BASE,
        z2.ZSERVER_FIXTURE,
    ),
    name="ImioWebspellcheckerLayer:AcceptanceTesting",
)
