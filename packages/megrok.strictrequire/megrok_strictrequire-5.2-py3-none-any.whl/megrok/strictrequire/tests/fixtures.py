#############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import grok
import zope.interface


class NoRequireView(grok.View):
    grok.context(zope.interface.Interface)

    def render(self):
        pass


class NoRequirePage(grok.Page):
    grok.context(zope.interface.Interface)

    def render(self):
        pass


class NoRequireViewletManager(grok.ViewletManager):
    grok.context(zope.interface.Interface)

    def render(self):
        pass


class NoRequireViewlet(grok.Viewlet):
    grok.context(zope.interface.Interface)
    grok.viewletmanager(NoRequireViewletManager)

    def render(self):
        pass


class NoRequireForm(grok.Form):
    grok.context(zope.interface.Interface)


class NoRequireAddForm(grok.AddForm):
    grok.context(zope.interface.Interface)


class NoRequireEditForm(grok.EditForm):
    grok.context(zope.interface.Interface)


class RequireView(grok.View):
    grok.context(zope.interface.Interface)
    grok.require('zope.Public')

    def render(self):
        pass


class RequirePage(grok.Page):
    grok.context(zope.interface.Interface)
    grok.require('zope.Public')

    def render(self):
        pass


class RequireForm(grok.Form):
    grok.context(zope.interface.Interface)
    grok.require('zope.Public')


class RequireAddForm(grok.AddForm):
    grok.context(zope.interface.Interface)
    grok.require('zope.Public')


class RequireEditForm(grok.EditForm):
    grok.context(zope.interface.Interface)
    grok.require('zope.Public')
