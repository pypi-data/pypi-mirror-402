Changelog of megrok.strictrequire
=================================

5.2 (2026-01-22)
----------------

- Move package metadata from setup.py to pyproject.toml.

- Add support for Python 3.14.

- Drop support for Python 3.9.


5.1 (2025-02-14)
----------------

- Fix how PEP 420 namespace is used in ``setup.py``.

- Add support for Python 3.13.

- Drop support for Python 3.7, 3.8.

5.0 (2024-03-22)
----------------

- Drop support for explicit (pkg_resources) namespaces and replace it with
  an implicit (PEP 420) namespace.


4.0 (2024-01-25)
----------------

- Drop support for Python 2.7, 3.4, 3.5, 3.6.

- Drop support for ``grok < 5``, thus dropping support for JSON, REST and
  XMLRPC.

- Add support for Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12.


3.0.0 (2018-01-17)
------------------

- Python 3 compatibility.

0.7 (2018-01-10)
----------------

- Dependencies update in preparation of Python2/3 migration.

0.6 (2013-10-16)
----------------

- Add grokker for grok.Page components.

0.5 (2011-07-19)
----------------

- Reflect recent changes in grok 1.8.

0.4 (2011-07-11)
----------------

- Use the groktoolkit versions.

- Don't check the requirement directive for ViewletManager, as these are
  not exposed as views.

0.3 (2010-05-18)
----------------

- Test-requirements have been fixed. They formally include zope.app.testing for
  the moment.

0.2 (2009-06-22)
----------------

- Check ViewletManager and Viewlet components too.

0.1 (2009-06-18)
----------------

- Initial release.
