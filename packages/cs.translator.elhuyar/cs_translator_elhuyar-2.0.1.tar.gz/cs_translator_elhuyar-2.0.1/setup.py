"""Installer for the cs.translator.elhuyar package."""

from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.md").read(),
        open("CHANGELOG.md").read(),
    ]
)


setup(
    name="cs.translator.elhuyar",
    version="2.0.1",
    description="An add-on for Plone",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: 6.1",
        "Framework :: Plone :: 6.2",
        "Framework :: Plone :: Addon",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="Ion Lizarazu",
    author_email="ilizarazu@codesyntax.com",
    url="https://github.com/codesyntax/cs.translator.elhuyar",
    project_urls={
        "PyPI": "https://pypi.org/project/cs.translator.elhuyar/",
        "Source": "https://github.com/codesyntax/cs.translator.elhuyar",
        "Tracker": "https://github.com/codesyntax/cs.translator.elhuyar/issues",
        # 'Documentation': 'https://cs.translator.elhuyar.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10,<3.14",
    install_requires=[
        # -*- Extra requirements: -*-
        "plone.api>=1.8.4",
        "plone.restapi",
        "requests",
        "Products.CMFPlone",
        "Zope",
        "plone.app.layout",
        "plone.app.registry",
        "plone.memoize",
        "plone.z3cform",
        "plone.app.upgrade",
        "Products.GenericSetup",
    ],
    extras_require={
        "test": [
            "plone.app.testing",
            # Plone KGS does not use this version, because it would break
            # Remove if your package shall be part of coredev.
            # plone_coredev tests as of 2016-04-01.
            "plone.app.dexterity",
            "plone.browserlayer",
            "pytest",
            "pytest-cov",
            "pytest-plone>=0.5.0",
            "plone.app.upgrade",
        ],
    },
    entry_points="""
    [z3c.autoinclude.plugin]
    target = plone
    [console_scripts]
    update_locale = cs.translator.elhuyar.locales.update:update_locale
    """,
)
