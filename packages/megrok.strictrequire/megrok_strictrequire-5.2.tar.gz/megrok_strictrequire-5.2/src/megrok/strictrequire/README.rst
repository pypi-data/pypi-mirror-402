megrok.strictrequire
====================

What is megrok.strictrequire?
-----------------------------

Strictrequire implements additional grokkers for the various view components
in Grok. These grokkers determine whether the ``grok.require`` directive has
been explicitly set on the view component (or on its baseclass).

It will raise an error (and thus prevent the startup of the application) if
there's a view component without an explicit use of the ``grok.require``
directive, providing a minimal safety net for finding unprotected views in
your application.

Making use of megrok.strictrequire
----------------------------------

To enable megrok.strictrequire simply list it as a requirement in your
projects's ``setup.py``. Grok based applications that were bootstrapped with
a recent version of the ``grokproject`` command will automatically include
the megrok.strictrequire's ``configure.zcml`` making the additional grokkers
effective.

Caveat
------

If your applications triggers the registration of "third-party" views that do
not themselves specifically use the ``grok.require`` directive, your
application will not start.

If you decide you still want to make use of the third-aprty views you should
make sure the inclusion of the ``configure.zcml`` of megrok.strictrequire
comes *after* the inclusion of the third-party package by tweaking your
applications's ``configure.zcml``. For example::

    <configure xmlns="http://namespaces.zope.org/zope"
               xmlns:grok="http://namespaces.zope.org/grok">
      <include package="grok" />

      <!-- include this package before mgrok.strictrequire is included -->
      <include package="package_with_unprotected_views" />

      <!-- includeDependencies will include megrok.strictrequire -->
      <includeDependencies package="." />
      <grok:grok package="." />
    </configure>
