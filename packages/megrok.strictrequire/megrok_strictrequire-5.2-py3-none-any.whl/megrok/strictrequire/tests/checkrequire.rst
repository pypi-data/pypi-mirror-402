"""
.. :doctest:

It is important to have all views closed by default, unless explicitely opened
up. Here we check to see that all view related component at have an explicitly
set `grok.require` directive.

This "assurance" is implemented by a custom grokker that checks whether a view
component does have a required permission defined::

    >>> from grokcore.component.testing import grok_component
    >>> from megrok.strictrequire.tests.fixtures import (
    ...     NoRequireView, NoRequirePage, NoRequireViewlet)
    >>> grok_component('NoRequireView', NoRequireView)
    Traceback (most recent call last):
    ...
    megrok.strictrequire.meta.SecurityError: megrok.strictrequire requires <class 'megrok.strictrequire.tests.fixtures.NoRequireView'> to use the grok.require directive!

    >>> grok_component('NoRequirePage', NoRequirePage)
    Traceback (most recent call last):
    ...
    megrok.strictrequire.meta.SecurityError: megrok.strictrequire requires <class 'megrok.strictrequire.tests.fixtures.NoRequirePage'> to use the grok.require directive!

    >>> grok_component('NoRequireViewlet', NoRequireViewlet)
    Traceback (most recent call last):
    ...
    megrok.strictrequire.meta.SecurityError: megrok.strictrequire requires <class 'megrok.strictrequire.tests.fixtures.NoRequireViewlet'> to use the grok.require directive!

Ditto for grok.Form, grok.AddForm. grok.EditForm, grok.XMLRPC, grok.JSON,
grok.REST components::

    >>> from megrok.strictrequire.tests.fixtures import (
    ...     NoRequireForm, NoRequireAddForm, NoRequireEditForm)
    >>> grok_component('NoRequireForm', NoRequireForm)
    Traceback (most recent call last):
    ...
    megrok.strictrequire.meta.SecurityError: megrok.strictrequire requires <class 'megrok.strictrequire.tests.fixtures.NoRequireForm'> to use the grok.require directive!

    >>> grok_component('NoRequireAddForm', NoRequireAddForm)
    Traceback (most recent call last):
    ...
    megrok.strictrequire.meta.SecurityError: megrok.strictrequire requires <class 'megrok.strictrequire.tests.fixtures.NoRequireAddForm'> to use the grok.require directive!

    >>> grok_component('NoRequireEditForm', NoRequireEditForm)
    Traceback (most recent call last):
    ...
    megrok.strictrequire.meta.SecurityError: megrok.strictrequire requires <class 'megrok.strictrequire.tests.fixtures.NoRequireEditForm'> to use the grok.require directive!

Of course, when the grok.require directive *is* used, there should not be any
exception raised::

    >>> from megrok.strictrequire.tests.fixtures import (
    ...     RequireView, RequirePage, RequireForm, RequireAddForm,
    ...     RequireEditForm)
    >>> grok_component('RequireView', RequireView)
    True
    >>> grok_component('RequirePage', RequirePage)
    True
    >>> grok_component('RequireForm', RequireForm)
    True
    >>> grok_component('RequireAddForm', RequireAddForm)
    True
    >>> grok_component('RequireEditForm', RequireEditForm)
    True

"""
