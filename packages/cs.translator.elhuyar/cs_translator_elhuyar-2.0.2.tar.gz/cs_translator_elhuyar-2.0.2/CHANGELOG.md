# Changelog

<!--
   You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst
-->

<!-- towncrier release notes start -->

## 2.0.2 (2026-01-17)


### Internal:

- Fix changelog formatting @erral [#changelog]({ cookiecutter.__repository_url }/issues/changelog)

# 2.0.1 (2026-01-17)

## Internal:


- Formatting of README and pypi page @erral


# 2.0 (2026-01-16)

## Breaking changes:


- Replace ``pkg_resources`` namespace with PEP 420 native namespace.
  Support only Plone 6.2 and Python 3.10+. (#3928)


## Internal:


- Go back to use setup.py, because we have many projects in the cs namespace that can't be migrated @erral
- Update configuration files.
  [plone devs]


# 1.0 (2025-08-26)

## Internal:

- Initial release @erral
