# -*- coding: utf-8 -*-
"""Installer for the imio.webspellchecker package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.md").read(),
        open("CONTRIBUTORS.md").read(),
        open("CHANGES.md").read(),
    ]
)


setup(
    name="imio.webspellchecker",
    version="1.2",
    description="Integration of Webspellchecker's WProofReader with Plone, "
    "providing real-time spellchecking for various WYSIWYG editors.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone",
    author="iMio",
    author_email="antoine.duchene@imio.be",
    url="https://github.com/collective/imio.webspellchecker",
    project_urls={
        "PyPI": "https://pypi.python.org/pypi/imio.webspellchecker",
        "Source": "https://github.com/imio/imio.webspellchecker",
        "Tracker": "https://github.com/imio/imio.webspellchecker/issues",
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["imio"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "Products.CMFPlone>=4.3.19",
        "Products.GenericSetup>=1.8.2",
        "plone.api",
        "six",
    ],
    extras_require={
        "test": ["plone.app.robotframework", "plone.app.testing"],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = imio.webspellchecker.locales.update:update_locale
    """,
)
